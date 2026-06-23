"""Per-mode panel layout: which control cards each mode presents.

The mode bar is the primary navigation; selecting a mode rebuilds the side panel
into a distinct, purpose-built set of cards (mirrors the Tk app's workspaces).
Each entry lists card-builder keys (resolved to methods on the ControlPanel) plus
optional curated lists. ``get`` falls back to a sensible default.
"""
from __future__ import annotations

# card keys map to ControlPanel._card_<key> builders.
WORKSPACES = {
    "Meditate":   {"cards": ["pattern", "pace", "bell", "voice", "naturalness",
                             "cues"]},
    "Breathwork": {"cards": ["pattern", "retention", "programs", "voice", "cues"]},
    "Chant":      {"cards": ["phrase", "pitch", "choir", "voice"]},
    "Sing":       {"cards": ["pitch", "voice", "choir", "naturalness"]},
    "Relax":      {"cards": ["soundscape", "pattern", "voice"]},
    "Sleep":      {"cards": ["story", "winddown", "soundscape"]},
}

_DEFAULT = {"cards": ["pattern", "voice", "cues"]}


def get(name: str) -> dict:
    return WORKSPACES.get(name, _DEFAULT)


def names() -> list[str]:
    return list(WORKSPACES.keys())
