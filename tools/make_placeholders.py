#!/usr/bin/env python3
"""
Generates elegant placeholder artwork (SVG) for every photo listed in
assets/js/data.js, so the gallery can be viewed before the real family
photos are added.

Usage:  python3 tools/make_placeholders.py

To use real photos instead, drop your files into images/<trip-slug>/ and
update the "src" values of that trip in assets/js/data.js.
"""

import os
import random
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# palette: sky_top, sky_bottom, sun, four silhouette layers (far -> near)
PALETTES = {
    "aegean":  ("#0d2b4e", "#f3bd75", "#ffe7b6", ["#3a5f80", "#24455f", "#142c40", "#0a1c2b"]),
    "tuscany": ("#2d3f63", "#eab878", "#ffdfae", ["#5d6a52", "#41503e", "#2a362b", "#18211b"]),
    "japan":   ("#1d2a52", "#dc93a3", "#ffdde3", ["#4a4468", "#332f4f", "#211f36", "#131223"]),
    "alps":    ("#123055", "#d6e7f4", "#ffffff", ["#8fa9c2", "#5b7995", "#334d6b", "#182c47"]),
    "thai":    ("#0f3b4e", "#f6c982", "#fff2cd", ["#2a7a76", "#175a58", "#0d3d3c", "#062626"]),
    "york":    ("#111c38", "#cf9560", "#ffdda6", ["#33436c", "#222d4c", "#151d34", "#0b1020"]),
    "negev":   ("#1e2f52", "#e5ac68", "#ffe3b0", ["#9a7148", "#775336", "#523825", "#2d2016"]),
    "lisbon":  ("#152a52", "#eda971", "#ffe6c1", ["#4a6a8c", "#324c68", "#1e3145", "#101c2a"]),
}

# every trip gets its own palette and a rotation of scenes that fits the place
TRIP_STYLE = {
    "santorini": ("aegean",  ["sea", "town", "sea", "hills", "sea", "town"]),
    "tuscany":   ("tuscany", ["hills", "hills", "forest", "hills", "town", "hills"]),
    "kyoto":     ("japan",   ["forest", "town", "mountains", "town", "forest", "town"]),
    "alps":      ("alps",    ["mountains", "lake", "mountains", "forest", "town", "mountains"]),
    "phuket":    ("thai",    ["sea", "sea", "forest", "sea", "town", "sea"]),
    "lisbon":    ("lisbon",  ["town", "town", "hills", "sea", "town", "town"]),
    "newyork":   ("york",    ["city", "forest", "city", "city", "city", "city"]),
    "negev":     ("negev",   ["dunes", "dunes", "mountains", "dunes", "hills", "dunes"]),
}
DEFAULT_STYLE = ("aegean", ["mountains", "sea", "hills", "forest", "town", "dunes"])


def r(v):
    return round(v, 1)


def poly(points, fill, opacity=1.0):
    pts = " ".join(f"{r(x)},{r(y)}" for x, y in points)
    op = "" if opacity == 1.0 else f' opacity="{opacity}"'
    return f'<polygon points="{pts}" fill="{fill}"{op}/>'


def ridge(rng, w, h, base_y, amp, color, steps=8):
    """A soft rolling silhouette across the full width."""
    step = w / steps
    d = f"M0,{r(base_y)} "
    x = 0.0
    y = base_y
    while x < w:
        nx = x + step
        ny = base_y + rng.uniform(-amp, amp)
        d += f"Q{r(x + step / 2)},{r(min(y, ny) - amp * 0.8)} {r(nx)},{r(ny)} "
        x, y = nx, ny
    d += f"L{r(w)},{r(h)} L0,{r(h)} Z"
    return f'<path d="{d}" fill="{color}"/>'


def peaks(rng, w, h, base_y, amp, color, count=4):
    pts = [(0, h), (0, base_y)]
    step = w / count
    x = 0.0
    for _ in range(count):
        pts.append((x + step * 0.5, base_y - rng.uniform(amp * 0.45, amp)))
        pts.append((x + step, base_y - rng.uniform(0, amp * 0.28)))
        x += step
    pts += [(w, base_y), (w, h)]
    return poly(pts, color)


def cypress(rng, w, base_y, color, count):
    out = []
    for _ in range(count):
        x = rng.uniform(w * 0.04, w * 0.96)
        th = rng.uniform(base_y * 0.10, base_y * 0.22)
        tw = th * rng.uniform(0.13, 0.2)
        out.append(
            f'<ellipse cx="{r(x)}" cy="{r(base_y - th / 2)}" rx="{r(tw)}" ry="{r(th / 2)}" fill="{color}"/>'
        )
        out.append(f'<rect x="{r(x - tw * 0.12)}" y="{r(base_y - th * 0.15)}" '
                   f'width="{r(tw * 0.24)}" height="{r(th * 0.2)}" fill="{color}"/>')
    return "".join(out)


def pines(rng, w, base_y, color, count):
    out = []
    for _ in range(count):
        x = rng.uniform(-w * 0.02, w * 1.02)
        th = rng.uniform(base_y * 0.12, base_y * 0.3)
        tw = th * rng.uniform(0.3, 0.42)
        out.append(poly([(x, base_y - th), (x - tw / 2, base_y + 4), (x + tw / 2, base_y + 4)], color))
        out.append(poly([(x, base_y - th * 0.62), (x - tw * 0.72, base_y + 4), (x + tw * 0.72, base_y + 4)], color))
    return "".join(out)


def houses(rng, w, base_y, color, count, roof=None):
    """Low cubic village houses with pitched roofs."""
    out = []
    for _ in range(count):
        bw = rng.uniform(w * 0.05, w * 0.11)
        bh = bw * rng.uniform(0.55, 0.95)
        x = rng.uniform(-bw, w)
        y = base_y - bh
        out.append(f'<rect x="{r(x)}" y="{r(y)}" width="{r(bw)}" height="{r(bh + 6)}" fill="{color}"/>')
        out.append(poly([(x - bw * 0.08, y), (x + bw / 2, y - bh * 0.34), (x + bw * 1.08, y)],
                        roof or color))
        for _ in range(rng.randint(1, 3)):
            wx = x + rng.uniform(bw * 0.15, bw * 0.75)
            wy = y + rng.uniform(bh * 0.2, bh * 0.65)
            out.append(f'<rect x="{r(wx)}" y="{r(wy)}" width="{r(bw * 0.12)}" '
                       f'height="{r(bh * 0.16)}" fill="#ffe0a8" opacity="0.5"/>')
    return "".join(out)


def skyline(rng, w, h, base_y, color, lit=None):
    out = []
    x = -10.0
    while x < w:
        bw = rng.uniform(w * 0.035, w * 0.085)
        bh = rng.uniform(h * 0.10, h * 0.4)
        top = base_y - bh
        out.append(f'<rect x="{r(x)}" y="{r(top)}" width="{r(bw)}" height="{r(bh + (h - base_y))}" fill="{color}"/>')
        if rng.random() < 0.35:
            out.append(f'<rect x="{r(x + bw * 0.42)}" y="{r(top - bh * 0.14)}" '
                       f'width="{r(bw * 0.16)}" height="{r(bh * 0.14)}" fill="{color}"/>')
        if lit:
            for _ in range(int(bh / 26)):
                wx = x + rng.uniform(bw * 0.12, bw * 0.8)
                wy = top + rng.uniform(bh * 0.08, bh * 0.92)
                out.append(f'<rect x="{r(wx)}" y="{r(wy)}" width="3" height="4.5" fill="{lit}" '
                           f'opacity="{round(rng.uniform(0.18, 0.7), 2)}"/>')
        x += bw + rng.uniform(1.5, w * 0.012)
    return "".join(out)


def dune_band(rng, w, h, base_y, color):
    d = f"M0,{r(base_y)} "
    x = 0.0
    y = base_y
    while x < w:
        cw = rng.uniform(w * 0.2, w * 0.42)
        ny = y + rng.uniform(-h * 0.045, h * 0.055)
        d += f"C{r(x + cw * 0.35)},{r(min(y, ny) - h * 0.075)} {r(x + cw * 0.7)},{r(ny)} {r(x + cw)},{r(ny)} "
        x += cw
        y = ny
    d += f"L{r(w)},{r(h)} L0,{r(h)} Z"
    return f'<path d="{d}" fill="{color}"/>'


def water(rng, w, h, top_y, color, sun_x, sun_color, sun_r):
    out = [f'<rect x="0" y="{r(top_y)}" width="{w}" height="{r(h - top_y)}" fill="{color}"/>']
    out.append(f'<rect x="{r(sun_x - sun_r * 0.7)}" y="{r(top_y)}" width="{r(sun_r * 1.4)}" '
               f'height="{r(h - top_y)}" fill="{sun_color}" opacity="0.2"/>')
    n = 20
    for i in range(n):
        yy = top_y + (h - top_y) * ((i / n) ** 1.6) + 4
        ww = w * rng.uniform(0.05, 0.3)
        xx = rng.uniform(0, w - ww)
        out.append(f'<rect x="{r(xx)}" y="{r(yy)}" width="{r(ww)}" height="{r(h * 0.0035)}" rx="2" '
                   f'fill="#ffffff" opacity="{round(rng.uniform(0.05, 0.2), 2)}"/>')
    return "".join(out)


def build_svg(seed, palette_key, scene, w, h, label):
    rng = random.Random(seed)
    top, bottom, sun, layers = PALETTES[palette_key]
    horizon = h * rng.uniform(0.5, 0.63)
    sun_x = w * rng.uniform(0.18, 0.82)
    sun_y = horizon * rng.uniform(0.32, 0.78)
    sun_r = min(w, h) * rng.uniform(0.045, 0.075)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="{label}">',
        '<defs>',
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{top}"/><stop offset="100%" stop-color="{bottom}"/></linearGradient>',
        '<radialGradient id="glow" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0%" stop-color="{sun}" stop-opacity="0.8"/>'
        f'<stop offset="100%" stop-color="{sun}" stop-opacity="0"/></radialGradient>',
        '<radialGradient id="vig" cx="50%" cy="45%" r="78%">'
        '<stop offset="52%" stop-color="#000" stop-opacity="0"/>'
        '<stop offset="100%" stop-color="#000" stop-opacity="0.5"/></radialGradient>',
        '</defs>',
        f'<rect width="{w}" height="{h}" fill="url(#sky)"/>',
        f'<circle cx="{r(sun_x)}" cy="{r(sun_y)}" r="{r(sun_r * 7)}" fill="url(#glow)"/>',
        f'<circle cx="{r(sun_x)}" cy="{r(sun_y)}" r="{r(sun_r)}" fill="{sun}" opacity="0.92"/>',
    ]

    # wisps of cloud
    for _ in range(rng.randint(3, 6)):
        cy = rng.uniform(horizon * 0.12, horizon * 0.85)
        cw = w * rng.uniform(0.12, 0.4)
        cx = rng.uniform(0, w - cw)
        out.append(f'<rect x="{r(cx)}" y="{r(cy)}" width="{r(cw)}" height="{r(h * 0.007)}" rx="6" '
                   f'fill="{sun}" opacity="{round(rng.uniform(0.05, 0.16), 2)}"/>')

    if scene == "sea":
        out.append(peaks(rng, w, horizon + 6, horizon, h * 0.12, layers[0], count=3))
        out.append(water(rng, w, h, horizon, layers[2], sun_x, sun, sun_r))
        out.append(ridge(rng, w, h, h * 0.93, h * 0.012, layers[3]))
    elif scene == "lake":
        out.append(peaks(rng, w, horizon + 6, horizon, h * 0.3, layers[0], count=3))
        out.append(peaks(rng, w, horizon + 6, horizon * 1.06, h * 0.18, layers[1], count=5))
        out.append(water(rng, w, h, horizon * 1.06, layers[2], sun_x, sun, sun_r))
        out.append(pines(rng, w, horizon * 1.06, layers[3], 12))
    elif scene == "mountains":
        out.append(peaks(rng, w, h, horizon * 0.96, h * 0.32, layers[0], count=3))
        out.append(peaks(rng, w, h, horizon * 1.1, h * 0.26, layers[1], count=4))
        out.append(ridge(rng, w, h, horizon * 1.3, h * 0.035, layers[2]))
        out.append(ridge(rng, w, h, horizon * 1.55, h * 0.025, layers[3]))
    elif scene == "hills":
        out.append(ridge(rng, w, h, horizon, h * 0.045, layers[0]))
        out.append(ridge(rng, w, h, horizon * 1.16, h * 0.05, layers[1]))
        out.append(cypress(rng, w, horizon * 1.16, layers[3], rng.randint(4, 8)))
        out.append(ridge(rng, w, h, horizon * 1.42, h * 0.04, layers[2]))
        out.append(ridge(rng, w, h, horizon * 1.72, h * 0.03, layers[3]))
    elif scene == "dunes":
        out.append(dune_band(rng, w, h, horizon, layers[0]))
        out.append(dune_band(rng, w, h, horizon * 1.2, layers[1]))
        out.append(dune_band(rng, w, h, horizon * 1.45, layers[2]))
        out.append(dune_band(rng, w, h, horizon * 1.75, layers[3]))
    elif scene == "forest":
        out.append(ridge(rng, w, h, horizon, h * 0.05, layers[0]))
        out.append(pines(rng, w, horizon * 1.12, layers[1], 20))
        out.append(f'<rect x="0" y="{r(horizon * 1.12)}" width="{w}" height="{r(h)}" fill="{layers[1]}"/>')
        out.append(pines(rng, w, horizon * 1.42, layers[3], 16))
        out.append(f'<rect x="0" y="{r(horizon * 1.42)}" width="{w}" height="{r(h)}" fill="{layers[3]}"/>')
    elif scene == "city":
        out.append(skyline(rng, w, h, horizon * 1.02, layers[1], lit=sun))
        out.append(skyline(rng, w, h, horizon * 1.28, layers[3], lit=sun))
    else:  # town — village / old quarter on a slope
        out.append(ridge(rng, w, h, horizon, h * 0.05, layers[0]))
        out.append(houses(rng, w, horizon * 1.1, layers[1], rng.randint(7, 11), roof=layers[2]))
        out.append(f'<rect x="0" y="{r(horizon * 1.1)}" width="{w}" height="{r(h)}" fill="{layers[1]}"/>')
        out.append(houses(rng, w, horizon * 1.38, layers[2], rng.randint(6, 9), roof=layers[3]))
        out.append(f'<rect x="0" y="{r(horizon * 1.38)}" width="{w}" height="{r(h)}" fill="{layers[3]}"/>')

    out.append(f'<rect width="{w}" height="{h}" fill="url(#vig)"/>')
    out.append('</svg>')
    return "".join(out)


def main():
    with open(os.path.join(ROOT, "assets", "js", "data.js"), encoding="utf-8") as f:
        source = f.read()

    paths = sorted(set(re.findall(r"images/([a-z0-9\-]+)/([a-z0-9\-]+)\.svg", source)))
    if not paths:
        raise SystemExit("no image paths found in data.js")

    made = 0
    for slug, name in paths:
        folder = os.path.join(ROOT, "images", slug)
        os.makedirs(folder, exist_ok=True)

        palette_key, scenes = TRIP_STYLE.get(slug, DEFAULT_STYLE)
        digits = "".join(ch for ch in name if ch.isdigit())
        order = int(digits) - 1 if digits else 0
        scene = scenes[order % len(scenes)]
        portrait = order % 6 in (2, 5)
        w, h = (1120, 1500) if portrait else (1600, 1067)

        svg = build_svg(f"{slug}/{name}", palette_key, scene, w, h, f"{slug} {name}")
        with open(os.path.join(folder, name + ".svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        made += 1

    print(f"generated {made} placeholder images")


if __name__ == "__main__":
    main()
