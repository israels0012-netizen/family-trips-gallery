import * as THREE from 'three';

/**
 * The control panel you see *inside* the headset: a canvas texture on a quad,
 * driven by controller ray-casts. Without it there is no way to pause, seek or
 * fix a wrongly detected projection once the goggles are on.
 */

const W = 1024;
const H = 560;
const PANEL_W = 1.15;           // metres
const PANEL_H = PANEL_W * H / W;

const COL = {
  bg: 'rgba(12,16,26,0.93)',
  line: '#2a3550',
  text: '#e8ecf6',
  muted: '#93a0bd',
  fill: '#1b2336',
  on: '#5b8cff',
  onText: '#07101f',
  track: '#2c3652',
};

function rounded(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

export function formatTime(t) {
  if (!isFinite(t) || t < 0) t = 0;
  const s = Math.floor(t % 60);
  const m = Math.floor(t / 60) % 60;
  const h = Math.floor(t / 3600);
  const mm = h ? String(m).padStart(2, '0') : String(m);
  return (h ? h + ':' : '') + mm + ':' + String(s).padStart(2, '0');
}

export class VRHud {
  constructor() {
    this.canvas = document.createElement('canvas');
    this.canvas.width = W;
    this.canvas.height = H;
    this.ctx = this.canvas.getContext('2d');

    this.texture = new THREE.CanvasTexture(this.canvas);
    this.texture.colorSpace = THREE.SRGBColorSpace;
    this.texture.anisotropy = 4;

    const material = new THREE.MeshBasicMaterial({ map: this.texture, transparent: true, depthTest: false });
    this.mesh = new THREE.Mesh(new THREE.PlaneGeometry(PANEL_W, PANEL_H), material);
    this.mesh.renderOrder = 999;
    this.mesh.visible = false;

    this.state = {};
    this.hot = null;        // id of the control the ray currently points at
    this.seekBar = { x: 48, y: 384, w: W - 96, h: 20 };
    this.buttons = [];
    this._dirty = true;
  }

  get visible() { return this.mesh.visible; }

  show(camera) {
    // Park the panel a comfortable arm's length in front of wherever you look.
    const dir = new THREE.Vector3();
    camera.getWorldDirection(dir);
    const pos = new THREE.Vector3();
    camera.getWorldPosition(pos);
    dir.y = 0;
    if (dir.lengthSq() < 1e-6) dir.set(0, 0, -1);
    dir.normalize();

    this.mesh.position.copy(pos).addScaledVector(dir, 1.25).add(new THREE.Vector3(0, -0.22, 0));
    this.mesh.quaternion.setFromRotationMatrix(
      new THREE.Matrix4().lookAt(this.mesh.position, pos, new THREE.Vector3(0, 1, 0))
    );
    this.mesh.visible = true;
    this._dirty = true;
  }

  hide() { this.mesh.visible = false; }
  toggle(camera) { this.mesh.visible ? this.hide() : this.show(camera); }

  update(state) {
    const changed = Object.keys(state).some((k) => this.state[k] !== state[k]);
    Object.assign(this.state, state);
    if (changed) this._dirty = true;
  }

  setHot(id) {
    if (this.hot !== id) { this.hot = id; this._dirty = true; }
  }

  /** Convert a UV hit on the quad into a control id (or a seek request). */
  pick(uv) {
    const x = uv.x * W;
    const y = (1 - uv.y) * H;

    const bar = this.seekBar;
    const pad = 26;
    if (x >= bar.x - pad && x <= bar.x + bar.w + pad && y >= bar.y - pad && y <= bar.y + bar.h + pad) {
      return { id: 'seek', fraction: Math.min(1, Math.max(0, (x - bar.x) / bar.w)) };
    }
    for (const b of this.buttons) {
      if (x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h) return { id: b.id };
    }
    return null;
  }

  render() {
    if (!this._dirty) return;
    this._dirty = false;

    const ctx = this.ctx;
    const s = this.state;
    ctx.clearRect(0, 0, W, H);

    rounded(ctx, 2, 2, W - 4, H - 4, 30);
    ctx.fillStyle = COL.bg;
    ctx.fill();
    ctx.strokeStyle = COL.line;
    ctx.lineWidth = 3;
    ctx.stroke();

    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    this.buttons = [];

    const drawButton = (id, x, y, w, h, label, opts = {}) => {
      const active = !!opts.active;
      const hot = this.hot === id;
      rounded(ctx, x, y, w, h, 14);
      ctx.fillStyle = active ? COL.on : hot ? '#27324c' : COL.fill;
      ctx.fill();
      ctx.strokeStyle = hot ? COL.on : COL.line;
      ctx.lineWidth = hot ? 4 : 2;
      ctx.stroke();
      ctx.fillStyle = active ? COL.onText : COL.text;
      ctx.font = `${opts.big ? 600 : 500} ${opts.size || 27}px system-ui, "Segoe UI", sans-serif`;
      ctx.fillText(label, x + w / 2, y + h / 2 + 1);
      this.buttons.push({ id, x, y, w, h });
    };

    // --- title -------------------------------------------------------------
    ctx.fillStyle = COL.muted;
    ctx.font = '24px system-ui, "Segoe UI", sans-serif';
    ctx.fillText(s.title || '', W / 2, 44, W - 120);

    // --- transport row -----------------------------------------------------
    const rowY = 96;
    drawButton('back10', 232, rowY, 140, 86, '10 ⏪');
    drawButton('play', 402, rowY, 220, 86, s.playing ? '⏸  השהה' : '▶  נגן', { big: true, size: 31 });
    drawButton('fwd10', 652, rowY, 140, 86, '⏩ 10');
    drawButton('mute', 48, rowY, 150, 86, s.muted ? '🔇 מושתק' : '🔊 קול', { size: 24, active: s.muted });
    drawButton('close', 822, rowY, 154, 86, '✕ סגור', { size: 24 });

    // Hebrew rows are laid out right to left; the transport row above keeps a
    // left-to-right order because rewind/forward follow the timeline, not the text.
    const rtlRow = (y, height, items, opts) => {
      let x = W - 48;
      for (const [id, width, label, extra] of items) {
        x -= width;
        drawButton(id, x, y, width, height, label, { ...opts, ...extra });
        x -= 14;
      }
    };

    // --- projection / layout row ------------------------------------------
    rtlRow(214, 80, [
      ['projection', 300, `הקרנה: ${s.projectionLabel || ''}`],
      ['layout', 300, `תלת־ממד: ${s.layoutLabel || ''}`],
      ['swap', 300, 'החלפת עיניים', { active: s.swapEyes }],
    ], { size: 25 });

    // --- size / recenter row ----------------------------------------------
    rtlRow(306, 64, [
      ['smaller', 140, '➖ קטן'],
      ['bigger', 140, '➕ גדול'],
      ['closer', 160, 'קרוב יותר'],
      ['farther', 160, 'רחוק יותר'],
      ['recenter', 272, '⌖ מרכוז מחדש'],
    ], { size: 23 });

    // --- seek bar ----------------------------------------------------------
    const bar = this.seekBar;
    const p = s.duration ? Math.min(1, (s.currentTime || 0) / s.duration) : 0;
    rounded(ctx, bar.x, bar.y, bar.w, bar.h, bar.h / 2);
    ctx.fillStyle = COL.track;
    ctx.fill();
    if (p > 0) {
      rounded(ctx, bar.x, bar.y, Math.max(bar.h, bar.w * p), bar.h, bar.h / 2);
      ctx.fillStyle = COL.on;
      ctx.fill();
    }
    ctx.beginPath();
    ctx.arc(bar.x + bar.w * p, bar.y + bar.h / 2, 18, 0, Math.PI * 2);
    ctx.fillStyle = '#dce6ff';
    ctx.fill();

    ctx.fillStyle = COL.muted;
    ctx.font = '25px system-ui, "Segoe UI", sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(formatTime(s.currentTime), bar.x, bar.y + 62);
    ctx.textAlign = 'right';
    ctx.fillText(formatTime(s.duration), bar.x + bar.w, bar.y + 62);

    // --- footer hint -------------------------------------------------------
    ctx.textAlign = 'center';
    ctx.fillStyle = '#6c7796';
    ctx.font = '21px system-ui, "Segoe UI", sans-serif';
    ctx.fillText('הדק = בחירה · ג׳ויסטיק ימינה/שמאלה = הרצה · כפתור עליון = פתיחה וסגירה של הלוח', W / 2, H - 34);

    this.texture.needsUpdate = true;
  }

  dispose() {
    this.mesh.geometry.dispose();
    this.mesh.material.dispose();
    this.texture.dispose();
  }
}
