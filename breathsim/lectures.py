"""Soothing 'lectures': long, poetic, sleep-inducing deep-dives on big ideas.

A category of bedtime narration alongside the procedural Scenes in ``stories.py``.
A :class:`Lecture` is *authored* (not procedural): an ordered list of gentle
sections, delivered slowly with breath / body-scan / relaxation interludes woven
between them, so it lulls rather than teaches. Each lecture lives in its own
``lectures_<topic>.py`` content module (NAME, AMBIENCE, SECTIONS); the `_CATALOG`
here groups them into **branches** (the Sleep picker shows them grouped).
``stories.story_units`` dispatches here by name.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import (lectures_alexandria, lectures_aurora, lectures_bees,
               lectures_birds, lectures_bread, lectures_breath, lectures_cell,
               lectures_clocks, lectures_deeptime, lectures_fungi,
               lectures_glaciers, lectures_heart, lectures_light, lectures_maps,
               lectures_moon, lectures_numbers, lectures_ocean, lectures_physics,
               lectures_plants, lectures_planets, lectures_salt, lectures_seasons,
               lectures_silkroad, lectures_sleep, lectures_spices, lectures_star,
               lectures_volcanoes, lectures_water, lectures_whales, lectures_tea,
               lectures_octopus, lectures_redwoods)
from . import (lectures_ants, lectures_blackholes, lectures_chocolate,
               lectures_coffee, lectures_eye, lectures_gardens,
               lectures_goldenratio, lectures_memory, lectures_milkyway,
               lectures_music, lectures_paper, lectures_spiders)
from . import (lectures_candles, lectures_constellations, lectures_glass,
               lectures_ink, lectures_pottery, lectures_weaving)
from . import (lectures_creation, lectures_phoenix, lectures_selkie,
               lectures_starmyths)
from . import lectures_hearing, lectures_smell, lectures_touch
from . import (lectures_honey, lectures_lighthouse, lectures_perfume,
               lectures_violin)
from . import lectures_cat, lectures_coral, lectures_moths, lectures_sloth
from . import lectures_caves, lectures_clouds, lectures_tides
from . import lectures_calendar, lectures_infinity, lectures_symmetry
from . import lectures_comets, lectures_nebulae, lectures_saturnsrings
from . import lectures_galaxies, lectures_meteors, lectures_sun
from . import (lectures_air, lectures_earth, lectures_fire,
               lectures_waterelement)
from . import (lectures_amber, lectures_diamond, lectures_jade, lectures_pearl)
from . import (lectures_balloon, lectures_caravan, lectures_compass,
               lectures_railway)
from . import (lectures_basketry, lectures_blacksmith, lectures_bookbinding,
               lectures_stainedglass)
from . import (lectures_dew, lectures_dust, lectures_seeds, lectures_snowflakes)
from . import (lectures_baobab, lectures_bamboo, lectures_cherryblossom,
               lectures_oak)
from . import (lectures_atlantis, lectures_avalon, lectures_eldorado,
               lectures_shangrila)
from . import (lectures_amazon, lectures_ganges, lectures_nile,
               lectures_yangtze)

# Pause (ms) after each lecture line / at a section's end. The narrator's
# ``pause_scale`` lengthens these further as the session winds down.
_LINE_PAUSE = 1400
_SECTION_PAUSE = 2100


@dataclass
class Lecture:
    name: str
    ambience: str
    sections: list = field(default_factory=list)
    category: str = "Lectures"


# Branches, in picker order — a wander cosmos -> earth -> life -> body, then the
# human stories (histories) and the play of ideas.
_CATALOG = [
    ("The Cosmos", [lectures_physics, lectures_star, lectures_moon,
                    lectures_planets, lectures_aurora, lectures_blackholes,
                    lectures_milkyway, lectures_constellations, lectures_comets,
                    lectures_nebulae, lectures_saturnsrings, lectures_sun,
                    lectures_galaxies, lectures_meteors]),
    ("Earth & Sea", [lectures_seasons, lectures_deeptime, lectures_water,
                     lectures_ocean, lectures_volcanoes, lectures_glaciers,
                     lectures_clouds, lectures_caves, lectures_tides]),
    ("The Living World", [lectures_whales, lectures_birds, lectures_plants,
                          lectures_fungi, lectures_bees, lectures_octopus,
                          lectures_redwoods, lectures_ants, lectures_spiders,
                          lectures_moths, lectures_sloth, lectures_coral,
                          lectures_cat]),
    ("The Human Body", [lectures_cell, lectures_heart, lectures_breath,
                        lectures_eye, lectures_hearing, lectures_smell,
                        lectures_touch, lectures_memory, lectures_sleep]),
    ("Histories", [lectures_tea, lectures_silkroad, lectures_alexandria,
                   lectures_bread, lectures_maps, lectures_clocks,
                   lectures_spices, lectures_salt, lectures_chocolate,
                   lectures_coffee, lectures_paper, lectures_gardens,
                   lectures_honey, lectures_lighthouse, lectures_violin,
                   lectures_perfume]),
    ("Materials & Making", [lectures_glass, lectures_pottery, lectures_weaving,
                            lectures_ink, lectures_candles]),
    ("Ideas & Wonders", [lectures_numbers, lectures_light, lectures_music,
                         lectures_goldenratio, lectures_infinity,
                         lectures_symmetry, lectures_calendar]),
    ("Voyages & Journeys", [lectures_compass, lectures_caravan, lectures_railway,
                            lectures_balloon]),
    ("The Quiet Crafts", [lectures_bookbinding, lectures_blacksmith,
                          lectures_basketry, lectures_stainedglass]),
    ("Small Wonders", [lectures_dew, lectures_dust, lectures_seeds,
                       lectures_snowflakes]),
    ("The Elements", [lectures_fire, lectures_waterelement, lectures_air,
                      lectures_earth]),
    ("Gems & Stones", [lectures_amber, lectures_pearl, lectures_jade,
                       lectures_diamond]),
    ("Myth & Legend", [lectures_starmyths, lectures_creation, lectures_phoenix,
                       lectures_selkie]),
    ("Trees of the World", [lectures_oak, lectures_bamboo, lectures_baobab,
                            lectures_cherryblossom]),
    ("Mythic Places", [lectures_atlantis, lectures_shangrila, lectures_eldorado,
                       lectures_avalon]),
    ("Great Rivers", [lectures_nile, lectures_amazon, lectures_ganges,
                      lectures_yangtze]),
]

LECTURES = {}
for _cat, _mods in _CATALOG:
    for _m in _mods:
        LECTURES[_m.NAME] = Lecture(_m.NAME, _m.AMBIENCE, _m.SECTIONS, _cat)


def names(category=None):
    if category is None:
        return list(LECTURES.keys())
    return [n for n, l in LECTURES.items() if l.category == category]


def categories():
    out = []
    for l in LECTURES.values():
        if l.category not in out:
            out.append(l.category)
    return out


def get(name):
    return LECTURES.get(name)


def category_of(name):
    l = LECTURES.get(name)
    return l.category if l else None


def ambience(name):
    l = LECTURES.get(name)
    return l.ambience if l else None


def units(name, rng=None, guidance=True):
    """Yield the lecture's lines in order (a finite stream), weaving a breath /
    body-scan / relaxation interlude after every other section so it stays a
    sleep aid. Imports the shared interludes lazily to avoid an import cycle."""
    import random
    rng = rng or random.Random()
    lec = LECTURES.get(name)
    if not lec:
        return
    from .stories import _bodyscan, _breath, _relax, _u
    interludes = [_breath, _bodyscan, _relax]
    n = len(lec.sections)
    for i, section in enumerate(lec.sections):
        for j, line in enumerate(section):
            last = j == len(section) - 1
            yield _u(line, pause=_SECTION_PAUSE if last else _LINE_PAUSE,
                     kind="lecture")
        if guidance and i % 2 == 1 and i < n - 1:
            yield from interludes[(i // 2) % len(interludes)](rng)
