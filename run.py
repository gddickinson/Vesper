#!/usr/bin/env python3
"""Launch Vesper -- a breath-paced meditation / sleep companion (face-centred).

Self-contained: the audio/logic core is vendored at ./breathsim. Run:  python run.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vesper.window import launch

if __name__ == "__main__":
    launch()
