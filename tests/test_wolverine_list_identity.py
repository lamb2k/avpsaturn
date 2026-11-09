"""Synthetic HOST test: the guest's object-list pass is byte-identical with and without the speed switches."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_wolverine_runtime import synthetic_assets

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = [[], ["-DSAT_GUEST_FAST_LIST=1"], ["-DSAT_GUEST_FAST_LIST=1", "-DSAT_GUEST_FOLD=1"],
           ["-DSAT_GUEST_FAST_LIST=1", "-DSAT_GUEST_FOLD=1", "-DSAT_GUEST_NAMES_LAZY=1", "-DSAT_GUEST_PAL_KEEP=1"]]


class WolverineListIdentityTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("gcc"), "gcc is needed for HOST C regressions")
    def test_switches_keep_list_bytes(self):
        asset, boxes = synthetic_assets()
        with tempfile.TemporaryDirectory() as d:
            temp = Path(d)
            (temp / "remap.json").write_text(json.dumps(asset))
            (temp / "boxes.json").write_text(json.dumps(boxes))
            subprocess.run([sys.executable, str(ROOT / "tools/wolverine/gen_c.py"), str(temp), str(temp / "wolverine_data.inc")], check=True)
            outs = []
            for n, flags in enumerate(CONFIGS):
                exe = temp / ("ident%d" % n)
                subprocess.run(["gcc", "-std=gnu99", "-Wall", "-Wextra", "-Werror", "-O2", "-DSAT_GUESTS"] + flags +
                               ["-I" + str(temp), "-I" + str(ROOT / "saturn/rt"), str(ROOT / "tests/wolverine_list_identity_test.c"),
                                "-o", str(exe)], check=True)
                outs.append(subprocess.run([str(exe)], check=True, capture_output=True).stdout)
            self.assertGreater(len(outs[0]), 100000)
            for n in range(1, len(outs)):
                self.assertEqual(outs[0], outs[n], "config %d differs" % n)


if __name__ == "__main__":
    unittest.main()
