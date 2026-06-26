"""Narration captions -- wrap a spoken line into a few centred display lines.

Pure, Qt-free text helper for the accessibility "Narration captions" toggle: the
storyteller / guided-session / lecture narration speaks one line at a time, and
when captions are on the GUI shows that *full* line as on-screen text (the small
scene subtitle is otherwise truncated). This module just turns one sentence into
a short list of word-wrapped lines, eliding gracefully if a line is unusually
long so the caption never grows past a few rows. Offline + unit-testable.
"""
from __future__ import annotations


def wrap(text, width=42, max_lines=3):
    """Word-wrap ``text`` into at most ``max_lines`` lines of about ``width``
    characters each. Returns a list of stripped lines (possibly empty). If the
    text does not fit, the last kept line is elided with a trailing ellipsis so
    the caption stays a fixed, calm size on screen."""
    if not text:
        return []
    width = max(8, int(width))
    max_lines = max(1, int(max_lines))
    words = str(text).split()
    lines = []
    cur = ""
    for word in words:
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
        if len(lines) == max_lines:            # no more room -- elide and stop
            break
    if len(lines) < max_lines and cur:
        lines.append(cur)
    # A single over-long word (or a truncated overflow) gets a soft ellipsis.
    leftover = len(words) > sum(len(ln.split()) for ln in lines)
    if lines and (leftover or len(lines[-1]) > width):
        last = lines[-1]
        if len(last) > width - 1:
            last = last[:width - 1].rstrip()
        lines[-1] = last + "..."
    return lines


def caption_base_px(h, scale=1.0):
    """The caption font size (px) for a view *h* px tall, before any fit-to-width
    shrink. Scales with the view and with the accessibility UI text-size *scale*
    (so 'Large'/'Extra-large' enlarge the captions too), clamped to a calm range.
    Pure + testable."""
    base = max(13, min(22, int(h * 0.030)))
    return max(10, min(40, int(round(base * max(0.5, float(scale))))))


def paint_caption(p, w, h, lines, scale=1.0):
    """Draw wrapped caption *lines* as soft centred text on a faint rounded panel
    at the foot of the view -- restful in a dark room, yet kept **legible over any
    scene** (a soft drop-shadow behind each glyph, the standard subtitle technique,
    so the text stays readable even over a bright scene like Sunrise or the
    jellyfish glow -- captions are an accessibility feature, so legibility wins).
    Shared by every view that can show narration (the scene VizWidget and the
    talking-head FaceWidget) so captions look identical wherever they appear.
    *scale* is the accessibility UI text-size factor, so larger text sizes enlarge
    the caption too (still shrunk to fit a narrow view). Qt is imported lazily
    here, keeping ``wrap`` usable in pure contexts."""
    if not lines:
        return
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QFont
    from . import theme
    lines = list(lines)[:3]
    pad = 18
    margin = 16                                   # keep clear of the view edges
    avail = max(40, w - 2 * margin - 2 * pad)     # widest a caption line may be
    size = caption_base_px(h, scale)
    p.setFont(QFont("Helvetica Neue", size))
    fm = p.fontMetrics()
    tw = max((fm.horizontalAdvance(ln) for ln in lines), default=0)
    if tw > avail:                                # shrink to fit a narrow view
        size = max(10, int(size * avail / tw))
        p.setFont(QFont("Helvetica Neue", size))
        fm = p.fontMetrics()
        tw = max((fm.horizontalAdvance(ln) for ln in lines), default=0)
    lh = fm.height() + 4
    block_h = lh * len(lines)
    bottom = h - max(24, int(h * 0.06))
    top = bottom - block_h
    panel = QRectF((w - tw) / 2 - pad, top - pad / 2, tw + 2 * pad, block_h + pad)
    bg = QColor(theme.BG)
    bg.setAlphaF(0.55)                             # a touch more backing for legibility
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(bg)
    p.drawRoundedRect(panel, 10, 10)
    shadow = QColor("#04070d")                     # soft dark drop-shadow keeps the text
    shadow.setAlphaF(0.7)                          # readable over any scene (a11y)
    text = QColor(theme.TEXT)
    y = top
    for ln in lines:
        lw = fm.horizontalAdvance(ln)
        x, base = int((w - lw) / 2), int(y + fm.ascent())
        p.setPen(shadow)
        p.drawText(x + 1, base + 1, ln)
        p.setPen(text)
        p.drawText(x, base, ln)
        y += lh
