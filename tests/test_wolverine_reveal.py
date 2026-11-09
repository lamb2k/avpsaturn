"""Post-credits Wolverine reveal: the recolour (tools/wolverine/reveal_recolour.py), the disc file (reveal_pack.py) and the unlock record (saturn/rt/unlock_save.h).
Synthetic HOST tests plus one check that the committed art data is reproducible from the committed recoloured frames. No ROM input."""
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/wolverine"))
try:
    import numpy as np
    from PIL import Image
    import reveal_pack
    import reveal_recolour
except ImportError:   # pragma: no cover
    np = None


def synthetic_frames(directory):
    """Three 384 x 224 indexed frames in the artist's layout: index 0 transparent, 1 black, a costume ramp (53 50 47 43), a shared steel blue, a teal alien."""
    pal = [(0, 0, 0)] * 83
    pal[1] = (0, 0, 0)
    pal[43] = (0x33, 0x33, 0x44)
    pal[47] = (0x44, 0x55, 0x77)
    pal[50] = (0x44, 0x55, 0x99)
    pal[53] = (0x55, 0x66, 0xaa)
    pal[25] = (0xbb, 0x77, 0x22)   # yellow
    pal[26] = (0xdd, 0x88, 0x11)
    pal[37] = (0x33, 0x44, 0x33)   # alien teal
    pal[44] = (0x44, 0x44, 0x55)
    flat = [c for rgb in pal for c in rgb]
    bands = ((48, 176), (48, 176), (24, 200))
    names = ("frame1_closed.png", "frame2_opening.png", "frame3_burst.png")
    for n, (r0, r1) in zip(names, bands):
        a = np.ones((224, 384), dtype=np.uint8)
        a[r0:r1] = 44
        if n.startswith("frame3"):
            a[100:110, 120:130] = 53
            a[110:120, 120:130] = 50
            a[120:122, 120:130] = 47     # the costume's dark steps, touching the blues
            a[122:125, 120:130] = 43
            a[100:110, 300:310] = 47     # scenery (a pipe) of the same entries, far from the costume
            a[110:120, 300:310] = 43
            a[60:70, 200:210] = 37       # an alien
            a[130:145, 165:180] = 26     # the costume's yellow (a patch of at least 80 pixels in the figure's box)
            a[130:140, 300:310] = 26     # a hazard stripe of the same entry
        im = Image.fromarray(a, "P")
        im.putpalette(flat + [0] * (768 - len(flat)))
        im.save(pathlib.Path(directory) / n)
    return names


@unittest.skipIf(np is None, "numpy and Pillow are needed")
class RecolourTest(unittest.TestCase):
    def test_costume_only(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = pathlib.Path(d) / "src", pathlib.Path(d) / "out"
            src.mkdir()
            names = synthetic_frames(src)
            rep = reveal_recolour.recolour(src, out)
            before = np.array(Image.open(src / names[2]))
            im = Image.open(out / names[2].replace(".png", "_80s.png"))
            after, pal = np.array(im), im.getpalette()
            self.assertEqual(rep["palette_entries_after"], rep["palette_entries_before"] + 6)
            # the costume blues became the 80s red-brown ramp, the yellows the gold ramp (revision 3)
            self.assertEqual(tuple(pal[53 * 3:53 * 3 + 3]), (0xbb, 0x77, 0x55))
            self.assertEqual(tuple(pal[50 * 3:50 * 3 + 3]), (0x99, 0x55, 0x33))
            red = lambda i: tuple(pal[i * 3:i * 3 + 3])
            self.assertEqual(red(after[123, 125]), (0x33, 0x11, 0x11))   # costume darkest
            self.assertEqual(red(after[121, 125]), (0x66, 0x22, 0x11))
            # the scenery of the shared entries and the alien keep their entry and colour
            self.assertTrue((after[100:110, 300:310] == 47).all() and (after[110:120, 300:310] == 43).all())
            self.assertTrue((after[60:70, 200:210] == 37).all())
            self.assertEqual(red(after[135, 170]), (0xbb, 0x88, 0x33))     # gold, third step
            self.assertTrue((after[130:140, 300:310] == 26).all())          # the hazard stripe is still the artist's orange
            self.assertEqual(red(37), (0x33, 0x44, 0x33))
            # frames 1 and 2 are copies
            for n in names[:2]:
                a = np.array(Image.open(src / n))
                b = np.array(Image.open(out / n.replace(".png", "_80s.png")))
                self.assertTrue((a == b).all())
            self.assertLessEqual(rep["max_opaque_colours_per_tile"], 15)

    def test_originals_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = pathlib.Path(d) / "src", pathlib.Path(d) / "out"
            src.mkdir()
            names = synthetic_frames(src)
            before = [(src / n).read_bytes() for n in names]
            reveal_recolour.recolour(src, out)
            self.assertEqual(before, [(src / n).read_bytes() for n in names])
            self.assertTrue(all((out / n.replace(".png", "_80s.png")).exists() for n in names))


@unittest.skipIf(np is None, "numpy and Pillow are needed")
class PackTest(unittest.TestCase):
    def test_committed_art_reproduces(self):
        art = ROOT / "art/wolverine-reveal"
        frames = [art / n for n in ("frame1_closed_80s.png", "frame2_opening_80s.png", "frame3_burst_80s.png")]
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d) / "reveal.bin"
            reveal_pack.pack([str(f) for f in frames], str(out))
            self.assertEqual(out.read_bytes(), (art / "reveal.bin").read_bytes())
        blob = (art / "reveal.bin").read_bytes()
        self.assertEqual(blob[:4], b"RVL1")
        size, npal, nfr = struct.unpack(">IHH", blob[4:12])
        self.assertEqual((size, len(blob) % 2048, nfr), (len(blob), 0, 3))
        # frames fit a 512 x 256 bitmap and the bands are the ones the runtime copies
        for i, (r0, rows) in enumerate(((48, 128), (48, 128), (24, 176))):
            off = struct.unpack(">I", blob[12 + 4 * i:16 + 4 * i])[0]
            self.assertEqual(struct.unpack(">HH", blob[off:off + 4]), (r0, rows))
            self.assertEqual(off % 4, 0)
        self.assertEqual(struct.unpack(">H", blob[24:26])[0], 0)         # entry 0 clear
        self.assertEqual(struct.unpack(">H", blob[26:28])[0], 0x8000)    # entry 1 black

    def test_rejects_picture_outside_band(self):
        with tempfile.TemporaryDirectory() as d:
            src = pathlib.Path(d)
            names = synthetic_frames(src)
            a = np.array(Image.open(src / names[0]))
            a[10, 10] = 44
            im = Image.fromarray(a, "P")
            im.putpalette(Image.open(src / names[0]).getpalette())
            im.save(src / names[0])
            with self.assertRaises(AssertionError):
                reveal_pack.pack([str(src / n) for n in names], str(src / "x.bin"))


class UnlockRecordTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("gcc"), "gcc is needed for HOST C regressions")
    def test_record(self):
        with tempfile.TemporaryDirectory() as d:
            exe = pathlib.Path(d) / "unlock_save_test"
            subprocess.run(["gcc", "-std=c90", "-Wall", "-Wextra", "-Werror", str(ROOT / "tests/unlock_save_test.c"), "-o", str(exe)], check=True)
            out = subprocess.run([str(exe)], check=True, capture_output=True, text=True).stdout
            self.assertIn("pass", out)


if __name__ == "__main__":
    unittest.main()
