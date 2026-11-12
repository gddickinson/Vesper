// About page: what Vesper is, what is in the browser version, how to run both apps, credits (from the README).
import { route, api, app, esc } from './core.js';

route('about', async () => {
  const [info, sleep] = await Promise.all([api('/info'), api('/sleep')]);
  app().innerHTML = `
  <p class="kicker">About</p>
  <h1>Vesper</h1>
  <p class="lead">${esc(info.summary)} A glowing avatar breathes with you, lip-syncs a procedural bedtime storyteller,
  and is wrapped in fully procedural breath, voice, chant and nature sound, with no audio assets required.</p>
  <div class="callout">Vesper is a relaxation tool. It is not a medical device and is not medical advice. If a pattern
  makes you light-headed or uncomfortable, stop and breathe normally.</div>
  <h2>In this web version</h2>
  <ul>
    <li><b>The breath clock</b>: the ${info.patterns} patterns, paced breathing at any rate, the optional per-breath
      "naturalness" variation, the settle-in ease and the Sleep wind-down, ported from <code>breathsim/patterns.py</code>,
      <code>naturalness.py</code>, <code>controller.py</code> and <code>session.py</code>.</li>
    <li><b>A breathing orb and a night sky</b>: canvas scenes drawn after the desktop app's Orb and Night scenes and its
      phase colours.</li>
    <li><b>Procedural sound</b>: ${info.web_breath_voices} breath voices and ${info.web_ambiences} ambience beds synthesised in an
      AudioWorklet from the same filtered-noise and struck-resonator recipes as <code>breathsim/tracks.py</code> and
      <code>textures.py</code>. No samples.</li>
    <li><b>A sleep timer</b> that fades the sound over ${sleep.fade_seconds} seconds and pauses (<code>vesper/sleeptimer.py</code>), and the
      ${info.programs} <b>guided programs</b> with their stages and on-screen instructions.</li>
  </ul>
  <h2>Only in the desktop app</h2>
  <p>The 3D talking head and the cartoon cast, the ${info.lectures} narrated sleep-lectures across ${info.branches} branches,
  neural narration (Kokoro, optional XTTS) and macOS speech, the ${info.phrases} sung chants, the book reader, the
  vocal-tract voices, the pitch trainer, stats and the optional AI assistant. Of the app's ${info.voices} voices, the
  browser plays the filtered-noise and texture ones. Nothing here calls an AI service or needs an API key.</p>
  <h2>Run the desktop app</h2>
<pre>pip install -r requirements.txt
python run.py          # launch the app
python selftest.py     # headless checks</pre>
  <h2>Run the web app</h2>
<pre>pip install -r requirements-web.txt
python run_web.py      # http://127.0.0.1:8216
python scripts/build_static.py   # the static site in site/</pre>
  <h2>Credits</h2>
  <p>Vesper by George Dickinson (<a href="https://github.com/gddickinson/Vesper">gddickinson/Vesper</a>, see LICENSE).
  The desktop avatar is rendered from the <a href="https://github.com/ICT-VGL/ICT-FaceKit">ICT-FaceKit</a>.
  Optional XTTS-v2 voices are under the non-commercial Coqui Public Model License and are never bundled.</p>`;
});
