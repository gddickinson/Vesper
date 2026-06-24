"""Accessibility: a global UI text-size scale.

Pure + testable. The window applies a chosen scale by (1) scaling the Qt
application font and (2) regenerating the theme stylesheet with its ``font-size``
values multiplied -- only font sizes are touched, so layout/geometry stay stable.
It is a readability setting, nothing more.
"""
from __future__ import annotations

import re

# Label -> scale factor (Normal = 1.0).
OPTIONS = [("Small", 0.85), ("Normal", 1.0), ("Large", 1.25),
           ("Extra-large", 1.5)]

_FONT_PX = re.compile(r"font-size:\s*(\d+)px")


def scaled_css(css, scale):
    """Return *css* with every ``font-size: Npx`` multiplied by *scale* (rounded).
    Only font sizes are changed; paddings, borders and widths are left alone."""
    if abs(float(scale) - 1.0) < 1e-6:
        return css
    return _FONT_PX.sub(
        lambda m: f"font-size: {max(1, round(int(m.group(1)) * scale))}px", css)


def label_for(scale):
    """The option label closest to *scale* (defaults to Normal)."""
    best, diff = "Normal", 1e9
    for lbl, s in OPTIONS:
        if abs(s - float(scale)) < diff:
            best, diff = lbl, abs(s - float(scale))
    return best


def scale_for(label):
    for lbl, s in OPTIONS:
        if lbl == label:
            return s
    return 1.0
