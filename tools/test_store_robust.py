"""Offline test: a corrupt-but-valid store JSON file must not crash the app.

The user files in ``~/.breathsim`` are hand-editable and can be written
partially or in a legacy shape. A list-typed file (patterns / voices / presets /
ai_stories / ai_mantras / favourites / recent_picks) that parses as a JSON
*scalar*, ``null`` or *object* instead of an array used to slip through the
reader untouched, and every consumer that iterated it would then crash -- most
seriously ``register_all`` (called unguarded at window construction), which
raised ``TypeError: ... is not iterable`` and failed the whole launch.

This pins the fix: the list-readers degrade a non-list file to ``[]`` (like the
dict-readers degrade to ``{}``), so startup and every save/delete survive a
junk file.  Pure, no Qt, no audio.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# point the store at a throwaway home BEFORE importing it (DIR is read at import)
_TMP = tempfile.mkdtemp(prefix="bhstore_")
os.environ["BREATHSIM_HOME"] = _TMP

from breathsim import store  # noqa: E402


def _write(name, raw):
    with open(os.path.join(_TMP, name), "w") as fh:
        fh.write(raw)


# every list-typed file and a reader that returns its contents
_LIST_FILES = {
    "patterns.json": store.patterns_list,
    "voices.json": store.voices_list,
    "presets.json": store.presets_list,
    "ai_stories.json": store.ai_stories_list,
    "ai_mantras.json": store.ai_mantras_list,
    "favourites.json": store.favourites,
    "recent_picks.json": store.recent_picks,
}

# JSON values that parse cleanly yet are NOT a list (the dangerous cases)
_JUNK = ["5", "null", "true", '"a string"', '{"name": "X", "inhale": 4}', "{}"]


def main():
    # 1) every list-reader returns a list (never crashes) for every junk shape
    for raw in _JUNK:
        for name, reader in _LIST_FILES.items():
            _write(name, raw)
            got = reader()
            assert isinstance(got, list), (name, raw, "->", type(got))
    print("ok: all list-readers degrade a non-list file to a list (%d shapes)"
          % len(_JUNK))

    # 2) register_all (called unguarded at launch) must not raise on any junk
    for raw in ("5", "null", "true", '{"name": "Box"}', '"oops"'):
        _write("patterns.json", raw)
        _write("voices.json", raw)
        store.register_all()          # used to TypeError 'int'/'NoneType' not iterable
    print("ok: register_all survives scalar/null/object patterns.json + voices.json")

    # 3) save/delete/preset-load recover from an object-shaped file (action-crash)
    _write("patterns.json", '{"name": "Legacy", "inhale": 4}')
    store.save_pattern({"name": "New", "inhale": 4, "hold_full": 2,
                        "exhale": 6, "hold_empty": 2})
    assert any(p.get("name") == "New" for p in store.patterns_list())
    store.delete_pattern("New")

    _write("voices.json", '{"name": "Legacy"}')
    store.save_voice({"name": "Vx", "kind": "noise", "source": "pink"})
    assert any(v.get("name") == "Vx" for v in store.voices_list())

    _write("presets.json", '{"name": "Legacy"}')
    assert store.preset_by_name("anything") is None      # used to AttributeError
    store.save_preset({"name": "P1", "voice": "Nose Breath"})
    assert store.preset_by_name("P1") is not None
    print("ok: save_pattern/save_voice/preset_by_name recover from an object file")

    # 4) a healthy list still round-trips untouched
    _write("patterns.json", json.dumps([{"name": "Keep", "inhale": 4,
                                         "hold_full": 0, "exhale": 6,
                                         "hold_empty": 0}]))
    assert [p["name"] for p in store.patterns_list()] == ["Keep"]
    print("ok: a well-formed list file is preserved")

    print("PASS: store corrupt-file robustness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
