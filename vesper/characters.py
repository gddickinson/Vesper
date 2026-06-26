"""Registry of the 2D characters + costumes (the cartoon face options). The face
widget picks a character by name and an optional costume; both are user choices
(persisted) and could be driven by the storyteller. Pure data + thin re-exports.
"""
from __future__ import annotations

from . import char_costume
from .char_alien import Alien
from .char_bear import Bear
from .char_bot import Bot
from .char_bunny import Bunny
from .char_cat import Cat
from .char_chicken import Chicken
from .char_cow import Cow
from .char_deer import Deer
from .char_dog import Dog
from .char_duckling import Duckling
from .char_elephant import Elephant
from .char_fox import Fox
from .char_frog import Frog
from .char_giraffe import Giraffe
from .char_hedgehog import Hedgehog
from .char_human import Man, Woman
from .char_koala import Koala
from .char_lion import Lion
from .char_luna import Luna
from .char_martian import Martian
from .char_monkey import Monkey
from .char_mouse import Mouse
from .char_owl import Owl
from .char_panda import Panda
from .char_penguin import Penguin
from .char_pig import Pig
from .char_rat import Rat
from .char_redpanda import RedPanda
from .char_rhino import Rhino
from .char_robot import Robot
from .char_sheep import Sheep
from .char_skull import Skull
from .char_sloth import Sloth
from .char_snowman import Snowman
from .char_tiger import Tiger

_CHARS = [Cat(), Penguin(), Dog(), Owl(), Fox(), Chicken(), Bunny(), Bear(),
          Panda(), Frog(), Duckling(), Hedgehog(), Mouse(), Rat(), Sheep(),
          Sloth(), Koala(), RedPanda(), Lion(), Tiger(), Elephant(), Giraffe(),
          Rhino(), Pig(), Cow(), Monkey(), Deer(), Snowman(), Luna(), Robot(),
          Bot(), Alien(), Martian(), Woman(), Man(), Skull()]
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
