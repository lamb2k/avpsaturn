"""HOST: binary readback ABI, rollover, and mutually exclusive presentation counts."""
import importlib.util
from pathlib import Path
import struct
import unittest

MODULE = Path(__file__).resolve().parents[1] / "tools" / "vdp1_profile.py"
SPEC = importlib.util.spec_from_file_location("vdp1_profile", MODULE)
profile = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(profile)


class ProfileTests(unittest.TestCase):
    def test_ring_rollover_and_uncommitted_row(self):
        raw = b"".join(struct.pack(">6I", n, 0, 0, 0, 0, 0)
                       for n in (1, 0, 0xFFFFFFFF, 2, 0xFFFFFFFE))
        rows = profile.decode_ring(raw, profile.FRAME_FIELDS)
        self.assertEqual([r["vblank"] for r in rows], [0xFFFFFFFE, 0xFFFFFFFF, 1, 2])

    def test_repeated_plot_and_cpu_skip_are_not_added(self):
        rows = [dict(zip(profile.FRAME_FIELDS, values)) for values in (
            (10, 3, 2, 2, 0, 1),  # incomplete plot, also busy CPU
            (11, 3, 2, 3, 2, 0),  # safe frame-change request
            (12, 3, 3, 3, 0, 1),  # previous plot already handed over
        )]
        result = profile.summarize([], rows)["presentation"]
        self.assertEqual(result["sampled_vblanks"], 3)
        self.assertEqual(result["waiting_for_end_flag"], 1)
        self.assertEqual(result["frame_change_requests"], 1)
        self.assertEqual(result["no_unshown_plot"], 1)
        self.assertEqual(result["slave_busy_at_vblank"], 2)

    def test_truncated_dump_is_rejected(self):
        with self.assertRaises(ValueError):
            profile.decode_ring(b"\0" * 23, profile.FRAME_FIELDS)


if __name__ == "__main__":
    unittest.main()
