#!/usr/bin/env python
"""Lane wv-native-gfx 11-09: the golden mask of the relocation identity run: tools/lift_runner/mask.txt plus the four named pointer fields of every 0x80-aligned block of work RAM
(+0x1c frame record, +0x52 animation table base, +0x96 and +0xa6 saved record pointers). usage: mask_reloc.py OUT.txt"""
import pathlib, sys
src = (pathlib.Path(__file__).resolve().parent / "mask.txt").read_text().rstrip("\n") + "\n"
extra = "".join("%x %x\n" % (0xff0000 + b + o, 0xff0000 + b + o + 3) for b in range(0x7f00, 0xe300, 0x80) for o in (0x1c, 0x52, 0x96, 0xa6))
pathlib.Path(sys.argv[1]).write_text(src + extra)
