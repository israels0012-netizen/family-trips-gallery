/* ------------------------------------------------------------------
   עמוד הבית: תמונות רקע מתחלפות, נתונים, סינון וחיפוש, ציר זמן
   ------------------------------------------------------------------ */

(function () {
  const byYearDesc = (a, b) => b.year - a.year;
  const byYearAsc = (a, b) => a.year - b.year;

  /* ---------- רקע ה-Hero ---------- */
  function initHero() {
    const bg = document.getElementById('heroBg');
    const note = document.getElementById('heroNote');
    if (note) note.textContent = SITE.intro;
    if (!bg) return;

    const covers = TRIPS.slice()
      .sort(byYearDesc)
      .slice(0, 5)
      .map((t) => t.cover);

    covers.forEach((src, i) => {
      const slide = document.createElement('div');
      slide.className = 'hero-slide' + (i === 0 ? ' is-active' : '');
      slide.style.backgroundImage = `url("${src}")`;
      bg.appendChild(slide);
    });

    if (covers.length < 2 || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const slides = Array.from(bg.children);
    let current = 0;
    setInterval(() => {
      slides[current].classList.remove('is-active');
      current = (current + 1) % slides.length;
      slides[current].classList.add('is-active');
    }, 6500);
  }

  /* ---------- פס הנתונים ---------- */
  function countUp(el, target) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      el.textContent = target;
      return;
    }
    const duration = 1100;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min((now - start) / duration, 1);
      el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  function initStats() {
    const strip = document.getElementById('stats');
    if (!strip) return;

    const years = TRIPS.map((t) => t.year);
    const values = {
      statTrips: TRIPS.length,
      statCountries: new Set(TRIPS.map((t) => t.country)).size,
      statPhotos: TRIPS.reduce((sum, t) => sum + t.photos.length, 0),
      statYears: years.length ? Math.max(...years) - Math.min(...years) + 1 : 0
    };

    const run = () => Object.entries(values).forEach(([id, v]) => {
      const el = document.getElementById(id);
      if (el) countUp(el, v);
    });

    if (!('IntersectionObserver' in window)) return run();
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        run();
        io.disconnect();
      }
    }, { threshold: 0.35 });
    io.observe(strip);
  }

  /* ---------- כרטיס טיול ---------- */
  function cardHTML(trip) {
    return `
      <a class="trip-card reveal" href="trip.html?trip=${encodeURIComponent(trip.slug)}"
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

  /* ---------- סינון וחיפוש ---------- */
  function initGallery() {
    const grid = document.getElementById('tripGrid');
    const chipsBox = document.getElementById('filterChips');
    const search = document.getElementById('searchInput');
    const empty = document.getElementById('emptyState');
    if (!grid) return;

    const regions = Array.from(new Set(TRIPS.map((t) => t.region)));
    const filters = [{ key: 'all', label: 'הכול' }].concat(
      regions.map((r) => ({ key: `region:${r}`, label: r }))
    );

    chipsBox.innerHTML = filters
      .map(
        (f, i) =>
          `<button class="chip${i === 0 ? ' is-active' : ''}" type="button" data-filter="${esc(f.key)}"
             aria-pressed="${i === 0}">${esc(f.label)}</button>`
      )
      .join('');

    let activeFilter = 'all';
    let query = '';

    const matches = (trip) => {
      if (activeFilter !== 'all' && `region:${trip.region}` !== activeFilter) return false;
      if (!query) return true;
      const haystack = [
        trip.title, trip.country, trip.region, trip.summary,
        trip.dateLabel, String(trip.year)
      ].join(' ').toLowerCase();
      return query.split(/\s+/).every((word) => haystack.includes(word));
    };

    const render = () => {
      const list = TRIPS.slice().sort(byYearDesc).filter(matches);
      grid.innerHTML = list.map(cardHTML).join('');
      empty.hidden = list.length > 0;
      observeReveals(grid);
      // הכרטיסים שכבר בתוך המסך נחשפים מיד
      requestAnimationFrame(() => {
        $$('.trip-card', grid).forEach((card) => {
          if (card.getBoundingClientRect().top < window.innerHeight) card.classList.add('is-visible');
        });
      });
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
      debounce = setTimeout(() => {
        query = search.value.trim().toLowerCase();
        render();
      }, 140);
    });

    render();
  }

  /* ---------- ציר זמן ---------- */
  function initTimeline() {
    const box = document.getElementById('timelineList');
    if (!box) return;

    box.innerHTML = TRIPS.slice()
      .sort(byYearAsc)
      .map(
        (trip) => `
        <div class="tl-item reveal">
          <a class="tl-card" href="trip.html?trip=${encodeURIComponent(trip.slug)}">
            <img src="${esc(trip.cover)}" alt="" loading="lazy" decoding="async">
            <span>
              <span class="tl-year">${esc(trip.dateLabel)}</span>
              <h4>${esc(trip.title)}</h4>
              <p>${esc(trip.country)} · ${trip.days} ימים · ${trip.photos.length} תמונות</p>
            </span>
          </a>
        </div>`
      )
      .join('');

    observeReveals(box);
  }

  document.addEventListener('DOMContentLoaded', () => {
    initHero();
    initStats();
    initGallery();
    initTimeline();
  });
})();
