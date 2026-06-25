"""Offline test for breathsim.bookcast -- pure, no Qt, no network, no LLM.

Feeds a fixture passage with two named speakers (including a tag split onto the
next fragment after a '?') and asserts: speakers detected, distinct characters
per speaker, dialogue vs narration flagged, deterministic across runs, and a
plain (no-dialogue) book yields all-Narrator segments with an empty cast.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import bookcast, books  # noqa: E402

books.LIB_DIR = os.path.join(os.environ["BREATHSIM_HOME"], "books")

TEXT = (
    "The garden was still under the moon.\n\n"
    '"Good evening," said Alice.\n\n'
    '"And to you," replied Bob.\n\n'
    '"Shall we walk by the river?" Alice asked.\n\n'   # tag splits after the '?'
    '"Yes, let us go," said Bob.\n\n'
    "They walked together along the quiet path."
)


def main():
    book = books.from_text(TEXT, "An Evening", source="upload")
    sc = bookcast.script(book)
    segs = sc["segments"]
    by_text = {s["text"]: s for s in segs}

    # speakers + distinct characters
    assert sc["speakers"] == ["Alice", "Bob"], sc["speakers"]
    ca, cb = sc["cast"]["Alice"]["character"], sc["cast"]["Bob"]["character"]
    assert ca != cb and ca in bookcast.POOL and cb in bookcast.POOL
    print(f"ok: cast Alice->{ca}, Bob->{cb} (distinct, from the pool)")

    # attribution: 'said Alice' / 'Alice asked' (split) / 'said Bob'
    assert by_text['"Good evening," said Alice.']["speaker"] == "Alice"
    assert by_text['"And to you," replied Bob.']["speaker"] == "Bob"
    # the bare quote whose 'Alice asked.' tag was split onto the next sentence
    q = by_text['"Shall we walk by the river?"']
    assert q["speaker"] == "Alice" and q["is_dialogue"], q
    assert q["emotion"] == "soft"                      # a question
    print("ok: attribution incl. a tag split across the '?' boundary")

    # narration -> Narrator, no character
    nar = by_text["The garden was still under the moon."]
    assert nar["speaker"] == "Narrator" and not nar["is_dialogue"]
    assert nar["character"] == ""
    print("ok: narration is the Narrator (no character swap)")

    # every dialogue segment carries an assigned character; speaker chars valid
    for s in segs:
        if s["is_dialogue"] and s["speaker"] in sc["cast"]:
            assert s["character"] in bookcast.POOL
    print(f"ok: {sc['dialogue_lines']} dialogue / {sc['narrator_lines']} narration lines")

    # deterministic
    assert bookcast.script(book) == sc
    print("ok: deterministic across runs")

    # plain book -> all Narrator, empty cast
    plain = books.from_text("It was quiet. The lamp glowed. Snow fell softly.",
                            "Plain", source="upload")
    ps = bookcast.script(plain)
    assert ps["speakers"] == [] and ps["cast"] == {}
    assert all(s["speaker"] == "Narrator" for s in ps["segments"])
    print("ok: a plain book casts no speakers (all Narrator)")

    print("PASS: bookcast -- speakers, casting, dialogue/narration, deterministic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
