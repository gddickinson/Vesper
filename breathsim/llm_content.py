"""Generate VALIDATED structured app content with the optional LLM -- no code.

When :func:`breathsim.llm.available`, these turn a plain-language request into the
app's own *data* objects, never code: a **breathing pattern**, a safe **breath
voice**, or a simple **mantra**. The model emits JSON; we treat it as UNTRUSTED:
parse, coerce every field against the real dataclasses/registries (clamp numeric
ranges into safe bounds, restrict enums, drop unknown fields), CONSTRUCT the
object, and -- for voices -- render a few blocks to confirm the audio is finite
and not clipping. Anything that still cannot be made valid is repaired by
re-prompting with the specific errors, then rejected (``None``).

Saved items go through the ordinary `store` paths (`save_pattern` / `save_voice`)
so they reload next run, with an **"AI: "** name prefix. Gated on
`llm.available()`; with no LLM the whole feature is absent and the app unaffected.
"""
from __future__ import annotations

import json
import re

import numpy as np

from . import llm, store, tracks, voices
from .patterns import BreathPattern, state_at

PREFIX = "AI: "
_NOISE = {"white", "pink", "brown"}
_FILT = {"bandpass", "lowpass", "highpass"}


def available():
    return llm.available()


def _gate(complete):
    comp = complete or (llm.complete if llm.available() else None)
    if comp is None:
        raise llm.LLMUnavailable(
            "This needs an LLM (set an API key or enable Ollama).")
    return comp


def _parse(text):
    if not isinstance(text, str):
        return None
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def _num(v, lo, hi, default):
    try:
        x = float(v)
    except Exception:
        return float(default)
    if not np.isfinite(x):
        return float(default)
    return max(lo, min(hi, x))


def _ascii(s):
    return str(s).encode("ascii", "ignore").decode("ascii")


def _prefixed(name):
    name = _ascii(name).strip() or "Untitled"
    return name if name.startswith(PREFIX) else PREFIX + name


# --- breathing pattern -----------------------------------------------------

def _pat_prompt(req, errors):
    p = ("Return ONLY JSON {\"name\":..., \"inhale\":..., \"hold_full\":..., "
         "\"exhale\":..., \"hold_empty\":..., \"description\":...} giving the four "
         "phase durations in SECONDS of a calming breathing pattern that " + str(req)
         + ". inhale 1-30, exhale 1-40, holds 0-30; total cycle 3-60s. Longer "
         "exhales are calming. ASCII only.")
    return ("Previous problems: " + "; ".join(errors) + ". Fix and return JSON only.\n"
            + p) if errors else p


def pattern(request, complete=None, max_repairs=2):
    comp = _gate(complete)
    errors = None
    for _ in range(int(max_repairs) + 1):
        d = _parse(comp(_pat_prompt(request, errors), max_tokens=400))
        if not d:
            errors = ["the reply was not valid JSON"]
            continue
        p = {"name": _prefixed(str(d.get("name") or request)[:40]),
             "inhale": _num(d.get("inhale"), 1, 30, 4),
             "hold_full": _num(d.get("hold_full"), 0, 30, 0),
             "exhale": _num(d.get("exhale"), 1, 40, 6),
             "hold_empty": _num(d.get("hold_empty"), 0, 30, 0),
             "description": _ascii(str(d.get("description") or "Custom pattern."))[:140]}
        cyc = p["inhale"] + p["hold_full"] + p["exhale"] + p["hold_empty"]
        if cyc < 3 or cyc > 60:
            errors = [f"total cycle {cyc:.0f}s should be 3-60"]
            continue
        try:
            BreathPattern(p["name"], p["inhale"], p["hold_full"], p["exhale"],
                          p["hold_empty"], p["description"])
        except Exception as e:
            errors = [str(e)]
            continue
        return p
    return None


def save_pattern(p):
    store.save_pattern(p)               # persists + patterns.add_pattern
    return p["name"]


# --- breath voice (restricted, safe whitelist) -----------------------------

def _voice_prompt(req, errors):
    p = ("Return ONLY JSON for a gentle breath/ambience voice that " + str(req)
         + ': {"name":..., "noise":"white|pink|brown", "filt":["bandpass|lowpass|'
         'highpass", centre_Hz, Q], "bright_base":Hz, "bright_mod":Hz, '
         '"exhale_mul":0.3-1.5, "gain":0.05-0.6, "width":0-1, "air":0-1, '
         '"description":...}. centre 80-12000 Hz, Q 0.3-8, bright 200-12000. Keep it '
         "soft (low gain). ASCII only.")
    return ("Previous problems: " + "; ".join(errors) + ". Fix and return JSON only.\n"
            + p) if errors else p


def _voice_dict(d):
    f = d.get("filt") or ["bandpass", 600, 1.0]
    if not isinstance(f, (list, tuple)) or not f:
        f = ["bandpass", 600, 1.0]
    ftype = str(f[0]).lower() if f else "bandpass"
    if ftype not in _FILT:
        ftype = "bandpass"
    noise = str(d.get("noise", "pink")).lower()
    return {"name": _prefixed(str(d.get("name") or "Voice")[:40]),
            "kind": "noise", "env": "airflow",
            "noise": noise if noise in _NOISE else "pink",
            "filt": (ftype, _num(f[1] if len(f) > 1 else 600, 80, 12000, 600),
                     _num(f[2] if len(f) > 2 else 1.0, 0.3, 8.0, 1.0)),
            "bright_base": _num(d.get("bright_base"), 200, 12000, 2000),
            "bright_mod": _num(d.get("bright_mod"), 0, 8000, 1200),
            "exhale_mul": _num(d.get("exhale_mul"), 0.3, 1.5, 0.85),
            "gain": _num(d.get("gain"), 0.05, 0.6, 0.45),
            "width": _num(d.get("width"), 0, 1, 0.2),
            "air": _num(d.get("air"), 0, 1, 0.0),
            "description": _ascii(str(d.get("description") or ""))[:140]}


def _render_ok(cfg, sr=22050):
    pat = BreathPattern("t", 4.0, 2.0, 6.0, 2.0)
    tr = tracks.build_track(cfg, sr)
    block, t, dt, peak = 2048, 0.0, 2048 / sr, 0.0
    for _ in range(48):
        out = tr.render(block, state_at(pat, t), state_at(pat, t + dt))
        if not np.all(np.isfinite(out)):
            return False, peak
        peak = max(peak, float(np.abs(out).max()))
        t += dt
    return True, peak


def voice(request, complete=None, max_repairs=2):
    comp = _gate(complete)
    errors = None
    for _ in range(int(max_repairs) + 1):
        d = _parse(comp(_voice_prompt(request, errors), max_tokens=500))
        if not d:
            errors = ["the reply was not valid JSON"]
            continue
        cfg = _voice_dict(d)
        try:
            vc = voices.VoiceConfig(group=voices.GROUP_CUSTOM, **cfg)
            finite, peak = _render_ok(vc)
        except Exception as e:
            errors = [str(e)]
            continue
        if not finite:
            errors = ["the voice produced non-finite audio"]
            continue
        if peak > 1.0:                                  # turn it down to be safe
            cfg["gain"] = max(0.03, cfg["gain"] * 0.9 / peak)
            try:
                vc = voices.VoiceConfig(group=voices.GROUP_CUSTOM, **cfg)
                _, peak = _render_ok(vc)
            except Exception:
                pass
            if peak > 1.0:
                errors = [f"voice too loud (peak {peak:.2f})"]
                continue
        return cfg
    return None


def save_voice(cfg):
    store.save_voice(cfg)               # persists + voices.register_from_dict
    return cfg["name"]


# --- simple mantra (validated text + tonic) --------------------------------

def _mantra_prompt(req, errors):
    p = ("Return ONLY JSON {\"name\":..., \"syllables\":[...], \"note\":\"C3\", "
         "\"description\":...} for a simple chant/mantra that " + str(req)
         + ". syllables = 1-12 short seed syllables (e.g. om, ma, ni, so, ham), "
         "lowercase letters only. note = a tonic like C3 or A2. ASCII only.")
    return ("Previous problems: " + "; ".join(errors) + ". Fix and return JSON only.\n"
            + p) if errors else p


def mantra(request, complete=None, max_repairs=2):
    from .music import note_to_hz
    comp = _gate(complete)
    errors = None
    for _ in range(int(max_repairs) + 1):
        d = _parse(comp(_mantra_prompt(request, errors), max_tokens=300))
        if not d:
            errors = ["the reply was not valid JSON"]
            continue
        raw = d.get("syllables")
        if not isinstance(raw, list) or not (1 <= len(raw) <= 12):
            errors = ["syllables must be a list of 1 to 12 short tokens"]
            continue
        syl = []
        for s in raw:
            t = re.sub(r"[^a-z]", "", _ascii(str(s)).strip().lower())
            if 1 <= len(t) <= 8:
                syl.append(t)
        if not syl:
            errors = ["each syllable must be 1 to 8 letters"]
            continue
        note = str(d.get("note", "C3")).strip()
        try:
            note_to_hz(note)
        except Exception:
            note = "C3"
        return {"name": _prefixed(str(d.get("name") or request)[:40]),
                "syllables": syl, "note": note,
                "description": _ascii(str(d.get("description") or ""))[:140]}
    return None


def save_mantra(m):
    store.save_ai_mantra(m)
    return m["name"]
