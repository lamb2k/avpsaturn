"""Generate the ROM-driven boss build data and its C header.

For every archive boss pose (0..28) we recover the ROM assembly the game
displayed (same mapping as tools/verify_boss_rom_poses.py), expand it into a
set of 16x16 ROM tiles, and record the per-pose anchor (dx, dy) that places the
ROM composition at exactly the archive cel's content position.  The output is:

* generated/avsp_boss_rom_data.json  -- machine-readable data for the host test
* generated/avsp_boss_rom.h          -- the C header compiled into main.c

The generated data is a *transcription* of verify_pose_gate.compose_rom_pose:
each part stores the tile working set in natural (source_y, source_x) order for
the pose's passing facing, plus the layout offset (lx, ly).  main.c composes a
part by fetching block[source_y*nx + source_x], applying the flip, and stamping
at origin + (lx, ly); the origin is the compose_rom_pose centred origin shifted
by (dx, dy).  Because the host test re-runs that exact algorithm against the
oracle cels, a 0-difference result proves the C data reproduces the archive
render before main.c is touched.

Read-only with respect to ROM and captures; writes only the two generated
files.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decode_avsp_animation_scripts as das  # noqa: E402
import verify_pose_gate as vp  # noqa: E402
import extract_avspu_stage1 as avsp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / ".deps" / "mame" / "actorprobe"
ROM = (PROBE / "rom_window_13c_13f.bin").read_bytes()
BASE = 0x13C000
OFFSET_DATA = (PROBE / "offset_program.bin").read_bytes()
LAYOUT_DATA = (PROBE / "offset_full_program.bin").read_bytes()
TRACE = ROOT / "data" / "boss_play_sequence.json"
BOSS_HEADER = ROOT / "generated" / "avsp_boss_animation.h"

OFFSET_WINDOW_BASE = 0x1E0000
ASSEMBLY_FIRST = 0x13DE00
ASSEMBLY_LAST = 0x13F000
CEL_W, CEL_H = vp.CEL_WIDTH, vp.CEL_HEIGHT
TILE_BYTES = 128


def header_table(name: str) -> list[int]:
    text = BOSS_HEADER.read_text(encoding="ascii", errors="ignore")
    match = re.search(name + r"\[[^\]]*\]\s*=\s*\{(.*?)\};", text, re.S)
    if not match:
        raise SystemExit(f"table {name} not found in {BOSS_HEADER.name}")
    return [int(v.strip(), 0) for v in match.group(1).split(",")
            if v.strip()]


def captured_code_set(geometry: dict, frame: int):
    spec = geometry.get(frame)
    if spec is None:
        return None
    entries = avsp.decode_object_entries(vp.read_words(spec["path"]))
    by_offset = {en["offset"]: en for en in entries}
    codes = set()
    for off in spec["offsets"]:
        en = by_offset.get(off)
        if en is None:
            continue
        y = (en["y"] & ~0x3FF) | (
            ((en["y"] & 0x3FF) + spec["shift_y"]) & 0x3FF)
        codes.add((en["code"] + ((y & 0x6000) << 3)) & 0xFFFF)
    return codes


def compose_tile_code(base_code: int, source_x: int, source_y: int,
                      flip_x: bool, flip_y: bool) -> int:
    """Match verify_pose_gate.compose_rom_pose's tile code formula exactly."""
    if not flip_x and not flip_y:
        return ((base_code & ~0xF) + ((base_code + source_x) & 0xF) +
                0x10 * source_y)
    return base_code + source_x + 0x10 * source_y


def pack4(pens: np.ndarray) -> bytes:
    """16x16 pen indices -> 128 high-nibble-first 4bpp bytes."""
    out = bytearray()
    for y in range(16):
        for x in range(0, 16, 2):
            out.append((int(pens[y, x]) << 4) | int(pens[y, x + 1]))
    return bytes(out)


def part_from_entry(entry: dict, facing_flip_x: bool) -> dict:
    """Expand one decoded assembly entry to a ROM part (passing facing baked)."""
    base_code = int(entry["code"], 16)
    attr = int(entry["source_attribute"], 16)
    nx = (1 + ((attr >> 8) & 0x0F)) if attr & 0xFF00 else 1
    ny = (1 + ((attr >> 12) & 0x0F)) if attr & 0xFF00 else 1
    flip_x = bool(attr & 0x20) ^ facing_flip_x
    flip_y = bool(attr & 0x40)
    return {
        "base_code": base_code,
        "nx": nx,
        "ny": ny,
        "flip_x": 1 if flip_x else 0,
        "flip_y": 1 if flip_y else 0,
        "lx": int(entry["layout_x_signed"]),
        "ly": int(entry["layout_y_signed"]),
    }


def _full_search(assembly_by_addr: dict, code_sets: dict,
                 pose: int) -> tuple | None:
    """Compose every valid assembly and match the pose oracle crop (0 diff)."""
    oracle = vp.load_oracle_pose(pose)[0]
    ocrop, _ = vp.crop_to_content(oracle)
    for addr, asm in assembly_by_addr.items():
        if asm.get("status") != "decoded_structure":
            continue
        if asm.get("selector") not in (2, 6, 10):
            continue
        for facing in (True, False):
            canvas = vp.compose_rom_pose(asm, facing)
            crop, _ = vp.crop_to_content(canvas)
            if crop.shape == ocrop.shape and \
                    int(np.count_nonzero(crop != ocrop)) == 0:
                return (addr, facing)
    return None


def main() -> None:
    vp._GFX = (ROOT / ".deps" / "mame" / "captures" /
               "gfx_region.bin").read_bytes()
    trace = json.loads(TRACE.read_text(encoding="ascii"))
    frame_to_asm = {f["frame"]: f["assembly"] for f in trace["frames"]}
    source_frames = header_table("avsp_boss_source_frames")
    n_poses = len(source_frames)

    # Decode every assembly referenced by the trace, plus the whole region, so
    # the idle pose (no trace pointer) can be found by a compose search.
    trace_addrs = sorted(set(frame_to_asm.values()))
    region_addrs = list(range(ASSEMBLY_FIRST, ASSEMBLY_LAST, 2))
    decode_addrs = sorted(set(trace_addrs) | set(region_addrs))
    assemblies = {
        a: das.decode_assembly(ROM, BASE, a, OFFSET_DATA, LAYOUT_DATA,
                               offset_window_base=OFFSET_WINDOW_BASE)
        for a in decode_addrs
    }
    code_sets = {
        a: ({int(e["code"], 16) for e in d["entries"][:d["count"]]}
            if d.get("status") == "decoded_structure" else None)
        for a, d in assemblies.items()
    }
    geometry = vp.load_frame_geometry()

    # Map each pose to (assembly_addr, facing, how).
    mapping: dict[int, tuple] = {}
    for pose in range(n_poses):
        frame = source_frames[pose]
        ptr_asm = frame_to_asm.get(frame)
        if ptr_asm is not None:
            cap = captured_code_set(geometry, frame)
            matches = [a for a in assemblies if code_sets.get(a) == cap]
            if ptr_asm in matches:
                mapping[pose] = (ptr_asm, "ptr")
            elif matches:
                mapping[pose] = (matches[0], "codes")
            else:
                mapping[pose] = (ptr_asm, "ptr!")
        else:
            mapping[pose] = (None, "search")

    # Decide the passing facing and (dx, dy) anchor per pose; build the parts.
    # The tile working set is deduplicated by 128-byte CONTENT (not code), so
    # fully-transparent and repeated tiles collapse to one entry.
    tile_data_list: list[bytes] = []
    bytes_to_index: dict[bytes, int] = {}
    tile_codes: list[int] = []
    poses_out: list[dict] = []
    failures = []
    for pose in range(n_poses):
        addr, how = mapping[pose]
        if addr is None:
            found = _full_search(assemblies, code_sets, pose)
            if found is None:
                failures.append((pose, "no ROM assembly matched the oracle"))
                continue
            addr, facing = found
            how = "found"
        else:
            # Pick the facing that composes 0-diff against the oracle crop.
            asm = assemblies[addr]
            ocrop, _ = vp.crop_to_content(vp.load_oracle_pose(pose)[0])
            facing = None
            for cand in (True, False):
                canvas = vp.compose_rom_pose(asm, cand)
                crop, _ = vp.crop_to_content(canvas)
                if crop.shape == ocrop.shape and \
                        int(np.count_nonzero(crop != ocrop)) == 0:
                    facing = cand
                    break
            if facing is None:
                failures.append(
                    (pose, f"no 0-diff facing for assembly 0x{addr:06x}"))
                continue

        asm = assemblies[addr]
        oracle = vp.load_oracle_pose(pose)[0]
        _, abox = vp.crop_to_content(oracle)
        rom = vp.compose_rom_pose(asm, facing)
        _, rbox = vp.crop_to_content(rom)
        dx = int(abox[0] - rbox[0])
        dy = int(abox[1] - rbox[1])

        # Build the parts (natural order, passing facing baked), collecting tiles.
        parts = []
        for entry in asm["entries"][:asm["count"]]:
            part = part_from_entry(entry, facing)
            codes = []
            for sy in range(part["ny"]):
                for sx in range(part["nx"]):
                    tc = compose_tile_code(part["base_code"], sx, sy,
                                           bool(part["flip_x"]),
                                           bool(part["flip_y"]))
                    packed = pack4(np.asarray(avsp.decode_tile(vp._GFX, tc, 16)))
                    if packed not in bytes_to_index:
                        bytes_to_index[packed] = len(tile_data_list)
                        tile_data_list.append(packed)
                        tile_codes.append(tc)
                    codes.append(bytes_to_index[packed])
            part["tiles"] = codes
            parts.append(part)
        poses_out.append({
            "pose": pose,
            "assembly": f"0x{addr:06x}",
            "facing": int(facing),
            "how": how,
            "dx": dx,
            "dy": dy,
            "parts": parts,
        })

    if failures:
        for pose, why in failures:
            print(f"FAIL pose {pose}: {why}")
        raise SystemExit(1)

    # Full-cel verification using the STORED tile indices (faithful to the C
    # data): compose from the tile working set by index, not by recomputed code.
    tile_table = tile_data_list
    for rec in poses_out:
        canvas = compose_full(rec, tile_table)
        oracle = vp.load_oracle_pose(rec["pose"])[0]
        diff = int(np.count_nonzero(canvas != oracle))
        if diff != 0:
            _, cbox = vp.crop_to_content(canvas)
            _, obox = vp.crop_to_content(oracle)
            print(f"FULL-CEL FAIL pose {rec['pose']}: {diff} px "
                  f"asm={rec['assembly']} facing={rec['facing']} "
                  f"dx={rec['dx']} dy={rec['dy']} "
                  f"canvas_tl=({cbox[0]},{cbox[1]}) "
                  f"oracle_tl=({obox[0]},{obox[1]})")
            raise SystemExit(1)
    print(f"Full-cel verify: {len(poses_out)}/{n_poses} poses 0-diff")

    tile_data = b"".join(tile_data_list)

    payload = {
        "schema": 1,
        "cel_width": CEL_W,
        "cel_height": CEL_H,
        "tile_bytes": TILE_BYTES,
        "tile_codes": tile_codes,
        "tile_data_hex": tile_data.hex(),
        "poses": poses_out,
    }
    out_json = ROOT / "generated" / "avsp_boss_rom_data.json"
    out_json.write_text(json.dumps(payload, separators=(",", ":")),
                        encoding="ascii")
    write_c_header(ROOT / "generated" / "avsp_boss_rom.h", payload)
    n_tiles = len(tile_codes)
    n_parts = sum(len(r["parts"]) for r in poses_out)
    print(f"Poses: {len(poses_out)}  distinct tiles: {n_tiles}  "
          f"parts: {n_parts}  tile bytes: {n_tiles * TILE_BYTES}")
    print(f"Wrote {out_json}")
    print(f"Wrote {ROOT / 'generated' / 'avsp_boss_rom.h'}")


def compose_full(rec: dict, tile_table: list) -> np.ndarray:
    """Port of the C compose: centred origin + (dx,dy), reverse part order.

    Tiles are fetched by the stored working-set index
    block[source_y*nx + source_x], exactly as main.c will.
    """
    parts = rec["parts"]
    width = lambda p: p["nx"] * 16
    min_x = min(-p["lx"] - width(p) for p in parts)
    max_x = max(-p["lx"] for p in parts)
    min_y = min(p["ly"] for p in parts)
    max_y = max(p["ly"] + p["ny"] * 16 for p in parts)
    origin_x = CEL_W // 2 - (min_x + max_x) // 2 + rec["dx"]
    origin_y = CEL_H // 2 - (min_y + max_y) // 2 + rec["dy"]
    canvas = np.zeros((CEL_H, CEL_W), dtype=np.uint8)
    for p in reversed(parts):
        nx, ny = p["nx"], p["ny"]
        fx, fy = bool(p["flip_x"]), bool(p["flip_y"])
        for tile_y in range(ny):
            for tile_x in range(nx):
                source_y = ny - 1 - tile_y if fy else tile_y
                source_x = nx - 1 - tile_x if fx else tile_x
                index = p["tiles"][source_y * nx + source_x]
                tile = np.frombuffer(tile_table[index], dtype=np.uint8)
                pens = np.empty(16 * 16, dtype=np.uint8)
                pens[0::2] = tile >> 4
                pens[1::2] = tile & 0x0F
                pens = pens.reshape(16, 16)
                if fx:
                    pens = pens[:, ::-1]
                if fy:
                    pens = pens[::-1, :]
                dest_x = int(origin_x - p["lx"] - nx * 16 + tile_x * 16)
                dest_y = int(origin_y + p["ly"] + tile_y * 16)
                x0, y0 = max(dest_x, 0), max(dest_y, 0)
                x1, y1 = min(dest_x + 16, CEL_W), min(dest_y + 16, CEL_H)
                if x1 <= x0 or y1 <= y0:
                    continue
                region = np.ascontiguousarray(
                    pens[y0 - dest_y:y1 - dest_y, x0 - dest_x:x1 - dest_x])
                mask = region != 15
                canvas[y0:y1, x0:x1][mask] = region[mask] + 1
    return canvas


def write_c_header(path: Path, payload: dict) -> None:
    tile_codes = payload["tile_codes"]
    tile_hex = payload["tile_data_hex"]
    poses = payload["poses"]
    lines = []
    a = lines.append
    a("// Generated by tools/gen_boss_rom_data.py -- do not edit by hand.")
    a("// ROM-derived boss animation: tile working set + per-pose ROM parts.")
    a("// Compose rule: for each part (reverse order), fetch tile")
    a("// block[source_y*nx + source_x], apply flip, stamp at")
    a("// origin + (-lx, ly); origin = centred compose origin + (dx, dy).")
    a("#ifndef AVSP_BOSS_ROM_H")
    a("#define AVSP_BOSS_ROM_H")
    a("")
    a(f"#define AVSP_BOSS_ROM_CEL_WIDTH {CEL_W}")
    a(f"#define AVSP_BOSS_ROM_CEL_HEIGHT {CEL_H}")
    a(f"#define AVSP_BOSS_ROM_TILE_BYTES {TILE_BYTES}")
    a(f"#define AVSP_BOSS_ROM_TILE_COUNT {len(tile_codes)}")
    a(f"#define AVSP_BOSS_ROM_POSE_COUNT {len(poses)}")
    a("")
    a("typedef struct {")
    a("    short lx;")
    a("    short ly;")
    a("    unsigned char nx;")
    a("    unsigned char ny;")
    a("    unsigned char flip_x;")
    a("    unsigned char flip_y;")
    a("    unsigned short tile_count;")
    a("    unsigned short tile_offset;")
    a("} AvspBossRomPart;")
    a("")
    a("typedef struct {")
    a("    unsigned short part_count;")
    a("    unsigned short part_offset;")
    a("    short dx;")
    a("    short dy;")
    a("} AvspBossRomPose;")
    a("")
    a("// 16x16 tiles as high-nibble-first 4bpp (2 pixels per byte).")
    a("static const unsigned char avsp_boss_rom_tiles"
      "[AVSP_BOSS_ROM_TILE_COUNT * AVSP_BOSS_ROM_TILE_BYTES] = {")
    # 20 bytes per line
    for i in range(0, len(tile_hex), 40):
        chunk = tile_hex[i:i + 40]
        a("    " + ", ".join(f"0x{chunk[j:j+2]}" for j in range(0, len(chunk), 2)) + ",")
    a("};")
    a("")

    # Flatten parts and tile indices.  tile_offset is ABSOLUTE into the whole
    # avsp_boss_rom_part_tiles array so the C compose needs no per-pose base:
    # a part's tiles are avsp_boss_rom_part_tiles[tile_offset .. +tile_count].
    flat_parts: list[dict] = []
    flat_tiles: list[int] = []
    pose_tables: list[dict] = []
    for rec in poses:
        base = len(flat_parts)
        part_rows = []
        for p in rec["parts"]:
            offset = len(flat_tiles)
            flat_tiles.extend(p["tiles"])
            part_rows.append(
                f"    {{{p['lx']}, {p['ly']}, {p['nx']}, {p['ny']}, "
                f"{p['flip_x']}, {p['flip_y']}, {len(p['tiles'])}, {offset}}}")
        flat_parts.extend(part_rows)
        pose_tables.append({
            "part_count": len(part_rows),
            "part_offset": base,
            "dx": rec["dx"],
            "dy": rec["dy"],
        })

    a(f"static const unsigned short avsp_boss_rom_part_tiles"
      f"[{len(flat_tiles)}] = {{")
    for i in range(0, len(flat_tiles), 12):
        a("    " + ", ".join(str(c) for c in flat_tiles[i:i + 12]) + ",")
    a("};")
    a("")
    a(f"static const AvspBossRomPart avsp_boss_rom_parts"
      f"[{len(flat_parts)}] = {{")
    for row in flat_parts:
        a(row + ",")
    a("};")
    a("")
    a("static const AvspBossRomPose avsp_boss_rom_poses"
      "[AVSP_BOSS_ROM_POSE_COUNT] = {")
    for t in pose_tables:
        a(f"    {{{t['part_count']}, {t['part_offset']}, {t['dx']}, "
          f"{t['dy']}}},")
    a("};")
    a("")
    a("#endif")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
