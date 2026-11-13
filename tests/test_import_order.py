"""Every voice-registering module imports cleanly on its own, in a fresh interpreter.

Regression: ``import breathsim.textures`` before ``breathsim.voices`` used to raise a circular
ImportError (textures -> voices -> cosmic -> textures.register_generator, not defined yet).
The generator registry now lives in the dependency-free ``breathsim.texture_registry``.
Also checks that the registered voices are the same whichever module is imported first.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

FIRST = ["textures", "cosmic", "synth_bell", "synth_drum", "synth_wind", "synth_fx",
         "tracks", "voices", "texture_registry"]

_PROBE = """
import importlib, json, sys
importlib.import_module("breathsim." + sys.argv[1])
from breathsim import voices
print(json.dumps(sorted(c.name for c in voices.all_configs())))
"""


def _voices_after(first):
    r = subprocess.run([sys.executable, "-c", _PROBE, first], cwd=ROOT,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"import breathsim.{first} first failed:\n{r.stderr[-1500:]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def reference():
    return _voices_after("voices")


@pytest.mark.parametrize("first", FIRST)
def test_module_imports_first(first, reference):
    assert _voices_after(first) == reference


def test_texture_voices_render_after_textures_first():
    code = ("import breathsim.textures, numpy as np\n"
            "from breathsim import voices, tracks, patterns\n"
            "s0 = patterns.state_at(patterns.PRESETS[0], 0.0)\n"
            "s1 = patterns.state_at(patterns.PRESETS[0], 0.1)\n"
            "for n in ('Singing Bowl', 'Slow Swell', 'Music of the Spheres'):\n"
            "    t = tracks.build_track(voices.get_voice(n), 44100)\n"
            "    out = t.render(1024, s0, s1)\n"
            "    assert np.isfinite(out).all()\n"
            "print('ok')")
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True,
                       text=True, timeout=120)
    assert r.returncode == 0 and r.stdout.strip().endswith("ok"), r.stderr[-1500:]
