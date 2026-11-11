"""Select screen name plates fitted to the scaled picture (tools/wolverine/hud_art.py plate_fit, lane frontend 2026-11-11): synthetic HOST tests, no ROM input."""
import pathlib
import random
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools/wolverine"))
import hud_art  # noqa: E402

RAW_SIZE = 0x800000 + 0x2e0000
RGB = [(17 * i, 255 - 17 * i, 17 * (i % 5)) for i in range(15)]


def solid(pen):
    return [[pen] * hud_art.PLATE_W for _ in range(hud_art.PLATE_H)]


def span(row):
    cols = [x for x, p in enumerate(row) if p != 15]
    return (cols[0], cols[-1]) if cols else None


class PlateFit(unittest.TestCase):
    def test_solid_plate_shrinks_11_12_into_place(self):
        for side, (ax0, sx0) in hud_art.PLATE_SIDES.items():
            out = hud_art.plate_fit(solid(4), RGB, side)
            lo, hi = span(out[0])
            # the plate's arcade pixels 0..159 sit at Saturn x ax0 * 11/12 .. (ax0 + 160) * 11/12, relative to the plate's first cell at sx0
            want_lo, want_hi = ax0 * 11 / 12 - sx0, (ax0 + 160) * 11 / 12 - sx0
            self.assertLessEqual(abs(lo - want_lo), 1, side)
            self.assertLessEqual(abs(hi + 1 - want_hi), 1, side)
            self.assertEqual({p for r in out for p in r}, {4, 15})
            self.assertTrue(all(span(r) == (lo, hi) for r in out))

    def test_allowed_pens_only_and_transparent_stays(self):
        rng = random.Random(5)
        pens = [[rng.choice([15, 15, 0, 9, 10, 11, 12, 13]) for _ in range(hud_art.PLATE_W)] for _ in range(hud_art.PLATE_H)]
        out = hud_art.plate_fit(pens, RGB, "R", allowed=[0, 9, 10, 11, 12, 13])
        self.assertTrue({p for r in out for p in r} <= {15, 0, 9, 10, 11, 12, 13})
        empty = hud_art.plate_fit(solid(15), RGB, "L")
        self.assertTrue(all(p == 15 for r in empty for p in r))

    def test_tile_roundtrip_and_only_plate_halves_change(self):
        rng = random.Random(7)
        raw = bytearray(rng.randrange(256) for _ in range(0x800000 + 0x4000 * 4))
        raw = bytes(raw) + bytes(RAW_SIZE - len(raw))
        for name, spec in hud_art.STOCK_PLATES.items():
            pens = hud_art.get_plate(raw, spec["code"])
            self.assertEqual(len(pens), 24)
            fitted = hud_art.plate_fit(pens, RGB, spec["side"])
            out = bytearray(raw)
            hud_art.put_plate(out, spec["code"], fitted)
            self.assertEqual(hud_art.get_plate(bytes(out), spec["code"]), fitted, name)
            touched = {i for i in range(len(raw)) if raw[i] != out[i]}
            allowed = set()
            for r in range(3):
                for c in range(20):
                    base = hud_art.SCROLL_BASE + hud_art.plate_code(spec["code"], r, c) * 0x40
                    par = (1 + c) & 1
                    for y in range(8):
                        allowed.update(range(base + y * 8 + par * 4, base + y * 8 + par * 4 + 4))
            self.assertTrue(touched <= allowed, name)

    def test_plate_keys_are_the_arcades_parity(self):
        keys = hud_art.plate_keys(0x0e30)
        self.assertEqual(len(keys), 60)
        self.assertIn(0x0e30 << 1 | 1, keys)    # first column is arcade column 1: odd half of its code
        self.assertIn(0x0f33 << 1 | 0, keys)    # column 20 (index 19): code 0x0f33, even half
        self.assertEqual(hud_art.plate_code(0x0e30, 2, 19), 0x0f53)


if __name__ == "__main__":
    unittest.main()
