"""Apply one guided-program ``Stage`` to the Qt app.

The ``SessionDirector`` calls ``app.apply_stage(stage)`` at each stage boundary.
A stage only specifies the keys it wants to change; everything else is left
untouched. Mirrors the Tk app's stage_apply (minus the canvas/scene, which the Qt
face handles via the breath state).
"""
from __future__ import annotations

from breathsim import choir, personas, phrases
from breathsim.patterns import BreathPattern, preset_by_name


def apply_stage(app, stage):
    d, eng = stage.settings, app.engine
    if "pattern" in d:
        pat = d["pattern"]
        if isinstance(pat, (tuple, list)):
            app.controller.change_pattern(BreathPattern("Stage", *pat))
        else:
            p = preset_by_name(pat)
            if p:
                app.controller.change_pattern(p)
    if "persona" in d:
        eng.set_persona(personas.get(d["persona"]))
    if "phrase" in d:
        eng.set_phrase(phrases.get(d["phrase"]))
        eng.set_chant_style(d.get("chant_style", "per_breath"))
    elif "voice" in d:
        eng.set_voice_a(d["voice"])
        eng.set_voice_out(d.get("voice_out"))
    if "ambience" in d:
        eng.set_voice(d["ambience"], "ambience")
    if "effect" in d:
        eng.set_layer("effects", d["effect"],
                      level=eng.slot_levels.get("effects", 0.85))
    if "cue_style" in d:
        app.speech.set_style(d["cue_style"])
    if "volume" in d:
        app.set_volume(d["volume"])
    if "choir" in d:
        ch = d["choir"]
        if ch and ch[0] and ch[0] != "None":
            choir.apply(eng, *ch)
        else:
            choir.clear(eng)
    app._scene_hint = d.get("scene", app._scene_hint)
    # Reflect the new state in whatever workspace widgets are visible.
    app.panel.sync()
