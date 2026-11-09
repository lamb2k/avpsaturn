"""Synthetic host regressions: no ROM, console or private asset inputs."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "saturn/rt"))
import round_cache


def build_function(name, namespace):
    """Execute an actual build helper without invoking its private toolchain setup."""
    source = ROOT / "saturn/rt/build.py"
    tree = ast.parse(source.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), namespace)
    return namespace[name]


class RoundCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.disc = self.root / "disc"
        self.disc.mkdir()
        self.names = round_cache.round_names(2)
        for i, name in enumerate(self.names):
            (self.disc / name).write_bytes(bytes([i + 1]) * 2048)
        self.gfx = self.root / "gfx.bin"
        self.gfx.write_bytes(b"synthetic graphics")
        self.audio = self.root / "audio.bin"
        self.audio.write_bytes(b"synthetic sound")
        self.receipt = self.root / "receipt.json"
        self.plan = {"files": [{"guest_keys": [1, 2], "keys": [[1, 2], [], [], []]}]}
        self.layout = [[0x2400000, 0x2401000], [0x27e0000, 0]]
        self.controls = {"shared_min": 10, "min_run": 1, "screen_keys": [[9], [], [], []]}
        self.sources = {"gfx": self.gfx, "audio": self.audio, "rank": None}

    def fingerprint(self):
        return round_cache.packing_inputs(self.plan, self.layout, self.controls, self.sources)

    def record(self):
        fingerprint = self.fingerprint()
        round_cache.save_receipt(self.receipt, fingerprint, self.disc, self.names)
        return fingerprint

    def reason(self, fingerprint):
        return round_cache.reuse_reason(self.receipt, fingerprint, self.disc, self.names)

    def test_missing_and_invalid_receipts_cannot_reuse(self):
        self.assertIsNotNone(self.reason(self.fingerprint()))
        for text in ("broken", "null", "[]", '{"version": 999}'):
            self.receipt.write_text(text)
            self.assertIsNotNone(self.reason(self.fingerprint()))

    def test_exact_inputs_and_files_reuse(self):
        self.assertIsNone(self.reason(self.record()))

    def test_reselected_pose_invalidates_even_with_unchanged_layout(self):
        old = self.record()
        self.plan["files"][0]["guest_keys"].append(3)
        self.assertNotEqual(old, self.fingerprint())
        self.assertIsNotNone(self.reason(self.fingerprint()))

    def test_graphics_and_audio_bytes_each_invalidate(self):
        for source in (self.gfx, self.audio):
            old = self.record()
            source.write_bytes(source.read_bytes() + b" changed")
            self.assertNotEqual(old, self.fingerprint())
            self.assertIsNotNone(self.reason(self.fingerprint()))

    def test_controls_layout_rank_and_packer_source_invalidate(self):
        old = self.fingerprint()
        self.controls["screen_keys"][0].append(10)
        self.assertNotEqual(old, self.fingerprint())
        old = self.fingerprint()
        self.controls["arena_keep"] = "all"
        self.assertNotEqual(old, self.fingerprint())
        old = self.fingerprint()
        self.layout[-1][0] -= 4096
        self.assertNotEqual(old, self.fingerprint())
        for label in ("rank", "packer"):
            old = self.fingerprint()
            path = self.root / label
            path.write_text("version 1")
            self.sources[label] = path
            self.assertNotEqual(old, self.fingerprint())
            old = self.fingerprint()
            path.write_text("version 2")
            self.assertNotEqual(old, self.fingerprint())

    def test_required_source_absence_fails(self):
        self.gfx.unlink()
        with self.assertRaises(FileNotFoundError):
            self.fingerprint()

    def test_corrupt_missing_and_surplus_rounds_are_rejected(self):
        old = self.record()
        target = self.disc / self.names[0]
        target.write_bytes(b"foreign round")
        self.assertIsNotNone(self.reason(old))
        target.unlink()
        self.assertIsNotNone(self.reason(old))
        target.write_bytes(b"new round")
        old = self.record()
        extra = self.disc / "R002.BIN"
        extra.write_bytes(b"old larger build")
        self.assertEqual(round_cache.extra_rounds(self.disc, self.names), [extra])
        self.assertIsNotNone(self.reason(old))

    def test_relinked_rom_restores_refresh_without_changing_sprite_payload(self):
        # The real helper must refresh only ROM restores, not the later sprite
        # spill at another ROM address. Both regions deliberately fit the ROM.
        cart = {"ROMB": 0x2400000, "SAT_PACK": 0x2654000}
        regions = [(cart["SAT_PACK"], b"A" * 2048), (1, b""),
                   (cart["ROMB"], b"R" * 2048),
                   (cart["SAT_PACK"], b"P" * 2048),
                   (cart["ROMB"] + 2048, b"S" * 2048)]
        head = struct.pack(">I", len(regions)) + b"".join(
            struct.pack(">II", at, len(data)) for at, data in regions)
        payload = head.ljust(2048, b"\0") + b"".join(data for _, data in regions)
        (self.disc / self.names[0]).write_bytes(payload)
        old = self.record()
        self.assertIsNone(self.reason(old))
        refresh = build_function("refresh_restores", {"ISO": self.disc, "CART": cart})
        # The second file is also a valid empty-region round in this fixture.
        (self.disc / self.names[1]).write_bytes(bytes(2048))
        self.record()
        self.assertEqual(refresh(bytearray(b"N" * 4096)), 1)
        result = (self.disc / self.names[0]).read_bytes()
        self.assertEqual(result[4096:6144], b"N" * 2048)
        self.assertEqual(result[6144:8192], b"P" * 2048)
        self.assertEqual(result[8192:10240], b"S" * 2048)
        self.assertEqual(old, self.fingerprint())
        self.assertIsNotNone(self.reason(old))
        self.assertIsNone(self.reason(self.record()))

    def test_required_guest_keys_cannot_be_dropped_or_absent(self):
        round_cache.require_guest_tiles("stage06_wv", [1, 2], [1, 2, 3], [3], {})
        for required, candidates, dropped, plan in (
            ([1, 2], [1, 2], [2], {}), ([1, 2], [1], [], {}), ([], [], [], None)):
            with self.assertRaises(ValueError):
                round_cache.require_guest_tiles("stage1c_wv", required, candidates, dropped, plan)

    def test_actual_round_planner_refuses_before_any_output_write(self):
        import re
        calls = []
        fake = types.SimpleNamespace()
        def fit(raw, keys, room, free, rank):
            return {"segs": []}, [99] if 99 in keys[0] else []
        fake.fit = fit
        fake.write_file = lambda *args: calls.append(args)
        base = dict(name="stage02", keep_pages=[], keys=[[1], [], [], []], stages=[2])
        guest = dict(name="stage1e_m2_wv", keep_pages=[], keys=[[99], [], [], []],
                     stages=[0x1e], guest_keys=[99])
        namespace = dict(sys=sys, pathlib=__import__("pathlib"), os=os, json=json,
                         re=re, REPO=ROOT, WORK=self.root, ISO=self.disc,
                         ROUNDS={"page": 0x200000, "files": [base, guest]},
                         CART={"ROMB": 0x2400000, "SAT_PACK": 0x2654000},
                         SHARED_MIN=10, MIN_RUN=1, SCREEN_KEYS=[set()] * 4,
                         POSE_KEYS=set(), POSE_RANK=400, FUZZ_STAGE={},
                         EDGE_KEYS=set(), CAPTION_KEYS=set(), SELECT_DIGIT_KEYS=set(),
                         round_cache=round_cache)
        planner = build_function("round_files", namespace)
        with patch.dict(sys.modules, {"rounds_pack": fake}), patch.dict(
                os.environ, {"GFX_BIN": str(self.gfx)}, clear=True):
            with self.assertRaisesRegex(ValueError, "required guest tiles"):
                planner(bytearray(0x200000), [], 0x27e0000)
        self.assertEqual(calls, [])

    def test_remap_collision_in_unselected_extraction_is_rejected(self):
        round_cache.require_unused_remap("guest", [100, 101], [1, 2])
        with self.assertRaisesRegex(ValueError, "regenerate guest assets"):
            round_cache.require_unused_remap("guest", [100, 101], [1, 101])

    def test_store_directory_boundary_matches_real_packer(self):
        spec = importlib.util.spec_from_file_location("sector_store", ROOT / "tools/sector_store.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for count, expected in ((1, 1), (255, 1), (256, 2), (511, 2)):
            self.assertEqual(round_cache.store_header_sectors(count), expected)
            files = [bytes([i & 255]) * 2048 for i in range(count)]
            store, _ = module.build(files)
            self.assertEqual(module.rebuild(store, count - 1), files[-1])
            first, _ = struct.unpack_from(">II", store, 8 + 8 * (count - 1))
            word = struct.unpack_from(">I", store, expected * 2048 + 4 * first)[0]
            self.assertGreaterEqual(word >> 14, expected)
        for count in (0, 512):
            with self.assertRaises(ValueError):
                round_cache.store_header_sectors(count)


if __name__ == "__main__":
    unittest.main()
