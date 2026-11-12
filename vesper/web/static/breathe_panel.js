// Control panel for the Breathe page: builds the HTML and wires every control to the Pacer / Soundscape.
import { esc, list, $, slider } from './core.js';
import { patternForBpm } from './breath_engine.js';
import { fromApi } from './pacer.js';

const opt = (v, label, sel) => `<option value="${esc(v)}"${sel ? ' selected' : ''}>${esc(label)}</option>`;
const fmtT = s => s == null ? '' : `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
export { fmtT };

export function panelHtml(D, init) {
  return `
  <details class="grp" open><summary>Pattern</summary><div class="body">
    <label for="pat">Breath pattern</label>
    <select id="pat">${opt('__pace', 'Paced breathing (choose a rate)')}${list(D.pats, p => opt(p.name, `${p.name}  (${p.summary})`, p.name === init.pattern))}</select>
    <p class="small mute" id="pat-desc"></p>
    <div id="pace-box" hidden></div>
    <label class="check"><input type="checkbox" id="settle"> Settle in: start a little faster and ease to the pattern over 2.5 min</label>
    <div id="nat-box"></div>
  </div></details>
  <details class="grp" open><summary>Sound</summary><div class="body">
    <button id="snd" class="alt">Turn sound on</button> <span class="small mute" id="snd-msg"></span>
    <label for="bv">Breath voice</label>
    <select id="bv">${opt('', 'None')}${list(D.voices.breath, v => opt(v.name, v.name, v.name === init.voice))}</select>
    <label for="amb">Ambience bed</label>
    <select id="amb">${opt('', 'None')}${list(D.voices.ambience, v => opt(v.name, v.name, v.name === init.ambience))}</select>
    <p class="small mute" id="snd-desc"></p>
    <div id="vol-box"></div>
  </div></details>
  <details class="grp" open><summary>Sleep</summary><div class="body">
    <label>Sleep timer: fade the sound out over ${D.sleep.fade_seconds} s, then pause</label>
    <div class="seg" id="timer" role="group" aria-label="Sleep timer">${list(D.sleep.options, o => `<button data-m="${o.minutes}" class="${o.minutes === 0 ? 'on' : ''}" aria-pressed="${o.minutes === 0}">${esc(o.label)}</button>`)}</div>
    <div class="btns"><button id="wind" class="alt">Sleep wind-down</button></div>
    <p class="small mute">Wind-down: the breath slows from ${esc(D.sleep.wind_down.start)} to ${esc(D.sleep.wind_down.end)}
      over ${D.sleep.wind_down.seconds / 60} min and the volume eases out over the last 30% (the desktop Sleep mode).</p>
    <label for="scene">Scene</label>
    <select id="scene">${opt('orb', 'Orb', init.scene !== 'night')}${opt('night', 'Night sky', init.scene === 'night')}</select>
  </div></details>
  <details class="grp"><summary>Guided program</summary><div class="body">
    <label for="prog">Program</label>
    <select id="prog">${opt('', 'None')}${list(D.programs, p => opt(p.name, p.name, p.name === init.program))}</select>
    <p class="small mute" id="prog-desc"></p>
    <p class="stage-say" id="say" aria-live="polite"></p>
  </div></details>`;
}

export function wirePanel(root, D, pacer, sound, ui) {
  const byName = n => D.pats.find(p => p.name === n);
  const voice = (list_, n) => list_.find(v => v.name === n) || null;
  const pat = $('#pat', root), paceBox = $('#pace-box', root);
  let bpm = 6, longEx = false;
  const applyPattern = () => {
    const custom = pat.value === '__pace';
    paceBox.hidden = !custom;
    const p = custom ? patternForBpm(bpm, longEx) : fromApi(byName(pat.value));
    $('#pat-desc', root).textContent = p.description;
    pacer.choose(p, { settle: $('#settle', root).checked });
    $('#prog', root).value = ''; $('#say', root).textContent = ''; $('#prog-desc', root).textContent = '';
  };
  slider(paceBox, { id: 'bpm', label: 'Breaths per minute', min: 3, max: 20, step: 0.5, value: bpm }, v => { bpm = v; applyPattern(); });
  paceBox.insertAdjacentHTML('beforeend', '<label class="check"><input type="checkbox" id="longex"> Longer exhale (40 / 60)</label>');
  $('#longex', root).addEventListener('change', e => { longEx = e.target.checked; applyPattern(); });
  pat.addEventListener('change', applyPattern);
  $('#settle', root).addEventListener('change', applyPattern);
  slider($('#nat-box', root), { id: 'nat', label: 'Naturalness (per-breath variation)', min: 0, max: 1, step: 0.05, value: 0, fmt: v => v.toFixed(2) },
    v => { pacer.nat.amount = v; });
  slider($('#vol-box', root), { id: 'vol', label: 'Volume', min: 0, max: 1, step: 0.05, value: pacer.volume, fmt: v => Math.round(v * 100), unit: '%' },
    v => { pacer.volume = v; });

  const desc = () => {
    const b = voice(D.voices.breath, $('#bv', root).value), a = voice(D.voices.ambience, $('#amb', root).value);
    $('#snd-desc', root).textContent = [b && `${b.name}: ${b.description}`, a && `${a.name}: ${a.description}`].filter(Boolean).join(' ');
  };
  const setV = () => { sound.setVoice('breath', voice(D.voices.breath, $('#bv', root).value)); sound.setVoice('ambience', voice(D.voices.ambience, $('#amb', root).value)); desc(); };
  $('#bv', root).addEventListener('change', setV); $('#amb', root).addEventListener('change', setV);
  setV();
  $('#snd', root).addEventListener('click', async e => {
    const btn = e.target;
    if (sound.ok && sound.ctx.state === 'running') { await sound.suspend(); btn.textContent = 'Turn sound on'; return; }
    const ok = await sound.start();
    btn.textContent = ok ? 'Mute sound' : 'Sound unavailable';
    $('#snd-msg', root).textContent = ok ? '' : sound.error;
  });

  $('#timer', root).addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b) return;
    root.querySelectorAll('#timer button').forEach(x => { x.classList.toggle('on', x === b); x.setAttribute('aria-pressed', x === b); });
    pacer.armTimer(+b.dataset.m);
  });
  $('#wind', root).addEventListener('click', () => {
    const W = D.sleep.wind_down;
    pacer.startWind(fromApi(byName(W.start)), fromApi(byName(W.end)), W.seconds);
    pat.value = W.start; $('#prog', root).value = ''; pacer.start(); ui.refresh();
  });
  $('#scene', root).addEventListener('change', e => ui.setScene(e.target.value));

  const prog = $('#prog', root);
  pacer.onStage = st => {
    $('#say', root).textContent = st.say ? `“${st.say}”` : '';
    if (st.pattern && byName(st.pattern)) pat.value = st.pattern;
    if (st.ambience && voice(D.voices.ambience, st.ambience)) { $('#amb', root).value = st.ambience; setV(); }
    if (st.voice && voice(D.voices.breath, st.voice)) { $('#bv', root).value = st.voice; setV(); }
    if (st.scene) ui.setScene(st.scene === 'night' ? 'night' : 'orb');
  };
  prog.addEventListener('change', () => {
    const P = D.programs.find(p => p.name === prog.value);
    if (!P) { applyPattern(); return; }
    $('#prog-desc', root).textContent = `${P.description} ${P.stages.length} stages, ${P.minutes} min.`;
    pacer.startProgram(P); pacer.start(); ui.refresh();
  });
  return { applyPattern, setV };
}
