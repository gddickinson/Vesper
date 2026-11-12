// node vesper/web/static/sound_worklet.test.mjs: the worklet's synthesis against the Python NoiseTrack.
// The noise itself is random, so levels are compared statistically (RMS within 12%) at a steady mid-inhale
// state; textures must stay finite and below clipping.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { voiceLevel } from './breath_engine.js';

globalThis.AudioWorkletProcessor = class { constructor() { this.port = {}; } };
globalThis.registerProcessor = () => {};
const { NoiseVoice, TextureVoice } = await import('./sound_worklet.js');
const here = dirname(fileURLToPath(import.meta.url));
const F = JSON.parse(readFileSync(join(here, '../../../tests/fixtures/vesper_reference.json'), 'utf8'));

const st = { phase: 'inhale', progress: 0.5, volume: 1, airflow: 1, tone_mod: 1 };
const voices = JSON.parse(readFileSync(join(here, '../../../tests/fixtures/web_voices.json'), 'utf8'));
const cfgOf = n => [...voices.breath, ...voices.ambience].find(v => v.name === n);
let bad = 0;
const { sr, seconds, rows } = F.levels;
for (const row of rows) {
  const cfg = cfgOf(row.name), v = new NoiseVoice(cfg, sr, 3), n = 128, L = new Float64Array(n), R = new Float64Array(n);
  let sl = 0, sr2 = 0, cnt = 0;
  const lvl = voiceLevel(cfg, st);
  for (let b = 0; b < Math.floor(seconds * sr / n); b++) {
    L.fill(0); R.fill(0); v.render(L, R, n, lvl, st.phase, 1);
    if (b * n >= sr) for (let i = 0; i < n; i++) { sl += L[i] * L[i]; sr2 += R[i] * R[i]; cnt++; }
  }
  const jl = Math.sqrt(sl / cnt), jr = Math.sqrt(sr2 / cnt);
  const ok = Math.abs(jl / row.rms_l - 1) < 0.12 && Math.abs(jr / row.rms_r - 1) < 0.12;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${row.name}: RMS L/R JS ${jl.toFixed(4)}/${jr.toFixed(4)} vs Python ${row.rms_l.toFixed(4)}/${row.rms_r.toFixed(4)}`);
  if (!ok) bad++;
}
for (const name of ['Singing Bowl', 'Wind Chimes', 'Slow-Wave Pulse']) {
  const v = new TextureVoice(cfgOf(name), 48000, 42), n = 128, L = new Float64Array(n), R = new Float64Array(n);
  let peak = 0, sum = 0, cnt = 0;
  for (let b = 0; b < 48000 * 40 / n; b++) {
    L.fill(0); R.fill(0); v.render(L, R, n);
    for (let i = 0; i < n; i++) { if (!Number.isFinite(L[i]) || !Number.isFinite(R[i])) bad++; peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i])); sum += L[i] * L[i]; cnt++; }
  }
  const ok = peak < 1.2 && sum > 0;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}: 40 s peak ${peak.toFixed(3)}, RMS ${Math.sqrt(sum / cnt).toFixed(4)}`);
  if (!ok) bad++;
}
if (bad) process.exit(1);
