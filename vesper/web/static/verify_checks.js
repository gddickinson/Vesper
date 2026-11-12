// Every comparison of the JavaScript port against the Python reference (/api/reference, the same data as
// tests/fixtures/vesper_reference.json). Used by the Verify page and by engines.test.mjs (node).
import { pattern, stateAt, patternForBpm, Naturalness, controllerState, envelope, durations } from './breath_engine.js';
import { fadeGain, remainingSeconds, windDown, settleStart, settleAt, FADE_SECONDS } from './session_engine.js';
import { designers, IIR, OnePoleLP, PINK_A, PINK_B, BROWN_A, BROWN_B, SCALE, Struck,
  BOWL_PARTIALS, CHIME_PARTIALS, CHIME_NOTES, CHIME_BASE } from './dsp_core.js';

const KEYS = ['phase', 'progress', 'remaining', 'volume', 'airflow', 'cycle_index', 'cycle_frac', 'pitch_mod', 'tone_mod'];

class Area {
  constructor(name, source) { Object.assign(this, { name, source, checks: 0, worst: 0, failures: [] }); }
  eq(a, b, what, tol = 1e-9) {
    this.checks++;
    if (typeof b !== 'number') { if (a !== b) this.failures.push(`${what}: ${a} vs ${b}`); return; }
    const d = Math.abs(a - b) / Math.max(1, Math.abs(b));
    this.worst = Math.max(this.worst, d);
    if (!(d <= tol)) this.failures.push(`${what}: ${a} vs ${b}`);
  }
  all(a, b, what, tol) { if (a.length !== b.length) this.failures.push(`${what}: length`); else b.forEach((v, i) => this.eq(a[i], v, `${what}[${i}]`, tol)); }
  state(js, py, what) { KEYS.forEach(k => this.eq(js[k], py[k], `${what}.${k}`)); }
}

export function runChecks(F) {
  const A = [];
  const pat = new Area('Breath clock: state_at for every pattern', 'breathsim/patterns.py'); A.push(pat);
  for (const row of F.patterns) { const p = pattern(row.name, ...row.pattern); for (const [t, st] of row.states) pat.state(stateAt(p, t), st, `${row.name}@${t}`); }
  for (const [bpm, le, d] of F.bpm) pat.all(durations(patternForBpm(bpm, le)), d, `bpm ${bpm}`);

  const nat = new Area('Naturalness hash + jittered controller states', 'naturalness.py, controller.py'); A.push(nat);
  for (const n of F.naturalness) {
    const N = new Naturalness({ amount: n.amount, seed: n.seed });
    for (const [k, pf, df, pm, tm] of n.k) { nat.all(N.phaseFactors(k), pf, `pf ${k}`); nat.eq(N.depthFactor(k), df, 'depth'); nat.eq(N.pitchMod(k), pm, 'pitch'); nat.eq(N.toneMod(k), tm, 'tone'); }
  }
  for (const run of F.nat_states) {
    const row = F.patterns.find(r => r.name === run.pattern), [timing, depth, pitch, tone] = run.flags;
    const N = new Naturalness({ amount: run.amount, seed: run.seed, timing, depth, pitch, tone });
    for (const [t, st] of run.states) nat.state(controllerState(pattern(run.pattern, ...row.pattern), N, t), st, `nat@${t}`);
  }

  const env = new Area('Breath envelopes (all modes and attacks)', 'envelopes.py'); A.push(env);
  const box = pattern('Box', 4, 4, 4, 4);
  for (const row of F.envelopes) {
    const s = stateAt(box, row.t);
    for (const e of ['airflow', 'volume', 'exhale', 'inhale', 'breath_both'])
      for (const atk of ['smooth', 'explosive', 'swell']) env.eq(envelope(e, s, { attack: atk }), row[`${e}/${atk}`], `${e}/${atk}@${row.t}`);
    env.eq(envelope('breath', s, { attack: 'explosive', attackIn: 'swell', inhaleLevel: 0.6, exhaleLevel: 0.9 }), row.breath, `breath@${row.t}`);
  }

  const dsp = new Area('Filters: RBJ biquads, one-pole, pink + brown', 'dsp.py'); A.push(dsp);
  const D = F.dsp, x = Float64Array.from(D.x);
  for (const [kind, fc, q, b, a] of D.coeffs) { const [jb, ja] = designers[kind](D.sr, fc, q); dsp.all(jb, b, `${kind} b`); dsp.all(ja, a, `${kind} a`); }
  const [lb, la] = designers.lowpass(D.sr, 1400, 0.7), bq = new IIR(lb, la);
  dsp.all([...bq.process(x.slice(0, 150)), ...bq.process(x.slice(150))], D.biquad, 'biquad', 1e-8);
  const lp = new OnePoleLP();
  dsp.all([...lp.process(x.slice(0, 200), 900, D.sr), ...lp.process(x.slice(200), 2500, D.sr)], D.onepole, 'onepole', 1e-8);
  dsp.all([...new IIR(PINK_B, PINK_A).process(x)], D.pink, 'pink', 1e-8);
  dsp.all([...new IIR(BROWN_B, BROWN_A).process(x)], D.brown, 'brown', 1e-8);
  for (const k of ['white', 'pink', 'brown']) dsp.eq(SCALE[k], D.scale[k], `scale ${k}`);

  const tex = new Area('Singing bowl / wind chime partials and strikes', 'textures.py'); A.push(tex);
  const T = F.textures;
  T.bowl_partials.forEach((p, i) => tex.all(BOWL_PARTIALS[i], p, 'bowl'));
  T.chime_partials.forEach((p, i) => tex.all(CHIME_PARTIALS[i], p, 'chime'));
  tex.all(CHIME_NOTES, T.chime_notes, 'notes'); tex.eq(CHIME_BASE, T.chime_base, 'base');
  const s = T.struck, hit = new Struck(s.f0, BOWL_PARTIALS, s.t0, s.amp, s.pan);
  s.t.forEach((t, i) => { const v = hit.value(t); tex.eq(v * hit.gl, s.left[i], `L@${t}`, 1e-8); tex.eq(v * hit.gr, s.right[i], `R@${t}`, 1e-8); });
  [30, 38.4, 38.6].forEach((t, i) => tex.eq(hit.dead(t), s.dead[i], `dead@${t}`));

  const ses = new Area('Sleep timer, wind-down and settle-in', 'sleeptimer.py, session.py'); A.push(ses);
  const S = F.session;
  ses.eq(FADE_SECONDS, S.fade_seconds, 'FADE_SECONDS');
  for (const [m, e, g, d, r] of S.fade) { const [jg, jd] = fadeGain(m, e); ses.eq(jg, g, `gain ${m}/${e}`); ses.eq(jd, d, 'done'); ses.eq(remainingSeconds(m, e), r, 'remaining'); }
  const W = S.wind, a = pattern('a', ...W.a), b = pattern('b', ...W.b);
  for (const [t, p, vol] of W.rows) { const w = windDown(a, b, W.duration, t, W.user_volume); ses.all(durations(w.pattern), p, `wind@${t}`); ses.eq(w.volume, vol, `vol@${t}`); }
  const Tt = S.settle, target = pattern('t', ...Tt.target), start = settleStart(target, Tt.ratio);
  ses.all(durations(start), Tt.rows[0][1], 'settle start');
  for (const [t, p] of Tt.rows.slice(1)) ses.all(durations(settleAt(start, target, Tt.duration, t).pattern), p, `settle@${t}`);
  return A;
}
