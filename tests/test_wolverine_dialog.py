"""Wolverine's story box wording (tools/wolverine/dialog.py, saturn/rt/guest_dialog.h): synthetic HOST tests, no ROM input.
One extra test runs the real wording against the real ROM image when it is on this PC (skipped otherwise)."""
import importlib
import os
import pathlib
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/wolverine"))
import dialog  # noqa: E402
import dialog_lines  # noqa: E402
import dialog_hashes  # noqa: E402

REAL_ROM = pathlib.Path("E:/AvP/learning/lane-wv-talkbox/wd/rt.bin")
ROM_SIZE = 0x200000


def put_record(rom, at, sel, l1, l2, dur=0x78):
    w = [0xffff, 0, 0, 0, 0, dur, sel] + dialog.encode(l1) + [0] + dialog.encode(l2)
    rom[at:at + 0x80] = struct.pack(">64H", *w)


class World:
    def __init__(self, td):
        rng = random.Random(7)
        self.rom = bytearray(rng.randrange(256) for _ in range(ROM_SIZE))
        self.recs = {0x1000: ("They just keep coming!", "We have to fall back!"), 0x1080: ("Hold on, bub?", ""), 0x1100: ("Schaefer? Clear out!", "")}
        put_record(self.rom, 0x1000, 0x100, *self.recs[0x1000])
        put_record(self.rom, 0x1080, 0x100, *self.recs[0x1080])
        put_record(self.rom, 0x1100, 0x900, *self.recs[0x1100])
        put_record(self.rom, 0x1180, 0x300, "Linn speaks here.", "Not changed.")        # another speaker: never in the wording
        self.rom[0x2000:0x2020] = b"Maj.D.SCHAEFER      PREDATOR H"[:32].ljust(32, b" ")
        self.rom[0x2100:0x2112] = b"Maj.D.SCHAEFER  \0\0"
        self.rom_path = pathlib.Path(td) / "rom.bin"
        self.rom_path.write_bytes(bytes(self.rom))
        self.lines = {0x1000: ("They keep coming, bub.", "We gotta fall back!"), 0x1080: ("Hold on!", ""), 0x1100: ("Wolverine? Clear out!", "It's coming!")}
        self.names = ((0x2000, 20, "WOLVERINE", "left"), (0x2100, 16, "WOLVERINE", "centre"))
        self.saved = (dialog_lines.LINES, dialog_lines.NAMES, dialog_hashes.HASHES)
        dialog_lines.LINES, dialog_lines.NAMES = self.lines, self.names
        dialog_hashes.HASHES = {a: dialog.rec_hash(bytes(self.rom), a) for a in self.lines}

    def close(self):
        dialog_lines.LINES, dialog_lines.NAMES, dialog_hashes.HASHES = self.saved


class DialogTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.w = World(self._t.name)

    def tearDown(self):
        self.w.close()
        self._t.cleanup()

    def test_font_round_trip_and_limits(self):
        s = "Gah, it's stuck? Yes - 'em."
        self.assertEqual(dialog.decode(dialog.encode(s)), s)
        self.assertEqual(len(dialog.encode("")), 28)
        with self.assertRaises(ValueError):
            dialog.encode("x" * 29)
        with self.assertRaises(ValueError):
            dialog.encode("no digits 1")           # the font has no 1 in the story box
        # the arcade's own cell codes for the words seen on its screens: T h e y at 0x2c8 0x2e6 0x2e3 0x307
        self.assertEqual(dialog.encode("They")[:4], [0x2c8, 0x2e6, 0x2e3, 0x307])

    def test_build_checks_the_rom(self):
        out = pathlib.Path(self._t.name) / "out"
        r = dialog.build(self.w.rom_path, out)
        self.assertEqual(r["records"], 3)
        text = pathlib.Path(r["include"]).read_text()
        self.assertIn("dlg_data", text)
        self.assertIn("dlg_names", text)
        # another ROM revision: the hash no longer matches
        rom = bytearray(self.w.rom)
        rom[0x1000 + 20] ^= 1
        p = pathlib.Path(self._t.name) / "rom2.bin"
        p.write_bytes(bytes(rom))
        with self.assertRaisesRegex(ValueError, "not the ones the wording was written for"):
            dialog.build(p, out)
        # a record of another speaker is refused
        dialog_lines.LINES[0x1180] = ("x", "")
        dialog_hashes.HASHES[0x1180] = dialog.rec_hash(bytes(self.w.rom), 0x1180)
        with self.assertRaisesRegex(ValueError, "not Schaefer's slot"):
            dialog.build(self.w.rom_path, out)
        del dialog_lines.LINES[0x1180]

    @unittest.skipUnless(shutil.which("gcc"), "gcc is needed for the HOST C check")
    def test_sync_on_off_is_exact_and_touches_only_the_wording(self):
        out = pathlib.Path(self._t.name) / "out"
        dialog.build(self.w.rom_path, out)
        main = pathlib.Path(self._t.name) / "t.c"
        main.write_text('''
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "guest_dialog.h"
#include "guest_dialog.inc"
int main(int argc, char **argv)
{
    static unsigned char rom[0x200000], orig[0x200000];
    FILE *f = fopen(argv[1], "rb"); fread(rom, 1, sizeof rom, f); fclose(f); memcpy(orig, rom, sizeof rom);
    guest_dialog_sync(dlg_data, dlg_glyph, 0, rom); guest_name_sync(dlg_names, 2, 0, rom);
    if (memcmp(rom, orig, sizeof rom)) { puts("OFF CHANGED THE IMAGE"); return 1; }          /* off: never a byte */
    guest_dialog_sync(dlg_data, dlg_glyph, 1, rom); guest_name_sync(dlg_names, 2, 1, rom);
    f = fopen(argv[2], "wb"); fwrite(rom, 1, sizeof rom, f); fclose(f);
    guest_dialog_sync(dlg_data, dlg_glyph, 0, rom); guest_name_sync(dlg_names, 2, 0, rom);
    if (memcmp(rom, orig, sizeof rom)) { puts("OFF DID NOT RESTORE"); return 2; }
    guest_dialog_sync(dlg_data, dlg_glyph, 1, rom); guest_name_sync(dlg_names, 2, 1, rom);   /* twice on is the same as once */
    guest_dialog_sync(dlg_data, dlg_glyph, 1, rom); guest_name_sync(dlg_names, 2, 1, rom);
    f = fopen(argv[3], "wb"); fwrite(rom, 1, sizeof rom, f); fclose(f);
    puts("ok"); return 0;
}
''')
        exe = pathlib.Path(self._t.name) / "t"
        subprocess.run(["gcc", "-std=gnu99", "-Wall", "-O1", "-I" + str(out), "-I" + str(ROOT / "saturn/rt"), str(main), "-o", str(exe)], check=True)
        a, b = pathlib.Path(self._t.name) / "on1.bin", pathlib.Path(self._t.name) / "on2.bin"
        r = subprocess.run([str(exe), str(self.w.rom_path), str(a), str(b)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        on = a.read_bytes()
        self.assertEqual(on, b.read_bytes())
        orig = bytes(self.w.rom)
        for at, (l1, l2) in self.w.lines.items():
            w = struct.unpack(">64H", on[at:at + 0x80])
            self.assertEqual(dialog.decode(list(w[7:35])), l1)
            self.assertEqual(dialog.decode(list(w[36:64])), l2)
            self.assertEqual(w[:7], struct.unpack(">64H", orig[at:at + 0x80])[:7])   # header, time and speaker word untouched
            self.assertEqual(w[35], 0)
        self.assertEqual(on[0x2000:0x2014], b"WOLVERINE           ")
        self.assertEqual(on[0x2100:0x2110], b"   WOLVERINE    ")
        changed = [i for i in range(len(orig)) if on[i] != orig[i]]
        allowed = set()
        for at in self.w.lines:
            allowed.update(range(at + 14, at + 14 + 56))
            allowed.update(range(at + 72, at + 72 + 56))
        allowed.update(range(0x2000, 0x2014))
        allowed.update(range(0x2100, 0x2110))
        self.assertTrue(set(changed) <= allowed)
        self.assertEqual(orig[0x1180:0x1200], on[0x1180:0x1200])                      # another speaker's record is never touched

    def test_lines_fit_and_use_only_the_font(self):
        for at, (l1, l2) in dialog_lines.LINES.items():
            self.assertLessEqual(len(l1), 27, "%x" % at)   # 28 is the field; the last cell stays blank as in the arcade's lines
            self.assertLessEqual(len(l2), 27, "%x" % at)
            dialog.encode(l1), dialog.encode(l2)
        for at, n, text, align in dialog_lines.NAMES:
            self.assertLessEqual(len(text), n)
        self.assertEqual(sorted(dialog_lines.LINES), sorted(dialog_hashes.HASHES))
        self.assertNotIn("Schaefer", "".join(l1 + l2 for l1, l2 in dialog_lines.LINES.values()))


@unittest.skipUnless(REAL_ROM.is_file(), "the real ROM image is not here")
class RealRomTest(unittest.TestCase):
    def test_real_wording_matches_the_real_rom(self):
        importlib.reload(dialog_lines)
        importlib.reload(dialog_hashes)
        rom = REAL_ROM.read_bytes()
        dialog.check(rom)
        for at in dialog_lines.LINES:
            w = dialog.record(rom, at)
            self.assertIn(w[6], (0x100, 0x900))
        with tempfile.TemporaryDirectory() as td:
            r = dialog.build(REAL_ROM, td)
            self.assertEqual(r["records"], len(dialog_lines.LINES))


if __name__ == "__main__":
    unittest.main()
