// node vesper/web/static/engines.test.mjs: the JS port against tests/fixtures/vesper_reference.json (Python).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { runChecks } from './verify_checks.js';
import { stageIndex } from './session_engine.js';
import { Noise } from './dsp_core.js';

const here = dirname(fileURLToPath(import.meta.url));
const F = JSON.parse(readFileSync(join(here, '../../../tests/fixtures/vesper_reference.json'), 'utf8'));
let bad = 0;
for (const a of runChecks(F)) {
  console.log(`${a.failures.length ? 'FAIL' : 'ok  '} ${a.name}: ${a.checks} checks, worst rel. diff ${a.worst.toExponential(2)}`);
  a.failures.slice(0, 5).forEach(f => console.log('     ' + f));
  bad += a.failures.length;
}
const stages = [{ minutes: 1 }, { minutes: 3 }, { minutes: 2.5 }];
for (const [t, i] of [[0, 0], [59.9, 0], [60, 1], [239.9, 1], [240, 2], [9999, 2]]) if (stageIndex(stages, t) !== i) { bad++; console.log(`FAIL stage@${t}`); }
for (const kind of ['white', 'pink', 'brown']) {          // coloured noise ~unit RMS after dsp._SCALE
  const buf = new Noise(kind, 7).generate(200000), rms = Math.sqrt(buf.reduce((s, v) => s + v * v, 0) / buf.length);
  if (!(rms > 0.4 && rms < 2.5)) { bad++; console.log(`FAIL ${kind} rms ${rms}`); }
}
if (bad) { console.log(`${bad} failures`); process.exit(1); }
