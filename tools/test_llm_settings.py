"""Offline tests for the AI Assistant settings helpers -- no Qt, no network.

Asserts the key-security contract of vesper/llm_settings.py's Qt-free helpers:
the typed key is stored where chosen, the active source reflects it, and the key
is NEVER echoed back in any status/result message. Uses a temp chmod-600 file
path and a fixture token that is deliberately NOT key-shaped (so the secret scan
stays clean).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import llm, llm_keys  # noqa: E402
from vesper import llm_settings  # noqa: E402

TOKEN = "vesper-local-test-token-0000wxyz"   # fixture; deliberately not a real key shape


def main():
    # Isolate: no env key, a temp file store, Ollama off, session cleared.
    os.environ.pop("ANTHROPIC_API_KEY", None)
    saved_path = llm_keys.FILE_PATH
    tmp = tempfile.mkdtemp()
    llm_keys.FILE_PATH = os.path.join(tmp, "llm.json")
    llm.enable_ollama(False)
    llm_keys.clear()
    try:
        # No backend by default; status says so and never leaks anything.
        assert not llm.available()
        s0 = llm_settings.status_text()
        assert "none" in s0.lower()
        print("ok: no backend by default; status honest")

        # Empty input is refused (must use Forget), no key stored.
        ok, msg = llm_settings.apply_key("", llm_settings.SESSION)
        assert not ok and TOKEN not in msg and llm_keys.source() is None
        print("ok: empty key refused")

        # Session storage: backend becomes claude, source 'session', key hidden.
        ok, msg = llm_settings.apply_key(TOKEN, llm_settings.SESSION)
        assert ok, msg
        assert llm_keys.source() == "session" and llm.backend_name() == "claude"
        assert TOKEN not in msg, "status message must never contain the key"
        assert TOKEN not in llm_settings.status_text()
        print("ok: session key stored, source=session, never echoed")

        # Forget wipes it everywhere we control; nothing left, message clean.
        msg = llm_settings.forget()
        assert TOKEN not in msg
        assert llm_keys.source() is None and not llm.available()
        print("ok: forget wipes session; status clean")

        # File storage: written chmod-600 to OUR temp path, never the repo.
        ok, msg = llm_settings.apply_key(TOKEN, llm_settings.FILE)
        assert ok and TOKEN not in msg
        assert os.path.exists(llm_keys.FILE_PATH)
        assert llm_keys.FILE_PATH.startswith(tmp)            # never the working tree
        mode = oct(os.stat(llm_keys.FILE_PATH).st_mode & 0o777)
        assert mode == "0o600", mode
        assert llm_keys.source() == "file"
        # The key is on disk only at the user-data path we set, never logged.
        with open(llm_keys.FILE_PATH) as fh:
            assert TOKEN in fh.read()                        # round-trips on this device
        print("ok: file store chmod-600 at user path, source=file")

        llm_settings.forget()
        assert not os.path.exists(llm_keys.FILE_PATH)
        assert llm_keys.source() is None
        print("ok: forget removes the file too")

        print("PASS: AI-assistant settings -- opt-in, source-not-key, key never echoed")
        return 0
    finally:
        llm_keys.clear()
        llm_keys.FILE_PATH = saved_path
        llm.enable_ollama(False)


if __name__ == "__main__":
    raise SystemExit(main())
