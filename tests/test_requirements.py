"""Regression: requirements.txt lists every third-party package the core imports.

breathsim/dsp.py imports scipy (and the README lists it), but requirements.txt
omitted it, so a fresh `pip install -r requirements.txt` could not run the app.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _listed():
    names = set()
    for line in (ROOT / "requirements.txt").read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            names.add(line.split(">")[0].split("=")[0].split("<")[0].strip().lower())
    return names


def test_scipy_listed_since_dsp_imports_it():
    assert "from scipy import" in (ROOT / "breathsim" / "dsp.py").read_text()
    assert "scipy" in _listed()


def test_core_packages_listed():
    assert {"numpy", "pyside6", "sounddevice", "soundfile"} <= _listed()
