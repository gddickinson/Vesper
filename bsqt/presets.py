"""Presets manager: save / load / delete full app presets.

A *preset* captures the whole audio+visual state (pattern, voice A/B/out, morph,
persona, ambience, effect, scene, cue style, volume, session length, slot levels).
`capture(win, name)` reads the live engine/controller/view; `apply(win, d)` routes
the dict back through the window's action methods. Persisted via
`store.presets_list / save_preset / delete_preset`. `open_presets(win)` is the dialog.
"""
from __future__ import annotations

from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLineEdit, QListWidget,
                               QPushButton, QVBoxLayout)

from breathsim import store
from breathsim.patterns import BreathPattern

from .widgets import muted


def capture(win, name):
    eng, ctrl = win.engine, win.controller
    p = ctrl.pattern
    return {
        "name": name,
        "pattern": {"name": p.name, "inhale": p.inhale, "hold_full": p.hold_full,
                    "exhale": p.exhale, "hold_empty": p.hold_empty},
        "voice_a": eng.voice_a, "voice_b": eng.voice_b, "voice_out": eng.voice_out,
        "morph": eng.morph, "persona": eng.persona.name,
        "ambience": eng.slot_voice.get("ambience"),
        "effect": eng.slot_voice.get("effects"),
        "scene": win.viz.scene_name(), "cue_style": win.speech.style,
        "volume": win.user_volume, "session": ctrl.session_seconds,
        "levels": dict(eng.slot_levels),
    }


def apply(win, d):
    eng, ctrl = win.engine, win.controller
    pat = d.get("pattern", {})
    ctrl.change_pattern(BreathPattern(
        pat.get("name", "Custom"), pat.get("inhale", 4), pat.get("hold_full", 0),
        pat.get("exhale", 4), pat.get("hold_empty", 0)))
    eng.slot_levels.update(d.get("levels", {}))
    if d.get("persona"):
        win.set_persona(d["persona"])
    win.set_voice_b(d.get("voice_b"))            # B before A (morph target ready)
    win.set_voice_a(d.get("voice_a"))
    win.set_voice_out(d.get("voice_out"))
    win.set_ambience(d.get("ambience"))
    win.set_effect(d.get("effect"))
    win.set_morph_manual(d.get("morph", 0.0))
    win.set_cue_style(d.get("cue_style", "Off"))
    win.set_volume(d.get("volume", 0.6))
    ctrl.session_seconds = d.get("session", 0.0)
    win.set_scene(d.get("scene", "orb"))
    win.current_mode = None                       # a manual override, not a mode
    win.panel.sync()


def open_presets(win):
    dlg = QDialog(win)
    dlg.setWindowTitle("Presets")
    dlg.setStyleSheet(win.styleSheet())
    dlg.resize(360, 430)
    lay = QVBoxLayout(dlg)
    lay.addWidget(muted("Saved presets (double-click to load)"))
    lst = QListWidget()
    lay.addWidget(lst, 1)

    def refresh():
        lst.clear()
        for p in store.presets_list():
            lst.addItem(p.get("name", "?"))

    def selected():
        it = lst.currentItem()
        return it.text() if it else None

    def do_load():
        nm = selected()
        d = store.preset_by_name(nm) if nm else None
        if d:
            apply(win, d)
            win.rebuild_menu()
            win.status.showMessage(f"Loaded preset '{nm}'", 3000)

    def do_delete():
        nm = selected()
        if nm:
            store.delete_preset(nm)
            refresh()

    def do_save():
        nm = name.text().strip() or "Preset"
        store.save_preset(capture(win, nm))
        name.clear()
        refresh()
        win.status.showMessage(f"Saved preset '{nm}'", 3000)

    refresh()
    lst.itemDoubleClicked.connect(lambda *_: do_load())

    row = QHBoxLayout()
    name = QLineEdit()
    name.setPlaceholderText("Name to save current settings")
    save = QPushButton("Save current")
    save.clicked.connect(do_save)
    row.addWidget(name, 1)
    row.addWidget(save)
    lay.addLayout(row)

    row2 = QHBoxLayout()
    load = QPushButton("Load")
    load.setObjectName("accent")
    load.clicked.connect(do_load)
    dele = QPushButton("Delete")
    dele.clicked.connect(do_delete)
    close = QPushButton("Close")
    close.clicked.connect(dlg.accept)
    row2.addWidget(load, 1)
    row2.addWidget(dele)
    row2.addWidget(close)
    lay.addLayout(row2)
    dlg.exec()
