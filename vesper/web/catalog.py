"""JSON views of the real Vesper/breathsim data for the web interface (no copies, no new content).

Only breath voices and ambience beds that the browser can synthesise faithfully are listed in
`voices()`: the filtered-noise voices (tracks.NoiseTrack) and three textures (Singing Bowl, Wind
Chimes, Slow-Wave Pulse). The vocal-tract, chant, narration and LLM features stay in the desktop app.
"""
from __future__ import annotations

from breathsim import disclaimer, lectures, modes, patterns, phrases, programs, voices

from .. import sleeptimer

WEB_TEXTURES = ("Singing Bowl", "Wind Chimes", "Slow-Wave Pulse")
CFG_KEYS = ("name", "group", "description", "kind", "noise", "filt", "bright_base", "bright_mod",
            "env", "floor", "gain", "width", "pan_rate", "pan_depth", "exhale_mul", "am_rate",
            "am_depth", "texture")


def _pattern(p) -> dict:
    return {"name": p.name, "inhale": p.inhale, "hold_full": p.hold_full, "exhale": p.exhale,
            "hold_empty": p.hold_empty, "description": p.description, "summary": p.summary(),
            "cycle": p.cycle, "bpm": 60.0 / p.cycle}


def pattern_list() -> list:
    return [_pattern(p) for p in patterns.PRESETS]


def _cfg(c) -> dict:
    d = voices.to_dict(c)
    out = {k: d[k] for k in CFG_KEYS}
    out["filt"] = list(out["filt"])
    return out


def voice_lists() -> dict:
    breath = [_cfg(c) for c in voices.all_configs()
              if c.group == voices.GROUP_BREATH and c.kind == "noise"]
    amb = [_cfg(c) for c in voices.all_configs()
           if c.group == voices.GROUP_NATURE and (c.kind == "noise" or c.name in WEB_TEXTURES)]
    return {"breath": breath, "ambience": amb, "total_voices": len(voices.all_configs())}


def _stage(s) -> dict:
    pat = s.settings.get("pattern")
    if isinstance(pat, (tuple, list)):
        durs, name = list(pat), "Stage"
    else:
        p = patterns.preset_by_name(pat) if pat else None
        durs, name = ([p.inhale, p.hold_full, p.exhale, p.hold_empty] if p else None), pat
    return {"title": s.title, "minutes": s.minutes, "say": s.say, "pattern": name,
            "durations": durs, "voice": s.settings.get("voice"),
            "ambience": s.settings.get("ambience"), "scene": s.settings.get("scene"),
            "phrase": s.settings.get("phrase")}


def program_list() -> list:
    return [{"name": p.name, "description": p.description, "minutes": p.total_minutes,
             "stages": [_stage(s) for s in p.stages]} for p in programs.PROGRAMS]


def mode_list() -> list:
    return [{"name": m.name, "description": m.description, "pattern": m.pattern, "voice": m.voice,
             "ambience": m.ambience, "effect": m.effect, "scene": m.scene, "volume": m.volume,
             "session": m.session, "sleep": list(m.sleep) if m.sleep else None}
            for m in modes.MODES]


def sleep_info() -> dict:
    sleep = modes.get("Sleep").sleep
    return {"options": [{"label": lbl, "minutes": m} for lbl, m in sleeptimer.OPTIONS],
            "fade_seconds": sleeptimer.FADE_SECONDS,
            "wind_down": {"seconds": sleep[0], "start": sleep[1], "end": sleep[2]}}


def info() -> dict:
    v = voice_lists()
    return {"title": "Vesper", "summary": "A breath-paced meditation & sleep companion.",
            "patterns": len(patterns.PRESETS), "programs": len(programs.PROGRAMS),
            "modes": len(modes.MODES), "voices": v["total_voices"],
            "web_breath_voices": len(v["breath"]), "web_ambiences": len(v["ambience"]),
            "lectures": len(lectures.names()), "branches": len(lectures.categories()),
            "phrases": len(phrases.names()), "disclaimer": list(disclaimer.POINTS)}
