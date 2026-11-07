#!/usr/bin/env python
"""Home menus: the game's own scroll 1 font glyphs and two text palettes, as C includes in WORK/gen. ROM-derived, never committed.
usage: home_font.py WORK GFX_BIN   WORK/home_pal.bin: two palette banks (white, yellow), from a graphics RAM dump of the game's attract."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import satgfx_pack
W, raw = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]).read_bytes()
out = bytearray()
for code in range(33, 91):
    pl, _ = satgfx_pack.payload(raw, 1, code << 1)
    out += pl
assert len(out) == 58 * 32
(W / "gen/home_font.inc").write_text(",".join(map(str, out)))
(W / "gen/home_pal.inc").write_text(",".join(map(str, (W / "home_pal.bin").read_bytes())))
