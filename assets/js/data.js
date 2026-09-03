/* ------------------------------------------------------------------
   נתוני הטיולים
   ------------------------------------------------------------------
   כדי להוסיף טיול חדש: העתיקו בלוק קיים, שנו את הערכים, וצרו תיקייה
   בשם ה-slug בתוך images/ עם התמונות.

   כדי להחליף תמונות דמו בתמונות אמיתיות: העלו את הקבצים לתיקיית
   images/<slug>/ ועדכנו את הנתיב בשדה src (למשל "images/greece/01.jpg").
   ------------------------------------------------------------------ */

const SITE = {
  name: 'סוסובר',
  tagline: 'מסביב לעולם ביום אחד',
  intro: 'אוסף הזיכרונות מהטיולים המשותפים שלנו — כל מסע, כל נוף וכל רגע שנשמר.',
  email: 'israels0012@gmail.com'
};

const TRIPS = [
  {
    slug: 'santorini',
    title: 'סנטוריני',
    country: 'יוון',
    region: 'אירופה',
    year: 2019,
    dateLabel: 'יוני 2019',
    days: 7,
    summary: 'בתים לבנים על הצוק, כיפות כחולות ושקיעות שלא נגמרות מעל הקלדרה.',
    story: 'התחלנו את הבוקר בעיירה אויה, כשהסמטאות עדיין ריקות והאור רך. ירדנו במדרגות אל הנמל הישן, שטנו סביב הקלדרה ועצרנו במעיינות החמים. בכל ערב חזרנו לאותה מרפסת קטנה כדי לראות את השמש נבלעת בים — וכל פעם מחדש כולם השתתקו לרגע.',
    participants: ['אבא', 'אמא', 'הילדים', 'סבתא'],
    cover: 'images/santorini/01.svg',
    photos: [
      { src: 'images/santorini/01.svg', caption: 'שקיעה מעל הקלדרה, אויה' },
      { src: 'images/santorini/02.svg', caption: 'הסמטאות הלבנות בבוקר' },
      { src: 'images/santorini/03.svg', caption: 'הדרך אל הנמל הישן' },
      { src: 'images/santorini/04.svg', caption: 'שיט סביב האי' },
      { src: 'images/santorini/05.svg', caption: 'ארוחת ערב מול הים' },
      { src: 'images/santorini/06.svg', caption: 'כיפות כחולות בשעת בין ערביים' }
    ]
  },
  {
    slug: 'tuscany',
    title: 'טוסקנה',
    country: 'איטליה',
    region: 'אירופה',
    year: 2021,
    dateLabel: 'ספטמבר 2021',
    days: 9,
    summary: 'גבעות ירוקות, שדרות ברושים וכפרים מבוצרים שנראים כאילו הזמן עצר בהם.',
    story: 'נסענו בכביש צדדי בין סיינה לוואל דאורצ׳ה, ובכל עיקול נפתח נוף חדש. עצרנו לפיקניק מתחת לשדרת ברושים, קנינו גבינה ולחם בשוק הכפרי, וסיימנו את היום ביקב משפחתי קטן שבו סיפרו לנו על ארבעה דורות שעובדים באותה אדמה.',
    participants: ['אבא', 'אמא', 'הילדים'],
    cover: 'images/tuscany/01.svg',
    photos: [
      { src: 'images/tuscany/01.svg', caption: 'שדרת הברושים בוואל דאורצ׳ה' },
      { src: 'images/tuscany/02.svg', caption: 'בוקר ערפילי בין הגבעות' },
      { src: 'images/tuscany/03.svg', caption: 'סמטה בכפר מבוצר' },
      { src: 'images/tuscany/04.svg', caption: 'הכרמים לפני הבציר' },
      { src: 'images/tuscany/05.svg', caption: 'שוק הבוקר' },
      { src: 'images/tuscany/06.svg', caption: 'אור אחרון על הגבעות' }
    ]
  },
  {
    slug: 'kyoto',
    title: 'קיוטו וטוקיו',
    country: 'יפן',
    region: 'אסיה',
    year: 2023,
    dateLabel: 'אפריל 2023',
    days: 12,
    summary: 'פריחת הדובדבן, מקדשים עתיקים ועיר ענקית שמצליחה להיות שקטה.',
    story: 'הגענו בדיוק בשיא הפריחה. בבוקר הלכנו בשביל הפילוסופים כשעלי כותרת ורודים נופלים על המים, ובערב מצאנו את עצמנו בסמטה זעירה בטוקיו מול דוכן ראמן עם שישה כיסאות. יפן לימדה אותנו כמה יופי יש בדברים הקטנים ובסדר שבהם.',
    participants: ['אבא', 'אמא', 'הילדים', 'דוד ודודה'],
    cover: 'images/kyoto/01.svg',
    photos: [
      { src: 'images/kyoto/01.svg', caption: 'פריחת דובדבן בשביל הפילוסופים' },
      { src: 'images/kyoto/02.svg', caption: 'שערי טורי אדומים' },
      { src: 'images/kyoto/03.svg', caption: 'גן הזן במקדש' },
      { src: 'images/kyoto/04.svg', caption: 'רחוב בטוקיו אחרי הגשם' },
      { src: 'images/kyoto/05.svg', caption: 'יער הבמבוק באראשיאמה' },
      { src: 'images/kyoto/06.svg', caption: 'פנסים בערב' }
    ]
  },
  {
    slug: 'alps',
    title: 'האלפים',
    country: 'שווייץ',
    region: 'אירופה',
    year: 2022,
    dateLabel: 'יולי 2022',
    days: 8,
    summary: 'פסגות מושלגות באמצע הקיץ, אגמים בצבע טורקיז ורכבות שמטפסות לעננים.',
    story: 'עלינו ברכבת ההרים עד לתחנה הגבוהה, ובחוץ חיכה שלג באמצע יולי. ירדנו ברגל בשביל שעובר בין אחו פרחים ופעמוני פרות, ובסוף היום ישבנו על שפת אגם שקוף לגמרי ופשוט הקשבנו לשקט.',
    participants: ['אבא', 'אמא', 'הילדים'],
    cover: 'images/alps/01.svg',
    photos: [
      { src: 'images/alps/01.svg', caption: 'הפסגה מעל העננים' },
      { src: 'images/alps/02.svg', caption: 'האגם הטורקיז' },
      { src: 'images/alps/03.svg', caption: 'שביל בין אחו הפרחים' },
      { src: 'images/alps/04.svg', caption: 'הרכבת המטפסת' },
      { src: 'images/alps/05.svg', caption: 'כפר קטן בעמק' },
      { src: 'images/alps/06.svg', caption: 'ערפל בוקר בהרים' }
    ]
  },
  {
    slug: 'phuket',
    title: 'פוקט והאיים',
    country: 'תאילנד',
    region: 'אסיה',
    year: 2018,
    dateLabel: 'דצמבר 2018',
    days: 10,
    summary: 'מים פושרים, מפרצים נסתרים וסירות עץ צבעוניות שלוקחות לאיים.',
    story: 'שכרנו סירת זנב ארוך ליום שלם והפלגנו בין האיים. גילינו מפרץ שאפשר להיכנס אליו רק בשפל, אכלנו פירות ים על החוף כשהרגליים בחול, וחזרנו בשקיעה כשהשמיים היו כתומים לגמרי.',
    participants: ['אבא', 'אמא', 'הילדים'],
    cover: 'images/phuket/01.svg',
    photos: [
      { src: 'images/phuket/01.svg', caption: 'מפרץ נסתר בין הצוקים' },
      { src: 'images/phuket/02.svg', caption: 'סירת זנב ארוך' },
      { src: 'images/phuket/03.svg', caption: 'החוף בבוקר מוקדם' },
      { src: 'images/phuket/04.svg', caption: 'שקיעה מהסירה' },
      { src: 'images/phuket/05.svg', caption: 'שוק הלילה' },
      { src: 'images/phuket/06.svg', caption: 'דקלים על קו החוף' }
    ]
  },
  {
    slug: 'lisbon',
    title: 'ליסבון',
    country: 'פורטוגל',
    region: 'אירופה',
    year: 2020,
    dateLabel: 'פברואר 2020',
    days: 6,
    summary: 'אריחי אזולז׳ו, חשמליות צהובות ונקודות תצפית מעל גגות רעפים.',
    story: 'עלינו וירדנו בין הגבעות של אלפמה עד שאיבדנו את הכיוון, ודווקא אז מצאנו את המרפסת הכי יפה בעיר. בערב שמענו פאדו במסעדה קטנה, ובדרך חזרה קנינו פסטל דה נאטה חמים ישר מהתנור.',
    participants: ['אבא', 'אמא', 'הילדים'],
    cover: 'images/lisbon/01.svg',
    photos: [
      { src: 'images/lisbon/01.svg', caption: 'גגות אלפמה בשעת זהב' },
      { src: 'images/lisbon/02.svg', caption: 'החשמלית הצהובה' },
      { src: 'images/lisbon/03.svg', caption: 'סמטה מרוצפת אריחים' },
      { src: 'images/lisbon/04.svg', caption: 'הנהר טז׳ו בערב' },
      { src: 'images/lisbon/05.svg', caption: 'נקודת תצפית מעל העיר' },
      { src: 'images/lisbon/06.svg', caption: 'חזיתות צבעוניות' }
    ]
  },
  {
    slug: 'newyork',
    title: 'ניו יורק',
    country: 'ארצות הברית',
    region: 'אמריקה',
    year: 2024,
    dateLabel: 'נובמבר 2024',
    days: 8,
    summary: 'גורדי שחקים, סנטרל פארק בצבעי סתיו ועיר שלא מפסיקה לרגע.',
    story: 'הלכנו את סנטרל פארק מקצה לקצה כשהעלים בכל גווני הכתום, עלינו לתצפית בדיוק בשקיעה וראינו את כל האורות נדלקים יחד. בערב האחרון תפסנו הצגה בברודוויי — וכולם הסכימו שזה היה השיא.',
    participants: ['אבא', 'אמא', 'הילדים'],
    cover: 'images/newyork/01.svg',
    photos: [
      { src: 'images/newyork/01.svg', caption: 'קו הרקיע בשקיעה' },
      { src: 'images/newyork/02.svg', caption: 'סנטרל פארק בסתיו' },
      { src: 'images/newyork/03.svg', caption: 'רחוב בין הבניינים' },
      { src: 'images/newyork/04.svg', caption: 'הגשר בלילה' },
      { src: 'images/newyork/05.svg', caption: 'אורות ברודוויי' },
      { src: 'images/newyork/06.svg', caption: 'בוקר בעיר' }
    ]
  },
  {
    slug: 'negev',
    title: 'הנגב והמכתש',
    country: 'ישראל',
    region: 'ישראל',
    year: 2025,
    dateLabel: 'מרץ 2025',
    days: 4,
    summary: 'זריחה על שפת המכתש, לילה מלא כוכבים ומדבר שנפתח עד האופק.',
    story: 'קמנו בארבע לפנות בוקר כדי לתפוס את הזריחה על שפת המכתש, וזה היה שווה כל דקה. במשך היום ירדנו לנחל, מצאנו מים בתוך המדבר, ובלילה שכבנו על שקי שינה וספרנו כוכבים עד שנרדמנו.',
    participants: ['אבא', 'אמא', 'הילדים', 'החברים'],
    cover: 'images/negev/01.svg',
    photos: [
      { src: 'images/negev/01.svg', caption: 'זריחה על שפת המכתש' },
      { src: 'images/negev/02.svg', caption: 'דיונות בשעת אור אחרון' },
      { src: 'images/negev/03.svg', caption: 'הדרך במדבר' },
      { src: 'images/negev/04.svg', caption: 'מים בתוך הנחל' },
      { src: 'images/negev/05.svg', caption: 'המחנה לפני החשכה' },
      { src: 'images/negev/06.svg', caption: 'שמי לילה מלאי כוכבים' }
    ]
  }
];
