"""The native menu bar — the global escape hatch for every control.

Workspaces show a focused, per-mode set of cards; the menus expose everything
else (all modes, sessions/programs, every pattern, every voice + body + morph,
sound settings + background-sound toggles, view/zen, stats). Built by ``build``
and refreshed by ``app.rebuild_menu()``.
"""
from __future__ import annotations

from PySide6.QtGui import QActionGroup

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
    m.addAction("Export Practice History (CSV)…").triggered.connect(
        lambda: app_io.export_history(win))
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
    m.addAction("Tonight's pick (random story)").triggered.connect(
        lambda: win.tonights_pick())
    from breathsim import lectures                     # "surprise me" within one branch
    surprise = m.addMenu("Surprise me in branch")
    for cat in lectures.categories():
        surprise.addAction(cat).triggered.connect(
            lambda _c=False, x=cat: win.surprise_in_branch(x))
    m.addAction("Fall asleep (one tap)").triggered.connect(
        lambda: win.start_fall_asleep())


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
    from breathsim import reverb
    spm = m.addMenu("Space (reverb)")                  # master room: Off..Cathedral
    spg = QActionGroup(spm); spg.setExclusive(True)
    cur_sp = win.engine.space_name()
    for nm in reverb.space_names():
        a = spm.addAction(nm); a.setCheckable(True); a.setChecked(nm == cur_sp)
        spg.addAction(a)
        a.triggered.connect(lambda _c=False, x=nm: win.set_space(x))
    m.addAction("High-quality voices (XTTS)…").triggered.connect(win.show_xtts_setup)
    nat = m.addAction("Naturalness")
    nat.setCheckable(True)
    nat.setChecked(win.controller.naturalness.amount > 1e-3)
    nat.toggled.connect(lambda on: win.set_naturalness(0.5 if on else 0.0, on))
    ss = m.addAction("Soundscape follows story")
    ss.setCheckable(True)
    ss.setChecked(getattr(win, "_soundscape_follow", True))
    ss.toggled.connect(win.set_soundscape_follow)
    sbg = m.addAction("Backdrop follows the story")
    sbg.setCheckable(True)
    sbg.setChecked(getattr(win, "_story_bg_follow", True))
    sbg.toggled.connect(win.set_story_bg_follow)
    sp = m.addAction("Spatial width (ambience)")
    sp.setCheckable(True)
    sp.setChecked(getattr(win, "_spatial", True))
    sp.toggled.connect(win.set_spatial)
    ar = m.addAction("Auto-rotate ambience")
    ar.setCheckable(True)
    ar.setChecked(getattr(win, "_amb_rotate", False))
    ar.toggled.connect(win.set_ambience_rotate)
    qh = m.addAction("Quiet hours (auto-soften late)")
    qh.setCheckable(True)
    qh.setChecked(getattr(win, "_quiet_hours", True))
    qh.toggled.connect(win.set_quiet_hours)
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
    cc = m.addAction("Breathing count cue")          # on-screen in/hold/out counting
    cc.setCheckable(True)
    cc.setChecked(getattr(win, "_coach", False))
    cc.toggled.connect(win.set_breath_coach)
    il = m.addAction("Settle-in lead-in")            # gentle text over the first breath
    il.setCheckable(True)
    il.setChecked(getattr(win, "_intro_on", True))
    il.toggled.connect(win.set_intro_lead_in)
    cl = m.addAction("Clock-aware light")            # gentle time-of-day warmth
    cl.setCheckable(True)
    cl.setChecked(getattr(win, "_clock_light", True))
    cl.toggled.connect(win.set_clock_light)
    fb = m.addMenu("Face background")
    for name in face_bg.names():
        fb.addAction(name).triggered.connect(
            lambda _c=False, x=name: win.set_face_background(x))
    from . import face_styles                          # cyberpunk render styles
    fs = m.addMenu("Face style")
    cur = getattr(win, "_face_style", "Default")
    fsg = QActionGroup(fs)                              # exclusive: the tick moves
    fsg.setExclusive(True)
    for st in face_styles._STYLES:
        a = fs.addAction(st.name if not st.desc else f"{st.name}  -  {st.desc}")
        a.setCheckable(True)
        a.setChecked(st.name == cur)
        fsg.addAction(a)
        a.triggered.connect(lambda _c=False, x=st.name: win.set_face_style(x))
    fs.setEnabled(win.face.faceview_available())       # 3D head only (cat ignores it)
    rx = m.addAction("Reactive face (story / breath / chant)")
    rx.setCheckable(True)
    rx.setChecked(getattr(win, "_face_reactive", False))
    rx.setEnabled(win.face.faceview_available())
    rx.toggled.connect(win.set_face_reactive)
    catf = m.addAction("Cartoon cat face")
    catf.setCheckable(True)
    catf.setChecked(win.face.uses_cat())
    catf.setEnabled(win.face.faceview_available())   # otherwise it's always the cat
    catf.triggered.connect(lambda checked: win.set_face_cat(checked))
    win._act_cat = catf
    from . import characters                            # 2D cartoon cast + costumes
    chm = m.addMenu("Character")
    chg = QActionGroup(chm); chg.setExclusive(True)
    curch = getattr(win, "_character", "Cat")
    for nm in characters.names():
        a = chm.addAction(nm); a.setCheckable(True); a.setChecked(nm == curch)
        chg.addAction(a)
        a.triggered.connect(lambda _c=False, x=nm: win.set_character(x))
    csm = m.addMenu("Costume")
    cog = QActionGroup(csm); cog.setExclusive(True)
    curco = getattr(win, "_costume", "None")
    for nm in characters.costume_names():
        a = csm.addAction(nm); a.setCheckable(True); a.setChecked(nm == curco)
        cog.addAction(a)
        a.triggered.connect(lambda _c=False, x=nm: win.set_costume(x))
    cv = m.addAction("Character voices")               # each character its own voice
    cv.setCheckable(True)
    cv.setChecked(getattr(win, "_char_voices", True))
    cv.toggled.connect(win.set_character_voices)
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
    bk = m.addAction("Blackout (sleep)")
    bk.setShortcut("B")
    bk.triggered.connect(lambda: win.toggle_blackout())
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
