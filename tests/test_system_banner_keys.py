"""HOST synthetic test of tools/system_banner_keys.py: no ROM data, a made-up image holding only the tables the module reads."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("system_banner_keys", ROOT / "tools/system_banner_keys.py")
sbk = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sbk)


def images():
    rom, op = bytearray(0x21000), bytearray(0x21000)
    rom[sbk.BANNER_TABLE:sbk.BANNER_TABLE + 16] = struct.pack(">8H", *sbk.EXPECT_BANNER)
    op[sbk.DIGIT_TABLE:sbk.DIGIT_TABLE + 20] = struct.pack(">10H", *sbk.EXPECT_DIGITS)
    for i, code in enumerate(sbk.COLON_CODES):   # move.l #code<<16, d(a0): 21 7c cc cc 00 00 dd dd
        op[sbk.COLON_CODE_AT + 8 * i:sbk.COLON_CODE_AT + 8 * i + 8] = struct.pack(">HHHH", 0x217c, code, 0, 0x100 * (i + 1))
    return bytes(rom), bytes(op)


class SystemBannerKeys(unittest.TestCase):
    def test_second_u_needs_the_other_column_parity(self):
        rom, op = images()
        k = sbk.keys(rom, op)
        # U at map column 18 (even) and again at column 27 (odd): all eight half-cell keys of the glyph.
        for code in (0x1c2, 0x1c3, 0x1d2, 0x1d3):
            self.assertIn(code << 1, k)
            self.assertIn(code << 1 | 1, k)
        # H is drawn once, at column 16: only the even-column halves of its left codes and the odd halves of its right codes.
        self.assertIn(0x188 << 1, k)
        self.assertNotIn(0x188 << 1 | 1, k)
        self.assertIn(0x189 << 1 | 1, k)
        self.assertNotIn(0x189 << 1, k)

    def test_counts(self):
        rom, op = images()
        k = sbk.keys(rom, op)
        # H, R, Y, P and ! four keys each, U eight, ten digits at three odd columns four each, the colon four.
        self.assertEqual(len(k), 4 * 5 + 8 + 10 * 4 + 4)

    def test_wrong_image_fails_loudly(self):
        rom, op = images()
        with self.assertRaises(ValueError):
            sbk.keys(bytes(len(rom)), op)

    def test_merge_into_screen_keys_file_is_idempotent(self):
        rom, op = images()
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "rom").write_bytes(rom)
            (d / "op").write_bytes(op)
            (d / "screen_keys.txt").write_text("0 1234\n1 310\n")
            self.assertEqual(sbk.main([str(d / "rom"), str(d / "op"), str(d / "screen_keys.txt")]), 0)
            first = (d / "screen_keys.txt").read_text()
            self.assertEqual(sbk.main([str(d / "rom"), str(d / "op"), str(d / "screen_keys.txt")]), 0)
            self.assertEqual(first, (d / "screen_keys.txt").read_text())
            self.assertTrue(first.startswith("0 1234\n1 310\n"))
            self.assertEqual(first.count("\n"), 2 + len(sbk.keys(rom, op)) - 1)   # 0x310 is H's first key, already listed


if __name__ == "__main__":
    unittest.main()
