#!/usr/bin/env python3
"""Verify an expression catalog's skin color.

Reports the green-dominant pixel fraction for each emotion, overall and in the
center face region. Exits non-zero if any image fails.

Usage: python3 verify_catalog.py [catalog_dir]
"""
import os
import sys

from PIL import Image

CATALOG = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/.hermes/narusya-expressions")
EMOTIONS = ["happy", "sad", "angry", "surprised", "love", "intrigued",
            "disgusted", "fear", "peace", "trickster", "sharp", "still"]
ALL_MIN = 0.05    # whole-image floor: below this the skin color didn't render at all
FACE_MIN = 0.50   # face region must be strongly green-dominant


def green_fraction(pixels):
    if not pixels:
        return 0.0
    return sum(1 for r, g, b in pixels if g > r and g > b) / len(pixels)


def main():
    failures = []
    for emo in EMOTIONS:
        path = next((os.path.join(CATALOG, f"{emo}{ext}")
                     for ext in (".jpg", ".png", ".webp")
                     if os.path.exists(os.path.join(CATALOG, f"{emo}{ext}"))), None)
        if path is None:
            print(f"MISSING {emo}")
            failures.append(emo)
            continue
        img = Image.open(path).convert("RGB").resize((100, 100))
        all_px = list(img.getdata())
        face = [img.getpixel((x, y)) for x in range(30, 70) for y in range(30, 70)]
        all_green = green_fraction(all_px)
        face_green = green_fraction(face)
        mean = tuple(sum(c[i] for c in face) // len(face) for i in range(3))
        ok = all_green >= ALL_MIN and face_green >= FACE_MIN
        print(f"{'OK  ' if ok else 'FAIL'} {emo:10} face_green={face_green:.2f} "
              f"all_green={all_green:.2f} face_mean={mean}")
        if not ok:
            failures.append(emo)
    print("---")
    print("FAILURES:", failures if failures else "none")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
