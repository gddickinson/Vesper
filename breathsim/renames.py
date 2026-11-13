"""Old display names -> current names, so saved settings keep working after a rename.

Sound and session names are also their IDs (settings, presets, soundscapes and mode
preferences store the name). When a name is changed (George, 2026-11-13: drop names that
sound like brain-state or sleep-depth claims) the old one is kept here as an alias:
:func:`canonical` maps a single name, :func:`migrate` rewrites any loaded JSON value.
Dependency-free so every module can import it.
"""
from __future__ import annotations

RENAMED = {
    "Slow-Wave Pulse": "Slow Swell",                    # texture "slowpulse"
    "Deep Sleep (Pink Noise)": "Pink Noise Swell",      # pink noise with a 0.8 Hz swell
    "Deeper Sleep": "Drifting Deeper",                  # guided sleep session (sleeptech)
}


def canonical(name):
    """The current name for ``name`` (unchanged when it was never renamed)."""
    if isinstance(name, str):
        return RENAMED.get(name, name)
    return name


def migrate(obj):
    """Return ``obj`` (parsed JSON) with every old name, as a value or a dict key,
    replaced by its current name. Only whole strings equal to an old name change."""
    if isinstance(obj, str):
        return RENAMED.get(obj, obj)
    if isinstance(obj, list):
        return [migrate(v) for v in obj]
    if isinstance(obj, dict):
        return {canonical(k): migrate(v) for k, v in obj.items()}
    return obj
