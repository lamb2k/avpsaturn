#!/usr/bin/env python
"""Wolverine's story box wording (SAT_WV_DIALOG), generated at build time from the user's ROM. Lane wv-talkbox, 2026-11-10.

The arcade keeps its story box text in the program ROM as 16 bit font cell codes: a record is 64 words (0x80 bytes), 0xffff, four zero
words, the display time, a speaker word (0x100 Schaefer's slot, 0 Warrior, 0x200 Hunter, 0x300 Linn; the soldier's calls use 0x900 and up),
line 1 (28 cells), a zero word, line 2 (28 cells). Every character has its own variants of a scene, and the game shows the one for the
player's character, so Schaefer's slot is every record whose speaker word is 0x100. The Saturn keeps this ROM image in cart RAM and the
English text is on pages no stage file takes for tiles. While Wolverine's stage files are the loaded ones, saturn/rt/guests.c writes his
wording over those records, else the originals (saturn/rt/guest_dialog.h), as it does for his palettes.

Nothing from the ROM is stored in git. The wording is tools/wolverine/dialog_lines.py (ours); each record is checked against a hash of
its original bytes (tools/wolverine/dialog_hashes.py, a truncated sha1 that cannot give the text back), and the originals the build writes
back come from the ROM it is given.

usage: dialog.py build ROM OUT_DIR       writes OUT_DIR/guest_dialog.inc
       dialog.py hashes ROM              prints a dialog_hashes.py body for the records in dialog_lines.py
       dialog.py table ROM               prints old line -> new line for every changed record (for the owner; keep it out of git)
"""
import hashlib
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dialog_lines

REC = 0x80
LINE1, LINE2 = 7 * 2, 36 * 2          # byte offsets of the lines inside a record
WIDTH = 28
SPEAKER = 0x100                       # Schaefer's slot

# Font cell codes of the story box font (the top cell of each 8x16 character; the bottom is code + 0x10), derived from the arcade's own screens.
GLYPH = {" ": 0x100, "!": 0xece, "'": 0x26d, ",": 0x282, "-": 0x283, ".": 0x284, "?": 0x2a3}
GLYPH.update({c: 0x2a5 + i for i, c in enumerate("ABCDEFGHIJK")})
GLYPH.update({c: 0x2c0 + i for i, c in enumerate("LMNOPQRSTUVWXYZ")})
GLYPH["a"] = 0x2cf
GLYPH.update({c: 0x2e0 + i for i, c in enumerate("bcdefghijklmnop")})
GLYPH["q"] = 0x2ef
GLYPH.update({c: 0x300 + i for i, c in enumerate("rstuvwxyz")})
CHARS = {v: k for k, v in GLYPH.items()}
CHARS[0xecf] = "!!"               # the arcade's wide !! (old lines only)


def words(rom, at, n):
    return list(struct.unpack(">%dH" % n, rom[at:at + 2 * n]))


def record(rom, at):
    w = words(rom, at, 64)
    if w[0] != 0xffff or w[1:5] != [0] * 4 or w[35] != 0:
        raise ValueError("%06x: not a story box record" % at)
    return w


def decode(ws):
    return "".join(CHARS.get(x, "<%x>" % x) for x in ws).rstrip()


def encode(text):
    if len(text) > WIDTH:
        raise ValueError("%r is %d characters, a line holds %d" % (text, len(text), WIDTH))
    bad = sorted({c for c in text if c not in GLYPH})
    if bad:
        raise ValueError("%r: the story box font has no %s" % (text, bad))
    return [GLYPH[c] for c in text] + [GLYPH[" "]] * (WIDTH - len(text))


def rec_hash(rom, at):
    return hashlib.sha1(rom[at + LINE1:at + LINE1 + 2 * WIDTH] + rom[at + LINE2:at + LINE2 + 2 * WIDTH]).hexdigest()[:12]


def check(rom):
    """Every record: a real record, Schaefer's slot or the soldier calling him, and the original bytes the wording was written for."""
    import dialog_hashes
    for at, (l1, l2) in sorted(dialog_lines.LINES.items()):
        w = record(rom, at)
        if w[6] not in (SPEAKER, 0x900):
            raise ValueError("%06x: speaker word %04x is not Schaefer's slot" % (at, w[6]))
        if dialog_hashes.HASHES.get(at) != rec_hash(rom, at):
            raise ValueError("%06x: the ROM's bytes are not the ones the wording was written for (another ROM revision?)" % at)
        encode(l1), encode(l2)
    for at, n, text, align in dialog_lines.NAMES:
        if len(text) > n:
            raise ValueError("name %r longer than its %d byte field" % (text, n))
        if bytes(rom[at:at + 14]) != b"Maj.D.SCHAEFER":
            raise ValueError("%06x: not Schaefer's name field" % at)


def name_bytes(n, text, align):
    pad = n - len(text)
    left = 0 if align == "left" else pad // 2
    return " " * left + text + " " * (pad - left)


def build(rom_path, out_dir):
    rom = pathlib.Path(rom_path).read_bytes()
    check(rom)
    used = sorted({c for l1, l2 in dialog_lines.LINES.values() for c in l1 + l2} | {" "})
    olds = {}
    for at in dialog_lines.LINES:
        w = record(rom, at)
        olds[at] = (w[7:7 + WIDTH], w[36:36 + WIDTH])
    glyphs = [GLYPH[c] for c in used]
    extra = sorted({x for o in olds.values() for l in o for x in l} - set(glyphs))
    glyphs += extra                       # cell codes the old lines use that the new ones do not (so the originals can be written back)
    index = {g: i for i, g in enumerate(glyphs)}
    data = bytearray()
    for at, (l1, l2) in sorted(dialog_lines.LINES.items()):
        data += struct.pack(">I", at + LINE1)
        for lines in ((encode(l1), encode(l2)), olds[at]):
            for line in lines:
                line = list(line)
                while line and line[-1] == GLYPH[" "]:
                    line.pop()
                data += bytes([len(line)]) + bytes(index[x] for x in line)
    data += b"\0\0\0\0"
    out = ["/* Generated by tools/wolverine/dialog.py: Wolverine's story box wording and the originals. ROM-derived; not in git. */",
           "#define GUEST_DIALOG_RECORDS %d" % len(dialog_lines.LINES),
           "static const unsigned short dlg_glyph[%d] = {%s};" % (len(glyphs), ",".join("0x%x" % g for g in glyphs)),
           "static const unsigned char dlg_data[%d] = {%s};" % (len(data), ",".join(str(b) for b in data))]
    names = []
    for i, (at, n, text, align) in enumerate(dialog_lines.NAMES):
        new = name_bytes(n, text, align).encode()
        old = bytes(rom[at:at + n])
        out.append("static const unsigned char dlg_name_new%d[%d] = {%s};" % (i, n, ",".join(str(b) for b in new)))
        out.append("static const unsigned char dlg_name_old%d[%d] = {%s};" % (i, n, ",".join(str(b) for b in old)))
        names.append("{ 0x%x, %d, dlg_name_new%d, dlg_name_old%d }" % (at, n, i, i))
    out.append("static const GuestName dlg_names[%d] = {\n    %s\n};" % (len(names), ",\n    ".join(names)))
    p = pathlib.Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    inc = p / "guest_dialog.inc"
    text = "\n".join(out) + "\n"
    if not inc.exists() or inc.read_text() != text:
        inc.write_text(text)
    keys = needed_keys()
    import json
    (p / "guest_dialog_keys.json").write_text(json.dumps(keys))   # for tools/wolverine/fit.py (FIT_DIALOG_KEYS)
    return dict(include=str(inc), keys=keys, records=len(dialog_lines.LINES), data_bytes=len(data), glyphs=len(glyphs), s1_keys=len(keys),
                names=len(names), table_bytes=len(data) + 2 * len(glyphs) + sum(2 * n for _, n, _, _ in dialog_lines.NAMES))


def needed_keys():
    """Scroll 1 tile keys (cell code << 1 | column parity) the new wording draws: the story font's top and bottom cells of every character of every
    new line, at the parity of its column (the arcade starts a line at a map column of odd parity: character i is at parity (i + 1) & 1; found
    by checking the arcade's own stage files, which hold exactly those keys for its lines), and the banner's name at both parities (its columns
    are not fixed). A stage file draws a cell blank unless its tile pack holds the key, and the arcade's file holds only the keys its own lines used."""
    keys = set()
    for l1, l2 in dialog_lines.LINES.values():
        for line in (l1, l2):
            for i, c in enumerate(line):
                if c == " ":
                    continue
                for cell in (GLYPH[c], GLYPH[c] + 0x10):
                    keys.add(cell << 1 | ((i + 1) & 1))
    for at, n, text, align in dialog_lines.NAMES:
        for c in text:
            for cell in (GLYPH[c], GLYPH[c] + 0x10):
                keys.update((cell << 1 | 0, cell << 1 | 1))
    return sorted(keys)


def table(rom_path):
    rom = pathlib.Path(rom_path).read_bytes()
    for at, (l1, l2) in sorted(dialog_lines.LINES.items()):
        w = record(rom, at)
        print("%06x | %s | %s  ->  %s | %s" % (at, decode(w[7:35]), decode(w[36:64]), l1, l2))


def hashes(rom_path):
    rom = pathlib.Path(rom_path).read_bytes()
    print('"""Truncated sha1 of the original bytes of every record in dialog_lines.LINES (tools/wolverine/dialog.py hashes ROM). Not reversible."""')
    print("HASHES = {")
    for at in sorted(dialog_lines.LINES):
        print("    0x%x: %r," % (at, rec_hash(rom, at)))
    print("}")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "build":
        print(build(sys.argv[2], sys.argv[3]))
    elif len(sys.argv) == 3 and sys.argv[1] == "hashes":
        hashes(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "table":
        table(sys.argv[2])
    else:
        raise SystemExit(__doc__)
