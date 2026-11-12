// Canvas scenes for the breath pacer, drawn in the spirit of the desktop app's Qt scenes
// (vesper/scenes.py OrbScene + the starry Sleep night; palette from vesper/theme.py): own canvas code.
// draw(c) takes the frame context { running, t, phase, volume, progress, cycle_frac, bpm, label, remaining, prog }.
import { rng } from './core.js';

export const PHASE_HUE = { inhale: '#69cfca', hold_full: '#86e3c4', exhale: '#b79ce0', hold_empty: '#5b7fb0' };
const BG = '#0a111e', NIGHT_BG = '#060a13', TEXT = '#e9eef7', MUTED = '#7b8da6', ACCENT_DIM = '#2c5560';

const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
export function blend(a, b, t) {
  t = Math.max(0, Math.min(1, t));
  const A = hex(a), B = hex(b);
  return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join('');
}
const glow = (h, k) => blend(h, '#ffffff', k);
const rgba = (h, a) => { const [r, g, b] = hex(h); return `rgba(${r},${g},${b},${Math.max(0, Math.min(1, a))})`; };

function motes(n, seed) {
  const r = rng(seed);
  return Array.from({ length: n }, () => ({ x: r(), y: r(), r: 0.6 + r() * 1.6, sx: (r() - 0.5) * 0.006,
    sy: -(0.004 + r() * 0.01), ph: r() * 6.2831, sp: 0.3 + r() * 0.6 }));
}
const mod1 = v => ((v % 1) + 1) % 1;

function disc(g, x, y, r, fill) { g.fillStyle = fill; g.beginPath(); g.arc(x, y, Math.max(0, r), 0, 2 * Math.PI); g.fill(); }
function radial(g, x, y, r, stops) {
  const gr = g.createRadialGradient(x, y, 0, x, y, Math.max(1e-3, r));
  stops.forEach(([o, c]) => gr.addColorStop(o, c));
  return gr;
}

export class Scene {
  constructor(canvas, kind = 'orb') {
    this.cv = canvas; this.g = canvas.getContext('2d'); this.kind = kind;
    this.motes = motes(16, 4); this.stars = motes(70, 9); this.rings = []; this.lastPhase = null;
  }
  fit() {
    const dpr = Math.min(2, window.devicePixelRatio || 1), w = this.cv.clientWidth, h = this.cv.clientHeight;
    if (this.cv.width !== Math.round(w * dpr) || this.cv.height !== Math.round(h * dpr)) {
      this.cv.width = Math.round(w * dpr); this.cv.height = Math.round(h * dpr);
    }
    this.g.setTransform(dpr, 0, 0, dpr, 0, 0);
    return [w, h];
  }
  draw(c) {
    const [w, h] = this.fit();
    if (!w || !h) return;
    if (this.kind === 'night') this.night(w, h, c); else this.orb(w, h, c);
  }
  orb(w, h, c) {
    const g = this.g, cx = w / 2, cy = h * 0.45, rMax = Math.min(w, h) * 0.29, rMin = rMax * 0.34;
    const vol = c.running ? c.volume : 0.5, rad = rMin + (rMax - rMin) * vol;
    const hue = c.running ? PHASE_HUE[c.phase] : ACCENT_DIM, t = c.t;
    g.fillStyle = BG; g.fillRect(0, 0, w, h);
    const R = Math.min(w, h) * 0.78;
    g.fillStyle = radial(g, cx, cy, R, [[0, rgba(blend(BG, hue, 0.13), 0.25 + 0.25 * vol)], [1, rgba(BG, 0)]]);
    g.fillRect(0, 0, w, h);
    // exhale rings: one gentle ring expands at each exhale onset
    if (c.running && c.phase !== this.lastPhase && c.phase === 'exhale') this.rings.push([t, hue]);
    this.lastPhase = c.phase;
    const speed = Math.min(w, h) * 0.14, maxr = rMax * 2.1;
    this.rings = this.rings.filter(r => (t - r[0]) * speed < maxr - rad && t >= r[0]).slice(-4);
    for (const [spawn, rh] of this.rings) {
      const rr = rad + (t - spawn) * speed, f = (rr - rad) / (maxr - rad + 1e-6);
      g.strokeStyle = rgba(glow(rh, 0.4), 0.45 * (1 - f)); g.lineWidth = Math.max(1, 2.5 * (1 - f));
      g.beginPath(); g.arc(cx, cy, rr, 0, 2 * Math.PI); g.stroke();
    }
    disc(g, cx, cy, rad * 1.55, radial(g, cx, cy, rad * 1.55, [[0, rgba(glow(hue, 0.4), 0.5 + 0.4 * vol)],
      [0.5, rgba(hue, 0.32 + 0.28 * vol)], [1, rgba(hue, 0)]]));
    disc(g, cx, cy, rad * 0.94, rgba(glow(hue, 0.18 + 0.16 * vol), 0.92));
    this.drawMotes(w, h, t, glow(hue, 0.5), c.running ? 0.3 : 0.16);
    g.strokeStyle = blend(BG, hue, 0.5); g.lineWidth = 1;
    g.beginPath(); g.arc(cx, cy, rMax, 0, 2 * Math.PI); g.stroke();
    if (c.running && c.bpm >= 5 && c.bpm <= 7) {            // coherence cue near ~6 breaths/min
      const pulse = 0.5 + 0.5 * Math.sin(2 * Math.PI * c.cycle_frac);
      g.strokeStyle = rgba('#86e6bf', 0.1 + 0.15 * pulse); g.lineWidth = 2.5;
      g.beginPath(); g.arc(cx, cy, rMax * 1.33, 0, 2 * Math.PI); g.stroke();
    }
    if (c.running) {
      const a = -Math.PI / 2 + 2 * Math.PI * c.cycle_frac;
      disc(g, cx + rMax * Math.cos(a), cy + rMax * Math.sin(a), 5, glow(hue, 0.55));
      const rp = rMax * 1.08;
      g.strokeStyle = blend(BG, hue, 0.3); g.lineWidth = 2; g.beginPath(); g.arc(cx, cy, rp, 0, 2 * Math.PI); g.stroke();
      g.strokeStyle = glow(hue, 0.45); g.lineWidth = 4; g.beginPath();
      g.arc(cx, cy, rp, -Math.PI / 2, -Math.PI / 2 + 2 * Math.PI * Math.max(0, Math.min(1, c.progress))); g.stroke();
      if (c.prog != null) {
        g.strokeStyle = glow(hue, 0.25); g.lineWidth = 3; g.beginPath();
        g.arc(cx, cy, rMax * 1.18, -Math.PI / 2, -Math.PI / 2 + 2 * Math.PI * Math.max(0, Math.min(1, c.prog))); g.stroke();
      }
    }
    this.overlay(w, cx, cy - 18, cy + 30, cy + rMax + 56, c, hue);
  }
  night(w, h, c) {
    const g = this.g, t = c.t, vol = c.running ? c.volume : 0.5, hue = c.running ? PHASE_HUE[c.phase] : ACCENT_DIM;
    const sky = g.createLinearGradient(0, 0, 0, h);
    sky.addColorStop(0, NIGHT_BG); sky.addColorStop(1, blend(NIGHT_BG, '#1f2e47', 0.6));
    g.fillStyle = sky; g.fillRect(0, 0, w, h);
    for (const s of this.stars) {
      const tw = 0.5 + 0.5 * Math.sin(t * s.sp + s.ph);
      disc(g, s.x * w, s.y * h * 0.8, s.r * 0.7, rgba('#cfdcf2', 0.15 + 0.55 * tw * (0.6 + 0.4 * vol)));
    }
    const mx = w * 0.5, my = h * 0.42, mr = Math.min(w, h) * (0.09 + 0.035 * vol);
    disc(g, mx, my, mr * (2.4 + 0.9 * vol), radial(g, mx, my, mr * (2.4 + 0.9 * vol), [[0, rgba('#eef1f8', 0.18 + 0.12 * vol)], [1, rgba('#eef1f8', 0)]]));
    disc(g, mx, my, mr, radial(g, mx - mr * 0.3, my - mr * 0.3, mr * 1.4, [[0, '#f6f8fc'], [1, '#c9d2e3']]));
    const hill = h * 0.86;
    g.fillStyle = '#04070d'; g.beginPath(); g.moveTo(0, h);
    for (let x = 0; x <= w; x += 8) g.lineTo(x, hill + Math.sin(x / w * 5.2 + 1.1) * h * 0.03);
    g.lineTo(w, h); g.fill();
    this.overlay(w, mx, my + mr + 46, my + mr + 88, h - 24, c, hue);
  }
  drawMotes(w, h, t, hue, alpha) {
    for (const m of this.motes) {
      const tw = 0.5 + 0.5 * Math.sin(t * m.sp + m.ph);
      disc(this.g, mod1(m.x + m.sx * t) * w, mod1(m.y + m.sy * t) * h, m.r * (0.7 + 0.5 * tw), rgba(hue, alpha * (0.15 + 0.6 * tw)));
    }
  }
  overlay(w, cx, labelY, countY, hintY, c, hue) {
    const g = this.g, mw = Math.max(40, 2 * Math.min(cx, w - cx) - 16);
    const text = (s, y, col, size, bold) => {
      if (!s) return;
      g.font = `${bold ? '600 ' : ''}${size}px -apple-system, "Helvetica Neue", sans-serif`;
      const tw = g.measureText(s).width;
      if (tw > mw) g.font = `${bold ? '600 ' : ''}${Math.max(9, Math.floor(size * mw / tw))}px -apple-system, "Helvetica Neue", sans-serif`;
      g.fillStyle = col; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, cx, y);
    };
    text(c.running ? c.label : 'Ready', labelY, blend(TEXT, hue, 0.3), 26);
    if (c.running && c.remaining > 0.05) text(String(Math.ceil(c.remaining - 1e-6)), countY, TEXT, 44, true);
    text(c.hint || '', hintY, MUTED, 13);
  }
}
