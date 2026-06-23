"""Guided multi-stage session programs.

A :class:`Program` is an ordered list of :class:`Stage`s. Each stage runs for a
number of minutes and applies its own settings (pattern, voice or chant phrase,
ambience, effect, scene, spoken-cue style), with an on-screen and optionally
spoken instruction. The :class:`~breathsim.session.SessionDirector` advances
through the stages automatically; each stage's pattern starts cleanly at the
inhale (see :meth:`breathsim.controller.BreathController.change_pattern`).

Structures follow common practice: guided meditations arc settle -> breath
awareness -> technique -> deepen -> return; pranayama goes energising ->
calming; Wim Hof is rounds of power-breaths + retention + recovery.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Stage:
    title: str
    minutes: float
    settings: dict
    say: str = ""


@dataclass
class Program:
    name: str
    description: str
    stages: list

    @property
    def total_minutes(self):
        return sum(s.minutes for s in self.stages)


PROGRAMS: list[Program] = []
_BY_NAME: dict[str, Program] = {}


def _st(title, minutes, say="", **settings):
    return Stage(title, minutes, settings, say or title)


def _add(name, desc, stages):
    p = Program(name, desc, stages)
    PROGRAMS.append(p)
    _BY_NAME[name] = p


def names():
    return [p.name for p in PROGRAMS]


def get(name):
    return _BY_NAME.get(name)


# --- programs --------------------------------------------------------------

_add("Calm & Unwind (12 min)", "Settle, lengthen the exhale, box-breathe, rest.",
     [_st("Arrive & settle", 1, "Find a comfortable position, and let your eyes "
          "gently close.", pattern="Coherent 5.5 (Resonance)", voice="Deep Calm",
          scene="orb", cue_style="Guided", volume=0.7),
      _st("Breath awareness", 3, "Simply notice the natural rhythm of your "
          "breath.", pattern="Coherent 5.5 (Resonance)", voice="Soft Whisper"),
      _st("Lengthen the exhale", 3, "Let each out-breath grow a little longer.",
          pattern="Calming 4-6 (Long Exhale)", voice="Ocean Breath (Ujjayi)",
          scene="wave"),
      _st("Box breathing", 2.5, "Breathe a square: in, hold, out, hold.",
          pattern="Box Breathing 4-4-4-4", voice="Deep Calm", scene="orb"),
      _st("Rest", 2.5, "Let the breath slow, and simply rest.",
          pattern="Extended 7-11", voice="Sleepy Warm", ambience="Soft Rainstorm",
          scene="night", cue_style="Off")])

_add("Energize (8 min)", "Warm up, breath of fire, bellows, then settle.",
     [_st("Warm up", 1.5, "Sit tall. A few easy breaths to begin.",
          pattern="Coherent 5.5 (Resonance)", voice="Nose Breath", scene="orb",
          cue_style="Standard", volume=0.75),
      _st("Breath of Fire", 1.5, "Rapid belly breaths. Sharp exhales through the "
          "nose.", pattern="Breath of Fire", voice="Breath of Fire"),
      _st("Pause & feel", 1, "Pause. Notice the bright, tingling energy.",
          pattern="Coherent 5.5 (Resonance)", voice="Soft Whisper"),
      _st("Bhastrika bellows", 1.5, "Forceful breaths, in and out, like bellows.",
          pattern="Bhastrika (Bellows)", voice="Bhastrika (Bellows)"),
      _st("Settle", 2, "Let the breath return to calm and even.",
          pattern="Coherent 5.5 (Resonance)", voice="Deep Calm",
          cue_style="Off")])

_add("Wim Hof (3 rounds)", "Power breaths, retention and recovery, three rounds.",
     [s for r in range(1, 4) for s in (
         _st(f"Round {r}: power breaths", 1.2, "Thirty deep breaths. In fully, "
             "let go.", pattern="Wim Hof Power", voice="Wim Hof Breath",
             scene="orb", cue_style="Off", volume=0.8),
         _st(f"Round {r}: hold (empty)", 1.5, "Exhale fully, and hold. Stay "
             "relaxed.", pattern=(1.5, 0, 1.5, 75), voice="Soft Whisper"),
         _st(f"Round {r}: recovery", 0.4, "Big breath in, and hold.",
             pattern=(2, 15, 2, 0), voice="Deep Calm"))])

_add("Pranayama (15 min)", "Kapalabhati, bhastrika, balance, hum, OM, stillness.",
     [_st("Kapalabhati", 2, "Cleansing breath of fire.", pattern="Breath of Fire",
          voice="Breath of Fire", scene="orb", cue_style="Standard"),
      _st("Bhastrika", 2, "Energising bellows breath.",
          pattern="Bhastrika (Bellows)", voice="Bhastrika (Bellows)"),
      _st("Nadi Shodhana", 3, "Slow, balanced breathing - imagine alternating "
          "nostrils.", pattern="Coherent 5.5 (Resonance)", voice="Nose Breath"),
      _st("Bhramari", 3, "Hum softly on each out-breath, like a bee.",
          pattern="OM Chant 3-9", voice="Hum (Mmm)", scene="ripple"),
      _st("OM", 2, "Chant OM on each exhale.", phrase="Om",
          chant_style="per_breath", scene="ripple"),
      _st("Stillness", 3, "Rest in stillness, and watch the breath.",
          pattern="Extended 7-11", voice="Soft Whisper", cue_style="Off",
          scene="orb")])

_add("Mantra Japa (12 min)", "Om Mani Padme Hum: spoken, then sung, then silent.",
     [_st("Arrive", 1, "Settle, and prepare to chant.", pattern="OM Chant 3-9",
          voice="Deep Calm", scene="ripple", cue_style="Off"),
      _st("One syllable per breath", 4, "One syllable on each out-breath.",
          phrase="Om Mani Padme Hum", chant_style="per_breath", scene="ripple",
          persona="Male"),
      _st("Full mantra per breath", 4, "Now the whole mantra on each breath.",
          phrase="Om Mani Padme Hum", chant_style="per_phrase", scene="ripple"),
      _st("Silent repetition", 3, "Continue silently, in your mind.",
          pattern="OM Chant 3-9", voice="Soft Whisper", scene="ripple",
          cue_style="Off")])

_add("Sleep Wind-Down (18 min)", "Slower and softer, under rain and a heartbeat.",
     [_st("Settle into bed", 3, "Lie down, and let your body grow heavy.",
          pattern="Calming 4-6 (Long Exhale)", voice="Sleepy Warm", scene="night",
          ambience="Soft Rainstorm", cue_style="Off", volume=0.65),
      _st("Slow the breath", 5, "Each breath slower than the last.",
          pattern="Ujjayi Slow 6-6", voice="Sleepy Warm",
          effect="Heartbeat (slow)"),
      _st("Drift", 6, "Let go. There is nothing to do.", pattern="Extended 7-11",
          voice="Sleepy Warm", volume=0.55),
      _st("Sleep", 4, "", pattern=(8, 0, 12, 0), voice="Sleepy Warm",
          volume=0.4)])

_add("Vocal Warm-Up", "Hum, lip trill, straw (SOVT), siren, scale - in order.",
     [_st("Humming", 1.5, "Gentle humming to wake the voice, lips together.",
          pattern="OM Chant 3-9", voice="Hum (Mmm)", scene="ripple",
          persona="Female", cue_style="Standard"),
      _st("Lip trills", 1.5, "Lip trills - 'brrr' - connecting breath and voice.",
          pattern="Long Tone 2-12 (Singers)", voice="Lip Trill (Brrr)"),
      _st("Straw phonation", 1.5, "Sing gently through a straw (SOVT) on 'oo'.",
          pattern="Long Tone 2-12 (Singers)", voice="Straw Phonation (Oo)"),
      _st("Sirens", 1.5, "Glide up and down like a siren to connect your range.",
          pattern="Long Tone 2-12 (Singers)", voice="Siren (Ng / Ee)"),
      _st("Scales", 1.5, "Walk up a major scale on 'ah'.",
          pattern="Long Tone 2-12 (Singers)", voice="Major Scale (Ah)"),
      _st("Arpeggios", 1.5, "Major arpeggio, do-mi-so-do, up and back.",
          pattern="Long Tone 2-12 (Singers)", voice="Arpeggio (Ah)",
          cue_style="Off")])

_add("Body & Breath (10 min)", "A breath-paced body scan from feet to head.",
     [_st("Arrive", 1, "Settle, and take a few easy breaths.",
          pattern="Coherent 5.5 (Resonance)", voice="Deep Calm", scene="orb",
          cue_style="Guided"),
      _st("Feet & legs", 2, "Breathe into your feet and legs, and soften them.",
          pattern="Calming 4-6 (Long Exhale)", voice="Soft Whisper"),
      _st("Belly & chest", 2, "Bring the breath to your belly and chest."),
      _st("Shoulders & head", 2, "Release your shoulders, your jaw, your brow."),
      _st("Whole body", 3, "Breathe through the whole body, completely at ease.",
          voice="Ocean Breath (Ujjayi)", pattern="Coherent 5.5 (Resonance)")])
