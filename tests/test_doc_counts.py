"""The counts quoted in README.md and CLAUDE.md match the code (regenerate with scripts/doc_counts.py)."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6")   # the cartoon-cast registry is part of the Qt package

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import doc_counts  # noqa: E402


def test_doc_counts_current():
    stale = doc_counts.apply(write=False)
    assert not stale, "run: python scripts/doc_counts.py\n" + "\n".join(stale)
