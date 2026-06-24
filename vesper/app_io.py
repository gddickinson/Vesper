"""Offline WAV export of the current sound bed (File > Export Audio).

`export_wav(win)` asks for a path then renders `seconds` of the live layer set
(primary breath voice + ambience + effects) offline -- no audio device needed --
summed at the slot levels, soft-clipped at the master volume, written as 16-bit
WAV. Ported from the legacy gui/app_io.render_export, adapted to the Qt window API.
"""
from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import QFileDialog
from scipy.io import wavfile

from breathsim import dsp, tracks, voices


def render_export(win, path, seconds=30):
    eng, ctrl = win.engine, win.controller
    sr, block = eng.sr, 2048
    layers = []
    prim = eng._build_primary_track()
    if prim:
        layers.append((prim, eng.slot_levels.get("primary", 1.0)))
    for slot, dflt in (("ambience", 1.0), ("effects", 0.85)):
        nm = eng.slot_voice.get(slot)
        cfg = voices.get_voice(nm) if nm else None
        if cfg:
            layers.append((tracks.build_track(cfg, sr, eng.persona),
                           eng.slot_levels.get(slot, dflt)))
    vol = float(getattr(win, "user_volume", 0.6))
    out = []
    for b in range(max(1, int(seconds * sr / block))):
        t0 = b * block / sr
        s0 = ctrl.state_at(t0)
        s1 = ctrl.state_at(t0 + block / sr)
        mix = np.zeros((block, 2))
        for tr, lev in layers:
            mix += tr.render(block, s0, s1) * lev
        out.append(dsp.soft_clip(mix * vol))
    audio = np.concatenate(out) if out else np.zeros((1, 2))
    wavfile.write(path, sr, (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16))
    return path


def export_history(win):
    """Save the practice history as CSV (File menu). Never crashes the app."""
    path, _ = QFileDialog.getSaveFileName(
        win, "Export Practice History (CSV)", "vesper-history.csv",
        "CSV files (*.csv);;Text files (*.txt)")
    if not path:
        return
    try:
        from breathsim import history_export
        text = (history_export.history_text() if path.lower().endswith(".txt")
                else history_export.history_csv())
        with open(path, "w") as fh:
            fh.write(text)
        win.status.showMessage(f"Exported history to {path}", 4000)
    except Exception as exc:                            # never crash on export
        win.status.showMessage(f"Export failed: {exc}", 5000)


def export_wav(win, seconds=30):
    path, _ = QFileDialog.getSaveFileName(
        win, "Export Audio (WAV)", "breathing.wav", "WAV files (*.wav)")
    if not path:
        return
    try:
        render_export(win, path, seconds)
        win.status.showMessage(f"Exported {seconds}s to {path}", 4000)
    except Exception as exc:                       # never crash the app on export
        win.status.showMessage(f"Export failed: {exc}", 5000)
