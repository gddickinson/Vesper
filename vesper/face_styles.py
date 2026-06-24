"""Cyberpunk face styles for the 3D head: a named combination of an eye pattern,
a skin treatment and a render mode (+ an accent colour).

Pure data, no GPU import, so it stays testable. The integer ids MUST match the
GLSL switches in :mod:`vesper.face_shaders`. The renderer (:mod:`face_gpu`) reads
the chosen style off ``params._style`` each frame; "Default" reproduces the
classic starry-eyed blue avatar exactly. Styles are offered as a user choice and
can also be driven by the storyteller / breath / chant for animated moods.
"""
from __future__ import annotations

from dataclasses import dataclass

# --- eye pattern ids (match face_shaders eye_pattern() switch) --------------
EYE_STARFIELD = 0    # the default deep-space twinkle
EYE_NEBULA = 1       # drifting coloured cloud + stars
EYE_PLASMA = 2       # neon energy plasma
EYE_CIRCUIT = 3      # HUD reticle: rings + ticks + a scanning sweep
EYE_MATRIX = 4       # falling code rain
EYE_SOLAR = 5        # molten radial corona
EYE_VOID = 6         # black-hole core + bright accretion ring (breath-friendly)
EYE_IRIS = 7         # mechanical camera aperture blades
EYE_HOLO = 8         # holographic horizontal scanlines
EYE_SONAR = 9        # expanding pulse rings (chant / breath friendly)

# --- skin treatment ids (match face_shaders skin_shade() switch) ------------
SKIN_SMOOTH = 0      # the default soft lambert + fresnel
SKIN_CHROME = 1      # polished metallic
SKIN_NEON = 2        # dark body, bright fresnel rim-light
SKIN_CIRCUIT = 3     # glowing PCB traces
SKIN_HOLO = 4        # tinted scanline hologram
SKIN_IRIDESCENT = 5  # oil-slick fresnel hue shift
SKIN_MATTE = 6       # desaturated dark
SKIN_GRID = 7        # Tron grid lines

# --- render modes (handled by face_gpu GL state) ----------------------------
MODE_SOLID = 0
MODE_WIRE = 1        # wireframe (triangle edges)
MODE_DOTS = 2        # point cloud / dot matrix
MODE_GHOST = 3       # translucent fresnel hologram


@dataclass(frozen=True)
class FaceStyle:
    name: str
    eye: int = EYE_STARFIELD
    skin: int = SKIN_SMOOTH
    mode: int = MODE_SOLID
    accent: tuple = (0.30, 0.85, 1.0)        # cyber-cyan
    desc: str = ""


# Curated, all futuristic/cyberpunk. "Default" is first and unchanged.
_STYLES = [
    FaceStyle("Default", desc="the classic starry-eyed blue avatar"),
    FaceStyle("Hologram", EYE_HOLO, SKIN_HOLO, MODE_GHOST, (0.30, 0.92, 1.0),
              "translucent cyan hologram with scanlines"),
    FaceStyle("Tron", EYE_CIRCUIT, SKIN_GRID, MODE_SOLID, (0.20, 0.95, 1.0),
              "glowing circuit-grid skin + HUD eyes"),
    FaceStyle("Wireframe", EYE_CIRCUIT, SKIN_NEON, MODE_WIRE, (0.35, 0.90, 1.0),
              "neon wireframe mesh"),
    FaceStyle("Dot Matrix", EYE_HOLO, SKIN_HOLO, MODE_DOTS, (0.40, 1.00, 0.70),
              "point-cloud dot matrix"),
    FaceStyle("Chrome", EYE_IRIS, SKIN_CHROME, MODE_SOLID, (0.72, 0.86, 1.0),
              "polished liquid-metal chrome + aperture eyes"),
    FaceStyle("Nebula", EYE_NEBULA, SKIN_IRIDESCENT, MODE_SOLID, (0.70, 0.40, 1.0),
              "cosmic nebula eyes, iridescent skin"),
    FaceStyle("Plasma", EYE_PLASMA, SKIN_NEON, MODE_SOLID, (1.00, 0.20, 0.80),
              "magenta plasma energy"),
    FaceStyle("Matrix", EYE_MATRIX, SKIN_GRID, MODE_DOTS, (0.20, 1.00, 0.35),
              "green falling-code rain"),
    FaceStyle("Solar", EYE_SOLAR, SKIN_CHROME, MODE_SOLID, (1.00, 0.55, 0.15),
              "molten solar corona, amber metal"),
    FaceStyle("Void", EYE_VOID, SKIN_MATTE, MODE_GHOST, (0.55, 0.35, 1.0),
              "black-hole eyes, ghostly violet form"),
    FaceStyle("Ghost", EYE_STARFIELD, SKIN_NEON, MODE_GHOST, (0.40, 0.90, 1.0),
              "translucent starlit spirit"),
    FaceStyle("Sonar", EYE_SONAR, SKIN_HOLO, MODE_SOLID, (0.30, 1.00, 0.90),
              "pulsing sonar rings (breathes with you)"),
    FaceStyle("Circuit", EYE_CIRCUIT, SKIN_CIRCUIT, MODE_SOLID, (0.95, 0.75, 0.20),
              "amber PCB traces"),
    FaceStyle("Aurora", EYE_NEBULA, SKIN_IRIDESCENT, MODE_GHOST, (0.30, 1.00, 0.60),
              "shimmering aurora veil"),
]

STYLES = {s.name: s for s in _STYLES}
DEFAULT = "Default"


def names():
    return list(STYLES)


def get(name):
    """The FaceStyle for *name*, or the Default style for an unknown name."""
    return STYLES.get(name) or STYLES[DEFAULT]
