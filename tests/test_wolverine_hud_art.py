"""Guest select screen and HUD art (tools/wolverine/hud_art.py, saturn/rt/guests.c): synthetic HOST tests, no ROM input.
One extra test runs on the real delivery and the real graphics region when they are on this PC (skipped otherwise)."""
import importlib.util
import json
import os
import pathlib
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools/wolverine"))
import satgfx_pack  # noqa: E402
import hud_art  # noqa: E402

try:
    from PIL import Image
except ImportError:   # pragma: no cover
    Image = None

SLOT = "schaefer"
RAW_SIZE = 0x800000 + 0x2e0000
ROM_SIZE = 0x200000


def portrait_palette(rng):
    return [(0, 0, 0)] + [tuple(17 * rng.randrange(16) for _ in range(3)) for _ in range(15)]


def make_png(path, size, pal16, pens_used, rng, transparent=0.2):
    im = Image.new("P", size)
    flat = []
    for rgb in pal16:
        flat += list(rgb)
    im.putpalette(flat + [0] * (768 - len(flat)))
    px = im.load()
    for y in range(size[1]):
        for x in range(size[0]):
            px[x, y] = 0 if rng.random() < transparent else rng.choice(pens_used) + 1
    im.save(path)


def make_art(d, rng, name_pal=None):
    """A synthetic delivery: the five PNGs on the artist's conventions, pens drawn at random from each piece's allowed set."""
    d = pathlib.Path(d)
    ppal = portrait_palette(rng)
    spec = hud_art.SLOTS[SLOT]
    plate_pal = [(0, 0, 0)] * 16
    plate_pal[1] = (255, 255, 255)
    for i in range(10, 15):
        plate_pal[i] = tuple(17 * rng.randrange(16) for _ in range(3))
    name_pal = name_pal or ([(0, 0, 0)] * 16)
    make_png(d / spec["select_portrait"]["png"], (128, 64), ppal, list(spec["select_portrait"]["pens"]), rng, 0.0)
    make_png(d / spec["select_plate"]["png"], (160, 24), plate_pal, list(spec["select_plate"]["pens"]), rng)
    make_png(d / spec["hud_portrait"]["png"], (24, 16), ppal, list(spec["hud_portrait"]["pens"]), rng)
    shutil.copyfile(d / spec["hud_portrait"]["png"], d / spec["rank_icon"]["png"])
    make_png(d / spec["hud_name"]["png"], (88, 16), name_pal, list(spec["hud_name"]["pens"]), rng)


def make_world(d, seed=1):
    """Art, graphics region (random bytes, so a stray write shows) and a ROM image holding the palette tables at the arcade's addresses."""
    rng = random.Random(seed)
    d = pathlib.Path(d)
    art = d / "art"
    art.mkdir()
    gfx = bytes(rng.randrange(256) for _ in range(RAW_SIZE))
    rom = bytearray(rng.randrange(256) for _ in range(ROM_SIZE))
    # the shared name bank: seven pens the name uses, in the PNG as in the ROM
    bank = {p: 17 * rng.randrange(1, 16) for p in (1, 2, 3, 4, 5, 6, 8)}
    name_pal = [(0, 0, 0)] * 16
    for p, v in bank.items():
        name_pal[p + 1] = (v, 17 * ((v // 17 + p) % 16), 255 - v)
        words = (name_pal[p + 1][0] // 17) << 8 | (name_pal[p + 1][1] // 17) << 4 | name_pal[p + 1][2] // 17
        rom[0x1ee2e0 + p * 2:0x1ee2e0 + p * 2 + 2] = bytes([words >> 8, words & 255])
    make_art(art, rng, name_pal)
    for sets in hud_art.PALETTES[SLOT]:
        orig = [rng.randrange(0x1000) for _ in range(15)]
        for at, tag in zip(sets["at"], sets["tags"]):
            for p, w in enumerate(orig):
                rom[at + p * 2:at + p * 2 + 2] = bytes([w >> 8, w & 255])
            rom[at + 30:at + 32] = bytes([tag >> 8, tag & 255])
    (d / "base.bin").write_bytes(gfx)
    (d / "rom.bin").write_bytes(bytes(rom))
    return art, d / "base.bin", d / "rom.bin", gfx, bytes(rom)


def expected_tile(pens, spec, r, c):
    n = spec["cell"]
    tile = [row[c * n:(c + 1) * n] for row in pens[r * n:(r + 1) * n]]
    return [t[::-1] for t in tile] if spec.get("flip") else tile   # a flipped piece is stored mirrored


def parities(spec, c):
    """The halves of a code block a piece's cell is written to (`both`: the arcade holds the same cell in both)."""
    return (0, 1) if spec.get("both") else ((spec["parity0"] + c) & 1,)


@unittest.skipIf(Image is None, "Pillow is needed")
class ConverterTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.d = pathlib.Path(self._t.name)
        self.art, self.base, self.rom, self.gfx, self.romb = make_world(self.d)
        self.out = self.d / "out"

    def tearDown(self):
        self._t.cleanup()

    def test_tiles_round_trip_through_the_packer(self):
        """Every converted tile decodes, through the packer's own payload(), to the PNG's pixels (pen 15 transparent); nothing else is written."""
        r = hud_art.build(self.art, self.base, self.rom, self.out)
        pieces = hud_art.load_slot(self.art, SLOT)
        spec = hud_art.SLOTS[SLOT]
        for which in ("stage", "front"):
            data = pathlib.Path(r[which + "_gfx"]).read_bytes()
            touched = set()
            for name, s in spec.items():
                if "same_as" in s:
                    continue
                n = s["cell"]
                w, h = s["size"]
                inplay = s.get(which)
                for row in range(h // n):
                    for col in range(w // n):
                        code = s["code"](row, col)
                        tile = expected_tile(pieces[name]["pens"], s, row, col)
                        if s["layer"] == 2:
                            pl, vis = satgfx_pack.payload(data, 2, code)
                            want = satgfx_pack.cells16(tile)
                            span = range(0x800000 + code * 0x80, 0x800000 + code * 0x80 + 0x80)
                            if inplay:
                                touched.update(span)
                        else:
                            for parity in parities(s, col):
                                pl, vis = satgfx_pack.payload(data, 1, code << 1 | parity)
                                want = satgfx_pack.tex(tile)
                                span = [0x800000 + code * 0x40 + y * 8 + parity * 4 + k for y in range(8) for k in range(4)]
                                if inplay:
                                    touched.update(span)
                                    self.assertEqual(pl, want, "%s tile %04x half %d (%s)" % (name, code, parity, which))
                                    self.assertEqual(vis, any(p != 15 for row_ in tile for p in row_))
                                else:
                                    base_pl, _ = satgfx_pack.payload(self.gfx, 1, code << 1 | parity)
                                    self.assertEqual(pl, base_pl, "%s must not change in the %s region" % (name, which))
                            continue
                        if inplay:
                            self.assertEqual(pl, want, "%s tile %04x (%s)" % (name, code, which))
                            self.assertEqual(vis, any(p != 15 for row_ in tile for p in row_))
                        else:
                            base_pl, _ = satgfx_pack.payload(self.gfx, 2, code)
                            self.assertEqual(pl, base_pl, "%s must not change in the %s region" % (name, which))
            # outside the written bytes the region is the original, byte for byte
            diff = [i for i in range(len(self.gfx)) if data[i] != self.gfx[i]]
            self.assertTrue(set(diff) <= touched)
            self.assertGreater(len(diff), 100)

    def test_stage_and_front_hold_the_right_pieces(self):
        r = hud_art.build(self.art, self.base, self.rom, self.out)
        stage, front = (pathlib.Path(r[k]).read_bytes() for k in ("stage_gfx", "front_gfx"))
        def block(data, code, sec):
            return data[0x800000 + code * (0x80 if sec == 2 else 0x40):][:0x80 if sec == 2 else 0x40]
        # select picture and plate only in the front file; HUD name only in the stage files; HUD portrait (and so the ranking icon) in both
        self.assertEqual(block(stage, 0x2c20, 2), block(self.gfx, 0x2c20, 2))
        self.assertNotEqual(block(front, 0x2c20, 2), block(self.gfx, 0x2c20, 2))
        self.assertEqual(block(stage, 0x0e30, 1), block(self.gfx, 0x0e30, 1))
        self.assertNotEqual(block(front, 0x0e30, 1), block(self.gfx, 0x0e30, 1))
        self.assertEqual(block(front, 0x0be0, 1), block(self.gfx, 0x0be0, 1))
        self.assertNotEqual(block(stage, 0x0be0, 1), block(self.gfx, 0x0be0, 1))
        self.assertEqual(block(front, 0x1ae6, 1), block(stage, 0x1ae6, 1))
        self.assertNotEqual(block(front, 0x1ae6, 1), block(self.gfx, 0x1ae6, 1))

    def test_talk_face_is_cropped_from_the_select_portrait_and_drawn_flipped(self):
        """The story box's face: 5x3 cells at codes 0xfbd-c + 16 r, stored mirrored in both halves of each code block, in the stage files only,
        on the portrait's own colours, and a PNG of its own in the art directory replaces the crop."""
        r = hud_art.build(self.art, self.base, self.rom, self.out)
        stage, front = (pathlib.Path(r[k]).read_bytes() for k in ("stage_gfx", "front_gfx"))
        pieces = hud_art.load_slot(self.art, SLOT)
        face = pieces["talk_face"]
        self.assertTrue(face["derived"])
        self.assertEqual((len(face["pens"][0]), len(face["pens"])), (40, 24))
        portrait = {p for row in pieces["select_portrait"]["pens"] for p in row}
        self.assertTrue({p for row in face["pens"] for p in row} <= portrait)   # nothing outside the portrait's colours; none transparent
        self.assertNotIn(15, {p for row in face["pens"] for p in row})
        fp = hud_art.TALK_FACE_FRAME_PEN   # the arcade's faces carry a 1 pixel white frame in their tiles
        self.assertTrue(all(p == fp for p in face["pens"][0] + face["pens"][-1]) and all(r[0] == fp and r[-1] == fp for r in face["pens"]))
        # mirrored by default (he faces the text); the constant turns it off and the inside of the frame is then the exact mirror
        self.assertTrue(hud_art.TALK_FACE_MIRROR)
        hud_art.TALK_FACE_MIRROR = False
        try:
            plain = hud_art.load_slot(self.art, SLOT)["talk_face"]["pens"]
        finally:
            hud_art.TALK_FACE_MIRROR = True
        self.assertEqual([r[1:-1] for r in face["pens"][1:-1]], [r[1:-1][::-1] for r in plain[1:-1]])
        spec = hud_art.SLOTS[SLOT]["talk_face"]
        for row in range(3):
            for col in range(5):
                code = 0xfbd - col + 16 * row
                self.assertEqual(spec["code"](row, col), code)
                cell = [face["pens"][row * 8 + y][col * 8:(col + 1) * 8] for y in range(8)]
                for half in (0, 1):
                    pl, _ = satgfx_pack.payload(stage, 1, code << 1 | half)
                    self.assertEqual(pl, satgfx_pack.tex([c[::-1] for c in cell]))   # the box flips it back on draw
                    base_pl, _ = satgfx_pack.payload(self.gfx, 1, code << 1 | half)
                    self.assertEqual(satgfx_pack.payload(front, 1, code << 1 | half)[0], base_pl)   # front end file keeps the arcade's face
        # an artist's PNG of the right size and colours wins over the crop
        im = Image.new("P", (40, 24), 0)
        im.putpalette(Image.open(self.art / hud_art.SLOTS[SLOT]["hud_portrait"]["png"]).getpalette())
        for y in range(24):
            for x in range(40):
                im.putpixel((x, y), 1 + (x + y) % 15)
        im.save(self.art / spec["png"])
        pieces2 = hud_art.load_slot(self.art, SLOT)
        self.assertNotIn("derived", pieces2["talk_face"])
        self.assertEqual(pieces2["talk_face"]["pens"][3][5], (5 + 3) % 15)
        # colours must be the HUD portrait's
        pal = Image.open(self.art / spec["png"]).getpalette()
        pal[3 * 2] ^= 17
        im2 = Image.open(self.art / spec["png"])
        im2.putpalette(pal)
        im2.save(self.art / spec["png"])
        with self.assertRaisesRegex(ValueError, "HUD portrait's 15 colours"):
            hud_art.load_slot(self.art, SLOT)

    def test_base_region_is_never_written(self):
        before = self.base.read_bytes()
        hud_art.build(self.art, self.base, self.rom, self.out)
        self.assertEqual(self.base.read_bytes(), before)

    def test_palette_words_and_include(self):
        r = hud_art.build(self.art, self.base, self.rom, self.out)
        pieces = hud_art.load_slot(self.art, SLOT)
        sets = hud_art.palette_sets(SLOT, 0, pieces, self.romb)
        self.assertEqual([len(s["at"]) for s in sets], [3, 1, 22])
        for s in sets:
            for q in range(15):
                if s["mask"] >> q & 1:
                    self.assertEqual(s["neu"][q], pieces[s["piece"]]["words"][q])
                else:
                    self.assertEqual(s["neu"][q], s["orig"][q])   # the plate keeps the arcade's pens it does not draw with
        self.assertEqual(sets[1]["mask"], 0x3e01)
        self.assertEqual(sets[0]["mask"], 0x7fff)
        text = pathlib.Path(r["include"]).read_text()
        self.assertIn("#define GUEST_PAL_N 3", text)
        self.assertEqual(hud_art.cps_word((204, 51, 51)), 0xc33)   # the brief's #cc3333: CPS word 0xfc33 without the brightness nibble
        self.assertEqual(hud_art.cps_word((255, 238, 102)), 0xfe6)
        self.assertEqual(hud_art.pen(0), 15)
        self.assertEqual(hud_art.pen(1), 0)
        self.assertEqual(hud_art.pen(15), 14)

    def test_no_art_is_an_empty_table(self):
        text = hud_art.pal_include([])
        self.assertIn("#define GUEST_PAL_N 0", text)

    def test_rejects_bad_art(self):
        spec = hud_art.SLOTS[SLOT]
        # a pen the piece may not use (the shared name bank has pens 1 to 6 and 8 only)
        im = Image.open(self.art / spec["hud_name"]["png"])
        im.putpixel((10, 8), 8 + 1 + 1)   # PNG index 10 = pen 9
        im.save(self.art / spec["hud_name"]["png"])
        with self.assertRaisesRegex(ValueError, "not allowed"):
            hud_art.build(self.art, self.base, self.rom, self.out)

    def test_rejects_a_ranking_icon_of_its_own(self):
        spec = hud_art.SLOTS[SLOT]
        im = Image.open(self.art / spec["rank_icon"]["png"])
        im.putpixel((8, 8), (im.getpixel((8, 8)) % 15) + 1)
        im.save(self.art / spec["rank_icon"]["png"])
        with self.assertRaisesRegex(ValueError, "ranking table draws"):
            hud_art.build(self.art, self.base, self.rom, self.out)

    def test_rejects_name_colours_that_differ_from_the_shared_bank(self):
        rom = bytearray(self.romb)
        rom[0x1ee2e0 + 2 * 3] ^= 0x0f
        (self.d / "rom2.bin").write_bytes(bytes(rom))
        with self.assertRaisesRegex(ValueError, "shared bank"):
            hud_art.build(self.art, self.base, self.d / "rom2.bin", self.out)

    def test_rejects_rom_copies_that_differ(self):
        rom = bytearray(self.romb)
        rom[0x105660 + 4] ^= 1
        (self.d / "rom2.bin").write_bytes(bytes(rom))
        with self.assertRaisesRegex(ValueError, "differs from the first"):
            hud_art.build(self.art, self.base, self.d / "rom2.bin", self.out)

    def test_rejects_wrong_size_and_unaligned_colours(self):
        spec = hud_art.SLOTS[SLOT]
        Image.new("P", (8, 8)).save(self.art / spec["hud_portrait"]["png"])
        with self.assertRaisesRegex(ValueError, "expected 24x16"):
            hud_art.build(self.art, self.base, self.rom, self.out)
        with self.assertRaisesRegex(ValueError, "multiple of 17"):
            hud_art.cps_word((18, 0, 0))

    def test_key_check_names_tiles_no_file_holds(self):
        have = set()
        spec = hud_art.SLOTS[SLOT]
        for name, s in spec.items():
            if "same_as" in s or s["layer"] != 1:
                continue
            for r in range(s["size"][1] // 8):
                for c in range(s["size"][0] // 8):
                    for par in parities(s, c):
                        have.add(s["code"](r, c) << 1 | par)
        s2 = {spec["select_portrait"]["code"](r, c) for r in range(4) for c in range(8)}
        rounds = dict(files=[dict(keys=[[], sorted(have), sorted(s2), []])])
        self.assertEqual(hud_art.check_keys(rounds, SLOT), [])
        have.discard(0x0be0 << 1 | 1)
        rounds = dict(files=[dict(keys=[[], sorted(have), sorted(s2), []])])
        self.assertEqual(hud_art.check_keys(rounds, SLOT), [("hud_name", "s1", 0x0be0 << 1 | 1)])


class GuestRoundsTest(unittest.TestCase):
    def test_front_file_and_stage_gfx_only_with_art(self):
        spec = importlib.util.spec_from_file_location("guest_rounds_t", ROOT / "tools/wolverine/guest_rounds.py")
        gr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gr)
        class Data:
            def __init__(self, path):
                self.own = {2: {7}}
        fake = type(sys)("rounds_variants")
        fake.Data = Data
        old = sys.modules.get("rounds_variants")
        sys.modules["rounds_variants"] = fake
        saved = os.environ.get("GFX_BIN")
        try:
            def rounds():
                files = [dict(name="front", stages=[0], keys=[[1, 7], [], [], []], sound=[], keep_pages=[])]
                table = {}
                for st in (2, 4):
                    row = [len(files)] + [0] * 3
                    files.append(dict(name="stage%02x" % st, stages=[st], keys=[[1, 7], [], [], []], keep_pages=[]))
                    for v in (1, 2, 3):
                        row[v] = len(files)
                        files.append(dict(files[-1], name="stage%02x_m%d" % (st, v)))
                    table[str(st)] = row
                return dict(files=files, variant_masks=[1, 2, 3], variant_file=table, stage_file={}, page=1024)
            with tempfile.TemporaryDirectory() as td:
                (pathlib.Path(td) / "remap.json").write_text(json.dumps(dict(stage_keys={}, keys=[100, 101])))
                plain = gr.extend(rounds(), td)
                self.assertNotIn("0", plain["guest_files"]["0"])
                self.assertTrue(all("gfx" not in f for f in plain["files"]))
                n = len(plain["files"])
                art = gr.extend(rounds(), td, dict(stage_gfx="S.bin", front_gfx="F.bin"))
                self.assertEqual(len(art["files"]), n + 1)
                front = art["files"][-1]
                self.assertEqual((front["name"], front["gfx"], front["audio_from"], front["stages"]), ("front_wv", "F.bin", 0, [0]))
                self.assertEqual(art["guest_files"]["0"]["0"], [n] + [0] * 3)
                wv = [f for f in art["files"] if f["name"].endswith("_wv") and f["name"] != "front_wv"]
                self.assertTrue(wv and all(f["gfx"] == "S.bin" for f in wv))
                # arcade files are the same dictionaries as without art: their graphics region is the build's
                self.assertTrue(all("gfx" not in f for f in art["files"] if not f["name"].endswith("_wv")))
                self.assertEqual([f for f in art["files"][:n] if not f["name"].endswith("_wv")], [f for f in plain["files"] if not f["name"].endswith("_wv")])
        finally:
            if old is None:
                sys.modules.pop("rounds_variants", None)
            else:
                sys.modules["rounds_variants"] = old
            if saved is None:
                os.environ.pop("GFX_BIN", None)
            else:
                os.environ["GFX_BIN"] = saved


@unittest.skipUnless(shutil.which("gcc"), "gcc is needed for HOST C regressions")
class RuntimeSelectionTest(unittest.TestCase):
    def test_front_selection_off_identity_and_palette_writes(self):
        sets = [
            dict(guest=1, mask=0x7fff, neu=[0x300 + i for i in range(15)], orig=[0x200 + i for i in range(15)], at=[0x1000, 0x3000]),
            dict(guest=1, mask=0x0201, neu=[0x400] + [0x200 + i for i in range(1, 15)], orig=[0x200 + i for i in range(15)], at=[0x2000]),
        ]
        sets[1]["neu"][9] = 0x409
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            (td / "guest_hudpal.inc").write_text(hud_art.pal_include(sets))
            rows = [[[0] * 3 for _ in range(5)] for _ in range(2)]
            rows[0][0][0] = 40
            rows[0][3][1] = 41
            rows[0][3][2] = 42
            (td / "guest_files.inc").write_text("#define GUEST_ROWS 2\nstatic const unsigned short guest_file[2][5][3] = {%s};\n" % ",".join(
                "{" + ",".join("{" + ",".join(map(str, v)) + "}" for v in g) + "}" for g in rows))
            exe = td / "t"
            subprocess.run(["gcc", "-std=gnu99", "-Wall", "-O1", "-I" + str(td), "-I" + str(ROOT / "saturn/rt"),
                            str(ROOT / "tests/wolverine_hud_guest_test.c"), str(ROOT / "saturn/rt/guests.c"), "-o", str(exe)], check=True)
            out = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stdout)
            self.assertIn("passed", out.stdout)


REAL_ART = pathlib.Path("E:/AvP/learning/wolverine-artist-20261109/zip/wolverine_hud_assets/assets")
REAL_GFX = pathlib.Path("E:/AvP/learning/lane-wolverine-v4/v41/D/gfx_wolverine.bin")
REAL_ROM = pathlib.Path("E:/AvP/learning/lane-wolverine-v4/work5/rt.bin")


@unittest.skipUnless(Image is not None and REAL_ART.is_dir() and REAL_GFX.is_file() and REAL_ROM.is_file(), "the artist's delivery and the work files are not here")
class RealArtTest(unittest.TestCase):
    def test_delivery_round_trips_and_leaves_the_shared_name_bank_alone(self):
        with tempfile.TemporaryDirectory() as td:
            r = hud_art.build(REAL_ART, REAL_GFX, REAL_ROM, td)
            base = REAL_GFX.read_bytes()
            spec = hud_art.SLOTS[SLOT]
            pieces = hud_art.load_slot(REAL_ART, SLOT)
            for which in ("stage", "front"):
                data = pathlib.Path(r[which + "_gfx"]).read_bytes()
                for name, s in spec.items():
                    if "same_as" in s or not s.get(which):
                        continue
                    n = s["cell"]
                    for row in range(s["size"][1] // n):
                        for col in range(s["size"][0] // n):
                            code = s["code"](row, col)
                            tile = expected_tile(pieces[name]["pens"], s, row, col)
                            if s["layer"] == 2:
                                pl, _ = satgfx_pack.payload(data, 2, code)
                                self.assertEqual(pl, satgfx_pack.cells16(tile))
                            else:
                                for par in parities(s, col):
                                    pl, _ = satgfx_pack.payload(data, 1, code << 1 | par)
                                    self.assertEqual(pl, satgfx_pack.tex(tile))
            # Schaefer's own pieces are still what they were in the unpatched region, which the arcade files keep using
            self.assertNotEqual(base, pathlib.Path(r["stage_gfx"]).read_bytes())
            rom = REAL_ROM.read_bytes()
            self.assertEqual(hud_art.rom_words(rom, 0x1ee2e0)[1], 0xffa)   # bank 0x27 pen 1 is what the name's PNG says


if __name__ == "__main__":
    unittest.main()
