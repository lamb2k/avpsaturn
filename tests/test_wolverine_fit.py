"""Synthetic pack-fit regressions; no ROM, capture, emulator, or SH-2 compiler."""
import contextlib
import importlib.util
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("wolverine_fit", ROOT / "tools/wolverine/fit.py")
fit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fit)


def rounds_fixture(stages=(0x06, 0x1c, 0x1e), masks=(2, 3, 6, 10)):
    files = [dict(name="front", stages=[0], keep_pages=[], keys=[[], [], [], []])]
    table = {}
    for stage in stages:
        # A deliberately closed ROM region makes these tests exercise main-pack
        # capacity, rather than fitting everything into synthetic free ROM pages.
        base = dict(name="stage%02x" % stage, stages=[stage],
                    keep_pages=list(range(0x200000 // 0x400)), keys=[[1, 2], [], [], []])
        row = [len(files)]
        files.append(base)
        for mask in masks:
            row.append(len(files))
            files.append(dict(base, name=base["name"] + "_m%x" % mask))
        table[str(stage)] = row
    return dict(page=0x400, files=files, variant_masks=list(masks), variant_file=table)


def graphics_fixture():
    raw = bytearray(b"\xff" * (128 * 8))
    for key in range(1, 6):
        raw[key * 128] = key   # distinct, nonblank synthetic 4bpp tile payloads
    return bytes(raw)


class WolverineFitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = pathlib.Path(self.temp.name) / "work"
        self.assets = pathlib.Path(self.temp.name) / "assets"
        self.work.mkdir()
        self.assets.mkdir()
        self.rounds = rounds_fixture()
        self.write("rounds.json", self.rounds)
        self.write("round_code_ends.json", [[fit.CART_PACK + 8192, 0]])
        (self.work / "screen_keys.txt").write_text("0 0005\n")
        self.write("key_rank.json", {})
        (self.assets / "remap.json").write_text(json.dumps(dict(
            keys=[3, 4, 5], stage_keys={"06": [3, 4], "1c": [3, 4], "1e": [3, 4]})))
        (self.assets / "gfx_wolverine.bin").write_bytes(graphics_fixture())

    def write(self, name, value):
        (self.work / name).write_text(json.dumps(value))

    def invoke(self, stages="06,1c,1e", **kwargs):
        argv = [str(self.work), str(self.assets)] + ([stages] if stages is not None else [])
        options = dict(environ={}, own_keys={1})
        options.update(kwargs)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return fit.main(argv, **options)

    def test_comma_hex_stages_and_bad_selectors(self):
        self.assertEqual(fit.parse_stages("06,1C,0x1e,06"), [6, 28, 30])
        for selector in ("06,", "00", "060", "06-1e", "xyz"):
            with self.subTest(selector=selector), self.assertRaises(ValueError):
                fit.parse_stages(selector)

    def test_real_packer_all_requested_stages_and_variants_pass(self):
        self.assertEqual(self.invoke(), 0)
        rows = json.loads((self.assets / "fit06_1c_1e.json").read_text())
        self.assertEqual(len(rows), 12)
        self.assertEqual({(r["stage"], r["mask"]) for r in rows},
                         {(stage, mask) for stage in ("06", "1c", "1e") for mask in (2, 3, 6, 10)})
        self.assertTrue(all(r["gate"] and r["wolverine"] == 2 for r in rows))

    def test_missing_requested_stage_fails_and_clears_previous_report(self):
        (self.assets / "fit06_1c_1e.json").write_text('[{"gate": true}]')
        del self.rounds["variant_file"][str(0x1c)]
        self.write("rounds.json", self.rounds)
        self.assertEqual(self.invoke(), 2)
        self.assertEqual(json.loads((self.assets / "fit06_1c_1e.json").read_text()), [])

    def test_missing_variant_cannot_hide_in_a_partial_pass(self):
        self.rounds["variant_file"][str(0x1e)][3] = 0  # wrong fallback to front end
        self.write("rounds.json", self.rounds)
        self.assertEqual(self.invoke(), 2)

    def test_empty_selection_is_an_error(self):
        self.rounds["variant_file"] = {}
        self.rounds["files"] = [self.rounds["files"][0]]
        self.write("rounds.json", self.rounds)
        self.assertEqual(self.invoke(stages=None), 2)

    def test_all_stages_cannot_ignore_a_stage_missing_from_the_variant_table(self):
        del self.rounds["variant_file"][str(0x1c)]
        self.write("rounds.json", self.rounds)
        self.assertEqual(self.invoke(stages=None), 2)

    def test_real_packer_guest_tile_loss_returns_failure(self):
        self.write("round_code_ends.json", [[fit.CART_PACK + 400, 0]])
        self.assertEqual(self.invoke(), 1)
        rows = json.loads((self.assets / "fit06_1c_1e.json").read_text())
        self.assertTrue(all(r["wolv_own_dropped"] > 0 and not r["gate"] for r in rows))

    def test_real_packer_more_arcade_tile_loss_also_fails(self):
        self.write("round_code_ends.json", [[fit.CART_PACK + 528, 0]])
        self.assertEqual(self.invoke(), 1)
        rows = json.loads((self.assets / "fit06_1c_1e.json").read_text())
        self.assertTrue(all(r["wolv_own_dropped"] == 0 and r["wolv_drop"] > r["sch_drop"] for r in rows))

    def test_missing_plan_is_failure_not_an_exception_or_pass(self):
        self.write("round_code_ends.json", [[fit.CART_PACK, 0]])
        self.assertEqual(self.invoke(), 1)
        rows = json.loads((self.assets / "fit06_1c_1e.json").read_text())
        self.assertTrue(all(r["wolv_tiles"] is None and not r["gate"] for r in rows))

    def test_screen_requirement_and_optional_rank_match_build(self):
        (self.work / "screen_keys.txt").unlink()
        self.assertEqual(self.invoke(), 2)
        (self.work / "key_rank.json").unlink()
        self.assertEqual(self.invoke(environ={"SCREEN_KEYS_REQUIRED": "0"}), 0)

    def test_real_packer_keeps_screen_then_guest_then_ordinary_keys(self):
        raw = graphics_fixture()
        base = dict(name="stage06_m2")
        p, dropped = fit.run(raw, base, [{1, 2}, set(), set(), set()], 365,
                             lambda f: [], {"1": 1000}, [{3}, set(), set(), set()], {2})
        self.assertIsNotNone(p)
        self.assertEqual(dropped, [1])

    def test_settings_shared_code_arena_and_minimum_run_exclusions(self):
        rounds = dict(page=0x400, files=[
            dict(name="stage02", keep_pages=[1, 2], stages=[2]),
            dict(name="stage06", keep_pages=[2], stages=[6]),
            dict(name="stage1c", keep_pages=[], stages=[28]),
        ])
        ends = [[fit.ROM_BASE + 4 * 0x400, fit.ROM_BASE + 5 * 0x400], [fit.CART_PACK + 8192, 0]]
        config = fit.settings(dict(ROUND_SHARED_MIN="2", ROUND_MIN_RUN="1", ARENA_KEEP="400-800"))
        runs = fit.free_runs(rounds, ends, **config)(rounds["files"][2])
        pages = {q for start, size in runs for q in range(start // 0x400, (start + size) // 0x400)}
        self.assertTrue({0, 3, 5} <= pages)
        self.assertTrue({1, 2, 4}.isdisjoint(pages))
        no_arena = fit.free_runs(rounds, ends, shared_min=2)(rounds["files"][2])
        self.assertIn([0, 2 * 0x400], no_arena)
        self.assertEqual(fit.free_runs(rounds, ends, min_run=10000)(rounds["files"][2]), [])
        self.assertEqual(runs, sorted(runs, key=lambda r: -r[1]))

    def test_spec_override_is_used(self):
        called = []
        module = types.SimpleNamespace(Data=lambda path: (called.append(path) or types.SimpleNamespace(own={2: {1}})))
        with mock.patch.dict(sys.modules, {"rounds_variants": module}):
            self.assertEqual(self.invoke(environ={"GUEST_SPEC": "synthetic-spec.json"}, own_keys=None), 0)
        self.assertEqual(called, ["synthetic-spec.json"])

    def test_file_specific_graphics_and_rank_are_used(self):
        custom = self.assets / "custom.bin"
        custom.write_bytes(b"synthetic override")
        for f in self.rounds["files"]:
            if "_m" in f["name"]:
                f["gfx"] = str(custom)
        self.write("rounds.json", self.rounds)
        self.write("key_rank.json", {"stage06_m2": {"2": 77}})
        calls = []
        def pack(raw, keys, room, free, rank):
            calls.append((raw, keys, rank))
            return dict(inmain=len(keys[0]), segs=[]), []
        self.assertEqual(self.invoke(fit_fn=pack), 0)
        self.assertTrue(all(call[0] == b"synthetic override" for call in calls))
        self.assertEqual(calls[0][2][2], 77)
        self.assertEqual(calls[1][2][2], 77)
        self.assertEqual(calls[1][2][3], 1 << 39)
        self.assertEqual(calls[1][2][5], 1 << 40)

    def test_command_line_usage_has_nonzero_exit_status(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools/wolverine/fit.py")],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
