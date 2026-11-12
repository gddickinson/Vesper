"""The one safety / not-medical-advice text, shared by every surface.

Used by the desktop About dialog and first-run welcome (``vesper.dialogs`` /
``vesper.onboarding``), the CBT-I sleep-program dialog (``SLEEP_PROGRAM_NOTE``), the web
API (``vesper.web.catalog.info``, shown on the Breathe and About pages) and, as ``SHORT``,
the web page footer. README.md quotes ``POINTS``. ``tests/test_health_claims.py`` checks
each surface still carries the key points (``KEY_PHRASES``).
"""
from __future__ import annotations

TITLE = "Please breathe gently"

POINTS = (
    "Vesper is for relaxation only. It is not a medical device and not medical advice.",
    "Breathe gently and comfortably. Stop and breathe normally if you feel dizzy, "
    "light-headed or uncomfortable.",
    "If you have a health condition, talk to a doctor or other qualified professional "
    "before trying breathing exercises.",
    "Patterns with breath holds or fast, forceful breathing are not suitable during "
    "pregnancy or for people with heart or respiratory (breathing) conditions.",
    "Never use Vesper while driving, operating machinery, or anywhere it is unsafe to "
    "become drowsy.",
)

TEXT = " ".join(POINTS)

# One line for the web page footer (plain ASCII-safe text, no markup).
SHORT = ("For relaxation only, not medical advice. Stop if you feel dizzy or uncomfortable. "
         "Talk to a professional if you have a health condition. Breath-hold and fast-breathing "
         "patterns are not for pregnancy or heart or respiratory conditions. "
         "Never use while driving.")

# Shown in the CBT-I-style sleep program dialog, under the main disclaimer.
SLEEP_PROGRAM_NOTE = (
    "A self-guided routine tool, not medical treatment. A shorter sleep window can make you "
    "sleepier during the day: do not drive or operate machinery if you feel drowsy. If sleep "
    "problems go on, or you have a health condition or are pregnant, talk to a doctor first.")

# Phrases every disclaimer surface must contain (case-insensitive).
KEY_PHRASES = ("not medical advice", "dizzy", "professional", "pregnan", "heart",
               "respiratory", "driving")
