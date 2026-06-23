"""Optional *naturalness*: small per-breath randomness for a human feel.

A perfectly repeating pacer can feel mechanical. With ``amount > 0`` each breath
cycle gets slightly different phase timing, depth and voice pitch/tone instead of
an identical repeat. The variation is a **deterministic function of the cycle
index** (a cheap integer hash -- no RNG state), so it is identical on every
thread and on every call within a cycle: the audio engine and the GUI stay in
lockstep and there are no clicks at cycle boundaries.

The user controls the overall ``amount`` (0..1) and which aspects vary
(``timing``, ``depth``, ``pitch``, ``tone``). The controller reads this to shape
each :class:`~breathsim.patterns.BreathState`; tracks read ``pitch_mod`` /
``tone_mod`` off that state.
"""
from __future__ import annotations

from dataclasses import dataclass

_MASK = 0xFFFFFFFF

# Per-target variation at amount = 1.0:
_PHASE_VAR = 0.30      # +-30% per phase length (re-normalised to keep tempo)
_DEPTH_VAR = 0.35      # up to -35% breath depth (never deeper than full)
_PITCH_VAR = 0.6       # +- ~0.6 semitone on voiced sounds
_TONE_VAR = 0.30       # +-30% brightness on breath sounds


def _hash01(seed: int, k: int, i: int) -> float:
    """Deterministic pseudo-random float in 0..1 from integer coordinates."""
    h = (seed * 2654435761 + (k + 1) * 40503 + (i + 1) * 2246822519) & _MASK
    h ^= h >> 15
    h = (h * 2246822519) & _MASK
    h ^= h >> 13
    h = (h * 3266489917) & _MASK
    h ^= h >> 16
    return h / float(_MASK)


def _signed(seed: int, k: int, i: int) -> float:
    return _hash01(seed, k, i) * 2.0 - 1.0          # -1..1


@dataclass
class Naturalness:
    amount: float = 0.0
    timing: bool = True
    depth: bool = True
    pitch: bool = True
    tone: bool = True
    seed: int = 1

    @property
    def on(self) -> bool:
        return self.amount > 1e-3 and (self.timing or self.depth
                                       or self.pitch or self.tone)

    def phase_factors(self, k: int):
        """Per-cycle multipliers for the four phase durations (>0)."""
        a = self.amount * _PHASE_VAR
        return [max(0.15, 1.0 + a * _signed(self.seed, k, i)) for i in range(4)]

    def depth_factor(self, k: int) -> float:
        """Per-cycle breath-depth scale in [1 - amount*VAR, 1]."""
        return 1.0 - self.amount * _DEPTH_VAR * _hash01(self.seed, k, 4)

    def pitch_mod(self, k: int) -> float:
        """Per-cycle pitch offset in semitones for voiced sounds."""
        return self.amount * _PITCH_VAR * _signed(self.seed, k, 5)

    def tone_mod(self, k: int) -> float:
        """Per-cycle brightness multiplier for breath sounds (~1.0)."""
        return 1.0 + self.amount * _TONE_VAR * _signed(self.seed, k, 6)
