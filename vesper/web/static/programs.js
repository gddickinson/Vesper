// Programs page: the guided multi-stage sessions (breathsim.programs) with each stage's pattern and spoken line.
import { route, api, app, list, esc } from './core.js';

const durs = d => d ? d.map(x => +x.toFixed(2)).join('-') : '';
route('programs', async () => {
  const [progs, voices] = await Promise.all([api('/programs'), api('/voices')]);
  const known = new Set([...voices.breath, ...voices.ambience].map(v => v.name));
  app().innerHTML = `
  <p class="kicker">Guided programs</p>
  <h1>${progs.length} programs</h1>
  <p class="lead">Each program walks through stages on the breath clock; every stage starts its pattern cleanly at the
  inhale and shows its instruction. In the browser the pattern, scene and any synthesisable sound follow the stages;
  chants, sung exercises and spoken cues need the desktop app.</p>
  <div class="grid wide">${list(progs, p => `<div class="card">
    <b>${esc(p.name)}</b><small>${p.stages.length} stages · ${+p.minutes.toFixed(1)} min</small>
    <span>${esc(p.description)}</span>
    <ol class="stages">${list(p.stages, s => `<li><b>${esc(s.title)}</b> <span class="mono small">${+s.minutes.toFixed(2)} min · ${esc(s.pattern || '')}${s.pattern === 'Stage' ? ' ' + durs(s.durations) : ''}</span>
      ${s.voice && !known.has(s.voice) ? `<span class="tag">${esc(s.voice)}: desktop only</span>` : ''}
      ${s.say && s.say !== s.title ? `<br><span class="small mute">“${esc(s.say)}”</span>` : ''}</li>`)}</ol>
    <div class="acts"><a class="btn" href="#/breathe?program=${encodeURIComponent(p.name)}">Run in the pacer</a></div>
  </div>`)}</div>`;
});
