"""Synthetic checks for guest audio capacity and optional cues."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "wolverine"))
import wv_audio


class GuestAudioTests(unittest.TestCase):
    def test_optional_cue_never_displaces_the_normal_guest_mix(self):
        base_cue, continue_cue = 0x0100, 0x0202
        base_pcm, continue_pcm = bytes([1]) * 64, bytes([2]) * 32
        old_row = wv_audio.ROW.pack(base_cue, 4, 0, 1, 20, 0, 0, 0, len(base_pcm))
        extra_row = wv_audio.ROW.pack(
            continue_cue, 7, 0, 2, 20, 0, 0, len(base_pcm), len(continue_pcm),
        )
        base = wv_audio.HDR.pack(b"SAU1", 1, 0, len(base_pcm)) + old_row + base_pcm
        combined = (
            wv_audio.HDR.pack(b"SAU1", 2, 0, len(base_pcm) + len(continue_pcm))
            + old_row + extra_row + base_pcm + continue_pcm
        )
        guest = {
            "cmd_base": 0x02C0,
            "sounds": [{"name": "VOICE", "id": 0, "prio": 7, "mask": 4,
                        "tl": 20, "data": bytes([3]) * 16, "n": 16}],
        }

        original, _ = wv_audio.build(base, guest)
        tight, report = wv_audio.build(
            combined, guest, room=len(original), optional_commands=(continue_cue,),
        )
        self.assertEqual(tight, original)
        self.assertEqual(report["optional_unfit"], ["0x202"])

        enough, report = wv_audio.build(
            combined, guest, room=len(original) + len(extra_row) + len(continue_pcm),
            optional_commands=(continue_cue,),
        )
        rows, _, pcm = wv_audio.parse(enough)
        self.assertEqual([r["cmd"] for r in rows], [base_cue, continue_cue, 0x02C0])
        cue = rows[1]
        self.assertEqual(pcm[cue["off"]:cue["off"] + cue["n"]], continue_pcm)
        self.assertNotIn("optional_unfit", report)


if __name__ == "__main__":
    unittest.main()
