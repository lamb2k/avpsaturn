#!/usr/bin/env python
"""Native Wolverine: reading his MSHvSF animation data (shared by gen_native.py and the census tools). ROM-derived input stays under E:/AvP/learning, never in git.

MSHvSF layout (decoded in docs/notes/AVP_WOLVERINE_NATIVE_GFX_20261109.md section 3b, extended 11-09 step 1):
  animation index   27 sub-tables of 16-bit offsets at 0xd1a7e..0xd1c90, separated by zero words. Each sub-table's base is the address of its own first word and an entry is
                    base + s16(word): the first record of a chain (the same scheme as AvP's f_16518). 238 entries.
  frame record      16 bytes (20 with a jump target): +0 u16 flags, +2 u16 duration (bit 15 = jump record), +4 u32 assembly, +8 u32 flags, +12 u32 box-set index.
  assembly          [0002][budget][n][u32 position table], n + 1 parts [code][attr]; position table [0002][x0][y0] then n (dx, dy) byte pairs.
usage as a library: mvlib.MV(dump_dir, assets_dir)"""
import json
import pathlib

import numpy as np

_here = pathlib.Path(__file__).resolve().parent


class MV:
    FEET = 13
    TABLE_LO, TABLE_HI = 0xd1a7e, 0xd1c90

    def __init__(self, dump, assets, K=12, stage="02"):
        import sys
        sys.path.insert(0, str(_here))
        import assets as A
        self.A = A
        dump, assets = pathlib.Path(dump), pathlib.Path(assets)
        self.mv = (dump / "prog_data.bin").read_bytes()
        self.gfx = (dump / "gfx_a000.bin").read_bytes()
        self.remap = json.loads((assets / "remap.json").read_text())
        keyraw = (assets / "gfx_wolverine.bin").read_bytes()
        self.resident = sorted(set(self.remap["stage_keys"][stage]))
        self.K = K
        self.ALPHA = 3
        self.RX = np.stack([np.array(A.pens(keyraw[k * 128:k * 128 + 128]), dtype=np.uint8).reshape(256) for k in self.resident])
        self._kc = {}
        self.stats = {"exact": 0, "near": 0}

    # ---- primitives
    def w(self, a): return int.from_bytes(self.mv[a:a + 2], "big")
    def l(self, a): return int.from_bytes(self.mv[a:a + 4], "big")
    @staticmethod
    def s16(v): return v - 65536 if v >= 32768 else v
    @staticmethod
    def s8(v): return v - 256 if v >= 128 else v

    # ---- the animation index
    def tables(self):
        """[(base, [first-record address ...])] for the 27 sub-tables"""
        subs, cur, a = [], None, self.TABLE_LO
        while a < self.TABLE_HI:
            v = self.w(a)
            if v == 0:
                cur = None
            else:
                if cur is None:
                    cur = [a, []]
                    subs.append(cur)
                cur[1].append(cur[0] + self.s16(v))
            a += 2
        return [(b, t) for b, t in subs]

    def chain(self, a):
        out = []
        while True:
            out.append(a)
            if self.w(a + 2) & 0x8000:
                return out
            a += 16

    def rec(self, a):
        fl = self.w(a + 2)
        return dict(at=a, f0=self.w(a), dur=fl & 0x7fff, jump=self.l(a + 16) if fl & 0x8000 else None, asm=self.l(a + 4), f8=self.l(a + 8), boxset=self.l(a + 12))

    # ---- tiles and poses
    def key_of(self, code):
        """(key, hflip, vflip) of the resident tile within K of the ROM tile, None for a blank tile, "far" when no resident tile is near"""
        if code in self._kc:
            return self._kc[code]
        A = self.A
        px = np.array(A.pens(self.gfx[code * 128:code * 128 + 128]), dtype=np.uint8)
        if (px == 15).all():
            self._kc[code] = None
            return None
        best = None
        for h, v in ((0, 0), (1, 0), (0, 1), (1, 1)):
            q = px[:, ::-1] if h else px
            q = q[::-1, :] if v else q
            u = q.reshape(1, 256)
            d = (((u != self.RX) & (u != 15) & (self.RX != 15)).sum(1) + self.ALPHA * ((u == 15) != (self.RX == 15)).sum(1))
            i = int(d.argmin())
            if best is None or d[i] < best[0]:
                best = (int(d[i]), self.resident[i], h, v)
        self.stats["exact" if best[0] == 0 else "near"] += 1
        self._kc[code] = (best[1], best[2], best[3]) if best[0] <= self.K else "far"
        return self._kc[code]

    def pose(self, rec_addr):
        """(cells, far) of a record's assembly: cells [(x, y, key, hflip, vflip, palette)] relative to his origin; far = ROM cells with no resident tile"""
        ap = self.l(rec_addr + 4)
        n = self.w(ap + 4)
        tab = self.l(ap + 6)
        px, py = self.s16(self.w(tab + 2)), self.s16(self.w(tab + 4))
        cells, far = [], 0
        for i in range(n + 1):
            if i:
                px += self.s8(self.mv[tab + 6 + 2 * (i - 1)])
                py += self.s8(self.mv[tab + 7 + 2 * (i - 1)])
            code, at = self.w(ap + 10 + 4 * i), self.w(ap + 12 + 4 * i)
            wd, ht, hf, vf, pal = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1, (at >> 5) & 1, (at >> 6) & 1, at & 0x1f
            for by in range(ht):
                for bx in range(wd):
                    kk = self.key_of(code + bx + 16 * by)
                    if kk is None:
                        continue
                    if kk == "far":
                        far += 1
                        continue
                    cx = px + 16 * ((wd - 1 - bx) if hf else bx)
                    cy = py + 16 * ((ht - 1 - by) if vf else by)
                    cells.append((cx, cy, kk[0], hf ^ kk[1], vf ^ kk[2], pal))
        return cells, far

    # ---- boxes (rectangles in his frame, forward/up as gen_native.mv_rect: (fwd0, fwd1, up0, up1))
    def rect(self, i):
        b = 0x3a2000 + (i & 0x1fff) * 8
        x, xr, y, yr = self.s16(self.w(b)), self.w(b + 2), self.s16(self.w(b + 4)), self.w(b + 6)
        return (-x - xr, -x + xr, -y - yr + self.FEET, -y + yr + self.FEET)

    def boxes(self, rec_addr):
        e = 0x1ce0f2 + self.l(rec_addr + 12) * 16
        ids = [self.w(e + 2 * k) for k in range(8)]
        hit = next((i for i in ids[:2] if i and not i & 0x8000), None)
        hurt = None
        for i in ids[2:6]:
            if i:
                r = self.rect(i)
                hurt = r if hurt is None else (min(hurt[0], r[0]), max(hurt[1], r[1]), min(hurt[2], r[2]), max(hurt[3], r[3]))
        return (self.rect(hit) if hit else None), hurt
