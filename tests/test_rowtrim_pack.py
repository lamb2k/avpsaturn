"""SGP2 row trimmed sprite tiles: pack, plan, assemble, then read them back the way saturn/gfx/sat_gfx.c does (rowtrim_pos, rowtrim_load) and compare with the SGP1 pack.
Synthetic graphics, no ROM."""
import random
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import rounds_pack
import satgfx_pack

PACK = 0x02654000
ROMB = 0x02400000


def gfx(n=600, seed=3):
    """n sprite tiles of 128 bytes (planar, 4 bytes a 8 pixel group): random rows, many rows fully transparent (all four planes set = pen 15)."""
    rnd = random.Random(seed)
    raw = bytearray(0x1000000)
    for k in range(n):
        for row in range(16):
            r = rnd.random()
            for g in range(2):
                o = k * 0x80 + row * 8 + g * 4
                if r < 0.35:
                    raw[o:o + 4] = b"\xff\xff\xff\xff"
                else:
                    raw[o:o + 4] = bytes(rnd.randrange(256) for _ in range(4))
        if k % 17 == 0:   # a duplicate of the tile before
            raw[k * 0x80:(k + 1) * 0x80] = raw[(k - 1) * 0x80:k * 0x80]
        if k % 29 == 0:   # fully blank
            raw[k * 0x80:(k + 1) * 0x80] = b"\xff" * 0x80
    return bytes(raw)


def load(regions):
    mem = {}
    for a, d in regions:
        for i in range(0, len(d), 1):
            pass
        mem[a] = d
    return mem


def read(mem, addr, n):
    for a, d in mem.items():
        if a <= addr and addr + n <= a + len(d):
            return d[addr - a:addr - a + n]
    raise KeyError(hex(addr))


class RowtrimTests(unittest.TestCase):
    def reader(self, regions):
        """The runtime's view: open_pack, then rowtrim_load for a payload index."""
        mem = load(regions)
        main = mem[PACK]
        assert main[:4] == b"SGP2"
        be32 = lambda b, o: struct.unpack_from(">I", b, o)[0]
        sec0 = (be32(main, 4), be32(main, 8), be32(main, 12))
        split, spill = be32(main, 52), be32(main, 56)
        rtbase, rtoffs = be32(main, 84), be32(main, 88)

        def pos(i):
            return be32(main, rtbase + (i >> 10) * 4) + struct.unpack_from(">H", main, rtoffs + i * 2)[0] * 4

        def load_tile(i):
            rec_at = sec0[2] + pos(i)
            src = main
            if i >= split:
                k = be32(main, spill)
                while k > 0:
                    k -= 1
                    first = be32(main, spill + 4 + k * 8)
                    if i >= first:
                        a = (PACK + be32(main, spill + 8 + k * 8) + (pos(i) - pos(first))) & 0xffffffff
                        n = 4 + 8 * bin(struct.unpack(">H", read(mem, a, 2))[0]).count("1")
                        return satgfx_pack.expand(read(mem, a, n))
            n = 4 + 8 * bin(struct.unpack_from(">H", src, rec_at)[0]).count("1")
            return satgfx_pack.expand(src[rec_at:rec_at + n])
        return sec0, load_tile

    def test_every_tile_reads_back_identically_main_and_spill(self):
        raw = gfx()
        keys = [set(range(0, 600)), set(), set(), set()]
        free = [[0x10000, 32768], [0x20000, 3072, True], [0x30000, 32768]]
        # room for 150 tiles of the stream in main so the rest spills
        plain = rounds_pack.plan(raw, keys, rounds_pack.HEAD + 4 + 8 * 3 + 4 * 600 + 150 * 128, free)
        self.assertIsNotNone(plain)
        p = rounds_pack.plan(raw, keys, rounds_pack.HEAD + 4 + 8 * 3 + 4 * 600 + 80 * 128 + 4096, free, rowtrim=True)
        self.assertIsNotNone(p)
        self.assertTrue(p["segs"], "the case must spill")
        self.assertLess(len(p["tile"][0]), len(plain["tile"][0]))
        rom = bytes(0x40000)
        regions = rounds_pack.assemble(p, PACK, rom)
        for a, d in regions:
            self.assertEqual(len(d) % 1, 0)
        sec0, load_tile = self.reader(regions)
        n = len(plain["tile"][0]) // 128
        self.assertEqual(p["n_tiles"], n)
        for i in range(n):
            self.assertEqual(load_tile(i), plain["tile"][0][i * 128:(i + 1) * 128], "payload %d" % i)

    def test_keys_are_unchanged(self):
        raw = gfx()
        keys = [set(range(0, 300)), set(), set(), set()]
        a, _ = satgfx_pack.pack(raw, keys)
        b, _ = satgfx_pack.pack(raw, keys, rowtrim=True)
        ka = struct.unpack_from(">III", a, 4)
        kb = struct.unpack_from(">III", b, 4)
        self.assertEqual(ka[0], kb[0])
        self.assertEqual(a[ka[1]:ka[2]], b[kb[1]:kb[2]])

    def test_spill_regions_are_whole_sectors_padded_with_rom(self):
        raw = gfx()
        keys = [set(range(0, 500)), set(), set(), set()]
        free = [[0x10000, 3072, True], [0x20000, 65536]]
        p = rounds_pack.plan(raw, keys, rounds_pack.HEAD + 4 + 8 * 2 + 4 * 500 + 60 * 128, free, rowtrim=True)
        rom = bytes((i * 5) & 255 for i in range(0x40000))
        regions = rounds_pack.assemble(p, PACK, rom)
        for (a, d), (first, at, take), nb in zip(regions[1:], p["segs"], p["seg_bytes"]):
            self.assertEqual(len(d) % rounds_pack.SEC, 0)
            self.assertEqual(d[nb:], rom[at + nb:at + len(d)])
            self.assertLessEqual(len(d), [r for r in free if r[0] == at][0][1] + 1024)

    def test_sizes_are_smaller_than_plain_and_never_larger_than_a_record_of_16_rows(self):
        raw = gfx()
        keys = [set(range(0, 400)), set(), set(), set()]
        plain, _ = satgfx_pack.pack(raw, keys)
        rt, _ = satgfx_pack.pack(raw, keys, rowtrim=True)
        self.assertLess(len(rt), len(plain))


if __name__ == "__main__":
    unittest.main()
