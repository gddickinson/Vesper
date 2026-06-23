"""breathsim -- procedural breathing-sound meditation pacer.

Modules
-------
patterns    BreathPattern, preset library, breath-cycle envelope math.
dsp         Coloured noise generators and stateful filters.
tracks      NoiseTrack / TonalTrack / SampleTrack renderers.
voices      VoiceConfig registry (breath, nature and tonal voices).
controller  BreathController -- session clock and breath state.
engine      AudioEngine -- real-time sounddevice mixing with crossfades.
speech      Optional macOS spoken phase cues in different accents.
samples     Optional sampled-loop voices loaded from assets/sounds/.
gui         Tkinter application (see breathsim.gui).

See INTERFACE.md for the full navigation map.
"""

__version__ = "1.0.0"
