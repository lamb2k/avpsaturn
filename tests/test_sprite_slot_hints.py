"""Actual-driver safety and output identity; synthetic HOST evidence only."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("gcc"), "gcc is required for production-driver checks")
class SpriteSlotHintsTests(unittest.TestCase):
    def build_run(self, directory, name, flags, sources, args=()):
        output = Path(directory) / name
        command = ["gcc", "-std=c90", "-pedantic", "-Wall", "-Wextra", "-Werror", "-O2"]
        command += flags + [str(ROOT / p) for p in sources] + ["-o", str(output)]
        subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
        return subprocess.run([str(output), *args], cwd=ROOT, check=True, capture_output=True, text=True)

    def test_live_slot_validation_eviction_and_abort(self):
        variants = [
            ["-DSAT_GFX_SLOT_HINTS=1", "-DSAT_GFX_FIT=0"],
            ["-DSAT_GFX_SLOT_HINTS=512", "-DSAT_GFX_FIT=1"],
            ["-DSAT_GFX_SLOT_HINTS=1024", "-DSAT_GFX_FIT=1", "-DSAT_VLOG", "-DSAT_VDP1_PROFILE"],
            ["-DSAT_GFX_SLOT_HINTS=64", "-DSAT_GFX_FIT=2", "-DSAT_READOUT"],
        ]
        with tempfile.TemporaryDirectory() as directory:
            for index, flags in enumerate(variants):
                with self.subTest(flags=flags):
                    result = self.build_run(directory, "hints" + str(index),
                                            flags + ["-DSAT_GFX_SLOT_HINT_STATS"],
                                            ["tests/sprite_slot_hints_test.c"])
                    self.assertIn("HOST tests passed", result.stdout)

    def test_presentation_ownership_with_hints(self):
        variants = [[], ["-DSAT_VLOG", "-DSAT_VDP1_PROFILE"],
                    ["-DSAT_VLOG", "-DSAT_VDP1_PROFILE", "-DSAT_READOUT"],
                    ["-DSAT_VLOG", "-DSAT_VDP1_PROFILE", "-DSAT_GFX_PAIR_REUSE=1",
                     "-DSAT_VDP1_HW_ERASE=1"]]
        with tempfile.TemporaryDirectory() as directory:
            for index, flags in enumerate(variants):
                with self.subTest(flags=flags):
                    result = self.build_run(directory, "presentation" + str(index),
                                            flags + ["-DSAT_GFX_SLOT_HINTS=512"],
                                            ["tests/vdp1_presentation_test.c"])
                    self.assertIn("HOST tests passed", result.stdout)

    def test_full_video_memory_identity(self):
        # The existing randomized harness exercises all layers, palette changes,
        # flips, moving/reordered objects, clipping and cache pressure for 600
        # frames. Exact video-memory hashes also catch changed texture placement.
        with tempfile.TemporaryDirectory() as directory:
            for fit in (0, 1):
                flags = ["-DSAT_GFX_HOST", "-DSAT_GFX_FIT=" + str(fit),
                         "-I", str(ROOT / "saturn/gfx")]
                sources = ["tests/host_gfx_layers_identity.c", "saturn/gfx/sat_gfx.c"]
                with self.subTest(fit=fit):
                    baseline = self.build_run(directory, "base" + str(fit), flags, sources)
                    candidate = self.build_run(directory, "candidate" + str(fit),
                                               flags + ["-DSAT_GFX_SLOT_HINTS=512"], sources)
                    self.assertEqual(len(baseline.stdout.splitlines()), 600)
                    self.assertEqual(candidate.stdout, baseline.stdout)


if __name__ == "__main__":
    unittest.main()
