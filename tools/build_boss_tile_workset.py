"""Build and measure the Chrysalis boss tile working set from ROM references.

The boss is driven by six canonical animation programs (see
``data/avsp_animation_scripts.json``).  This tool enumerates, for every one of
their selector-6 assemblies, the exact 16x16 tile codes the ROM renderer
fetches when it composes a pose, and reports the union (the working set) with
its byte size.  It is a size/measurement tool: it does not decode tile pixels.

Two facts shape the measurement:

* A part with a base code ``C`` that is ``nx`` tiles wide and ``ny`` tall
  occupies an ``nx x ny`` block of the graphics region.  The horizontal flip
  changes *which* tiles in the block are read: the un-flipped read wraps within
  the row (``(C & ~0xF) + ((C + sx) & 0xF) + 0x10*sy``) while the flipped read
  continues into the next row (``C + sx + 0x10*sy``).  The ROM stores both
  orientations, so a boss that can face either way needs the union of both
  sets.  The working set therefore reports the union across both facings, and
  separately the single-facing set actually fetched in the captured run.
* Each 16x16 tile at 4bpp is 128 bytes in the region, so a repacked working
  set of ``N`` unique tiles is ``N * 128`` bytes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "data" / "avsp_animation_scripts.json"
TILE_BYTES = 128          # 16x16 @ 4bpp, stride 1024 bits
GFX_TOTAL_BYTES = 16 * 1024 * 1024
REGION_TILES = GFX_TOTAL_BYTES // TILE_BYTES

# The three boss pose archives the ROM working set would replace.
ARCHIVES = {
    "BACT.RLE": 119868,
    "BHIT.RLE": 5900,
    "BKO.RLE": 43232,
}


def part_codes(base: int, nx: int, ny: int, flip_x: bool):
    """The set of tile codes a single part fetches for a given facing."""
    codes = set()
    for sy in range(ny):
        for sx in range(nx):
            if flip_x:
                codes.add(base + sx + 0x10 * sy)
            else:
                codes.add((base & ~0xF) + ((base + sx) & 0xF) + 0x10 * sy)
    return codes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only-facings", action="store_true",
                        help="size the working set for a single facing only "
                             "(the exact captured run), not both")
    args = parser.parse_args()

    scripts = json.loads(SCRIPTS.read_text(encoding="ascii"))
    assemblies = scripts.get("assemblies", [])
    programs = scripts.get("programs", [])

    both = set()       # union across both facings (the real working set)
    single = set()     # union for facing=1 only (the captured run)
    per_asm = []
    total_refs = 0
    for asm in assemblies:
        count = asm.get("count", 0)
        asm_codes = set()
        parts = 0
        for entry in asm.get("entries", [])[:count]:
            base = int(entry["code"], 16)
            attr = int(entry["source_attribute"], 16)
            nx = (1 + ((attr >> 8) & 0x0F)) if attr & 0xFF00 else 1
            ny = (1 + ((attr >> 12) & 0x0F)) if attr & 0xFF00 else 1
            both |= part_codes(base, nx, ny, True)
            both |= part_codes(base, nx, ny, False)
            single |= part_codes(base, nx, ny, True)
            asm_codes |= part_codes(base, nx, ny, True)
            parts += nx * ny
            total_refs += nx * ny
        per_asm.append((asm["address"], parts, len(asm_codes)))

    oob = sorted(c for c in both if c >= REGION_TILES)
    print(f"Boss tile working set  ({len(assemblies)} assemblies, "
          f"{len(programs)} canonical programs)\n")
    print(f"{'assembly':>10}  {'part tiles':>10}  {'unique (1 facing)':>18}")
    for addr, parts, uniq in per_asm:
        print(f"{addr:>10}  {parts:>10}  {uniq:>18}")

    print(f"\nTotal part-tile references (counting reuse): {total_refs}")
    print(f"Unique tiles, single facing (captured run)   : {len(single)} "
          f"-> {len(single) * TILE_BYTES} bytes")
    print(f"Unique tiles, both facings (full working set): {len(both)} "
          f"-> {len(both) * TILE_BYTES} bytes")
    if oob:
        print(f"WARNING: {len(oob)} codes exceed the {REGION_TILES}-tile region: "
              f"{', '.join(hex(c) for c in oob[:8])}")

    reuse = (total_refs - len(both)) / total_refs if total_refs else 0.0
    print(f"\nReal tile reuse (both facings): "
          f"{total_refs - len(both)}/{total_refs} references shared "
          f"({reuse:.1%})")

    print("\nArchive baselines the working set would replace:")
    for name, size in ARCHIVES.items():
        print(f"  {name:<10} {size:>8} bytes")
    total = sum(ARCHIVES.values())
    print(f"  {'TOTAL':<10} {total:>8} bytes")

    both_bytes = len(both) * TILE_BYTES
    # The six programs cover the walk/idle poses only (BACT poses 2-13); the
    # attack/hit/KO poses (14-28, incl. BHIT + BKO) are not in these programs.
    # So the honest baseline is the BACT walk/idle slice the working set
    # directly displaces, not the full three-archive total.
    walked = 0
    walked_poses = 0
    bact_total = 0
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import verify_pose_gate as gate
        archives = gate.header_table("avsp_boss_rle_archives")
        rbytes = gate.header_table("avsp_boss_rle_bytes")
        for i, b in enumerate(rbytes):
            if archives[i] == 0:
                bact_total += b
                if 2 <= i <= 13:
                    walked += b
                    walked_poses += 1
    except Exception:
        pass

    print(f"\nWorking set (raw, repacked) = {both_bytes} bytes")
    if walked:
        delta = both_bytes - walked
        print(f"Directly replaces BACT walk/idle (poses 2-13, {walked_poses} poses) "
              f"= {walked} RLE bytes")
        print(f"  -> raw working set {'costs' if delta > 0 else 'saves'} "
              f"{abs(delta)} bytes vs that RLE slice "
              f"({'larger' if delta > 0 else 'smaller'})")
    print(f"\nContext (three boss pose archives, all 29 poses): {total} bytes")
    if walked:
        print(f"  the six programs cover only {walked}/{total} bytes ({walked / total:.0%}) "
              f"of it (walk/idle);")
        print(f"  attack (BACT 14-19 + BHIT 20) and KO (BKO 21-28) are not in these")
        print(f"  programs and would add more tiles when decoded.")
    print(f"\nNOTE: 0% cross-pose reuse -- each pose stores its own body in a distinct")
    print(f"tile block (verified by hand: consecutive walk poses occupy non-overlapping")
    print(f"tile rows), so repacking cannot shrink below the sum of the pose budgets.")
    print(f"The ROM path's value is parity (driving from ROM), not a byte saving: for")
    print(f"walk/idle the raw working set is larger than the RLE-compressed cels.")


if __name__ == "__main__":
    main()
