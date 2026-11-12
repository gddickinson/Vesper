"""Web interface tests: every exported endpoint answers, the static build is complete, and the JS engine tests pass.

Run: python -m pytest -q tests/test_web.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vesper.web.app import STATIC, STATIC_ENDPOINTS, app  # noqa: E402

client = TestClient(app)


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200 and "static/main.js" in r.text


@pytest.mark.parametrize("path", STATIC_ENDPOINTS)
def test_endpoint(path):
    r = client.get("/api" + path)
    assert r.status_code == 200, r.text
    assert r.json() is not None


def test_static_build(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_static
    build_static.build(tmp_path / "site")
    assert (tmp_path / "site" / "index.html").read_text().count("APP_STATIC") == 1
    for path in STATIC_ENDPOINTS:
        assert (tmp_path / "site" / "api" / (path.strip("/") + ".json")).exists()


def test_static_assets_referenced_exist():
    html = (STATIC / "index.html").read_text()
    for name in ("style.css", "main.js"):
        assert f"static/{name}" in html and (STATIC / name).exists()


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_js_engine():
    tests = sorted(STATIC.glob("*.test.mjs"))
    for t in tests:
        r = subprocess.run(["node", str(t)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr


# --- Vesper-specific -------------------------------------------------------------------------------

FIXTURES = ROOT / "tests" / "fixtures"


def _close(a, b, path="$"):
    """Recursive comparison with a tolerance (libm differs in the last digit between macOS and Linux)."""
    if isinstance(b, dict):
        assert isinstance(a, dict) and a.keys() == b.keys(), path
        for k in b:
            _close(a[k], b[k], f"{path}.{k}")
    elif isinstance(b, list):
        assert isinstance(a, list) and len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            _close(x, y, f"{path}[{i}]")
    elif isinstance(b, float) and not isinstance(b, bool):
        assert a == pytest.approx(b, rel=1e-9, abs=1e-12), path
    else:
        assert a == b, path


def test_fixtures_are_current():
    """The node tests compare against these; regenerate with python scripts/make_js_fixtures.py."""
    import json

    from vesper.web.catalog import voice_lists
    from vesper.web.reference import fixture
    _close(json.loads(json.dumps(fixture())), json.loads((FIXTURES / "vesper_reference.json").read_text()))
    _close(json.loads(json.dumps(voice_lists())), json.loads((FIXTURES / "web_voices.json").read_text()))


def test_info_counts_come_from_the_core():
    from breathsim import lectures, patterns, programs
    info = client.get("/api/info").json()
    assert info["patterns"] == len(patterns.PRESETS) == len(client.get("/api/patterns").json())
    assert info["programs"] == len(programs.PROGRAMS)
    assert info["lectures"] == len(lectures.names())


def test_patterns_match_presets():
    from breathsim import patterns
    rows = client.get("/api/patterns").json()
    for row, p in zip(rows, patterns.PRESETS):
        assert row["name"] == p.name and row["summary"] == p.summary()
        assert [row["inhale"], row["hold_full"], row["exhale"], row["hold_empty"]] == \
            [p.inhale, p.hold_full, p.exhale, p.hold_empty]
        assert row["bpm"] == pytest.approx(60 / p.cycle)


def test_web_voices_are_ones_the_worklet_can_synthesise():
    v = client.get("/api/voices").json()
    assert v["breath"] and v["ambience"]
    for cfg in v["breath"] + v["ambience"]:
        if cfg["kind"] == "texture":
            assert cfg["texture"] in ("bowl", "chimes", "slowpulse")
        else:
            assert cfg["kind"] == "noise" and cfg["filt"][0] in ("lowpass", "highpass", "bandpass")
            assert cfg["noise"] in ("white", "pink", "brown")


def test_programs_resolve_every_stage_pattern():
    for prog in client.get("/api/programs").json():
        for st in prog["stages"]:
            if st["pattern"] is not None:
                assert st["durations"] and len(st["durations"]) == 4, (prog["name"], st["title"])


def test_sleep_info_matches_sleeptimer_and_sleep_mode():
    from breathsim import modes
    from vesper import sleeptimer
    s = client.get("/api/sleep").json()
    assert [(o["label"], o["minutes"]) for o in s["options"]] == sleeptimer.OPTIONS
    assert s["fade_seconds"] == sleeptimer.FADE_SECONDS
    assert tuple(s["wind_down"].values()) == modes.get("Sleep").sleep


def test_no_llm_or_keys_in_web_layer():
    """LLM / TTS features stay in the desktop app: the web layer never imports them or mentions keys."""
    web = ROOT / "vesper" / "web"
    for f in list(web.glob("*.py")) + list((web / "static").glob("*.js")):
        text = f.read_text().lower()
        for bad in ("import llm", "llm_keys", "kokoro_tts", "xtts_", "anthropic", "api_key", "x-api-key"):
            assert bad not in text, (f.name, bad)
