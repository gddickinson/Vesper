"""The native menu bar — the global escape hatch for every control.

Workspaces show a focused, per-mode set of cards; the menus expose everything
else, organised by intent:

* **File** — screenshots, exports, presets, quit.
* **Modes** — the six activities (mirrors the mode bar; reachable in Focus mode).
* **Sessions** — guided programs, multi-night courses, and one-tap quick starts.
* **Pattern / Voice / Sound** — the breath, the voice + morph, the audio mix.
* **Face** — everything about how the avatar / character looks.
* **View** — the visualization, reading aids, and window display.
* **Help** — welcome, library, stats, shortcuts, about.

Built by ``build`` and refreshed by ``app.rebuild_menu()``.
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
    _books(win, mb.addMenu("Books"))
    _pattern(win, mb.addMenu("Pattern"))
    _voice(win, mb.addMenu("Voice"))
    _sound(win, mb.addMenu("Sound"))
    _face(win, mb.addMenu("Face"))
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
    ex = m.addMenu("Export")                              # all exports in one place
    ex.addAction("Audio (WAV)…").triggered.connect(lambda: app_io.export_wav(win))
    from . import session_export
    ex.addAction("Session summary (text)…").triggered.connect(
        lambda: session_export.export_summary(win))
    ex.addAction("Summary card (PNG)…").triggered.connect(
        lambda: session_export.save_card(win))
    ex.addAction("Practice history (CSV)…").triggered.connect(
        lambda: app_io.export_history(win))
    m.addAction("Presets…").triggered.connect(lambda: presets.open_presets(win))
    m.addSeparator()
    q = m.addAction("Quit")
    q.setShortcut("Ctrl+Q")
    q.triggered.connect(win.close)


def _sessions(win, m):
    for name in programs.names():                         # guided multi-stage programs
        m.addAction(name).triggered.connect(
            lambda _c=False, x=name: win.start_session_mode(x))
    m.addSeparator()
    from breathsim import courses, store
    if courses.names():
        cm = m.addMenu("Courses (multi-night)")
        for cname in courses.names():
            c = courses.get(cname)
            day = store.course_day(cname)
            label = (f"{cname}  (complete)" if day >= c.total
                     else f"{cname}  ({c.unit} {day + 1}/{c.total})")
            cm.addAction(label).triggered.connect(
                lambda _c=False, x=cname: win.start_course_day(x))
            cm.addAction(f"    Restart {cname}").triggered.connect(
                lambda _c=False, x=cname: win.restart_course(x))
        m.addSeparator()
    qs = m.addMenu("Quick start")                         # one-tap starts
    qs.addAction("Sunrise (gentle wake-up)").triggered.connect(
        lambda: win.start_sunrise())
    qs.addAction("Fall asleep (one tap)").triggered.connect(
        lambda: win.start_fall_asleep())
    qs.addAction("Tonight's pick (random story)").triggered.connect(
        lambda: win.tonights_pick())
    from breathsim import lectures                        # "surprise me" within a branch
    surprise = qs.addMenu("Surprise me in branch")
    for cat in lectures.categories():
        surprise.addAction(cat).triggered.connect(
            lambda _c=False, x=cat: win.surprise_in_branch(x))
    m.addSeparator()
    m.addAction("One good thing (gratitude)…").triggered.connect(
        lambda: win.gratitude_now())
    m.addAction("Greet me by name…").triggered.connect(
        lambda: win.ask_listener_name())


def _books(win, m):
    """The audiobook / novels feature. The Reader narrates a public-domain or
    user-supplied book at a steady reading pace, with read-along text. Importing
    and downloading books arrive in later rounds."""
    from . import booklib, reader
    m.addAction("Read a book…").triggered.connect(lambda: reader.open_reader(win))
    m.addAction("Find & manage books…").triggered.connect(
        lambda: booklib.open_library(win))
    m.addAction("Import a book (file)…").triggered.connect(
        lambda: booklib.import_book_dialog(win))
    m.addSeparator()
    _toggle(m, "Dramatized (cast voices)", getattr(win, "_dramatize", False),
            win.set_dramatized)
    _toggle(m, "Expressive cast (daytime reading)",
            getattr(win, "_cast_expressive", False), win.set_cast_expressive)
    from . import cast as cast_mod
    m.addAction("Who's in this book…").triggered.connect(
        lambda: cast_mod.open_who_dialog(win))
    from breathsim import books
    n = len(books.list_books())
    info = m.addAction(f"In your library: {n}" if n else "Library is empty")
    info.setEnabled(False)


def _voice(win, m):
    from breathsim import store                           # quick-access favourites
    favs = [f for f in store.favourites() if voices.get_voice(f)]
    fm = m.addMenu("Favourites")
    if favs:
        _list_menu(fm, favs, win.set_voice_a)
    else:
        fm.addAction("(none yet - star a voice below)").setEnabled(False)
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
    auto = morph.addMenu("Automation")                   # morph drift over the session
    for mode in session.SessionDirector.MODES:
        auto.addAction(mode).triggered.connect(
            lambda _c=False, x=mode: win.start_session_mode(x))
    m.addSeparator()
    m.addAction("Voice Editor…").triggered.connect(
        lambda: voice_editor.open_editor(win))


def _pattern(win, m):
    m.addAction("Pattern Editor…").triggered.connect(
        lambda: pattern_editor.open_pattern_editor(win))
    _toggle(m, "Settle in (ease to your pace)", getattr(win, "_settle", False),
            win.set_settle)
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
    m.addSeparator()
    from breathsim import reverb
    spm = m.addMenu("Space (reverb)")                    # master room: Off..Cathedral
    spg = QActionGroup(spm); spg.setExclusive(True)
    cur_sp = win.engine.space_name()
    for nm in reverb.space_names():
        a = spm.addAction(nm); a.setCheckable(True); a.setChecked(nm == cur_sp)
        spg.addAction(a)
        a.triggered.connect(lambda _c=False, x=nm: win.set_space(x))
    m.addAction("High-quality voices (XTTS)…").triggered.connect(win.show_xtts_setup)
    _toggle(m, "Naturalness", win.controller.naturalness.amount > 1e-3,
            lambda on: win.set_naturalness(0.5 if on else 0.0, on))
    _toggle(m, "Spatial width (ambience)", getattr(win, "_spatial", True),
            win.set_spatial)
    _toggle(m, "Auto-rotate ambience", getattr(win, "_amb_rotate", False),
            win.set_ambience_rotate)
    _toggle(m, "Quiet hours (auto-soften late)", getattr(win, "_quiet_hours", True),
            win.set_quiet_hours)
    _toggle(m, "Breathing soundscape (bed swells with you)",
            getattr(win, "_breath_swell", False), win.set_breath_swell)
    m.addSeparator()
    _toggle(m, "Soundscape follows story", getattr(win, "_soundscape_follow", True),
            win.set_soundscape_follow)
    _toggle(m, "Backdrop follows the story", getattr(win, "_story_bg_follow", True),
            win.set_story_bg_follow)
    _toggle(m, "Mood check-ins", getattr(win, "_mood_on", False),
            win.set_mood_checkins)
    _toggle(m, "Bedtime gratitude (one good thing)",
            getattr(win, "_gratitude_on", False), win.set_gratitude)
    m.addSeparator()
    inst = m.addMenu("Ambience & instruments")           # all sound beds in one place
    _sub_list(inst, "Cosmic Music", voices.names(voices.GROUP_MUSIC), win.set_ambience)
    _sub_list(inst, "Bells & Gongs", voices.names(voices.GROUP_BELLS), win.set_ambience)
    _sub_list(inst, "Drums", voices.names(voices.GROUP_DRUMS), win.set_effect)
    _sub_list(inst, "Winds & Organs", voices.names(voices.GROUP_WIND), win.set_ambience)
    _sub_list(inst, "Environmental FX", voices.names(voices.GROUP_FX), win.set_ambience)
    from . import sleeptimer                              # fade out + pause after N min
    stm = m.addMenu("Sleep timer")
    for lbl, mins in sleeptimer.OPTIONS:
        a = stm.addAction(lbl)
        a.setCheckable(True)
        a.setChecked(int(getattr(win, "_sleep_timer_min", 0)) == mins)
        a.triggered.connect(lambda _c=False, x=mins: win.set_sleep_timer(x))
    m.addAction("Mixer…").triggered.connect(lambda: dialogs.open_mixer(win))


def _face(win, m):
    fb = m.addMenu("Face background")
    for name in face_bg.names():
        fb.addAction(name).triggered.connect(
            lambda _c=False, x=name: win.set_face_background(x))
    from . import face_styles                             # cyberpunk render styles
    fs = m.addMenu("Face style")
    cur = getattr(win, "_face_style", "Default")
    fsg = QActionGroup(fs); fsg.setExclusive(True)        # exclusive: the tick moves
    for st in face_styles._STYLES:
        a = fs.addAction(st.name if not st.desc else f"{st.name}  -  {st.desc}")
        a.setCheckable(True); a.setChecked(st.name == cur)
        fsg.addAction(a)
        a.triggered.connect(lambda _c=False, x=st.name: win.set_face_style(x))
    fs.setEnabled(win.face.faceview_available())          # 3D head only (cat ignores it)
    rx = _toggle(m, "Reactive face (story / breath / chant)",
                 getattr(win, "_face_reactive", False), win.set_face_reactive)
    rx.setEnabled(win.face.faceview_available())
    m.addSeparator()
    catf = m.addAction("Cartoon character face")
    catf.setCheckable(True)
    catf.setChecked(win.face.uses_cat())
    catf.setEnabled(win.face.faceview_available())        # otherwise it's always the cat
    catf.triggered.connect(lambda checked: win.set_face_cat(checked))
    win._act_cat = catf
    from . import characters                              # 2D cartoon cast + costumes
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
    _toggle(m, "Character voices", getattr(win, "_char_voices", True),
            win.set_character_voices)
    _toggle(m, "Character follows the story", getattr(win, "_story_char_follow", False),
            win.set_story_char_follow)


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
    wx = m.addMenu("Weather")                            # optional particle overlay
    for kind in scene_particles.KINDS:
        wx.addAction(kind.capitalize()).triggered.connect(
            lambda _c=False, x=kind: win.set_weather(x))
    m.addSeparator()
    from . import fontscale                               # accessibility: UI text size
    ts = m.addMenu("Text size")
    for lbl, scl in fontscale.OPTIONS:
        a = ts.addAction(lbl)
        a.setCheckable(True)
        a.setChecked(abs(getattr(win, "_font_scale", 1.0) - scl) < 1e-6)
        a.triggered.connect(lambda _c=False, x=scl: win.set_text_scale(x))
    _toggle(m, "Calm visuals (reduce motion)", getattr(win, "_calm_visuals", False),
            win.set_calm_visuals)
    _toggle(m, "Breathing count cue", getattr(win, "_coach", False),
            win.set_breath_coach)
    _toggle(m, "Settle-in lead-in", getattr(win, "_intro_on", True),
            win.set_intro_lead_in)
    _toggle(m, "Clock-aware light", getattr(win, "_clock_light", True),
            win.set_clock_light)
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
    m.addSeparator()
    from . import llm_settings                            # optional, opt-in AI assistant
    m.addAction("AI Assistant (optional)…").triggered.connect(
        lambda: llm_settings.open_llm_settings(win))
    m.addAction("About…").triggered.connect(lambda: dialogs.open_about(win))


# --- helpers --------------------------------------------------------------
def _modes():
    from breathsim import modes
    return modes.names()


def _toggle(menu, label, checked, fn):
    """A checkable menu action wired to a 1-arg setter. Returns the action."""
    a = menu.addAction(label)
    a.setCheckable(True)
    a.setChecked(bool(checked))
    a.toggled.connect(fn)
    return a


def _sub_list(menu, label, names, fn):
    """Add a submenu of *names* under *menu*, only if there are any."""
    if names:
        _list_menu(menu.addMenu(label), names, fn)


def _list_menu(menu, names, fn):
    for name in names:
        menu.addAction(name).triggered.connect(
            lambda _c=False, x=name: fn(x))
