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
    import reveal_voice
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
            im = Image.open(out / names[2].replace(".png", "_red.png"))
            after, pal = np.array(im), im.getpalette()
            self.assertEqual(rep["palette_entries_after"], rep["palette_entries_before"] + 2)
            # the costume blues became his sprite's reds; the yellows stay
            self.assertEqual(tuple(pal[53 * 3:53 * 3 + 3]), (0xee, 0x33, 0x00))
            self.assertEqual(tuple(pal[50 * 3:50 * 3 + 3]), (0xcc, 0x00, 0x00))
            red = lambda i: tuple(pal[i * 3:i * 3 + 3])
            self.assertEqual(red(after[123, 125]), (0x55, 0x00, 0x00))   # costume darkest
            self.assertEqual(red(after[121, 125]), (0x88, 0x00, 0x00))
            # the scenery of the shared entries and the alien keep their entry and colour
            self.assertTrue((after[100:110, 300:310] == 47).all() and (after[110:120, 300:310] == 43).all())
            self.assertTrue((after[60:70, 200:210] == 37).all())
            self.assertTrue((after[130:145, 165:180] == 26).all())          # the costume's yellow stays as the artist drew it
            self.assertTrue((after[130:140, 300:310] == 26).all())          # so does the hazard stripe
            self.assertEqual(red(37), (0x33, 0x44, 0x33))
            # frames 1 and 2 are copies
            for n in names[:2]:
                a = np.array(Image.open(src / n))
                b = np.array(Image.open(out / n.replace(".png", "_red.png")))
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
            self.assertTrue(all((out / n.replace(".png", "_red.png")).exists() for n in names))


@unittest.skipIf(np is None, "numpy and Pillow are needed")
class PackTest(unittest.TestCase):
    def test_committed_art_reproduces(self):
        art = ROOT / "art/wolverine-reveal"
        frames = [art / n for n in ("frame1_closed_red.png", "frame2_opening_red.png", "frame3_burst_red.png")]
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


@unittest.skipIf(np is None, "numpy and Pillow are needed")
class VoiceFileTest(unittest.TestCase):
    def test_intro_file(self):
        """the reveal's voice file from a (synthetic) wv-sounds asset directory: header, level, octave, samples, even length"""
        import json
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            blob = bytes((i * 7) & 0xff for i in range(100)) + bytes(range(1, 52))
            (d / "wv_sound.bin").write_bytes(blob)
            (d / "wv_sound.json").write_text(json.dumps({"rate": 11025, "sounds": [
                {"name": "SELECT", "cmd": 538, "off": 0, "n": 100, "tl": 44},
                {"name": "INTRO", "cmd": 519, "off": 100, "n": 51, "tl": 42}]}))
            out = d / "v.bin"
            rep = reveal_voice.intro(d, out)
            b = out.read_bytes()
            self.assertEqual((rep["command"], rep["samples"]), ("0x207", 52))
            self.assertEqual(b[:4], b"RVV1")
            self.assertEqual(struct.unpack(">I", b[4:8])[0], 52)
            self.assertEqual((b[8], b[9]), (42, 0xe))                  # SCSP total level, octave nibble: 11025 Hz
            self.assertEqual(b[16:16 + 51], blob[100:151])
            self.assertEqual(len(b), 16 + 52)


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
