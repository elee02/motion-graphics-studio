#!/usr/bin/env python3
"""3x2 contact sheet of key frames from the rendered sequence."""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = os.path.join(ROOT, "renders", "frames")
OUT = os.path.join(ROOT, "renders", "previews", "contact_sheet.png")
FONT = "/usr/share/fonts/julietaula-montserrat-fonts/Montserrat-Bold.otf"

PICKS = [1, 48, 96, 144, 192, 240]
TW, TH = 640, 360


def main():
    font = ImageFont.truetype(FONT, 22)
    sheet = Image.new("RGB", (TW * 3, TH * 2 + 54), (10, 11, 15))
    d = ImageDraw.Draw(sheet)
    d.text((18, 16), "MIDNIGHT RAMEN  ·  episode 003  ·  shot 01 key frames", font=font, fill=(232, 224, 210))
    for i, f in enumerate(PICKS):
        path = os.path.join(FRAMES, f"frame_{f:04d}.png")
        im = Image.open(path).convert("RGB").resize((TW, TH), Image.LANCZOS)
        x, y = (i % 3) * TW, (i // 3) * TH + 54
        sheet.paste(im, (x, y))
        dd = ImageDraw.Draw(sheet, "RGBA")
        dd.rectangle([x + 12, y + TH - 46, x + 92, y + TH - 12], fill=(0, 0, 0, 150))
        dd.text((x + 24, y + TH - 42), f"f{f:03d}", font=font, fill=(255, 255, 255))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sheet.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
