# ספריות צד שלישי

הקבצים כאן מגיעים כמו שהם מ‑npm ולא נערכו. הם נשמרים בתוך הפרויקט כדי
שהאפליקציה תעבוד גם בלי חיבור ל‑CDN — למשל ברשת ביתית איטית או כשמשקפי ה‑VR
לא מצליחים לגשת לשרתים חיצוניים.

| קובץ | חבילה | גרסה | רישיון |
| --- | --- | --- | --- |
| `three.module.min.js` | [three](https://www.npmjs.com/package/three) | 0.160.0 | MIT — `three.LICENSE` |
| `hls.min.js` | [hls.js](https://www.npmjs.com/package/hls.js) | 1.5.17 | Apache-2.0 — `hls.js.LICENSE` |

עדכון גרסה:

```bash
npm pack three@<version>
tar xzf three-<version>.tgz package/build/three.module.min.js
cp package/build/three.module.min.js vr/vendor/three.module.min.js
```
