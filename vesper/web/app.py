"""FastAPI web app for Vesper: serves the front end in static/ and the JSON API under /api.

Run with `python run_web.py` (http://127.0.0.1:8216, local only). `scripts/build_static.py` exports every
path in STATIC_ENDPOINTS to JSON for the GitHub Pages site, so keep that list in step with the GET routes
below. All data comes from the real breathsim core (see catalog.py); the breath clock, sound synthesis and
timers run in the browser (static/*_engine.js, sound_worklet.js), tested against Python. No API keys, LLM,
voice-cloning or TTS calls are made by this server.
"""
from functools import lru_cache
from pathlib import Path

import vesper  # noqa: F401  (puts the project root on sys.path for breathsim)
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import catalog
from .reference import fixture

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Vesper")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/info")
def info():
    """Project summary and real counts for the home page."""
    return catalog.info()


@app.get("/api/patterns")
def patterns():
    """The breath-pattern library (breathsim.patterns.PRESETS)."""
    return catalog.pattern_list()


@app.get("/api/voices")
def voices():
    """Breath voices and ambience beds the browser can synthesise, with their synthesis settings."""
    return catalog.voice_lists()


@app.get("/api/programs")
def programs():
    """Guided multi-stage programs (breathsim.programs)."""
    return catalog.program_list()


@app.get("/api/modes")
def modes():
    """The desktop app's seven activity modes (breathsim.modes)."""
    return catalog.mode_list()


@app.get("/api/sleep")
def sleep():
    """Sleep-timer options, fade length and the Sleep-mode wind-down (vesper/sleeptimer.py, modes.py)."""
    return catalog.sleep_info()


@lru_cache(maxsize=1)
def _reference():
    return fixture()


@app.get("/api/reference")
def reference():
    """Python reference numbers (same as tests/fixtures) for the Python-vs-JavaScript page."""
    return _reference()


# GET paths (without the /api prefix) written to the static site as api/<path>.json.
STATIC_ENDPOINTS = ["/info", "/patterns", "/voices", "/programs", "/modes", "/sleep", "/reference"]
