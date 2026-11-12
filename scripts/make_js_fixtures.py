"""Write tests/fixtures/vesper_reference.json (and web_voices.json, the voice recipes): numbers from the real Python core (breath clock,
naturalness, envelopes, DSP filters, struck textures, wind-down, settle-in, sleep timer) that the
node tests (vesper/web/static/*.test.mjs) compare the JavaScript port against.

Run after changing breathsim/patterns.py, naturalness.py, controller.py, envelopes.py, dsp.py,
textures.py, session.py, vesper/sleeptimer.py or vesper/web/reference.py:
    python scripts/make_js_fixtures.py
tests/test_web.py fails if the committed fixture is out of date.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vesper.web.catalog import voice_lists  # noqa: E402
from vesper.web.reference import fixture  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "vesper_reference.json"
VOICES = ROOT / "tests" / "fixtures" / "web_voices.json"


def dumps(data) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=True)


def main():
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(dumps(fixture()))
    VOICES.write_text(dumps(voice_lists()))
    for f in (FIXTURE, VOICES):
        print(f"wrote {f} ({f.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
