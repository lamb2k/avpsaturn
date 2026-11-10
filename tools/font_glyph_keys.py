#!/usr/bin/env python
"""Scroll 1 tile keys of every text font the arcade's printers can draw, from the program ROM's own glyph tables, so every stage file holds the whole font
(lane text-glyphs, 2026-11-09).

The route censuses (tools/rounds_census.py) keep only the tiles a play route happened to draw. A glyph the route never reached, or reached only at one
column parity, draws blank (owner reports: "HURRY  P", "These   iens"). tools/system_banner_keys.py closes the one banner the owner saw; this module closes the fonts.

What the arcade draws text with (all scroll 1 map writes, a 4 byte entry per cell, code word first, one column 0x80 bytes on, see source 0xabb20, 0xab9b8, 0xabbe6,
0xac034, 0xad3a2 to 0xad47c, 0xab69c):
  - chrome font (headlines, timers, "HURRY UP!", GAME OVER): char 0x20..0x7f -> code through the word table at 0xab8b4; a glyph is 2 x 2 cells, code g at its
    column, g + 0x10 below it, g + 1 and g + 0x11 one column on; a table word of 0 draws the blank cell 0x20;
  - two row font (messages, names, score lines, story captions): char -> code through the word table at 0xab70e, code c with c + 0x10 below it; the double wide
    printers (0xad3d6, 0xad42e) add c + 1 and c + 0x11 one column on;
  - small ASCII font (HUD text, high score names): char 0x20..0x7f is the cell code itself (0x00..0x0f are the digits and hex letters of the score), in the
    front bank 0x0000, the stage bank 0x1000 (the printers add 0x1000 when the RAM flag at 0x1d6(a5) is set: 0xbcba, 0xef98, 0xf1a6 to 0xf62e) and the name entry
    bank 0xa60 (strings at 0x1e83a, codes 0xa80 to 0xadf);
  - the character select's countdown digits, scroll 1 codes 0x0b00..0x0b3f (two cells wide, three rows high; owner report: the select's stat bars shifted when
    a digit appeared), which a continue opens from every stage file.
The two glyph tables hold bank 0 codes; the printers add 0x1000 for the stage bank (0xbcba reads 0xab70e then adds it), so both banks of both fonts are kept.
A scroll 1 key is code << 1 | (map column & 1) (tools/screen_keys.lua), and text can start at any column, so every glyph code is kept at both parities:
a glyph at the wrong parity picks the other half of the 16 pixel pair in the graphics ROM and draws blank or half a letter. Cells with no visible pen cost a
key table word only, and identical pairs are stored once (tools/satgfx_pack.py).

usage: font_glyph_keys.py ROM_IMAGE [SCREEN_KEYS_TXT]   with a file: adds the lines "1 <hexkey>" it lacks, else prints the count by font.
Library: keys(rom) returns the scroll 1 key set, by_font(rom) the same split by font (for the cost report); build.py, tools/wolverine/fit.py and
tools/check_screen_keys.py use it."""
import pathlib
import struct
import sys

CHROME_TABLE = 0xab8b4
TWO_ROW_TABLE = 0xab70e
TABLE_CHARS = 0x60                      # chars 0x20..0x7f
BANKS = (0x0000, 0x1000)
SMALL_ASCII = list(range(0x00, 0x10)) + list(range(0x20, 0x80))
NAME_ENTRY_BASE = 0xa60                 # name entry bank: char + 0xa60
SELECT_DIGITS = range(0x0b00, 0x0b40)
# Two cells drawn straight from the score table printer (0xf198 to 0xf1c2: move.w #$1ce, d0, code and code + 1 side by side, stage bank too), outside the glyph tables.
DIRECT_CELLS = (0x1ce, 0x1cf)
# A different ROM image fails loudly instead of keeping the wrong tiles: both tables must hold these code ranges only.
CHROME_RANGE = (0x100, 0x250)
TWO_ROW_RANGE = (0x100, 0x310)
TWO_ROW_EXTRA = {0xece}                 # char 0x21 ("!") has its own cell pair outside the font rows


def words(rom, at, n):
    return list(struct.unpack(">%dH" % n, rom[at:at + 2 * n]))


def both(codes):
    return {(c << 1) | p for c in codes for p in (0, 1)}


def tables(rom):
    chrome = words(rom, CHROME_TABLE, TABLE_CHARS)
    two_row = words(rom, TWO_ROW_TABLE, TABLE_CHARS)
    for c in chrome:
        if c and not CHROME_RANGE[0] <= c < CHROME_RANGE[1]:
            raise ValueError("ROM image does not hold the chrome glyph table: word %#x at %#x" % (c, CHROME_TABLE))
    for c in two_row:
        if c and not (TWO_ROW_RANGE[0] <= c < TWO_ROW_RANGE[1] or c in TWO_ROW_EXTRA):
            raise ValueError("ROM image does not hold the two row glyph table: word %#x at %#x" % (c, TWO_ROW_TABLE))
    if len({c for c in chrome if c}) < 60 or len({c for c in two_row if c}) < 60:
        raise ValueError("ROM image glyph tables are nearly empty")
    return chrome, two_row


def by_font(rom):
    """{font name: scroll 1 key set}."""
    chrome, two_row = tables(rom)
    out = {}
    glyphs = {c + d for c in chrome if c for d in (0, 1, 0x10, 0x11)} | {0x20}
    out["chrome"] = both(g + b for g in glyphs for b in BANKS)
    cells = {c + d for c in two_row if c for d in (0, 0x10, 1, 0x11)}
    out["two row"] = both(c + b for c in cells for b in BANKS)
    out["small"] = both(c + b for c in SMALL_ASCII for b in BANKS) | both(c + NAME_ENTRY_BASE for c in SMALL_ASCII if c >= 0x20)
    out["select digits"] = both(SELECT_DIGITS)
    out["chrome"] |= both(c + b for c in DIRECT_CELLS for b in BANKS)
    return out


def keys(rom):
    out = set()
    for k in by_font(rom).values():
        out |= k
    return out


def from_work(work):
    """The key set from a build work directory (rt.bin is the program image the data reads see)."""
    return keys((pathlib.Path(work) / "rt.bin").read_bytes())


def main(argv):
    if not 1 <= len(argv) <= 2:
        print(__doc__)
        return 2
    rom = pathlib.Path(argv[0]).read_bytes()
    split = by_font(rom)
    found = keys(rom)
    if len(argv) == 1:
        print({k: len(v) for k, v in split.items()}, "total", len(found))
        return 0
    path = pathlib.Path(argv[1])
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
    print("font glyph keys:", len(found), "added", len(add))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
