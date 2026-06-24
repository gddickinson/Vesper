"""Sleep-timer auto-stop: gently fade the sound out, then pause, after N minutes.

Pure and unit-testable. The window keeps no second clock -- it passes the
session's elapsed seconds (since the timer was armed) into :func:`fade_gain`
each frame, which returns the master-volume multiplier and whether the timer has
finished (time to pause). The fade is a slow linear ramp over ``fade_seconds``
starting at the chosen mark, so the audio eases away rather than cutting out.

Honest: it just fades the volume and pauses transport -- nothing more.
"""
from __future__ import annotations

FADE_SECONDS = 30.0          # how long the gentle fade lasts once the mark is reached


def fade_gain(armed_minutes, elapsed_seconds, fade_seconds=FADE_SECONDS):
    """Return ``(gain, done)`` for a sleep timer.

    ``gain`` is the master-volume multiplier in [0, 1]; ``done`` is True once the
    fade has completed and the session should pause. With the timer off
    (``armed_minutes <= 0``) it is always ``(1.0, False)``.
    """
    if armed_minutes <= 0:
        return (1.0, False)
    mark = float(armed_minutes) * 60.0
    fade = max(1.0, float(fade_seconds))
    if elapsed_seconds < mark:
        return (1.0, False)
    if elapsed_seconds >= mark + fade:
        return (0.0, True)
    return (max(0.0, 1.0 - (elapsed_seconds - mark) / fade), False)


def remaining_seconds(armed_minutes, elapsed_seconds):
    """Seconds until the fade begins (0 once reached), or None if the timer is off."""
    if armed_minutes <= 0:
        return None
    return max(0.0, float(armed_minutes) * 60.0 - elapsed_seconds)


# Menu / picker options: label -> minutes (0 = off).
OPTIONS = [("Off", 0), ("15 min", 15), ("30 min", 30),
           ("45 min", 45), ("60 min", 60)]


def label_for(minutes):
    for lbl, m in OPTIONS:
        if m == int(minutes):
            return lbl
    return "Off"
