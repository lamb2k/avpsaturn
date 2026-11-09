"""Synthetic HOST tests for the actual guest/runtime adapter, with no ROM input."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def synthetic_assets():
    def seq(*steps):
        return [[pose, frames, [0, 0]] for pose, frames in steps]

    moves = {
        "idle": seq((0, 8), (1, 8)),
        "walk": seq((2, 3), (3, 4), (4, 5), (2, 3)),
        "jump": seq((5, 8), (6, 8)),
        "lp": seq((7, 1), (8, 6), (9, 21), (0, 8)),
        "hp": seq((10, 1), (11, 9), (12, 41), (0, 8)),
        "hk": seq((13, 1), (14, 4), (15, 23), (0, 8)),
        "berserker": seq((16, 1), (17, 9), (18, 41), (0, 8)),
        "tornado": seq((19, 1), (20, 9), (21, 50), (0, 8)),
        "knockdown": seq((22, 1), (23, 12)),
        "throw": seq((24, 1), (25, 12)),
        "hit_etc": seq((26, 1), (27, 12)),
        "hit_m": seq((26, 1), (27, 12)),
        "hit_h": seq((26, 1), (27, 12)),
        "crouch": seq((28, 1), (29, 12)),
    }
    asset = {
        "poses": [[[0, 0, n, 0, 0, 0]] for n in range(30)],
        "keys": list(range(100, 130)),
        "moves": moves,
        "moves_one": moves,
        "stance_pose": 0,
        "default_colour": "test",
        "colours": {"test": [[[0, 0, 0]] * 16] * 2},
    }
    boxes = {
        name: [
            {"hit": [2, 8, 0, 8] if k == 1 and name in
             ("lp", "hp", "hk", "berserker", "tornado") else None,
             "hurt": [-4, 4, 0, 16]}
            for k in range(len(steps))
        ]
        for name, steps in moves.items()
    }
    return asset, boxes


class WolverineRuntimeTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("gcc"), "gcc is needed for HOST C regressions")
    def test_production_clock_and_adapter(self):
        asset, boxes = synthetic_assets()
        with tempfile.TemporaryDirectory() as d:
            temp = Path(d)
            (temp / "remap.json").write_text(json.dumps(asset))
            (temp / "boxes.json").write_text(json.dumps(boxes))
            subprocess.run([sys.executable, str(ROOT / "tools/wolverine/gen_c.py"),
                            str(temp), str(temp / "wolverine_data.inc")], check=True)
            for debug, measure, native in ((False, False, False), (True, False, False), (False, True, False), (True, True, False), (False, False, True)):
                exe = temp / ("clock-%s-%s-%s" % (debug, measure, native))
                command = [
                    "gcc", "-std=c90", "-pedantic", "-Wall", "-Wextra", "-Werror", "-O2",
                    "-ffunction-sections", "-fdata-sections", "-DSAT_GUESTS",
                    "-I" + str(temp), "-I" + str(ROOT / "saturn/rt"),
                    str(ROOT / "tests/wolverine_clock_test.c"),
                    str(ROOT / "saturn/game/game_bind.c"), "-Wl,--gc-sections", "-o", str(exe),
                ]
                if native:
                    command.insert(1, "-DSAT_WV_NATIVE_TIMING")
                if debug:
                    command.insert(1, "-DSAT_WOLVERINE_DEBUG")
                if measure:
                    command.insert(1, "-DWV_MEASURE")
                subprocess.run(command, check=True)
                subprocess.run([str(exe)], check=True)


if __name__ == "__main__":
    unittest.main()
