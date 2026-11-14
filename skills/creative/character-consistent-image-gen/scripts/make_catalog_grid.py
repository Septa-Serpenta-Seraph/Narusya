#!/usr/bin/env python3
"""Build a labeled grid of an expression catalog for review.

Usage: python3 make_catalog_grid.py [catalog_dir] [out.png]
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

CATALOG = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/.hermes/narusya-expressions")
OUT = sys.argv[2] if len(sys.argv) > 2 else "/home/adora/.hermes/cache/scratch/catalog_grid.png"
EMOTIONS = ["happy", "sad", "angry", "surprised", "love", "intrigued",
            "disgusted", "fear", "peace", "trickster", "sharp", "still"]
COLS, ROWS = 4, 3
CELL, LABEL_H = 420, 46


def load_font(size=30):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def main():
    canvas = Image.new("RGB", (COLS * CELL, ROWS * (CELL + LABEL_H)), (18, 18, 22))
    draw = ImageDraw.Draw(canvas)
    font = load_font()
    missing = []
    for i, emo in enumerate(EMOTIONS):
        row, col = divmod(i, COLS)
        x, y = col * CELL, row * (CELL + LABEL_H)
        path = next((os.path.join(CATALOG, f"{emo}{ext}")
                     for ext in (".jpg", ".png", ".webp")
                     if os.path.exists(os.path.join(CATALOG, f"{emo}{ext}"))), None)
        if path is None:
            missing.append(emo)
            continue
        img = Image.open(path).convert("RGB")
        img.thumbnail((CELL - 8, CELL - 8))
        canvas.paste(img, (x + (CELL - img.width) // 2, y + (CELL - img.height) // 2))
        label = draw.textbbox((0, 0), emo, font=font)
        width = label[2] - label[0]
        draw.text((x + (CELL - width) // 2, y + CELL + 6), emo, fill=(245, 240, 230), font=font)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    canvas.save(OUT, "PNG")
    print("SAVED", OUT, canvas.size, "missing:", missing)


if __name__ == "__main__":
    main()
