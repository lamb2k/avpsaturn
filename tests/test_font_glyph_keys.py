"""HOST synthetic test of tools/font_glyph_keys.py: no ROM data, a made-up image holding only the two glyph tables the module reads."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("font_glyph_keys", ROOT / "tools/font_glyph_keys.py")
fgk = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fgk)


def image(chrome=None, two_row=None):
    """Chrome glyphs at 0x100, 0x102, ... (80 distinct), two row glyphs 0x280 + i (80 distinct), char 0x20 blank."""
    chrome = chrome or [0] + [0x100 + 2 * i for i in range(80)] + [0] * 15
    two_row = two_row or [0x100] + [0x280 + i for i in range(80)] + [0x100] * 15
    rom = bytearray(0xac000)
    rom[fgk.CHROME_TABLE:fgk.CHROME_TABLE + 192] = struct.pack(">96H", *chrome)
    rom[fgk.TWO_ROW_TABLE:fgk.TWO_ROW_TABLE + 192] = struct.pack(">96H", *two_row)
    return bytes(rom)


class FontGlyphKeys(unittest.TestCase):
    def test_every_glyph_at_both_parities_in_both_banks(self):
        split = fgk.by_font(image())
        chrome = split["chrome"]
        for g in (0x100, 0x102, 0x100 + 2 * 79):
            for d in (0, 1, 0x10, 0x11):    # the 2 x 2 cells of one glyph
                for bank in (0, 0x1000):
                    for p in (0, 1):
                        self.assertIn((g + d + bank) << 1 | p, chrome)
        two_row = split["two row"]
        for c in (0x280, 0x280 + 79):
            for d in (0, 0x10, 1, 0x11):    # code, the cell below, and the double wide printers' second column
                for p in (0, 1):
                    self.assertIn((c + d + 0x1000) << 1 | p, two_row)

    def test_small_font_and_select_digits(self):
        split = fgk.by_font(image())
        for c in list(range(0x20, 0x80)) + [0, 9, 0xf]:
            for p in (0, 1):
                self.assertIn(c << 1 | p, split["small"])
                self.assertIn((c + 0x1000) << 1 | p, split["small"])
        for c in (0x20, 0x41, 0x7f):    # name entry bank
            self.assertIn((c + 0xa60) << 1, split["small"])
        self.assertEqual(split["select digits"], {c << 1 | p for c in range(0xb00, 0xb40) for p in (0, 1)})

    def test_keys_is_the_union(self):
        rom = image()
        split = fgk.by_font(rom)
        self.assertEqual(fgk.keys(rom), set().union(*split.values()))

    def test_wrong_image_fails_loudly(self):
        with self.assertRaises(ValueError):
            fgk.keys(bytes(0xac000))                      # empty tables
        bad = [0] + [0x100 + 2 * i for i in range(79)] + [0x1234] + [0] * 15
        with self.assertRaises(ValueError):
            fgk.keys(image(chrome=bad))                   # a word outside the chrome rows

    def test_merge_into_screen_keys_file_is_idempotent(self):
        rom = image()
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "rom").write_bytes(rom)
            (d / "screen_keys.txt").write_text("0 1234\n1 200\n")
            self.assertEqual(fgk.main([str(d / "rom"), str(d / "screen_keys.txt")]), 0)
            first = (d / "screen_keys.txt").read_text()
            self.assertEqual(fgk.main([str(d / "rom"), str(d / "screen_keys.txt")]), 0)
            self.assertEqual(first, (d / "screen_keys.txt").read_text())
            self.assertTrue(first.startswith("0 1234\n1 200\n"))


if __name__ == "__main__":
    unittest.main()
