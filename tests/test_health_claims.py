"""Shipped content makes no health, medical or scientific-efficacy claims, and carries the disclaimer.

Scans everything a user can read -- pattern / voice / program / sound descriptions, lectures,
guided-session scripts, in-app text, the web pages, the iOS app's strings and lecture bundle,
README and INTERFACE.md -- for a list of banned claim phrases (George, 2026-11-12: "Soften or
remove all health claims, with disclaimers if kept"). History files (SESSION_LOG, UPDATES,
CHANGELOG) and the public-domain sample novel are not scanned.

If this fails: rewrite the phrase as a gentle description of the experience ("a slow, steady
rhythm many people find relaxing"), or remove it.
"""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from breathsim import disclaimer  # noqa: E402

BANNED = [
    "nervous system", "parasympathetic", "vagus", "vagal", "cortisol", "blood pressure",
    "immune", "heart rate variability", "heart-rate variability", "hrv sweet spot",
    "navy seal", "clinician", "clinically", "slow-wave (deep) sleep", "support slow-wave",
    "increase slow-wave", "increases slow-wave", "deepen slow-wave",
    "evidence-based", "evidence-grounded", "proven to", "clinically proven",
    "scientifically proven", "shown to support", "shown to shorten", "shown to increase",
    "shown to reduce", "shown to improve", "studies show", "research shows",
    "the research links", "first-line treatment", "insomnia treatment", "well-established",
    "measurably", "reliably increases", "fastest known", "fastest way back to calm",
    "melatonin-friendly", "reduces anxiety", "relieves anxiety", "treats anxiety",
    "cures insomnia", "lowers stress", "lower your blood", "boosts your immune",
]

SCAN_GLOBS = [
    "README.md", "INTERFACE.md", "ios/README.md",
    "breathsim/**/*.py", "vesper/**/*.py", "vesper/web/static/*.js",
    "vesper/web/static/*.html", "ios/Vesper/Vesper/**/*.swift",
    "ios/Vesper/Vesper/**/*.json",
]
SKIP_PARTS = {"__pycache__"}


def _files():
    seen = set()
    for g in SCAN_GLOBS:
        for f in ROOT.glob(g):
            if f.is_file() and not SKIP_PARTS & set(f.parts) and f not in seen:
                seen.add(f)
                yield f


def test_scan_covers_the_content():
    names = {f.relative_to(ROOT).as_posix() for f in _files()}
    for must in ("breathsim/patterns.py", "breathsim/voices.py", "breathsim/textures.py",
                 "breathsim/programs.py", "breathsim/sleeptech.py", "breathsim/lectures_touch.py",
                 "vesper/web/static/index.html", "ios/Vesper/Vesper/Core/Patterns.swift",
                 "ios/Vesper/Vesper/Content/lectures.json", "README.md"):
        assert must in names, must


def test_no_banned_claims():
    pat = re.compile("|".join(re.escape(b) for b in BANNED), re.IGNORECASE)
    hits = []
    for f in _files():
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in pat.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            hits.append(f"{f.relative_to(ROOT)}:{line}: {m.group(0)!r}")
    assert not hits, "health/efficacy claim phrases found:\n" + "\n".join(hits)


def test_registry_descriptions_clean():
    """The runtime text the apps show (pattern, voice, program and phrase descriptions)."""
    from breathsim import patterns, phrases, programs, voices
    progs = programs.PROGRAMS.values() if isinstance(programs.PROGRAMS, dict) else programs.PROGRAMS
    texts = [p.description for p in patterns.PRESETS]
    texts += [c.description for c in voices.all_configs()]
    texts += [p.description for p in progs]
    texts += [st.say for p in progs for st in p.stages]
    texts += [phrases.get(n).description for n in phrases.names() if phrases.get(n)]
    pat = re.compile("|".join(re.escape(b) for b in BANNED), re.IGNORECASE)
    assert texts and not [t for t in texts if pat.search(t)]


def _has_points(text):
    low = text.lower()
    return [k for k in disclaimer.KEY_PHRASES if k not in low]


def test_disclaimer_text_complete():
    assert not _has_points(disclaimer.TEXT)
    assert not _has_points(disclaimer.SHORT)


@pytest.mark.parametrize("path", ["README.md", "vesper/web/static/index.html"])
def test_disclaimer_shown(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    assert not _has_points(text), path


def test_web_footer_and_pages_use_the_shared_text():
    html = (ROOT / "vesper/web/static/index.html").read_text(encoding="utf-8")
    foot = re.search(r'<footer class="foot">(.*?)</footer>', html, re.S).group(1)
    assert disclaimer.SHORT in foot
    from vesper.web import catalog
    assert catalog.info()["disclaimer"] == list(disclaimer.POINTS)
    for page in ("breathe.js", "about.js"):
        assert "info.disclaimer" in (ROOT / "vesper/web/static" / page).read_text(encoding="utf-8")


def test_desktop_about_and_first_run_show_disclaimer():
    for mod in ("vesper/dialogs.py", "vesper/onboarding.py"):
        assert "disclaimer." in (ROOT / mod).read_text(encoding="utf-8"), mod
