// DSP building blocks ported from breathsim/dsp.py (RBJ biquads, one-pole LP, coloured noise) plus the
// struck-resonator texture used by Singing Bowl / Wind Chimes (breathsim/textures.py). No DOM, no Web
// Audio: imported by the audio worklet (sound_worklet.js) and by dsp_core.test.mjs.

export const TWO_PI = 2 * Math.PI;
const clampFc = (fc, sr) => Math.min(Math.max(fc, 20), sr * 0.45);

function norm(b0, b1, b2, a0, a1, a2) { return [[b0 / a0, b1 / a0, b2 / a0], [1, a1 / a0, a2 / a0]]; }

export function lowpass(sr, fc, q = 0.707) {
  const w0 = TWO_PI * clampFc(fc, sr) / sr, cw = Math.cos(w0), al = Math.sin(w0) / (2 * q);
  return norm((1 - cw) / 2, 1 - cw, (1 - cw) / 2, 1 + al, -2 * cw, 1 - al);
}
export function highpass(sr, fc, q = 0.707) {
  const w0 = TWO_PI * clampFc(fc, sr) / sr, cw = Math.cos(w0), al = Math.sin(w0) / (2 * q);
  return norm((1 + cw) / 2, -(1 + cw), (1 + cw) / 2, 1 + al, -2 * cw, 1 - al);
}
export function bandpass(sr, fc, q = 1) {
  const w0 = TWO_PI * clampFc(fc, sr) / sr, cw = Math.cos(w0), al = Math.sin(w0) / (2 * q);
  return norm(al, 0, -al, 1 + al, -2 * cw, 1 - al);
}
export const designers = { lowpass, highpass, bandpass };

// scipy.signal.lfilter (transposed direct form II) with state kept across blocks; a[0] must be 1.
export class IIR {
  constructor(b, a) { this.b = b; this.a = a; this.z = new Float64Array(Math.max(b.length, a.length) - 1); }
  process(x, out = new Float64Array(x.length)) {
    const { b, a, z } = this, n = z.length;
    for (let j = 0; j < x.length; j++) {
      const xi = x[j], y = (b[0] || 0) * xi + (n ? z[0] : 0);
      for (let i = 0; i < n; i++) z[i] = (b[i + 1] || 0) * xi + (i + 1 < n ? z[i + 1] : 0) - (a[i + 1] || 0) * y;
      out[j] = y;
    }
    return out;
  }
}

// dsp.OnePoleLP: cutoff may change per block without clicks.
export class OnePoleLP {
  constructor() { this.z = 0; }
  process(x, fc, sr, out = new Float64Array(x.length)) {
    const alpha = 1 - Math.exp(-TWO_PI * clampFc(fc, sr) / sr), k = 1 - alpha;
    let z = this.z;
    for (let j = 0; j < x.length; j++) { const y = alpha * x[j] + z; z = k * y; out[j] = y; }
    this.z = z;
    return out;
  }
}

// Paul Kellet's economy pink filter and the leaky-integrator brown filter (dsp.py), with dsp._SCALE.
export const PINK_B = [0.049922035, -0.095993537, 0.050612699, -0.004408786];
export const PINK_A = [1.0, -2.494956002, 2.017265875, -0.522189400];
export const BROWN_B = [1.0], BROWN_A = [1.0, -0.99];
export const SCALE = { white: 1.0, pink: 12.0, brown: 0.141 };

// Seeded uniform RNG (mulberry32) and Gaussian deviates (Box-Muller), standing in for numpy's generator.
export function mulberry(seed = 1) {
  let s = seed >>> 0;
  return () => { s = (s + 0x6D2B79F5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

export class Noise {
  constructor(kind = 'white', seed = 1) {
    this.kind = kind; this.rand = mulberry(seed); this.spare = null;
    this.filter = kind === 'pink' ? new IIR(PINK_B, PINK_A) : kind === 'brown' ? new IIR(BROWN_B, BROWN_A) : null;
    this.scale = SCALE[kind] ?? 1;
  }
  gauss() {
    if (this.spare !== null) { const v = this.spare; this.spare = null; return v; }
    const u = 1 - this.rand(), v = this.rand(), r = Math.sqrt(-2 * Math.log(u));
    this.spare = r * Math.sin(TWO_PI * v);
    return r * Math.cos(TWO_PI * v);
  }
  generate(n, out = new Float64Array(n)) {
    for (let i = 0; i < n; i++) out[i] = this.gauss();
    if (this.filter) this.filter.process(out, out);
    for (let i = 0; i < n; i++) out[i] *= this.scale;
    return out;
  }
}

// tracks.SynthBreathTrack / NoiseTrack tremolo law: gain = 1 - depth * (1 + sin(phase)) / 2.
export const tremolo = (depth, phase) => 1 - depth * 0.5 * (1 + Math.sin(phase));

// Equal-power pan used by the tracks: pan in -1..1 -> [left, right].
export const panGains = pan => { const th = (pan + 1) * Math.PI / 4; return [Math.cos(th), Math.sin(th)]; };

// textures._Struck: decaying inharmonic partials with a 2 ms attack; partials are [ratio, amp, decay_s].
export class Struck {
  constructor(f0, partials, t0, amp, pan, decayScale = 1) {
    this.f = partials.map(p => f0 * p[0]); this.pa = partials.map(p => p[1]);
    this.pd = partials.map(p => p[2] * decayScale); this.t0 = t0;
    this.amp = amp / (this.pa.reduce((a, b) => a + b, 0) + 1e-9);
    [this.gl, this.gr] = panGains(pan);
    this.dmax = Math.max(...this.pd);
  }
  value(t) {
    const ts = t - this.t0;
    if (ts < 0) return 0;
    const atk = Math.min(1, ts / 0.002);
    let v = 0;
    for (let i = 0; i < this.f.length; i++) v += this.pa[i] * Math.sin(TWO_PI * this.f[i] * t) * atk * Math.exp(-ts / this.pd[i]);
    return v * this.amp;
  }
  dead(t) { return t - this.t0 > this.dmax * 7; }
}

export const BOWL_PARTIALS = [[1.0, 1.0, 5.5], [1.005, 0.5, 5.5], [2.0, 0.5, 4.0], [2.7, 0.35, 3.0], [4.8, 0.18, 2.0]];
export const BOWL_NOTES = [196.0, 220.0, 261.6, 293.7];
export const CHIME_PARTIALS = [[1.0, 1.0, 2.6], [2.0, 0.4, 1.8], [3.8, 0.2, 1.0]];
export const CHIME_NOTES = [1, 9 / 8, 5 / 4, 3 / 2, 5 / 3, 2, 9 / 4];
export const CHIME_BASE = 523.25;
