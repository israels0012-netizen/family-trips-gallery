/* ------------------------------------------------------------------
   גרסת עמוד יחיד של האתר (לפרסום כקישור לשיתוף).
   אותה לוגיקה של האתר, עם ניתוב פנימי לפי ה-hash: #trip/<slug>
   ------------------------------------------------------------------ */

(function () {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function observeReveals(root = document) {
    const items = $$('.reveal:not(.is-visible)', root);
    if (!items.length) return;
    if (!('IntersectionObserver' in window) || reduceMotion) {
      items.forEach((el) => el.classList.add('is-visible'));
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.05 });

    items.forEach((el, i) => {
      el.style.transitionDelay = `${Math.min(i, 6) * 70}ms`;
      io.observe(el);
      // כל מה שכבר בתוך המסך נחשף מיד, כדי שהעמוד לא ייראה ריק בטעינה
      if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add('is-visible');
    });
  }

  /* ---------- כותרת ותפריט ---------- */
  function initChrome() {
    const header = $('#siteHeader');
    const sync = () => header.classList.toggle('is-stuck', window.scrollY > 40);
    sync();
    window.addEventListener('scroll', sync, { passive: true });

    const toggle = $('#navToggle');
    const nav = $('#mainNav');
    const setOpen = (open) => {
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
    };
    toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
    nav.addEventListener('click', (e) => { if (e.target.closest('a')) setOpen(false); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setOpen(false); });

    $('#year').textContent = new Date().getFullYear();
  }

  /* ---------- לייטבוקס ---------- */
  const Lightbox = (function () {
    let photos = [];
    let index = 0;
    let title = '';
    let lastFocus = null;
    const el = {};

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
    }

    function go(step) {
      if (!photos.length) return;
      index = (index + step + photos.length) % photos.length;
      draw();
    }

    function open(list, startIndex, galleryTitle) {
      if (!list || !list.length) return;
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
      el.root.classList.remove('is-open');
      document.body.classList.remove('is-locked');
      el.stage.innerHTML = '';
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    const isOpen = () => el.root.classList.contains('is-open');

    function init() {
      el.root = $('#lightbox');
      el.stage = $('#lbStage');
      el.title = $('#lbTitle');
      el.count = $('#lbCount');
      el.caption = $('#lbCaption');
      el.close = $('#lbClose');
      el.prev = $('#lbPrev');
      el.next = $('#lbNext');

      el.close.addEventListener('click', close);
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
          focusables[(pos + (e.shiftKey ? -1 : 1) + focusables.length) % focusables.length].focus();
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

    return { init, open, close, isOpen };
  })();

  /* ---------- עמוד הבית ---------- */
  function initHero() {
    $('#heroNote').textContent = SITE.intro;
    const bg = $('#heroBg');
    const covers = TRIPS.slice().sort((a, b) => b.year - a.year).slice(0, 5).map((t) => t.cover);

    covers.forEach((src, i) => {
      const slide = document.createElement('div');
      slide.className = 'hero-slide' + (i === 0 ? ' is-active' : '');
      slide.style.backgroundImage = `url("${src}")`;
      bg.appendChild(slide);
    });

    if (covers.length < 2 || reduceMotion) return;
    const slides = Array.from(bg.children);
    let current = 0;
    setInterval(() => {
      slides[current].classList.remove('is-active');
      current = (current + 1) % slides.length;
      slides[current].classList.add('is-active');
    }, 6500);
  }

  function countUp(el, target) {
    if (reduceMotion) { el.textContent = target; return; }
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min((now - start) / 1100, 1);
      el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  function initStats() {
    const years = TRIPS.map((t) => t.year);
    const values = {
      statTrips: TRIPS.length,
      statCountries: new Set(TRIPS.map((t) => t.country)).size,
      statPhotos: TRIPS.reduce((sum, t) => sum + t.photos.length, 0),
      statYears: years.length ? Math.max(...years) - Math.min(...years) + 1 : 0
    };
    const run = () => Object.entries(values).forEach(([id, v]) => countUp($('#' + id), v));

    if (!('IntersectionObserver' in window)) return run();
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) { run(); io.disconnect(); }
    }, { threshold: 0.35 });
    io.observe($('#stats'));
  }

  function cardHTML(trip) {
    return `
      <a class="trip-card reveal" href="#trip/${encodeURIComponent(trip.slug)}"
         aria-label="${esc(trip.title)}, ${esc(trip.country)}, ${trip.year}">
        <div class="trip-card-media">
          <span class="trip-year">${trip.year}</span>
          <img src="${esc(trip.cover)}" alt="${esc(trip.title)} — ${esc(trip.country)}" loading="lazy" decoding="async">
        </div>
        <div class="trip-card-body">
          <span class="trip-card-country">${esc(trip.country)}</span>
          <h3>${esc(trip.title)}</h3>
          <p class="trip-card-summary">${esc(trip.summary)}</p>
          <div class="trip-card-meta">
            <span>${esc(trip.dateLabel)}</span>
            <span>${trip.photos.length} תמונות</span>
            <span class="go">לצפייה <span aria-hidden="true">←</span></span>
          </div>
        </div>
      </a>`;
  }

  function initGallery() {
    const grid = $('#tripGrid');
    const chipsBox = $('#filterChips');
    const search = $('#searchInput');
    const empty = $('#emptyState');

    const regions = Array.from(new Set(TRIPS.map((t) => t.region)));
    const filters = [{ key: 'all', label: 'הכול' }].concat(
      regions.map((r) => ({ key: `region:${r}`, label: r }))
    );

    chipsBox.innerHTML = filters
      .map((f, i) => `<button class="chip${i === 0 ? ' is-active' : ''}" type="button"
           data-filter="${esc(f.key)}" aria-pressed="${i === 0}">${esc(f.label)}</button>`)
      .join('');

    let activeFilter = 'all';
    let query = '';

    const matches = (trip) => {
      if (activeFilter !== 'all' && `region:${trip.region}` !== activeFilter) return false;
      if (!query) return true;
      const haystack = [trip.title, trip.country, trip.region, trip.summary, trip.dateLabel, String(trip.year)]
        .join(' ').toLowerCase();
      return query.split(/\s+/).every((word) => haystack.includes(word));
    };

    const render = () => {
      const list = TRIPS.slice().sort((a, b) => b.year - a.year).filter(matches);
      grid.innerHTML = list.map(cardHTML).join('');
      empty.hidden = list.length > 0;
      observeReveals(grid);
    };

    chipsBox.addEventListener('click', (e) => {
      const chip = e.target.closest('.chip');
      if (!chip) return;
      activeFilter = chip.dataset.filter;
      $$('.chip', chipsBox).forEach((c) => {
        const on = c === chip;
        c.classList.toggle('is-active', on);
        c.setAttribute('aria-pressed', String(on));
      });
      render();
    });

    let debounce;
    search.addEventListener('input', () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => { query = search.value.trim().toLowerCase(); render(); }, 140);
    });

    render();
  }

  function initTimeline() {
    const box = $('#timelineList');
    box.innerHTML = TRIPS.slice().sort((a, b) => a.year - b.year).map((trip) => `
      <div class="tl-item reveal">
        <a class="tl-card" href="#trip/${encodeURIComponent(trip.slug)}">
          <img src="${esc(trip.cover)}" alt="" loading="lazy" decoding="async">
          <span>
            <span class="tl-year">${esc(trip.dateLabel)}</span>
            <h4>${esc(trip.title)}</h4>
            <p>${esc(trip.country)} · ${trip.days} ימים · ${trip.photos.length} תמונות</p>
          </span>
        </a>
      </div>`).join('');
    observeReveals(box);
  }

  /* ---------- עמוד טיול ---------- */
  function renderTrip(trip) {
    $('#tripHeroImg').style.backgroundImage = `url("${trip.cover}")`;
    $('#tripEyebrow').textContent = `${trip.country} · ${trip.dateLabel}`;
    $('#tripTitle').textContent = trip.title;
    $('#tripSummary').textContent = trip.summary;
    $('#tripStory').textContent = trip.story;

    $('#tripMeta').innerHTML = [
      ['מתי', trip.dateLabel],
      ['יעד', `${trip.title}, ${trip.country}`],
      ['משך', `${trip.days} ימים`],
      ['מי היה', trip.participants.join(' · ')]
    ].map(([dt, dd]) => `<div><dt>${esc(dt)}</dt><dd>${esc(dd)}</dd></div>`).join('');

    const mosaic = $('#mosaic');
    mosaic.innerHTML = trip.photos.map((photo, i) => `
      <button class="mosaic-item reveal" type="button" data-index="${i}"
              aria-label="פתיחת התמונה במסך מלא: ${esc(photo.caption || trip.title)}">
        <img src="${esc(photo.src)}" alt="${esc(photo.caption || trip.title)}" loading="lazy" decoding="async">
        <span class="mosaic-cap">${esc(photo.caption || '')}</span>
      </button>`).join('');
    mosaic.onclick = (e) => {
      const item = e.target.closest('.mosaic-item');
      if (item) Lightbox.open(trip.photos, Number(item.dataset.index), trip.title);
    };
    $('#playAll').onclick = () => Lightbox.open(trip.photos, 0, trip.title);

    const ordered = TRIPS.slice().sort((a, b) => b.year - a.year);
    const pos = ordered.findIndex((t) => t.slug === trip.slug);
    const link = (item, kind) => item
      ? `<a class="${kind === 'next' ? 'is-next' : ''}" href="#trip/${encodeURIComponent(item.slug)}">
           <small>${kind === 'next' ? 'הטיול הקודם' : 'הטיול הבא'}</small>
           <strong>${esc(item.title)}</strong>
           <span>${esc(item.country)} · ${item.year}</span>
         </a>`
      : `<a href="#trips"><small>האוסף המלא</small><strong>כל הטיולים</strong><span>חזרה לגלריה</span></a>`;
    $('#tripNav').innerHTML = link(ordered[pos - 1], 'prev') + link(ordered[pos + 1], 'next');

    observeReveals($('#viewTrip'));
  }

  /* ---------- ניתוב ---------- */
  function route() {
    const hash = window.location.hash;
    const home = $('#viewHome');
    const trip = $('#viewTrip');

    if (Lightbox.isOpen()) Lightbox.close();

    const match = hash.match(/^#trip\/(.+)$/);
    const found = match && TRIPS.find((t) => t.slug === decodeURIComponent(match[1]));

    if (found) {
      home.hidden = true;
      trip.hidden = false;
      document.title = `${found.title}, ${found.country} · סוסובר`;
      renderTrip(found);
      window.scrollTo(0, 0);
      return;
    }

    trip.hidden = true;
    home.hidden = false;
    document.title = 'סוסובר';

    const target = hash && hash !== '#top' ? document.querySelector(hash) : null;
    if (target) {
      target.scrollIntoView({ behavior: 'auto', block: 'start' });
    } else if (hash === '#top') {
      window.scrollTo(0, 0);
    }
    observeReveals(home);
  }

  function boot() {
    initChrome();
    Lightbox.init();
    initHero();
    initStats();
    initGallery();
    initTimeline();
    route();
    window.addEventListener('hashchange', route);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
