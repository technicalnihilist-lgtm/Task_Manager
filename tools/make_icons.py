#!/usr/bin/env python3
"""Generate the launcher icons (gradient glass square + check mark).

Usage:  python3 tools/make_icons.py     (needs Pillow)
Writes res/mipmap-*/ic_launcher.png and tools/icon-512.png
"""
import os
from PIL import Image, ImageDraw

SIZES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
STOPS = [(0.0, (0x8F, 0xB2, 0xFF)), (0.5, (0xC9, 0xA6, 0xFF)), (1.0, (0xFF, 0xB5, 0xC8))]


def icon(px):
    s = px * 4  # supersample, then downscale for smooth edges
    grad = Image.new("RGB", (s, s))
    gd = ImageDraw.Draw(grad)
    for y in range(s):
        t = y / (s - 1)
        for i in range(len(STOPS) - 1):
            a, ca = STOPS[i]
            b, cb = STOPS[i + 1]
            if a <= t <= b:
                k = (t - a) / (b - a)
                gd.line([(0, y), (s, y)], fill=tuple(int(ca[j] + (cb[j] - ca[j]) * k) for j in range(3)))
                break

    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.235), fill=255)
    img.paste(grad, (0, 0), mask)

    glass = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(glass).rounded_rectangle(
        [s * 0.19, s * 0.19, s * 0.81, s * 0.81], radius=int(s * 0.17),
        fill=(255, 255, 255, 72), outline=(255, 255, 255, 150), width=max(2, int(s * 0.012)))
    img = Image.alpha_composite(img, glass)

    tick = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    td = ImageDraw.Draw(tick)
    w = max(4, int(s * 0.085))
    pts = [(s * 0.34, s * 0.51), (s * 0.455, s * 0.63), (s * 0.68, s * 0.385)]
    td.line(pts, fill=(255, 255, 255, 255), width=w, joint="curve")
    for p in pts:
        td.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=(255, 255, 255, 255))
    img = Image.alpha_composite(img, tick)
    return img.resize((px, px), Image.LANCZOS)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name, px in SIZES.items():
        d = os.path.join(root, "res", "mipmap-" + name)
        os.makedirs(d, exist_ok=True)
        ic = icon(px)
        ic.save(os.path.join(d, "ic_launcher.png"))
        ic.save(os.path.join(d, "ic_launcher_round.png"))
    icon(512).save(os.path.join(root, "tools", "icon-512.png"))
    print("icons written")


if __name__ == "__main__":
    main()
