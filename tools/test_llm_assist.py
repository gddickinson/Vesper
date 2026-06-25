"""Offline tests for the quiet-helper assistant -- no network/backend.

Asserts: gating on llm.available(); a request that maps to a known action returns
a VALIDATED tool call (with clamped args); unknown actions, unknown registry
names, and out-of-range values are refused (never returned as executable); only
whitelisted actions ever appear in the result. Uses a stubbed llm.chat -- no
network -- and the real registries for validation.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import llm, llm_keys, llm_assist, modes, stories  # noqa: E402


def stub(tool_calls, text="Of course."):
    def chat(messages, **kw):
        assert kw.get("tools") and kw.get("system"), "system + tools must be passed"
        return {"text": text, "tool_calls": tool_calls, "backend": "stub"}
    return chat


def main():
    saved_env = os.environ.pop("ANTHROPIC_API_KEY", None)
    saved_kc = llm_keys._from_keychain
    llm_keys._from_keychain = lambda: None
    llm_keys._session = None
    llm.enable_ollama(False)
    try:
        assert not llm.available()

        # gating: no backend -> clear disabled error
        try:
            llm_assist.ask("help")
            raise AssertionError("ask should be gated when no LLM")
        except llm.LLMUnavailable:
            pass
        print("ok: gated on llm.available()")

        a_mode = modes.names()[-1]                 # a real mode (Sleep)
        a_story = stories.lecture_names()[0]       # a real lecture name
        calls = [
            {"name": "set_mode", "input": {"mode": a_mode}},
            {"name": "set_volume", "input": {"level": 9.0}},       # out of range -> clamp
            {"name": "start_story", "input": {"name": a_story}},
            {"name": "set_sleep_timer", "input": {"minutes": 999}},  # clamp to 180
            {"name": "set_pattern", "input": {"name": "Totally Made Up"}},  # unknown -> refuse
            {"name": "delete_everything", "input": {}},             # off-whitelist -> refuse
            {"name": "set_mode", "input": {"mode": "Banana"}},      # unknown mode -> refuse
        ]
        res = llm_assist.ask("set me up for sleep", chat=stub(calls))
        acts = {a["action"]: a["args"] for a in res["actions"]}

        assert res["reply"], "expected a calm reply"
        assert acts.get("set_mode") == {"mode": a_mode}
        assert acts["set_volume"]["level"] == 1.0, "volume must clamp to 1.0"
        assert acts["start_story"] == {"name": a_story}
        assert acts["set_sleep_timer"]["minutes"] == 180, "timer must clamp"
        assert "set_pattern" not in acts, "unknown pattern must be refused"
        assert "delete_everything" not in acts, "off-whitelist must be refused"
        assert "delete_everything" in res["refused"]
        assert res["refused"].count("set_mode") == 1, "the bad mode must be refused once"
        # only whitelisted actions are ever returned as executable
        assert all(a["action"] in llm_assist.WHITELIST for a in res["actions"])
        print("ok: known actions validated/clamped; unknown + off-whitelist refused")

        print("PASS: quiet helper -- whitelist-bounded, validated, gated, no codegen")
        return 0
    finally:
        llm_keys._from_keychain = saved_kc
        llm_keys._session = None
        if saved_env is not None:
            os.environ["ANTHROPIC_API_KEY"] = saved_env


if __name__ == "__main__":
    raise SystemExit(main())
