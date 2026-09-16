/**
 * Turning "whatever the user gave us" into a playing <video> element.
 * Handles local files, direct video URLs, HLS playlists, and explains
 * clearly when a link (YouTube and friends) simply cannot be streamed.
 */

const HLS_LIB = new URL('../vendor/hls.min.js', import.meta.url).href;

const DIRECT_EXT = /\.(mp4|m4v|webm|ogv|ogg|mov|mkv|avi)(\?|#|$)/i;

export function classify(url) {
  let u;
  try { u = new URL(url, location.href); } catch { return { kind: 'invalid' }; }
  const host = u.hostname.replace(/^www\./, '');
  const path = u.pathname;

  if (/(^|\.)(youtube\.com|youtu\.be|youtube-nocookie\.com)$/i.test(host)) return { kind: 'youtube', host };
  if (/(^|\.)vimeo\.com$/i.test(host)) return { kind: 'vimeo', host };
  if (/(^|\.)(facebook\.com|instagram\.com|tiktok\.com|drive\.google\.com)$/i.test(host)) return { kind: 'walled', host };
  if (/\.m3u8(\?|#|$)/i.test(path + u.search)) return { kind: 'hls', host };
  if (/\.mpd(\?|#|$)/i.test(path + u.search)) return { kind: 'dash', host };
  if (DIRECT_EXT.test(path)) return { kind: 'direct', host };
  return { kind: 'unknown', host };
}

/** Human explanation for links we knowingly cannot play. */
export function unsupportedReason(kind, host) {
  switch (kind) {
    case 'invalid':
      return { title: 'הקישור לא תקין', body: 'בדקו שהדבקתם כתובת מלאה שמתחילה ב‑https://' };
    case 'youtube':
      return {
        title: 'קישורי YouTube לא ניתנים לניגון ישיר',
        body: 'YouTube לא מאפשר לאתרים חיצוניים לגשת לקובץ הווידאו עצמו. הורידו את הסרטון למכשיר וגררו אותו לכאן — אז הוא יותאם למשקפיים בדיוק כמו כל סרטון אחר.',
      };
    case 'vimeo':
      return {
        title: 'קישורי Vimeo לא ניתנים לניגון ישיר',
        body: 'צריך קישור לקובץ הווידאו עצמו. אם יש לכם הרשאת הורדה — הורידו את הקובץ וגררו אותו לכאן.',
      };
    case 'walled':
      return {
        title: `אי אפשר לנגן קישורים מ‑${host}`,
        body: 'האתר הזה לא חושף את קובץ הווידאו לאתרים אחרים. הורידו את הקובץ וגררו אותו לכאן.',
      };
    case 'dash':
      return {
        title: 'קישורי DASH (‎.mpd) אינם נתמכים',
        body: 'נתמכים קבצי וידאו ישירים (‎.mp4 / ‎.webm / ‎.mov) וגם שידורי HLS (‎.m3u8).',
      };
    default:
      return null;
  }
}

/**
 * Shown after a link that looked plausible turned out not to be a video.
 * Nearly always this is a page address rather than the file itself, so say
 * that in words instead of leaving "unsupported format" hanging.
 */
export function pageNotFileReason(url) {
  const looksLikeFile = DIRECT_EXT.test(new URL(url, location.href).pathname);
  return looksLikeFile
    ? {
        title: 'הקובץ קיים, אבל השרת לא מרשה להשתמש בו כאן',
        body: 'כדי להציג סרטון בתלת־ממד הדפדפן דורש אישור מפורש מהשרת שמאחסן אותו, ' +
              'ורוב השרתים לא נותנים אותו. הורידו את הסרטון למכשיר וגררו אותו לכאן — ככה זה תמיד יעבוד.',
      }
    : {
        title: 'הקישור הזה מוביל לעמוד אינטרנט, לא לקובץ וידאו',
        body: 'צריך קישור לקובץ עצמו — כזה שנגמר ב‑.mp4 או ב‑.webm. כתובת של עמוד ' +
              '(יוטיוב, פייסבוק, אתר חדשות, כל אתר) לא מכילה את הסרטון, אלא רק נגן שמוגן ' +
              'מפני אתרים אחרים. הדרך שתמיד עובדת: מורידים את הסרטון למכשיר וגוררים אותו לכאן.',
      };
}

let hlsPromise = null;
function loadHlsLibrary() {
  if (hlsPromise) return hlsPromise;
  hlsPromise = new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = HLS_LIB;
    s.onload = () => resolve(window.Hls);
    s.onerror = () => reject(new Error('לא הצלחנו לטעון את רכיב ה‑HLS'));
    document.head.appendChild(s);
  });
  return hlsPromise;
}

let activeHls = null;

function detachActive(video) {
  if (activeHls) { activeHls.destroy(); activeHls = null; }
  video.removeAttribute('src');
  video.load();
}

/** Resolves once the video has enough metadata to know its dimensions. */
function whenReady(video) {
  return new Promise((resolve, reject) => {
    if (video.videoWidth) return resolve();
    const ok = () => { cleanup(); resolve(); };
    const fail = () => {
      cleanup();
      const err = video.error;
      reject(new Error(err && err.code === 4
        ? 'הפורמט הזה לא נתמך בדפדפן, או שהשרת חוסם גישה מאתרים אחרים (CORS).'
        : 'טעינת הסרטון נכשלה.'));
    };
    const cleanup = () => {
      video.removeEventListener('loadedmetadata', ok);
      video.removeEventListener('error', fail);
      clearTimeout(timer);
    };
    const timer = setTimeout(fail, 30000);
    video.addEventListener('loadedmetadata', ok);
    video.addEventListener('error', fail);
  });
}

/**
 * @param {HTMLVideoElement} video
 * @param {{type:'file'|'url', url:string, name:string}} source
 */
export async function attach(video, source) {
  detachActive(video);

  if (source.type === 'file') {
    video.crossOrigin = null;
    video.src = source.url;
    await whenReady(video);
    return;
  }

  const { kind } = classify(source.url);

  if (kind === 'hls' && !video.canPlayType('application/vnd.apple.mpegurl')) {
    const Hls = await loadHlsLibrary();
    if (!Hls || !Hls.isSupported()) throw new Error('הדפדפן הזה לא תומך בשידורי HLS.');
    activeHls = new Hls({ enableWorker: true });
    activeHls.loadSource(source.url);
    activeHls.attachMedia(video);
    await new Promise((resolve, reject) => {
      activeHls.on(Hls.Events.MANIFEST_PARSED, resolve);
      activeHls.on(Hls.Events.ERROR, (_e, data) => {
        if (data.fatal) reject(new Error('טעינת השידור נכשלה — ייתכן שהשרת חוסם גישה מאתרים אחרים (CORS).'));
      });
    });
    await whenReady(video);
    return;
  }

  // Ask for CORS first: WebGL refuses to sample a cross-origin video without it.
  video.crossOrigin = 'anonymous';
  video.src = source.url;
  try {
    await whenReady(video);
  } catch (err) {
    // Some servers serve the file happily but send no CORS headers at all.
    // Retrying without the attribute at least lets the user hear/see it in 2D.
    video.crossOrigin = null;
    video.src = source.url;
    await whenReady(video).catch(() => { throw err; });
    throw Object.assign(new Error('tainted'), { tainted: true });
  }
}
