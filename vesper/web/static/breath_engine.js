// Breath clock ported from breathsim (patterns.py, naturalness.py, controller.py, envelopes.py).
// Pure functions, no DOM: used by the pages, the audio worklet driver and breath_engine.test.mjs,
// which checks every number against tests/fixtures/vesper_reference.json written by the Python code.

export const INHALE = 'inhale', HOLD_FULL = 'hold_full', EXHALE = 'exhale', HOLD_EMPTY = 'hold_empty';
export const PHASES = [INHALE, HOLD_FULL, EXHALE, HOLD_EMPTY];
export const PHASE_LABELS = { inhale: 'Breathe In', hold_full: 'Hold', exhale: 'Breathe Out', hold_empty: 'Hold' };

// A pattern is { name, inhale, hold_full, exhale, hold_empty, description }.
export const pattern = (name, inhale, hold_full, exhale, hold_empty, description = '') =>
  ({ name, inhale, hold_full, exhale, hold_empty, description });
export const durations = p => [p.inhale, p.hold_full, p.exhale, p.hold_empty];
export const cycleOf = p => Math.max(0.001, p.inhale + p.hold_full + p.exhale + p.hold_empty);
export const summary = p => durations(p).map(d => String(+d.toFixed(2))).join('-');
export const bpmOf = p => 60 / cycleOf(p);

// Python's float floor division (t // c), including its rounding rule, so cycle indices match exactly.
export function floorDiv(vx, wx) {
  let mod = vx % wx;
  let div = (vx - mod) / wx;
  if (mod && ((wx < 0) !== (mod < 0))) { mod += wx; div -= 1; }
  if (!div) return 0;
  let fd = Math.floor(div);
  if (div - fd > 0.5) fd += 1;
  return fd;
}

const raisedCos = p => 0.5 - 0.5 * Math.cos(Math.PI * p);

function volumeAt(phase, p) {
  if (phase === INHALE) return raisedCos(p);
  if (phase === HOLD_FULL) return 1;
  if (phase === EXHALE) return raisedCos(1 - p);
  return 0;
}

const airflowAt = (phase, p) => (phase === INHALE || phase === EXHALE) ? Math.sin(Math.PI * p) : 0;

// patterns.state_at: the breath state of pattern p at t seconds.
export function stateAt(p, t) {
  const cycle = cycleOf(p);
  if (t < 0) t = 0;
  const cycleIndex = floorDiv(t, cycle);
  const pos = t - cycleIndex * cycle;
  const ds = durations(p);
  let acc = 0, chosen = null, last = null;
  for (let i = 0; i < 4; i++) {
    const dur = ds[i];
    if (dur <= 0) continue;
    last = [PHASES[i], dur, acc];
    if (pos < acc + dur) { chosen = last; break; }
    acc += dur;
  }
  if (!chosen) chosen = last || [INHALE, cycle, 0];
  const [phase, dur, start] = chosen;
  let pr = dur > 0 ? (pos - start) / dur : 0;
  pr = Math.min(Math.max(pr, 0), 1);
  return { phase, progress: pr, remaining: dur * (1 - pr), volume: volumeAt(phase, pr),
    airflow: airflowAt(phase, pr), cycle_index: cycleIndex, label: PHASE_LABELS[phase],
    cycle_frac: Math.min(1, Math.max(0, pos / cycle)), pitch_mod: 0, tone_mod: 1 };
}

// patterns.pattern_for_bpm: a smooth hold-free pattern (Python's round(x, 2) on the halves).
// Python's round(x, 2): nearest by exact decimal value (toFixed), half-to-even on exact ties.
export function round2(x) {
  const y = x * 100, f = Math.floor(y);
  if (y - f === 0.5 && Number.isInteger(f)) return (f % 2 === 0 ? f : f + 1) / 100;
  return Number(x.toFixed(2));
}
export function patternForBpm(bpm, longExhale = false) {
  const cycle = 60 / Math.max(1, +bpm);
  const inh = cycle * (longExhale ? 0.4 : 0.5);
  const exh = cycle - inh;
  return pattern('Custom', round2(inh), 0, round2(exh), 0,
    `Paced breathing at ${Number((+bpm).toPrecision(6))}/min (${longExhale ? 'longer exhale' : 'even'}).`);
}

// --- naturalness.py: deterministic per-breath variation from an integer hash ---
const PHASE_VAR = 0.30, DEPTH_VAR = 0.35, PITCH_VAR = 0.6, TONE_VAR = 0.30;
export function hash01(seed, k, i) {
  let h = (Math.imul(seed, 2654435761 | 0) + Math.imul(k + 1, 40503) + Math.imul(i + 1, 2246822519 | 0)) >>> 0;
  h = (h ^ (h >>> 15)) >>> 0;
  h = Math.imul(h, 2246822519 | 0) >>> 0;
  h = (h ^ (h >>> 13)) >>> 0;
  h = Math.imul(h, 3266489917 | 0) >>> 0;
  h = (h ^ (h >>> 16)) >>> 0;
  return h / 4294967295;
}
const signed = (s, k, i) => hash01(s, k, i) * 2 - 1;

export class Naturalness {
  constructor({ amount = 0, timing = true, depth = true, pitch = true, tone = true, seed = 1 } = {}) {
    Object.assign(this, { amount, timing, depth, pitch, tone, seed });
  }
  get on() { return this.amount > 1e-3 && (this.timing || this.depth || this.pitch || this.tone); }
  phaseFactors(k) { const a = this.amount * PHASE_VAR; return [0, 1, 2, 3].map(i => Math.max(0.15, 1 + a * signed(this.seed, k, i))); }
  depthFactor(k) { return 1 - this.amount * DEPTH_VAR * hash01(this.seed, k, 4); }
  pitchMod(k) { return this.amount * PITCH_VAR * signed(this.seed, k, 5); }
  toneMod(k) { return 1 + this.amount * TONE_VAR * signed(this.seed, k, 6); }
}

// controller.BreathController.state_at: optional naturalness keeps the cycle length fixed and jitters
// the phase split per cycle, so cycle boundaries stay at k * cycle.
export function jittered(p, nat, k) {
  const f = nat.phaseFactors(k);
  const d = [p.inhale * f[0], p.hold_full * f[1], p.exhale * f[2], p.hold_empty * f[3]];
  const s = d[0] + d[1] + d[2] + d[3];
  if (s <= 0) return p;
  const sc = cycleOf(p) / s;
  return pattern(p.name, d[0] * sc, d[1] * sc, d[2] * sc, d[3] * sc);
}

export function controllerState(p, nat, t, patternT0 = 0) {
  const tt = Math.max(0, t - patternT0);
  if (!nat || !nat.on) return stateAt(p, tt);
  const cycle = cycleOf(p);
  const k = Math.trunc(floorDiv(tt, cycle));
  const within = tt - k * cycle;
  const base = stateAt(nat.timing ? jittered(p, nat, k) : p, within);
  let vol = base.volume, air = base.airflow;
  if (nat.depth) { const d = nat.depthFactor(k); vol *= d; air *= d; }
  return { ...base, cycle_index: k, volume: vol, airflow: air,
    pitch_mod: nat.pitch ? nat.pitchMod(k) : 0, tone_mod: nat.tone ? nat.toneMod(k) : 1 };
}

// --- envelopes.py ---
export function windowEnv(phase, target, p, attack = 'smooth') {
  if (phase !== target) return 0;
  if (attack === 'explosive') { const rise = 0.025; return p < rise ? raisedCos(p / rise) : Math.exp(-(p - rise) * 5.5); }
  if (attack === 'swell') return Math.sin(Math.PI * p);
  const edge = 0.16;
  if (p < edge) return raisedCos(p / edge);
  if (p > 1 - edge) return raisedCos((1 - p) / edge);
  return 1;
}

export function envelope(env, s, { attack = 'smooth', attackIn = 'smooth', inhaleLevel = 1, exhaleLevel = 1 } = {}) {
  const ph = s.phase, p = s.progress;
  if (env === 'airflow') return s.airflow;
  if (env === 'volume') return s.volume;
  if (env === 'exhale') return windowEnv(ph, EXHALE, p, attack);
  if (env === 'inhale') return windowEnv(ph, INHALE, p, attack);
  if (env === 'breath') {
    if (ph === INHALE) return inhaleLevel * windowEnv(ph, INHALE, p, attackIn);
    if (ph === EXHALE) return exhaleLevel * windowEnv(ph, EXHALE, p, attack);
    return 0;
  }
  if (env === 'breath_both') return Math.max(windowEnv(ph, INHALE, p, attack), windowEnv(ph, EXHALE, p, attack));
  return s.airflow;
}

// tracks._env_value: a voice's level for a state (floor lifts ambiences off silence).
export const voiceLevel = (cfg, s) => cfg.floor + (1 - cfg.floor) * envelope(cfg.env, s);
