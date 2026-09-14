import { detect, describe } from '../js/detect.js';

/**
 * Real-world file names and resolutions, and the projection a viewer expects.
 * These are the cases the auto-detection exists to get right.
 */
const CASES = [
  // name, width, height, expected
  ['family_trip_paris.mp4',            1920, 1080, 'flat/mono'],
  ['phone_clip.mov',                   1080, 1920, 'flat/mono'],
  ['drone_ultrawide.mp4',              3840, 1600, 'flat/mono'],
  ['GoPro_MAX_360.mp4',                5760, 2880, '360/mono'],
  ['insta360_equirect.mp4',            4096, 2048, '360/mono'],
  ['beach_VR180_SBS.mp4',              3840, 1920, '180/sbs'],
  ['vr180_mono.mp4',                   4096, 4096, '180/mono'],
  ['unknown_square.mp4',               4096, 4096, '180/mono'],
  ['tour_360_tb.mp4',                  4096, 4096, '360/tb'],
  ['concert 360 3D over-under.mp4',    3840, 3840, '360/tb'],
  ['movie.2023.HSBS.1080p.mkv',        3840, 1080, 'flat/sbs'],
  ['half_ou_3d_movie.mp4',             1920, 1080, 'flat/tb'],
  ['https://cdn.example.com/a/b_vr180_sbs.mp4?token=9', 4096, 2048, '180/sbs'],
];

let failed = 0;
for (const [name, width, height, expected] of CASES) {
  const result = detect(name, width, height);
  const actual = `${result.projection}/${result.layout}`;
  const ok = actual === expected;
  if (!ok) failed++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name.padEnd(38)} ${`${width}×${height}`.padEnd(11)} ${actual}${ok ? '' : `  (expected ${expected})`}`);
}

// `describe` drives the badge text, so it must never show an empty label.
for (const p of ['flat', '180', '360']) {
  for (const l of ['mono', 'sbs', 'tb']) {
    if (!describe({ projection: p, layout: l }).trim()) { console.log(`FAIL  describe(${p}/${l}) is empty`); failed++; }
  }
}

console.log(failed ? `\n${failed} failed` : `\n${CASES.length} detection cases passed`);
process.exit(failed ? 1 : 0);
