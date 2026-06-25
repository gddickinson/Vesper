"""Offline safety tests for the optional LLM provider.

Runs with NO API key and NO Ollama installed: asserts the module imports clean,
degrades to a null backend, never makes a network call, and never leaks the key.
The fake token below is deliberately NOT key-shaped (no 'sk-ant-') so the repo's
secret scan stays clean -- it is a test fixture, never a real secret.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import llm, llm_keys  # noqa: E402

FAKE = "vesper-local-test-token-0000abcd"   # not a real / key-shaped secret


def main():
    # --- isolate from the real environment -------------------------------
    saved_env = os.environ.pop("ANTHROPIC_API_KEY", None)
    saved_path = llm_keys.FILE_PATH
    saved_kc = llm_keys._from_keychain
    llm_keys._from_keychain = lambda: None       # ignore any real keychain entry
    llm_keys._session = None
    llm.enable_ollama(False)
    tmp = tempfile.mkdtemp()
    llm_keys.FILE_PATH = os.path.join(tmp, "llm.json")
    try:
        # (1) no key + no ollama -> disabled, no network, imports clean
        assert llm_keys.resolve() is None, "expected no key"
        assert llm.backend_name() == "none", llm.backend_name()
        assert llm.available() is False
        assert llm_keys.source() is None
        print("ok: null backend when no key + no ollama")

        # (3) mask hides all but the last 4 chars
        m = llm_keys.mask(FAKE)
        assert m.endswith("abcd") and FAKE[:-4] not in m and m.count("*") == len(FAKE) - 4
        assert llm_keys.mask("") == "" and llm_keys.mask("ab") == "**"
        print("ok: mask hides all but last 4")

        # (2) a session key resolves, but never lands on disk or in any shown text
        llm_keys.set_session(FAKE)
        assert llm_keys.resolve() == FAKE, "session key should resolve"
        assert llm_keys.source() == "session"
        assert not os.path.exists(llm_keys.FILE_PATH), "session key must NOT be written to disk"
        st = llm.status()
        assert FAKE not in str(st) and FAKE not in repr(st), "key leaked into status()"
        assert st["key_source"] == "session" and st["backend"] == "claude"
        print("ok: session key resolves, never written to disk, never shown")

        # file store round-trips with chmod 600, then clear() removes it
        llm_keys.set_session(None)
        llm_keys.set_file(FAKE)
        assert os.path.exists(llm_keys.FILE_PATH)
        mode = os.stat(llm_keys.FILE_PATH).st_mode & 0o777
        assert mode == 0o600, oct(mode)
        assert llm_keys.resolve() == FAKE and llm_keys.source() == "file"
        llm_keys.clear()
        assert not os.path.exists(llm_keys.FILE_PATH) and llm_keys.resolve() is None
        print("ok: chmod-600 file store round-trips + clear() removes it")

        print("PASS: llm provider safe + offline-degrading; key never leaks")
        return 0
    finally:
        llm_keys._from_keychain = saved_kc
        llm_keys.FILE_PATH = saved_path
        llm_keys._session = None
        if saved_env is not None:
            os.environ["ANTHROPIC_API_KEY"] = saved_env


if __name__ == "__main__":
    raise SystemExit(main())
