// Breathe page: the pacer. A canvas scene (orb or night sky) breathes with the chosen pattern, the audio
// worklet synthesises the breath voice + ambience in step, and the sleep timer / wind-down / programs run
// on the same clock. Query: ?mode=Sleep, ?pattern=<name>, ?program=<name>, ?ambience=<name>, ?voice=<name>.
import { route, api, app, $, esc, animate } from './core.js';
import { Scene } from './scene.js';
import { Pacer, fromApi } from './pacer.js';
import { Soundscape } from './sound.js';
import { panelHtml, wirePanel, fmtT } from './breathe_panel.js';

route('breathe', async (_args, q) => {
  const [pats, voices, programs, modes, sleep] = await Promise.all(
    ['/patterns', '/voices', '/programs', '/modes', '/sleep'].map(p => api(p)));
  const D = { pats, voices, programs, modes, sleep };
  const mode = modes.find(m => m.name === q.mode);
  const has = (l, n) => l.some(v => v.name === n);
  const init = {
    pattern: q.pattern || mode?.pattern || pats[0].name,
    voice: q.voice || (mode && has(voices.breath, mode.voice) ? mode.voice : 'Deep Calm'),
    ambience: q.ambience ?? (mode?.ambience || ''),
    scene: q.scene || (mode?.scene === 'night' ? 'night' : 'orb'),
    program: q.program || '',
  };
  app().innerHTML = `
  <p class="kicker">${mode ? esc(mode.name) + ' mode' : 'Breath pacer'}</p>
  <h1 class="h-small">${mode ? esc(mode.description) : 'Breathe with the orb'}</h1>
  ${mode?.effect && !has(voices.ambience, mode.effect) ? `<p class="small mute">The ${esc(mode.effect)} effect plays in the desktop app only.</p>` : ''}
  <div class="pace">
    <div class="pace-col">
      <div class="pace-stage"><canvas id="stage" role="img" aria-label="Breathing scene: grows as you breathe in, shrinks as you breathe out"></canvas></div>
      <div class="btns"><button id="go">Start</button><button id="reset" class="alt">Reset</button></div>
      <div class="readout" aria-live="off" id="readout"></div>
      <p class="small mute">For relaxation. Breathe gently and comfortably; if you feel light-headed, stop and breathe normally.</p>
    </div>
    <div class="panel panel-tight">${panelHtml(D, init)}</div>
  </div>`;
  const root = app();
  const pattern = pats.find(p => p.name === init.pattern) || pats[0];
  const pacer = new Pacer(fromApi(pattern));
  const sound = new Soundscape();
  const scene = new Scene($('#stage'), init.scene);
  const go = $('#go');
  const ui = {
    refresh: () => { go.textContent = pacer.running ? 'Pause' : 'Start'; },
    setScene: k => { scene.kind = k; $('#scene', root).value = k; },
  };
  const P = wirePanel(root, D, pacer, sound, ui);
  $('#pat', root).value = pattern.name;
  P.applyPattern();
  if (mode?.sleep) { $('#wind', root).click(); pacer.pause(); }        // Sleep mode arms the wind-down
  if (init.program) { $('#prog', root).value = init.program; $('#prog', root).dispatchEvent(new Event('change')); pacer.pause(); }
  ui.refresh();
  pacer.onDone = () => { ui.refresh(); root.querySelector('#timer button[data-m="0"]')?.click(); };

  go.addEventListener('click', async () => {
    pacer.toggle(); ui.refresh();
    if (pacer.running && !sound.ok && (sound.cfg.breath || sound.cfg.ambience)) {
      const ok = await sound.start();
      $('#snd', root).textContent = ok ? 'Mute sound' : 'Sound unavailable';
      if (!ok) $('#snd-msg', root).textContent = sound.error;
    }
  });
  $('#reset').addEventListener('click', () => { pacer.reset(); P.applyPattern(); ui.refresh(); });

  const out = $('#readout');
  let lastTxt = '';
  animate(() => {
    const f = pacer.frame(), i = f.info;
    const hint = i.stage ? `Stage ${i.stageNo}/${i.stages}: ${i.stage}` : i.wind != null ? 'Sleep wind-down'
      : i.settle != null ? 'Settling in' : '';
    scene.draw({ running: pacer.running, t: f.t, ...f.state, bpm: i.bpm, prog: i.prog, hint });
    sound.update(f.state, f.master);
    const parts = [`<span>pace <b>${i.bpm.toFixed(1)}</b>/min</span>`, `<span>elapsed <b>${fmtT(f.t)}</b></span>`,
      `<span>breaths <b>${f.state.cycle_index}</b></span>`];
    if (i.stage) parts.push(`<span>stage left <b>${fmtT(i.stageLeft)}</b></span>`, `<span>program left <b>${fmtT(i.totalLeft)}</b></span>`);
    if (i.wind != null) parts.push(`<span>wind-down <b>${Math.round(i.wind * 100)}%</b></span>`);
    if (i.timerLeft != null) parts.push(`<span>sleep timer <b>${i.fading ? 'fading' : fmtT(i.timerLeft)}</b></span>`);
    const txt = parts.join('');
    if (txt !== lastTxt) { out.innerHTML = txt; lastTxt = txt; }
  });
  // animate() owns the router's onLeave slot; close the audio context when the route changes too.
  window.addEventListener('hashchange', function h() { sound.close(); window.removeEventListener('hashchange', h); });
});
