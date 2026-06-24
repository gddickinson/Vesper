"""Shared frame-loop constants, in a neutral module so window.py and the frame
mixin can both import them without a circular dependency."""
from __future__ import annotations

FPS = 40

# Talking takes precedence over breathing. A voiced frame means the storyteller
# is exhaling words; a gap means a breath before the next sentence.
_AMP_TH = 0.06          # narration amp above this counts as "voicing now"
_SPEAK_HOLD = 0.35      # s: short word/syllable gaps still count as speaking
_TALK_WINDOW = 9.0      # s of silence after which we revert to plain breathing
_BREATH_EASE = 0.08     # per-frame easing of the speech-driven visible breath
