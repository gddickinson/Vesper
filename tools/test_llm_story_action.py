"""Offline tests for the Sleep AI-story action helpers -- no Qt loop, no network.

Asserts the Qt-free core of vesper/llm_story_action.py: the feature is OFF with no
backend (`can_generate` False); a stubbed model reply that validates registers a
real, narratable AI story into the live lecture library; and a bad reply yields
(None, None) and registers nothing.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import lectures, llm, llm_keys, stories  # noqa: E402
from vesper import llm_story_action as act  # noqa: E402


def _good_reply(prompt, **kw):
    sections = [["You let the day go now." for _ in range(12)] for _ in range(7)]
    sections[6] = ["You drift gently down into sleep now." for _ in range(12)]
    return json.dumps({"title": "a quiet harbour at night",
                       "ambience": "Ocean Waves", "sections": sections})


def _bad_reply(prompt, **kw):
    return "sorry, I cannot do that"        # not JSON -> never validates


def main():
    os.environ.pop("ANTHROPIC_API_KEY", None)
    llm_keys.clear()
    llm.enable_ollama(False)
    try:
        assert not act.can_generate(), "must be off with no backend"
        print("ok: feature off with no backend")

        name, story = act.make_story("a quiet harbour", complete=_good_reply)
        assert name and name.startswith("AI: "), name
        assert name in lectures.LECTURES
        assert lectures.category_of(name) == "AI Stories"
        assert stories.ambience_for(name) == "Ocean Waves"
        units = list(stories.story_units(name, guidance=False))
        assert len(units) >= 84, len(units)
        print(f"ok: stubbed story registers + narrates ({name}, {len(units)} units)")

        bad_name, bad_story = act.make_story("nope", complete=_bad_reply)
        assert bad_name is None and bad_story is None
        print("ok: invalid reply rejected, nothing registered")

        # clean up the registered fixture
        lectures.LECTURES.pop(name, None)
        print("PASS: AI story action -- gated, validated, narratable, fail-closed")
        return 0
    finally:
        llm_keys.clear()
        llm.enable_ollama(False)


if __name__ == "__main__":
    raise SystemExit(main())
