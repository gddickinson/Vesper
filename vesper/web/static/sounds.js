// Sounds page: the breath voices and ambience beds the browser synthesises, each with its recipe (from the
// app's voice registry) and a live preview paced by the Calming 4-6 pattern.
import { route, api, app, list, esc, animate } from './core.js';
import { Soundscape } from './sound.js';
import { Pacer, fromApi } from './pacer.js';

function recipe(v) {
  if (v.kind === 'texture') return `procedural texture "${esc(v.texture)}" · gain ${v.gain}`;
  const [type, fc, q] = v.filt;
  const bits = [`${v.noise} noise`, `${type} ${fc} Hz, Q ${q}`, `brightness ${v.bright_base}${v.bright_mod ? ` + ${v.bright_mod}` : ''} Hz`,
    `follows ${v.env}`];
  if (v.floor) bits.push(`floor ${v.floor}`);
  if (v.width) bits.push('stereo');
  if (v.pan_rate) bits.push(`auto-pan ${v.pan_rate} Hz`);
  if (v.am_rate) bits.push(`swell ${v.am_rate} Hz`);
  return bits.map(esc).join(' · ');
}
const card = (v, slot) => `<div class="card"><b>${esc(v.name)}</b><small class="mono">${recipe(v)}</small>
  <span>${esc(v.description)}</span>
  <div class="acts"><button class="alt" data-slot="${slot}" data-name="${esc(v.name)}" aria-pressed="false">Play</button>
  <a class="btn alt" href="#/breathe?${slot === 'breath' ? 'voice' : 'ambience'}=${encodeURIComponent(v.name)}">Use in the pacer</a></div></div>`;

route('sounds', async () => {
  const [voices, pats] = await Promise.all([api('/voices'), api('/patterns')]);
  app().innerHTML = `
  <p class="kicker">Procedural sound</p>
  <h1>Sounds</h1>
  <p class="lead">Every sound here is synthesised live in an AudioWorklet from noise, filters and decaying partials,
  with the recipes and levels of the desktop app's voice registry. Breath voices swell and fade with the breath;
  ambience beds breathe more gently on top of a steady floor. No recordings are used.</p>
  <p class="small mute" id="msg">Previews breathe with the Calming 4-6 pattern. Press Play to start the audio (your browser needs a click first).</p>
  <h2>Breath voices (${voices.breath.length})</h2>
  <div class="grid patgrid">${list(voices.breath, v => card(v, 'breath'))}</div>
  <h2>Ambience beds (${voices.ambience.length})</h2>
  <div class="grid patgrid">${list(voices.ambience, v => card(v, 'ambience'))}</div>`;
  const sound = new Soundscape();
  const pacer = new Pacer(fromApi(pats.find(p => p.name.startsWith('Calming')) || pats[0]));
  const all = [...voices.breath, ...voices.ambience];
  app().addEventListener('click', async e => {
    const b = e.target.closest('button[data-slot]'); if (!b) return;
    const on = b.getAttribute('aria-pressed') !== 'true';
    app().querySelectorAll(`button[data-slot="${b.dataset.slot}"]`).forEach(x => { x.setAttribute('aria-pressed', 'false'); x.textContent = 'Play'; });
    sound.setVoice(b.dataset.slot, on ? all.find(v => v.name === b.dataset.name) : null);
    if (on) {
      b.setAttribute('aria-pressed', 'true'); b.textContent = 'Stop';
      pacer.start();
      if (!(await sound.start())) document.getElementById('msg').textContent = `Sound unavailable: ${sound.error}`;
    }
  });
  animate(() => { const f = pacer.frame(); sound.update(f.state, f.master); });
  window.addEventListener('hashchange', function h() { sound.close(); window.removeEventListener('hashchange', h); });
});
