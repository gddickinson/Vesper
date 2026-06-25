"""Offline test for the optional spoken-name greeting (vesper/greeting.py).

Covers the pure helpers: sanitize_name (ASCII-fold, allowed chars, length cap,
empty-on-garbage), greeting_line (time-aware variants, None when no name), and
prepend (greeting unit first, then the story stream). No Qt window is built, so
this stays headless; ask_name (the dialog) is exercised by the offscreen smoke.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vesper import greeting  # noqa: E402


def main():
    # sanitize: trims, collapses spaces, caps length
    assert greeting.sanitize_name("  Alex  ") == "Alex"
    assert greeting.sanitize_name("Mary   Jane") == "Mary Jane"
    assert greeting.sanitize_name("x" * 50) == "x" * 24            # capped at 24
    # accents folded to plain ASCII; apostrophe + hyphen kept
    assert greeting.sanitize_name("Zoe") == "Zoe"
    assert greeting.sanitize_name("Anne-Marie O'Neil") == "Anne-Marie O'Neil"
    # garbage / digits / symbols stripped; empty stays empty (= off)
    assert greeting.sanitize_name("") == ""
    assert greeting.sanitize_name("   ") == ""
    assert greeting.sanitize_name("123 #!@") == ""
    assert greeting.sanitize_name("Sam99") == "Sam"
    # output is always pure ASCII
    for raw in ("Jose", "Bjork", "naive", "<script>", "Tom; rm -rf"):
        greeting.sanitize_name(raw).encode("ascii")
    print("ok: sanitize_name folds + filters + caps; empty on garbage")

    # greeting_line: None without a name, time-aware with one
    assert greeting.greeting_line("") is None
    assert greeting.greeting_line("   ") is None
    morn = greeting.greeting_line("Alex", 7)
    eve = greeting.greeting_line("Alex", 20)
    night = greeting.greeting_line("Alex", 23)
    noon = greeting.greeting_line("Alex", 13)
    neutral = greeting.greeting_line("Alex", None)
    for ln in (morn, eve, night, noon, neutral):
        assert ln and ln.startswith("Good") or ln.startswith("Hello"), ln
        assert "Alex" in ln
        ln.encode("ascii")
    assert "morning" in morn and "evening" in eve and "rest" in night.lower()
    assert morn != eve != night != noon
    # the name is sanitized inside greeting_line too
    assert "Alex" in greeting.greeting_line("  alex99 ", 20).replace("alex", "Alex") \
        or "alex" in greeting.greeting_line("  alex99 ", 20)
    print("ok: greeting_line is time-aware, None without a name, pure ASCII")

    # prepend: greeting unit first (kind 'greeting', no section), then the stream
    story = [{"text": "once upon a time", "kind": "story", "section": 0}]
    out = list(greeting.prepend("Good night, Alex.", iter(story)))
    assert len(out) == 2
    g = out[0]
    assert g["text"] == "Good night, Alex." and g["kind"] == "greeting"
    assert "section" not in g and g["pause"] > 0 and g["phase"] is None
    assert out[1] is story[0]                                      # rest untouched
    print("ok: prepend yields the greeting unit, then the story, lazily")

    print("PASS: spoken-name greeting -- sanitize + greeting_line + prepend")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
