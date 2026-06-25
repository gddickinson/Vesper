"""EXPERIMENTAL, opt-in, sandboxed LLM code-plugin generation.

This is the one place the LLM writes actual *code*, and it is deliberately the
most guarded. It is **OFF by default** and unusable until the user explicitly
opts in AND acknowledges the risk (``enable(accept_risk=True)``). Generated code
is **never executed in the app process**. Instead each candidate plugin is:

  1. **statically pre-screened** (defence in depth) -- obviously dangerous
     imports/calls (subprocess, socket, ctypes, network libs, os.system/exec/
     remove, eval/exec/compile/__import__, write-mode ``open`` ...) are rejected
     before the file is ever written;
  2. written to a local, **gitignored** ``plugins`` directory (under the user
     data dir, never the repo working tree);
  3. **bug-tested in an isolated subprocess** -- a fresh ``python`` with a
     strict timeout, a minimal environment (no inherited secrets) and cwd set to
     the plugin dir -- which imports it and runs a tiny ``selfcheck()``; stdout/
     stderr/returncode are captured. A generate -> test -> repair loop re-prompts
     with the captured error a few times.

Even after a plugin passes, the app does **not** load it automatically; loading
stays a separate, explicit, user-gated action. This module only exposes
:func:`loadable` manifests. The PRIMARY guarantees are: opt-in, process isolation,
and no in-process execution -- the static screen is a helper, not the wall.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

from . import llm, store

_enabled = False
_passed = {}                                  # name -> manifest of tested plugins
PLUGIN_DIR = os.path.join(store.DIR, "plugins")   # ~/.breathsim/plugins (gitignored)

# Defence-in-depth denylist (the real wall is the isolated subprocess + opt-in).
_BANNED = [
    r"\bimport\s+subprocess\b", r"\bimport\s+socket\b", r"\bimport\s+ctypes\b",
    r"\bimport\s+multiprocessing\b", r"\bimport\s+(urllib|requests|http|httplib|"
    r"ftplib|smtplib|telnetlib|asyncio|aiohttp)\b", r"\bimport\s+(pickle|marshal|"
    r"shelve)\b", r"\bimport\s+(pty|signal|resource|mmap|fcntl)\b",
    r"\bimport\s+importlib\b", r"\bfrom\s+(subprocess|socket|ctypes|os)\s+import\b",
    r"\bos\.(system|popen|exec[a-z]*|spawn[a-z]*|fork|remove|unlink|rmdir|rename|"
    r"replace|chmod|chown|kill|putenv)\b", r"\bshutil\.", r"\bsubprocess\.",
    r"\bsocket\.", r"\beval\s*\(", r"\bexec\s*\(", r"\bcompile\s*\(",
    r"\b__import__\s*\(", r"\bbreakpoint\s*\(", r"\bglobals\s*\(", r"\binput\s*\(",
    r"\bopen\s*\([^)]*['\"][wax]b?\+?['\"]",   # write/append/exclusive open
]


def is_enabled():
    return _enabled


def enable(accept_risk=False):
    """Opt in to plugin generation. Refuses unless *accept_risk* is true."""
    global _enabled
    _enabled = bool(accept_risk)
    if _enabled:
        os.makedirs(PLUGIN_DIR, exist_ok=True)
    return _enabled


def disable():
    global _enabled
    _enabled = False


def screen(src):
    """Return a list of dangerous constructs found in *src* (empty == clean)."""
    bad = []
    for pat in _BANNED:
        m = re.search(pat, src)
        if m:
            bad.append(m.group(0).strip())
    return bad


def _strip_code(text):
    if not isinstance(text, str):
        return ""
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()


def _safe_name(name):
    n = re.sub(r"[^a-z0-9_]", "", str(name).lower()).strip("_")[:40] or "plugin"
    return "plugin_" + n


_RUNNER = (
    "import sys, importlib.util\n"
    "spec = importlib.util.spec_from_file_location('plugin_under_test', sys.argv[1])\n"
    "m = importlib.util.module_from_spec(spec)\n"
    "spec.loader.exec_module(m)\n"
    "ok = getattr(m, 'selfcheck', lambda: True)()\n"
    "assert ok, 'selfcheck() returned a falsey value'\n"
    "print('SELFCHECK_OK')\n")


def run_isolated(path, timeout=8):
    """Import + self-check *path* in a fresh subprocess (minimal env, cwd=plugin
    dir, hard timeout). Never runs the plugin in this process. Returns a dict."""
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"}
    if os.environ.get("SYSTEMROOT"):
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    try:
        r = subprocess.run([sys.executable, "-I", "-c", _RUNNER, path],
                           cwd=os.path.dirname(path) or ".", env=env,
                           capture_output=True, text=True, timeout=timeout)
        return {"ok": r.returncode == 0 and "SELFCHECK_OK" in r.stdout,
                "returncode": r.returncode, "stdout": r.stdout,
                "stderr": r.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "returncode": None, "stdout": e.stdout or "",
                "stderr": "timed out", "timed_out": True}


def _prompt(spec, error=None):
    p = ("Write a small, self-contained Python plugin module that " + str(spec)
         + ". It MUST define a function selfcheck() that returns True when the "
         "plugin works. Use only pure Python and the standard library math/random "
         "(numpy is allowed). Do NOT use files, the network, subprocess, sockets, "
         "ctypes, eval/exec, or os.system. Return ONLY the Python code, no prose "
         "and no markdown fences.")
    return ("Your previous code failed with:\n" + str(error)[:600]
            + "\nFix it and return ONLY the corrected Python code.\n\n" + p) \
        if error else p


def generate(spec, complete=None, max_repairs=2, timeout=8):
    """Generate -> static-screen -> write -> isolated-test -> repair, returning a
    manifest of a passing plugin (or None). Requires opt-in via :func:`enable`."""
    if not _enabled:
        raise RuntimeError("Plugin generation is disabled. Call "
                           "enable(accept_risk=True) to opt in (experimental).")
    comp = complete or (llm.complete if llm.available() else None)
    if comp is None:
        raise llm.LLMUnavailable("Plugin generation needs an LLM.")
    os.makedirs(PLUGIN_DIR, exist_ok=True)
    name = _safe_name(spec)
    path = os.path.join(PLUGIN_DIR, name + ".py")
    error = None
    for _ in range(int(max_repairs) + 1):
        src = _strip_code(comp(_prompt(spec, error), max_tokens=1500))
        if not src:
            error = "empty response"
            continue
        bad = screen(src)
        if bad:                                # never even write dangerous code
            error = "banned constructs: " + ", ".join(bad)
            continue
        with open(path, "w") as fh:
            fh.write(src)
        res = run_isolated(path, timeout=timeout)
        if res["ok"]:
            manifest = {"name": name, "path": path, "spec": str(spec),
                        "tested": True, "experimental": True}
            _passed[name] = manifest
            return manifest
        error = (res["stderr"] or "")[:600] or "self-check failed"
    try:                                       # leave no failing file behind
        if os.path.exists(path) and name not in _passed:
            os.remove(path)
    except OSError:
        pass
    return None


def loadable():
    """Manifests of plugins that PASSED the isolated test. The app does NOT load
    these automatically -- loading remains a separate, explicit, user action."""
    return list(_passed.values())


def clear():
    _passed.clear()
