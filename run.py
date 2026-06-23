#!/usr/bin/env python3
"""Launch the PySide6 rebuild of Breathing Sim (face-centred).

Reuses the audio/logic core from ../breathing_sim. Run:  python run.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bsqt.window import launch

if __name__ == "__main__":
    launch()
