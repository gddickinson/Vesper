"""Web interface for Vesper (FastAPI server + plain ES-module front end, no build step).

app.py        routes under /api and STATIC_ENDPOINTS (exported to JSON for GitHub Pages)
catalog.py    JSON views of the real breathsim data: patterns, voices, programs, modes, sleep timer
reference.py  Python reference numbers the JavaScript port is tested against (tests/fixtures)
static/       the front end: breath clock, DSP and session engines ported to JS, the audio
              worklet, canvas scenes and one module per page

Run: python run_web.py (http://127.0.0.1:8216). No LLM, voice or TTS feature is exposed here:
those stay in the desktop app.
"""
