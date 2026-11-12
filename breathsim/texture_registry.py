"""The ``kind="texture"`` generator registry, kept free of other breathsim imports.

``textures`` (the built-in beds) and the plug-in engines (``cosmic``, ``synth_bell``,
``synth_drum``, ``synth_wind``, ``synth_fx``) all register here, and
``textures.TextureTrack`` looks generators up here. Because this module imports nothing
from the package, any of those modules can be imported first without a circular
ImportError (``import breathsim.textures`` before ``breathsim.voices`` used to fail).
"""
from __future__ import annotations

GENERATORS: dict = {}   # texture key -> factory(sr, rng) -> object with step(tarr, frames)
SEEDS: dict = {}        # texture key -> deterministic RNG seed
DEFAULT_SEED = 11


def register_generator(key, factory, seed):
    """Plug a texture generator in. ``factory(sr, rng)`` must return an object with
    ``step(tarr, frames) -> (frames, 2)`` (or ``step(tarr, frames, s0, s1)`` when it sets
    ``wants_state = True``)."""
    GENERATORS[key] = factory
    SEEDS[key] = seed


def make(key, sr, rng):
    return GENERATORS[key](sr, rng)


def seed_for(key):
    return SEEDS.get(key, DEFAULT_SEED)
