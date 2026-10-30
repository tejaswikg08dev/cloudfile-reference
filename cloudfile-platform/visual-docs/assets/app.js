/* ==========================================================================
   CloudFile Visual Docs — shared animation helpers (vanilla JS, no deps)
   ========================================================================== */

/**
 * StepPlayer drives a sequence of steps over an SVG diagram.
 *
 * Each step: { caption, nodes:[ids], edges:[ids], token:{path:id} }
 *  - nodes: element ids to add `.active` to
 *  - edges: element ids to add `.active` to (animated dashes)
 *  - token: optional { path: "<svg path id>" } to animate the file token along
 */
class StepPlayer {
  constructor(opts) {
    this.svg = document.getElementById(opts.svg);
    this.steps = opts.steps;
    this.captionEl = document.getElementById(opts.caption);
    this.barEl = opts.bar ? document.getElementById(opts.bar) : null;
    this.tokenEl = opts.token ? document.getElementById(opts.token) : null;
    this.i = -1;
    this.playing = false;
    this.timer = null;
  }

  _clear() {
    this.svg.querySelectorAll('.node.active').forEach(n => n.classList.remove('active'));
    this.svg.querySelectorAll('.edge.active').forEach(e => e.classList.remove('active'));
    if (this.tokenEl) this.tokenEl.classList.remove('show');
  }

  _render(step) {
    this._clear();
    (step.nodes || []).forEach(id => {
      const el = this.svg.getElementById ? this.svg.getElementById(id) : document.getElementById(id);
      if (el) el.classList.add('active');
    });
    (step.edges || []).forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.add('active');
    });
    if (step.token && this.tokenEl) {
      this._moveToken(step.token);
    }
    if (this.captionEl) {
      this.captionEl.innerHTML =
        `<span class="step-no">${this.i + 1}/${this.steps.length}</span>${step.caption}`;
    }
    if (this.barEl) {
      this.barEl.style.width = `${((this.i + 1) / this.steps.length) * 100}%`;
    }
  }

  _moveToken(token) {
    const target = document.getElementById(token.at);
    if (!target || !this.tokenEl) return;
    // Move the token group to the center of the target node via transform.
    const tx = target.getAttribute('data-cx');
    const ty = target.getAttribute('data-cy');
    if (tx && ty) {
      this.tokenEl.classList.add('show');
      this.tokenEl.setAttribute('transform', `translate(${tx}, ${ty})`);
    }
  }

  step() {
    this.i = (this.i + 1) % this.steps.length;
    this._render(this.steps[this.i]);
  }

  reset() {
    this.pause();
    this.i = -1;
    this._clear();
    if (this.captionEl) this.captionEl.innerHTML =
      '<span class="step-no">Ready</span>Press <b>Play</b> or <b>Step</b> to begin.';
    if (this.barEl) this.barEl.style.width = '0%';
  }

  play() {
    if (this.playing) return;
    this.playing = true;
    const tick = () => {
      if (!this.playing) return;
      this.step();
      if (this.i === this.steps.length - 1) { this.playing = false; return; }
      this.timer = setTimeout(tick, 1900);
    };
    tick();
  }

  pause() {
    this.playing = false;
    if (this.timer) clearTimeout(this.timer);
  }
}

/** Count-up animation for stat values. */
function countUp() {
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseInt(el.getAttribute('data-count'), 10);
    const suffix = el.getAttribute('data-suffix') || '';
    let cur = 0;
    const step = Math.max(1, Math.floor(target / 40));
    const t = setInterval(() => {
      cur += step;
      if (cur >= target) { cur = target; clearInterval(t); }
      el.textContent = cur + suffix;
    }, 25);
  });
}

/** Wire standard Play/Step/Reset buttons to a player instance. */
function wirePlayer(player, ids) {
  const play = document.getElementById(ids.play);
  const step = document.getElementById(ids.step);
  const reset = document.getElementById(ids.reset);
  if (play) play.onclick = () => player.play();
  if (step) step.onclick = () => { player.pause(); player.step(); };
  if (reset) reset.onclick = () => player.reset();
  player.reset();
}

document.addEventListener('DOMContentLoaded', countUp);
