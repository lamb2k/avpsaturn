"""HOST synthetic tests; no Saturn timing or hardware-fit claim."""
import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cpu_slack_profile", ROOT / "tools/cpu_slack_profile.py")
profile = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(profile)


def row(vblank, flags=profile.FINISHED | profile.HANDED, done=2000, period=3500):
    return dict(zip(profile.FIELDS, (vblank, flags, period, 300, 800, 900,
                                    done, 12, 12, 12, 0xff010002)))


def raw(rows):
    return b"".join(struct.pack(">11I", *(r[f] for f in profile.FIELDS)) for r in rows)


def function_body(source, name):
    start = source.index("static void " + name + "(")
    brace = source.index("{", start)
    level = 1
    end = brace + 1
    while level:
        level += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


class CpuSlackTests(unittest.TestCase):
    def test_pairs_same_frame_and_keeps_busy_samples_separate(self):
        a = row(10, profile.FINISHED | profile.HANDED | profile.BUSY_DONE | profile.BUSY_END)
        b = row(11, done=3400)
        result = profile.summarize([a, b], candidate_ticks=1000, reserve_ticks=200)
        self.assertEqual(result["completion_window_ticks"]["min"], 100)
        self.assertEqual(result["completion_window_with_slave_busy_at_done"]["mean"], 1500)
        self.assertEqual(result["candidate"]["fits_gameplay_window_upper_bound"], 1)
        self.assertEqual(result["candidate"]["fits_busy_end_window_upper_bound"], 1)

    def test_overrun_home_and_invalid_samples_never_offer_slack(self):
        invalid = [profile.OVERRUN, profile.HOME, profile.TIMER_WRAP,
                   profile.UNPAIRED_DONE, profile.BAD_ORDER]
        result = profile.summarize([row(i + 1, profile.FINISHED | bit) for i, bit in enumerate(invalid)],
                                   candidate_ticks=0)
        self.assertEqual(result["counts"]["valid_completion_windows"], 0)
        self.assertEqual(result["candidate"]["fits_gameplay_window_upper_bound"], 0)

    def test_detects_reversed_missing_and_wrapped_phases(self):
        rows = [row(1, done=800), row(2, done=4000), row(3, done=profile.UNKNOWN), row(4, period=0)]
        self.assertTrue(all(r["completion_window_ticks"] is None for r in profile.summarize(rows)["rows"]))

    def test_missing_handoff_still_measures_master(self):
        sample = row(1, flags=profile.FINISHED)
        sample["handoff_tick"] = sample["layers_done_tick"] = profile.UNKNOWN
        result = profile.summarize([sample])
        self.assertEqual(result["completion_window_ticks"]["mean"], 1500)
        self.assertEqual(result["snapshot_handoff_ticks"], {"count": 0})

    def test_ring_rollover_and_incomplete_publication(self):
        decoded = profile.decode_ring(raw([row(1), row(0), row(0xffffffff), row(2)]))
        self.assertEqual([r["vblank"] for r in decoded], [0xffffffff, 1, 2])
        self.assertEqual(profile.summarize(decoded)["counts"]["vblank_gaps"], 1)

    def test_bad_binary_is_rejected(self):
        for data in (b"", b"\0" * 43, raw([row(1), row(1)]),
                     raw([row(1, flags=4096)]), raw([row(1, period=65536)])):
            with self.assertRaises(ValueError):
                profile.decode_ring(data)

    def test_join_uses_source_vblank_never_cross_cpu_timestamps(self):
        plot = {"source_vblank": 5, "submit_tick": 60000, "cpu_ticks": 7, "flags": 1}
        report = {"plot_rows": [plot], "frame_rows": [{"vblank": 6, "shown_after": 9}]}
        sample = profile.summarize([row(5)], vdp1=report)["rows"][0]
        self.assertEqual(sample["completion_window_ticks"], 1500)
        self.assertEqual(sample["vdp1_source_plots"], [plot])
        self.assertEqual(sample["next_vblank_presentation"]["shown_after"], 9)

    def test_negative_candidate_or_reserve_rejected(self):
        for kwargs in ({"candidate_ticks": -1}, {"reserve_ticks": -1}):
            with self.assertRaises(ValueError):
                profile.summarize([], **kwargs)

    def test_actual_recorder_and_kernel_sampler_strict_c90(self):
        kernel = (ROOT / "saturn/rt/kernel.c").read_text()
        with tempfile.TemporaryDirectory(prefix="cpu-slack-test-") as tmp:
            temp = Path(tmp)
            (temp / "cpu_slack_mark_idle.inc").write_text(function_body(kernel, "cpu_slack_mark_idle"))
            for depth in (2, 4, 16):
                binary = temp / f"probe-{depth}"
                subprocess.run(["gcc", "-std=c90", "-pedantic", "-Wall", "-Wextra", "-Werror", "-O2",
                                "-DSAT_CPU_SLACK_PROFILE", f"-DSAT_CPU_SLACK_DEPTH={depth}",
                                "-I", str(temp), str(ROOT / "tests/cpu_slack_profile_test.c"),
                                "-o", str(binary)], check=True)
                result = subprocess.run([str(binary), str(temp / "rows.bin")], check=True,
                                        text=True, capture_output=True)
                self.assertIn(f"declared state {44 * depth + 56} bytes", result.stdout)
                parsed = profile.decode_ring((temp / "rows.bin").read_bytes(), sys.byteorder)
                if depth == 16:
                    self.assertEqual(profile.summarize(parsed)["counts"]["valid_completion_windows"], 1)

    def test_disabled_probe_has_no_symbols_or_storage(self):
        source = '#include "saturn/rt/cpu_slack_profile.h"\nint main(void) { return 0; }\n'
        with tempfile.TemporaryDirectory(prefix="cpu-slack-disabled-") as tmp:
            binary = str(Path(tmp) / "off")
            subprocess.run(["gcc", "-std=c90", "-pedantic", "-Wall", "-Wextra", "-Werror",
                            "-x", "c", "-I", str(ROOT), "-o", binary, "-"],
                           input=source, text=True, check=True, capture_output=True)
            symbols = subprocess.run(["nm", binary], check=True, text=True, capture_output=True).stdout
            self.assertNotIn("cpu_slack", symbols)

    def test_non_power_of_two_depth_is_rejected(self):
        source = '#define SAT_CPU_SLACK_PROFILE\n#include "saturn/rt/cpu_slack_profile.h"\n'
        result = subprocess.run(["gcc", "-E", "-x", "c", "-I", str(ROOT), "-DSAT_CPU_SLACK_DEPTH=3", "-"],
                                input=source, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("power of two", result.stderr)


if __name__ == "__main__":
    unittest.main()
