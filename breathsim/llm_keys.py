"""Secure resolution of the user's Anthropic API key -- never committed/shipped.

The key is the USER'S OWN. It is resolved (read, never generated) from, in order:
  1. the ``ANTHROPIC_API_KEY`` environment variable (the app stores nothing);
  2. the OS keychain via the optional ``keyring`` package, if installed;
  3. a local ``~/.breathsim/llm.json`` written **chmod 600** (opt-in; plaintext on
     this device only);
  4. a **session-only** value held in memory (typed this run, never persisted).

It is NEVER written to a tracked path, NEVER printed/logged, and NEVER shown
unmasked -- use :func:`mask`. There is no object here that holds the key in a
``__repr__``; callers should fetch it lazily via :func:`resolve` at the moment of
use and not store it. Reading env / file / keychain is local: **no network**.
"""
from __future__ import annotations

import json
import os

_SERVICE = "vesper"            # keychain service name
_USER = "anthropic_api_key"    # keychain account name
_session = None                # in-memory only; never persisted

# The chmod-600 store path (overridable, e.g. for tests). Lives in ~/.breathsim,
# which is outside the repo and gitignored.
FILE_PATH = os.path.expanduser("~/.breathsim/llm.json")


def _from_env():
    v = os.environ.get("ANTHROPIC_API_KEY")
    return v.strip() if v and v.strip() else None


def _keyring():
    try:
        import keyring  # optional dependency
        return keyring
    except Exception:
        return None


def _from_keychain():
    kr = _keyring()
    if kr is None:
        return None
    try:
        v = kr.get_password(_SERVICE, _USER)
        return v.strip() if v and v.strip() else None
    except Exception:
        return None


def _from_file():
    try:
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH) as fh:
                v = (json.load(fh) or {}).get("anthropic_api_key")
            return v.strip() if v and v.strip() else None
    except Exception:
        return None
    return None


def _from_session():
    return _session


def resolve():
    """Return the API key (str) or None, checked env -> keychain -> file ->
    session. Purely local: never makes a network call."""
    for fn in (_from_env, _from_keychain, _from_file, _from_session):
        v = fn()
        if v:
            return v
    return None


def source():
    """Where the active key comes from: 'env'/'keychain'/'file'/'session'/None.
    Never returns the key itself."""
    if _from_env():
        return "env"
    if _from_keychain():
        return "keychain"
    if _from_file():
        return "file"
    if _from_session():
        return "session"
    return None


def set_session(key):
    """Hold a key in memory for this run only (never written to disk)."""
    global _session
    _session = key.strip() if key and key.strip() else None


def set_file(key):
    """Persist the key to ~/.breathsim/llm.json, chmod 600 (opt-in; plaintext)."""
    key = (key or "").strip()
    if not key:
        return clear_file()
    d = os.path.dirname(FILE_PATH)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(FILE_PATH, "w") as fh:
        json.dump({"anthropic_api_key": key}, fh)
    try:
        os.chmod(FILE_PATH, 0o600)
    except OSError:
        pass


def set_keychain(key):
    """Store the key in the OS keychain (most secure) if keyring is installed."""
    kr = _keyring()
    if kr is None:
        return False
    try:
        kr.set_password(_SERVICE, _USER, (key or "").strip())
        return True
    except Exception:
        return False


def clear_file():
    try:
        if os.path.exists(FILE_PATH):
            os.remove(FILE_PATH)
    except OSError:
        pass


def clear():
    """Forget the key everywhere we control: session, file and keychain entry."""
    global _session
    _session = None
    clear_file()
    kr = _keyring()
    if kr is not None:
        try:
            kr.delete_password(_SERVICE, _USER)
        except Exception:
            pass


def mask(key):
    """A safe display form: all but the last 4 characters hidden."""
    k = str(key or "")
    if not k:
        return ""
    if len(k) <= 4:
        return "*" * len(k)
    return "*" * (len(k) - 4) + k[-4:]
