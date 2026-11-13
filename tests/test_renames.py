"""Renamed sounds / sessions keep working under their old names (saved settings, presets).

George, 2026-11-13: "Slow-Wave Pulse" -> "Slow Swell", "Deep Sleep (Pink Noise)" -> "Pink Noise
Swell", "Deeper Sleep" -> "Drifting Deeper" (iOS also renames its pulse / 528 / 432 Hz beds).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from breathsim import renames, sleeptech, stories, voices  # noqa: E402


def test_new_names_registered_and_old_names_resolve():
    for old, new in renames.RENAMED.items():
        assert renames.canonical(old) == new
        if new == sleeptech.NAME_DEEPER:
            assert sleeptech.has(old) and sleeptech.has(new)
            assert stories.ambience_for(old) == stories.ambience_for(new) == "Pink Noise Swell"
            assert next(sleeptech.units(old, guidance=False)) == \
                next(sleeptech.units(new, guidance=False))       # (units() never ends)
        else:
            assert voices.get_voice(new) is not None, new
            assert voices.get_voice(old) is voices.get_voice(new)
    assert voices.get_voice("Slow Swell").texture == "slowpulse"   # ID unchanged
    assert renames.canonical("Brown Noise") == "Brown Noise"


def test_migrate_rewrites_saved_json():
    saved = {"ambience": "Slow-Wave Pulse", "story": "Deeper Sleep", "volume": 0.5,
             "mix": {"Deep Sleep (Pink Noise)": 0.4, "Gentle Rain": 0.2},
             "presets": [{"ambience": "Deep Sleep (Pink Noise)"}],
             "note": "Slow-Wave Pulse was nice"}
    out = renames.migrate(saved)
    assert out["ambience"] == "Slow Swell" and out["story"] == "Drifting Deeper"
    assert out["mix"] == {"Pink Noise Swell": 0.4, "Gentle Rain": 0.2}
    assert out["presets"][0]["ambience"] == "Pink Noise Swell"
    assert out["note"] == "Slow-Wave Pulse was nice"          # only whole names change
    assert out["volume"] == 0.5


def test_store_reads_migrate(tmp_path, monkeypatch):
    from breathsim import store
    monkeypatch.setattr(store, "DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text(json.dumps({"ambience": "Slow-Wave Pulse"}))
    assert store._read("settings.json", {}) == {"ambience": "Slow Swell"}


def test_ios_aliases_cover_every_rename():
    amb = (ROOT / "ios/Vesper/Vesper/Audio/Ambience.swift").read_text(encoding="utf-8")
    names = set(re.findall(r'AmbienceVoice\(name: "([^"]+)"', amb))
    pairs = dict(re.findall(r'"([^"]+)": "([^"]+)",\s*// legacy name', amb))
    assert set(pairs) == {"Theta Pulse (6 Hz)", "Delta Pulse (2.5 Hz)", "Solfeggio 528 Hz",
                          "Solfeggio 432 Hz", "Deep Sleep (Pink Noise)"}
    assert set(pairs.values()) <= names and not set(pairs) & names
    vm = (ROOT / "ios/Vesper/Vesper/UI/SessionViewModel.swift").read_text(encoding="utf-8")
    assert "AmbienceVoice.canonical(" in vm and "SleepAids.canonical(" in vm
    aids = (ROOT / "ios/Vesper/Vesper/UI/SleepAids.swift").read_text(encoding="utf-8")
    assert '"Deeper Sleep": "Drifting Deeper"' in aids and "switch canonical(name)" in aids
