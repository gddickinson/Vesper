"""The native menu bar — the global escape hatch for every control.

Workspaces show a focused, per-mode set of cards; the menus expose everything
else (all modes, sessions/programs, every pattern, every voice + body + morph,
sound settings + background-sound toggles, view/zen, stats). Built by ``build``
and refreshed by ``app.rebuild_menu()``.
"""
from __future__ import annotations

from breathsim import patterns, personas, programs, session, voices

from . import (app_io, dialogs, face_bg, onboarding, pattern_editor, presets,
               scenes, shortcuts, voice_editor)

_VOICE_GROUPS = (voices.GROUP_BREATH, voices.GROUP_CAT, voices.GROUP_VOCAL,
                 voices.GROUP_TECHNIQUE, voices.GROUP_SING, voices.GROUP_EXERCISE,
                 voices.GROUP_SYNTH, voices.GROUP_CUSTOM)


def build(win):
    mb = win.menuBar()
    mb.clear()
    _file(win, mb.addMenu("File"))
    _list_menu(mb.addMenu("Modes"), _modes(), win.apply_mode)
    _sessions(win, mb.addMenu("Sessions"))
    _pattern(win, mb.addMenu("Pattern"))
    _voice(win, mb.addMenu("Voice"))
    _sound(win, mb.addMenu("Sound"))
    _view(win, mb.addMenu("View"))
    _help(win, mb.addMenu("Help"))


# --- builders -------------------------------------------------------------
def _file(win, m):
    a = m.addAction("Save Screenshot")
    a.setShortcut("Ctrl+S")
    a.triggered.connect(lambda: win.save_screenshot())
    f = m.addAction("Save Face Only")
    f.setShortcut("Ctrl+Shift+S")
    f.triggered.connect(lambda: win.save_screenshot(face_only=True))
    m.addSeparator()
    m.addAction("Presets…").triggered.connect(lambda: presets.open_presets(win))
    m.addAction("Export Audio (WAV)…").triggered.connect(
        lambda: app_io.export_wav(win))
    from . import session_export                       # a small practice summary
    m.addAction("Export Session Summary…").triggered.connect(
        lambda: session_export.export_summary(win))
    m.addAction("Save Summary Card (PNG)…").triggered.connect(
        lambda: session_export.save_card(win))
    m.addSeparator()
    q = m.addAction("Quit")
    q.setShortcut("Ctrl+Q")
    q.triggered.connect(win.close)


def _sessions(win, m):
    for mode in session.SessionDirector.MODES:
        m.addAction(mode).triggered.connect(
            lambda _c=False, x=mode: win.start_session_mode(x))
    m.addSeparator()
    for name in programs.names():
        m.addAction(name).triggered.connect(
            lambda _c=False, x=name: win.start_session_mode(x))
    m.addSeparator()
    from breathsim import courses, store
    if courses.names():
        cm = m.addMenu("Courses (multi-night)")
        for cname in courses.names():
            c = courses.get(cname)
            day = store.course_day(cname)
            if day >= c.total:
                label = f"{cname}  (complete)"
            else:
                label = f"{cname}  ({c.unit} {day + 1}/{c.total})"
            cm.addAction(label).triggered.connect(
                lambda _c=False, x=cname: win.start_course_day(x))
            cm.addAction(f"    Restart {cname}").triggered.connect(
                lambda _c=False, x=cname: win.restart_course(x))
    m.addSeparator()
    m.addAction("Sunrise (gentle wake-up)").triggered.connect(
        lambda: win.start_sunrise())


def _voice(win, m):
    from breathsim import store                        # quick-access favourites
    favs = [f for f in store.favourites() if voices.get_voice(f)]
    fm = m.addMenu("Favourites")
    if favs:
        _list_menu(fm, favs, win.set_voice_a)
    else:
        none = fm.addAction("(none yet - star a voice below)")
        none.setEnabled(False)
    cur = win.engine.voice_a
    if cur:
        starred = store.is_favourite(cur)
        m.addAction(f"{'Unstar' if starred else 'Star'} \"{cur}\"").triggered.connect(
            lambda: win.toggle_favourite_voice())
    m.addSeparator()
    va = m.addMenu("Inhale voice")
    for g in _VOICE_GROUPS:
        names = voices.names(g)
        if names:
            _list_menu(va.addMenu(g), names, win.set_voice_a)
    _list_menu(m.addMenu("Exhale voice"),
               ["Same as inhale"] + voices.names(voices.GROUP_BREATH),
               win.set_voice_out)
    _list_menu(m.addMenu("Voice body"), personas.names(), win.set_persona)
    morph = m.addMenu("Morph A▸B")
    vb = morph.addMenu("Voice B")
    for g in voices.MORPHABLE:
        names = voices.names(g)
        if names:
            _list_menu(vb.addMenu(g), names, win.set_voice_b)
    morph.addSeparator()
    for label, amt in (("A only (0%)", 0.0), ("Blend (50%)", 0.5),
                       ("B only (100%)", 1.0)):
        morph.addAction(label).triggered.connect(
            lambda _c=False, a=amt: win.set_morph_manual(a))
    m.addSeparator()
    m.addAction("Voice Editor…").triggered.connect(
        lambda: voice_editor.open_editor(win))


def _pattern(win, m):
    m.addAction("Pattern Editor…").triggered.connect(
        lambda: pattern_editor.open_pattern_editor(win))
    m.addSeparator()
    _list_menu(m, [p.name for p in patterns.PRESETS], win.set_pattern)


def _sound(win, m):
    mute = m.addAction("Mute")
    mute.setCheckable(True)
    mute.toggled.connect(win.set_muted)
    win._act_mute = mute
    bg = m.addMenu("Background sounds")
    for slot, label in (("primary", "Breathing"), ("ambience", "Ambience"),
                        ("effects", "Heartbeat & effects")):
        a = bg.addAction(label)
        a.setCheckable(True)
        a.setChecked(True)
        a.toggled.connect(lambda on, s=slot: win.toggle_layer(s, on))
    chime = m.addAction("Transition chime")
    chime.setCheckable(True)
    chime.setChecked(getattr(win.engine, "chime_enabled", True))
    chime.toggled.connect(win.engine.set_chime)
    nat = m.addAction("Naturalness")
    nat.setCheckable(True)
    nat.setChecked(win.controller.naturalness.amount > 1e-3)
    nat.toggled.connect(lambda on: win.set_naturalness(0.5 if on else 0.0, on))
    ss = m.addAction("Soundscape follows story")
    ss.setCheckable(True)
    ss.setChecked(getattr(win, "_soundscape_follow", True))
    ss.toggled.connect(win.set_soundscape_follow)
    sp = m.addAction("Spatial width (ambience)")
    sp.setCheckable(True)
    sp.setChecked(getattr(win, "_spatial", True))
    sp.toggled.connect(win.set_spatial)
    mood = m.addAction("Mood check-ins")
    mood.setCheckable(True)
    mood.setChecked(getattr(win, "_mood_on", False))
    mood.toggled.connect(win.set_mood_checkins)
    m.addSeparator()
    music = voices.names(voices.GROUP_MUSIC)        # generative cosmic music beds
    if music:
        _list_menu(m.addMenu("Cosmic Music"), music, win.set_ambience)
    bells = voices.names(voices.GROUP_BELLS)         # bells / bowls / gongs (tolling)
    if bells:
        _list_menu(m.addMenu("Bells & Gongs"), bells, win.set_ambience)
    drums = voices.names(voices.GROUP_DRUMS)         # rhythmic drum layers (effects slot)
    if drums:
        _list_menu(m.addMenu("Drums"), drums, win.set_effect)
    wind = voices.names(voices.GROUP_WIND)           # organs / reed drones / horns
    if wind:
        _list_menu(m.addMenu("Winds & Organs"), wind, win.set_ambience)
    fx = voices.names(voices.GROUP_FX)               # trains / ship / storm / buoy
    if fx:
        _list_menu(m.addMenu("Environmental FX"), fx, win.set_ambience)
    m.addSeparator()
    from . import sleeptimer                              # fade out + pause after N min
    stm = m.addMenu("Sleep timer")
    for lbl, mins in sleeptimer.OPTIONS:
        a = stm.addAction(lbl)
        a.setCheckable(True)
        a.setChecked(int(getattr(win, "_sleep_timer_min", 0)) == mins)
        a.triggered.connect(lambda _c=False, x=mins: win.set_sleep_timer(x))
    m.addSeparator()
    m.addAction("Mixer…").triggered.connect(lambda: dialogs.open_mixer(win))


def _view(win, m):
    vf = m.addAction("Show face")
    vf.setCheckable(True)
    vf.triggered.connect(lambda: win.set_view("face"))
    vs = m.addAction("Show scene  (V to toggle)")
    vs.setCheckable(True)
    vs.triggered.connect(lambda: win.set_view("scene"))
    win._act_face, win._act_scene = vf, vs
    sc = m.addMenu("Scene")
    for name in scenes.names():
        sc.addAction(name.capitalize()).triggered.connect(
            lambda _c=False, x=name: win.set_scene(x))
    from . import scene_particles
    wx = m.addMenu("Weather")                        # optional particle overlay
    for kind in scene_particles.KINDS:
        wx.addAction(kind.capitalize()).triggered.connect(
            lambda _c=False, x=kind: win.set_weather(x))
    from . import fontscale                           # accessibility: UI text size
    ts = m.addMenu("Text size")
    for lbl, sc in fontscale.OPTIONS:
        a = ts.addAction(lbl)
        a.setCheckable(True)
        a.setChecked(abs(getattr(win, "_font_scale", 1.0) - sc) < 1e-6)
        a.triggered.connect(lambda _c=False, x=sc: win.set_text_scale(x))
    cl = m.addAction("Clock-aware light")            # gentle time-of-day warmth
    cl.setCheckable(True)
    cl.setChecked(getattr(win, "_clock_light", True))
    cl.toggled.connect(win.set_clock_light)
    fb = m.addMenu("Face background")
    for name in face_bg.names():
        fb.addAction(name).triggered.connect(
            lambda _c=False, x=name: win.set_face_background(x))
    catf = m.addAction("Cartoon cat face")
    catf.setCheckable(True)
    catf.setChecked(win.face.uses_cat())
    catf.setEnabled(win.face.faceview_available())   # otherwise it's always the cat
    catf.triggered.connect(lambda checked: win.set_face_cat(checked))
    win._act_cat = catf
    m.addSeparator()
    hg = m.addAction("Hourglass timer")
    hg.setCheckable(True)
    hg.setChecked(getattr(win, "_hg_show", False))
    hg.triggered.connect(lambda checked: win.toggle_hourglass(checked))
    win._act_hourglass = hg
    m.addSeparator()
    z = m.addAction("Focus mode (Zen)")
    z.setShortcut("Z")
    z.triggered.connect(lambda: shortcuts.toggle_zen(win))
    f = m.addAction("Fullscreen")
    f.setShortcut("F")
    f.triggered.connect(lambda: shortcuts.toggle_fullscreen(win))
    reflect_view(win)


def reflect_view(win):
    f, s = getattr(win, "_act_face", None), getattr(win, "_act_scene", None)
    if f is not None:
        f.setChecked(win._view == "face")
    if s is not None:
        s.setChecked(win._view == "scene")


def _help(win, m):
    m.addAction("Welcome / Getting Started…").triggered.connect(
        lambda: onboarding.open_onboarding(win))
    m.addSeparator()
    m.addAction("Story Library…").triggered.connect(
        lambda: dialogs.open_story_library(win))
    m.addAction("Practice Stats…").triggered.connect(
        lambda: dialogs.open_stats(win))
    m.addAction("Keyboard Shortcuts…").triggered.connect(
        lambda: dialogs.open_shortcuts(win))
    m.addAction("About…").triggered.connect(lambda: dialogs.open_about(win))


# --- helpers --------------------------------------------------------------
def _modes():
    from breathsim import modes
    return modes.names()


def _list_menu(menu, names, fn):
    for name in names:
        menu.addAction(name).triggered.connect(
            lambda _c=False, x=name: fn(x))
