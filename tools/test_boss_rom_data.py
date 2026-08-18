"""Host gate: does the *generated* C artifact reproduce every archive pose?

Unlike tools/gen_boss_rom_data.py (which verifies in-memory before writing),
this test parses the ACTUAL generated/generated/avsp_boss_rom.h file on disk --
the exact byte table, part table, and pose table that main.c #includes -- ports
the intended C compose algorithm to Python, and asserts each of the 29 poses
reproduces the decoded archive oracle cel with 0 differing pixels across the
full 288x192 frame.

It is deliberately independent of the generator's in-memory structures: it only
reads the .h, so a regression in write_c_header's layout (struct field order,
tile packing, per-pose tile flattening, offset base) is caught here before
main.c is touched.  Read-only; exits non-zero on any difference.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_pose_gate as vp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "generated" / "avsp_boss_rom.h"


def parse_block(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.S)
    if not m:
        raise SystemExit(f"could not find array {pattern!r} in {HEADER.name}")
    return m.group(1)


def parse_tiles(text: str) -> list[bytes]:
    body = parse_block(text, r"avsp_boss_rom_tiles\[[^\]]*\]\s*=\s*\{(.*?)\};")
    values = [int(v.strip(), 0) for v in body.split(",") if v.strip()]
    if len(values) % 128:
        raise SystemExit(f"tile byte count {len(values)} is not a multiple of 128")
    return [bytes(values[i:i + 128]) for i in range(0, len(values), 128)]


def parse_uint_list(text: str, name: str) -> list[int]:
    pattern = name + r"\[\d+\]\s*=\s*\{(.*?)\};"
    body = parse_block(text, pattern)
    return [int(v.strip(), 0) for v in body.split(",") if v.strip()]


def parse_struct_rows(text: str, name: str) -> list[list[int]]:
    pattern = name + r"\[[^\]]*\]\s*=\s*\{(.*?)\};"
    body = parse_block(text, pattern)
    rows = []
    for inner in re.findall(r"\{([^}]*)\}", body):
        rows.append([int(v.strip(), 0) for v in inner.split(",") if v.strip()])
    return rows


def compose_pose(parts: list[dict], tile_table: list[bytes]) -> np.ndarray:
    """Port of the C compose main.c will run (mirrors gen.compose_full).

    For each part (reverse order) fetch tile block[source_y*nx + source_x],
    unpack 4bpp high-nibble-first, apply the flip, and stamp at origin +
    (-lx, ly).  Origin is the centred compose origin shifted by (dx, dy).
    15 is transparent; visible pens are stored as pen+1 (0 stays blank).
    """
    width = lambda p: p["nx"] * 16
    min_x = min(-p["lx"] - width(p) for p in parts)
    max_x = max(-p["lx"] for p in parts)
    min_y = min(p["ly"] for p in parts)
    max_y = max(p["ly"] + p["ny"] * 16 for p in parts)
    origin_x = vp.CEL_WIDTH // 2 - (min_x + max_x) // 2 + parts[0]["dx"]
    origin_y = vp.CEL_HEIGHT // 2 - (min_y + max_y) // 2 + parts[0]["dy"]
    canvas = np.zeros((vp.CEL_HEIGHT, vp.CEL_WIDTH), dtype=np.uint8)
    for p in reversed(parts):
        nx, ny = p["nx"], p["ny"]
        fx, fy = bool(p["flip_x"]), bool(p["flip_y"])
        for tile_y in range(ny):
            for tile_x in range(nx):
                source_y = ny - 1 - tile_y if fy else tile_y
                source_x = nx - 1 - tile_x if fx else tile_x
                index = p["tiles"][source_y * nx + source_x]
                raw = np.frombuffer(tile_table[index], dtype=np.uint8)
                pens = np.empty(16 * 16, dtype=np.uint8)
                pens[0::2] = raw >> 4
                pens[1::2] = raw & 0x0F
                pens = pens.reshape(16, 16)
                if fx:
                    pens = pens[:, ::-1]
                if fy:
                    pens = pens[::-1, :]
                dest_x = origin_x - p["lx"] - nx * 16 + tile_x * 16
                dest_y = origin_y + p["ly"] + tile_y * 16
                x0, y0 = max(dest_x, 0), max(dest_y, 0)
                x1, y1 = min(dest_x + 16, vp.CEL_WIDTH), min(dest_y + 16, vp.CEL_HEIGHT)
                if x1 <= x0 or y1 <= y0:
                    continue
                region = np.ascontiguousarray(
                    pens[y0 - dest_y:y1 - dest_y, x0 - dest_x:x1 - dest_x])
                mask = region != 15
                canvas[y0:y1, x0:x1][mask] = region[mask] + 1
    return canvas


def main() -> None:
    if not HEADER.is_file():
        raise SystemExit(
            f"missing {HEADER}; run tools/gen_boss_rom_data.py first")
    text = HEADER.read_text(encoding="ascii")

    tile_count = int(re.search(
        r"#define AVSP_BOSS_ROM_TILE_COUNT (\d+)", text).group(1))
    pose_count = int(re.search(
        r"#define AVSP_BOSS_ROM_POSE_COUNT (\d+)", text).group(1))

    tile_table = parse_tiles(text)
    if len(tile_table) != tile_count:
        raise SystemExit(f"parsed {len(tile_table)} tiles, expected {tile_count}")

    part_tiles = parse_uint_list(text, "avsp_boss_rom_part_tiles")
    part_rows = parse_struct_rows(text, "avsp_boss_rom_parts")
    pose_rows = parse_struct_rows(text, "avsp_boss_rom_poses")
    if len(pose_rows) != pose_count:
        raise SystemExit(f"parsed {len(pose_rows)} poses, expected {pose_count}")

    # Rebuild each pose's parts.  The header stores parts contiguously
    # (part_offset indexes avsp_boss_rom_parts) and each part's tile_offset is
    # ABSOLUTE into avsp_boss_rom_part_tiles -- exactly the layout main.c reads.
    failures = 0
    print(f"{'pose':>4} {'parts':>5} {'diff':>6}  status")
    for pose in range(pose_count):
        part_count, part_offset, dx, dy = pose_rows[pose]
        parts = []
        for j in range(part_count):
            pr = part_rows[part_offset + j]
            lx, ly, nx, ny, fx, fy, tcount, toff = pr
            tiles = part_tiles[toff: toff + tcount]
            if len(tiles) != tcount:
                raise SystemExit(
                    f"pose {pose} part {j}: got {len(tiles)} tiles, "
                    f"expected {tcount}")
            parts.append({"lx": lx, "ly": ly, "nx": nx, "ny": ny,
                          "flip_x": fx, "flip_y": fy, "tiles": tiles,
                          "dx": dx, "dy": dy})

        canvas = compose_pose(parts, tile_table)
        oracle, _ = vp.load_oracle_pose(pose)
        diff = int(np.count_nonzero(canvas != oracle))
        if diff == 0:
            status = "PASS"
        else:
            status = "FAIL"
            failures += 1
            _, cbox = vp.crop_to_content(canvas)
            _, obox = vp.crop_to_content(oracle)
            print(f"{pose:>4} {part_count:>5} {diff:>6}  {status} "
                  f"canvas_tl=({cbox[0]},{cbox[1]}) oracle_tl=({obox[0]},{obox[1]})")
            continue
        print(f"{pose:>4} {part_count:>5} {diff:>6}  {status}")

    # Sanity: every part's absolute tile range must fit the flat array.
    max_end = max(pr[7] + pr[6] for pr in part_rows)
    print(f"\nTile table: {len(tile_table)} tiles  "
          f"flat tile refs: {len(part_tiles)}  max ref end: {max_end}  "
          f"poses: {pose_count}")
    if max_end != len(part_tiles):
        print(f"WARNING: max ref end {max_end} != part_tiles len "
              f"{len(part_tiles)}")
    if failures:
        print(f"FAIL: {failures}/{pose_count} poses did not reproduce the oracle")
        sys.exit(1)
    print(f"PASS: {pose_count}/{pose_count} poses reproduced the archive cel "
          f"(0 diff, position-inclusive)")


if __name__ == "__main__":
    main()
