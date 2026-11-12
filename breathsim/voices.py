"""Voice registry: the palette of breath, nature and tonal sound characters.

Each :class:`VoiceConfig` is pure data describing how to synthesise a voice.
:mod:`breathsim.tracks` turns a config into an audio renderer.

Voices fall into three groups:

* **Breath**   -- realistic human breath timbres (different "accents" of
  breathing). Driven by *airflow*, so they fall silent during holds.
* **Nature**   -- synthetic ambiences from natural events (waves, rain, wind,
  streams). Driven by lung *volume*, so they swell and recede with the breath.
* **Tonal**    -- smooth synthetic drones that bloom with the inhale.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

GROUP_BREATH = "Breath"
GROUP_NATURE = "Nature"
GROUP_TONAL = "Tonal"
GROUP_VOCAL = "Human Voice"
GROUP_EXERCISE = "Vocal Exercises"
GROUP_TECHNIQUE = "Breathwork"
GROUP_SING = "Singing"
GROUP_SYNTH = "Synthetic Breath"
GROUP_EFFECTS = "Effects"
GROUP_WORDS = "Spoken Words"
GROUP_CUSTOM = "Custom"
GROUP_CAT = "Cat"
GROUP_MUSIC = "Cosmic Music"
GROUP_BELLS = "Bells & Gongs"
GROUP_DRUMS = "Drums"
GROUP_WIND = "Winds & Organs"
GROUP_FX = "Environmental FX"

# Voice families whose primary slot supports the human<->synthetic morph and
# per-voice morphing (everything voice/breath based).
MORPHABLE = (GROUP_BREATH, GROUP_VOCAL, GROUP_EXERCISE, GROUP_TECHNIQUE,
             GROUP_SING, GROUP_SYNTH)


@dataclass
class VoiceConfig:
    name: str
    group: str
    description: str = ""
    kind: str = "noise"                       # noise | tonal | sample
    # --- noise voice parameters ---
    noise: str = "pink"                       # white | pink | brown
    filt: tuple = ("bandpass", 600.0, 1.0)    # (type, centre/cutoff Hz, Q)
    bright_base: float = 4000.0               # one-pole LP base cutoff (Hz)
    bright_mod: float = 0.0                   # cutoff added at full envelope
    env: str = "airflow"                      # airflow | volume
    floor: float = 0.0                        # baseline level for ambiences
    gain: float = 0.5
    width: float = 0.0                        # 0 mono .. 1 fully decorrelated
    pan_rate: float = 0.0                     # slow auto-pan rate (Hz)
    pan_depth: float = 0.0
    exhale_mul: float = 1.0                   # brightness mult on the exhale
    # --- tonal voice parameters ---
    base_freq: float = 110.0
    partials: tuple = ((1.0, 0.5),)           # ((ratio, amp), ...)
    # --- sample voice parameters ---
    data: object = field(default=None, repr=False)
    trigger: str = "loop"          # loop | exhale | inhale (one-shot per cycle)
    # --- vocal voice parameters (kind == "vocal") ---
    source: str = "noise"          # noise | buzz | mix
    voicing: float = 0.0           # 0 pure breath .. 1 fully voiced
    vowel: str = ""                # formant preset key (vowel or breath shape)
    vowel_to: str = ""             # exhale glides vowel -> vowel_to (e.g. AUM)
    vowel_in: str = ""             # formant for the inhale (env="breath")
    attack_in: str = "smooth"      # inhale attack (env="breath")
    inhale_level: float = 1.0      # inhale loudness scale (env="breath")
    exhale_level: float = 1.0      # exhale loudness scale (env="breath")
    pitch: float = 130.0           # glottal fundamental (Hz)
    vibrato_rate: float = 0.0
    vibrato_depth: float = 0.0
    pitch_glide: float = 0.0       # semitones swept across the exhale
    glide_shape: str = "linear"    # linear | updown | scale_up | arp_up
    attack: str = "smooth"         # smooth | explosive | swell
    air: float = 0.0               # extra breathy air mixed in
    am_rate: float = 0.0           # amplitude-modulation rate (lip trills)
    am_depth: float = 0.0
    n_harm: int = 18
    # --- rhythmic effect parameters (kind == "rhythm") ---
    bpm: float = 60.0
    rhythm: str = "heartbeat"      # heartbeat | drum
    # --- procedural texture (kind == "texture") ---
    texture: str = ""              # campfire | bowl | chimes | crickets


_VOICES: dict[str, VoiceConfig] = {}


def register(cfg: VoiceConfig) -> VoiceConfig:
    _VOICES[cfg.name] = cfg
    return cfg


def get_voice(name: str) -> VoiceConfig | None:
    return _VOICES.get(name)


def unregister(name: str):
    """Remove a voice (e.g. a transient '(preview)' from the Voice Editor)."""
    _VOICES.pop(name, None)


def names(group: str | None = None):
    return [c.name for c in _VOICES.values() if group is None or c.group == group]


def all_configs():
    return list(_VOICES.values())


def to_dict(cfg: VoiceConfig) -> dict:
    """Serialise a voice config to a JSON-safe dict (drops sample data)."""
    return {f.name: getattr(cfg, f.name)
            for f in dataclasses.fields(cfg) if f.name != "data"}


def register_from_dict(d: dict) -> VoiceConfig:
    """Register a saved voice as a Custom-group voice."""
    d = {k: v for k, v in d.items() if k != "data"}
    d["group"] = GROUP_CUSTOM
    return register(VoiceConfig(**d))


# --- Breath voices (realistic, airflow-driven) -----------------------------

register(VoiceConfig(
    "Deep Calm", GROUP_BREATH, noise="pink",
    filt=("bandpass", 450.0, 0.8), bright_base=900.0, bright_mod=1300.0,
    exhale_mul=0.78, gain=0.46, width=0.18,
    description="Low, warm, breathy. A slow grounding breath."))

register(VoiceConfig(
    "Ocean Breath (Ujjayi)", GROUP_BREATH, noise="pink",
    filt=("bandpass", 520.0, 2.2), bright_base=1400.0, bright_mod=1500.0,
    exhale_mul=0.85, gain=0.62, width=0.2,
    description="The throaty, oceanic yoga breath made in the back of the "
                "throat."))

register(VoiceConfig(
    "Soft Whisper", GROUP_BREATH, noise="white",
    filt=("bandpass", 1800.0, 0.7), bright_base=5000.0, bright_mod=3000.0,
    exhale_mul=0.9, gain=0.41, width=0.25,
    description="Airy and gentle, like a quiet sigh close to the ear."))

register(VoiceConfig(
    "Nasal Gentle", GROUP_BREATH, noise="white",
    filt=("bandpass", 1150.0, 1.4), bright_base=3200.0, bright_mod=2200.0,
    exhale_mul=0.85, gain=0.77, width=0.15,
    description="A brighter, focused through-the-nose breath."))

register(VoiceConfig(
    "Sleepy Warm", GROUP_BREATH, noise="brown",
    filt=("lowpass", 700.0, 0.7), bright_base=700.0, bright_mod=600.0,
    exhale_mul=0.7, gain=0.19, width=0.2,
    description="Very soft and warm - made for drifting off to sleep."))


# --- Nature voices (synthetic ambiences, volume-driven) --------------------

register(VoiceConfig(
    "Ocean Waves", GROUP_NATURE, noise="pink", env="volume",
    filt=("lowpass", 1400.0, 0.7), bright_base=320.0, bright_mod=1900.0,
    floor=0.12, gain=0.15, width=0.75, pan_rate=0.03, pan_depth=0.35,
    description="A wave swells in on the inhale and recedes on the exhale."))

register(VoiceConfig(
    # Calibrated: at gain 1.0 this brown-noise wash peaks ~3.9 / rms ~0.81; gain
    # 0.08 -> peak ~0.30, rms ~0.065 (a touch softer than Ocean Waves, for sleep).
    "Distant Surf (night)", GROUP_NATURE, noise="brown", env="volume",
    filt=("lowpass", 560.0, 0.7), bright_base=240.0, bright_mod=520.0,
    floor=0.72, gain=0.08, width=0.85, pan_rate=0.02, pan_depth=0.28,
    description="A far-off ocean at night: a low, steady wash that breathes "
                "softly in and out, darker and gentler than Ocean Waves."))

register(VoiceConfig(
    # Calibrated: at gain 1.0 this warm mid-band wash peaks ~1.9 / rms ~0.32; gain
    # 0.24 -> peak ~0.41, rms ~0.077 (matched to the other nature beds).
    "Summer Porch", GROUP_NATURE, noise="pink", env="volume",
    filt=("bandpass", 1500.0, 0.45), bright_base=900.0, bright_mod=1100.0,
    floor=0.62, gain=0.24, width=0.8, pan_rate=0.025, pan_depth=0.3,
    description="A warm summer night on a porch: a soft, steady wash of warm "
                "air that breathes gently, with no chill in it."))

register(VoiceConfig(
    "Gentle Rain", GROUP_NATURE, noise="white", env="volume",
    filt=("bandpass", 2600.0, 0.5), bright_base=9000.0, bright_mod=3000.0,
    floor=0.2, gain=0.22, width=0.85,
    description="Steady rainfall that softly intensifies with each breath."))

register(VoiceConfig(
    "Forest Wind", GROUP_NATURE, noise="pink", env="volume",
    filt=("bandpass", 520.0, 0.6), bright_base=600.0, bright_mod=1700.0,
    floor=0.1, gain=0.24, width=0.7, pan_rate=0.05, pan_depth=0.5,
    description="Wind moving through trees, sweeping side to side."))

register(VoiceConfig(
    "Mountain Stream", GROUP_NATURE, noise="white", env="volume",
    filt=("bandpass", 1800.0, 0.7), bright_base=3000.0, bright_mod=2600.0,
    floor=0.22, gain=0.36, width=0.7,
    description="A bright babbling stream over rocks."))

register(VoiceConfig(
    "Distant Thunder", GROUP_NATURE, noise="brown", env="volume",
    filt=("lowpass", 220.0, 0.7), bright_base=120.0, bright_mod=240.0,
    floor=0.16, gain=0.19, width=0.5,
    description="A deep, slow low-end rumble felt more than heard."))

register(VoiceConfig(
    "Soft Rainstorm", GROUP_NATURE, noise="pink", env="volume",
    filt=("lowpass", 4200.0, 0.6), bright_base=1800.0, bright_mod=3200.0,
    floor=0.18, gain=0.14, width=0.85,
    description="Broad rainfall with a hint of low rumble underneath."))

register(VoiceConfig(
    "Rain on a Roof", GROUP_NATURE, noise="brown", env="volume",
    filt=("lowpass", 2400.0, 0.9), bright_base=1500.0, bright_mod=1400.0,
    floor=0.85, gain=0.14, width=0.7, pan_rate=0.03, pan_depth=0.15,
    description="The warm, low patter of rain drumming on a roof overhead."))


# --- Tonal voice -----------------------------------------------------------

register(VoiceConfig(
    "Cosmic Drone", GROUP_TONAL, kind="tonal", env="volume",
    base_freq=110.0, floor=0.06, gain=0.56, width=0.6,
    partials=((0.5, 0.22), (1.0, 0.5), (1.005, 0.28), (2.0, 0.22),
              (3.0, 0.12), (5.0, 0.07)),
    description="A warm synth pad that blooms as you breathe in."))

# Steady tones (floor=1.0 => constant level, not breath-modulated): a tonic
# drone/shruti to chant against and a near-pure pitch reference for singers.
register(VoiceConfig(
    "Drone (Tonic)", GROUP_TONAL, kind="tonal", env="volume",
    base_freq=110.0, floor=1.0, gain=0.42, width=0.5,
    partials=((1.0, 0.5), (2.0, 0.26), (3.0, 0.14), (4.0, 0.08), (5.0, 0.05)),
    description="A steady tonic drone (shruti) to chant against; set the key."))

register(VoiceConfig(
    "Pitch Reference", GROUP_TONAL, kind="tonal", env="volume",
    base_freq=110.0, floor=1.0, gain=0.5, width=0.0,
    partials=((1.0, 1.0), (2.0, 0.12)),
    description="A steady, near-pure tone for matching pitch by ear."))


# --- Masking noise (steady broadband beds for relaxation / sleep) ----------

register(VoiceConfig(
    "Pink Noise", GROUP_NATURE, noise="pink", env="volume",
    filt=("lowpass", 7000.0, 0.7), bright_base=4000.0, bright_mod=0.0,
    floor=1.0, gain=0.16, width=0.9,            # calibrated: worst peak ~0.81 / 120 runs
    description="Steady pink noise - balanced, soothing masking."))

register(VoiceConfig(
    "Brown Noise", GROUP_NATURE, noise="brown", env="volume",
    filt=("lowpass", 1800.0, 0.7), bright_base=1100.0, bright_mod=0.0,
    floor=1.0, gain=0.16, width=0.9,            # calibrated: worst peak ~0.83 / 120 runs
    description="Steady brown noise - deep and soft, good for sleep."))

register(VoiceConfig(
    "Deep Sleep (Pink Noise)", GROUP_NATURE, noise="pink", env="volume",
    filt=("lowpass", 1600.0, 0.7), bright_base=1400.0, bright_mod=0.0,
    am_rate=0.8, am_depth=0.35,                 # a slow ~0.8 Hz swell
    floor=1.0, gain=0.16, width=0.9,            # calibrated like Pink/Brown (peak < 0.85)
    description="Soft pink noise swelling gently at ~0.8 Hz - a slow, even rise "
                "and fall to drift off to."))

register(VoiceConfig(
    "Cafe Murmur", GROUP_NATURE, noise="pink", env="volume",
    filt=("bandpass", 500.0, 0.5), bright_base=1100.0, bright_mod=400.0,
    floor=0.85, gain=0.22, width=0.85, pan_rate=0.04, pan_depth=0.2,
    description="A warm, distant hubbub - soft background chatter of a room."))

register(VoiceConfig(
    "Rain on a Tent", GROUP_NATURE, noise="pink", env="volume",
    filt=("bandpass", 1700.0, 0.8), bright_base=2800.0, bright_mod=0.0,
    floor=1.0, gain=0.34, width=0.5, pan_rate=0.03, pan_depth=0.15,
    description="Rain pattering on taut canvas - cosy under a tent."))

register(VoiceConfig(
    "Wind in Pines", GROUP_NATURE, noise="pink", env="volume",
    filt=("bandpass", 700.0, 0.6), bright_base=1400.0, bright_mod=300.0,
    floor=0.9, gain=0.30, width=0.7, pan_rate=0.05, pan_depth=0.35,
    description="A steady wind sighing through pine boughs, drifting side to side."))

register(VoiceConfig(
    "Fan (White Noise)", GROUP_NATURE, noise="pink", env="volume",
    filt=("lowpass", 1400.0, 0.7), bright_base=1400.0, bright_mod=0.0,
    floor=1.0, gain=0.17, width=0.3,
    description="A smooth, steady fan / white-noise machine for masking."))


# Additional voice families live in their own modules to keep files small;
# importing them registers each into the same registry.
from . import voices_human  # noqa: E402,F401
from . import voices_exercise  # noqa: E402,F401
from . import voices_technique  # noqa: E402,F401
from . import voices_sing  # noqa: E402,F401
from . import voices_synth  # noqa: E402,F401
from . import voices_extra  # noqa: E402,F401
from . import rhythm  # noqa: E402,F401
from . import textures  # noqa: E402,F401
from . import voices_cat  # noqa: E402,F401
from . import voices_breath_nature  # noqa: E402,F401  (natural-sound breaths)
from . import cosmic  # noqa: E402,F401  (generative Cosmic Music; needs textures)
from . import synth_bell  # noqa: E402,F401  (Bells & Gongs; needs textures)
from . import synth_drum  # noqa: E402,F401  (Drums; needs textures)
from . import synth_wind  # noqa: E402,F401  (Winds & Organs; needs textures)
from . import synth_fx  # noqa: E402,F401  (Environmental FX; needs textures)
