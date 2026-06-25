"""Pure Poetry across cultures: Japanese, Chinese-Tang and Persian traditions.

A set of "Pure Poetry: <tradition>" Sleep storyteller options, recited slowly
(reusing :func:`breathsim.poetry.recite`) with breath-length pauses, stanza rests
and long silences between poems. Three traditions:

- **Haiku & Tanka** -- short Japanese-form verses (haiku / tanka) in the mood of
  *mono no aware*, the tender transience of things.
- **Tang Nature** -- poems in the spirit of classical Chinese nature poetry
  (Wang Wei / Meng Haoran / Li Bai): still mountains, the river moon, pine wind.
- **Persian** -- ghazal couplets with a lulling repeated refrain (*radif*) and
  rubaiyat quatrains in the contemplative mood of Omar Khayyam.

All verses here are **original**, written for Vesper *in the spirit of* each
tradition (so there are no copyright concerns) -- they are not translations or
reproductions of any published poem. Honest framing: an homage, not authentic
historical text. Pure data + ``random``; unit-testable. Surfaced via
:mod:`breathsim.stories` (``story_units`` dispatches here by name).
"""
from __future__ import annotations

import random

from . import poetry

# (title, lines). An empty string "" is a stanza break (a longer pause).
_HAIKU = [
    ("Frost Moon", ["a thin white moon", "rests on the cold field --", "nothing stirs", "", "and the frost keeps", "its small bright silence", "till the slow dawn"]),
    ("Plum Petals", ["plum petals letting go", "one by one in the dark --", "no sound at all", "", "i watch them settle", "on the still black water", "and forget my name", "", "the branch is lighter now", "the night a little softer", "for the falling"]),
    ("Last Cricket", ["the cricket's last song", "thins into the grass --", "autumn lets it go", "", "and i lie quiet", "loving the small voice", "for leaving so gently"]),
    ("Paper Lantern", ["paper lantern dims", "by the closing garden door --", "a slow orange breath", "", "i leave it burning low", "and walk into the dark room", "carrying its glow"]),
    ("River Of Stars", ["the river of stars", "drifts above the still pond --", "two skies, one silence", "", "i give up my thoughts", "to that slow current of light", "and sink toward sleep"]),
    ("First Snow", ["first snow on the eaves", "softening every edge --", "the whole world hushed", "", "even the river", "lowers its voice tonight", "under falling white", "", "i pull the quilt close", "and let the cold blue evening", "fold itself away"]),
    ("Dew At Dawn", ["one drop of dew", "holds the fading moon --", "then quietly falls", "", "i too let the day", "slip from my open hand", "and rest in the grass"]),
]

_TANG = [
    ("Empty Mountain", ["No one on the mountain road,", "only the pine wind moving;", "the evening mist comes down", "and folds the path away.", "", "I set my lamp aside.", "Far off, a temple bell.", "The moon will keep the night,", "and I lie down to sleep."]),
    ("River Moon", ["The river holds the moon", "and does not let it go;", "no boat, no oar, no voice,", "only the water turning.", "", "I lean against the rail.", "The current carries nothing,", "the way the night will carry me,", "softly, toward the morning."]),
    ("After Rain", ["The rain has wandered off", "beyond the eastern hills.", "Each leaf lets down its weight", "of small and silver drops.", "", "The garden breathes again.", "I close the bamboo door.", "There is nothing left to do", "but watch the stillness deepen."]),
    ("White Clouds", ["White clouds without a home", "drift over the blue ridge,", "asking nothing of the sky,", "leaving no trace behind.", "", "I have set the wine aside;", "even joy grows quiet now.", "I will follow the clouds", "the easy way, into sleep."]),
    ("The Heron", ["A heron stands in shallows", "where the dusk pools cold and clear,", "one foot lifted, perfectly still,", "as if it had all of time.", "", "Reeds bend, then hold their breath.", "Mist gathers at the bank.", "The heron folds into the grey,", "and the marsh goes dark, and rests."]),
    ("Coming Home", ["The mountain path winds back", "through pine and falling leaves;", "the gate hangs half ajar,", "the lamp already lit.", "", "No errand calls me out.", "I hang my travelling cloak.", "Let the white clouds keep the peaks;", "I am home, and it is night."]),
    ("Single Lamp", ["One small lamp on the sill,", "one cup of cooling tea,", "the far-off river sound", "that has no need of words.", "", "The world grows soft and wide.", "I let my eyes fall shut.", "Outside, the quiet snow;", "inside, the gentle dark."]),
]

_PERSIAN = [
    ("The Night Is Kind", ["Lay down the long day's weight, and let it go.", "Unbend the tired hands, and let it go.", "", "The rose has loosed its red into the dark,", "the garden keeps no grief; and let it go.", "", "The moon walks slow across the courtyard stone,", "asking nothing of you; let it go.", "", "What the wheel of the sky has turned will turn,", "the dust, the years, the morning; let it go."]),
    ("Till Morning Comes", ["Close now the quiet book of all you did, till morning comes.", "The candle leans to sleep upon its wick, till morning comes.", "", "The nightingale has folded up its song,", "the courtyard cools to silver, till morning comes.", "", "Let the caravan of days go on without you, friend,", "you need not walk beside it till morning comes.", "", "Breathe out the small bright sorrows one by one,", "and lay your head on darkness till morning comes."]),
    ("The Patient Dark", ["What the heart could not finish, leave it to the patient dark.", "The wheel of the sky will carry it; leave it to the patient dark.", "", "No rose was ever scolded for its falling,", "no star asked why it faded; leave it to the patient dark.", "", "The garden does not count what bloomed and went,", "it only deepens, breathing; leave it to the patient dark.", "", "Tonight you owe the morning nothing more,", "so lay the day down gently in the patient dark."]),
    ("The Cup Of Evening", ["The cup of evening fills with quiet light,", "drink slowly; there is nothing left to win.", "The wheel that turned the noon will turn the stars,", "and pour the soft, forgiving dark within."]),
    ("Caravan", ["The caravan of days moves on, then on,", "its lanterns dimming one by one to rest.", "Unload your heart here in the cooling sand,", "the dark is wide, the patient dark is best."]),
    ("Dust And Stars", ["We are a little dust that learned to dream,", "lent for an evening to the turning sky.", "So let the worry loosen from your hands,", "the same kind dark that holds the stars holds I."]),
    ("Moonlit Courtyard", ["A garden sleeps; the moon has filled the well,", "the rose breathes out its colour into night.", "What troubled you at noon is only mist,", "now close your eyes and trust the gentle light."]),
]

_PREFIX = "Pure Poetry: "

# key -> (ambience voice, intro line, poems)
_TRADITIONS = {
    "Haiku & Tanka": ("Wind in Pines",
                      "A few small Japanese verses, to settle the mind toward sleep.",
                      _HAIKU),
    "Tang Nature": ("Gentle Rain",
                    "Some quiet poems in the spirit of old mountain nights.",
                    _TANG),
    "Persian": ("Singing Bowl",
                "Gentle verses in the spirit of old Persian gardens.",
                _PERSIAN),
}


def names():
    """The tradition session names, e.g. 'Pure Poetry: Haiku & Tanka'."""
    return [_PREFIX + k for k in _TRADITIONS]


def _key(name):
    return name[len(_PREFIX):] if name.startswith(_PREFIX) else name


def has(name):
    return _key(name) in _TRADITIONS


def ambience(name):
    t = _TRADITIONS.get(_key(name))
    return t[0] if t else poetry.AMBIENCE


def units(name, rng=None, guidance=True):
    t = _TRADITIONS.get(_key(name))
    if t is None:
        return poetry.units(rng, guidance)
    _amb, intro, poems = t
    return poetry.recite(poems, rng, guidance, intro=intro)
