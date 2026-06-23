"""Breath-amplitude envelopes shared by the vocal and synthetic tracks.

An *env mode* maps a :class:`~breathsim.patterns.BreathState` to a 0..1
amplitude. This is what makes even a synthetic timbre read as breathing: the
shape (two pulses per cycle, silent holds) is the breath signature.

Modes
-----
``airflow``     both in/exhale breath bumps, silent holds (natural breaths).
``volume``      swell with lung fullness (ambiences, drones).
``exhale``      active only on the exhale (chants, sighs, hisses).
``inhale``      active only on the inhale (sniffs, cooling breaths).
``breath``      both phases, each with its own attack and level (techniques
                with different in/out character, e.g. breath of fire).
``breath_both`` both phases, same smooth shape.
"""
from __future__ import annotations

import math

from .patterns import PHASE_EXHALE, PHASE_INHALE, BreathState


def _rc(p: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * p)


def window(phase: str, target: str, p: float, attack: str = "smooth") -> float:
    """A single-phase window with shaped attack (0 outside *target*)."""
    if phase != target:
        return 0.0
    if attack == "explosive":
        rise = 0.025
        return _rc(p / rise) if p < rise else math.exp(-(p - rise) * 5.5)
    if attack == "swell":                  # messa di voce: 0 -> 1 -> 0
        return math.sin(math.pi * p)
    edge = 0.16
    if p < edge:
        return _rc(p / edge)
    if p > 1.0 - edge:
        return _rc((1.0 - p) / edge)
    return 1.0


def envelope(env: str, state: BreathState, attack: str = "smooth",
             attack_in: str = "smooth", inhale_level: float = 1.0,
             exhale_level: float = 1.0) -> float:
    ph, p = state.phase, state.progress
    if env == "airflow":
        return state.airflow
    if env == "volume":
        return state.volume
    if env == "exhale":
        return window(ph, PHASE_EXHALE, p, attack)
    if env == "inhale":
        return window(ph, PHASE_INHALE, p, attack)
    if env == "breath":
        if ph == PHASE_INHALE:
            return inhale_level * window(ph, PHASE_INHALE, p, attack_in)
        if ph == PHASE_EXHALE:
            return exhale_level * window(ph, PHASE_EXHALE, p, attack)
        return 0.0
    if env == "breath_both":
        return max(window(ph, PHASE_INHALE, p, attack),
                   window(ph, PHASE_EXHALE, p, attack))
    return state.airflow
