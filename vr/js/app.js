import { Viewer } from './viewer.js';
import { detect, describe } from './detect.js';
import { attach, classify, unsupportedReason } from './media.js';
import { formatTime } from './hud.js';

const $ = (id) => document.getElementById(id);

const video = $('video');
const viewer = new Viewer($('stage'), video);

const dom = {
  dropzone: $('dropzone'), ui: $('ui'), loadMsg: $('loadMsg'),
  filePicker: $('filePicker'), urlForm: $('urlForm'), urlInput: $('urlInput'),
  recents: $('recents'), recentsList: $('recentsList'),
  mediaTitle: $('mediaTitle'), autoBadge: $('autoBadge'),
  btnBack: $('btnBack'), btnSettings: $('btnSettings'), settings: $('settings'),
  btnCloseSettings: $('btnCloseSettings'), detected: $('detected'),
  segProjection: $('segProjection'), segLayout: $('segLayout'), chkSwap: $('chkSwap'),
  flatOnly: $('flatOnly'),
  rngSize: $('rngSize'), rngDist: $('rngDist'), rngCurve: $('rngCurve'), rngYaw: $('rngYaw'),
  valSize: $('valSize'), valDist: $('valDist'), valCurve: $('valCurve'), valYaw: $('valYaw'),
  btnReset: $('btnReset'),
  seek: $('seek'), tCur: $('tCur'), tDur: $('tDur'),
  btnPlay: $('btnPlay'), btnBack10: $('btnBack10'), btnFwd10: $('btnFwd10'),
  btnMute: $('btnMute'), volume: $('volume'),
  btnRecenter: $('btnRecenter'), btnCardboard: $('btnCardboard'), btnVR: $('btnVR'),
};

let current = null;      // { name, key, source }
let autoSettings = null; // what detection proposed, for the reset button
let wakeLock = null;

/* --------------------------------------------------------------- storage */

const store = {
  read(key, fallback) {
    try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
  },
  write(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* private mode */ }
  },
};

const PREFS_KEY = 'vrplayer.prefs';
const RECENTS_KEY = 'vrplayer.recents';

const savedFor = (key) => store.read(PREFS_KEY, {})[key] || null;

function savePrefs(key, settings) {
  const all = store.read(PREFS_KEY, {});
  all[key] = settings;
  store.write(PREFS_KEY, all);
}

function rememberRecent(entry) {
  const list = store.read(RECENTS_KEY, []).filter((r) => r.url !== entry.url);
  list.unshift(entry);
  store.write(RECENTS_KEY, list.slice(0, 8));
  renderRecents();
}

function renderRecents() {
  const list = store.read(RECENTS_KEY, []);
  dom.recents.hidden = list.length === 0;
  dom.recentsList.textContent = '';
  for (const item of list) {
    const button = document.createElement('button');
    button.className = 'recent';
    button.type = 'button';
    button.innerHTML = `<span class="rname"></span><span class="rtag"></span>`;
    button.querySelector('.rname').textContent = item.name;
    button.querySelector('.rtag').textContent = item.tag || '';
    button.addEventListener('click', () => load({ type: 'url', url: item.url, name: item.name }));
    dom.recentsList.appendChild(button);
  }
}

/* ------------------------------------------------------------ load a source */

function message(html, kind = 'info') {
  dom.loadMsg.hidden = false;
  dom.loadMsg.className = `loadmsg ${kind}`;
  dom.loadMsg.innerHTML = html;
}

function clearMessage() { dom.loadMsg.hidden = true; }

async function load(source) {
  clearMessage();

  if (source.type === 'url') {
    const { kind, host } = classify(source.url);
    const problem = unsupportedReason(kind, host);
    if (problem) return message(`<b>${problem.title}</b>${problem.body}`, 'err');
  }

  message('טוען…');
  try {
    await attach(video, source);
  } catch (err) {
    if (err.tainted) {
      return message(
        '<b>השרת חוסם שימוש בסרטון מאתר אחר</b>' +
        'הקובץ קיים, אבל השרת לא שולח כותרת CORS ולכן הדפדפן לא מרשה להקרין אותו בתלת־ממד. ' +
        'הורידו את הקובץ למכשיר וגררו אותו לכאן.', 'err');
    }
    return message(`<b>לא הצלחנו לטעון</b>${err.message}`, 'err');
  }

  clearMessage();
  current = { name: source.name, key: source.type === 'url' ? source.url : source.name, source };

  const auto = detect(source.name, video.videoWidth, video.videoHeight);
  autoSettings = { projection: auto.projection, layout: auto.layout, swapEyes: false };

  const saved = savedFor(current.key);
  viewer.set({ ...autoSettings, size: 1.3, distance: 4.5, curve: 45, yaw: 0, ...(saved || {}) });
  viewer.recenter();

  dom.mediaTitle.textContent = source.name;
  dom.autoBadge.textContent = saved ? `לפי ההעדפות שלכם · ${describe(viewer.settings)}` : `זוהה: ${describe(auto)}`;
  renderDetected(auto, !!saved);
  syncSettingsUI();

  if (source.type === 'url') {
    rememberRecent({ url: source.url, name: source.name, tag: describe(viewer.settings) });
  }

  dom.dropzone.hidden = true;
  dom.ui.hidden = false;
  try { await video.play(); } catch { /* needs another tap */ }
  requestWakeLock();
  scheduleChromeHide();
}

function renderDetected(auto, usedSaved) {
  const parts = [
    `<b>${usedSaved ? 'נטען לפי ההעדפות ששמרתם' : 'זיהוי אוטומטי'}:</b> ${describe(auto)}`,
    `<div>${auto.reason}</div>`,
  ];
  dom.detected.innerHTML = parts.join('');

  if (auto.alternatives.length) {
    const wrap = document.createElement('div');
    wrap.className = 'alt';
    wrap.append('לא נראה נכון? ');
    for (const alt of auto.alternatives) {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = describe(alt);
      button.addEventListener('click', () => {
        viewer.set({ projection: alt.projection, layout: alt.layout });
        syncSettingsUI();
      });
      wrap.appendChild(button);
      wrap.append(' ');
    }
    dom.detected.appendChild(wrap);
  }
}

/* -------------------------------------------------------------- settings UI */

function syncSettingsUI() {
  const s = viewer.settings;
  for (const [group, key] of [[dom.segProjection, 'projection'], [dom.segLayout, 'layout']]) {
    for (const button of group.children) button.classList.toggle('on', button.dataset.v === s[key]);
  }
  dom.chkSwap.checked = s.swapEyes;
  dom.chkSwap.closest('.checkrow').style.opacity = s.layout === 'mono' ? 0.45 : 1;
  dom.flatOnly.hidden = s.projection !== 'flat';

  dom.rngSize.value = Math.round(s.size * 100);
  dom.rngDist.value = Math.round(s.distance * 10);
  dom.rngCurve.value = Math.round(s.curve);
  dom.rngYaw.value = Math.round(s.yaw);
  dom.valSize.textContent = `${Math.round(s.size * 100)}%`;
  dom.valDist.textContent = `${s.distance.toFixed(1)} מ׳`;
  dom.valCurve.textContent = `${Math.round(s.curve)}°`;
  dom.valYaw.textContent = `${Math.round(s.yaw)}°`;

  dom.autoBadge.textContent = describe(s);
}

for (const [group, key] of [[dom.segProjection, 'projection'], [dom.segLayout, 'layout']]) {
  group.addEventListener('click', (e) => {
    const button = e.target.closest('button[data-v]');
    if (!button) return;
    viewer.set({ [key]: button.dataset.v });
    syncSettingsUI();
  });
}

dom.chkSwap.addEventListener('change', () => { viewer.set({ swapEyes: dom.chkSwap.checked }); syncSettingsUI(); });
dom.rngSize.addEventListener('input', () => { viewer.set({ size: +dom.rngSize.value / 100 }); syncSettingsUI(); });
dom.rngDist.addEventListener('input', () => { viewer.set({ distance: +dom.rngDist.value / 10 }); syncSettingsUI(); });
dom.rngCurve.addEventListener('input', () => { viewer.set({ curve: +dom.rngCurve.value }); syncSettingsUI(); });
dom.rngYaw.addEventListener('input', () => { viewer.set({ yaw: +dom.rngYaw.value }, { rebuild: false }); syncSettingsUI(); });
dom.btnReset.addEventListener('click', () => {
  viewer.set({ ...autoSettings, size: 1.3, distance: 4.5, curve: 45, yaw: 0 });
  syncSettingsUI();
});

dom.btnSettings.addEventListener('click', () => { dom.settings.hidden = !dom.settings.hidden; });
dom.btnCloseSettings.addEventListener('click', () => { dom.settings.hidden = true; });

// Every tweak is remembered per video, so the same clip opens correctly next time.
viewer.onChange = (settings) => { if (current) savePrefs(current.key, { ...settings }); };

/* ---------------------------------------------------------- transport / UI */

const togglePlay = () => (video.paused ? video.play().catch(() => {}) : video.pause());
const skip = (seconds) => {
  if (!isFinite(video.duration)) return;
  video.currentTime = Math.min(video.duration, Math.max(0, video.currentTime + seconds));
};

dom.btnPlay.addEventListener('click', togglePlay);
dom.btnBack10.addEventListener('click', () => skip(-10));
dom.btnFwd10.addEventListener('click', () => skip(10));
dom.btnMute.addEventListener('click', () => { video.muted = !video.muted; });
dom.volume.addEventListener('input', () => { video.volume = +dom.volume.value / 100; video.muted = false; });
dom.btnRecenter.addEventListener('click', () => { viewer.recenter(); syncSettingsUI(); });
dom.seek.addEventListener('input', () => {
  if (isFinite(video.duration)) video.currentTime = (+dom.seek.value / 1000) * video.duration;
});

dom.btnBack.addEventListener('click', () => {
  video.pause();
  dom.ui.hidden = true;
  dom.settings.hidden = true;
  dom.dropzone.hidden = false;
  clearMessage();
  renderRecents();
});

video.addEventListener('play', () => { dom.btnPlay.textContent = '⏸'; requestWakeLock(); });
video.addEventListener('pause', () => { dom.btnPlay.textContent = '▶'; });
video.addEventListener('volumechange', () => { dom.btnMute.textContent = video.muted || !video.volume ? '🔇' : '🔊'; });
video.addEventListener('timeupdate', () => {
  dom.tCur.textContent = formatTime(video.currentTime);
  dom.tDur.textContent = formatTime(video.duration);
  if (isFinite(video.duration) && document.activeElement !== dom.seek) {
    dom.seek.value = Math.round((video.currentTime / video.duration) * 1000);
  }
});

/* --------------------------------------------------------------- VR buttons */

Viewer.isVRSupported().then((supported) => {
  dom.btnVR.disabled = !supported;
  dom.btnVR.title = supported ? 'צפייה במשקפיים' : 'הדפדפן הזה לא תומך ב‑WebXR — פתחו את הדף בדפדפן של המשקפיים';
  if (!supported) dom.btnVR.textContent = 'VR לא זמין כאן';
});

dom.btnVR.addEventListener('click', async () => {
  try {
    if (video.paused) await video.play().catch(() => {});
    await viewer.enterVR();
  } catch (err) {
    message(`<b>לא הצלחנו להיכנס ל‑VR</b>${err.message}`, 'err');
    dom.dropzone.hidden = false;
  }
});

dom.btnCardboard.addEventListener('click', async () => {
  const turnOn = !viewer.cardboard;
  const ok = await viewer.setCardboard(turnOn);
  if (!ok) return alert('המכשיר לא נתן גישה לחיישני התנועה, ולכן אי אפשר להפעיל מצב קרדבורד.');
  dom.btnCardboard.classList.toggle('on', viewer.cardboard);
  if (viewer.cardboard) {
    document.documentElement.requestFullscreen?.().catch(() => {});
    screen.orientation?.lock?.('landscape').catch(() => {});
    viewer.recenter();
  } else if (document.fullscreenElement) {
    document.exitFullscreen().catch(() => {});
  }
});

/* ------------------------------------------------------- in-headset actions */

viewer.onAction = ({ id, fraction }) => {
  switch (id) {
    case 'play': togglePlay(); break;
    case 'back10': skip(-10); break;
    case 'fwd10': skip(10); break;
    case 'mute': video.muted = !video.muted; break;
    case 'close': viewer.hud.hide(); break;
    case 'projection': viewer.cycle('projection'); break;
    case 'layout': viewer.cycle('layout'); break;
    case 'swap': viewer.set({ swapEyes: !viewer.settings.swapEyes }); break;
    case 'smaller': viewer.set({ size: Math.max(0.5, viewer.settings.size - 0.15) }); break;
    case 'bigger': viewer.set({ size: Math.min(4, viewer.settings.size + 0.15) }); break;
    case 'closer': viewer.set({ distance: Math.max(1.5, viewer.settings.distance - 0.5) }); break;
    case 'farther': viewer.set({ distance: Math.min(12, viewer.settings.distance + 0.5) }); break;
    case 'recenter': viewer.recenter(); break;
    case 'seek':
      if (isFinite(video.duration)) video.currentTime = fraction * video.duration;
      break;
  }
  syncSettingsUI();
};

/* ------------------------------------------------------------ input sources */

dom.filePicker.addEventListener('change', () => {
  const file = dom.filePicker.files[0];
  if (file) load({ type: 'file', url: URL.createObjectURL(file), name: file.name });
});

dom.urlForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const url = dom.urlInput.value.trim();
  if (!url) return;
  load({ type: 'url', url, name: decodeURIComponent(url.split('/').pop().split('?')[0]) || url });
});

for (const type of ['dragenter', 'dragover']) {
  document.addEventListener(type, (e) => { e.preventDefault(); dom.dropzone.classList.add('dragging'); });
}
for (const type of ['dragleave', 'drop']) {
  document.addEventListener(type, (e) => { e.preventDefault(); dom.dropzone.classList.remove('dragging'); });
}
document.addEventListener('drop', (e) => {
  const file = [...(e.dataTransfer?.files || [])].find((f) => f.type.startsWith('video/') || /\.(mp4|m4v|webm|mov|ogv|mkv)$/i.test(f.name));
  if (file) {
    dom.dropzone.hidden = false;
    return load({ type: 'file', url: URL.createObjectURL(file), name: file.name });
  }
  const text = e.dataTransfer?.getData('text/uri-list') || e.dataTransfer?.getData('text/plain');
  if (text) { dom.dropzone.hidden = false; dom.urlInput.value = text.trim(); dom.urlForm.requestSubmit(); }
});

// "Just paste a link anywhere" — the fastest path there is.
document.addEventListener('paste', (e) => {
  if (e.target.tagName === 'INPUT') return;
  const text = e.clipboardData?.getData('text')?.trim();
  if (!text || !/^https?:\/\//i.test(text)) return;
  dom.dropzone.hidden = false;
  dom.urlInput.value = text;
  dom.urlForm.requestSubmit();
});

/* --------------------------------------------------------------- keyboard */

addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT' || dom.ui.hidden) return;
  const actions = {
    ' ': togglePlay,
    ArrowRight: () => skip(-5),   // RTL layout: right arrow rewinds
    ArrowLeft: () => skip(5),
    j: () => skip(-10), l: () => skip(10), k: togglePlay,
    m: () => { video.muted = !video.muted; },
    r: () => { viewer.recenter(); syncSettingsUI(); },
    f: () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen()),
    s: () => { dom.settings.hidden = !dom.settings.hidden; },
  };
  const action = actions[e.key];
  if (action) { e.preventDefault(); action(); }
});

/* ------------------------------------------------------- chrome auto-hiding */

let hideTimer = null;
function scheduleChromeHide() {
  clearTimeout(hideTimer);
  dom.ui.classList.remove('hide-chrome');
  hideTimer = setTimeout(() => {
    if (dom.settings.hidden && !video.paused) dom.ui.classList.add('hide-chrome');
  }, 3200);
}
for (const type of ['pointermove', 'pointerdown', 'keydown']) {
  addEventListener(type, scheduleChromeHide, { passive: true });
}

/* --------------------------------------------------------------- wake lock */

async function requestWakeLock() {
  try {
    if (!wakeLock && navigator.wakeLock) {
      wakeLock = await navigator.wakeLock.request('screen');
      wakeLock.addEventListener('release', () => { wakeLock = null; });
    }
  } catch { /* not critical */ }
}
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && !video.paused) requestWakeLock();
});

/* ------------------------------------------------------------------ startup */

renderRecents();

// Allow deep links such as  index.html#https://example.com/clip_180_sbs.mp4
const deepLink = decodeURIComponent(location.hash.slice(1));
if (/^https?:\/\//i.test(deepLink)) {
  dom.urlInput.value = deepLink;
  load({ type: 'url', url: deepLink, name: deepLink.split('/').pop().split('?')[0] });
}

// Handy when debugging from the headset's remote console.
window.vrplayer = { viewer, video, load, detect };
