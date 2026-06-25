"""Dramatized book reading -- a little cast acts out the voices in a book.

When the **Dramatized** toggle is on and a book is playing (Reader or the Sleep
"Book: <title>" path), the heuristic cast Script from :func:`breathsim.bookcast.
script` drives, per spoken line: the **narration voice** (the speaker's character
voice, resolved via :mod:`vesper.char_voice`; the Narrator keeps the base voice),
a gentle **2D character** swap to the speaker (visual only -- it never restarts
the narration stream), a small **face mood** from the line's emotion, and -- in
the optional *expressive* mode -- a soft **background-sound** cue.

Kept SLEEP-GENTLE by default: only the voice + a subtle character/mood change,
no abrupt jumps, no extra threads. Per-line voice is set on the unit dict in the
narrator-thread callback (honoured by ``narration.Narrator``); the character/mood
are plain per-tick state applied on the GUI thread. Default OFF -- with it off (or
no book / no dialogue) narration behaves exactly as before. The pure
:func:`segment_plan` is unit-tested offline.
"""
from __future__ import annotations

# Gentle emotion -> (smile, brow, eyeb) deltas. Small, so it still lulls.
_EMOTION_MOOD = {
    "bright": (0.18, 0.0, 0.05),
    "soft": (0.02, 0.0, 0.0),
    "hush": (-0.04, 0.0, -0.03),
    "neutral": (0.07, 0.0, 0.0),
}


def segment_plan(seg, voices, base_voice):
    """Pure: map a bookcast segment -> ``{voice, character, mood}`` deterministically.

    *voices* maps speaker -> ``{character, voice}`` (a resolved voice id). The
    Narrator (or an uncast speaker) keeps *base_voice* and no character swap."""
    sp = (seg or {}).get("speaker", "Narrator")
    vc = (voices or {}).get(sp)
    voice = vc["voice"] if (vc and vc.get("voice")) else base_voice
    character = vc["character"] if vc else ""          # "" -> keep narrator's char
    mood = _EMOTION_MOOD.get(seg.get("emotion", "neutral"), (0.0, 0.0, 0.0))
    return {"voice": voice, "character": character, "mood": mood}


class _CastMixin:
    def set_dramatized(self, on):
        """Toggle the dramatized cast reading (persisted). Off -> plain narration."""
        self._dramatize = bool(on)
        from breathsim import store
        store.save_settings({"dramatize": self._dramatize})
        if not self._dramatize:
            self._restore_cast_character()
            self._cast = None
        if self._story_scene and self.controller.running:
            self._start_story()                        # rebuild so it (de)casts

    def set_cast_expressive(self, on):
        """Wider variation (background-sound following) for the daytime Reader."""
        self._cast_expressive = bool(on)
        from breathsim import store
        store.save_settings({"cast_expressive": self._cast_expressive})

    def build_cast(self, book):
        """Build a cast for *book* (or None when off / no dialogue). Prefers a saved
        (LLM-refined) cast; resolves each speaker's character to a real narrator
        voice ONCE. When a backend is configured + no saved cast yet, it kicks off
        the LLM director off-thread (used next time)."""
        if not getattr(self, "_dramatize", False) or not book:
            return None
        from breathsim import bookcast, llm_cast, narration, xtts_tts
        from . import char_voice, characters
        sc = bookcast.script(book, pool=characters.names())
        if not sc.get("speakers"):
            return None                                # no dialogue -> plain reading
        self._maybe_direct_cast(book)                  # opt-in LLM refine (off-thread)
        saved = None
        try:
            saved = llm_cast.load_cast(book.id)        # speaker -> {character, costume, ...}
        except Exception:
            saved = None
        names = set(characters.names())
        avail = narration.available_voices(self.speech)
        voices = {}
        for sp in sc["speakers"]:
            info = (saved.get(sp) if isinstance(saved, dict) else None) or sc["cast"][sp]
            ch = info.get("character")
            if ch not in names:
                ch = sc["cast"][sp]["character"]
            cv = char_voice.get(ch)
            v = (xtts_tts.PREFIX + cv.xtts) if (cv.xtts and xtts_tts.ready()) else None
            v = v or char_voice.pick_voice(cv.hints, avail)
            voices[sp] = {"character": ch, "voice": v,
                          "costume": (info.get("costume") or "None")}
        return {"by": {s["sentence"]: s for s in sc["segments"]},
                "voices": voices, "base_voice": self.narrator.voice,
                "cast": sc["cast"], "speakers": sc["speakers"],
                "source": "llm" if saved else "heuristic"}

    def _maybe_direct_cast(self, book):
        """If a backend is configured + no cast is saved yet, run the LLM director
        ON A DAEMON THREAD (never blocks; result used next time). Opt-in only."""
        from breathsim import llm, llm_cast
        if not llm.available():
            return
        try:
            if llm_cast.load_cast(book.id) is not None:
                return
        except Exception:
            return
        inflight = getattr(self, "_cast_inflight", None)
        if inflight is None:
            inflight = self._cast_inflight = set()
        if book.id in inflight:
            return
        inflight.add(book.id)
        import threading
        from . import characters

        def work():
            try:
                llm_cast.direct(book, characters.names(), characters.costume_names())
            except Exception:
                pass
            finally:
                inflight.discard(book.id)
        threading.Thread(target=work, daemon=True).start()

    def cast_annotate(self, unit):
        """Narrator-thread callback: set this line's voice on the unit + stash the
        pending character / mood / sound (plain state, applied on the GUI tick)."""
        cast = getattr(self, "_cast", None)
        if not cast:
            return
        seg = cast["by"].get(int(unit.get("sentence", -1)))
        if not seg:
            return
        plan = segment_plan(seg, cast["voices"], cast["base_voice"])
        unit["voice"] = plan["voice"]                  # honoured per line by the narrator
        self._cast_char_pending = plan["character"]
        self._cast_mood = plan["mood"]
        if getattr(self, "_cast_expressive", False) and seg.get("sound"):
            self._sfx_target = seg["sound"]            # gentle bed follow (expressive)
            self._sfx_idle = 0

    def apply_cast_tick(self):
        """GUI-thread per-tick: swap the visible character + set the mood (gentle).
        Uses ``face.set_character`` (visual only) so it never restarts narration."""
        if not getattr(self, "_cast", None):
            return
        pend = getattr(self, "_cast_char_pending", None)
        if pend is not None and self.face.uses_cat():
            want = pend or getattr(self, "_character", "Cat")
            if want != self.face.character():
                self.face.set_character(want)
                self._cast_active = True
        m = getattr(self, "_cast_mood", None)
        if m:
            self._mood_target = m

    def _restore_cast_character(self):
        if getattr(self, "_cast_active", False):
            self.face.set_character(getattr(self, "_character", "Cat"))
            self._cast_active = False
