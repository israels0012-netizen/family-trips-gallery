import * as THREE from 'three';
import { VRHud } from './hud.js';
import { PROJECTIONS, LAYOUTS, PROJECTION_LABEL, LAYOUT_LABEL } from './detect.js';

const DEG = Math.PI / 180;
const SPHERE_RADIUS = 500;

/** Rewrite a geometry's UVs so it samples only part of a packed stereo frame. */
function remapUV(geometry, offsetX, offsetY, scaleX, scaleY) {
  const uv = geometry.attributes.uv;
  for (let i = 0; i < uv.count; i++) {
    uv.setXY(i, uv.getX(i) * scaleX + offsetX, uv.getY(i) * scaleY + offsetY);
  }
  uv.needsUpdate = true;
  return geometry;
}

export class Viewer {
  constructor(canvas, video) {
    this.video = video;
    this.settings = {
      projection: 'flat',
      layout: 'mono',
      swapEyes: false,
      size: 1.3,          // screen height multiplier
      distance: 4.5,      // metres
      curve: 45,          // degrees of arc, 0 = perfectly flat
      yaw: 0,             // user rotation offset, degrees
    };
    this.baseYaw = 0;

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.setSize(innerWidth, innerHeight, false);
    this.renderer.xr.enabled = true;
    this.renderer.xr.setReferenceSpaceType('local-floor');

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x05070c);

    this.camera = new THREE.PerspectiveCamera(72, innerWidth / innerHeight, 0.1, 2000);
    this.camera.position.set(0, 1.6, 0);
    this.camera.layers.enable(1);  // desktop preview shows the left eye

    this.stage = new THREE.Group();
    this.stage.position.set(0, 1.6, 0);
    this.scene.add(this.stage);

    this.texture = new THREE.VideoTexture(video);
    this.texture.colorSpace = THREE.SRGBColorSpace;
    this.texture.minFilter = THREE.LinearFilter;
    this.texture.generateMipmaps = false;

    this.room = this._buildRoom();
    this.scene.add(this.room);

    this.meshes = [];
    this.hud = new VRHud();
    this.scene.add(this.hud.mesh);

    this.stereoCamera = new THREE.StereoCamera();
    this.stereoCamera.aspect = 0.5;
    this.cardboard = false;
    this._orientation = null;

    this.onAction = () => {};
    this.onChange = () => {};

    this._raycaster = new THREE.Raycaster();
    this._raycaster.layers.enableAll();
    this._tmpMatrix = new THREE.Matrix4();
    this._clock = new THREE.Clock();

    this._setupControllers();
    this._setupDesktopLook(canvas);

    addEventListener('resize', () => this.resize());
    this.renderer.xr.addEventListener('sessionstart', () => {
      this.room.visible = this.settings.projection === 'flat';
      setTimeout(() => this.recenter(), 120);
    });
    this.renderer.xr.addEventListener('sessionend', () => this.hud.hide());

    this.rebuild();
    this.renderer.setAnimationLoop(() => this._tick());
  }

  /* ------------------------------------------------------------------ scene */

  _buildRoom() {
    const room = new THREE.Group();
    const grid = new THREE.GridHelper(40, 40, 0x2a3550, 0x141a28);
    grid.position.y = -0.01;
    room.add(grid);
    const floor = new THREE.Mesh(
      new THREE.CircleGeometry(22, 48).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({ color: 0x080b12 })
    );
    floor.position.y = -0.02;
    room.add(floor);

    // The room is pure backdrop. Painting it first and never letting it touch
    // the depth buffer means it can never clip a corner off the picture —
    // the screen's bottom edge sits right at floor level, so it otherwise does.
    for (const object of room.children) {
      object.renderOrder = -10;
      object.material.depthTest = false;
      object.material.depthWrite = false;
    }
    return room;
  }

  /** A gently curved cinema screen, centred on the local origin facing -Z. */
  _screenGeometry() {
    const aspect = this._contentAspect();
    const height = 2.0 * this.settings.size;
    const width = height * aspect;
    const distance = this.settings.distance;
    const arc = this.settings.curve * DEG;

    if (arc < 0.02) {
      return new THREE.PlaneGeometry(width, height, 1, 1).translate(0, 0, -distance);
    }
    const radius = width / arc;
    const geometry = new THREE.CylinderGeometry(
      radius, radius, height, 96, 1, true,
      Math.PI - arc / 2, arc
    );
    geometry.scale(-1, 1, 1);              // flip to face inward
    geometry.translate(0, 0, radius - distance);
    return geometry;
  }

  /**
   * Shape of the cinema screen. Flat 3D ships in two flavours: "full" packing
   * where each eye keeps its own shape, and "half" packing where the frame
   * keeps the display shape and each eye is squeezed. Pick whichever reading
   * lands closer to a normal screen instead of stretching faces sideways.
   */
  _contentAspect() {
    const w = this.video.videoWidth || 16;
    const h = this.video.videoHeight || 9;
    const full = w / h;
    const { layout } = this.settings;
    if (layout === 'mono') return full;
    const eye = layout === 'sbs' ? full / 2 : full * 2;
    const off = (ar) => Math.abs(Math.log(ar / 1.78));
    return off(eye) <= off(full) ? eye : full;
  }

  _baseGeometry() {
    const { projection } = this.settings;
    if (projection === '360') {
      return new THREE.SphereGeometry(SPHERE_RADIUS, 72, 48).scale(-1, 1, 1);
    }
    if (projection === '180') {
      return new THREE.SphereGeometry(SPHERE_RADIUS, 72, 48, -Math.PI / 2, Math.PI).scale(-1, 1, 1);
    }
    return this._screenGeometry();
  }

  /** Rebuild the projection meshes. Cheap enough to call on any setting change. */
  rebuild() {
    for (const mesh of this.meshes) {
      this.stage.remove(mesh);
      mesh.geometry.dispose();
      mesh.material.dispose();
    }
    this.meshes = [];

    const { layout, swapEyes } = this.settings;
    const base = this._baseGeometry();
    const material = () => new THREE.MeshBasicMaterial({ map: this.texture, toneMapped: false });

    if (layout === 'mono') {
      const mesh = new THREE.Mesh(base, material());
      mesh.layers.set(0);                       // both eyes see the same thing
      this.meshes.push(mesh);
    } else {
      const first = base;
      const second = base.clone();
      if (layout === 'sbs') {
        remapUV(first, 0, 0, 0.5, 1);
        remapUV(second, 0.5, 0, 0.5, 1);
      } else {
        remapUV(first, 0, 0.5, 1, 0.5);         // top half
        remapUV(second, 0, 0, 1, 0.5);          // bottom half
      }
      const left = new THREE.Mesh(swapEyes ? second : first, material());
      const right = new THREE.Mesh(swapEyes ? first : second, material());
      left.layers.set(1);
      right.layers.set(2);
      this.meshes.push(left, right);
    }

    for (const mesh of this.meshes) this.stage.add(mesh);
    this.room.visible = this.settings.projection === 'flat';
    this._applyTransform();
  }

  _applyTransform() {
    this.stage.rotation.y = this.baseYaw + this.settings.yaw * DEG;
  }

  set(partial, { rebuild = true } = {}) {
    const before = JSON.stringify(this.settings);
    Object.assign(this.settings, partial);
    if (JSON.stringify(this.settings) === before) return;
    if (rebuild) this.rebuild(); else this._applyTransform();
    this.onChange(this.settings);
  }

  cycle(key) {
    const list = key === 'projection' ? PROJECTIONS : LAYOUTS;
    const next = list[(list.indexOf(this.settings[key]) + 1) % list.length];
    this.set({ [key]: next });
  }

  recenter() {
    const cam = this.renderer.xr.isPresenting ? this.renderer.xr.getCamera() : this.camera;
    const position = new THREE.Vector3();
    const direction = new THREE.Vector3();
    cam.getWorldPosition(position);
    cam.getWorldDirection(direction);
    this.stage.position.copy(position);
    this.baseYaw = Math.atan2(-direction.x, -direction.z);
    this.set({ yaw: 0 }, { rebuild: false });
    this._applyTransform();
  }

  resize() {
    this.camera.aspect = innerWidth / innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(innerWidth, innerHeight, false);
  }

  /* ------------------------------------------------------------ XR plumbing */

  static async isVRSupported() {
    try {
      return !!navigator.xr && await navigator.xr.isSessionSupported('immersive-vr');
    } catch { return false; }
  }

  async enterVR() {
    const session = await navigator.xr.requestSession('immersive-vr', {
      optionalFeatures: ['local-floor', 'bounded-floor', 'hand-tracking', 'layers'],
    });
    await this.renderer.xr.setSession(session);
    return session;
  }

  _setupControllers() {
    this.controllers = [];
    const rayGeometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, -1),
    ]);

    for (let i = 0; i < 2; i++) {
      const controller = this.renderer.xr.getController(i);
      const ray = new THREE.Line(rayGeometry, new THREE.LineBasicMaterial({ color: 0x5b8cff, transparent: true, opacity: 0.75 }));
      ray.scale.z = 3;
      ray.visible = false;
      controller.add(ray);
      controller.userData.ray = ray;
      controller.addEventListener('selectstart', () => this._onSelect(controller));
      this.scene.add(controller);
      this.controllers.push(controller);
    }
  }

  _hudHit(controller) {
    if (!this.hud.visible) return null;
    this._tmpMatrix.identity().extractRotation(controller.matrixWorld);
    this._raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    this._raycaster.ray.direction.set(0, 0, -1).applyMatrix4(this._tmpMatrix);
    const hit = this._raycaster.intersectObject(this.hud.mesh, false)[0];
    return hit ? { distance: hit.distance, pick: this.hud.pick(hit.uv) } : null;
  }

  _onSelect(controller) {
    if (!this.hud.visible) {
      this.hud.show(this.renderer.xr.getCamera());
      return;
    }
    const hit = this._hudHit(controller);
    if (hit && hit.pick) this.onAction(hit.pick);
  }

  _pollGamepads(dt) {
    const session = this.renderer.xr.getSession();
    if (!session) return;
    for (const source of session.inputSources) {
      const pad = source.gamepad;
      if (!pad) continue;
      const id = source.handedness || 'x';

      // A/X/B/Y or grip opens and closes the panel.
      const menuPressed = [1, 4, 5].some((i) => pad.buttons[i] && pad.buttons[i].pressed);
      this._menuWas = this._menuWas || {};
      if (menuPressed && !this._menuWas[id]) this.hud.toggle(this.renderer.xr.getCamera());
      this._menuWas[id] = menuPressed;

      const x = pad.axes[2] ?? pad.axes[0] ?? 0;
      const y = pad.axes[3] ?? pad.axes[1] ?? 0;
      if (Math.abs(x) > 0.6 && this.video.duration) {
        this.video.currentTime = Math.min(
          this.video.duration,
          Math.max(0, this.video.currentTime + Math.sign(x) * 25 * dt)
        );
      }
      if (Math.abs(y) > 0.6 && this.settings.projection === 'flat') {
        const distance = Math.min(12, Math.max(1.5, this.settings.distance + Math.sign(y) * 2.2 * dt));
        this.set({ distance });
      }
    }
  }

  /* --------------------------------------------------- desktop & cardboard */

  _setupDesktopLook(canvas) {
    let dragging = false;
    let lastX = 0, lastY = 0;
    let yaw = 0, pitch = 0;

    const down = (e) => {
      if (this.renderer.xr.isPresenting) return;
      dragging = true;
      lastX = e.clientX; lastY = e.clientY;
      canvas.setPointerCapture?.(e.pointerId);
    };
    const move = (e) => {
      if (!dragging) return;
      yaw -= (e.clientX - lastX) * 0.0045;
      pitch -= (e.clientY - lastY) * 0.0045;
      pitch = Math.max(-1.4, Math.min(1.4, pitch));
      lastX = e.clientX; lastY = e.clientY;
      this.camera.rotation.set(pitch, yaw, 0, 'YXZ');
    };
    const up = () => { dragging = false; };

    canvas.addEventListener('pointerdown', down);
    canvas.addEventListener('pointermove', move);
    canvas.addEventListener('pointerup', up);
    canvas.addEventListener('pointercancel', up);
    this._resetLook = () => { yaw = 0; pitch = 0; this.camera.rotation.set(0, 0, 0, 'YXZ'); };
  }

  async setCardboard(on) {
    if (on && !this._orientation) {
      this._orientation = await createOrientationTracker();
      if (!this._orientation) return false;
    }
    this.cardboard = on;
    if (!on) this._resetLook();
    return true;
  }

  /* ------------------------------------------------------------------ frame */

  _tick() {
    const dt = Math.min(0.1, this._clock.getDelta());

    if (this.renderer.xr.isPresenting) {
      this._pollGamepads(dt);
      const xrCamera = this.renderer.xr.getCamera();
      let nearest = null;
      for (const controller of this.controllers) {
        const hit = this._hudHit(controller);
        controller.userData.ray.visible = this.hud.visible;
        if (this.hud.visible) controller.userData.ray.scale.z = hit ? hit.distance : 3;
        if (hit && hit.pick && (!nearest || hit.distance < nearest.distance)) nearest = hit;
      }
      this.hud.setHot(nearest && nearest.pick ? nearest.pick.id : null);
      this.hud.update({
        playing: !this.video.paused,
        muted: this.video.muted,
        currentTime: Math.round(this.video.currentTime),
        duration: Math.round(this.video.duration || 0),
        projectionLabel: PROJECTION_LABEL[this.settings.projection],
        layoutLabel: LAYOUT_LABEL[this.settings.layout],
        swapEyes: this.settings.swapEyes,
      });
      this.hud.render();
      this.renderer.render(this.scene, xrCamera);
      return;
    }

    if (this.cardboard && this._orientation) {
      this._orientation.apply(this.camera);
      this._renderCardboard();
      return;
    }

    this.renderer.render(this.scene, this.camera);
  }

  _renderCardboard() {
    const size = this.renderer.getSize(new THREE.Vector2());
    const half = size.width / 2;
    this.camera.updateWorldMatrix(true, false);
    this.stereoCamera.update(this.camera);

    this.renderer.setScissorTest(true);
    this.renderer.setScissor(0, 0, half, size.height);
    this.renderer.setViewport(0, 0, half, size.height);
    this.renderer.render(this.scene, this.stereoCamera.cameraL);
    this.renderer.setScissor(half, 0, half, size.height);
    this.renderer.setViewport(half, 0, half, size.height);
    this.renderer.render(this.scene, this.stereoCamera.cameraR);
    this.renderer.setScissorTest(false);
    this.renderer.setViewport(0, 0, size.width, size.height);
  }
}

/* ------------------------------------------------------ device orientation */

async function createOrientationTracker() {
  const Ctor = window.DeviceOrientationEvent;
  if (!Ctor) return null;
  if (typeof Ctor.requestPermission === 'function') {
    try {
      if (await Ctor.requestPermission() !== 'granted') return null;
    } catch { return null; }
  }

  const state = { alpha: 0, beta: 0, gamma: 0, screen: 0 };
  addEventListener('deviceorientation', (e) => {
    state.alpha = (e.alpha || 0) * DEG;
    state.beta = (e.beta || 0) * DEG;
    state.gamma = (e.gamma || 0) * DEG;
    state.screen = (screen.orientation?.angle || window.orientation || 0) * DEG;
  });

  const zee = new THREE.Vector3(0, 0, 1);
  const euler = new THREE.Euler();
  const q0 = new THREE.Quaternion();
  const q1 = new THREE.Quaternion(-Math.sqrt(0.5), 0, 0, Math.sqrt(0.5)); // -90° about X

  return {
    apply(camera) {
      euler.set(state.beta, state.alpha, -state.gamma, 'YXZ');
      camera.quaternion.setFromEuler(euler);
      camera.quaternion.multiply(q1);
      camera.quaternion.multiply(q0.setFromAxisAngle(zee, -state.screen));
    },
  };
}
