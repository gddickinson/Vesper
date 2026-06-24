"""A gentle "pick up where you left off" launch line.

Pure + unit-testable: `resume_hint(settings)` takes the saved-settings dict
(as :func:`breathsim.store.load_settings` returns) and returns a calm one-line
reminder of the last session -- e.g. "Last time: Sleep with 'The Alhambra'" or
"Welcome back to Meditate" -- or ``None`` when there is nothing meaningful to
resume. It is only a reminder of your last session: no advice, no claims.
"""
from __future__ import annotations


def resume_hint(settings):
    """A friendly reminder of the last session, or ``None`` if there is none."""
    if not isinstance(settings, dict):
        return None
    mode = settings.get("mode")
    if not isinstance(mode, str) or not mode.strip():
        return None
    mode = mode.strip()
    scene = settings.get("last_scene")
    scene = scene.strip() if isinstance(scene, str) else ""
    if mode == "Sleep" and scene and scene.lower() != "off":
        return f"Last time: Sleep with \"{scene}\"."
    return f"Welcome back to {mode}."
