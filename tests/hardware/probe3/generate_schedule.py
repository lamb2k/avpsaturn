#!/usr/bin/env python3
"""Generate the provenance-locked Probe 3 object schedules.

The ignored MAME object-list captures are private source material.  The
tracked output contains only CPS2 object commands, tile identities, counts,
and hashes; it contains no graphics ROM or pixel data.  Each schedule can be
expanded by ``avsp_entry_tiles`` without an approximation step.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DEMAND = ROOT / "data" / "avsp_sprite_demand.json"
OUT_JSON = HERE / "probe3-schedule.json"
OUT_HEADER = HERE / "generated" / "probe3_schedule.h"

DEMAND_SHA256 = "9b3d110bb353b0103f7739b46dc37b6bf895d1b09952e7f6e2739fbab1f6e39b"
SCHEDULES = (
    {
        "id": "PROBE3_REPRESENTATIVE",
        "frame": 5637,
        "raw_sha256": "c19168b1e00dd50608f2dbeb8ad5e3d9c63fb5e2ef8ec720bde3e2533237f14d",
        "palette_sha256": "296a307c2c02c682bbcfda8a1ad9d307cd74ba03913e8ddd0638419894b563dc",
        "selection": (
            "minimum unweighted L1 distance to the committed street-route "
            "means for objects, tiles, palettes, and distinct tile codes; "
            "ties select the earliest source frame"
        ),
        "declared_tiles": 567,
    },
    {
        "id": "PROBE3_PEAK_909",
        "frame": 5776,
        "raw_sha256": "df57e87bb7cb42532e4c6e01b8832c7361b923dabb1ab2453b1baca914294cd6",
        "palette_sha256": "fd2b1a848a59ad457c54b51f25f34f830e1929de7d60c523a1d7717a687dfc8a",
        "selection": "committed peak_tiles_16x16 frame and value",
        "declared_tiles": 909,
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_words(path: Path) -> list[int]:
    words: list[int] = []
    for row in path.read_text(encoding="ascii").splitlines()[1:]:
        parts = row.split("\t")
        if len(parts) == 2:
            words.append(int(parts[1], 16))
    return words


def expand_entry(y: int, code: int, attr: int) -> list[dict[str, int]]:
    """Match avsp_entry_tiles and MAME 0.289 CPS2 block expansion."""
    code17 = code + ((y & 0x6000) << 3)
    nx = ((attr >> 8) & 0xF) + 1
    ny = ((attr >> 12) & 0xF) + 1
    flip_x = (attr >> 5) & 1
    flip_y = (attr >> 6) & 1
    tiles = []
    for out_y in range(ny):
        for out_x in range(nx):
            if flip_x or flip_y:
                source_x = nx - 1 - out_x if flip_x else out_x
                source_y = ny - 1 - out_y if flip_y else out_y
                tile = code17 + source_x + 0x10 * source_y
            else:
                tile = ((code17 & ~0xF) + ((code17 + out_x) & 0xF)
                        + 0x10 * out_y)
            tiles.append({
                "code": tile & 0x1FFFF,
                "dx": out_x * 16,
                "dy": out_y * 16,
                "flip_x": flip_x,
                "flip_y": flip_y,
            })
    return tiles


def workload_checksum(entries: list[dict[str, int]], tiles: list[dict[str, int]]) -> str:
    payload = bytearray()
    for entry in entries:
        for field in ("x", "y", "code", "attr"):
            payload += entry[field].to_bytes(2, "big")
    payload += b"TILES\0"
    for tile in tiles:
        payload += tile["code"].to_bytes(4, "big")
        payload += tile["dx"].to_bytes(2, "big", signed=True)
        payload += tile["dy"].to_bytes(2, "big", signed=True)
        payload += bytes((tile["flip_x"], tile["flip_y"]))
    return hashlib.sha256(payload).hexdigest()


def parse_schedule(spec: dict[str, object]) -> dict[str, object]:
    frame = int(spec["frame"])
    capture = (ROOT / ".deps" / "mame" / "enemy_actions" /
               f"objram_active_{frame:05d}.tsv")
    palette = (ROOT / ".deps" / "mame" / "enemy_actions" /
               f"palette_{frame:05d}.tsv")
    if not capture.exists():
        raise SystemExit(f"missing Probe 3 source artifact: {capture}")
    if not palette.exists():
        raise SystemExit(f"missing Probe 3 palette artifact: {palette}")
    if sha256(capture) != spec["raw_sha256"]:
        raise SystemExit(f"Probe 3 source hash mismatch: {capture}")
    if sha256(palette) != spec["palette_sha256"]:
        raise SystemExit(f"Probe 3 palette hash mismatch: {palette}")

    words = read_words(capture)
    entries: list[dict[str, int]] = []
    expanded: list[dict[str, int]] = []
    for offset in range(0, len(words) - 3, 4):
        x, y, code, attr = words[offset:offset + 4]
        if y >= 0x8000 or attr >= 0xFF00:
            break
        entry = {"x": x, "y": y, "code": code, "attr": attr}
        entries.append(entry)
        expanded += expand_entry(y, code, attr)

    if len(expanded) != int(spec["declared_tiles"]):
        raise SystemExit(
            f"{spec['id']} reconstructed {len(expanded)} tiles; "
            f"expected {spec['declared_tiles']}")
    banks = sorted({entry["attr"] & 0x1F for entry in entries})
    codes = sorted({tile["code"] for tile in expanded})
    return {
        "id": spec["id"],
        "source_scene": "avspu street wave",
        "source_frame": frame,
        "source_artifact": str(capture.relative_to(ROOT)).replace("\\", "/"),
        "source_artifact_sha256": sha256(capture),
        "palette_artifact": str(palette.relative_to(ROOT)).replace("\\", "/"),
        "palette_artifact_sha256": sha256(palette),
        "selection_rule": spec["selection"],
        "requested_tile_count": int(spec["declared_tiles"]),
        "actual_reachable_command_count": len(expanded),
        "actual_expected_drawn_command_count": len(expanded),
        "object_count": len(entries),
        "texture_tile_identities": [f"0x{code:05x}" for code in codes],
        "distinct_texture_tile_count": len(codes),
        "palette_banks": [f"0x{bank:02x}" for bank in banks],
        "palette_cram_slot_demand": len(banks),
        "texture_transfer_demand_cold_bytes": len(codes) * 128,
        "object_entries": entries,
        "workload_checksum_sha256": workload_checksum(entries, expanded),
        "expansion_contract": "avsp_entry_tiles-v1 / MAME 0.289 cps2_render_sprites",
    }


def render_header(schedules: list[dict[str, object]]) -> str:
    lines = [
        "/* Generated by tests/hardware/probe3/generate_schedule.py. */",
        "#ifndef AVSP_PROBE3_SCHEDULE_H",
        "#define AVSP_PROBE3_SCHEDULE_H",
        "",
        "typedef struct { unsigned short x, y, code, attr; } AvspProbe3Object;",
        "typedef struct {",
        "    const char *id;",
        "    const AvspProbe3Object *objects;",
        "    unsigned short object_count;",
        "    unsigned short reachable_commands;",
        "    unsigned long checksum_word;",
        "} AvspProbe3Schedule;",
        "",
    ]
    for index, schedule in enumerate(schedules):
        lines.append(f"static const AvspProbe3Object avsp_probe3_objects_{index}[] = {{")
        for entry in schedule["object_entries"]:
            lines.append("    {0x%04x, 0x%04x, 0x%04x, 0x%04x}," % (
                entry["x"], entry["y"], entry["code"], entry["attr"]))
        lines += ["};", ""]
    lines.append("static const AvspProbe3Schedule avsp_probe3_schedules[2] = {")
    for index, schedule in enumerate(schedules):
        checksum_word = int(str(schedule["workload_checksum_sha256"])[:8], 16)
        lines.append(
            '    {"%s", avsp_probe3_objects_%d, %d, %d, 0x%08xUL},' % (
                schedule["id"], index, schedule["object_count"],
                schedule["actual_reachable_command_count"], checksum_word))
    lines += ["};", "", "#endif", ""]
    return "\n".join(lines)


def main() -> int:
    if sha256(DEMAND) != DEMAND_SHA256:
        raise SystemExit("committed AvP sprite-demand identity drifted")
    demand = json.loads(DEMAND.read_text(encoding="utf-8"))
    peak = demand["combined"]["peak_tiles_16x16"]
    if peak != {"at_source_frame": 5776, "value": 909}:
        raise SystemExit("committed 909-tile declaration drifted")
    street = demand["routes"][0]["summary"]
    expected_means = {
        "objects": 59.04,
        "tiles_16x16": 564.17,
        "distinct_palettes": 9.29,
        "distinct_tile_codes": 372.21,
    }
    actual_means = {key: street[f"mean_{key}"] for key in expected_means}
    if actual_means != expected_means:
        raise SystemExit("committed representative-selection means drifted")

    schedules = [parse_schedule(spec) for spec in SCHEDULES]
    union_codes = sorted({code for schedule in schedules
                          for code in schedule["texture_tile_identities"]})
    report = {
        "schema": "avsp-probe3-schedule-v1",
        "classification": "copyright-safe CPS2 object-command schedule; no pixels",
        "committed_measurement": {
            "artifact": "data/avsp_sprite_demand.json",
            "sha256": DEMAND_SHA256,
        },
        "representative_selection_target": expected_means,
        "schedules": schedules,
        "profile_union": {
            "distinct_texture_tile_count": len(union_codes),
            "texture_tile_identities": union_codes,
        },
        "overload": {
            "id": "PROBE3_OVERLOAD",
            "base_schedule": "PROBE3_PEAK_909",
            "reachable_commands": 909,
            "method": "declared diagnostic deadline tightened to zero fields",
            "production_budget_claim": False,
            "expected_detector_state": "DEADLINE_TRIPPED",
        },
    }
    OUT_JSON.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    OUT_HEADER.parent.mkdir(parents=True, exist_ok=True)
    OUT_HEADER.write_text(render_header(schedules), encoding="ascii", newline="\n")
    print(f"wrote {OUT_JSON} sha256={sha256(OUT_JSON)}")
    print(f"wrote {OUT_HEADER} sha256={sha256(OUT_HEADER)}")
    for schedule in schedules:
        print("%s frame=%d objects=%d commands=%d checksum=%s" % (
            schedule["id"], schedule["source_frame"], schedule["object_count"],
            schedule["actual_reachable_command_count"],
            schedule["workload_checksum_sha256"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
