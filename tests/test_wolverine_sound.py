"""Synthetic HOST checks for Wolverine's sounds (lane wv-sounds): the id list agrees between C and Python, and the pack rebuild keeps the arcade rows, remaps Schaefer's, adds Wolverine's,
drops by rank when the room is short, and leaves a pack with no assets alone. No ROM data: clips are made up."""
import importlib.util
import re
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/wolverine"))
sys.path.insert(0, str(ROOT / "saturn/audio"))
spec = importlib.util.spec_from_file_location("wv_audio", ROOT / "tools/wolverine/wv_audio.py")
wv_audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wv_audio)
spec = importlib.util.spec_from_file_location("wv_sound", ROOT / "tools/wolverine/wv_sound.py")
wv_sound = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wv_sound)


def make_pack(rows, music=1):
    """rows: [(cmd, prio, mask, tl, data)] sorted by cmd."""
    blob, table = bytearray(), bytearray()
    for cmd, prio, mask, tl, data in rows:
        table += struct.pack(">HBBBBBBII", cmd, prio, mask >> 8, mask & 255, tl, 0, 0, len(blob), len(data))
        blob += data + bytes(len(data) & 1)
    return struct.pack(">4sHHI", b"SAU1", len(rows), music, len(blob)) + bytes(table) + bytes(16 * music) + bytes(blob)


def assets():
    sounds = []
    for i, name in enumerate(["SELECT", "HURT_A", "KO", "TORNADO", "CLAW_H", "CLAW_M", "BERSERKER"]):
        data = bytes([i + 1]) * (100 + i)
        sounds.append(dict(id=i, name=name, cmd=0x100 + i, prio=6, mask=0x1000, tl=40 + i, off=0, n=len(data), where="front" if name == "SELECT" else "stage", data=data))
    return dict(rate=11025, cmd_base=wv_audio.WV_CMD_BASE if hasattr(wv_audio, "WV_CMD_BASE") else 0x2c0, sounds=sounds)


class SoundList(unittest.TestCase):
    def test_header_matches_python(self):
        text = (ROOT / "saturn/guests/wolverine/wv_sound.h").read_text()
        base = int(re.search(r"#define WV_CMD_BASE (0x[0-9a-f]+)", text).group(1), 16)
        names = re.findall(r"WV_SFX_([A-Z_]+?)(?: = 0)?,", text[text.index("enum {"):text.index("WV_SFX_COUNT")])
        self.assertEqual(base, wv_sound.CMD_BASE)
        self.assertEqual(names, [s["name"] for s in wv_sound.SOUNDS])
        self.assertEqual([s["id"] for s in wv_sound.SOUNDS], list(range(len(names))))

    def test_commands_unused_by_the_game(self):
        # the driver's table 0x276..0x2ff are null entries (the game never sends them); a Wolverine command must stay inside
        for s in wv_sound.SOUNDS:
            self.assertTrue(0x276 <= wv_sound.CMD_BASE + s["id"] <= 0x2ff)
        self.assertTrue(len(wv_sound.SOUNDS) < 0x2ff - 0x2c0)


class PackRebuild(unittest.TestCase):
    def base(self):
        rows = [(0x30, 4, 0x8000, 20, b"a" * 50), (0x97, 7, 0x400, 29, b"b" * 60), (0x213, 6, 0x1000, 24, b"c" * 70), (0x214, 7, 0x1000, 27, b"d" * 80),
                (0x250, 6, 0x1000, 24, b"e" * 90), (0x300, 4, 0x2000, 30, b"f" * 40)]
        return make_pack(rows)

    def test_remap_and_add(self):
        out, rep = wv_audio.build(self.base(), assets(), {}, "stage")
        rows, music, clips = wv_audio.parse(out)
        by = {r["cmd"]: r for r in rows}
        w = {s["name"]: s for s in assets()["sounds"]}
        self.assertEqual(sorted(rep["remapped"]), ["0x213", "0x214", "0x250", "0x97"])
        self.assertEqual(clips[by[0x213]["off"]:by[0x213]["off"] + by[0x213]["n"]], w["HURT_A"]["data"])
        self.assertEqual(by[0x213]["tl"], w["HURT_A"]["tl"])
        self.assertEqual((by[0x213]["prio"], by[0x213]["mask"]), (6, 0x1000))   # the game's priority and channel stay
        self.assertEqual(by[0x214]["n"], len(w["KO"]["data"]))
        self.assertIn(0x2c0 + 1, by)                                        # HURT_A at base + id
        self.assertNotIn(0x2c0, by)                                         # SELECT is the front file's
        self.assertEqual(clips[by[0x30]["off"]:by[0x30]["off"] + 50], b"a" * 50)   # arcade rows untouched
        self.assertEqual([r["cmd"] for r in rows], sorted(r["cmd"] for r in rows))
        self.assertEqual(len(music), 16)
        self.assertEqual(by[0x2c0 + 1]["off"], by[0x213]["off"])              # identical clips are shared

    def test_front_gets_only_select(self):
        out, rep = wv_audio.build(make_pack([(0x264, 5, 0x2000, 29, b"s" * 90), (0x30, 4, 0x8000, 20, b"a" * 50)]), assets(), {}, "front")
        rows, _, clips = wv_audio.parse(out)
        by = {r["cmd"]: r for r in rows}
        self.assertEqual(rep["remapped"], ["0x264"])
        self.assertEqual(sorted(by), [0x30, 0x264, 0x2c0])

    def test_drop_by_rank_never_wolverine(self):
        pack = self.base()
        rows, _, _ = wv_audio.parse(pack)
        full, _ = wv_audio.build(pack, assets(), {}, "stage")
        out, rep = wv_audio.build(pack, assets(), {0x30: 1000, 0x300: 5}, "stage", room=len(full) - 30)
        by = {r["cmd"] for r in wv_audio.parse(out)[0]}
        self.assertNotIn(0x300, by)                 # fewest uses leave first
        self.assertIn(0x30, by)
        for s in assets()["sounds"]:
            if s["where"] == "stage":
                self.assertIn(0x2c0 + s["id"], by)
        with self.assertRaises(SystemExit):
            wv_audio.build(pack, assets(), {}, "stage", room=100)

    def test_pack_limit_respected(self):
        out, rep = wv_audio.build(self.base(), assets(), {}, "stage")
        self.assertLessEqual(len(out), wv_audio.SCSP_ROOM)
        self.assertEqual(rep["size"], len(out))


if __name__ == "__main__":
    unittest.main()
