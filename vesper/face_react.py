"""Map the live session context to a face style + breath glow, for the optional
**reactive face**. Pure + testable: the window calls these each frame (only when
the reactive toggle is on) and applies the result with light smoothing so the
look shifts gently rather than flickering.

- ``style_for(mode, ...)`` picks a fitting cyberpunk style from the current
  activity (mode), whether a chant/song is voicing, and the storyteller's mood.
- ``pulse_for(volume)`` turns the lung volume (0..1) into a gentle glow pulse so
  the face breathes with the user (brighter on the in-breath).
It never changes the saved style; the window restores that when the toggle is off.
"""
from __future__ import annotations

# Storyteller mood bucket -> the Sleep style that suits it.
_SLEEP_MOOD = {"calm": "Nebula", "wonder": "Aurora", "warm": "Solar",
               "tense": "Void"}

# Mode -> reactive style. Meditate keeps the classic face (it just breathes via
# the glow pulse); the others take on a fitting cyberpunk look.
_MODE = {"Meditate": "Default", "Breathwork": "Tron", "Chant": "Sonar",
         "Sing": "Plasma", "Relax": "Nebula", "Sleep": "Nebula"}


def style_for(mode, chanting=False, singing=False, story_active=False,
              mood="calm"):
    """The reactive style name for the current context."""
    if singing:
        return "Plasma"                       # voice work: vivid plasma
    if chanting:
        return "Sonar"                        # chant: rings pulse with the voice
    if mode == "Sleep" and story_active:
        return _SLEEP_MOOD.get(mood, "Nebula")
    return _MODE.get(mode, "Default")


def pulse_for(volume):
    """Breath glow (0.84..1.20) from the lung *volume* (0..1): the face brightens
    a touch on the in-breath and softens on the out-breath. 1.0 would be no change."""
    v = max(0.0, min(1.0, float(volume)))
    return 0.84 + 0.36 * v


def mood_key(mood_target):
    """A coarse mood bucket from the eased emotion tuple (smile, brow, eye_bias)
    the storyteller sets per line. Pure; tolerant of a missing/short tuple."""
    try:
        ds, db, do = (list(mood_target) + [0.0, 0.0, 0.0])[:3]
    except TypeError:
        return "calm"
    if db > 0.12:
        return "wonder"
    if ds > 0.12:
        return "warm"
    if do < -0.06:
        return "tense"
    return "calm"
