# Optional XTTS-v2 narration engine

Vesper can use **XTTS-v2** (Coqui) for the bedtime storyteller — the
highest-fidelity offline voice we can drive on Apple Silicon (voice-cloning + 58
studio speakers, faster-than-real-time on Metal). It is **opt-in** and never
bundled:

- It is heavy (PyTorch + a ~1.8 GB model) and Apple-Silicon/CUDA-specific.
- Its model is under the **Coqui Public Model License — non-commercial only**.
- So the default stays **Kokoro** (Apache, zero-setup, real-time, commercial-safe)
  and the app degrades straight back to Kokoro / macOS `say` when XTTS is absent.

The heavy stack is kept **out of the app's own Python env**: synthesis runs in a
separate interpreter via a persistent worker subprocess (`breathsim/xtts_worker.py`,
driven by `breathsim/xtts_tts.py`). The model loads once (~20–40 s the first time),
then each sentence takes ~3 s on an M1 Max (RTF ≈ 0.8 on MPS, ≈ 1.3 on CPU).

## Measured on an M1 Max / 32 GB
| device | real-time factor |
|---|---|
| MPS (Metal) | **0.83×** (faster than real-time) |
| CPU | 1.33× (use for pre-rendering) |

## One-time setup

1. **Create a venv with the right pins** (the latest `coqui-tts` does *not* pull
   torch and currently **breaks on `transformers` 5.x**, so pin to the last 4.x):

   ```sh
   python3.11 -m venv ~/.vesper-xtts/venv
   ~/.vesper-xtts/venv/bin/pip install coqui-tts soundfile torch torchaudio \
       torchcodec "transformers>=4.57,<5"
   ```
   `torchcodec` needs system **FFmpeg** (`brew install ffmpeg`). Python 3.9–3.12.

2. **Write `~/.vesper-xtts/config.json`** pointing at that interpreter and a model
   cache directory:

   ```json
   {
     "python": "/Users/<you>/.vesper-xtts/venv/bin/python",
     "tts_home": "/Users/<you>/.vesper-xtts/tts_home",
     "device": "mps",
     "speakers": ["Daisy Studious", "..."]
   }
   ```
   The `speakers` list is optional (the worker reports the real list on first run);
   include it so the picker is fully populated before the model has loaded. The
   ~1.8 GB model downloads into `tts_home` on first synth (then fully offline).

   Env-var overrides also work: `VESPER_XTTS_PYTHON`, `VESPER_XTTS_HOME`,
   `VESPER_XTTS_DEVICE`.

## Using it

When configured, the Sleep **Narration voice** picker is **grouped** —
*Recommended*, *High quality · female/male (XTTS)* (each voice labelled with its
gender + timbre and a ★ for the cleanest), then Kokoro *British / American / Other*
by accent. Pick an XTTS voice and the storyteller routes it through XTTS; everything
else stays on the default engine. The first narrated line waits for the one-time
model load.

**Characters** also speak in a fitting XTTS voice when it's installed (e.g. Cat →
Daisy Studious, Owl → Damien Black), falling back to their Kokoro / `say` voice
otherwise. The **Sound ▸ "High-quality voices (XTTS)…"** menu item shows status and
the install command.

Worker errors are logged to `~/.vesper-xtts/worker.log`. The voices are studio
English; we label gender + timbre (measured) rather than claim regional accents.
