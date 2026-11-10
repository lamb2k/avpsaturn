#!/usr/bin/env python
"""Contact sheet of Yaba capture frames (framebuffer_burst output f<NNNN>_*.png): contact.py DIR OUT.png FROM TO STEP [COLS] [SCALE] [CROP x0,y0,x1,y1]. Private: pictures stay out of git."""
import os, sys
from PIL import Image, ImageDraw
d, out, a, b, s = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
cols = int(sys.argv[6]) if len(sys.argv) > 6 else 4
sc = float(sys.argv[7]) if len(sys.argv) > 7 else 0.5
crop = tuple(int(v) for v in sys.argv[8].split(",")) if len(sys.argv) > 8 else None
files = {int(f[1:5]): f for f in os.listdir(d) if f.startswith("f") and f.endswith(".png")}
fr = [f for f in range(a, b + 1, s) if f in files]
ims = []
for f in fr:
    im = Image.open(os.path.join(d, files[f])).convert("RGB")
    if crop: im = im.crop(crop)
    im = im.resize((int(im.width * sc), int(im.height * sc)))
    ImageDraw.Draw(im).text((3, 3), str(f), fill=(255, 255, 0))
    ims.append(im)
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (w * cols, h * rows))
for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out)
print(len(ims), "frames", sheet.size)
