// Main-thread side of the procedural sound: starts an AudioContext + the vesper-sound worklet, picks the
// breath voice and the ambience bed, and posts the live breath levels every animation frame.
import { voiceLevel } from './breath_engine.js';

export class Soundscape {
  constructor() { this.ctx = null; this.node = null; this.cfg = {}; this.error = null; }
  get ok() { return !!this.node; }
  async start() {
    if (this.node) { await this.ctx.resume(); return true; }
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC || !(AC.prototype && 'audioWorklet' in AC.prototype)) throw new Error('Web Audio worklets are not supported in this browser');
      this.ctx = new AC();
      await this.ctx.audioWorklet.addModule('static/sound_worklet.js');
      this.node = new AudioWorkletNode(this.ctx, 'vesper-sound', { numberOfInputs: 0, outputChannelCount: [2] });
      this.node.connect(this.ctx.destination);
      for (const [slot, cfg] of Object.entries(this.cfg)) this.post(slot, cfg);
      return true;
    } catch (e) { this.error = e.message; console.warn('sound off:', e); return false; }
  }
  post(slot, cfg) { this.node?.port.postMessage({ type: 'voice', slot, cfg, seed: slot === 'ambience' ? 11 : 1 }); }
  // slot: 'breath' | 'ambience'; cfg: a voice config from /api/voices (or null to silence it).
  setVoice(slot, cfg) { this.cfg[slot] = cfg; this.post(slot, cfg); }
  update(state, master) {
    if (!this.node) return;
    const levels = {};
    for (const [slot, cfg] of Object.entries(this.cfg)) if (cfg) levels[slot] = cfg.kind === 'texture' ? 1 : voiceLevel(cfg, state);
    this.node.port.postMessage({ type: 'state', levels, phase: state.phase, tone: state.tone_mod ?? 1, master });
  }
  async suspend() { if (this.ctx && this.ctx.state === 'running') await this.ctx.suspend(); }
  close() { if (this.ctx) { this.node.port.postMessage({ type: 'state', levels: {}, phase: 'inhale', master: 0 }); this.ctx.close(); } this.ctx = this.node = null; }
}
