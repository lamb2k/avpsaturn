#!/usr/bin/env python
"""Lane satgfx host reference: rebuild a CPS2 picture from a scene dump, to fix semantics against the MAME still before any SH-2.
Reads only what sat_gfx_frame reads. Tier HOST. usage: satgfx_ref.py SCENE.bin GFX.bin OUTDIR [IRQ,IRQ]"""
import struct, sys, pathlib
import numpy as np
from PIL import Image
REC = 8 + 0x10000 + 0x2000 * 2 + 0x30000 + 0x40 + 0x40 + 0x10
def scenes(p):
    d = pathlib.Path(p).read_bytes()
    for o in range(0, len(d), REC):
        yield Scene(d[o:o + REC])
class Scene:
    def __init__(s, b):
        s.irq = struct.unpack(">I", b[4:8])[0]; o = 8
        s.ram = b[o:o + 0x10000]; o += 0x10000
        s.obj0 = b[o:o + 0x2000]; o += 0x2000
        s.obj8 = b[o:o + 0x2000]; o += 0x2000
        s.gfx = b[o:o + 0x30000]; o += 0x30000
        s.a = b[o:o + 0x40]; o += 0x40
        s.b = b[o:o + 0x40]; o += 0x40
        s.out = b[o:o + 0x10]
    def r(s, a): return struct.unpack(">H", s.ram[a - 0xff0000:a - 0xff0000 + 2])[0]
def be(b, o): return (b[o] << 8) | b[o + 1]
class Gfx:
    def __init__(s, p):
        raw = np.frombuffer(pathlib.Path(p).read_bytes(), dtype=np.uint8)
        s.raw = raw; s.n = len(raw); s.c = {}
    def row(s, off, n):  # n pixels from byte offset; plane bits 24,16,8,0 in each little 32-bit group as MAME's layout
        r = np.zeros(n, int)
        for x in range(n):
            bo = off + (x // 8) * 4
            px = 7 - (x % 8)
            v = 0
            for pl, shift in enumerate((3, 2, 1, 0)):
                v |= ((int(s.raw[(bo + shift) % s.n]) >> px) & 1) << (3 - pl)
            r[x] = v
        return r
    def tile(s, off, w, h, stride):
        k = (off, w, h)
        if k in s.c: return s.c[k]
        s.c[k] = r = np.array([s.row(off + y * stride, w) for y in range(h)])
        return r
def pal(sc, page, bank, base):
    return [be(sc.gfx, base + (page * 0x200 + bank * 16 + i) * 2) for i in range(16)]
def rgb(c):
    br = 0x0f + ((c >> 12) << 1)
    return (((c >> 8) & 15) * 0x11 * br // 0x2d, ((c >> 4) & 15) * 0x11 * br // 0x2d, (c & 15) * 0x11 * br // 0x2d)
def render(sc, gx, buf_obj):
    F = 0xff8000
    bases = [sc.r(F + 0x24), sc.r(F + 0x26), sc.r(F + 0x28)]
    pbase = sc.r(F + 0x2c)
    ctrl = sc.r(F + 0x4a); prictl = sc.r(F + 0x50)
    sx = [sc.r(0xffee1a), sc.r(0xffee1e), sc.r(0xffee22)]; sy = [sc.r(0xffee1c), sc.r(0xffee20), sc.r(0xffee24)]
    pctl = sc.r(F + 0x4c)
    gbase = pbase * 0x100 - 0x900000
    # map skipped pages
    pages = {}; p = 0
    for pg in range(6):
        if pctl >> pg & 1: pages[pg] = p; p += 1
        elif p: p += 1
    W, H = 384, 224
    im = np.zeros((H, W, 3), np.uint8)
    def color(page, bank, pen):
        if page not in pages: return (0, 0, 0)
        return rgb(be(sc.gfx, gbase + ((pages[page] * 0x200 + bank * 16 + pen) * 2)))
    bg = color(5, 31, 15)
    im[:] = bg
    order = [(ctrl >> s) & 3 for s in (6, 8, 10, 12)]
    pr = {l: (prictl >> (4 * l)) & 15 for l in range(4)}
    layers = [l for l in order if l]
    enable = {1: ctrl & 2, 2: ctrl & 4, 3: ctrl & 8}
    pri = np.zeros((H, W), np.uint8)
    for li, l in enumerate(layers):
        if not enable.get(l): continue
        ts = {1: 8, 2: 16, 3: 32}[l]
        g = (bases[l - 1] & 0xffc0) * 0x100 - 0x900000
        for row in range(H // ts + 2):
            for col in range(W // ts + 2):
                wx = col * ts + sx[l - 1] + 64; wy = row * ts + sy[l - 1] + 16
                c = (wx // ts) & 63; r = (wy // ts) & 63
                if l == 1: idx = (r & 0x1f) + (c << 5) + ((r & 0x20) << 6)
                elif l == 2: idx = (r & 0x0f) + (c << 4) + ((r & 0x30) << 6)
                else: idx = (r & 7) + (c << 3) + ((r & 0x38) << 6)
                code = be(sc.gfx, g + idx * 4); attr = be(sc.gfx, g + idx * 4 + 2)
                if l == 3: code &= 0x3fff
                if l == 1: t = gx.tile(0x800000 + code * 0x40, 16, 8, 8)[:, 8:16] if idx & 32 else gx.tile(0x800000 + code * 0x40, 8, 8, 8)
                elif l == 2: t = gx.tile(0x800000 + code * 0x80, 16, 16, 8)
                else: t = gx.tile(0x800000 + code * 0x200, 32, 32, 16)
                if attr & 0x20: t = t[:, ::-1]
                if attr & 0x40: t = t[::-1]
                x0 = col * ts - ((sx[l - 1] + 64) % ts); y0 = row * ts - ((sy[l - 1] + 16) % ts)
                for y in range(ts):
                    Y = y0 + y
                    if not 0 <= Y < H: continue
                    for x in range(ts):
                        X = x0 + x
                        if 0 <= X < W and t[y, x] != 15:
                            im[Y, X] = color(l, attr & 31, t[y, x]); pri[Y, X] = 1 << li
    # sprites
    ob = buf_obj
    xo = be(sc.out, 8) ; yo = be(sc.out, 10)
    n = 0
    while n < 0x400 and not (be(ob, n * 8 + 2) >= 0x8000 or be(ob, n * 8 + 6) >= 0xff00): n += 1
    lp = [pr[l] for l in layers]
    done = np.zeros((H, W), bool)
    def visible(p, Y, X):
        li = pri[Y, X]
        if li == 0: return True
        k = {1: 0, 2: 1, 4: 2}[li]
        return p > lp[k]
    for i in range(n - 1, -1, -1):  # MAME draws from the end and the first pixel down keeps its place
        o = i * 8
        x = be(ob, o); y = be(ob, o + 2); code = be(ob, o + 4); a = be(ob, o + 6)
        p = x >> 13
        code += (y & 0x6000) << 3
        fx = bool(a & 0x20); fy = bool(a & 0x40); col = a & 31
        if a & 0x80: x += xo; y += yo
        nx = (a >> 8 & 15) + 1; ny = (a >> 12 & 15) + 1
        for ty in range(ny):
            for tx in range(nx):
                if fx or fy:
                    sxx = nx - 1 - tx if fx else tx; syy = ny - 1 - ty if fy else ty
                    c = code + sxx + 0x10 * syy
                else:
                    c = (code & ~15) + ((code + tx) & 15) + 0x10 * ty
                t = gx.tile((c & 0x3ffff) * 0x80, 16, 16, 8)
                if fx: t = t[:, ::-1]
                if fy: t = t[::-1]
                X0 = ((x + tx * 16 + 64 - xo) & 0x3ff) - 64; Y0 = ((y + ty * 16 + 16 - yo) & 0x3ff) - 16
                for yy in range(16):
                    Y = Y0 + yy
                    if not 0 <= Y < H: continue
                    for xx in range(16):
                        X = X0 + xx
                        if 0 <= X < W and t[yy, xx] != 15 and not done[Y, X]:
                            done[Y, X] = True
                            if visible(p, Y, X): im[Y, X] = color(0, col, t[yy, xx])
    return im, n
if __name__ == "__main__":
    gx = Gfx(sys.argv[2]); out = pathlib.Path(sys.argv[3]); out.mkdir(exist_ok=True, parents=True)
    only = set(int(x) for x in sys.argv[4].split(",")) if len(sys.argv) > 4 else None
    for sc in scenes(sys.argv[1]):
        if only and sc.irq not in only: continue
        for nm, ob in (("o8", sc.obj8), ("o0", sc.obj0)):
            im, n = render(sc, gx, ob)
            Image.fromarray(im).save(out / f"r{sc.irq:05d}_{nm}.png")
            print(sc.irq, nm, "objs", n, "base", hex(be(sc.out, 0)), "pri", hex(sc.r(0xff8050)), "ctl", hex(sc.r(0xff804a)), "pal", hex(sc.r(0xff802c)), hex(sc.r(0xff804c)))
