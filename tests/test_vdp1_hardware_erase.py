"""Compile/run the real renderer's erase tests. Evidence tier: HOST only."""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class HardwareEraseTests(unittest.TestCase):
    def test_strict_production_driver_configurations(self):
        configurations = (
            ("fit1", []),
            ("fit0", ["-DSAT_GFX_FIT=0"]),
            ("diagnostics", ["-DSAT_GFX_FIT=2", "-DSAT_VDP1_PROFILE",
                             "-DSAT_VLOG", "-DSAT_READOUT"]),
            ("reuse_hints", ["-DSAT_GFX_PAIR_REUSE=1", "-DSAT_GFX_SLOT_HINTS=512",
                             "-DSAT_VDP1_PROFILE", "-DSAT_VLOG"]),
        )
        with tempfile.TemporaryDirectory(prefix="vdp1-erase-host-") as tmp:
            for name, flags in configurations:
                with self.subTest(configuration=name):
                    binary = Path(tmp) / name
                    command = ["gcc", "-std=c90", "-pedantic", "-Wall",
                               "-Wextra", "-Werror", "-O2", *flags,
                               str(ROOT / "tests/vdp1_hardware_erase_test.c"),
                               "-o", str(binary)]
                    compiled = subprocess.run(command, text=True,
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.STDOUT)
                    self.assertEqual(compiled.returncode, 0, compiled.stdout)
                    ran = subprocess.run([str(binary)], text=True,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT)
                    self.assertEqual(ran.returncode, 0, ran.stdout)
                    self.assertIn("HOST coverage tests passed", ran.stdout)


if __name__ == "__main__":
    unittest.main()
