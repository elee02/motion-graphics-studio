#!/usr/bin/env python3
"""Title and end cards for episode 003 (1920x1080, no external assets)."""

from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FONT_DIR = "/usr/share/fonts/julietaula-montserrat-fonts"
BOLD = os.path.join(FONT_DIR, "Montserrat-ExtraBold.otf")
MED = os.path.join(FONT_DIR, "Montserrat-Medium.otf")
LIGHT = os.path.join(FONT_DIR, "Montserrat-Light.otf")

AMBER = (255, 176, 92)
CREAM = (240, 232, 218)
DIM = (150, 146, 138)


def base_plate() -> Image.Image:
    """Dark plate with a warm pool of light and a faint crest ring."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W * 0.5, H * 0.62
    r = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 1.25) ** 2) / (W * 0.55)
    glow = np.clip(1.0 - r, 0.0, 1.0) ** 2.6
    img = np.zeros((H, W, 3), dtype=np.float32)
    img[..., 0] = 6 + glow * 58
    img[..., 1] = 7 + glow * 27
    img[..., 2] = 11 + glow * 12

    # crest ring motif
    ring = np.abs(np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) - 300.0)
    ring = np.clip(1.0 - ring / 2.2, 0.0, 1.0) * 0.10
    img += ring[..., None] * np.array([255, 176, 92], dtype=np.float32)

    rng = np.random.default_rng(11)
    img += (rng.standard_normal((H, W, 1)) * 3.2).clip(-8, 8)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


def tracked(draw, xy, text, font, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x


def tracked_width(draw, text, font, tracking=0):
    return sum(draw.textlength(c, font=font) for c in text) + tracking * (len(text) - 1)


def center_tracked(draw, y, text, font, fill, tracking=0):
    w = tracked_width(draw, text, font, tracking)
    tracked(draw, ((W - w) / 2, y), text, font, fill, tracking)


def title_card(path: str):
    img = base_plate()
    d = ImageDraw.Draw(img)
    f_kicker = ImageFont.truetype(MED, 30)
    f_title = ImageFont.truetype(BOLD, 148)
    f_sub = ImageFont.truetype(LIGHT, 34)

    center_tracked(d, 250, "EPISODE 003", f_kicker, AMBER, tracking=16)
    center_tracked(d, 330, "MIDNIGHT", f_title, CREAM, tracking=18)
    center_tracked(d, 490, "RAMEN", f_title, CREAM, tracking=46)

    line_w = 210
    d.rectangle([(W - line_w) / 2, 712, (W + line_w) / 2, 714], fill=AMBER)
    center_tracked(d, 748, "a night shift, in one shot", f_sub, DIM, tracking=8)

    img = img.filter(ImageFilter.GaussianBlur(0.4))
    img.save(path, quality=95)


def end_card(path: str):
    img = base_plate()
    img = img.point(lambda v: int(v * 0.55))
    d = ImageDraw.Draw(img)
    f_title = ImageFont.truetype(BOLD, 74)
    f_kicker = ImageFont.truetype(MED, 24)
    f_credit = ImageFont.truetype(LIGHT, 30)
    f_mark = ImageFont.truetype(MED, 22)

    center_tracked(d, 250, "MIDNIGHT RAMEN", f_title, CREAM, tracking=12)
    center_tracked(d, 352, "EPISODE 003  ·  SHOT 01", f_kicker, AMBER, tracking=10)

    d.rectangle([(W - 150) / 2, 430, (W + 150) / 2, 432], fill=(90, 74, 58))

    credits = [
        "story, set, cast, light and camera built from code",
        "Blender 4.2 LTS  ·  Cycles  ·  1920 × 1080  ·  24 fps",
        "score and mix generated with numpy",
    ]
    y = 480
    for line in credits:
        w = d.textlength(line, font=f_credit)
        d.text(((W - w) / 2, y), line, font=f_credit, fill=DIM)
        y += 52

    center_tracked(d, 720, "MOTION GRAPHICS STUDIO", f_mark, (120, 96, 72), tracking=9)

    img = img.filter(ImageFilter.GaussianBlur(0.4))
    img.save(path, quality=95)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "renders", "cards")
    os.makedirs(out, exist_ok=True)
    title_card(os.path.join(out, "title.png"))
    end_card(os.path.join(out, "end.png"))
    print("cards ->", out)
