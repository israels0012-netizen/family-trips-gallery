import { chromium } from 'playwright';
import { serve } from './server.mjs';

/**
 * End-to-end checks against a real (software-rendered) WebGL context.
 * The point is not pixel beauty — it is that the picture lands the right way
 * up, the right way round, and in the right eye. Those are the mistakes that
 * make a VR player unwatchable and that nothing else catches.
 */

const PORT = 8477;
const server = await serve(PORT);

let failed = 0;
const check = (name, ok, detail = '') => {
  if (!ok) failed++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? `  → ${detail}` : ''}`);
};

const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
         '--autoplay-policy=no-user-gesture-required'],
});
const page = await browser.newPage({ viewport: { width: 900, height: 600 } });
const consoleErrors = [];
page.on('console', (m) => m.type() === 'error' && consoleErrors.push(m.text()));
page.on('pageerror', (e) => consoleErrors.push('pageerror: ' + e.message));

await page.goto(`http://127.0.0.1:${PORT}/index.html`);
await page.waitForFunction(() => !!window.vrplayer, null, { timeout: 20000 });
check('app boots (modules, three.js, first render)', true);

await page.addScriptTag({ content: `
/** Record a clip whose four quadrants are individually identifiable. */
window.makeQuadClip = async function (w, h) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const ctx = c.getContext('2d');
  const paint = () => {
    ctx.fillStyle = '#ff0000'; ctx.fillRect(0, 0, w / 2, h / 2);       // top-left     red
    ctx.fillStyle = '#00ff00'; ctx.fillRect(w / 2, 0, w / 2, h / 2);   // top-right    green
    ctx.fillStyle = '#0000ff'; ctx.fillRect(0, h / 2, w / 2, h / 2);   // bottom-left  blue
    ctx.fillStyle = '#ffff00'; ctx.fillRect(w / 2, h / 2, w / 2, h / 2); // bottom-right yellow
  };
  const rec = new MediaRecorder(c.captureStream(20), { mimeType: 'video/webm;codecs=vp8' });
  const chunks = []; rec.ondataavailable = (e) => chunks.push(e.data);
  rec.start();
  for (let i = 0; i < 30; i++) { paint(); await new Promise((r) => setTimeout(r, 25)); }
  await new Promise((r) => { rec.onstop = r; rec.stop(); });
  return URL.createObjectURL(new Blob(chunks, { type: 'video/webm' }));
};

/** Colour rendered at a screen position, optionally restricted to one eye's layer. */
window.probe = (fromLeft, fromTop, eyeLayer) => new Promise((resolve) => {
  const viewer = window.vrplayer.viewer, camera = viewer.camera;
  const savedMask = camera.layers.mask;
  if (eyeLayer) { camera.layers.disableAll(); camera.layers.enable(eyeLayer); }
  requestAnimationFrame(() => {
    const gl = viewer.renderer.getContext();
    const w = gl.drawingBufferWidth, h = gl.drawingBufferHeight;
    const px = new Uint8Array(4);
    gl.readPixels(Math.round(fromLeft * w), Math.round((1 - fromTop) * h), 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
    camera.layers.mask = savedMask;
    const [r, g, b] = px;
    resolve(r > 150 && g > 150 ? 'yellow' : r > 150 ? 'red' : g > 150 ? 'green' : b > 150 ? 'blue' : 'dark');
  });
});
` });

const probe = (x, y, eye) => page.evaluate(([x, y, e]) => window.probe(x, y, e), [x, y, eye]);
const settings = () => page.evaluate(() => ({ ...window.vrplayer.viewer.settings }));

async function loadClip(name, w, h) {
  const url = await page.evaluate(([w, h]) => window.makeQuadClip(w, h), [w, h]);
  await page.evaluate(([url, name]) => window.vrplayer.load({ type: 'file', url, name }), [url, name]);
  await page.waitForFunction(() => !document.getElementById('ui').hidden, null, { timeout: 15000 });
  await page.waitForTimeout(400);
}
const apply = async (partial) => {
  await page.evaluate((p) => window.vrplayer.viewer.set(p), partial);
  await page.waitForTimeout(250);
};

// --- detection drives the scene -------------------------------------------
await loadClip('family_trip_paris.webm', 640, 360);
let s = await settings();
check('an ordinary clip opens as a flat 2D screen', s.projection === 'flat' && s.layout === 'mono', `${s.projection}/${s.layout}`);
const playback = await page.evaluate(() => {
  const v = window.vrplayer.video;
  return { paused: v.paused, ended: v.ended, at: +v.currentTime.toFixed(2) };
});
// Short test clips can already have run to the end by the time we look.
check('playback starts by itself', !playback.paused || playback.ended || playback.at > 0, JSON.stringify(playback));

let wiring = await page.evaluate(() => ({
  count: window.vrplayer.viewer.meshes.length,
  layers: window.vrplayer.viewer.meshes.map((m) => m.layers.mask),
}));
check('2D video draws once, for both eyes', wiring.count === 1 && wiring.layers[0] === 1, `layers=${wiring.layers}`);

// --- orientation: up is up, left is left ----------------------------------
await apply({ curve: 0, size: 1.6, distance: 3 });
check('top-left of the frame shows top-left', await probe(0.35, 0.28) === 'red');
check('top-right shows top-right (image is not mirrored)', await probe(0.65, 0.28) === 'green');
check('bottom-left shows bottom-left (image is not upside down)', await probe(0.35, 0.72) === 'blue');
check('bottom-right shows bottom-right', await probe(0.65, 0.72) === 'yellow');
check('the room backdrop never covers the picture', await probe(0.5, 0.82) !== 'dark', await probe(0.5, 0.82));

// --- side-by-side goes to the right eyes ----------------------------------
await loadClip('beach_VR180_SBS.webm', 1024, 512);
s = await settings();
check('"VR180 SBS" in the name opens as a 180° stereo sphere', s.projection === '180' && s.layout === 'sbs', `${s.projection}/${s.layout}`);
wiring = await page.evaluate(() => window.vrplayer.viewer.meshes.map((m) => m.layers.mask));
check('stereo draws one mesh per eye layer', wiring.length === 2 && wiring[0] === 2 && wiring[1] === 4, `layers=${wiring}`);

await apply({ projection: 'flat', layout: 'sbs', swapEyes: false, curve: 0, size: 1.6, distance: 3 });
check('side-by-side: left eye gets the left half', await probe(0.35, 0.28, 1) === 'red');
check('side-by-side: right eye gets the right half', await probe(0.35, 0.28, 2) === 'green');
await apply({ swapEyes: true });
check('swapping eyes really swaps them', await probe(0.35, 0.28, 1) === 'green');

// --- top-and-bottom --------------------------------------------------------
await loadClip('canyon_tb.webm', 512, 1024);
await apply({ projection: 'flat', layout: 'tb', swapEyes: false, curve: 0, size: 1.6, distance: 3 });
check('over-under: left eye gets the top half', await probe(0.35, 0.28, 1) === 'red');
check('over-under: right eye gets the bottom half', await probe(0.35, 0.28, 2) === 'blue');

// --- spheres ---------------------------------------------------------------
await loadClip('canyon_360.webm', 1024, 512);
await apply({ projection: '360', layout: 'mono' });
await page.evaluate(() => window.vrplayer.viewer.recenter());
await page.waitForTimeout(250);
const up = await probe(0.5, 0.28), down = await probe(0.5, 0.72);
check('360°: sky above, ground below', (up === 'red' || up === 'green') && (down === 'blue' || down === 'yellow'), `${up}/${down}`);

await apply({ projection: '180' });
await page.evaluate(() => {
  window.vrplayer.viewer.recenter();
  window.vrplayer.viewer.camera.rotation.set(0, Math.PI, 0, 'YXZ');
});
await page.waitForTimeout(250);
check('180°: nothing is smeared behind you', await probe(0.5, 0.5) === 'dark');
await page.evaluate(() => window.vrplayer.viewer.camera.rotation.set(0, 0, 0, 'YXZ'));

// --- choices are remembered per clip ---------------------------------------
const stored = await page.evaluate(() => JSON.parse(localStorage.getItem('vrplayer.prefs'))['canyon_360.webm']);
check('per-clip settings are saved', stored && stored.projection === '180', JSON.stringify(stored && stored.projection));

// --- links we cannot play are explained, not swallowed ---------------------
await page.click('#btnBack');
await page.fill('#urlInput', 'https://www.youtube.com/watch?v=abc123');
await page.click('#urlForm button[type=submit]');
await page.waitForTimeout(400);
const msg = await page.textContent('#loadMsg');
check('a YouTube link gets a real explanation', /YouTube/.test(msg) && !/undefined/.test(msg));

// --- the in-headset panel ---------------------------------------------------
const hud = await page.evaluate(() => {
  const h = window.vrplayer.viewer.hud;
  h.update({ playing: true, duration: 100, currentTime: 10, projectionLabel: 'a', layoutLabel: 'b' });
  h.render();
  const at = (x, y) => (h.pick({ x: x / 1024, y: 1 - y / 560 }) || {}).id;
  return {
    play: at(500, 140), swap: at(150, 250), recenter: at(150, 330),
    seek: h.pick({ x: 0.5, y: 1 - 394 / 560 }),
    outside: at(6, 546),
  };
});
check('every panel button is reachable by a controller ray',
  hud.play === 'play' && hud.swap === 'swap' && hud.recenter === 'recenter' && !hud.outside, JSON.stringify(hud));
check('the panel seek bar maps to a position in the video',
  hud.seek && hud.seek.id === 'seek' && Math.abs(hud.seek.fraction - 0.5) < 0.06, JSON.stringify(hud.seek));

check('no console errors along the way', consoleErrors.length === 0, consoleErrors.slice(0, 3).join(' | '));

await browser.close();
server.close();
console.log(failed ? `\n${failed} check(s) failed` : '\nall browser checks passed');
process.exit(failed ? 1 : 0);
