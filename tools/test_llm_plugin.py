"""Offline tests for the experimental sandboxed plugin path -- no network/LLM.

Asserts: it is OFF by default and enable() refuses without accept_risk; the
static screen rejects dangerous constructs (and such code is never written/run);
a benign plugin passes the isolated-subprocess self-check (and actually runs
THERE, not in-process); an erroring plugin is caught (returncode != 0) without
crashing; and generation is gated. Uses a stubbed completer + temp plugin dir.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from breathsim import llm_plugin  # noqa: E402

BENIGN = "import math\n\ndef selfcheck():\n    print('PLUGIN_RAN_IN_SUBPROCESS')\n    return math.sqrt(4) == 2\n"
ERRORING = "def selfcheck():\n    raise ValueError('boom')\n"
DANGEROUS = "import subprocess\n\ndef selfcheck():\n    subprocess.run(['echo','hi'])\n    return True\n"


def reply(src):
    return lambda prompt, **kw: src


def main():
    saved_dir = llm_plugin.PLUGIN_DIR
    llm_plugin.disable()
    llm_plugin.clear()
    tmp = tempfile.mkdtemp()
    llm_plugin.PLUGIN_DIR = os.path.join(tmp, "plugins")
    try:
        # OFF by default; enable() refuses without accept_risk
        assert not llm_plugin.is_enabled()
        assert llm_plugin.enable() is False and not llm_plugin.is_enabled()
        try:
            llm_plugin.generate("anything", complete=reply(BENIGN))
            raise AssertionError("generate must be gated when disabled")
        except RuntimeError:
            pass
        print("ok: off by default; generate refused until opt-in")

        assert llm_plugin.enable(accept_risk=True) is True
        os.makedirs(llm_plugin.PLUGIN_DIR, exist_ok=True)

        # static screen catches dangerous constructs
        assert llm_plugin.screen(DANGEROUS), "screen must flag subprocess"
        assert llm_plugin.screen("open('x','w')"), "screen must flag write-open"
        assert llm_plugin.screen("eval('1')"), "screen must flag eval"
        assert llm_plugin.screen(BENIGN) == [], "benign code must be clean"
        print("ok: static screen flags dangerous, passes benign")

        # dangerous generation is rejected -- file never written / run
        out = llm_plugin.generate("evil", complete=reply(DANGEROUS), max_repairs=1)
        assert out is None, "dangerous plugin must be rejected"
        assert not os.path.exists(os.path.join(llm_plugin.PLUGIN_DIR, "plugin_evil.py"))
        print("ok: dangerous plugin rejected, never written")

        # benign plugin: passes, ran in the SUBPROCESS (its print is captured)
        m = llm_plugin.generate("a square-root check", complete=reply(BENIGN))
        assert m and m["tested"] and m["experimental"]
        assert os.path.exists(m["path"])
        res = llm_plugin.run_isolated(m["path"])
        assert res["ok"] and "PLUGIN_RAN_IN_SUBPROCESS" in res["stdout"]
        assert m in llm_plugin.loadable()
        # it ran in the child only -- never imported/exec'd in this process
        assert "plugin_under_test" not in sys.modules
        print("ok: benign plugin passes in an isolated subprocess (not in-process)")

        # erroring plugin: caught, returncode != 0, no crash, returns None
        bad = llm_plugin.generate("broken", complete=reply(ERRORING), max_repairs=1)
        assert bad is None
        # and run_isolated reports the failure cleanly on a written erroring file
        p = os.path.join(llm_plugin.PLUGIN_DIR, "err.py")
        with open(p, "w") as fh:
            fh.write(ERRORING)
        r = llm_plugin.run_isolated(p)
        assert not r["ok"] and r["returncode"] not in (0, None) and "boom" in r["stderr"]
        print("ok: erroring plugin caught (nonzero rc), app not crashed")

        print("PASS: plugin path opt-in + screened + isolated + never auto-run")
        return 0
    finally:
        llm_plugin.disable()
        llm_plugin.clear()
        llm_plugin.PLUGIN_DIR = saved_dir


if __name__ == "__main__":
    raise SystemExit(main())
