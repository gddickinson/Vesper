# Changelog

## 2026-11-13 — neutral names for sounds and a sleep session

George approved renaming the names that still sounded like brain-state, sleep-depth or
frequency-therapy claims. The sounds themselves are unchanged (same settings and texture IDs).

| Old name | New name | Where |
|---|---|---|
| Slow-Wave Pulse | Slow Swell | desktop, web |
| Deep Sleep (Pink Noise) | Pink Noise Swell | desktop, web, iOS |
| Deeper Sleep (guided session) | Drifting Deeper | desktop, iOS |
| Theta Pulse (6 Hz) | Soft Pulse (6 Hz) | iOS |
| Delta Pulse (2.5 Hz) | Low Pulse (2.5 Hz) | iOS |
| Solfeggio 528 Hz | 528 Hz Tone | iOS |
| Solfeggio 432 Hz | 432 Hz Tone | iOS |

Saved settings, presets and soundscapes that use an old name still load: the desktop maps old
names on read (`breathsim/renames.py`, also used by `voices.get_voice` and the sleep sessions), and
the iOS app maps its saved ambience and guided-session names (`AmbienceVoice.canonical`,
`SleepAids.canonical`). `tests/test_health_claims.py` now fails if an old name reappears in
user-visible text; `tests/test_renames.py` checks the aliases.

## 2026-11-12 — wording: health claims softened, safety disclaimer added

George's decision: "Soften or remove all health claims, with disclaimers if kept."

**Rewritten as gentle, non-medical descriptions** (desktop, web and iOS share the same text):
- Breath patterns: Coherent 5.5 ("Calms the nervous system" → "a slow, steady rhythm many people
  find relaxing"), Box ("used by Navy SEALs and clinicians" removed; "also called square breathing"),
  4-7-8 (now "popularised by Dr Andrew Weil"), Calming 4-6 ("engage the parasympathetic response"
  removed), Physiological Sigh ("the fastest known calmer" removed); iOS Resonance 6/min ("heart-coherence
  sweet spot" removed) and the iOS daily picks.
- Sounds: Deep Sleep (Pink Noise) ("stimulation shown to support slow-wave (deep) sleep" → "a slow,
  even rise and fall to drift off to"), Slow-Wave Pulse description; iOS pulse/solfeggio comments.
- Guided sessions: Let Go of Trying / Deeper Sleep / Put the Day to Rest descriptions (no "AASM
  well-established insomnia treatment", "shown to increase slow-wave sleep", "measurably speeds sleep
  onset"); two spoken lines softened ("you will wake refreshed", "healing depths"); hypnosis, safe-place,
  loving-kindness and autogenic descriptions no longer claim evidence of effect; the Physiological Sigh
  Reset program no longer promises to calm "in a couple of minutes".
- Sleep program (CBT-I): no longer called "the first-line treatment for chronic insomnia"; described as
  a self-guided take on the sleep-diary / sleep-window steps used in CBT-I, with a safety note in the
  dialog; the rotating sleep tips are phrased as suggestions, not physiology claims.
- One lecture line ("The whole nervous system ... lowers its guard" → "The whole body ..."), in the
  desktop lecture and the iOS lecture bundle.
- README / iOS README / INTERFACE.md: "Evidence-based calm", "melatonin-friendly", "both shown to shorten
  sleep onset", "Evidence-based sleep science", "HRV coherence" claims reworded.

**Disclaimer added** (one text, `breathsim/disclaimer.py`): not medical advice; stop if dizzy or
uncomfortable; talk to a professional about health conditions; breath-hold and fast-breathing patterns
not for pregnancy or heart / respiratory conditions; never use while driving. Shown in the desktop
About dialog and first-run welcome, the CBT-I dialog (plus a sleep-restriction note), README, the web
footer on every page, and the web Breathe and About pages.

**Guard:** `tests/test_health_claims.py` scans the shipped content (Python, web, iOS strings and lecture
bundle, README, INTERFACE.md) for a list of banned claim phrases, and checks every disclaimer surface.

Origin statements kept (accurate, not endorsements): 4-7-8 popularised by Dr Andrew Weil; Autogenic
Training by Johannes Schultz (1932); research references to Cordi & Rasch (2014) and Scullin et al.
(2018) now describe where an idea comes from, not what it does for you.
