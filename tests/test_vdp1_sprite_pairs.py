"""HOST-only pixel and ownership checks for optional vertical sprite pairs.

All input pixels are synthetic. Both sides compile the production driver;
pair count zero supplies the original tile-by-tile reference. This proves
the command transformation against a host raster oracle, not console speed.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "saturn" / "gfx"
HARNESS = ROOT / "tests" / "vdp1_sprite_pairs_test.c"


class SpritePairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="avp-sprite-pairs-")
        cls.directory = Path(cls.temp.name)
        cls.executables = {}
        cls.references = {}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def build(self, fit, pairs, source=None, tag="", reuse=False, extra=()):
        key = (fit, pairs, reuse, tag, tuple(extra))
        if key not in self.executables:
            executable = self.directory / f"pairs-{fit}-{pairs}-reuse{int(reuse)}{tag}"
            args = ["gcc", "-std=c90", "-pedantic", "-Wall", "-Wextra", "-Werror", "-O2",
                    f"-DSAT_GFX_FIT={fit}", f"-DSAT_GFX_SPRITE_PAIRS={pairs}",
                    f"-DSAT_GFX_PAIR_REUSE={int(reuse)}",
                    "-DSAT_GFX_PAIR_STATS", "-I", str(GFX), str(HARNESS), "-o", str(executable)]
            args[1:1] = extra
            if source:
                args.insert(1, f'-DSAT_GFX_SOURCE="{source}"')
            subprocess.run(args, check=True, capture_output=True, text=True)
            self.executables[key] = executable
        return self.executables[key]

    def run_pixels(self, fit, pairs, source=None, tag="", fit_on=1, reuse=False):
        return subprocess.run([str(self.build(fit, pairs, source, tag, reuse=reuse)), "pixels", str(fit_on)],
                              check=True, capture_output=True, text=True)

    def reference(self, fit, fit_on=1):
        key = fit, fit_on
        if key not in self.references:
            self.references[key] = self.run_pixels(fit, 0, fit_on=fit_on)
        return self.references[key]

    def test_pixels_flips_scaling_phases_clipping_wrap_overlap(self):
        for fit in (0, 1, 2, 3):
            for fit_on in ((0, 1) if fit == 3 else (1,)):
                reference = self.reference(fit, fit_on)
                original_commands = int(re.search(r"commands=(\d+)", reference.stderr)[1])
                for pairs in (16, 32):
                    with self.subTest(fit=fit, fit_on=fit_on, pairs=pairs):
                        result = self.run_pixels(fit, pairs, fit_on=fit_on)
                        self.assertEqual(result.stdout, reference.stdout)
                        commands = int(re.search(r"commands=(\d+)", result.stderr)[1])
                        saved = int(re.search(r"saved=(\d+)", result.stderr)[1])
                        self.assertGreater(saved, 0)
                        self.assertEqual(original_commands - commands, saved)
                with self.subTest(fit=fit, fit_on=fit_on, mode="reuse"):
                    result = self.run_pixels(fit, 0, fit_on=fit_on, reuse=True)
                    self.assertEqual(result.stdout, reference.stdout)
                    commands = int(re.search(r"commands=(\d+)", result.stderr)[1])
                    saved = int(re.search(r"saved=(\d+)", result.stderr)[1])
                    self.assertGreater(saved, 0)
                    self.assertEqual(original_commands - commands, saved)
                    self.assertEqual(re.search(r"uploads=(\d+)", result.stderr)[1],
                                     re.search(r"uploads=(\d+)", reference.stderr)[1])

    def test_cache_protects_current_previous_aborted_wrap_reinit_and_pack_swap(self):
        for pairs in (16, 32):
            with self.subTest(pairs=pairs):
                result = subprocess.run([str(self.build(1, pairs)), "cache"],
                                        check=True, capture_output=True, text=True)
                self.assertIn("pair cache ownership ok", result.stdout)

    def test_admission_budget_command_capacity_and_fallback_counts(self):
        for pairs in (16, 32):
            with self.subTest(pairs=pairs):
                result = subprocess.run([str(self.build(1, pairs)), "limits"],
                                        check=True, capture_output=True, text=True)
                self.assertIn("pair admission and command limits ok", result.stdout)

    def test_reuse_saved_answers_both_mirrors_blank_missing_refused_and_late_plot(self):
        for extra in ((), ("-DSAT_VLOG",),
                      ("-DSAT_VLOG", "-DSAT_GFX_SLOT_HINTS=512", "-DSAT_GFX_SLOT_HINT_STATS")):
            executable = self.build(1, 0, reuse=True, extra=extra, tag="-fallbacks" + str(len(extra)))
            result = subprocess.run([str(executable), "reuse"], check=True, capture_output=True, text=True)
            self.assertIn("zero-copy reuse fallbacks and ownership ok", result.stdout)

    def test_pairs_compose_with_validated_slot_hints(self):
        flags = ("-DSAT_GFX_SLOT_HINTS=512", "-DSAT_GFX_SLOT_HINT_STATS")
        for fit, pairs, reuse in ((0, 0, True), (1, 0, True), (1, 32, False)):
            with self.subTest(fit=fit, pairs=pairs, reuse=reuse):
                executable = self.build(fit, pairs, reuse=reuse, extra=flags, tag="-hints")
                result = subprocess.run([str(executable), "pixels", "1"],
                                        check=True, capture_output=True, text=True)
                self.assertEqual(result.stdout, self.reference(fit).stdout)
                # Pairing must still be active when hints are enabled. A bad
                # preprocessor merge can silently select hints instead.
                self.assertGreater(int(re.search(r"saved=(\d+)", result.stderr)[1]), 0)
                plain = self.run_pixels(fit, pairs, reuse=reuse)
                self.assertEqual(result.stderr, plain.stderr)

    def test_reuse_oracle_rejects_noncontiguous_pair(self):
        text = (GFX / "sat_gfx.c").read_text()
        needle = "first != NOSLOT && second == first + 1U"
        self.assertEqual(text.count(needle), 1)
        wrong = self.directory / "wrong_adjacent.c"
        wrong.write_text(text.replace(needle, "first != NOSLOT && second != NOSLOT"))
        executable = self.build(1, 0, source=wrong, reuse=True, tag="-wrong-adjacent")
        result = subprocess.run([str(executable), "reuse"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Assertion", result.stderr)

    def test_census_probe_and_mutually_exclusive_flags_are_rejected(self):
        for pairs, reuse in ((16, False), (0, True)):
            for flag in ("-DSAT_KEYLOG", "-DSAT_READOUT", "-DSAT_ABL=1"):
                with self.subTest(pairs=pairs, reuse=reuse, flag=flag):
                    with self.assertRaises(subprocess.CalledProcessError) as caught:
                        self.build(1, pairs, reuse=reuse, extra=(flag,), tag="-unsupported")
                    self.assertIn("Disable sprite pair experiments", caught.exception.stderr)
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            self.build(1, 16, reuse=True, tag="-both")
        self.assertIn("Select either", caught.exception.stderr)

    def test_pixel_oracle_rejects_wrong_second_payload(self):
        text = (GFX / "sat_gfx.c").read_text()
        needle = "pair_payload((u32)second), 128)"
        self.assertEqual(text.count(needle), 1)
        wrong = self.directory / "wrong_payload.c"
        wrong.write_text(text.replace(needle, "pair_payload((u32)first), 128)"))
        result = self.run_pixels(1, 16, source=wrong, tag="-wrong-payload")
        self.assertNotEqual(result.stdout, self.reference(1).stdout)

    def test_cache_oracle_rejects_lost_previous_plot_guard(self):
        text = (GFX / "sat_gfx.c").read_text()
        needle = "r->stamp == stamp || (prev_stamp && r->stamp == prev_stamp)"
        self.assertEqual(text.count(needle), 1)
        wrong = self.directory / "wrong_guard.c"
        wrong.write_text(text.replace(needle, "r->stamp == stamp"))
        result = subprocess.run([str(self.build(1, 16, source=wrong, tag="-wrong-guard")), "cache"],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Assertion", result.stderr)


if __name__ == "__main__":
    unittest.main()
