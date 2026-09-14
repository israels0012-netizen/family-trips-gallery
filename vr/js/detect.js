/**
 * Automatic detection of how a video is meant to be projected in VR.
 *
 * Two independent signals are combined:
 *   1. Tokens in the file name / URL ("VR180", "SBS", "360", "over-under", ...)
 *   2. The pixel aspect ratio of the video itself.
 *
 * Every (projection, layout) pair is scored, so an explicit hint and an odd
 * aspect ratio can argue with each other and the more confident one wins.
 */

export const PROJECTIONS = ['flat', '180', '360'];
export const LAYOUTS = ['mono', 'sbs', 'tb'];

export const PROJECTION_LABEL = { flat: 'מסך שטוח', '180': '180°', '360': '360°' };
export const LAYOUT_LABEL = { mono: 'רגיל (2D)', sbs: 'זה לצד זה (SBS)', tb: 'אחד מעל השני (TB)' };

/** Lowercase and turn every separator into a space so tokens stand alone. */
function tokenize(name) {
  return ' ' + String(name || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim() + ' ';
}

const NAME_RULES = {
  projection: [
    ['180', /\s(vr180|180|fisheye180|180vr|hemispherical)\s/],
    ['360', /\s(360|vr360|360vr|equirect|equirectangular|spherical|panoramic|panorama|monoscopic360)\s/],
    ['flat', /\s(flat|cinema|screen2d)\s/],
  ],
  layout: [
    ['sbs', /\s(sbs|hsbs|fsbs|lr|rl|3dh|halfsbs|fullsbs|side\sby\sside|stereo\ssbs)\s/],
    ['tb', /\s(tb|tab|htab|ou|ab|3dv|overunder|over\sunder|top\sbottom|topbottom|above\sbelow|abovebelow)\s/],
    ['mono', /\s(mono|monoscopic|2d)\s/],
  ],
};

export function hintsFromName(name) {
  const s = tokenize(name);
  const out = { projection: null, layout: null, tokens: [] };
  for (const kind of ['projection', 'layout']) {
    for (const [value, re] of NAME_RULES[kind]) {
      const m = s.match(re);
      if (m) { out[kind] = value; out.tokens.push(m[1].trim()); break; }
    }
  }
  return out;
}

const bell = (x, mu, sigma) => Math.exp(-((x - mu) ** 2) / (2 * sigma * sigma));

/** Plausibility of `ar` as the shape of ordinary footage: landscape or portrait. */
const flatLobe = (ar) => Math.max(bell(ar, 1.78, 0.45), bell(ar, 0.5625, 0.18) * 0.95);

/** Aspect ratio of one eye once the stereo packing is undone. */
export function eyeAspectOf(aspect, layout) {
  return layout === 'sbs' ? aspect / 2 : layout === 'tb' ? aspect * 2 : aspect;
}

function aspectScore(projection, aspect, layout) {
  const eye = eyeAspectOf(aspect, layout);
  if (projection === '360') return bell(eye, 2.0, 0.11);
  if (projection === '180') return bell(eye, 1.0, 0.085);
  // Flat 3D comes both "full" (each eye keeps its own shape) and "half"
  // (the packed frame keeps the display shape and is stretched back on
  // playback), so for a stereo layout both readings stay on the table.
  return Math.max(flatLobe(eye), layout === 'mono' ? 0 : flatLobe(aspect));
}

/**
 * @param {string} name  file name or URL
 * @param {number} width  video pixel width
 * @param {number} height video pixel height
 * @returns {{projection:string,layout:string,confidence:number,reason:string,alternatives:Array}}
 */
export function detect(name, width, height) {
  const hints = hintsFromName(name);
  const aspect = width && height ? width / height : 16 / 9;

  const ranked = [];
  for (const projection of PROJECTIONS) {
    for (const layout of LAYOUTS) {
      let score = aspectScore(projection, aspect, layout);

      if (hints.projection) score += hints.projection === projection ? 1.15 : -0.5;
      if (hints.layout) score += hints.layout === layout ? 1.15 : -0.5;

      // Without evidence to the contrary, the simpler reading is likelier.
      if (layout === 'mono') score += 0.15;
      if (projection === 'flat') score += 0.04;
      // Immersive footage is almost always high resolution.
      if (projection !== 'flat' && width && width < 1600) score -= 0.25;

      ranked.push({ projection, layout, score });
    }
  }

  ranked.sort((a, b) => b.score - a.score);
  const best = ranked[0];
  const runnerUps = ranked.slice(1).filter((c) => c.score > best.score - 0.6).slice(0, 2);

  const why = [];
  if (hints.tokens.length) why.push(`רמזים בשם הקובץ (${hints.tokens.join(', ')})`);
  if (width && height) why.push(`מידות ${width}×${height} · יחס ${aspect.toFixed(2)}`);

  return {
    projection: best.projection,
    layout: best.layout,
    confidence: Math.min(1, best.score / 2.3),
    reason: why.join(' · ') || 'ברירת מחדל',
    alternatives: runnerUps,
  };
}

export function describe({ projection, layout }) {
  return layout === 'mono'
    ? PROJECTION_LABEL[projection]
    : `${PROJECTION_LABEL[projection]} · ${LAYOUT_LABEL[layout]}`;
}
