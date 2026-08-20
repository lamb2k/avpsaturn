"""Generate the ROM tile archive the per-object VDP1 renderer consumes.

S2 Body E's texture source. Enumerates every CPS2 object entry the proven
corpus decoder produces across the four paired capture routes, expands each
entry into its 16x16 ROM tile codes exactly as the CPS2 object hardware does
(MAME 0.289 cps2_render_sprites: non-flipped reads wrap within the tile row,
flipped reads run linearly; the union over both facings is stored so one
archive serves either), decodes those tiles from the locally supplied
graphics ROMs (`extract_avspu_stage1.load_gfx_region`, the SHA-verified
interleave + unshuffle already trusted by the cel pipeline), and packs them
as VDP1 16-colour-bank textures (pen 15 transparent -> pixel 0; visible pen
p -> pixel p+1, matching Jo's CRAM base+1 convention used by every cel).

Outputs:

* build/avsp_cd/SPR4/TILES.BIN - the archive, written straight into the
  staged ISO content root (build/ is git-ignored; the bytes derive from the
  private graphics ROMs and are never committed). Big-endian throughout:
    0x00 u32 magic 'AVTL'
    0x04 u32 tile_count
    0x08 u32 palette_slot_count  (16-colour banks stored)
    0x0C u32 codes_offset        (byte offset of the code table)
    0x10 u8  bank_map[32]        (CPS2 colour 0..31 -> palette slot, 0xFF unused)
    0x30 u16 cram[slot_count*16] (Saturn RGB555|0x8000, entry 0 written but
                                  unused: pen p renders colour cram[slot*16+p-1]
                                  after Jo's base+1 shift; kept 16-aligned)
    codes_offset: u32 codes[tile_count] ascending
    then tile_count * 128 bytes of 4bpp texture (high nibble = left pixel)
* data/avsp_gfx_tiles.json - tracked manifest: counts, hashes, palette source
  frame, per-route entry statistics. No ROM bytes.

The palette block is transcribed from a route-matched captured palette frame
(ADAPTED until palette RAM emulation lands: CPS2 palettes fade dynamically;
one mid-combat frame is used and its choice is recorded in the manifest).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import extract_avspu_stage1 as avsp        # noqa: E402
from decode_avsp_object_stream import Rom  # noqa: E402
import verify_avsp_object_corpus as V      # noqa: E402

ROM_PATH = ROOT / ".deps/mame/actorprobe/decrypted_program_2m.bin"
MAIN_C = ROOT / "main.c"
# Two named scopes only - no scope may be inferred from whether TILES.BIN
# happens to exist (that inference is what let extract_avspu_stage1.py's
# generic SPR4 sweep silently force a full-scope regen on every build; see
# docs/AGENT_HANDOFF.md "Item 1 continued"). --scope is REQUIRED, not
# defaulted, so a caller must say which budget it is asking for.
ROUTES_BY_SCOPE = {
    "street": ("enemy_actions", "full_route:3474:3674"),
    "round1": ("enemy_actions", "stalker_actions", "boss_actions", "boss_ko"),
}
# "street" (1,533 tiles, 202,564 bytes) is the archive MEASURED to fit the
# current cartridge budget alongside the rest of the boot working set.
# "round1" (4,640 tiles, 612,720 bytes) is the complete four-route cast;
# it does NOT fit today - widening AVSP_TILE_REGION_BYTES to hold it left
# EACT.RLE (131,552 bytes) with no single cart zone able to allocate it
# (bank0 ~13 KB free, bank1 ~103 KB free, MEASURED live over MCP). Do not
# build --scope round1 into a normal-release ISO until more PCM moves to
# phase-boundary loads - see docs/AGENT_HANDOFF.md.
PALETTE_ROUTE = "enemy_actions"
OUT_BIN = ROOT / "build" / "avsp_cd" / "SPR4" / "TILES.BIN"
OUT_JSON = ROOT / "data" / "avsp_gfx_tiles.json"
TILE_BYTES = 128
# Stride 1: sampling every 3rd frame proved lossy - the two-frame pose at
# record 0x12DE78 (tiles 0x4A20-0x4A28/0x4A30-0x4A38) fell entirely between
# samples and the renderer silently dropped it. Every captured frame is
# decoded. Residual completeness risk (labelled UNRESOLVED): poses reachable
# by the free-running interpreter that the captured routes never visited;
# closing it needs an actor-state-free assembly part walker.
SAMPLE_STRIDE = 1


def entry_tile_codes(code: int, y: int, attr: int) -> set[int]:
    """All tile codes either facing of this entry can fetch (MAME 0.289)."""
    code17 = code + ((y & 0x6000) << 3)
    nx = ((attr >> 8) & 0xF) + 1
    ny = ((attr >> 12) & 0xF) + 1
    codes = set()
    for sy in range(ny):
        for sx in range(nx):
            # non-flipped: wrap within the 16-tile row (pgear fix)
            codes.add((code17 & ~0xF) + ((code17 + sx) & 0xF) + 0x10 * sy)
            # flipped (x, y, or both): linear
            codes.add(code17 + sx + 0x10 * sy)
    return codes


def collect_full_route_entries(spec, tiles, banks):
    """Object-list truth from the RP2 delta capture for a frame interval.

    Spec is "full_route:first:last". Unlike the workram actor decode, this
    reads the recorded active object banks directly, so it covers every
    transient the interval actually drew (projectiles, shadows, effects)."""
    from census_full_route import RouteState
    name, first, last = spec.split(":")
    first, last = int(first), int(last)
    state = RouteState(ROOT / ".deps" / "mame" / name)
    n_entries = 0
    n_frames = 0
    for rec in state.frames():
        if rec["frame"] < first:
            continue
        if rec["frame"] > last:
            break
        n_frames += 1
        active = state.current["objram2" if rec["active_bank"]
                               else "objram1"]
        for offset in range(0, len(active) - 7, 8):
            y = int.from_bytes(active[offset + 2:offset + 4], "big")
            code = int.from_bytes(active[offset + 4:offset + 6], "big")
            attr = int.from_bytes(active[offset + 6:offset + 8], "big")
            if y >= 0x8000 or attr >= 0xFF00:
                break
            tiles |= entry_tile_codes(code, y, attr)
            banks.add(attr & 0x1F)
            n_entries += 1
    state.close()
    print("%s: %d frames, %d entries -> %d tiles"
          % (spec, n_frames, n_entries, len(tiles)))
    return {"frames_sampled": n_frames, "entries": n_entries}


def collect_entries(rom: Rom, routes):
    """Decode every eligible actor instance across the corpus routes."""
    per_route = {}
    tiles = set()
    banks = set()
    for route in routes:
        if route.startswith("full_route:"):
            per_route[route] = collect_full_route_entries(route, tiles,
                                                          banks)
            continue
        root = ROOT / ".deps" / "mame" / route
        frames = sorted(root.glob("workram_*.bin"))[::SAMPLE_STRIDE]
        n_entries = 0
        for wpath in frames:
            work = wpath.read_bytes()
            if len(work) != 0x8000:
                continue
            ax, ay = V.read_anchors(work)
            for n in range((0x10000 - 0x8380) // V.ACTOR_STRIDE):
                so = (V.ACTOR_ANCHOR - V.WORKRAM_BASE) + n * V.ACTOR_STRIDE
                if so + V.ACTOR_STRIDE > len(work):
                    break
                try:
                    flat, _meta = V.decode_actor_entries(rom, work, so, ax, ay)
                except IndexError:
                    flat = None
                if not flat:
                    continue
                for i in range(0, len(flat), 4):
                    _x, y, code, attr = flat[i:i + 4]
                    tiles |= entry_tile_codes(code, y, attr)
                    banks.add(attr & 0x1F)
                    n_entries += 1
        per_route[route] = {"frames_sampled": len(frames),
                            "entries": n_entries}
        print("%s: %d frames, %d entries so far -> %d tiles"
              % (route, len(frames), n_entries, len(tiles)))
    return tiles, banks, per_route


def pick_palette_frame() -> Path:
    """A mid-combat street-route palette frame, stable vs its neighbours."""
    root = ROOT / ".deps" / "mame" / PALETTE_ROUTE
    frames = sorted(root.glob("palette_*.tsv"))
    if not frames:
        raise SystemExit("no palette captures in " + str(root))
    mid = frames[len(frames) // 2]
    return mid


def build_palette_block(banks: set[int], palette_path: Path):
    palette = avsp.load_palette_path(palette_path)
    bank_map = [0xFF] * 32
    slots = []
    for bank in sorted(banks):
        bank_map[bank] = len(slots)
        slots.append(bank)
    cram = []
    for bank in slots:
        for pen in range(16):
            # Saturn colour for VDP1 pixel value pen+1 lands at CRAM index
            # slot*16+pen after Jo's base+1 shift; pen 15's slot (index 15)
            # is written from CPS2 pen 15 but never rendered (transparent).
            r, g, b, _a = palette[bank * 16 + pen]
            cram.append(0x8000 | ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3))
    return bank_map, slots, cram


def tile_texture(gfx: bytearray, code: int) -> bytes:
    """One 16x16 tile as VDP1 4bpp bytes (pen15 -> 0, pen p -> p+1)."""
    image = avsp.decode_tile(gfx, code, 16)
    pixels = image.load()
    out = bytearray(TILE_BYTES)
    for y in range(16):
        for x in range(0, 16, 2):
            left = pixels[x, y]
            right = pixels[x + 1, y]
            left = 0 if left == 15 else left + 1
            right = 0 if right == 15 else right + 1
            out[y * 8 + x // 2] = (left << 4) | right
    return bytes(out)


def read_tile_region_bytes() -> int:
    """The runtime's carved cart budget, parsed straight from main.c so
    this generator and the compiled runtime can never silently disagree."""
    text = MAIN_C.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"#define\s+AVSP_TILE_REGION_BYTES\s+(0x[0-9A-Fa-f]+)",
                 text)
    if not m:
        raise SystemExit("AVSP_TILE_REGION_BYTES not found in main.c")
    return int(m.group(1), 16)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True, choices=("street", "round1"),
                        help="street: the archive proven to fit the current "
                             "cartridge budget. round1: the complete "
                             "four-route cast archive, does not fit today.")
    parser.add_argument("--allow-over-budget", action="store_true",
                        help="write the archive even if it exceeds the "
                             "runtime's AVSP_TILE_REGION_BYTES carve "
                             "(measurement only - never for a build).")
    args = parser.parse_args()
    routes = ROUTES_BY_SCOPE[args.scope]
    avsp.verify_roms()
    gfx = avsp.load_gfx_region()
    avsp.verify_loaded_gfx_region(gfx)
    rom = Rom(ROM_PATH.read_bytes())

    tiles, banks, per_route = collect_entries(rom, routes)
    max_code = len(gfx) * 8 // (TILE_BYTES * 8)
    bad = [c for c in tiles if c < 0 or c >= max_code]
    if bad:
        raise SystemExit("tile codes outside gfx region: %s"
                         % ", ".join("0x%X" % c for c in sorted(bad)[:8]))
    codes = sorted(tiles)

    palette_path = pick_palette_frame()
    bank_map, slots, cram = build_palette_block(banks, palette_path)
    print("tiles: %d (%d bytes), palette banks: %s -> %d slots"
          % (len(codes), len(codes) * TILE_BYTES,
             ",".join("0x%02X" % b for b in sorted(banks)), len(slots)))

    header_bytes = 0x10 + 32 + len(cram) * 2
    codes_offset = header_bytes
    blob = bytearray()
    blob += b"AVTL"
    blob += len(codes).to_bytes(4, "big")
    blob += len(slots).to_bytes(4, "big")
    blob += codes_offset.to_bytes(4, "big")
    blob += bytes(bank_map)
    for value in cram:
        blob += value.to_bytes(2, "big")
    assert len(blob) == header_bytes
    for code in codes:
        blob += code.to_bytes(4, "big")
    for code in codes:
        blob += tile_texture(gfx, code)

    region_bytes = read_tile_region_bytes()
    if len(blob) > region_bytes and not args.allow_over_budget:
        raise SystemExit(
            "REFUSING to write: archive is %d bytes but the runtime's "
            "AVSP_TILE_REGION_BYTES carve (main.c) is only %d bytes. "
            "A build must never ship an ISO member the runtime cannot "
            "hold. Either regenerate with --scope street, or widen the "
            "carve in main.c AND re-measure the cartridge allocator "
            "budget for every other cart-resident asset before doing so "
            "(see docs/AGENT_HANDOFF.md). Pass --allow-over-budget only "
            "to measure an oversized archive offline, never to build."
            % (len(blob), region_bytes))
    print("tile region budget: %d / %d bytes used (%.1f%%)"
         % (len(blob), region_bytes, 100 * len(blob) / region_bytes))

    OUT_BIN.parent.mkdir(parents=True, exist_ok=True)
    OUT_BIN.write_bytes(blob)

    manifest = {
        "schema": 1,
        "classification": "tile archive manifest - no ROM bytes",
        "archive": {"file": "build/avsp_cd/SPR4/TILES.BIN",
                    "bytes": len(blob),
                    "sha256": hashlib.sha256(bytes(blob)).hexdigest()},
        "tile_count": len(codes),
        "tile_bytes": TILE_BYTES,
        "palette": {"source": str(palette_path.relative_to(ROOT)).replace(
                        "\\", "/"),
                    "banks": ["0x%02X" % b for b in slots],
                    "label": "ADAPTED single-frame palette"},
        "facing_union": True,
        "scope": args.scope,
        "tile_region_budget_bytes": region_bytes,
        "tile_region_budget_used_pct": round(100 * len(blob) / region_bytes, 2),
        "sample_stride": SAMPLE_STRIDE,
        "routes": per_route,
        "gfx_region_sha256": hashlib.sha256(bytes(gfx)).hexdigest(),
    }
    OUT_JSON.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print("wrote %s (%d bytes) and %s" % (OUT_BIN, len(blob), OUT_JSON))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
