"""Offline test for the storyteller's soundscape cues (sound_cues.cue_for_text).

The bedtime storyteller's ambience bed follows the words: a line about rain, waves,
a hearth, lanterns... crossfades the bed to a matching procedural nature voice.
This checks the long-standing cues still fire, the newly-added imagery (festival
lamps / lanterns / diyas, and water dripping / trickling / a fountain) maps to a
fitting bed, every target is an always-registered voice, and abstract lines and a
couple of known false-hit traps return nothing.  Pure, no Qt, no audio.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import sound_cues, voices  # noqa: E402


def main():
    # every cue target is a real, always-registered (procedural nature) voice
    for _keys, voice in sound_cues._CUES:
        assert voices.get_voice(voice) is not None, ("unregistered cue target", voice)
    print("ok: every cue target is a registered voice")

    cases = {
        # long-standing cues still fire
        "the rain on the roof": "Rain on a Roof",
        "far off, a roll of thunder": "Distant Thunder",
        "the waves break on the shore": "Ocean Waves",
        "a stream runs through the wood": "Mountain Stream",
        "the crickets sing in the summer night": "Night Crickets",
        "the hearth crackles low": "Campfire",
        # newly added: festival / lamp / lantern glow -> a warm bed
        "the warm lanterns drift on the dark water": "Campfire",
        "rows of little diya lamps line the path": "Campfire",
        "she lights the oil lamp by the door": "Campfire",
        "a paper lantern glows softly overhead": "Campfire",
        # newly added: dripping / trickling water -> the stream bed
        "water trickling slowly into the bowl": "Mountain Stream",
        "the soft dripping of the water clock": "Mountain Stream",
        "a little fountain plays in the courtyard": "Mountain Stream",
    }
    for line, want in cases.items():
        got = sound_cues.cue_for_text(line)
        assert got == want, (line, "->", got, "expected", want)
    print("ok: %d representative lines (incl. the new imagery) cue correctly" % len(cases))

    # abstract / empty lines and known traps return no cue
    for none_line in ("", None, "you let the day's worries drift away",
                      "there is nothing you must do tonight",
                      "the warm light fills the quiet hall"):  # 'warm light' must NOT force fire
        assert sound_cues.cue_for_text(none_line) is None, ("unexpected cue", none_line)
    print("ok: abstract lines + the 'warm light' trap return no cue")

    # anti-thrash: a bed->bed switch must be confirmed over two cueing lines, so a
    # single stray image never flips the ambience back and forth.
    base = "Forest Wind"
    nb = sound_cues.next_bed
    # a first cue blooms in from the base immediately
    assert nb(base, base, "Campfire", None) == ("Campfire", None)
    assert nb(None, base, "Campfire", None) == ("Campfire", None)
    # staying on the same imagery is a no-op
    assert nb("Campfire", base, "Campfire", None) == ("Campfire", None)
    # a single different image is HELD (current bed kept, the new one pending)
    assert nb("Campfire", base, "Ocean Waves", None) == ("Campfire", "Ocean Waves")
    # ...and only switches when that new image recurs on the next cueing line
    assert nb("Campfire", base, "Ocean Waves", "Ocean Waves") == ("Ocean Waves", None)
    # alternating A,B,A,B never switches off A (B never recurs consecutively)
    cur, pend = "Campfire", None
    for img in ("Ocean Waves", "Campfire", "Ocean Waves", "Campfire"):
        cur, pend = nb(cur, base, img, pend)
    assert cur == "Campfire", ("alternating imagery should hold the bed", cur)
    # no cue leaves the bed (caller eases home) and clears any pending candidate
    assert nb("Campfire", base, None, "Ocean Waves") == ("Campfire", None)
    print("ok: next_bed blooms in, holds a stray image, confirms a real switch")

    print("PASS: soundscape cues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
