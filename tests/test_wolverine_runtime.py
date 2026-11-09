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


    @unittest.skipUnless(shutil.which("gcc"), "gcc is needed for HOST C regressions")
    def test_native_patch_warp_fork_and_walk(self):
        """SAT_WV_NATIVE pieces (default off): data patch apply/undo, agreed attack lengths, fork gate, walk weight. Synthetic tables only."""
        asset, boxes = synthetic_assets()
        asset["moves"]["lp"] = [[7, 1, [0, 0]], [8, 6, [0, 0]], [9, 21, [0, 0]], [0, 8, [0, 0]]]
        asset["moves"]["hp"] = [[10, 1, [0, 0]], [11, 9, [0, 0]], [12, 41, [0, 0]], [0, 8, [0, 0]]]
        asset["moves_one"] = asset["moves"]
        for name in ("lp", "hp"):
            boxes[name] = [{"hit": [2, 8, 4, 8] if k == 1 else None, "hurt": [-4, 4, 0, 16]} for k in range(4)]
        with tempfile.TemporaryDirectory() as d:
            temp = Path(d)
            (temp / "remap.json").write_text(json.dumps(asset))
            (temp / "boxes.json").write_text(json.dumps(boxes))
            subprocess.run([sys.executable, str(ROOT / "tools/wolverine/gen_c.py"), str(temp), str(temp / "wolverine_data.inc")], check=True)
            (temp / "wv_patch.inc").write_text(
                "typedef struct { unsigned long addr; unsigned short orig, now; } WvPatch;\n#define WV_PATCHES 2\n"
                "static const WvPatch wv_patch_tab[WV_PATCHES] = {{0x1000, 0x0002, 0x0001}, {0x1100, 0x0006, 0x0004}};\n")
            exe = temp / "native-test"
            subprocess.run(["gcc", "-std=c90", "-pedantic", "-Wall", "-Wextra", "-Werror", "-O2", "-DSAT_WV_NATIVE", "-DWV_HOST_ROM",
                            "-I" + str(temp), "-I" + str(ROOT / "saturn/rt"), str(ROOT / "tests/wolverine_native_test.c"), "-o", str(exe)], check=True)
            r = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("wolverine native test ok", r.stdout)

    def test_forkgen_synthetic(self):
        """forkgen on synthetic lifted text: entry copies, private-callee closure, wrappers, textual identity (no ROM input)."""
        sys.path.insert(0, str(ROOT / "tools/wolverine"))
        import forkgen
        pro = "typedef unsigned int u32;\n#define X 1\n"

        def fn(addr, body):
            return "#define a6 (R->a[6])\nvoid f_%x(void){int fz=0;\n%s\n}\n#undef a6\n" % (addr, body)
        text = pro + "extern void f_1656e(void);\n" + fn(0x24454, "f_1656e();") + fn(0x24f04, "f_1656e();") + fn(0x2539e, "f_252e6();") + fn(0x252e6, "f_1656e();")
        src = {"c4.c": text}
        r = forkgen.build(src, forkgen.SHIP_IDS)
        self.assertEqual(r.wrapped, [0x24454, 0x24f04])
        self.assertEqual(r.copied, [0x24454, 0x24f04])
        self.assertIn("void wvf_24454(void)", r.text)
        self.assertIn("if (sat_wv_fork_on(a6, 0))", r.text)
        self.assertIn("lifted_24454", r.text)
        self.assertEqual(forkgen.check_textual_identity(src, r), [])
        # the jump routine owns its private callee: the clone is closed and calls the copy
        j = forkgen.build(src, (2,))
        self.assertEqual(j.copied, [0x252e6, 0x2539e])
        self.assertIn("wvf_252e6()", j.text)
        self.assertEqual(forkgen.check_textual_identity(src, j), [])


if __name__ == "__main__":
    unittest.main()
