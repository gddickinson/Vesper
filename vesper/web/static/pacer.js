// The browser's BreathController + SessionDirector: one clock with pause/resume that drives the scene and
// the sound, plus the optional settle-in ease, Sleep wind-down, guided program and sleep timer.
// No DOM; the Breathe page owns one Pacer and calls frame() every animation frame.
import { controllerState, cycleOf, Naturalness, pattern } from './breath_engine.js';
import { fadeGain, remainingSeconds, windDown, settleStart, settleAt, stageIndex, stageStart, programSeconds } from './session_engine.js';

export const fromApi = p => pattern(p.name, p.inhale, p.hold_full, p.exhale, p.hold_empty, p.description);

export class Pacer {
  constructor(p) {
    this.pattern = p; this.base = p; this.running = false; this.accum = 0; this.t0 = 0; this.patternT0 = 0;
    this.nat = new Naturalness({ amount: 0 });
    this.settle = null; this.wind = null; this.program = null; this.timer = null; this.volume = 0.7;
    this.onStage = null; this.onDone = null;
  }
  now() { return performance.now() / 1000; }
  elapsed() { return this.accum + (this.running ? this.now() - this.t0 : 0); }
  start() { if (!this.running) { this.t0 = this.now(); this.running = true; } }
  pause() { if (this.running) { this.accum += this.now() - this.t0; this.running = false; } }
  toggle() { this.running ? this.pause() : this.start(); }
  reset() { this.running = false; this.accum = 0; this.patternT0 = 0; this.stopExtras(); this.pattern = this.base; }
  stopExtras() { this.settle = null; this.wind = null; this.program = null; this.timer = this.timer && { ...this.timer, t0: 0 }; }
  // change_pattern: switch and restart the breath at the inhale.
  change(p) { this.pattern = p; this.base = p; this.patternT0 = this.elapsed(); }
  choose(p, { settle = false } = {}) {
    this.program = null; this.wind = null; this.change(p);
    this.settle = settle ? { start: settleStart(p), target: p, t0: this.elapsed(), duration: 150 } : null;
    if (this.settle) this.pattern = this.settle.start;
  }
  startWind(a, b, seconds) { this.program = null; this.settle = null; this.change(a); this.wind = { a, b, seconds, t0: this.elapsed() }; }
  startProgram(prog) {
    this.settle = null; this.wind = null;
    this.program = { prog, t0: this.elapsed(), stage: -1, total: programSeconds(prog.stages) };
  }
  armTimer(minutes) { this.timer = minutes > 0 ? { minutes, t0: this.elapsed() } : null; }

  // One frame: advance the extras, return { state, master, info } for the scene and the sound.
  frame() {
    const t = this.elapsed();
    let master = this.volume;
    const info = { bpm: 60 / cycleOf(this.pattern) };
    if (this.program) {
      const P = this.program, local = t - P.t0, i = stageIndex(P.prog.stages, local);
      if (i !== P.stage) {
        P.stage = i;
        const st = P.prog.stages[i];
        if (st.durations) { this.pattern = pattern(st.pattern || 'Stage', ...st.durations); this.patternT0 = t; }
        this.onStage?.(st, i);
      }
      const st = P.prog.stages[i], end = stageStart(P.prog.stages, i) + st.minutes * 60;
      Object.assign(info, { stage: st.title, stageNo: i + 1, stages: P.prog.stages.length,
        stageLeft: Math.max(0, end - local), totalLeft: Math.max(0, P.total - local), prog: Math.min(1, local / P.total) });
    } else if (this.wind) {
      const W = this.wind, r = windDown(W.a, W.b, W.seconds, t - W.t0, this.volume);
      this.pattern = r.pattern; master = r.volume;
      Object.assign(info, { wind: r.frac, prog: r.frac });
    } else if (this.settle) {
      const S = this.settle, r = settleAt(S.start, S.target, S.duration, t - S.t0);
      this.pattern = r.pattern; info.settle = r.frac;
      if (r.done) this.settle = null;
    }
    if (this.timer) {
      const el = t - this.timer.t0, [g, done] = fadeGain(this.timer.minutes, el);
      master *= g; info.timerLeft = remainingSeconds(this.timer.minutes, el); info.fading = g < 1;
      if (done && this.running) { this.pause(); this.timer = null; this.onDone?.(); }
    }
    info.bpm = 60 / cycleOf(this.pattern);
    const state = controllerState(this.pattern, this.nat, t, this.patternT0);
    return { state, master: this.running ? master : 0, info, t };
  }
}
