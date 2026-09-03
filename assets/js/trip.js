/* ------------------------------------------------------------------
   עמוד טיול בודד: נקרא לפי ?trip=<slug>
   ------------------------------------------------------------------ */

(function () {
  function getTrip() {
    const slug = new URLSearchParams(window.location.search).get('trip');
    return TRIPS.find((t) => t.slug === slug) || null;
  }

  function renderMeta(trip) {
    const rows = [
      ['מתי', trip.dateLabel],
      ['יעד', `${trip.title}, ${trip.country}`],
      ['משך', `${trip.days} ימים`],
      ['מי היה', trip.participants.join(' · ')]
    ];
    document.getElementById('tripMeta').innerHTML = rows
      .map(([dt, dd]) => `<div><dt>${esc(dt)}</dt><dd>${esc(dd)}</dd></div>`)
      .join('');
  }

  function renderMosaic(trip) {
    const mosaic = document.getElementById('mosaic');
    mosaic.innerHTML = trip.photos
      .map(
        (photo, i) => `
        <button class="mosaic-item reveal" type="button" data-index="${i}"
                aria-label="פתיחת התמונה במסך מלא: ${esc(photo.caption || trip.title)}">
          <img src="${esc(photo.src)}" alt="${esc(photo.caption || trip.title)}" loading="lazy" decoding="async">
          <span class="mosaic-cap">${esc(photo.caption || '')}</span>
        </button>`
      )
      .join('');

    mosaic.addEventListener('click', (e) => {
      const item = e.target.closest('.mosaic-item');
      if (!item) return;
      Lightbox.open(trip.photos, Number(item.dataset.index), trip.title);
    });

    observeReveals(mosaic);
  }

  function renderNav(trip) {
    const ordered = TRIPS.slice().sort((a, b) => b.year - a.year);
    const pos = ordered.findIndex((t) => t.slug === trip.slug);
    const prev = ordered[pos - 1];
    const next = ordered[pos + 1];

    const link = (item, kind) =>
      item
        ? `<a class="${kind === 'next' ? 'is-next' : ''}" href="trip.html?trip=${encodeURIComponent(item.slug)}">
             <small>${kind === 'next' ? 'הטיול הקודם' : 'הטיול הבא'}</small>
             <strong>${esc(item.title)}</strong>
             <span>${esc(item.country)} · ${item.year}</span>
           </a>`
        : `<a href="index.html#trips">
             <small>האוסף המלא</small>
             <strong>כל הטיולים</strong>
             <span>חזרה לגלריה</span>
           </a>`;

    document.getElementById('tripNav').innerHTML = link(prev, 'prev') + link(next, 'next');
  }

  document.addEventListener('DOMContentLoaded', () => {
    const trip = getTrip();

    if (!trip) {
      document.getElementById('notFound').hidden = false;
      document.title = 'הטיול לא נמצא · סוסובר';
      return;
    }

    document.getElementById('tripRoot').hidden = false;
    document.title = `${trip.title}, ${trip.country} · סוסובר`;
    const desc = document.querySelector('meta[name="description"]');
    if (desc) desc.setAttribute('content', trip.summary);

    document.getElementById('tripHeroImg').style.backgroundImage = `url("${trip.cover}")`;
    document.getElementById('tripEyebrow').textContent = `${trip.country} · ${trip.dateLabel}`;
    document.getElementById('tripTitle').textContent = trip.title;
    document.getElementById('tripSummary').textContent = trip.summary;
    document.getElementById('tripStory').textContent = trip.story;

    renderMeta(trip);
    renderMosaic(trip);
    renderNav(trip);
    observeReveals();

    document.getElementById('playAll').addEventListener('click', () => {
      Lightbox.open(trip.photos, 0, trip.title);
    });
  });
})();
