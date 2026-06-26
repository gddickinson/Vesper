"""Offline test for narration.speakable -- the spoken-text sanitiser that stops a
TTS engine reading out text symbols ('_', '*', '|', '&', em-dashes...). Pure, no
audio, no Qt. The read-along / caption text is untouched; only what is SENT to the
engine is cleaned.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim.narration import speakable  # noqa: E402


def main():
    # symbols a narrator would mispronounce are removed / folded
    assert speakable('"What lies over _there?_" he asked') == \
        '"What lies over there? " he asked'
    assert speakable("a gold watch & chain") == "a gold watch and chain"
    assert speakable('"Dearest Diana" [wrote Anne],') == '"Dearest Diana" (wrote Anne),'
    assert speakable("*The mutineers were eight") == "The mutineers were eight"
    assert speakable("Her + Mark.") == "Her Mark."
    assert speakable("C{2}HCl{3}O") == "C 2 HCl 3 O"
    assert "_" not in speakable("the word _emphasis_ here")
    assert "|" not in speakable("C (1) |\\ - _ D | \\ ||-")
    print("ok: underscores / asterisks / bars / braces / ampersands cleaned")

    # non-ASCII a lecture or AI story might carry is folded (em-dash, smart quotes)
    assert speakable("smell it — the warm bread") == "smell it -- the warm bread"
    assert speakable("‘hello,’ she said") == "'hello,' she said"
    assert speakable("she said “yes” softly") == 'she said "yes" softly'
    assert speakable("wait… listen") == "wait... listen"
    print("ok: em-dash + smart quotes + ellipsis folded to ASCII")

    # a long ASCII rule collapses to a single pause; '--' em-dash is kept
    assert speakable("end ----------- start") == "end -- start"
    assert speakable('He said, "Wait -- listen," and paused.') == \
        'He said, "Wait -- listen," and paused.'
    print("ok: long rules collapse; real em-dash '--' preserved")

    # clean prose + ordinary punctuation must pass through UNCHANGED
    for s in ("It is a truth universally acknowledged, that a single man.",
              "Mr. Bennet's family; the Gardiners (and the Lucases) too!",
              "'Tom!' No answer. 'TOM!' No answer.",
              "She paused, then -- quietly -- went on."):
        assert speakable(s) == s, (s, speakable(s))
    print("ok: clean prose + ordinary punctuation pass through unchanged")

    # robust to junk input
    assert speakable("") == "" and speakable(None) == ""
    assert speakable("* * *") == ""          # a divider collapses to nothing
    print("ok: empty / None / divider handled")

    print("PASS: narration.speakable -- symbols cleaned, prose untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
