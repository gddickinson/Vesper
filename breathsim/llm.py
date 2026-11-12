"""Optional LLM provider, auto-selecting and degrading gracefully.

Backend selection (re-evaluated on each call, so it tracks key/setting changes):
  * **Claude** -- chosen whenever an Anthropic API key resolves (see
    :mod:`breathsim.llm_keys`); the key is the user's own.
  * **Ollama** -- a *local* model fallback, **off by default** and only used when
    the user opts in (``enable_ollama(True)``) -- honouring "no network unless the
    user opts in". When enabled, reachability is probed lazily.
  * **none** -- a null provider: ``available()`` is False and ``complete``/``chat``
    raise :class:`LLMUnavailable`. The whole app works fully in this state.

Safety: nothing here imports or calls the network at module import or in tests.
The API key is fetched lazily via :func:`llm_keys.resolve` at call time and never
stored on a provider object, so it cannot leak through a ``__repr__``. Errors are
sanitised so the key never appears in a message/log.
"""
from __future__ import annotations

import json
import urllib.request

from . import llm_keys

DEFAULT_CLAUDE_MODEL = "claude-haiku-5-5"   # cheap + fast; override per call with model=
# Claude Haiku 5.5 thinks by default (adaptive thinking) and that thinking counts toward
# max_tokens, so the short-output callers (300-500 tokens) ask for low effort. Sent only
# with the default model: an overriding older model (e.g. Haiku 4.5) rejects `effort`.
DEFAULT_CLAUDE_EFFORT = "low"
DEFAULT_OLLAMA_MODEL = "llama3.2"
_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"

# Ollama is OFF by default (no network unless the user opts in).
_ollama = {"enabled": False, "host": "http://localhost:11434"}


class LLMError(RuntimeError):
    pass


class LLMUnavailable(LLMError):
    pass


def enable_ollama(on=True, host=None):
    """Opt in to the local Ollama fallback (default off). Optional custom host."""
    _ollama["enabled"] = bool(on)
    if host:
        _ollama["host"] = host


def _sanitize(text):
    """Strip any occurrence of the live key from a string before it is shown."""
    k = llm_keys.resolve()
    s = str(text)
    return s.replace(k, llm_keys.mask(k)) if k else s


def _ollama_reachable():
    if not _ollama["enabled"]:
        return False
    try:                                            # tiny probe, only when opted in
        req = urllib.request.Request(_ollama["host"] + "/api/tags")
        with urllib.request.urlopen(req, timeout=0.6):
            return True
    except Exception:
        return False


def backend_name():
    """'claude' (a key resolved), else 'ollama' (opted in + reachable), else 'none'."""
    if llm_keys.resolve():
        return "claude"
    if _ollama_reachable():
        return "ollama"
    return "none"


def available():
    return backend_name() != "none"


def status():
    """A safe, log-able snapshot: backend + key source (never the key itself)."""
    return {"backend": backend_name(), "key_source": llm_keys.source(),
            "ollama_enabled": _ollama["enabled"]}


# --- Claude (Anthropic API over urllib; no SDK dependency) ------------------

def _claude_call(messages, system=None, tools=None, max_tokens=1024, model=None):
    key = llm_keys.resolve()
    if not key:
        raise LLMUnavailable("No Anthropic API key is set.")
    model = model or DEFAULT_CLAUDE_MODEL
    body = {"model": model, "max_tokens": int(max_tokens), "messages": messages}
    if model == DEFAULT_CLAUDE_MODEL and DEFAULT_CLAUDE_EFFORT:
        body["output_config"] = {"effort": DEFAULT_CLAUDE_EFFORT}
    if system:
        body["system"] = system
    if tools:
        body["tools"] = tools
    req = urllib.request.Request(
        _ANTHROPIC_URL, data=json.dumps(body).encode("utf-8"),
        headers={"x-api-key": key, "anthropic-version": _ANTHROPIC_VERSION,
                 "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except Exception as e:                          # never leak the key in the error
        raise LLMError("Claude request failed: " + _sanitize(e))


def _claude_text(out):
    parts = [b.get("text", "") for b in out.get("content", [])
             if b.get("type") == "text"]
    return "".join(parts).strip()


# --- Ollama (local) --------------------------------------------------------

def _ollama_post(path, body):
    req = urllib.request.Request(
        _ollama["host"] + path, data=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


# --- public API ------------------------------------------------------------

def complete(prompt, system=None, max_tokens=1024, model=None, **_):
    """Return generated text (str) for *prompt*, using the active backend."""
    b = backend_name()
    if b == "claude":
        return _claude_text(_claude_call(
            [{"role": "user", "content": prompt}], system=system,
            max_tokens=max_tokens, model=model))
    if b == "ollama":
        out = _ollama_post("/api/generate", {
            "model": model or DEFAULT_OLLAMA_MODEL, "prompt": prompt,
            "system": system or "", "stream": False})
        return (out.get("response") or "").strip()
    raise LLMUnavailable("No LLM backend is available (set a key or enable Ollama).")


def chat(messages, system=None, tools=None, max_tokens=1024, model=None, **_):
    """A normalized chat turn: returns {'text', 'tool_calls', 'backend'}.

    *messages* is a list of {'role': 'user'|'assistant', 'content': str}."""
    b = backend_name()
    if b == "claude":
        out = _claude_call(messages, system=system, tools=tools,
                           max_tokens=max_tokens, model=model)
        calls = [{"name": c.get("name"), "input": c.get("input"), "id": c.get("id")}
                 for c in out.get("content", []) if c.get("type") == "tool_use"]
        return {"text": _claude_text(out), "tool_calls": calls, "backend": b}
    if b == "ollama":
        out = _ollama_post("/api/chat", {
            "model": model or DEFAULT_OLLAMA_MODEL, "messages": messages,
            "stream": False})
        return {"text": (out.get("message", {}).get("content") or "").strip(),
                "tool_calls": [], "backend": b}
    raise LLMUnavailable("No LLM backend is available (set a key or enable Ollama).")
