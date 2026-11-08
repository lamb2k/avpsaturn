#!/usr/bin/env python
"""Lane alien-measure: contact sheet of one actor kind's sample poses (alien_walk.lua samples.tsv), drawn from the graphics region
(E:/AvP/learning/lane-satgfx/gfx.bin, 16x16 sprite key k at k*0x80) with the palette colours MAME showed at that frame.
usage: render.py RUNDIR KIND OUT.png [SWAP]   KIND like 0c:1f. SWAP: none | hue:DEG | mono:RRGGBB | inv   (palette-swap still).
ROM-derived output: E:/AvP/learning only."""
import colorsys, sys
from PIL import Image, ImageDraw
sys.path.insert(0, "E:/AvP/worktrees/lane-packs/tools")
import satgfx_pack
RAW = open("E:/AvP/learning/lane-satgfx/gfx.bin", "rb").read()
_tc = {}


def tile(k):
    if k not in _tc:
        _tc[k] = satgfx_pack.pens(RAW, (k & 0x3ffff) * 0x80, 16, 16, 8)
    return _tc[k]


def swap(c, mode):
    r, g, b = c >> 16 & 255, c >> 8 & 255, c & 255
    if mode.startswith("hue:"):
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        r, g, b = (int(x * 255) for x in colorsys.hls_to_rgb((h + float(mode[4:]) / 360) % 1, l, s))
    elif mode.startswith("mono:"):
        t = int(mode[5:], 16); l = (0.3 * r + 0.59 * g + 0.11 * b) / 255
        r, g, b = (int(min(255, (t >> s & 255) * l * 1.6)) for s in (16, 8, 0))
    elif mode == "inv":
        r, g, b = 255 - r, 255 - g, 255 - b
    return (r, g, b)


def pose(sig, pals, mode):
    ents = []
    for e in sig.split(";"):
        x, y, code, aw = e.split(",")
        ents.append((int(x), int(y), int(code, 16), int(aw, 16)))
    xs, ys = [], []
    for x, y, code, aw in ents:
        nx, ny = ((aw >> 8) & 15) + 1, ((aw >> 12) & 15) + 1
        xs += [x, x + 16 * nx]; ys += [y, y + 16 * ny]
    x0, y0 = min(xs), min(ys)
    im = Image.new("RGBA", (max(xs) - x0, max(ys) - y0), (0, 0, 0, 0))
    px = im.load()
    for x, y, code, aw in reversed(ents):   # first entry on top
        nx, ny = ((aw >> 8) & 15) + 1, ((aw >> 12) & 15) + 1
        fx, fy = aw & 0x20, aw & 0x40
        pal = pals.get(aw & 0x1f) or [0x808080 + i * 0x080808 for i in range(16)]
        for ty in range(ny):
            for tx in range(nx):
                if fx or fy:
                    t = code + (nx - 1 - tx if fx else tx) + 0x10 * (ny - 1 - ty if fy else ty)
                else:
                    t = (code & ~15) + ((code + tx) & 15) + 0x10 * ty
                p = tile(t)
                for yy in range(16):
                    for xx in range(16):
                        v = p[15 - yy if fy else yy][15 - xx if fx else xx]
                        if v == 15:
                            continue
                        X, Y = x - x0 + tx * 16 + xx, y - y0 + ty * 16 + yy
                        if 0 <= X < im.width and 0 <= Y < im.height:
                            px[X, Y] = swap(pal[v], mode) + (255,)
    return im


def samples(run, kind):
    out, seen = [], set()
    for l in open(f"{run}/samples.tsv"):
        p = l.rstrip("\n").split("\t")
        if p[1] != kind:
            continue
        pals = {}
        for q in p[5].split("|") if len(p) > 5 and p[5] else []:
            n, cs = q.split("=")
            pals[int(n)] = [int(c, 16) for c in cs.split(",")]
        shape = ";".join(",".join(e.split(",")[:3] + [f"{int(e.split(',')[3], 16) & ~0x1f:x}"]) for e in p[4].split(";"))
        if shape in seen:
            continue
        seen.add(shape)
        out.append((p[2], p[3], p[4], pals))
    return out


def sheet(run, kind, outp, mode="none", cols=10, cell=128, limit=200):
    S = samples(run, kind)[:limit]
    rows = (len(S) + cols - 1) // cols or 1
    W = Image.new("RGB", (cols * cell, rows * (cell + 12) + 16), (40, 40, 48))
    d = ImageDraw.Draw(W)
    d.text((4, 2), f"{kind}  {len(S)} sample poses  MAME 0.289 avspu capture  swap={mode}", fill=(255, 255, 255))
    for i, (stg, st, sig, pals) in enumerate(S):
        im = pose(sig, pals, mode)
        if im.width > cell or im.height > cell:
            f = cell / max(im.width, im.height)
            im = im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))))
        cx, cy = (i % cols) * cell, 16 + (i // cols) * (cell + 12)
        W.paste(im, (cx + (cell - im.width) // 2, cy + (cell - im.height)), im)
        d.text((cx + 2, cy + cell), f"s{stg} {st}", fill=(200, 200, 120))
    W.save(outp)
    return len(S)


if __name__ == "__main__":
    print(sheet(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "none"))
