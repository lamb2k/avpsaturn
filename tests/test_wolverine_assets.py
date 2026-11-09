"""Synthetic HOST checks for gameplay residency and generated table bounds."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_wolverine_runtime import ROOT, synthetic_assets


spec = importlib.util.spec_from_file_location("wolverine_reselect", ROOT / "tools/wolverine/reselect.py")
reselect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reselect)


class SelectionTest(unittest.TestCase):
    def fixture(self):
        return {
            "poses": [[[0, 0, i, 0, 0, 0]] for i in range(20)],
            "keys": list(range(100, 120)), "stance_pose": 0,
            "portraits": {"hud": [[0, 0, 0, 0, 0, 0], [16, 0, 19, 0, 0, 0]]},
            "moves": {
                "idle": [[0, 5, []], [1, 1, []], [2, 1, []], [3, 1, []]],
                "walk": [[2, 1, []], [4, 2, []], [5, 1, []], [6, 1, []], [7, 1, []], [4, 2, []]],
            },
        }

    def test_every_emitted_pose_is_resident_without_unused_portrait(self):
        result = reselect.select(self.fixture(), [], hit8=False)
        poses = {step[0] for seq in result["moves_one"].values() for step in seq}
        expected = {result["keys"][tile[2]] for pose in poses for tile in result["poses"][pose]}
        self.assertEqual(expected, set(result["stage_keys"]["06"]))
        self.assertIn(102, expected)  # walk's first pose was an unselected idle pose
        self.assertIn(100, expected)  # shared portrait/body tile still needed
        self.assertNotIn(119, expected)
        self.assertEqual(result["one_set"]["portrait_only_tiles_omitted"], 1)
        self.assertTrue(result["boxes_pending"])

    def test_full_walk_retains_every_pose_and_tick(self):
        source = self.fixture()
        result = reselect.select(source, ["walk"], hit8=False)
        self.assertEqual(result["moves_one"]["walk"], source["moves"]["walk"])
        for name, seq in source["moves"].items():
            self.assertEqual(sum(step[1] for step in seq),
                             sum(step[1] for step in result["moves_one"][name]))

    def test_required_set_cannot_silently_exceed_budget(self):
        with self.assertRaisesRegex(ValueError, "exceeding BUDGET"):
            reselect.select(self.fixture(), ["walk"], budget=1)
        with self.assertRaisesRegex(ValueError, "positive"):
            reselect.select(self.fixture(), ["walk/0"])

    def test_reselection_refreshes_graphics_and_keeps_old_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory) / "source", Path(directory) / "target"
            source.mkdir(); target.mkdir()
            (source / "remap.json").write_text(json.dumps(self.fixture()))
            (source / "gfx_wolverine.bin").write_bytes(b"synthetic-new")
            (target / "gfx_wolverine.bin").write_bytes(b"stale")
            (target / "boxes.json").write_text('{"old": []}')
            self.assertEqual(reselect.main([str(source), str(target), "walk"]), 0)
            self.assertEqual((target / "gfx_wolverine.bin").read_bytes(), b"synthetic-new")
            self.assertEqual((target / "boxes.json").read_text(), '{"old": []}')
            self.assertTrue(json.loads((target / "remap.json").read_text())["boxes_pending"])


class GeneratorTest(unittest.TestCase):
    def generate(self, asset, boxes):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            (temporary / "remap.json").write_text(json.dumps(asset))
            (temporary / "boxes.json").write_text(json.dumps(boxes))
            result = subprocess.run([sys.executable, str(ROOT / "tools/wolverine/gen_c.py"),
                                     str(temporary), str(temporary / "data.inc")],
                                    capture_output=True, text=True)
            return result, (temporary / "data.inc").exists()

    def test_rejects_stale_boxes_before_writing_output(self):
        asset, boxes = synthetic_assets()
        asset["boxes_pending"] = True
        result, written = self.generate(asset, boxes)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("regenerate boxes.json", result.stderr)
        self.assertFalse(written)
        asset.pop("boxes_pending")
        boxes["hp"].pop()
        result, written = self.generate(asset, boxes)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stale box steps", result.stderr)
        self.assertFalse(written)

    def test_rejects_silent_clock_and_index_truncation(self):
        original, boxes = synthetic_assets()
        for change, message in (
                (lambda a: a["moves_one"]["hp"][0].__setitem__(1, 256), "1..255"),
                (lambda a: a["moves_one"].__setitem__("hp", [[10, 1, []]] * 257), "step count"),
                (lambda a: a.__setitem__("stance_pose", 90), "ready stance"),
                (lambda a: a.__setitem__("stage_keys", {"06": [100]}), "emitted-pose tiles")):
            asset = copy.deepcopy(original)
            change(asset)
            result, written = self.generate(asset, boxes)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(message, result.stderr)
            self.assertFalse(written)


if __name__ == "__main__":
    unittest.main()
