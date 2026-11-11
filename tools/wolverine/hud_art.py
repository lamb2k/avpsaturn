#!/usr/bin/env python
"""Guest select-screen and HUD art, converted offline (lane wolverine-art, 2026-11-09).

A guest takes an AvP character's slot, and the arcade draws that character's select-screen picture, name plate and HUD portrait and name
as tile art. This module turns an artist's indexed PNGs into the same tiles at the slot character's own tile codes, so the arcade's own
maps draw them with no new code, and into the colour changes that go with them:

  tiles    patched into a copy of the graphics region (gfx_wolverine.bin): one copy for the guest's stage files (HUD portrait and name), one
           for the guest's front end file (select picture and plate, and the HUD portrait the ranking table reuses). Files built from the
           original region (every arcade file) are untouched, so a guest that is off changes nothing.
  colours  guest_hudpal.inc, read by saturn/rt/guests.c (guest_pal.h): the arcade loads these palettes from tables in its program ROM
           image; while the guest's art files are the loaded ones, the guest's words are written over the tables' pens, else the originals.

Talk box face (2026-11-09, lane wv-talkbox): the story box's speaker picture is a 40x24 face of 5x3 scroll 1 cells (codes 0xfb9-0xfbd, 0xfc9-0xfcd,
0xfd9-0xfdd, palette bank 0x13, drawn x-flipped; both halves of every code block hold the same cell). It is cropped and shrunk from the approved
select portrait (TALK_FACE_CROP) onto the same 15 colours, or read from wolverine_talk_face_40x24.png when the artist supplies one.

PNG convention (the artist's, checked here): index 0 = transparent = arcade pen 15; index n = pen n - 1; colours are multiples of 17.
The name's palette (bank 0x27) is shared by every character, so that piece only maps its indices to the bank's existing pens and
never changes a colour. Mega Man (Predator Hunter's slot) needs the same four pieces: add a SLOTS entry and a GUESTS row.

ROM-derived output (the patched regions, the generated include) stays in the build's work directory, never in git. The artist's PNGs are
not in git either (their lettering was recovered from the game's own plates): a build reads them from GUEST_HUD_ART, or from
GUEST_ASSETS/hud_art, and a build without them is exactly the build without this feature.

usage: hud_art.py build ART_DIR BASE_GFX ROM OUT_DIR   writes OUT_DIR/gfx_hud_stage.bin, gfx_hud_front.bin, guest_hudpal.inc and a report
       hud_art.py preview ART_DIR BASE_GFX ROM OUT.png   what the converted tiles and colours draw (nearest neighbour, for review)
"""
import hashlib
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import satgfx_pack

SCROLL_BASE = 0x800000   # scroll tiles in the graphics region (satgfx_pack.payload)
# The talk box face is this box of the 128x64 select portrait (x, y, w, h) shrunk to 38x22 (the whole head and shoulders: head x 32-108, y 10-57),
# area average to the nearest of the portrait's own colours, inside the arcade's 1 pixel white frame (pen 1, the portrait's white; every arcade face
# has it in its tiles). The approved portrait looks left, as in the select screen; the talk box shows him facing the text like Schaefer's face does,
# so the crop is mirrored (owner 2026-11-10: "mirror the talk-box portrait so he faces the text like Schaefer"). TALK_FACE_MIRROR = False restores it.
TALK_FACE_CROP = (20, 8, 88, 50.9)
TALK_FACE_FRAME_PEN = 1
TALK_FACE_MIRROR = True


# One slot's pieces. code(r, c): scroll tile code of the picture's tile row r, column c. cell: tile size in pixels. parity0: scroll 1 draws
# the left or right half of a code's 16x8 block by the map column's parity; the arcade's map puts this piece's first column at that parity
# (checked against a build's own key lists by `check_keys`). pens: the pens the piece may use (pen 15, PNG index 0, is always allowed).
PORTRAIT_PENS = tuple(range(15))
SLOTS = {
    "schaefer": {
        "select_portrait": dict(png="wolverine_select_portrait_128x64.png", size=(128, 64), cell=16, layer=2, parity0=0,
                                code=lambda r, c: 0x2c20 + r * 8 + c, pens=PORTRAIT_PENS, front=True, stage=False),
        "select_plate": dict(png="wolverine_select_plate_160x24.png", size=(160, 24), cell=8, layer=1, parity0=1,
                             code=lambda r, c: (0x0e30 + r * 16 + c) if c < 16 else (0x0f30 + r * 16 + c - 16),
                             pens=(0, 9, 10, 11, 12, 13), front=True, stage=False),
        "hud_portrait": dict(png="wolverine_hud_portrait_24x16.png", size=(24, 16), cell=8, layer=1, parity0=0,
                             code=lambda r, c: 0x1ae6 + r * 16 + c, pens=PORTRAIT_PENS, front=True, stage=True),
        "hud_name": dict(png="wolverine_hud_name_88x16.png", size=(88, 16), cell=8, layer=1, parity0=1,
                         code=lambda r, c: 0x0be0 + r * 16 + c, pens=(1, 2, 3, 4, 5, 6, 8), front=False, stage=True,
                         shared_palette=0x1ee2e0),
        # The story box's face (and the 2P HUD's, unflipped): the stored cells are mirrored, the box draws them x-flipped in descending code order.
        # `derive`: no PNG of its own, cropped from another piece (TALK_FACE_CROP of the select portrait) unless the art directory has the PNG.
        # `both`: the arcade holds the same cell in both halves of a code block, so the key's column parity does not matter; so does the copy.
        "talk_face": dict(png="wolverine_talk_face_40x24.png", size=(40, 24), cell=8, layer=1, parity0=0, flip=True, both=True,
                          derive="select_portrait", code=lambda r, c: 0xfbd - c + r * 16, pens=PORTRAIT_PENS, front=False, stage=True),
        # The ranking table draws the HUD portrait's own tiles (checked on the arcade's pictures: the icon is the portrait, two pixels
        # over), so the ranking icon is a copy of piece C and carries no tiles of its own.
        "rank_icon": dict(png="wolverine_rank_icon_24x16.png", size=(24, 16), same_as="hud_portrait"),
    },
}
# Palette tables in the program ROM image: 32 bytes each, pens 0 to 14 as 0RGB words, then a tag word (page << 8 | bank).
STAGE_PAGES = [0x100660 + 0x1000 * k for k in range(20)]   # each stage's scroll 1 palette page, bank 0x13
PALETTES = {
    "schaefer": [
        dict(piece="select_portrait", at=[0x1f0a60, 0x1f1340, 0x1f6ac0], tags=[0x0903, 0x0b0a, 0x00e6]),
        dict(piece="select_plate", at=[0x1ee340], tags=[0x000a]),
        dict(piece="hud_portrait", at=[0x1ee460, 0x1f0640] + STAGE_PAGES, tags=[0x0013, 0x0802] + [0x0113] * 20),
    ],
}
# Guest row of saturn/rt/guests.c -> the slot it takes and the folder of its art under the art directory.
GUESTS = {0: "schaefer"}


def read_png(path):
    """(width, height, rows of palette indices, 16 (r, g, b) entries)."""
    from PIL import Image
    im = Image.open(path)
    if im.mode != "P":
        raise ValueError("%s: not an indexed PNG (mode %s)" % (path, im.mode))
    px = im.load()
    rows = [[px[x, y] for x in range(im.width)] for y in range(im.height)]
    if max(max(r) for r in rows) > 15:
        raise ValueError("%s: palette index above 15" % path)
    flat = im.getpalette() or []
    pal = [tuple(flat[i * 3:i * 3 + 3]) if len(flat) >= i * 3 + 3 else (0, 0, 0) for i in range(16)]
    return im.width, im.height, rows, pal


def pen(index):
    """PNG index -> arcade pen (index 0 is transparent, pen 15)."""
    return 15 if index == 0 else index - 1


def cps_word(rgb):
    """0RGB word of the program ROM, four bits a channel; the artist's colours are multiples of 17."""
    if any(c % 17 for c in rgb):
        raise ValueError("colour %s is not a multiple of 17" % (rgb,))
    return (rgb[0] // 17) << 8 | (rgb[1] // 17) << 4 | rgb[2] // 17


def shrink(src, crop, size):
    """Crop box (x, y, w, h) of a loaded piece shrunk by area averaging to size; each pixel takes the nearest of the piece's colours (never transparent)."""
    sw, sh = len(src["pens"][0]), len(src["pens"])
    ow, oh = size
    x0, y0, cw, ch = crop
    pal, pens = src["pal"], src["pens"]   # pen p is PNG colour p + 1
    out = []
    for oy in range(oh):
        row = []
        for ox in range(ow):
            xa, xb, ya, yb = x0 + ox * cw / ow, x0 + (ox + 1) * cw / ow, y0 + oy * ch / oh, y0 + (oy + 1) * ch / oh
            acc, tot = [0.0, 0.0, 0.0], 0.0
            for yy in range(int(ya), int(yb + 0.9999)):
                for xx in range(int(xa), int(xb + 0.9999)):
                    if not (0 <= xx < sw and 0 <= yy < sh) or pens[yy][xx] == 15:
                        continue
                    wt = max(0.0, min(xb, xx + 1) - max(xa, xx)) * max(0.0, min(yb, yy + 1) - max(ya, yy))
                    c = pal[pens[yy][xx] + 1]
                    for k in range(3):
                        acc[k] += c[k] * wt
                    tot += wt
            if tot == 0:
                raise ValueError("talk face crop %s has no opaque pixel at %d,%d" % (crop, ox, oy))
            a = [v / tot for v in acc]
            row.append(min(range(15), key=lambda p: (sum((pal[p + 1][k] - a[k]) ** 2 for k in range(3)), p)))
        out.append(row)
    return out


def load_piece(art, name, spec):
    """Validated pixels of one piece: rows of pens, and its palette words by pen."""
    w, h, rows, pal = read_png(pathlib.Path(art) / spec["png"])
    if (w, h) != spec["size"]:
        raise ValueError("%s: %dx%d, expected %dx%d" % (spec["png"], w, h, *spec["size"]))
    pens = [[pen(i) for i in r] for r in rows]
    bad = sorted({p for r in pens for p in r if p != 15 and p not in spec["pens"]})
    if bad:
        raise ValueError("%s: pens %s are not allowed for %s (allowed %s)" % (spec["png"], bad, name, list(spec["pens"])))
    words = {p: cps_word(pal[p + 1]) for p in range(15)} if "shared_palette" not in spec else {}
    return dict(pens=pens, words=words, pal=pal)


def planes(row8):
    """Eight pens -> the four bit plane bytes of the graphics region (inverse of satgfx_pack.pens)."""
    b = [0, 0, 0, 0]
    for x, p in enumerate(row8):
        for k in range(4):
            if p >> k & 1:
                b[k] |= 0x80 >> x
    return bytes(b)


def put_scroll1(raw, code, parity, tile):
    """An 8x8 tile of pens as the left (parity 0) or right half of scroll 1 code's 16x8 block."""
    base = SCROLL_BASE + code * 0x40
    for y in range(8):
        at = base + y * 8 + parity * 4
        raw[at:at + 4] = planes(tile[y])


def put_scroll2(raw, code, tile):
    """A 16x16 tile of pens as scroll 2 code."""
    base = SCROLL_BASE + code * 0x80
    for y in range(16):
        for g in range(2):
            at = base + y * 8 + g * 4
            raw[at:at + 4] = planes(tile[y][g * 8:g * 8 + 8])


def cells(name, spec, pens):
    """(code, parity or None, tile) for every tile of a piece. `flip`: the stored cell is the picture's cell mirrored (the arcade draws it
    x-flipped); `both`: the cell is written to both halves of its code block."""
    n = spec["cell"]
    w, h = spec["size"]
    for r in range(h // n):
        for c in range(w // n):
            tile = [row[c * n:(c + 1) * n] for row in pens[r * n:(r + 1) * n]]
            if spec.get("flip"):
                tile = [t[::-1] for t in tile]
            if spec.get("both"):
                for par in (0, 1):
                    yield spec["code"](r, c), par, tile
            else:
                yield spec["code"](r, c), (spec["parity0"] + c) & 1 if spec["layer"] == 1 else None, tile


def patch(raw, slot, pieces, which):
    """Copy of the graphics region with the pieces of `which` ('front' or 'stage') written at the slot character's tile codes."""
    out = bytearray(raw)
    written = {}
    for name, spec in SLOTS[slot].items():
        if "same_as" in spec or not spec.get(which):
            continue
        for code, par, tile in cells(name, spec, pieces[name]["pens"]):
            k = (spec["layer"], code, par)
            if k in written:
                raise ValueError("%s: tile %04x written twice (also by %s)" % (name, code, written[k]))
            written[k] = name
            if spec["layer"] == 2:
                put_scroll2(out, code, tile)
            else:
                put_scroll1(out, code, par, tile)
    return out


def check_pieces(slot, pieces):
    """Palettes shared between pieces must agree; the rank icon must be the HUD portrait."""
    spec = SLOTS[slot]
    for name, s in spec.items():
        if "same_as" in s:
            a, b = pieces[name], pieces[s["same_as"]]
            if a["pens"] != b["pens"] or [a["pal"][i] for i in range(16)] != [b["pal"][i] for i in range(16)]:
                raise ValueError("%s differs from %s: the ranking table draws the HUD portrait's tiles, so it cannot have its own" % (name, s["same_as"]))
    p, c = pieces["select_portrait"], pieces["hud_portrait"]
    if p["words"] != c["words"]:
        raise ValueError("select portrait and HUD portrait must use the same 15 colours in the same order")
    if "talk_face" in pieces and pieces["talk_face"]["words"] != c["words"]:
        raise ValueError("talk face must use the HUD portrait's 15 colours (it draws in the same palette bank)")


def rom_words(rom, at):
    return list(struct.unpack(">15H", rom[at:at + 30]))


def palette_sets(slot, guest, pieces, rom):
    """Palette tables to rewrite: the guest's words, the arcade's, and every ROM copy (all must hold the same arcade words and the tags expected)."""
    sets = []
    for p in PALETTES[slot]:
        spec = SLOTS[slot][p["piece"]]
        pen_mask = sum(1 << q for q in spec["pens"])
        orig = rom_words(rom, p["at"][0])
        for at, tag in zip(p["at"], p["tags"]):
            if rom_words(rom, at) != orig:
                raise ValueError("%s: ROM copy at %06x differs from the first (%06x)" % (p["piece"], at, p["at"][0]))
            if struct.unpack(">H", rom[at + 30:at + 32])[0] != tag:
                raise ValueError("%s: ROM copy at %06x has tag %04x, expected %04x" % (p["piece"], at, struct.unpack(">H", rom[at + 30:at + 32])[0], tag))
        neu = [pieces[p["piece"]]["words"][q] if pen_mask >> q & 1 else orig[q] for q in range(15)]
        sets.append(dict(piece=p["piece"], guest=1 << guest, mask=pen_mask, neu=neu, orig=orig, at=list(p["at"])))
    return sets


def pal_include(sets):
    """C text for saturn/rt/guests.c; no sets gives the empty table the code expects."""
    out = ["/* Generated by tools/wolverine/hud_art.py: guest select screen and HUD palettes (ROM words 0RGB). ROM-derived; not in git. */"]
    if not sets:
        out += ["#define GUEST_PAL_N 0", "static const GuestPal guest_pal[1] = { { 0, 0, 0, 0, 0, 0 } };"]
        return "\n".join(out) + "\n"
    rows = []
    for i, s in enumerate(sets):
        out.append("static const unsigned short hudpal_new%d[15] = {%s};" % (i, ",".join("0x%03x" % w for w in s["neu"])))
        out.append("static const unsigned short hudpal_old%d[15] = {%s};" % (i, ",".join("0x%03x" % w for w in s["orig"])))
        out.append("static const unsigned long hudpal_at%d[%d] = {%s};" % (i, len(s["at"]), ",".join("0x%x" % a for a in s["at"])))
        rows.append("{ %d, 0x%04x, hudpal_new%d, hudpal_old%d, hudpal_at%d, %d }" % (s["guest"], s["mask"], i, i, i, len(s["at"])))
    out.append("#define GUEST_PAL_N %d" % len(sets))
    out.append("static const GuestPal guest_pal[GUEST_PAL_N] = {\n    %s\n};" % ",\n    ".join(rows))
    return "\n".join(out) + "\n"


def load_slot(art, slot):
    pieces = {}
    for name, spec in SLOTS[slot].items():
        if "same_as" in spec:   # the same pixels and colours, under its own file name
            spec = dict(SLOTS[slot][spec["same_as"]], png=spec["png"])
        if "derive" in spec and not (pathlib.Path(art) / spec["png"]).exists():
            continue   # cropped below, once its source is loaded
        pieces[name] = load_piece(art, name, spec)
    for name, spec in SLOTS[slot].items():
        if name not in pieces:
            src = pieces[spec["derive"]]
            w, h = spec["size"]
            inner = shrink(src, TALK_FACE_CROP, (w - 2, h - 2))
            if TALK_FACE_MIRROR:
                inner = [r[::-1] for r in inner]
            pens = [[TALK_FACE_FRAME_PEN] * w] + [[TALK_FACE_FRAME_PEN] + r + [TALK_FACE_FRAME_PEN] for r in inner] + [[TALK_FACE_FRAME_PEN] * w]
            pieces[name] = dict(pens=pens, words=dict(src["words"]), pal=src["pal"], derived=True)
    check_pieces(slot, pieces)
    return pieces


def check_shared_palette(slot, pieces, rom):
    """A piece on a shared palette (the name) must use the bank's existing colours, or it would look wrong for the others and for itself."""
    for name, spec in SLOTS[slot].items():
        if "shared_palette" not in spec:
            continue
        have = rom_words(rom, spec["shared_palette"])
        pal = pieces[name]["pal"]
        used = sorted({p for r in pieces[name]["pens"] for p in r if p != 15})
        for p in used:
            if cps_word(pal[p + 1]) != have[p]:
                raise ValueError("%s: pen %d is %03x in the PNG but the shared bank has %03x" % (name, p, cps_word(pal[p + 1]), have[p]))


def face_include(pieces, stage_data):
    """C text for saturn/rt/guests.c: the 15 distinct cells of his talk box face (scroll 1 payloads, 32 bytes) and their 30 keys (code << 1 | column parity), so the
    renderer can draw them in any stage file while his bonus slot is on: the HUD's "SELECT YOUR CHARACTER" icon (a continue) and the talk box show the face of
    Schaefer's slot in the arcade's own files too."""
    spec = SLOTS["schaefer"]["talk_face"]
    keys, data, seen = [], [], {}
    for code, par, tile in cells("talk_face", spec, pieces["talk_face"]["pens"]):
        key = code << 1 | par
        pl, _ = satgfx_pack.payload(stage_data, 1, key)
        if pl not in seen:
            seen[pl] = len(data)
            data.append(pl)
        keys.append((key, seen[pl]))
    keys.sort()
    out = ["/* Generated by tools/wolverine/hud_art.py: his talk box face cells, drawn in every stage file while his slot is on. ROM-derived; not in git. */",
           "#define GUEST_FACE_N %d" % len(keys),
           "static const unsigned long guest_face_key[GUEST_FACE_N] = {%s};" % ",".join("0x%x" % k for k, _ in keys),
           "static const unsigned char guest_face_idx[GUEST_FACE_N] = {%s};" % ",".join(str(i) for _, i in keys),
           "static const unsigned char guest_face_data[%d][32] __attribute__((aligned(4))) = {%s};" % (len(data), ",".join("{" + ",".join(str(b) for b in pl) + "}" for pl in data))]
    return "\n".join(out) + "\n"


def face_include_empty():
    return "\n".join(["/* no guest art: no face override */", "#define GUEST_FACE_N 0", "static const unsigned long guest_face_key[1] = {0};",
                    "static const unsigned char guest_face_idx[1] = {0};", "static const unsigned char guest_face_data[1][32] __attribute__((aligned(4))) = {{0}};"]) + "\n"


def _write(path, data):
    path = pathlib.Path(path)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)


def build(art, base_gfx, rom_path, out_dir, guest=0):
    """Writes the two patched graphics regions and the palette include; returns their paths and a report."""
    slot = GUESTS[guest]
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw = pathlib.Path(base_gfx).read_bytes()
    rom = pathlib.Path(rom_path).read_bytes()
    pieces = load_slot(art, slot)
    check_shared_palette(slot, pieces, rom)
    res = {}
    for which in ("stage", "front"):
        data = bytes(patch(raw, slot, pieces, which))
        res[which] = out / ("gfx_hud_%s.bin" % which)
        _write(res[which], data)
    sets = palette_sets(slot, guest, pieces, rom)
    inc = out / "guest_hudpal.inc"
    _write(inc, pal_include(sets).encode())
    face_inc = out / "guest_face.inc"
    _write(face_inc, face_include(pieces, pathlib.Path(res["stage"]).read_bytes()).encode())
    report = dict(slot=slot, guest=guest,
                  stage_gfx=str(res["stage"]), front_gfx=str(res["front"]), include=str(inc), face_include=str(face_inc),
                  tiles={n: sum(1 for _ in cells(n, s, pieces[n]["pens"])) for n, s in SLOTS[slot].items() if "same_as" not in s},
                  palettes=[dict(piece=s["piece"], copies=len(s["at"]), mask="0x%04x" % s["mask"]) for s in sets],
                  base_sha256=hashlib.sha256(raw).hexdigest(),
                  art_sha256={s["png"]: hashlib.sha256((pathlib.Path(art) / s["png"]).read_bytes()).hexdigest() for s in SLOTS[slot].values() if (pathlib.Path(art) / s["png"]).exists()},
                  talk_face=("derived from the select portrait, crop %s" % (TALK_FACE_CROP,)) if pieces["talk_face"].get("derived") else SLOTS[slot]["talk_face"]["png"])
    (out / "hud_art_report.json").write_text(json.dumps(report, indent=1))
    return dict(stage_gfx=str(res["stage"]), front_gfx=str(res["front"]), include=str(inc), face_include=str(face_inc), report=report)


def check_keys(rounds, slot):
    """The scroll 1 key (code << 1 | parity) of every tile of the slot's pieces must be one the arcade's own files hold: it proves the parity
    rule (which half of a code's block the map reads) on the build's own census. Returns the keys missing from every base file."""
    have = set()
    for f in rounds["files"]:
        if "keys" in f:
            have.update(f["keys"][1])
    have2 = set()
    for f in rounds["files"]:
        if "keys" in f:
            have2.update(f["keys"][2])
    miss = []
    for name, spec in SLOTS[slot].items():
        if "same_as" in spec:
            continue
        w, h = spec["size"]
        n = spec["cell"]
        for r in range(h // n):
            for c in range(w // n):
                code = spec["code"](r, c)
                if spec["layer"] == 1:
                    for par in ((0, 1) if spec.get("both") else ((spec["parity0"] + c) & 1,)):
                        k = code << 1 | par
                        if k not in have:
                            miss.append((name, "s1", k))
                elif code not in have2:
                    miss.append((name, "s2", code))
    return miss


def preview(art, base_gfx, rom_path, out_png):
    """Review picture: the Schaefer originals above the converted Wolverine pieces, drawn from the patched region with the written palettes."""
    from PIL import Image
    rom = pathlib.Path(rom_path).read_bytes()
    raw = pathlib.Path(base_gfx).read_bytes()
    slot = GUESTS[0]
    pieces = load_slot(art, slot)
    full = bytes(patch(patch(raw, slot, pieces, "front"), slot, pieces, "stage"))
    sets = {s["piece"]: s for s in palette_sets(slot, 0, pieces, rom)}
    names = ["select_portrait", "select_plate", "hud_portrait", "hud_name"]
    sheet = Image.new("RGBA", (200, 4 * 2 * 72), (64, 64, 64, 255))
    y0 = 0
    for guest_on in (False, True):
        src = full if guest_on else raw
        for name in names:
            spec = SLOTS[slot][name]
            w, h = spec["size"]
            word = (sets[name]["neu"] if guest_on else sets[name]["orig"]) if name in sets else rom_words(rom, spec["shared_palette"])
            im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            n = spec["cell"]
            for r in range(h // n):
                for c in range(w // n):
                    code = spec["code"](r, c)
                    if spec["layer"] == 2:
                        px = satgfx_pack.pens(src, SCROLL_BASE + code * 0x80, 16, 16, 8)
                    else:
                        full16 = satgfx_pack.pens(src, SCROLL_BASE + code * 0x40, 16, 8, 8)
                        px = satgfx_pack.part(full16, 0, 8 * ((spec["parity0"] + c) & 1), 8, 8)
                    for y in range(n):
                        for x in range(n):
                            p = px[y][x]
                            if p != 15:
                                wv = word[p]
                                im.putpixel((c * n + x, r * n + y), ((wv >> 8 & 15) * 17, (wv >> 4 & 15) * 17, (wv & 15) * 17, 255))
            sheet.alpha_composite(im, (4, y0 + 4))
            y0 += max(h, 24) + 4
    sheet.crop((0, 0, 200, y0)).resize((800, y0 * 4), Image.NEAREST).save(out_png)


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "build":
        r = build(*sys.argv[2:6])
        print(json.dumps(r["report"], indent=1))
    elif len(sys.argv) == 6 and sys.argv[1] == "preview":
        preview(*sys.argv[2:6])
    else:
        raise SystemExit(__doc__)
