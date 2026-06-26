"""Registry of the 2D characters + costumes (the cartoon face options). The face
widget picks a character by name and an optional costume; both are user choices
(persisted) and could be driven by the storyteller. Pure data + thin re-exports.
"""
from __future__ import annotations

from . import char_costume
from .char_bear import Bear
from .char_bunny import Bunny
from .char_cat import Cat
from .char_chicken import Chicken
from .char_dog import Dog
from .char_duckling import Duckling
from .char_fox import Fox
from .char_frog import Frog
from .char_hedgehog import Hedgehog
from .char_human import Man, Woman
from .char_mouse import Mouse
from .char_owl import Owl
from .char_panda import Panda
from .char_penguin import Penguin
from .char_robot import Robot
from .char_sheep import Sheep
from .char_skull import Skull
from .char_sloth import Sloth

_CHARS = [Cat(), Penguin(), Dog(), Owl(), Fox(), Chicken(), Bunny(), Bear(),
          Panda(), Frog(), Duckling(), Hedgehog(), Mouse(), Sheep(), Sloth(),
          Robot(), Woman(), Man(), Skull()]
CHARACTERS = {c.name: c for c in _CHARS}
DEFAULT = "Cat"


def names():
    return list(CHARACTERS)


def get(name):
    return CHARACTERS.get(name) or CHARACTERS[DEFAULT]


def costume_names():
    return char_costume.names()


def draw_costume(p, head, name, anim, hue):
    char_costume.draw(p, head, name, anim, hue)
