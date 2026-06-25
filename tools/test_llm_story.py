"""Offline tests for AI story generation -- no network, no backend needed.

Asserts: generation is gated on llm.available(); the validator accepts a good
7x12 story and rejects/repairs malformed ones; a mocked generator's output is
validated, registered, saved, narrates through stories.story_units and resolves
its ambience; the AI-written label is applied. Uses a stubbed completer + a temp
store dir, so nothing touches the network or the real ~/.breathsim.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import llm, llm_keys, llm_story, store, stories  # noqa: E402


def _good_sections():
    s1 = ["You are settling down now, soft and slow." for _ in range(12)]
    mid = ["The quiet river drifts on, gentle and calm." for _ in range(12)]
    last = ["Let yourself drift down now, and rest, and sleep." for _ in range(12)]
    return [s1, mid, mid, mid, mid, mid, last]


def _good_json():
    return json.dumps({"title": "The Quiet River", "ambience": "Mountain Stream",
                       "sections": _good_sections()})


def main():
    # isolate from any real key / ollama / store
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
        assert not llm.available(), "test must run with no backend"

        # gating: with no backend, generate raises a clear disabled error
        try:
            llm_story.generate("the moon")
            raise AssertionError("generate should be gated when no LLM")
        except llm.LLMUnavailable:
            pass
        print("ok: generation gated on llm.available()")

        # validator: good passes, malformed variants fail
        assert llm_story.validate(_good_sections()) == []
        assert llm_story.validate(_good_sections()[:6])           # 6 sections
        bad = _good_sections(); bad[1] = bad[1][:11]              # 11 sentences
        assert llm_story.validate(bad)
        nope = _good_sections(); nope[2] = ["no end punct here"] * 12
        assert llm_story.validate(nope)
        facty = _good_sections(); facty[0] = ["It was the year 1838." for _ in range(12)]
        assert any("fact-free" in e for e in llm_story.validate(facty))
        print("ok: validator accepts good 7x12, rejects malformed")

        # mock completer with a repair loop: 1st reply malformed, 2nd good
        calls = {"n": 0}
        def flaky(prompt, **kw):
            calls["n"] += 1
            return "garbage not json" if calls["n"] == 1 else _good_json()
        story = llm_story.generate("a river", complete=flaky, max_repairs=2)
        assert story and calls["n"] == 2, ("repair loop failed", calls)
        assert story["name"].startswith("AI: ") and story["ai"] is True
        assert len(story["sections"]) == 7 and len(story["sections"][0]) == 12
        print("ok: mocked generate validates + repairs + labels AI-written")

        # save -> registers into the library, dispatches + resolves ambience
        name = llm_story.save(story)
        assert name and name in stories.lecture_names()
        amb = stories.ambience_for(name)
        from breathsim import voices
        assert amb in set(voices.names()), ("ambience did not resolve", amb)
        g = stories.story_units(name)
        first = next(g)
        assert "text" in first and "pause" in first
        # persisted to the (temp) store, and reloadable
        assert any(s["name"] == name for s in store.ai_stories_list())
        from breathsim import lectures
        lectures.LECTURES.pop(name, None)
        llm_story.register_saved()
        assert name in lectures.LECTURES, "saved story should reload"
        llm_story.delete(name)
        assert name not in lectures.LECTURES and not any(
            s["name"] == name for s in store.ai_stories_list())
        print("ok: save -> narrates + persists + reloads + delete")

        print("PASS: AI story gen gated, validated, repaired, saved, label-safe")
        return 0
    finally:
        llm_keys._from_keychain, llm_keys.FILE_PATH = saved_kc, saved_path
        llm_keys._session, store.DIR = None, saved_dir
        if saved_env is not None:
            os.environ["ANTHROPIC_API_KEY"] = saved_env


if __name__ == "__main__":
    raise SystemExit(main())
