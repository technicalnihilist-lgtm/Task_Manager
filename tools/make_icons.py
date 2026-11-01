#!/usr/bin/env python3
"""Generate the launcher icons for Task Manager.

Draws a gradient "glass card with a check mark" mark and writes:
  res/mipmap-*/ic_launcher.png            legacy icon (API 21-25), rounded square
  res/mipmap-*/ic_launcher_round.png      legacy round icon
  res/mipmap-*/ic_launcher_background.png adaptive icon background layer (full bleed gradient)
  res/mipmap-*/ic_launcher_foreground.png adaptive icon foreground layer (mark inside 72dp safe zone)
  tools/icon-512.png                      512 px store icon

Usage:  python3 tools/make_icons.py        (needs Pillow)
"""
import os
from PIL import Image, ImageDraw

# density -> launcher icon px / adaptive layer px (108dp canvas)
SIZES = {"mdpi": (48, 108), "hdpi": (72, 162), "xhdpi": (96, 216),
         "xxhdpi": (144, 324), "xxxhdpi": (192, 432)}

STOPS = [(0.0, (0x8F, 0xB2, 0xFF)), (0.5, (0xC9, 0xA6, 0xFF)), (1.0, (0xFF, 0xB5, 0xC8))]
SS = 4  # supersample factor


def gradient(s):
    """Vertical-ish diagonal gradient as an RGB image of s x s."""
    small = Image.new("RGB", (1, 256))
    px = small.load()
    for y in range(256):
        t = y / 255.0
        for i in range(len(STOPS) - 1):
            a, ca = STOPS[i]
            b, cb = STOPS[i + 1]
            if a <= t <= b:
                k = (t - a) / (b - a)
                px[0, y] = tuple(int(ca[j] + (cb[j] - ca[j]) * k) for j in range(3))
                break
    return small.resize((s, s), Image.BILINEAR)


def mark(img, s, box=(0.19, 0.81)):
    """Draw the glass card + check mark onto img, inside the given relative box."""
    x0, y0, x1, y1 = box[0] * s, box[0] * s, box[1] * s, box[1] * s
    w, h = x1 - x0, y1 - y0
    glass = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(glass).rounded_rectangle(
        [x0, y0, x1, y1], radius=int(w * 0.27),
        fill=(255, 255, 255, 78), outline=(255, 255, 255, 165), width=max(2, int(w * 0.02)))
    img = Image.alpha_composite(img, glass)

    tick = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    td = ImageDraw.Draw(tick)
    lw = max(4, int(w * 0.135))
    pts = [(x0 + w * 0.245, y0 + h * 0.515),
           (x0 + w * 0.435, y0 + h * 0.705),
           (x0 + w * 0.79, y0 + h * 0.30)]
    td.line(pts, fill=(255, 255, 255, 255), width=lw, joint="curve")
    for p in pts:
        td.ellipse([p[0] - lw / 2, p[1] - lw / 2, p[0] + lw / 2, p[1] + lw / 2], fill=(255, 255, 255, 255))
    return Image.alpha_composite(img, tick)


def legacy_icon(px):
    s = px * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.235), fill=255)
    img.paste(gradient(s), (0, 0), mask)
    img = mark(img, s)
    return img.resize((px, px), Image.LANCZOS)


def adaptive_bg(px):
    s = px * SS
    return gradient(s).convert("RGBA").resize((px, px), Image.LANCZOS)


def adaptive_fg(px):
    """108dp canvas, artwork kept inside the 72dp safe zone."""
    s = px * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    img = mark(img, s, box=(0.245, 0.755))
    return img.resize((px, px), Image.LANCZOS)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name, (px, apx) in SIZES.items():
        d = os.path.join(root, "res", "mipmap-" + name)
        os.makedirs(d, exist_ok=True)
        ic = legacy_icon(px)
        ic.save(os.path.join(d, "ic_launcher.png"))
        ic.save(os.path.join(d, "ic_launcher_round.png"))
        adaptive_bg(apx).save(os.path.join(d, "ic_launcher_background.png"))
        adaptive_fg(apx).save(os.path.join(d, "ic_launcher_foreground.png"))
    legacy_icon(512).save(os.path.join(root, "tools", "icon-512.png"))
    print("icons written")


if __name__ == "__main__":
    main()
