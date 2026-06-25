"""Offline test for the Read-mode reading themes (read_pane THEMES + set_theme).

Night (dark, default), Sepia (warm paper) and Day (light) recolour the read-along
page and the per-theme sentence highlight; an unknown name falls back to Night.
Headless apart from the QWidget pane (no full window, no narration).
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402


class _StubWin:
    def toggle_reading(self):
        pass


def main():
    app = QApplication.instance() or QApplication([])
    from vesper.read_pane import THEME_NAMES, THEMES, ReadAlongPane

    assert THEME_NAMES == ["Night", "Sepia", "Day"], THEME_NAMES
    for name, vals in THEMES.items():
        assert len(vals) == 4 and all(isinstance(c, str) for c in vals), (name, vals)
    print("ok: THEMES has Night/Sepia/Day, each a 4-tuple of colours")

    pane = ReadAlongPane(_StubWin())
    assert pane._theme == "Night"                  # default
    night_hl = pane._hl_bg

    pane.set_theme("Sepia")
    assert pane._theme == "Sepia"
    assert (pane._hl_bg, pane._hl_fg) == THEMES["Sepia"][2:]
    assert THEMES["Sepia"][0] in pane.text.styleSheet()    # page bg applied
    assert pane._hl_bg != night_hl                 # highlight recoloured
    print("ok: set_theme('Sepia') recolours page + highlight")

    # a book + highlight, then switch -> the highlight re-applies (no stale colour)
    class _Book:
        title = "T"
        def sentences(self):
            return ["One.", "Two.", "Three."]
        def paragraph_starts(self):
            return [0]
    pane.set_book(_Book(), 0, 0)
    pane.highlight(1)
    assert pane._last_hl == 1
    pane.set_theme("Day")
    assert pane._theme == "Day" and pane._last_hl == 1   # re-highlighted in Day colours
    assert (pane._hl_bg, pane._hl_fg) == THEMES["Day"][2:]
    print("ok: switching theme re-highlights the current sentence")

    pane.set_theme("Nonsense")
    assert pane._theme == "Night"                  # unknown -> Night fallback
    print("ok: unknown theme falls back to Night")

    print("PASS: reading themes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
