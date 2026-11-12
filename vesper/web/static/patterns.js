// Patterns page: every breath pattern from breathsim.patterns.PRESETS with its timings, pace, the lung-volume
// (solid) and airflow (dashed) envelopes over one cycle drawn by the JS breath clock, and a link to the pacer.
import { route, api, app, list, esc } from './core.js';
import { stateAt } from './breath_engine.js';
import { fromApi } from './pacer.js';
import { PHASE_HUE } from './scene.js';

function plot(cv, p) {
  const dpr = Math.min(2, devicePixelRatio || 1), w = cv.clientWidth, h = cv.clientHeight;
  cv.width = w * dpr; cv.height = h * dpr;
  const g = cv.getContext('2d'); g.scale(dpr, dpr);
  const cyc = p.cycle, n = 160;
  for (let i = 0; i < n; i++) {                    // phase-coloured baseline band
    const s = stateAt(fromApi(p), cyc * i / n);
    g.fillStyle = PHASE_HUE[s.phase] + '33'; g.fillRect(w * i / n, h - 4, w / n + 1, 4);
  }
  for (const [key, dash] of [['volume', []], ['airflow', [3, 3]]]) {
    g.beginPath(); g.setLineDash(dash); g.lineWidth = 1.6; g.strokeStyle = key === 'volume' ? '#69cfca' : '#b79ce0';
    for (let i = 0; i <= n; i++) {
      const s = stateAt(fromApi(p), Math.min(cyc * i / n, cyc - 1e-9));
      const x = w * i / n, y = (h - 8) - s[key] * (h - 12);
      i ? g.lineTo(x, y) : g.moveTo(x, y);
    }
    g.stroke();
  }
}

route('patterns', async () => {
  const pats = await api('/patterns');
  app().innerHTML = `
  <p class="kicker">Breath patterns</p>
  <h1>${pats.length} patterns</h1>
  <p class="lead">Each pattern is four phases in seconds: inhale, hold, exhale, hold. The curves show one cycle:
  lung fullness (solid, drives the orb) and airflow (dashed, drives breath-sound loudness). Descriptions are the
  desktop app's own. Fast patterns are best practised gently and briefly.</p>
  <div class="grid patgrid">${list(pats, (p, i) => `<div class="card">
    <b>${esc(p.name)}</b>
    <small class="mono">${esc(p.summary)} s · ${p.bpm.toFixed(1)} breaths/min · cycle ${p.cycle.toFixed(1)} s</small>
    <span>${esc(p.description)}</span>
    <canvas class="env" id="env${i}" role="img" aria-label="Volume and airflow over one ${esc(p.name)} cycle"></canvas>
    <div class="acts"><a class="btn" href="#/breathe?pattern=${encodeURIComponent(p.name)}">Breathe this</a></div>
  </div>`)}</div>`;
  pats.forEach((p, i) => plot(document.getElementById('env' + i), p));
});
