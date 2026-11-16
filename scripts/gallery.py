"""Build previews/gallery.jpg: one labelled row per saved style, from previews/subN.jpg (a 3-frame strip) + subN.txt (label).
Run: python -I scripts/gallery.py   (re-run after adding a style)"""
import glob, os, re
from PIL import Image, ImageDraw, ImageFont
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -P drops the script dir; fontkit lives here
from fontkit import font as kfont

P = os.path.join(os.path.dirname(__file__), "..", "previews")
strips = sorted(glob.glob(os.path.join(P, "sub*.jpg")), key=lambda p: int(re.search(r"sub(\d+)", p).group(1)))
assert strips, "no previews"
rows = []
for s in strips:
    im = Image.open(s).convert("RGB")
    txt = open(s[:-4] + ".txt", encoding="utf-8").read().strip() if os.path.exists(s[:-4] + ".txt") else os.path.basename(s)
    row = Image.new("RGB", (im.width, im.height + 70), (18, 18, 20))
    row.paste(im, (0, 70))
    ImageDraw.Draw(row).text((14, 16), txt, font=kfont("HelveticaNeueBold.otf", 34), fill=(240, 240, 240))
    rows.append(row)
cw, rh = max(r.width for r in rows), max(r.height for r in rows)   # two columns so 8+ styles stay viewable
nr = (len(rows) + 1) // 2
g = Image.new("RGB", (cw * 2 + 30, nr * (rh + 20)), (18, 18, 20))
for i, r in enumerate(rows):
    g.paste(r, ((i % 2) * (cw + 30), (i // 2) * (rh + 20)))
g.save(os.path.join(P, "gallery.jpg"), quality=88)
print("gallery:", len(rows), "styles")
