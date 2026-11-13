// AudioWorklet that synthesises Vesper's procedural sound in real time, sample by sample, with the same
// recipes as breathsim/tracks.py NoiseTrack (coloured noise -> static biquad -> brightness one-pole ->
// breath envelope -> auto-pan / tremolo -> gain) and breathsim/textures.py (Singing Bowl, Wind Chimes,
// Slow Swell). No samples are loaded. The page posts voice configs and the live breath levels.
import { designers, IIR, OnePoleLP, Noise, Struck, mulberry, panGains, tremolo, TWO_PI,
  BOWL_PARTIALS, BOWL_NOTES, CHIME_PARTIALS, CHIME_NOTES, CHIME_BASE } from './dsp_core.js';

const SQRT2 = Math.SQRT2;

export class NoiseVoice {
  constructor(cfg, sr, seed) {
    this.cfg = cfg; this.sr = sr; this.stereo = cfg.width > 0;
    const [type, fc, q] = cfg.filt;
    const mk = () => { const [b, a] = (designers[type] || designers.bandpass)(sr, fc, q); return new IIR(b, a); };
    this.ch = [{ n: new Noise(cfg.noise, seed), stat: mk(), br: new OnePoleLP() }];
    if (this.stereo) this.ch.push({ n: new Noise(cfg.noise, seed + 101), stat: mk(), br: new OnePoleLP() });
    this.level = null; this.pan = 0; this.am = 0;
    this.buf = new Float64Array(128); this.amp = new Float64Array(128);
  }
  render(L, R, n, target, phase, tone) {
    const cfg = this.cfg;
    const prev = this.level ?? target;
    this.level = prev + (target - prev) * 0.2;                // ~15 ms glide between posted levels
    let mean = 0;
    for (let i = 0; i < n; i++) { this.amp[i] = prev + (this.level - prev) * (i + 1) / n; mean += this.amp[i]; }
    mean /= n;
    let cutoff = (cfg.bright_base + cfg.bright_mod * mean) * tone;
    if (phase === 'exhale') cutoff *= cfg.exhale_mul;
    const outs = this.ch.map(c => {
      const x = c.n.generate(n, new Float64Array(n));
      c.stat.process(x, x); c.br.process(x, cutoff, this.sr, x);
      for (let i = 0; i < n; i++) x[i] *= this.amp[i];
      return x;
    });
    const l = outs[0], r = outs[1] || outs[0];
    const panOn = cfg.pan_rate > 0 && cfg.pan_depth > 0, amOn = cfg.am_rate > 0 && cfg.am_depth > 0;
    const pinc = TWO_PI * cfg.pan_rate / this.sr, ainc = TWO_PI * (cfg.am_rate || 0) / this.sr;
    for (let i = 0; i < n; i++) {
      let gl = 1, gr = 1, g = cfg.gain;
      if (panOn) { this.pan += pinc; const [a, b] = panGains(cfg.pan_depth * Math.sin(this.pan)); gl = a * SQRT2; gr = b * SQRT2; }
      if (amOn) { this.am += ainc; g *= tremolo(cfg.am_depth, this.am); }
      L[i] += l[i] * gl * g; R[i] += r[i] * gr * g;
    }
    this.pan %= TWO_PI; this.am %= TWO_PI;
  }
}

export class TextureVoice {
  constructor(cfg, sr, seed) {
    this.cfg = cfg; this.sr = sr; this.t = 0; this.rng = mulberry(seed); this.hits = [];
    this.next = cfg.texture === 'bowl' ? 1.0 : 0.8;
    if (cfg.texture === 'slowpulse') { this.pink = new Noise('pink', seed); this.brown = new Noise('brown', seed + 1); this.lp = new OnePoleLP(); }
  }
  schedule(end) {
    const r = this.rng;
    while (this.cfg.texture === 'bowl' && this.next < end) {
      const f0 = BOWL_NOTES[Math.floor(r() * BOWL_NOTES.length)];
      this.hits.push(new Struck(f0, BOWL_PARTIALS, this.next, 0.7 + 0.2 * r(), (r() * 2 - 1) * 0.3));
      this.next += 7 + 5 * r();
    }
    while (this.cfg.texture === 'chimes' && this.next < end) {
      let t = this.next;
      for (let k = 0, m = 2 + Math.floor(r() * 4); k < m; k++) {
        const ratio = CHIME_NOTES[Math.floor(r() * CHIME_NOTES.length)];
        this.hits.push(new Struck(CHIME_BASE * ratio, CHIME_PARTIALS, t, 0.35 + 0.25 * r(), (r() * 2 - 1) * 0.8, 0.8 + 0.5 * r()));
        t += 0.08 + 0.22 * r();
      }
      this.next += 3 + 5 * r();
    }
  }
  render(L, R, n) {
    const g = this.cfg.gain, dt = 1 / this.sr, end = this.t + n * dt;
    if (this.cfg.texture === 'slowpulse') {
      const bed = this.lp.process(this.pink.generate(n), 900, this.sr), br = this.brown.generate(n);
      for (let i = 0; i < n; i++) {
        const t = this.t + i * dt, pulse = 1 - 0.38 + 0.38 * (0.5 + 0.5 * Math.sin(TWO_PI * 0.8 * t - Math.PI / 2));
        const v = (bed[i] * 1.1 + br[i] * 0.35) * pulse * g; L[i] += v; R[i] += v;
      }
    } else {
      this.schedule(end);
      for (const h of this.hits) for (let i = 0; i < n; i++) { const v = h.value(this.t + i * dt) * g; L[i] += v * h.gl; R[i] += v * h.gr; }
      this.hits = this.hits.filter(h => !h.dead(end));
    }
    this.t = end;
  }
}

class VesperSound extends AudioWorkletProcessor {
  constructor() {
    super();
    this.voices = {}; this.levels = {}; this.phase = 'inhale'; this.tone = 1; this.master = 0; this.masterTarget = 0;
    this.L = new Float64Array(128); this.R = new Float64Array(128);
    this.port.onmessage = ({ data: m }) => {
      if (m.type === 'voice') {
        if (!m.cfg) delete this.voices[m.slot];
        else this.voices[m.slot] = m.cfg.kind === 'texture' ? new TextureVoice(m.cfg, sampleRate, m.seed || 42) : new NoiseVoice(m.cfg, sampleRate, m.seed || 1);
      } else if (m.type === 'state') {
        Object.assign(this.levels, m.levels); this.phase = m.phase; this.tone = m.tone ?? 1; this.masterTarget = m.master;
      }
    };
  }
  process(_inputs, outputs) {
    const out = outputs[0], n = out[0].length, L = this.L, R = this.R;
    L.fill(0, 0, n); R.fill(0, 0, n);
    for (const [slot, v] of Object.entries(this.voices)) v.render(L, R, n, this.levels[slot] ?? 0, this.phase, this.tone);
    const m0 = this.master; this.master += (this.masterTarget - m0) * 0.05;
    for (let i = 0; i < n; i++) {
      const m = m0 + (this.master - m0) * (i + 1) / n;
      const l = Math.tanh(L[i] * m), r = Math.tanh(R[i] * m);                    // dsp.soft_clip
      out[0][i] = Number.isFinite(l) ? l : 0; if (out[1]) out[1][i] = Number.isFinite(r) ? r : 0;
    }
    return true;
  }
}
registerProcessor('vesper-sound', VesperSound);

