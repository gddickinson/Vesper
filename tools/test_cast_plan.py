"""Offline test for vesper.cast.segment_plan -- pure, no Qt loop, no network.

Asserts the deterministic segment -> (voice, character, mood) mapping that the
dramatized reader uses: a cast speaker gets their resolved voice + character + an
emotion-coloured mood; the Narrator (or an uncast speaker) keeps the base voice
and no character swap.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vesper import cast  # noqa: E402

VOICES = {"Alice": {"character": "Owl", "voice": "bf_emma"},
          "Bob": {"character": "Fox", "voice": "am_adam"}}
BASE = "af_heart"


def main():
    # a cast speaker -> their voice + character + a mood
    p = cast.segment_plan({"speaker": "Alice", "emotion": "bright"}, VOICES, BASE)
    assert p["voice"] == "bf_emma" and p["character"] == "Owl"
    assert p["mood"] == cast._EMOTION_MOOD["bright"]
    print("ok: cast speaker -> resolved voice + character + bright mood")

    p2 = cast.segment_plan({"speaker": "Bob", "emotion": "hush"}, VOICES, BASE)
    assert p2["voice"] == "am_adam" and p2["character"] == "Fox"
    assert p2["mood"] == cast._EMOTION_MOOD["hush"]
    print("ok: a second speaker maps to their own distinct voice/character")

    # Narrator keeps the base voice, no character swap
    n = cast.segment_plan({"speaker": "Narrator", "emotion": "neutral"}, VOICES, BASE)
    assert n["voice"] == BASE and n["character"] == ""
    print("ok: Narrator keeps the base voice, no character swap")

    # an uncast / unknown speaker also falls back to base + no swap
    u = cast.segment_plan({"speaker": "Ghost", "emotion": "soft"}, VOICES, BASE)
    assert u["voice"] == BASE and u["character"] == ""
    print("ok: an unknown speaker falls back to the base voice")

    # deterministic
    assert cast.segment_plan({"speaker": "Alice", "emotion": "bright"}, VOICES,
                             BASE) == p
    print("ok: deterministic")

    print("PASS: cast.segment_plan -- voice + character + mood, fail-safe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
