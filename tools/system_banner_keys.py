#!/usr/bin/env python
"""Tile keys of the arcade's rare system banners, read from the program ROM image, so every stage file holds them (lane hurryup, 2026-11-09).

The route censuses never see these: they play the first minutes of a stage and the screens after a KO (tools/screen_keys.py). A banner the arcade
draws only late in a timed section leaves its tiles out of a stage file, and the banner draws with letters missing (owner report: the U gone
from "HURRY UP!").

Timed stages: the arcade keeps a countdown in work RAM, minutes and seconds as BCD at 0xff8224 and 0xff8225 (source 0x85a0 to 0x8700). From
1:00 down it writes the countdown and the flashing banner "HURRY UP!" into the scroll 1 map, in the large chrome font (scroll 1 codes 0x100 to 0x1ff):
  - the banner (source 0x20d2c to 0x20da2): glyph table at 0x20e92, eight words (H U R R Y, U P !); the first five letters start at map
    column 16 and take two columns each, a blank column follows, the last three start at column 27;
  - the countdown (source 0x8650 to 0x86d0): digits from the table at 0x86d2 at map columns 21, 25 and 27, the colon (codes 0x164, 0x174, 0x165,
    0x175) at column 23.
Each glyph is four map entries: code g at its column, g + 0x10 below it, g + 1 and g + 0x11 at the next column. A scroll 1 key is
code << 1 | (map column & 1) (tools/screen_keys.lua), so the same letter needs different keys at an even and an odd column: the two U's of
the banner are drawn at columns 18 and 27 and need all eight keys of the glyph.

usage: system_banner_keys.py ROM_IMAGE OPCODE_IMAGE [SCREEN_KEYS_TXT]   with a file: adds the lines "1 <hexkey>" it lacks, else prints the keys.
Library: keys(rom, op) returns the scroll 1 key set (checked against the ROM's own tables); build.py, tools/wolverine/fit.py and assets.py use it."""
import pathlib
import struct
import sys

BANNER_TABLE, BANNER_LETTERS = 0x20e92, 8
BANNER_COLUMNS = [16, 18, 20, 22, 24, 27, 29, 31]
DIGIT_TABLE, DIGIT_COUNT = 0x86d2, 10
DIGIT_COLUMNS = [21, 25, 27]
COLON_CODE_AT, COLON_CODES = 0x8650, [0x164, 0x174, 0x165, 0x175]
COLON_COLUMN = 23
# What the tables must say, so a different ROM image fails loudly instead of keeping the wrong tiles.
EXPECT_BANNER = [0x188, 0x1c2, 0x1ac, 0x1ac, 0x1ca, 0x1c2, 0x1a8, 0x102]
EXPECT_DIGITS = [0x140, 0x142, 0x144, 0x146, 0x148, 0x14a, 0x14c, 0x14e, 0x160, 0x162]


def words(rom, at, n):
    return list(struct.unpack(">%dH" % n, rom[at:at + 2 * n]))


def glyph(code, column):
    """Keys of one 2 x 2 glyph whose first map column is `column`."""
    return {(code << 1) | (column & 1), ((code + 0x10) << 1) | (column & 1),
            ((code + 1) << 1) | ((column + 1) & 1), ((code + 0x11) << 1) | ((column + 1) & 1)}


def keys(rom, op):
    """rom: the program image (data reads), op: the decrypted opcode image (the digit table is read PC-relative and the colon codes are
    instruction operands, so both sit in the opcode image)."""
    banner = words(rom, BANNER_TABLE, BANNER_LETTERS)
    digits = words(op, DIGIT_TABLE, DIGIT_COUNT)
    # the colon is four move.l #imm,d(a0) instructions of eight bytes: 21 7c 01 64 00 00 01 00 ...
    colon = [struct.unpack(">H", op[COLON_CODE_AT + 8 * i + 2:COLON_CODE_AT + 8 * i + 4])[0] for i in range(4)]
    if banner != EXPECT_BANNER or digits != EXPECT_DIGITS or colon != COLON_CODES:
        raise ValueError("ROM image does not hold the banner tables the keys were derived from: %r %r %r" % (banner, digits, colon))
    out = set()
    for code, col in zip(banner, BANNER_COLUMNS):
        out |= glyph(code, col)
    for code in digits:
        for col in DIGIT_COLUMNS:
            out |= glyph(code, col)
    out |= glyph(COLON_CODES[0], COLON_COLUMN)
    return out


def from_work(work):
    """The key set from a build work directory (rt.bin is the program image, op.bin the opcode image)."""
    work = pathlib.Path(work)
    return keys((work / "rt.bin").read_bytes(), (work / "op.bin").read_bytes())


def main(argv):
    if not 2 <= len(argv) <= 3:
        print(__doc__)
        return 2
    found = keys(pathlib.Path(argv[0]).read_bytes(), pathlib.Path(argv[1]).read_bytes())
    if len(argv) == 2:
        print(" ".join("%x" % k for k in sorted(found)))
        return 0
    path = pathlib.Path(argv[2])
    have = set()
    lines = path.read_text().splitlines() if path.exists() else []
    for line in lines:
        if line.strip():
            section, key = line.split()
            if section == "1":
                have.add(int(key, 16))
    add = sorted(found - have)
    if add:
        path.write_text("".join(l + "\n" for l in lines) + "".join("1 %x\n" % k for k in add))
    print("system banner keys:", len(found), "added", len(add))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
