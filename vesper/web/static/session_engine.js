// Session timing ported from the Python app: the sleep timer (vesper/sleeptimer.py), the Sleep wind-down
// and the settle-in ease (breathsim/session.py SessionDirector) and guided-program stepping.
// Pure functions; checked against Python by session_engine.test.mjs.
import { pattern, durations } from './breath_engine.js';

export const FADE_SECONDS = 30;

// sleeptimer.fade_gain -> [gain, done]
export function fadeGain(armedMinutes, elapsed, fadeSeconds = FADE_SECONDS) {
  if (armedMinutes <= 0) return [1, false];
  const mark = armedMinutes * 60, fade = Math.max(1, fadeSeconds);
  if (elapsed < mark) return [1, false];
  if (elapsed >= mark + fade) return [0, true];
  return [Math.max(0, 1 - (elapsed - mark) / fade), false];
}

export const remainingSeconds = (armedMinutes, elapsed) =>
  armedMinutes <= 0 ? null : Math.max(0, armedMinutes * 60 - elapsed);

const lerpPattern = (name, a, b, s) => {
  const A = durations(a), B = durations(b);
  const d = A.map((x, i) => x + (B[i] - x) * s);
  return pattern(name, d[0], d[1], d[2], d[3]);
};

// SessionDirector._update_sleep: breath slows linearly a -> b over the duration; the volume eases out
// over the last 30%.
export function windDown(a, b, duration, t, userVolume) {
  const d = Math.max(60, duration);
  const frac = d > 0 ? Math.min(1, t / d) : 1;
  let vol = userVolume;
  if (frac > 0.7) vol *= Math.max(0, 1 - (frac - 0.7) / 0.3);
  return { pattern: lerpPattern('Sleep wind-down', a, b, frac), volume: vol, frac };
}

// SessionDirector.start_settle / _update_settle: begin ~1.6x faster and ease to the target pace.
export function settleStart(target, ratio = 0.62) {
  const r = Math.max(0.4, Math.min(0.95, ratio));
  return pattern('Settling in', target.inhale * r, target.hold_full * r, target.exhale * r, target.hold_empty * r);
}
export function settleAt(start, target, duration, t) {
  const d = Math.max(20, duration);
  const frac = d <= 0 ? 1 : Math.min(1, Math.max(0, t / d));
  if (frac >= 1) return { pattern: target, frac, done: true };
  return { pattern: lerpPattern('Settling in', start, target, 0.5 - 0.5 * Math.cos(Math.PI * frac)), frac, done: false };
}

// SessionDirector._update_program: the stage whose start time has passed (stages from /api/programs).
export function stageIndex(stages, local) {
  let acc = 0, idx = 0;
  stages.forEach((s, i) => { if (local >= acc) idx = i; acc += s.minutes * 60; });
  return idx;
}
export const stageStart = (stages, idx) => stages.slice(0, idx).reduce((a, s) => a + s.minutes * 60, 0);
export const programSeconds = stages => stages.reduce((a, s) => a + s.minutes * 60, 0);
