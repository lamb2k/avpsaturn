#!/usr/bin/env python
"""usage: lookdiff.py DIR_A DIR_B [OUT_DIR]   (lane perf-pic)  Auto pixel diff of the look-check screenshots (runs of SAT_SCRIPT_FREEZE builds, look_run.py: look_1.png .. look_7.png, one per freeze at the same game tick).
Compares the picture area (the emulator window's client area without its title and menu bar) and leaves out the performance readout box at the bottom left (its numbers and build id differ by build). Per mark: pixels that differ by more
than THR in any channel, as a count and a share of the picture, the bounding box of the difference, and a diff image (OUT_DIR/diff_<n>.png: A | B | difference in red on black)."""
import os, sys
from PIL import Image, ImageChops
args = [x for x in sys.argv[1:] if not x.startswith('--')]
a, b = args[0], args[1]; out = args[2] if len(args) > 2 else None
THR = 24
MASK_BLINK = '--keep-blink' not in sys.argv
if out: os.makedirs(out, exist_ok=True)
tot = 0
for n in range(1, 8):
    pa, pb = os.path.join(a, 'look_%d.png' % n), os.path.join(b, 'look_%d.png' % n)
    if not (os.path.exists(pa) and os.path.exists(pb)): print('mark', n, 'missing'); continue
    A, B = Image.open(pa).convert('RGB'), Image.open(pb).convert('RGB')
    if A.size != B.size: print('mark', n, 'size differs', A.size, B.size); continue
    W, H = A.size
    box = (8, 88, W - 8, H - 42)   # picture area of the window (title and menu bar above, margin around)
    A, B = A.crop(box), B.crop(box)
    d = ImageChops.difference(A, B).convert('L').point(lambda v: 255 if v > THR else 0)
    w, h = d.size
    d.paste(0, (0, int(h * 0.74), int(w * 0.55), h))   # the readout box (7 lines at the bottom left)
    if MASK_BLINK: d.paste(0, (int(w * 0.62), 0, w, int(h * 0.16)))   # the 2P PRESS START text at the top right flashes by the vblank counter, not by the game tick: its phase differs between builds
    px = d.load(); cnt = sum(1 for y in range(h) for x in range(w) if px[x, y])
    bb = d.getbbox()
    tot += cnt
    print('mark %d: %d of %d pixels differ (%.3f %%) bbox %s' % (n, cnt, w * h, 100.0 * cnt / (w * h), bb))
    if out:
        red = Image.merge('RGB', (d, Image.new('L', d.size, 0), Image.new('L', d.size, 0)))
        sheet = Image.new('RGB', (w * 3, h)); sheet.paste(A, (0, 0)); sheet.paste(B, (w, 0)); sheet.paste(red, (2 * w, 0)); sheet.save(os.path.join(out, 'diff_%d.png' % n))
print('total differing pixels over the marks:', tot)
