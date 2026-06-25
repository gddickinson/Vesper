"""Offline test for vesper.cast.cast_summary -- pure who's-who, no Qt loop, no net.

Asserts the speaker->character/costume/source rows, that a saved (LLM-refined)
cast is preferred and labelled, and that a plain book yields no rows.
"""
import os
import sys
import tempfile

os.environ["BREATHSIM_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import books, llm_cast  # noqa: E402
from vesper import cast  # noqa: E402

books.LIB_DIR = os.path.join(os.environ["BREATHSIM_HOME"], "books")
llm_cast.CASTS = os.path.join(os.environ["BREATHSIM_HOME"], "casts.json")

CHARS = ["Cat", "Owl", "Fox", "Bear", "Mouse", "Sheep"]
TEXT = ('It was still.\n\n"Hello," said Alice.\n\n"Hi," replied Bob.\n\n'
        '"Come," Alice said.\n\nThey walked on.')


def main():
    b = books.from_text(TEXT, "Greetings", source="upload")
    books.save(b)

    rows = cast.cast_summary(b, CHARS)
    assert [r["speaker"] for r in rows] == ["Alice", "Bob"], rows
    assert all(r["character"] in CHARS for r in rows)
    assert rows[0]["source"] == "auto"           # heuristic by default
    print(f"ok: auto who's-who {[(r['speaker'], r['character']) for r in rows]}")

    # a saved (LLM) cast is preferred + labelled
    llm_cast.save_cast(b.id, {
        "Alice": {"character": "Sheep", "costume": "Nightcap", "voice": "soft", "emotion": "hush"},
        "Bob": {"character": "Bear", "costume": "None", "voice": "deep", "emotion": "calm"}},
        source="llm")
    rows2 = cast.cast_summary(b, CHARS)
    d = {r["speaker"]: r for r in rows2}
    assert d["Alice"]["character"] == "Sheep" and d["Alice"]["costume"] == "Nightcap"
    assert d["Bob"]["character"] == "Bear"
    assert all(r["source"] == "AI director" for r in rows2)
    print("ok: saved LLM cast preferred + labelled 'AI director'")

    # delete -> back to auto
    llm_cast.delete_cast(b.id)
    assert cast.cast_summary(b, CHARS)[0]["source"] == "auto"
    print("ok: delete_cast -> back to auto")

    # plain book -> no rows
    plain = books.from_text("It was quiet. The lamp glowed.", "Plain", source="upload")
    assert cast.cast_summary(plain, CHARS) == []
    print("ok: a plain book -> no cast rows")

    print("PASS: cast_summary -- who's-who, saved-cast preference, fail-safe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
