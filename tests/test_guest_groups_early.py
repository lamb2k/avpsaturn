"""Synthetic HOST test: SAT_GUEST_GROUPS_EARLY gives the same object list, count and palette as the in-snapshot group loop,
including the stale-stamp cases (no early run, state changed after it, group written after it, setting changed, vblank off by one)."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tools/wolverine"))
from test_wolverine_runtime import synthetic_assets
import hud_art

ROOT = HERE.parent
COMMON = ["-DSAT_GUESTS", "-DSAT_GUEST_GSTAT", "-DSAT_GUEST_FAST_LIST=1", "-DSAT_GUEST_NAMES_LAZY=1", "-DSAT_GUEST_PAL_KEEP=1"]


class GroupsEarlyTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("gcc"), "gcc is needed for HOST C regressions")
    def test_early_equals_in_snapshot(self):
        asset, boxes = synthetic_assets()
        with tempfile.TemporaryDirectory() as d:
            td = Path(d)
            (td / "remap.json").write_text(json.dumps(asset))
            (td / "boxes.json").write_text(json.dumps(boxes))
            subprocess.run([sys.executable, str(ROOT / "tools/wolverine/gen_c.py"), str(td), str(td / "wolverine_data.inc")], check=True)
            (td / "guest_hudpal.inc").write_text(hud_art.pal_include([]))
            rows = ",".join("{" + ",".join("{0,0,0}" for _ in range(5)) + "}" for _ in range(2))
            (td / "guest_files.inc").write_text("#define GUEST_ROWS 2\nstatic const unsigned short guest_file[2][5][3] = {%s};\n" % rows)
            outs = {}
            for early in (0, 1, 2):
                flags = COMMON + ["-DSAT_GUEST_GROUPS_EARLY=%d" % early, "-DSAT_GUEST_GROUPS_TASKS=2", "-DGFRT()=0u", "-I" + str(td), "-I" + str(ROOT / "saturn/rt")]
                wv = td / ("wv%d.o" % early)
                subprocess.run(["gcc", "-std=gnu99", "-Wall", "-Wextra", "-Werror", "-O2", "-c", "-Dsat_guest_objects=sat_guest_wolverine_objects"] + flags +
                               [str(ROOT / "saturn/guests/wolverine/wolverine.c"), "-o", str(wv)], check=True)
                exe = td / ("t%d" % early)
                subprocess.run(["gcc", "-std=gnu99", "-Wall", "-Wextra", "-O2"] + flags +
                               [str(ROOT / "tests/guest_groups_early_test.c"), str(ROOT / "saturn/rt/guests.c"), str(wv), "-o", str(exe)], check=True)
                r = subprocess.run([str(exe)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
                outs[early] = r
            self.assertGreater(len(outs[0].stdout), 200000)
            self.assertEqual(outs[0].stdout, outs[1].stdout, "early build differs from the in-snapshot path")
            self.assertEqual(outs[0].stdout, outs[2].stdout, "check build differs from the in-snapshot path")
            st = dict(zip(outs[1].stderr.split()[0::2], map(int, outs[1].stderr.split()[1::2])))
            self.assertGreater(st["used"], 300)       # the early result was consumed
            self.assertGreater(st["own"], 300)        # and the stale cases fell back
            self.assertGreater(st["special"], 100)    # with shots, flashes or guest bodies among the groups
            st2 = dict(zip(outs[2].stderr.split()[0::2], map(int, outs[2].stderr.split()[1::2])))
            self.assertGreater(st2["used"], 300)
            self.assertEqual(st2["differ"], 0)        # classification made early equals the one made in the snapshot
            print(outs[1].stderr.strip())


if __name__ == "__main__":
    unittest.main()
