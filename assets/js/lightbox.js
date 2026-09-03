/* ------------------------------------------------------------------
   לייטבוקס מסך מלא: מקלדת, חיצים, החלקה במגע, נעילת גלילה
   ------------------------------------------------------------------ */

const Lightbox = (function () {
  let photos = [];
  let index = 0;
  let title = '';
  let lastFocus = null;

  const el = {};

  function cache() {
    el.root = document.getElementById('lightbox');
    el.stage = document.getElementById('lbStage');
    el.title = document.getElementById('lbTitle');
    el.count = document.getElementById('lbCount');
    el.caption = document.getElementById('lbCaption');
    el.close = document.getElementById('lbClose');
    el.prev = document.getElementById('lbPrev');
    el.next = document.getElementById('lbNext');
    return Boolean(el.root);
  }

  function draw() {
    const photo = photos[index];
    if (!photo) return;

    el.stage.innerHTML = '';
    const img = new Image();
    img.src = photo.src;
    img.alt = photo.caption || title;
    el.stage.appendChild(img);

    el.title.textContent = title;
    el.count.textContent = `${index + 1} / ${photos.length}`;
    el.caption.textContent = photo.caption || '';

    // טעינה מוקדמת של השכנות
    [index + 1, index - 1].forEach((i) => {
      const neighbour = photos[(i + photos.length) % photos.length];
      if (neighbour) new Image().src = neighbour.src;
    });
  }

  function go(step) {
    if (!photos.length) return;
    index = (index + step + photos.length) % photos.length;
    draw();
  }

  function open(list, startIndex, galleryTitle) {
    if (!cache() || !list || !list.length) return;
    photos = list;
    index = Math.max(0, Math.min(startIndex || 0, list.length - 1));
    title = galleryTitle || '';
    lastFocus = document.activeElement;

    el.root.classList.add('is-open');
    document.body.classList.add('is-locked');
    draw();
    el.close.focus();
  }

  function close() {
    if (!el.root) return;
    el.root.classList.remove('is-open');
    document.body.classList.remove('is-locked');
    el.stage.innerHTML = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  const isOpen = () => Boolean(el.root && el.root.classList.contains('is-open'));

  function init() {
    if (!cache()) return;

    el.close.addEventListener('click', close);
    // ב-RTL: "הקודם" נמצא מימין, "הבא" משמאל
    el.prev.addEventListener('click', () => go(-1));
    el.next.addEventListener('click', () => go(1));

    el.root.addEventListener('click', (e) => {
      if (e.target === el.root || e.target === el.stage) close();
    });

    document.addEventListener('keydown', (e) => {
      if (!isOpen()) return;
      if (e.key === 'Escape') return close();
      // בממשק עברי חץ ימינה מוביל לתמונה הקודמת
      if (e.key === 'ArrowRight') { e.preventDefault(); go(-1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); go(1); }
      if (e.key === 'Home') { index = 0; draw(); }
      if (e.key === 'End') { index = photos.length - 1; draw(); }
      if (e.key === 'Tab') {
        const focusables = [el.close, el.prev, el.next];
        const pos = focusables.indexOf(document.activeElement);
        e.preventDefault();
        const nextPos = (pos + (e.shiftKey ? -1 : 1) + focusables.length) % focusables.length;
        focusables[nextPos].focus();
      }
    });

    let touchX = null;
    let touchY = null;
    el.root.addEventListener('touchstart', (e) => {
      touchX = e.changedTouches[0].clientX;
      touchY = e.changedTouches[0].clientY;
    }, { passive: true });

    el.root.addEventListener('touchend', (e) => {
      if (touchX === null) return;
      const dx = e.changedTouches[0].clientX - touchX;
      const dy = e.changedTouches[0].clientY - touchY;
      touchX = null;
      if (Math.abs(dx) < 45 || Math.abs(dx) < Math.abs(dy)) return;
      go(dx > 0 ? -1 : 1);
    }, { passive: true });
  }

  document.addEventListener('DOMContentLoaded', init);

  return { open, close, isOpen };
})();
