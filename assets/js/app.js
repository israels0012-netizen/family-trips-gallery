/* ------------------------------------------------------------------
   לוגיקה משותפת לכל העמודים: כותרת דביקה, תפריט נייד, אנימציות חשיפה
   ------------------------------------------------------------------ */

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

/** מנקה טקסט לפני הזרקה ל-HTML */
function esc(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/** מפעיל אנימציית חשיפה על אלמנטים עם המחלקה reveal */
function observeReveals(root = document) {
  const items = $$('.reveal:not(.is-visible)', root);
  if (!items.length) return;

  if (!('IntersectionObserver' in window)) {
    items.forEach((el) => el.classList.add('is-visible'));
    return;
  }

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      });
    },
    { rootMargin: '0px 0px -12% 0px', threshold: 0.06 }
  );

  items.forEach((el, i) => {
    el.style.transitionDelay = `${Math.min(i, 6) * 70}ms`;
    io.observe(el);
  });
}

/** כותרת שמתכווצת בגלילה */
function initHeader() {
  const header = $('#siteHeader');
  if (!header) return;

  const sync = () => header.classList.toggle('is-stuck', window.scrollY > 40);
  sync();
  window.addEventListener('scroll', sync, { passive: true });
}

/** תפריט המבורגר במובייל */
function initNav() {
  const toggle = $('#navToggle');
  const nav = $('#mainNav');
  if (!toggle || !nav) return;

  const setOpen = (open) => {
    nav.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
  };

  toggle.addEventListener('click', () => {
    setOpen(toggle.getAttribute('aria-expanded') !== 'true');
  });

  nav.addEventListener('click', (e) => {
    if (e.target.closest('a')) setOpen(false);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') setOpen(false);
  });
}

/** מדגיש את הקישור בתפריט לפי המקטע הנראה */
function initScrollSpy() {
  const links = $$('#mainNav a[href^="#"]');
  if (!links.length || !('IntersectionObserver' in window)) return;

  const sections = links
    .map((a) => document.getElementById(a.getAttribute('href').slice(1)))
    .filter(Boolean);

  const spy = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        links.forEach((a) =>
          a.classList.toggle('is-active', a.getAttribute('href') === `#${entry.target.id}`)
        );
      });
    },
    { rootMargin: '-45% 0px -50% 0px' }
  );

  sections.forEach((s) => spy.observe(s));
}

document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  initNav();
  initScrollSpy();
  observeReveals();

  const year = $('#year');
  if (year) year.textContent = new Date().getFullYear();
});
