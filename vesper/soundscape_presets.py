"""Save / recall a light, sound-only mix (a 'soundscape').

Unlike the full Presets system (pattern + voice + persona + scene...), this just
captures the current sound layers: the ambience and effect voices + their levels,
master volume, and the spatial / auto-rotate flags. `capture(win)` reads them
into a plain dict (store-able as JSON); `apply(win, mix)` sets them back, reusing
the normal setters and skipping any voice that is no longer in the registry.
It just stores names + levels -- no claims.
"""
from __future__ import annotations

from breathsim import voices


def capture(win):
    eng = win.engine
    return {
        "ambience": eng.slot_voice.get("ambience"),
        "ambience_level": float(eng.slot_levels.get("ambience", 0.8)),
        "effect": eng.slot_voice.get("effects"),
        "effect_level": float(eng.slot_levels.get("effects", 0.85)),
        "volume": float(getattr(win, "user_volume", 0.6)),
        "spatial": bool(getattr(win, "_spatial", True)),
        "rotate": bool(getattr(win, "_amb_rotate", False)),
    }


def _known(name):
    return bool(name) and voices.get_voice(name) is not None


def apply(win, mix):
    """Restore a saved mix. Unknown/missing voices are skipped (left as-is)."""
    if not mix:
        return
    amb = mix.get("ambience")
    if amb in (None, "", "None"):
        win.set_ambience("None")
    elif _known(amb):
        win.set_ambience(amb)                         # else: unknown -> skip
    if "ambience_level" in mix:
        win.set_slot_level("ambience", float(mix["ambience_level"]))
    eff = mix.get("effect")
    if eff in (None, "", "None"):
        win.set_effect("None")
    elif _known(eff):
        win.set_effect(eff)
    if "effect_level" in mix:
        win.set_slot_level("effects", float(mix["effect_level"]))
    if "volume" in mix:
        win.set_volume(float(mix["volume"]))
    if "spatial" in mix:
        win.set_spatial(bool(mix["spatial"]))
    if "rotate" in mix:
        win.set_ambience_rotate(bool(mix["rotate"]))
