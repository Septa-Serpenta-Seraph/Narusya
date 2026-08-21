#!/usr/bin/env python3
"""PIPNARU pipgirl mascot generator — Bethesda-recipe: inset hair/face (contrast),
signature ME/CFS thumbs-up pose, clean N monogram. Saves transparent-background PNG.
Run: python3 make_pipgirl.py  (needs Pillow)."""
from PIL import Image, ImageDraw

GREEN = (74, 255, 106, 255)   # body fill (#4aff6a)
DARK  = (8, 47, 29, 255)      # hair/face/N/boots (#082f1d)
BG    = (0, 0, 0, 0)          # transparent

W, H = 340, 300
img = Image.new("RGBA", (W, H), BG)
d = ImageDraw.Draw(img)

# ── HEAD (lighter green base so dark insets read) ──
d.ellipse([150, 44, 200, 94], fill=GREEN)
# inset HAIR: top half of head = dark, plus fringe curls + side lock
d.pieslice([150, 44, 200, 94], 180, 360, fill=DARK)
d.polygon([(150,70),(152,48),(162,40),(190,40),(200,52),(200,58),(198,54),(186,56),(160,62)], fill=DARK)
d.polygon([(150,66),(146,78),(150,88),(156,78)], fill=DARK)
# FACE (inset on lighter area): eyes + smile
d.ellipse([162,62,168,68], fill=DARK)
d.ellipse([182,62,188,68], fill=DARK)
d.arc([166,66,190,86], 200, 340, fill=DARK, width=2)

# ── NECK ──  (careful: rectangle needs y0 < y1)
d.rectangle([170,98,180,106], fill=GREEN)

# ── TORSO (tapered: shoulders → waist → hips) ──
torso = [(148,106),(144,116),(148,130),(156,146),(164,160),(170,174),
         (172,196),(182,200),(196,194),(194,180),(186,168),(182,152),
         (186,140),(190,126),(186,116)]
d.polygon(torso, fill=GREEN)

# ── SALUTE ARM (right): bent up, fist + thumb = the signature pose ──
d.polygon([(182,112),(196,104),(206,116),(196,126),(186,120),(184,114)], fill=GREEN)
d.polygon([(200,110),(216,116),(216,124),(200,116)], fill=GREEN)
d.polygon([(208,112),(224,114),(224,118),(208,118)], fill=GREEN)   # thumb bar
d.ellipse([212,108,220,116], fill=GREEN)                            # fist

# ── RELAXED LEFT ARM (down) ──
d.polygon([(146,112),(138,132),(142,160),(140,192)], fill=GREEN)
d.ellipse([134,188,146,198], fill=GREEN)

# ── LEGS ──
d.polygon([(170,198),(168,192),(162,222),(156,240),(150,254),(156,258),(176,246)], fill=GREEN)
d.polygon([(184,198),(192,196),(200,224),(206,244),(208,254),(202,258),(186,248)], fill=GREEN)

# ── BOOTS ──
d.polygon([(148,250),(152,264),(158,266),(150,264)], fill=DARK)
d.polygon([(206,250),(202,264),(196,266),(210,264)], fill=DARK)

# ── CHEST N monogram: two filled columns + one thick diagonal (NOT three thin strokes) ──
d.rectangle([166,136,173,158], fill=DARK)
d.rectangle([177,136,184,158], fill=DARK)
d.line([(167,140),(182,156)], fill=DARK, width=6)

img.save("pipgirl.png")
print("saved pipgirl.png")