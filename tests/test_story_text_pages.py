"""HOST synthetic test of tools/story_text_pages.py: no ROM data, a made-up image holding only the six story tables' offset words."""
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("story_text_pages", ROOT / "tools/story_text_pages.py")
stp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stp)


def image(sizes=None):
    """Six tables: table i holds 64 offsets from 0x80 up in steps of 0x20; its 64th offset ends the table at the next table's address."""
    rom = bytearray(0x130000)
    for i, t in enumerate(stp.TABLES):
        last = (stp.TABLES[i + 1] - t) if i + 1 < len(stp.TABLES) else 0x2000
        offs = [0x80 + (last - 0x80) * k // 63 & ~1 for k in range(64)]
        offs[0], offs[-1] = 0x80, last
        rom[t:t + 128] = struct.pack(">64H", *offs)
    return bytes(rom)


class StoryTextPages(unittest.TestCase):
    def test_pages_cover_all_tables(self):
        p = stp.pages(image(), 1024)
        self.assertIn(stp.TABLES[0] // 1024, p)
        self.assertIn((stp.TABLES[-1] + 0x1fff) // 1024, p)
        self.assertEqual(min(p), stp.TABLES[0] // 1024)
        self.assertEqual(max(p), (stp.TABLES[-1] + 0x2000 - 1) // 1024)
        self.assertEqual(p, set(range(min(p), max(p) + 1)))

    def test_page_size_scales(self):
        self.assertGreater(len(stp.pages(image(), 512)), len(stp.pages(image(), 4096)))

    def test_wrong_image_fails_loudly(self):
        with self.assertRaises(ValueError):
            stp.pages(bytes(0x130000), 1024)
        rom = bytearray(image())
        rom[stp.TABLES[1] + 126:stp.TABLES[1] + 128] = struct.pack(">H", 0x1234)   # sentinel not at the next table
        with self.assertRaises(ValueError):
            stp.pages(bytes(rom), 1024)


if __name__ == "__main__":
    unittest.main()
