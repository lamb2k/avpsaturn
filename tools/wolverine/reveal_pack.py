#!/usr/bin/env python
"""Wolverine reveal art -> the disc file REVEAL.BIN (saturn/rt/reveal.c reads it at the ending).
usage: reveal_pack.py FRAME1.png FRAME2.png FRAME3.png OUT.bin   (the recoloured frames: reveal_recolour.py)

The frames are 384 x 224 indexed pictures sharing one palette (index 0 transparent, 1 black). Rows the picture does not use are black, so only the picture
band of each frame is stored: frames 1 and 2 rows 48 to 175, frame 3 rows 24 to 199 (checked: every other row is index 1). The runtime expands a band into a 512 x 256
8 bit bitmap of VDP2 NBG0 (bank A1, B0, B1), rows above and below it clear to the back screen, which is black.
Format, big endian:
    0   'RVL1'   4 u32 file size (a whole number of 2048 byte sectors)   8 u16 palette entries   10 u16 frames (3)   12 u32 frame record offsets (3)
    24  palette, 128 words: Saturn colours (bit 15 set, 5 bits each of B G R), entry 0 clear
    then per frame: u16 first row, u16 rows, rows x 384 index bytes
The 12-bit grid colours are converted as sat_gfx_colour does for a CPS colour of full brightness."""
import struct
import sys
from PIL import Image
import numpy as np

W, H = 384, 224
BANDS = ((48, 176), (48, 176), (24, 200))   # first row, row after the last


def colour(r, g, b):
    return 0x8000 | (b // 17 * 17 >> 3) << 10 | (g // 17 * 17 >> 3) << 5 | (r // 17 * 17 >> 3)


def pack(frames, out):
    ims = [Image.open(f) for f in frames]
    pal = ims[0].getpalette()
    arrs = [np.array(i) for i in ims]
    npal = max(int(a.max()) for a in arrs) + 1
    assert npal <= 128 and all(i.getpalette()[:npal * 3] == pal[:npal * 3] for i in ims) and all(a.shape == (H, W) for a in arrs)
    words = [0] * 128
    for i in range(1, npal):
        r, g, b = pal[i * 3:i * 3 + 3]
        assert r % 17 == 0 and g % 17 == 0 and b % 17 == 0
        words[i] = colour(r, g, b)
    recs = []
    for a, (r0, r1) in zip(arrs, BANDS):
        assert (a[:r0] == 1).all() and (a[r1:] == 1).all(), "picture outside its band"
        assert not (a == 0).any(), "transparent pixel in a frame"
        recs.append(struct.pack(">HH", r0, r1 - r0) + a[r0:r1].tobytes())
    head = 24 + 256
    offs, at = [], head
    for r in recs:
        offs.append(at)
        at += len(r)
    size = (at + 2047) // 2048 * 2048
    blob = b"RVL1" + struct.pack(">IHH", size, npal, len(recs)) + struct.pack(">3I", *offs) + struct.pack(">128H", *words) + b"".join(recs)
    blob += bytes(size - len(blob))
    open(out, "wb").write(blob)
    return dict(size=size, palette=npal, bands=[(r0, r1) for r0, r1 in BANDS], frame_bytes=[len(r) for r in recs])


if __name__ == "__main__":
    print(pack(sys.argv[1:4], sys.argv[4]))
