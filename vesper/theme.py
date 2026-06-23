"""Qt palette + stylesheet, mirroring the breathsim night theme."""
from __future__ import annotations

BG = "#0a111e"
PANEL = "#0d1626"
CARD = "#121d31"
INPUT = "#192639"
BORDER = "#1f2e47"
TEXT = "#e9eef7"
MUTED = "#7b8da6"
FAINT = "#46566e"
ACCENT = "#69cfca"
ACCENT_DIM = "#2c5560"
ACCENT_WARM = "#b79ce0"
GLOW = "#ffffff"
GOOD = "#79d49a"        # in-tune green
OFFP = "#e0b46a"        # off-pitch amber

# Scene palettes.
NIGHT_BG = "#060a13"
MOON = "#eef1f8"
STAR = "#cfdcf2"
WATER = ["#1f4a72", "#163a5e", "#0f2a47"]
RIPPLE_BG = "#090f1e"

# Hue per breath phase (cool inhale → mint hold → lavender exhale → rest).
PHASE_HUE = {"inhale": "#69cfca", "hold_full": "#86e3c4",
             "exhale": "#b79ce0", "hold_empty": "#5b7fb0"}


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def blend(c1, c2, t):
    """Linear blend from *c1* (t=0) to *c2* (t=1)."""
    t = max(0.0, min(1.0, t))
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return rgb_to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def glow(hue, amount):
    """Lighten *hue* toward white — a cheap stand-in for a soft glow."""
    return blend(hue, GLOW, amount)


def phase_hue(phase):
    return PHASE_HUE.get(phase, ACCENT)

STYLESHEET = f"""
QWidget {{ background: {BG}; color: {TEXT}; font-size: 13px; }}
QFrame#card, QWidget#panel {{ background: {PANEL}; }}
QLabel {{ background: transparent; }}
QLabel#title {{ color: {ACCENT}; font-size: 15px; font-weight: 600; }}
QLabel#muted {{ color: {MUTED}; }}
QPushButton {{
    background: {CARD}; border: 1px solid {BORDER};
    padding: 7px 10px; border-radius: 6px;
}}
QPushButton:hover {{ background: #1a2740; }}
QPushButton:checked {{ background: {ACCENT}; color: {BG}; border-color: {ACCENT}; }}
QPushButton#accent {{ background: {ACCENT}; color: {BG}; border: none; }}
QComboBox {{ background: {INPUT}; border: 1px solid {BORDER}; padding: 4px 8px;
            border-radius: 5px; }}
QComboBox QAbstractItemView {{ background: {INPUT}; selection-background-color:
            {ACCENT}; selection-color: {BG}; }}
QSlider::groove:horizontal {{ background: {INPUT}; height: 5px; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {ACCENT}; width: 14px; margin: -5px 0;
            border-radius: 7px; }}
QCheckBox {{ background: transparent; }}
QStatusBar {{ background: {PANEL}; color: {MUTED}; }}
QMenuBar, QMenu {{ background: {PANEL}; color: {TEXT}; }}
QMenu::item:selected, QMenuBar::item:selected {{ background: {ACCENT}; color: {BG}; }}
"""
