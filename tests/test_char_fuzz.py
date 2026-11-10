"""Synthetic host regressions for the fuzz census inputs and the spill tail fill: no ROM, console or private asset inputs."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import char_fuzz
import rounds_pack

PAGE = 0x400


def rounds():
    mk = lambda name, st, **kw: dict(name=name, stages=[st], keep_pages=[10], keys=[[1, 2], [], [], []], **kw)
    return dict(page=PAGE, files=[mk("front", 0), mk("stage02", 2), mk("stage04", 4), mk("stage04_m1", 4, mask=1), mk("stage04_m2_wv", 4, mask=2)])


def data():
    return dict(version=1, page=PAGE, palette={}, pages={"00": [100], "02": [20], "04": [30]}, player_script_pages=[50],
                chars={"1": dict(runs=[], stage_keys={"04": [5, 6, 77]}, body_keys=[8, 77]),
                       "2": dict(runs=[], stage_keys={"04": [9]}, body_keys=[11])})


class AugmentTests(unittest.TestCase):
    def test_pages_cover_own_front_and_next_stage_with_a_page_either_side(self):
        r = rounds()
        rep = char_fuzz.augment(r, data(), pages=True)
        f = {x["name"]: x for x in r["files"]}
        lo, hi = char_fuzz.SCRIPT_REGION[0] // PAGE, (char_fuzz.SCRIPT_REGION[1] + PAGE - 1) // PAGE
        region = set(range(lo - 1, hi + 1))   # the script stretch with a page either side
        for x in f.values():
            self.assertTrue(region <= set(x["keep_pages"]))
            x["keep_pages"] = sorted(set(x["keep_pages"]) - region)
        self.assertEqual(f["stage02"]["keep_pages"], sorted({10, 99, 100, 101, 19, 20, 21, 29, 30, 31, 49, 50, 51}))   # own 02, front 00, next stage 04, player scripts
        self.assertEqual(f["stage04"]["keep_pages"], sorted({10, 99, 100, 101, 29, 30, 31, 49, 50, 51}))
        self.assertEqual(f["front"]["keep_pages"], sorted({10, 99, 100, 101, 19, 20, 21, 29, 30, 31, 49, 50, 51}))
        self.assertGreater(rep["pages_added"], 0)
        self.assertEqual(f["stage04"]["keys"][0], [1, 2])   # keys off by default

    def test_keys_follow_the_mask_and_leave_remap_keys_out(self):
        r = rounds()
        rep = char_fuzz.augment(r, data(), keys=True, pages=False, remap={77})
        f = {x["name"]: x for x in r["files"]}
        self.assertEqual(f["stage04_m1"]["keys"][0], [1, 2, 5, 6, 8, 9, 11])   # every variant asks for every character's keys; the ranks tell them apart
        self.assertEqual(f["stage04_m1"]["fuzz_keys"], [5, 6])
        self.assertEqual(f["stage04_m1"]["body_keys"], [8])
        self.assertEqual(f["stage04_m2_wv"]["keys"][0], [1, 2, 5, 6, 8, 9, 11])
        self.assertEqual(f["stage04_m2_wv"]["fuzz_keys"], [9])
        self.assertEqual(f["stage04"]["keys"][0], [1, 2, 5, 6, 8, 9, 11])   # the file for three or four players asks for every character
        self.assertEqual(f["front"]["keys"][0], [1, 2])
        self.assertNotIn("fuzz_keys", f["front"])
        self.assertEqual(f["stage04"]["keep_pages"], [10])
        self.assertEqual(rep["files"], 4)

    def test_keys_only_in_the_listed_stages(self):
        r = rounds()
        char_fuzz.augment(r, data(), keys=True, pages=False, key_stages={2})
        f = {x["name"]: x for x in r["files"]}
        self.assertEqual(f["stage04_m1"]["keys"][0], [1, 2])
        self.assertNotIn("fuzz_keys", f["stage04"])

    def test_rank_raises_never_lowers(self):
        v = dict(mask=1, fuzz_keys=[5], body_keys=[8])
        self.assertEqual(char_fuzz.rank(v, {5: 10, 8: 10 ** 9, 9: 3}), {5: char_fuzz.RANK_FUZZ_VARIANT, 8: 10 ** 9, 9: 3})
        b = dict(fuzz_keys=[5], body_keys=[8])
        self.assertEqual(char_fuzz.rank(b, {}), {5: char_fuzz.RANK_FUZZ_BASE, 8: char_fuzz.RANK_BODY_BASE})

    def test_no_data_changes_nothing(self):
        r = rounds()
        before = json.dumps(r)
        self.assertEqual(char_fuzz.augment(r, None, keys=True, pages=False)["files"], 0)
        self.assertEqual(json.dumps(r), before)

    def test_script_stretch_is_kept_without_a_census(self):
        r = rounds()
        char_fuzz.augment(r, None)
        lo, hi = char_fuzz.SCRIPT_REGION[0] // PAGE, (char_fuzz.SCRIPT_REGION[1] + PAGE - 1) // PAGE
        for f in r["files"]:
            self.assertTrue(set(range(lo, hi)) <= set(f["keep_pages"]), f["name"])
        self.assertIn(0x171400 // PAGE, r["files"][1]["keep_pages"])

    def test_build_reads_a_run_directory(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "run"
            d.mkdir()
            (d / "s04.txt").write_text("frames 5\n0 0\n0 1f\n1 33\nr 7800\nr 7802\no 12\nm 4\n")
            (d / "fuzz_pal.txt").write_text("0 1f\n3 20\n0 21\n")
            out = char_fuzz.build(t, {1: [d]})
            self.assertEqual(out["chars"]["1"]["stage_keys"], {"04": [0x1f]})
            self.assertEqual(out["chars"]["1"]["body_keys"], [0x1f, 0x21])
            self.assertEqual(out["pages"], {"04": [0x7800 // PAGE]})
            self.assertEqual(char_fuzz.load(t)["chars"]["1"]["body_keys"], [0x1f, 0x21])


class TailFillTests(unittest.TestCase):
    def plan(self, free, tiles):
        """rounds_pack.plan on a stub packer: `tiles` sprite payloads of 128 bytes and empty scroll sections."""
        off = 4 + 12 * 4 + 8 * 4
        body = bytes(range(256)) * (tiles // 2)

        def fake(raw, keys, rowtrim=False):
            hdr = struct.pack(">I", 0x53475031) + struct.pack(">III", tiles, off, off)
            for _ in range(3):
                hdr += struct.pack(">III", 0, off + len(body), off + len(body))
            hdr += struct.pack(">II", 0xffffffff, 0) * 4
            return hdr + body, []
        real = rounds_pack.satgfx_pack.pack
        rounds_pack.satgfx_pack.pack = fake
        try:   # room for four tiles in main and one stretch table row
            return rounds_pack.plan(b"", [set(), set(), set(), set()], rounds_pack.HEAD + 4 + 8 + 4 * 128, free)
        finally:
            rounds_pack.satgfx_pack.pack = real

    def test_odd_run_with_a_kept_page_after_it_is_used_whole(self):
        # 28 tiles: 4 in main, 24 in a run of three pages (3072 bytes). Whole sectors hold 16; with the kept page after the run all 24 fit.
        self.assertIsNone(self.plan([[0x10000, 3072]], 28))
        filled = self.plan([[0x10000, 3072, True]], 28)
        self.assertEqual(sum(x[2] for x in filled["segs"]), 24)

    def test_assemble_pads_with_the_roms_bytes(self):
        rom = bytes((i * 7) & 255 for i in range(0x40000))
        p = dict(key=[b""] * 4, tile=[bytes(range(256)) * 12, b"", b"", b""], secs=[(0, 0, 0)] * 4, inmain=0, segs=[(0, 0x10000, 24)])
        regions = rounds_pack.assemble(p, 0x2654000, rom)
        a, d = regions[1]
        self.assertEqual(a, rounds_pack.ROMB + 0x10000)
        self.assertEqual(len(d) % rounds_pack.SEC, 0)
        self.assertEqual(d[:3072], bytes(range(256)) * 12)
        self.assertEqual(d[3072:], rom[0x10000 + 3072:0x10000 + 4096])
        zero = rounds_pack.assemble(p, 0x2654000)[1][1]
        self.assertEqual(len(zero), 3072)   # unpadded here; write_file pads it with zeros as before


if __name__ == "__main__":
    unittest.main()
