#!/usr/bin/env python
"""ROM pages that hold the story caption text, so no round file's tile spill overwrites them (lane text-glyphs, 2026-11-09).

The stage files spill sprite tiles into ROM pages their stage's census route never read (saturn/rt/build.py round_files). The census presses through the story
scenes, so it reads only the captions it let print; a caption it skipped sits in a page the file treats as free and overwrites. Stage 14 (stage word 0x1c) showed
it: the second caption box of its story drew "ized by the aliens!" behind 17 cells of tile bytes, because the file wrote ROM 0x11cc00 to 0x11d400 over that line.

Layout (source 0xac2fa to 0xac5e8): the caption printer takes six story tables, one per jump table slot, at 0x11bafc, 0x11c496, 0x11ed2a, 0x1215bc, 0x123e50 and
0x1266e4. Each starts with 64 word offsets (the first one is 0x80), each offset points at a list of caption cells, 0 words ending a line and a word with bit 15
set ending the caption. The 64th offset is the end sentinel: it points at the next table (and, for the last table, at the end of the text).
Pages under cold lifted code (round_code_ends.json) cannot be kept and are reported by report().

usage: story_text_pages.py ROM_IMAGE [PAGE_BYTES]   prints the pages. Library: pages(rom, page) -> set of page numbers; build.py and tools/wolverine/fit.py use it."""
import pathlib
import struct
import sys

TABLES = [0x11bafc, 0x11c496, 0x11ed2a, 0x1215bc, 0x123e50, 0x1266e4]
ENTRIES = 64


def spans(rom):
    """[(first byte, end byte)] of each story table's strings, checked against the tables' own shape."""
    out = []
    for i, t in enumerate(TABLES):
        offs = struct.unpack(">%dH" % ENTRIES, rom[t:t + 2 * ENTRIES])
        if offs[0] != 2 * ENTRIES or any(o % 2 or o < 2 * ENTRIES or o >= 0x10000 for o in offs) or list(offs) != sorted(offs):
            raise ValueError("ROM image does not hold the story table at %#x" % t)
        end = t + offs[-1]
        if i + 1 < len(TABLES) and end != TABLES[i + 1]:
            raise ValueError("story table at %#x does not end at the next table" % t)
        out.append((t, end))
    return out


def pages(rom, page):
    out = set()
    for a, b in spans(rom):
        out |= set(range(a // page, (b - 1) // page + 1))
    return out


def from_work(work, page):
    return pages((pathlib.Path(work) / "rt.bin").read_bytes(), page)


def main(argv):
    if not 1 <= len(argv) <= 2:
        print(__doc__)
        return 2
    page = int(argv[1], 0) if len(argv) == 2 else 1024
    p = sorted(pages(pathlib.Path(argv[0]).read_bytes(), page))
    print(len(p), "pages of", page, "bytes:", hex(p[0] * page), "to", hex((p[-1] + 1) * page))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
