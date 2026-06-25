"""Offline test for the searchable picker (vesper/picker.py + picker_sources.py).

Covers the pure group sources (story_groups / voice_groups), the picker's
normalisation + first-visible-leaf helpers, and PickerButton's combo-duck-typed
state (current_value / set_value / is_open) that control_panel sync relies on.
The dialog's own exec loop isn't driven here (a PNG render + the offscreen GUI
smoke cover that); this stays headless apart from one QPushButton subclass.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication  # noqa: E402


def main():
    app = QApplication.instance() or QApplication([])

    from vesper import picker
    from vesper.picker_sources import story_groups, voice_groups

    # story groups: scenes + branches, every header a str, every value a str
    sg = story_groups()
    headers = [h for h, _ in sg]
    assert "General" in headers and "Scenes" in headers
    assert any("Grasslands" in h for h in headers), headers
    items = [v for _, vals in sg for v in vals]
    assert "The Serengeti" in items and "Off" in items
    assert len(items) > 200, len(items)         # the whole long story list
    print(f"ok: story_groups -> {len(sg)} groups, {len(items)} items")

    # voice groups: families; exhale variant prepends 'Same as inhale'
    vg = voice_groups()
    assert vg and all(isinstance(h, str) and vals for h, vals in vg)
    vgs = voice_groups(include_same=True)
    assert vgs[0] == ("General", ["Same as inhale"])
    print(f"ok: voice_groups -> {len(vg)} families (+General for exhale)")

    # _norm accepts bare values and (value, label) tuples
    norm = picker._norm([("G", ["a", ("b", "Bee")])], str)
    assert norm == [("G", [("a", "a"), ("b", "Bee")])], norm
    print("ok: _norm handles bare values and (value, label) tuples")

    # PickerButton duck-types the combo slice sync uses
    picked = {}
    btn = picker.PickerButton("Deep Calm", lambda: vg,
                              lambda v: picked.__setitem__("v", v),
                              title="Voice")
    assert btn.current_value() == "Deep Calm" and not btn.is_open()
    assert "Deep Calm" in btn.text()
    btn.set_value("Nose Breath")                 # what sync calls
    assert btn.current_value() == "Nose Breath" and "Nose Breath" in btn.text()
    assert picked == {}                          # set_value does NOT fire on_pick
    # empty value shows the placeholder
    btn2 = picker.PickerButton(None, lambda: vg, None, empty="Off")
    assert "Off" in btn2.text()
    print("ok: PickerButton current_value/set_value/is_open + placeholder")

    print("PASS: searchable picker")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
