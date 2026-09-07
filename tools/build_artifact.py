#!/usr/bin/env python3
"""
Builds a single self-contained HTML file from the site, for sharing as one
link (every image is embedded, so the file works with no server at all).

Usage:  python3 tools/build_artifact.py
Output: dist/soosover.html       — standalone page, opens straight from disk
        dist/artifact-body.html  — same page without the <html>/<head> shell,
                                   for hosts that supply their own document
"""

import base64
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def data_uri(rel_path):
    with open(os.path.join(ROOT, rel_path), "rb") as f:
        raw = f.read()
    mime = {
        ".svg": "image/svg+xml",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(os.path.splitext(rel_path)[1].lower(), "application/octet-stream")
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")


def main():
    data_js = read("assets", "js", "data.js")

    # החלפת נתיבי התמונות בקבצים מוטמעים
    missing = []
    cache = {}

    def replace(match):
        rel = match.group(0)
        if rel not in cache:
            full = os.path.join(ROOT, rel)
            if not os.path.exists(full):
                missing.append(rel)
                cache[rel] = rel
            else:
                cache[rel] = data_uri(rel)
        return cache[rel]

    # רק החלק שאחרי הגדרת TRIPS — כדי לא לגעת בדוגמאות שבהערות שבראש הקובץ
    split_at = data_js.index("const TRIPS")
    head, body = data_js[:split_at], data_js[split_at:]
    inlined = head + re.sub(r"images/[^'\"]+\.(?:svg|jpe?g|png|webp)", replace, body)
    if missing:
        print("warning: missing image files: " + ", ".join(sorted(set(missing))))

    page = (
        read("tools", "artifact_template.html")
        .replace("/*{{CSS}}*/", read("assets", "css", "style.css"))
        .replace("/*{{DATA}}*/", inlined)
        .replace("/*{{APP}}*/", read("tools", "artifact_app.js"))
    )

    standalone = (
        '<!DOCTYPE html>\n<html lang="he" dir="rtl">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="description" content="\u05e1\u05d5\u05e1\u05d5\u05d1\u05e8 \u2014 '
        '\u05d0\u05dc\u05d1\u05d5\u05dd \u05d4\u05de\u05e1\u05e2\u05d5\u05ea '
        '\u05d4\u05de\u05e9\u05e4\u05d7\u05ea\u05d9.">\n'
        '<meta name="theme-color" content="#0a1428">\n'
        '<style>body{margin:0}</style>\n'
        "</head>\n<body>\n" + page + "\n</body>\n</html>\n"
    )

    out_dir = os.path.join(ROOT, "dist")
    os.makedirs(out_dir, exist_ok=True)

    for name, content in (("soosover.html", standalone), ("artifact-body.html", page)):
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"wrote {path} ({len(content.encode('utf-8')) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
