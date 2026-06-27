#!/usr/bin/env python3
"""Render Vesper's app icon (a soft glowing breath-orb under a crescent moon, on
a night ground) to the iOS asset catalog. Run from the repo root:

    python ios/tools/make_icon.py

Needs Pillow. Writes a 1024x1024 PNG + updates the AppIcon Contents.json.
"""
from __future__ import annotations

import json
import math
import os

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ICONSET = os.path.join(ROOT, "ios", "Vesper", "Vesper",
                       "Resources", "Assets.xcassets", "AppIcon.appiconset")
S = 1024


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def main() -> None:
    img = Image.new("RGB", (S, S), (11, 16, 24))
    px = img.load()
    top, bot = (16, 22, 36), (7, 10, 17)
    for y in range(S):
        c = lerp(top, bot, y / S)
        for x in range(S):
            px[x, y] = c

    # soft mint glow orb
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy, r = S * 0.5, S * 0.56, S * 0.27
    mint = (134, 230, 191)
    for i in range(60, 0, -1):
        rr = r * (1 + i * 0.02)
        a = int(5 + (60 - i) * 0.7)
        gd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=mint + (a,))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"), (0, 0))

    d = ImageDraw.Draw(img, "RGBA")
    # core orb (radial-ish via stacked ellipses)
    for i in range(int(r), 0, -2):
        t = i / r
        col = lerp((180, 245, 220), (60, 150, 120), t)
        a = int(255 * (1 - t * 0.15))
        d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=col + (a,))

    # soft top highlight (blurred so it reads as a sheen, not a blob)
    hl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hr = r * 0.34
    hd.ellipse([cx - hr, cy - r * 0.5, cx + hr * 0.4, cy - r * 0.05],
               fill=(255, 255, 255, 70))
    img = Image.alpha_composite(img.convert("RGBA"),
                                hl.filter(ImageFilter.GaussianBlur(26))).convert("RGB")

    # crescent moon top-right — carve the bite out on a transparent layer so the
    # night sky shows through (no opaque dark disc)
    mx, my, mr = S * 0.72, S * 0.26, S * 0.105
    moonL = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    md = ImageDraw.Draw(moonL)
    md.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(245, 230, 173, 240))
    off = mr * 0.62
    md.ellipse([mx - mr + off, my - mr - off * 0.35,
                mx + mr + off, my + mr - off * 0.35], fill=(0, 0, 0, 0))
    img = Image.alpha_composite(img.convert("RGBA"), moonL).convert("RGB")

    # a few stars
    d = ImageDraw.Draw(img, "RGBA")
    for sx, sy, ss in [(0.2, 0.2, 4), (0.32, 0.13, 3), (0.85, 0.5, 3), (0.15, 0.42, 2)]:
        d.ellipse([S*sx-ss, S*sy-ss, S*sx+ss, S*sy+ss], fill=(230, 235, 245, 200))

    os.makedirs(ICONSET, exist_ok=True)
    out = os.path.join(ICONSET, "AppIcon-1024.png")
    img.save(out)
    with open(os.path.join(ICONSET, "Contents.json"), "w") as fh:
        json.dump({
            "images": [{"idiom": "universal", "platform": "ios",
                        "size": "1024x1024", "filename": "AppIcon-1024.png"}],
            "info": {"author": "xcode", "version": 1},
        }, fh, indent=2)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


if __name__ == "__main__":
    main()
