"""Offline tests for LLM structured-content generation -- no network/backend.

Asserts: generation is gated on llm.available(); a good pattern/voice/mantra
request validates, constructs (and for voices renders finite + non-clipping),
saves and reloads; out-of-range values are CLAMPED to safe bounds and unknown
fields are ignored; non-JSON replies are rejected. Stubbed completer + temp store
so nothing hits the network or the real ~/.breathsim.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import llm, llm_keys, llm_content, store, voices, patterns  # noqa: E402


def reply(obj):
    """A completer that always returns the JSON of *obj*."""
    return lambda prompt, **kw: json.dumps(obj)


def main():
    saved_env = os.environ.pop("ANTHROPIC_API_KEY", None)
    saved_kc, saved_path, saved_dir = (llm_keys._from_keychain, llm_keys.FILE_PATH,
                                       store.DIR)
    llm_keys._from_keychain = lambda: None
    llm_keys._session = None
    llm.enable_ollama(False)
    tmp = tempfile.mkdtemp()
    llm_keys.FILE_PATH = os.path.join(tmp, "llm.json")
    store.DIR = tmp
    try:
        assert not llm.available()

        # gating: no backend -> clear disabled error
        for fn in (llm_content.pattern, llm_content.voice, llm_content.mantra):
            try:
                fn("anything")
                raise AssertionError("should be gated when no LLM")
            except llm.LLMUnavailable:
                pass
        print("ok: pattern/voice/mantra gated on llm.available()")

        # pattern: out-of-range values are clamped; non-JSON rejected
        p = llm_content.pattern("slow", complete=reply(
            {"name": "Mine", "inhale": 999, "hold_full": -5, "exhale": 7,
             "hold_empty": 0, "description": "ok"}))
        assert p and p["inhale"] <= 30 and p["hold_full"] >= 0 and p["name"].startswith("AI: ")
        assert llm_content.pattern("x", complete=lambda *a, **k: "not json", max_repairs=1) is None
        name = llm_content.save_pattern(p)
        assert patterns.preset_by_name(name) is not None, "pattern not registered"
        assert any(x["name"] == name for x in store.patterns_list()), "pattern not saved"
        print("ok: pattern clamps ranges, rejects non-JSON, saves + registers")

        # voice: unknown fields ignored, gain clamped, constructs + renders, saves
        v = llm_content.voice("airy", complete=reply(
            {"name": "Breeze", "noise": "white", "filt": ["bandpass", 1800, 0.7],
             "gain": 99, "width": 5, "evil": True, "kind": "sample"}))
        assert v and v["gain"] <= 0.6 and v["width"] <= 1.0 and "evil" not in v
        assert v["kind"] == "noise", "kind must stay in the safe family"
        vn = llm_content.save_voice(v)
        assert vn in set(voices.names()), "voice not registered"
        print("ok: voice whitelists fields, clamps gain, renders, saves + registers")

        # mantra: cleaned to letters-only lowercase, valid tonic
        m = llm_content.mantra("om", complete=reply(
            {"name": "Aum", "syllables": ["OM!", "ma 3", "ni", "x" * 20], "note": "bogus"}))
        assert m and m["syllables"][:3] == ["om", "ma", "ni"] and m["note"] == "C3"
        mn = llm_content.save_mantra(m)
        assert any(x["name"] == mn for x in store.ai_mantras_list())
        print("ok: mantra cleans syllables + tonic, saves")

        print("PASS: structured content validated, clamped, render-checked, saved")
        return 0
    finally:
        llm_keys._from_keychain, llm_keys.FILE_PATH = saved_kc, saved_path
        llm_keys._session, store.DIR = None, saved_dir
        if saved_env is not None:
            os.environ["ANTHROPIC_API_KEY"] = saved_env


if __name__ == "__main__":
    raise SystemExit(main())
