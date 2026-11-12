// Home page: hero with a live breathing orb, real counts from the Python package, entry cards and modes.
import { route, api, app, list, esc, animate } from './core.js';
import { Scene } from './scene.js';
import { Pacer, fromApi } from './pacer.js';

const DOORS = [
  ['#/breathe', 'Breathe', 'The pacer: pick a pattern or a pace, watch the orb, add procedural breath sound and a nature bed, set a sleep timer.', 'a'],
  ['#/patterns', 'Patterns', 'All breath patterns from the desktop app, with their phase timings, pace and envelope shape.', 'b'],
  ['#/sounds', 'Sounds', 'Breath voices and ambience beds synthesised live with Web Audio from the same recipes as the app.', 'c'],
  ['#/programs', 'Guided programs', 'Multi-stage sessions that change pattern stage by stage, with their spoken instructions shown on screen.', 'a'],
  ['#/verify', 'Python vs JavaScript', 'The browser port of the breath clock, filters and timers checked number by number against the Python core.', 'b'],
  ['#/about', 'About', 'What Vesper is, what the full desktop app adds, and how to run both apps.', 'c'],
];

route('home', async () => {
  const [info, pats, modes] = await Promise.all([api('/info'), api('/patterns'), api('/modes')]);
  app().innerHTML = `
  <section class="hero home-hero">
    <div>
      <p class="kicker">Breathe · Relax · Sleep</p>
      <h1 class="glow">Vesper</h1>
      <p class="lead">${esc(info.summary)} A soft animated orb paces your breath while breath sound and nature
      ambience are synthesised in real time: no audio files. This web version runs the app's breath clock,
      soundscapes and sleep timer in your browser, for relaxation.</p>
      <a class="btn" href="#/breathe">Start breathing</a><a class="btn alt" href="#/about">About Vesper</a>
    </div>
    <div class="hero-orb"><canvas id="mini" role="img" aria-label="A breathing orb pacing the Coherent 5.5 pattern"></canvas></div>
  </section>
  <div class="tiles">
    <div class="tile"><b>${info.patterns}</b><span>breath patterns</span></div>
    <div class="tile"><b>${info.programs}</b><span>guided programs</span></div>
    <div class="tile"><b>${info.web_breath_voices + info.web_ambiences}</b><span>sounds in the browser</span></div>
    <div class="tile"><b>${info.voices}</b><span>voices in the desktop app</span></div>
    <div class="tile"><b>${info.lectures}</b><span>sleep-lectures (desktop)</span></div>
  </div>
  <div class="grid wide">${list(DOORS, ([href, t, d, c]) => `<a class="card door ${c}" href="${href}"><b>${t}</b><span>${d}</span></a>`)}</div>
  <h2>Quick start a mode</h2>
  <p class="mute">The desktop app's activity modes, with their pattern and sound bed (the narrated and sung parts stay in the desktop app).</p>
  <div class="chips">${list(modes.filter(m => m.name !== 'Read'), m => `<a class="chip" href="#/breathe?mode=${encodeURIComponent(m.name)}" title="${esc(m.description)}">${esc(m.name)}</a>`)}</div>`;
  const pacer = new Pacer(fromApi(pats[0]));
  const scene = new Scene(document.getElementById('mini'));
  pacer.start();
  const draw = () => { const f = pacer.frame(); scene.draw({ running: true, t: f.t, ...f.state, bpm: f.info.bpm, hint: '' }); };
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) draw(); else animate(draw);
});
