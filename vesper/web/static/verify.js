// Verify page: runs every Python-vs-JavaScript comparison live in this browser against /api/reference
// (numbers produced by the real breathsim code) and shows the agreement per area.
import { route, api, app, list, esc } from './core.js';
import { runChecks } from './verify_checks.js';

route('verify', async () => {
  const F = await api('/reference');
  const t0 = performance.now(), areas = runChecks(F), ms = performance.now() - t0;
  const total = areas.reduce((a, x) => a + x.checks, 0), fails = areas.reduce((a, x) => a + x.failures.length, 0);
  app().innerHTML = `
  <p class="kicker">Python vs JavaScript</p>
  <h1>${fails ? `${fails} mismatches` : 'All checks agree'}</h1>
  <p class="lead">The web pacer runs a JavaScript port of Vesper's breath clock, filters and timers. This page compares it,
  in your browser, with ${total.toLocaleString()} numbers produced by the Python code (${ms.toFixed(0)} ms).
  Tolerance: relative difference 1e-9 (1e-8 for long filter runs).</p>
  <div class="scroll"><table><thead><tr><th>Area</th><th>Python source</th><th>Checks</th><th>Worst rel. difference</th><th>Result</th></tr></thead>
  <tbody>${list(areas, a => `<tr class="${a.failures.length ? '' : 'ok-row'}"><td>${esc(a.name)}</td><td class="mono">${esc(a.source)}</td>
    <td>${a.checks}</td><td class="mono">${a.worst.toExponential(2)}</td>
    <td>${a.failures.length ? `<span class="err">${a.failures.length} failed</span><br><span class="small">${esc(a.failures.slice(0, 3).join('; '))}</span>` : 'agree'}</td></tr>`)}</tbody></table></div>
  <h2>Sound levels</h2>
  <p>The noise itself is random, so the synthesised sound is checked statistically by the node test
  <code>sound_worklet.test.mjs</code>: each breath voice and ambience bed rendered by the AudioWorklet code lands within
  12% of the RMS level of the Python <code>NoiseTrack</code> for the same recipe (in practice within about 1%).</p>
  <div class="scroll"><table><thead><tr><th>Voice</th><th>Python RMS (left / right)</th></tr></thead>
  <tbody>${list(F.levels.rows, r => `<tr><td>${esc(r.name)}</td><td class="mono">${r.rms_l.toFixed(4)} / ${r.rms_r.toFixed(4)}</td></tr>`)}</tbody></table></div>
  <p class="small mute">Regenerate the reference with <code>python scripts/make_js_fixtures.py</code>; <code>pytest tests/test_web.py</code>
  fails if it is out of date and runs the node tests.</p>`;
});
