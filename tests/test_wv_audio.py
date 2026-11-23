"""Synthetic checks for guest audio capacity and optional cues."""
from pathlib import Path
import math
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from predator_audio import WARRIOR_REENTRY, append_cues, donor_cues
from wolverine import wv_audio


class GuestAudioTests(unittest.TestCase):
    def test_frees_pcm_without_resampling_stock_sounds_or_guest_loops(self):
        sample = bytes(round(72 * math.sin(i * math.tau * 500 / 11025)) & 255 for i in range(640))
        stock, guest_alias, guest, loop = 0x0200, 0x0214, 0x02CB, 0x02CD
        entries = [
            (stock, 0, 0, 640), (guest_alias, 0, 640, 640),
            (guest, 0, 640, 496), (loop, 1, 1280, 640),
        ]
        rows = [dict(cmd=cmd, flags=flags, off=off, n=size, rate=0, prio=7, mask=4, tl=20)
                for cmd, flags, off, size in entries]
        music = bytes(range(wv_audio.ROW.size))
        original = wv_audio.encode(rows, music, sample * 3)
        self.assertIsNone(wv_audio.free_guest_pcm(original, 321))

        compacted = wv_audio.free_guest_pcm(original, 320)
        after, music_after, pcm = wv_audio.parse(compacted)
        by_cmd = {row["cmd"]: row for row in after}
        self.assertEqual(music_after, music)
        self.assertEqual(pcm[:640], sample)
        self.assertEqual(pcm[by_cmd[loop]["off"]:], sample)
        self.assertEqual(by_cmd[stock], rows[0])
        self.assertEqual(by_cmd[guest_alias], dict(rows[1], n=320, rate=2))
        self.assertEqual(by_cmd[guest], dict(rows[2], n=248, rate=2))
        self.assertEqual(by_cmd[loop], dict(rows[3], off=960))

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

        hit_cue, hit_pcm = 0x0041, bytes([4]) * 32
        hit_offset = len(base_pcm) + len(continue_pcm)
        hit_row = wv_audio.ROW.pack(hit_cue, 6, 0, 2, 20, 0, 0, hit_offset, len(hit_pcm))
        with_hit = (
            wv_audio.HDR.pack(b"SAU1", 3, 0, hit_offset + len(hit_pcm))
            + hit_row + old_row + extra_row + base_pcm + continue_pcm + hit_pcm
        )
        same_mix, report = wv_audio.build(
            with_hit, guest, room=len(enough), optional_commands=(continue_cue, hit_cue),
        )
        self.assertEqual(same_mix, enough)
        self.assertEqual(report["optional_unfit"], ["0x41"])

        reserved_mix, report = wv_audio.build(
            combined, guest, room=len(original), reserved_commands=(continue_cue,),
        )
        self.assertEqual(reserved_mix, enough)
        self.assertNotIn("optional_unfit", report)

        reserved_hit, report = wv_audio.build(
            with_hit, guest, room=len(original), optional_commands=(continue_cue,),
            reserved_commands=(hit_cue,),
        )
        rows, _, pcm = wv_audio.parse(reserved_hit)
        self.assertEqual([r["cmd"] for r in rows], [hit_cue, base_cue, 0x02C0])
        self.assertEqual(pcm[rows[0]["off"]:rows[0]["off"] + rows[0]["n"]], hit_pcm)
        self.assertEqual(report["optional_unfit"], ["0x202"])

    def test_optional_alias_keeps_its_own_length(self):
        long_command, short_command = 0x010C, 0x0041
        pcm = bytes(range(32))
        entries = b"".join(
            wv_audio.ROW.pack(command, 4, 0, 1, 20, 0, 0, 0, length)
            for command, length in ((long_command, 32), (short_command, 24))
        )
        bank = wv_audio.HDR.pack(b"SAU1", 2, 0, len(pcm)) + entries + pcm
        packed, report = wv_audio.build(
            bank, {"cmd_base": 0x02C0, "sounds": []},
            room=len(bank), optional_commands=(long_command, short_command),
        )
        rows, _, samples = wv_audio.parse(packed)
        self.assertEqual(samples, pcm)
        self.assertEqual([(r["cmd"], r["off"], r["n"]) for r in rows],
                         [(short_command, 0, 24), (long_command, 0, 32)])
        self.assertNotIn("optional_unfit", report)

    def test_optional_pcm_reserve_stops_at_scsp_boundary(self):
        pcm = bytes(wv_audio.SCSP_PCM_ROOM)
        base, optional = 0x0010, 0x0041
        entries = (
            wv_audio.ROW.pack(base, 4, 0, 1, 20, 0, 0, 0, len(pcm))
            + wv_audio.ROW.pack(optional, 4, 0, 1, 20, 0, 0, len(pcm), 2)
        )
        bank = wv_audio.HDR.pack(b"SAU1", 2, 0, len(pcm) + 2) + entries + pcm + b"\x01\x02"
        result, report = wv_audio.build(
            bank, {"cmd_base": 0x02C0, "sounds": []}, room=len(bank),
            reserved_commands=(optional,),
        )
        rows, _, samples = wv_audio.parse(result)
        self.assertEqual([r["cmd"] for r in rows], [base])
        self.assertEqual(len(samples), wv_audio.SCSP_PCM_ROOM)
        self.assertEqual(report["optional_unfit"], ["0x41"])


class PredatorAudioTests(unittest.TestCase):
    def test_appended_aliases_do_not_extend_legacy_clips(self):
        short, long = 0x0041, 0x010C
        donor_pcm = bytes(range(1, 33))
        donor_rows = b"".join(
            wv_audio.ROW.pack(command, 4, 0, 1, 20, 0, 0, 0, length)
            for command, length in ((short, 24), (long, 32))
        )
        donor = wv_audio.HDR.pack(b"SAU1", 2, 0, len(donor_pcm)) + donor_rows + donor_pcm
        cues = donor_cues(donor, (short, long))
        existing = 0x0020
        old_pcm = bytes(wv_audio.SCSP_PCM_ROOM - len(donor_pcm))
        old_row = wv_audio.ROW.pack(existing, 7, 0, 2, 24, 0, 0, len(old_pcm) - 4, 8)
        bank = wv_audio.HDR.pack(b"SAU1", 1, 0, len(old_pcm)) + old_row + old_pcm
        patched, missing = append_cues(bank, (short, long), cues)
        rows, _, pcm = wv_audio.parse(patched)
        self.assertFalse(missing)
        self.assertEqual(pcm, old_pcm + donor_pcm)
        self.assertEqual([(row["cmd"], row["off"], row["n"]) for row in rows],
                         [(existing, len(old_pcm) - 4, 4), (short, len(old_pcm), 24),
                          (long, len(old_pcm), 32)])

    def test_impact_cues_take_priority_over_reentry_in_full_banks(self):
        impact = 0x0046
        impact_pcm = bytes([31]) * 4
        reentry_pcm = bytes([62]) * 8
        stock_pcm = bytes(wv_audio.SCSP_PCM_ROOM - len(reentry_pcm))
        bank = wv_audio.encode([], b"", stock_pcm)
        entry = dict(prio=4, mask=1, tl=20, flags=0, rate=0)
        donor = {
            impact: (dict(entry, cmd=impact), impact_pcm),
            WARRIOR_REENTRY: (dict(entry, cmd=WARRIOR_REENTRY), reentry_pcm),
        }
        patched, missing = append_cues(bank, (impact, WARRIOR_REENTRY), donor)
        rows, _, pcm = wv_audio.parse(patched)
        self.assertEqual(missing, {WARRIOR_REENTRY})
        self.assertEqual([row["cmd"] for row in rows], [impact])
        self.assertEqual(pcm, stock_pcm + impact_pcm)


if __name__ == "__main__":
    unittest.main()
