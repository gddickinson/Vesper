"""Chant & song phrases -- multi-segment vocal sequences.

A :class:`Phrase` is an ordered list of :class:`Segment`s; the voice advances
**one segment per breath cycle** (sung on the exhale). Each segment is a
syllable label, its vowel (consonants can't be synthesised, so a syllable is
sung as its vowel nucleus, with an optional nasal ``vowel_to`` close for m/n),
and a pitch offset in semitones (for melodies). The label is shown on screen so
you can follow along.

Selecting a phrase turns the primary voice into a sequence; the Voice Body
persona still applies (male / female / child singer). See :mod:`breathsim.vocal`
for rendering and :meth:`breathsim.engine.AudioEngine.set_phrase`.
"""
from __future__ import annotations

from dataclasses import dataclass

from .voices import GROUP_VOCAL, VoiceConfig

CATEGORIES = ["Mantra", "Gregorian", "Song", "Chant Sounds", "Words"]


@dataclass
class Segment:
    syllable: str
    vowel: str
    vowel_to: str = ""
    semitone: float = 0.0
    onset: str = ""                 # leading consonant (synthesised articulation)
    coda: str = ""                  # closing consonant (synthesised at syllable end)


@dataclass
class Phrase:
    name: str
    category: str
    segments: list
    base_pitch: float = 120.0
    pattern: str = "OM Chant 3-9"
    description: str = ""
    groups: list = None             # breath-groups for the "phrase/breath" style
    source: str = "mix"
    voicing: float = 0.95           # mostly voiced -> a clear sung tone, little hiss
    air: float = 0.04               # a touch of warm breathiness
    vibrato_rate: float = 5.0
    vibrato_depth: float = 0.006
    gain: float = 1.2
    style: str = "per_phrase"       # the whole phrase sings across one exhale


PHRASES: list[Phrase] = []
_BY_NAME: dict[str, Phrase] = {}


def _add(p: Phrase):
    PHRASES.append(p)
    _BY_NAME[p.name] = p


def names(category: str | None = None):
    return [p.name for p in PHRASES if category is None or p.category == category]


def get(name: str) -> Phrase | None:
    return _BY_NAME.get(name)


def config(p: Phrase) -> VoiceConfig:
    """A base-timbre VoiceConfig for the phrase (the sequence overrides vowel
    and pitch per breath)."""
    s0 = p.segments[0]
    return VoiceConfig("(phrase)", GROUP_VOCAL, kind="vocal", env="exhale",
                       source=p.source, voicing=p.voicing, vowel=s0.vowel,
                       vowel_to=s0.vowel_to, pitch=p.base_pitch, air=p.air,
                       vibrato_rate=p.vibrato_rate, vibrato_depth=p.vibrato_depth,
                       gain=p.gain)


_DIGRAPHS = ("sh", "th", "ng")
_MAP = {"c": "k", "j": "d", "q": "k", "x": "k", "z": "s"}
# Consonants that synthesise cleanly as a *closing* (coda) sound. Others (b/g/v/
# h/w/y/...) are dropped from the coda, as a soft unreleased close.
_CODA_OK = {"s", "t", "d", "k", "p", "f", "l", "r", "sh", "th", "ng", "m", "n"}
_NASAL = {"m": "mm", "n": "mm", "ng": "mm"}      # voiced via the vowel_to glide


def _lead(syll):
    """Leading consonant of a syllable label, mapped to a synthesisable onset."""
    s = "".join(ch for ch in syll.lower() if ch.isalpha())
    for d in _DIGRAPHS:
        if s.startswith(d):
            return d
    if s and s[0] in "bcdfghjklmnpqrstvwxyz":
        return _MAP.get(s[0], s[0])
    return ""


def _trail(syll):
    """Trailing consonant of a label, mapped to a synthesisable coda. Returns ''
    for labels ending in a vowel letter (incl. silent-e) -- those need an explicit
    ``coda`` if a closing sound is wanted (English spelling is unreliable)."""
    s = "".join(ch for ch in syll.lower() if ch.isalpha())
    if not s or s[-1] in "aeiou":
        return ""
    for d in _DIGRAPHS:
        if s.endswith(d):
            return d if d in _CODA_OK else ""
    c = _MAP.get(s[-1], s[-1])
    return c if c in _CODA_OK else ""


def _S(syll, vowel, vowel_to="", semi=0.0, onset=None, coda=None):
    lead = _lead(syll) if onset is None else onset
    tail = _trail(syll) if coda is None else coda
    if tail in _NASAL:                  # a final m/n is sung as the vowel_to hum
        vowel_to = vowel_to or _NASAL[tail]
        tail = ""
    return Segment(syll, vowel, vowel_to, semi, lead, tail)


def _mantra(name, segs, base=120.0, desc="", groups=None):
    _add(Phrase(name, "Mantra", segs, base_pitch=base, pattern="OM Chant 3-9",
                description=desc, groups=groups))


def _greg(name, segs, base=130.0, desc="", groups=None):
    _add(Phrase(name, "Gregorian", segs, base_pitch=base, pattern="OM Chant 3-9",
                description=desc, groups=groups, voicing=0.9, air=0.07,
                vibrato_rate=3.0, vibrato_depth=0.003, gain=0.9))


def _song(name, vowel, notes, base=150.0, desc="", groups=None):
    segs = [Segment(lyr, vowel, "", semi, _lead(lyr)) for lyr, semi in notes]
    _add(Phrase(name, "Song", segs, base_pitch=base, pattern="Sigh Release 2-7",
                description=desc, groups=groups, source="buzz", voicing=1.0,
                air=0.03, vibrato_rate=5.0, vibrato_depth=0.007, gain=1.55))


# --- Mantras ---------------------------------------------------------------

_mantra("Om", [_S("Om", "oh", "mm")],
        desc="The seed sound - one long Om per breath.")
_mantra("Om Mani Padme Hum",
        [_S("Om", "oh", "mm", 0), _S("Ma", "ah", "", 0), _S("Ni", "ee", "", 2),
         _S("Pad", "ah", "", 2), _S("Me", "eh", "", 0), _S("Hum", "uh", "mm", -2)],
        desc="The mantra of compassion (one syllable per breath).")
_mantra("So Hum", [_S("So", "oh"), _S("Hum", "uh", "mm")],
        desc="'I am that' - a calming self-inquiry mantra.")
_mantra("Sat Nam", [_S("Sat", "ah"), _S("Nam", "ah", "mm", -2)],
        desc="'Truth is my identity' (Kundalini).")
_mantra("Om Namah Shivaya",
        [_S("Om", "oh", "mm"), _S("Na", "ah"), _S("Mah", "ah", "mm"),
         _S("Shi", "ee"), _S("Va", "ah"), _S("Ya", "ah")],
        desc="A devotional five-syllable mantra.")
_mantra("Om Shanti",
        [_S("Om", "oh", "mm"), _S("Shan", "ah", "mm"), _S("ti", "ee")],
        desc="'Om peace' - repeated for serenity.")
_mantra("Hare Krishna",
        [_S("Ha", "ah"), _S("re", "eh"), _S("Krish", "ee"), _S("na", "ah"),
         _S("Ha", "ah"), _S("re", "eh"), _S("Krish", "ee"), _S("na", "ah")],
        desc="Part of the maha-mantra.", groups=[(0, 4), (4, 8)])
_mantra("Gate Gate (Heart Sutra)",
        [_S("Ga", "ah"), _S("te", "eh"), _S("Ga", "ah"), _S("te", "eh"),
         _S("Pa", "ah"), _S("ra", "ah"), _S("ga", "ah"), _S("te", "eh"),
         _S("Bo", "oh"), _S("dhi", "ee"), _S("Sva", "ah"), _S("ha", "ah")],
        desc="The Heart Sutra's mantra of going beyond.",
        groups=[(0, 4), (4, 8), (8, 12)])

# More mantras (Tibetan / Vedic / Buddhist / Sikh) -------------------------
_mantra("Aum (A-U-M)",
        [_S("A", "ah", "oo"), _S("U", "oo", "mm")], base=104.0,
        desc="The three-part Om: 'ah' opening to 'oo', closing to a hum.",
        groups=[(0, 2)])
_mantra("Om Tare Tuttare",
        [_S("Om", "oh", "mm"), _S("Ta", "ah"), _S("re", "eh"), _S("Tut", "oo"),
         _S("ta", "ah"), _S("re", "eh"), _S("Tu", "oo"), _S("re", "eh"),
         _S("So", "oh"), _S("ha", "ah")],
        desc="Green Tara's mantra of swift protection and ease.",
        groups=[(0, 3), (3, 6), (6, 10)])
_mantra("Om Ah Hum",
        [_S("Om", "oh", "mm"), _S("Ah", "ah"), _S("Hum", "uh", "mm")],
        desc="Body, speech and mind - a Vajrayana purification.")
_mantra("Ra Ma Da Sa",
        [_S("Ra", "ah"), _S("Ma", "ah"), _S("Da", "ah"), _S("Sa", "ah"),
         _S("Sa", "ah"), _S("Say", "eh"), _S("So", "oh"), _S("Hung", "uh", "mm")],
        desc="A Kundalini healing mantra (sun, moon, earth, infinity).",
        groups=[(0, 4), (4, 8)])
_mantra("Om Gam Ganapataye",
        [_S("Om", "oh", "mm"), _S("Gam", "ah", "mm"), _S("Ga", "ah"),
         _S("na", "ah"), _S("pa", "ah"), _S("ta", "ah"), _S("ye", "eh")],
        desc="Invoking Ganesha, remover of obstacles.",
        groups=[(0, 2), (2, 7)])
_mantra("Nam Myoho Renge Kyo",
        [_S("Nam", "ah", "mm"), _S("Myo", "oh"), _S("ho", "oh"), _S("Ren", "eh", "mm"),
         _S("ge", "eh"), _S("Kyo", "oh")], base=128.0,
        desc="The Nichiren Buddhist daimoku.", groups=[(0, 3), (3, 6)])
_mantra("Lokah Samastah",
        [_S("Lo", "oh"), _S("kah", "ah"), _S("Sa", "ah"), _S("mas", "ah", coda="s"),
         _S("tah", "ah"), _S("Su", "oo"), _S("khi", "ee"), _S("no", "oh")],
        desc="'May all beings be happy and free' (loka samasta).",
        groups=[(0, 5), (5, 8)])
_mantra("Om Shanti Shanti Shanti",
        [_S("Om", "oh", "mm"), _S("Shan", "ah", "mm"), _S("ti", "ee"),
         _S("Shan", "ah", "mm"), _S("ti", "ee"), _S("Shan", "ah", "mm"),
         _S("ti", "ee")], desc="A threefold invocation of peace.",
        groups=[(0, 3), (3, 5), (5, 7)])
_mantra("So Ham",
        [_S("So", "oh"), _S("Ham", "ah", "mm")],
        desc="'I am that' - ride the breath: 'So' in, 'Ham' out.")


# --- Gregorian / monastic --------------------------------------------------

_greg("Kyrie Eleison",
      [_S("Ky", "ee", "", 0), _S("ri", "ee", "", 2), _S("e", "eh", "", 0),
       _S("e", "eh", "", 2), _S("le", "eh", "", 3), _S("i", "ee", "", 2),
       _S("son", "oh", "mm", 0)],
      desc="'Lord, have mercy' - a plainchant supplication.")
_greg("Alleluia",
      [_S("Al", "ah", "", 0), _S("le", "eh", "", 2), _S("lu", "oo", "", 4),
       _S("ia", "ah", "", 2)],
      desc="A joyful chant of praise.")
_greg("Dona Nobis Pacem",
      [_S("Do", "oh", "", 0), _S("na", "ah", "", 2), _S("no", "oh", "", 4),
       _S("bis", "ee", "", 2), _S("pa", "ah", "", 0), _S("cem", "eh", "mm", -1)],
      desc="'Grant us peace' - a gentle round.")
_greg("Agnus Dei",
      [_S("Ag", "ah", "", 0), _S("nus", "oo", "mm", 0), _S("De", "eh", "", 2),
       _S("i", "ee", "", 0)],
      desc="'Lamb of God' from the Mass.")
_greg("Amen", [_S("A", "ah", "", 4), _S("men", "eh", "mm", 0)],
      desc="A two-note plagal 'Amen'.")
_greg("Dies Irae",
      [_S("Di", "ee", "", 4), _S("es", "eh", "", 4), _S("i", "ee", "", 2),
       _S("rae", "ah", "", 4), _S("di", "ee", "", 0), _S("es", "eh", "", 2),
       _S("il", "ee", "", 0), _S("la", "ah", "", -1)],
      desc="The famous medieval 'day of wrath' chant motif.")
_greg("Ave Maria",
      [_S("A", "ah", "", 0), _S("ve", "eh", "", 2), _S("Ma", "ah", "", 4),
       _S("ri", "ee", "", 2), _S("a", "ah", "", 0)],
      desc="'Hail Mary' - a gentle plainchant opening.",
      groups=None)
_greg("Ubi Caritas",
      [_S("U", "oo", "", 0), _S("bi", "ee", "", 2), _S("ca", "ah", "", 4),
       _S("ri", "ee", "", 2), _S("tas", "ah", "", 0, coda="s"),
       _S("et", "eh", "", 2, coda="t"), _S("a", "ah", "", 4),
       _S("mor", "oh", "", 2, coda="r")],
      desc="'Where charity is' - a Holy Thursday chant.",
      groups=[(0, 5), (5, 8)])
_greg("Veni Sancte Spiritus",
      [_S("Ve", "eh", "", 0), _S("ni", "ee", "", 2), _S("San", "ah", "mm", 4),
       _S("cte", "eh", "", 2), _S("Spi", "ee", "", 4), _S("ri", "ee", "", 2),
       _S("tus", "oo", "", 0, coda="s")],
      desc="'Come, Holy Spirit' - a luminous sequence.",
      groups=[(0, 4), (4, 7)])


# --- Simple songs (one note per breath) ------------------------------------

_song("Twinkle Twinkle", "oo",
      [("Twin", 0), ("kle", 0), ("twin", 7), ("kle", 7), ("lit", 9), ("tle", 9),
       ("star", 7), ("How", 5), ("I", 5), ("won", 4), ("der", 4), ("what", 2),
       ("you", 2), ("are", 0)],
      desc="The nursery melody, one note per breath.", groups=[(0, 7), (7, 14)])
_song("Mary Had a Little Lamb", "ah",
      [("Ma", 4), ("ry", 2), ("had", 0), ("a", 2), ("lit", 4), ("tle", 4),
       ("lamb", 4), ("lit", 2), ("tle", 2), ("lamb", 2), ("lit", 4), ("tle", 7),
       ("lamb", 7)],
      desc="A simple, steadying tune.", groups=[(0, 7), (7, 13)])
_song("Row Your Boat", "oo",
      [("Row", 0), ("row", 0), ("row", 0), ("your", 2), ("boat", 4),
       ("gent", 4), ("ly", 2), ("down", 4), ("the", 5), ("stream", 7)],
      desc="A gentle rocking round.", groups=[(0, 5), (5, 10)])
_song("Frere Jacques", "ah",
      [("Fre", 0), ("re", 2), ("Jac", 4), ("ques", 0), ("Fre", 0), ("re", 2),
       ("Jac", 4), ("ques", 0), ("Dor", 4), ("mez", 5), ("vous", 7),
       ("Dor", 4), ("mez", 5), ("vous", 7)],
      desc="The round, slowed into breaths.", groups=[(0, 4), (4, 8), (8, 11), (11, 14)])
_song("Ode to Joy", "ah",
      [("♪", 4), ("♪", 4), ("♪", 5), ("♪", 7), ("♪", 7),
       ("♪", 5), ("♪", 4), ("♪", 2), ("♪", 0), ("♪", 0),
       ("♪", 2), ("♪", 4), ("♪", 4), ("♪", 2), ("♪", 2)],
      desc="Beethoven's joyful theme on an open 'ah'.", groups=[(0, 8), (8, 15)])
_song("Amazing Grace", "ah",
      [("A", -5), ("ma", 0), ("zing", 4), ("grace", 0), ("how", 4), ("sweet", 2),
       ("the", 0), ("sound", -3), ("that", -5)],
      desc="The hymn, one note per breath.")
_song("Brahms Lullaby", "oo",
      [("♪", 4), ("♪", 4), ("♪", 7), ("♪", 4), ("♪", 4),
       ("♪", 7), ("♪", 4), ("♪", 7), ("♪", 12), ("♪", 11),
       ("♪", 9), ("♪", 7)],
      desc="A soft cradle song for drifting off.", groups=[(0, 6), (6, 12)])


# --- Chant sounds: short seed syllables & vowels (one per breath) ----------

def _chant(name, segs, base=120.0, desc=""):
    _add(Phrase(name, "Chant Sounds", segs, base_pitch=base,
                pattern="OM Chant 3-9", description=desc, source="mix",
                voicing=0.95, air=0.04, gain=1.1))


# Consonant + open 'ah' seed syllables (the onset is synthesised from the label).
for _syl in ("Pa", "Ma", "Ya", "Ha", "Na", "La", "Da", "Ra", "Va", "Sa",
             "Ka", "Ta", "Ga"):
    _chant(_syl, [_S(_syl, "ah")],
           desc=f"Chant '{_syl.lower()}' on each out-breath - a seed syllable.")

# Pure sustained vowels (vocalises - no consonant).
_chant("Aah", [_S("Aah", "ah")], desc="An open 'aah' - release the jaw.")
_chant("Ooh", [_S("Ooh", "oo")], desc="A rounded 'ooh' - soft and low.")
_chant("Eee", [_S("Eee", "ee")], desc="A bright 'eee' - forward and light.")
_chant("Ohh", [_S("Ohh", "oh")], desc="A warm 'ohh'.")
_chant("Ehh", [_S("Ehh", "eh")], desc="An open 'ehh'.")
_chant("Mmm", [_S("Mmm", "uh", "mm")], desc="A closed-mouth hum.")

# Classic vocalises (several syllables across the breath).
_chant("Ma Me Mi Mo Mu",
       [_S("Ma", "ah"), _S("Me", "eh"), _S("Mi", "ee"), _S("Mo", "oh"),
        _S("Mu", "oo")],
       desc="The singer's 5-vowel warm-up on 'm'.")
_chant("Pa Ta Ka",
       [_S("Pa", "ah"), _S("Ta", "ah"), _S("Ka", "ah")],
       desc="A crisp articulation drill (plosive onsets).")


# --- Short words: affirmations & counting (one word per breath) ------------

def _word(name, segs, desc="", base=130.0, pattern="Calming 4-6 (Long Exhale)",
          style="per_phrase"):
    _add(Phrase(name, "Words", segs, base_pitch=base, pattern=pattern,
                description=desc, source="mix", voicing=0.93, air=0.05, gain=1.0,
                style=style))


_word("Peace", [_S("Peace", "ee", coda="s")], desc="Sing 'peace' on each out-breath.")
_word("Calm", [_S("Calm", "ah", "mm")], desc="A long, soft 'calm'.")
_word("Let Go", [_S("Let", "eh", coda="t"), _S("Go", "oh")], desc="'Let go'.")
_word("Be Still", [_S("Be", "ee"), _S("Still", "ee", coda="l")], desc="'Be still'.")
_word("I Am", [_S("I", "ah"), _S("Am", "ah", "mm")], desc="'I am' - presence.")
_word("Release", [_S("Re", "eh"), _S("lease", "ee", coda="s")],
      desc="'Release' tension.")
_word("Home", [_S("Home", "oh", "mm")], desc="Return 'home' to the breath.")
_word("Soft Belly", [_S("Soft", "oh", coda="f"), _S("Bel", "eh", coda="l"),
                     _S("ly", "ee")], desc="'Soft belly' - relax the core.")
_word("Trust", [_S("Trust", "uh", coda="s")], desc="Let the body 'trust' the breath.")
_word("At Ease", [_S("At", "ah", coda="t"), _S("Ease", "ee", coda="s")],
      desc="Settle 'at ease'.")
_word("All Is Well", [_S("All", "oh", coda="l"), _S("Is", "ee", coda="s"),
                      _S("Well", "eh", coda="l")], desc="A reassuring phrase.")
_word("Count to Ten",
      [_S("One", "uh", "mm", 0, onset="w"), _S("Two", "oo"), _S("Three", "ee"),
       _S("Four", "oh", coda="r"), _S("Five", "ah", coda="f"),
       _S("Six", "ee", coda="s"), _S("Sev", "eh", coda="v"),
       _S("Eight", "eh", coda="t"), _S("Nine", "ah", "mm"), _S("Ten", "eh", "mm")],
      desc="Count each breath from one to ten, then begin again.",
      pattern="Coherent 5.5 (Resonance)", style="per_breath")
