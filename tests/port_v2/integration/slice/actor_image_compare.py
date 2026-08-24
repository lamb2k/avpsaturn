#!/usr/bin/env python3
"""Compare MAME actor silhouettes with the exact Saturn asset layers.

This is deliberately a small image comparator.  It consumes the retained
cadence-1 MAME actor state, the paired Saturn semantic trace, and the exact
PCMBT/TILES/COMBAT bytes already verified in the review ISO.  It does not
learn expected hashes from the Saturn candidate and it does not alter runtime.
"""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
REFERENCE = (ROOT / "build/feedback" /
             "REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION")
OUTPUT = ROOT / "build/feedback/INTEGRATE-03-PLAYABLE-SLICE"
HEADER = ROOT / "src/port_v2/integration/combat/source_player_generated.h"
PLAYER_ARCHIVE = ROOT / "build/avsp_cd/SPR4/PCMBT.RLE"
TILE_ARCHIVES = (ROOT / "build/avsp_cd/SPR4/TILES.BIN",
                 ROOT / "build/avsp_cd/SPR4/COMBAT.BIN")
FIRST_FRAME = 5173
LAST_FRAME = 5469
WIDTH = 288
HEIGHT = 192
PIVOT_X = WIDTH // 2
BASELINE_Y = HEIGHT - 8

sys.path.insert(0, str(ROOT / "tools"))
import analyze_source_bound_combat_presentation as source  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def fit_352(value: int) -> int:
    return value * 352 // 384 if value >= 0 else -((-value * 352) // 384)


def scale_mask(mask: frozenset[int]) -> frozenset[int]:
    """Normalize both layers through the declared 384-to-352 X mapping."""
    out = set()
    for value in mask:
        y, x = divmod(value, WIDTH)
        mapped = PIVOT_X + fit_352(x - PIVOT_X)
        if 0 <= mapped < WIDTH:
            out.add(y * WIDTH + mapped)
    return frozenset(out)


def parse_array(name: str) -> list[int]:
    text = HEADER.read_text(encoding="ascii")
    match = re.search(
        rf"{re.escape(name)}\[[^;=]+\]\s*=\s*\{{(.*?)\}};",
        text, re.DOTALL)
    require(match is not None, f"missing generated array {name}")
    return [int(value) for value in re.findall(r"\b\d+\b", match.group(1))]


def rle_player_masks() -> list[frozenset[int]]:
    offsets = parse_array("avsp_source_combat_player_rle_offsets")
    lengths = parse_array("avsp_source_combat_player_rle_bytes")
    archive = PLAYER_ARCHIVE.read_bytes()
    masks = []
    for offset, length in zip(offsets, lengths):
        decoded = bytearray()
        encoded = archive[offset:offset + length]
        require(len(encoded) == length and length % 2 == 0,
                "player pose RLE bounds drifted")
        for index in range(0, length, 2):
            count, value = encoded[index:index + 2]
            require(count > 0, "player pose contains zero RLE count")
            decoded.extend(bytes((value,)) * count)
        require(len(decoded) == 192 * 192 // 2,
                "player pose decoded size drifted")
        pixels = set()
        for index, value in enumerate(decoded):
            y, byte_x = divmod(index, 192 // 2)
            for nibble, x in ((value >> 4, byte_x * 2),
                              (value & 15, byte_x * 2 + 1)):
                if nibble:
                    pixels.add(y * WIDTH + x + (WIDTH - 192) // 2)
        masks.append(scale_mask(frozenset(pixels)))
    return masks


class TileArchive:
    def __init__(self, path: Path):
        data = path.read_bytes()
        require(data[:4] == b"AVTL", f"{path.name} magic drifted")
        count = int.from_bytes(data[4:8], "big")
        slots = int.from_bytes(data[8:12], "big")
        codes_offset = int.from_bytes(data[12:16], "big")
        require(codes_offset == 0x30 + slots * 32,
                f"{path.name} layout drifted")
        codes = [int.from_bytes(data[codes_offset + i * 4:
                                     codes_offset + i * 4 + 4], "big")
                 for i in range(count)]
        textures = codes_offset + count * 4
        self.tiles = {
            code: data[textures + i * 128:textures + (i + 1) * 128]
            for i, code in enumerate(codes)
        }

    def mask(self, code: int) -> frozenset[tuple[int, int]] | None:
        packed = self.tiles.get(code)
        if packed is None:
            return None
        pixels = set()
        for index, value in enumerate(packed):
            y, byte_x = divmod(index, 8)
            if value >> 4:
                pixels.add((byte_x * 2, y))
            if value & 15:
                pixels.add((byte_x * 2 + 1, y))
        return frozenset(pixels)


def tile_lookup(archives: list[TileArchive], code: int):
    for archive in archives:
        result = archive.mask(code)
        if result is not None:
            return result
    raise AssertionError(f"Saturn tile archive lacks source code {code:#x}")


def source_tile(code: int) -> frozenset[tuple[int, int]]:
    image = source.decoded_tile(code)
    return frozenset((x, y) for y in range(16) for x in range(16)
                     if image.getpixel((x, y)) != 15)


def render_mask(commands: list[dict[str, int]], pivot: tuple[int, int],
                lookup) -> frozenset[int]:
    pixels = set()
    origin_x = PIVOT_X - pivot[0]
    origin_y = BASELINE_Y - pivot[1]
    for command in reversed(commands):
        attribute = command["attribute"]
        nx, ny = command["width"] // 16, command["height"] // 16
        flip_x, flip_y = bool(attribute & 0x20), bool(attribute & 0x40)
        for ty in range(ny):
            for tx in range(nx):
                sx = nx - 1 - tx if flip_x else tx
                sy = ny - 1 - ty if flip_y else ty
                base = command["tile_code"]
                code = ((base & ~0xF) + ((base + sx) & 0xF) + 0x10 * sy
                        if not flip_x and not flip_y
                        else base + sx + 0x10 * sy)
                for px, py in lookup(code):
                    dx = (origin_x + command["screen_x"] + tx * 16 +
                          (15 - px if flip_x else px))
                    dy = (origin_y + command["screen_y"] + ty * 16 +
                          (15 - py if flip_y else py))
                    if 0 <= dx < WIDTH and 0 <= dy < HEIGHT:
                        pixels.add(dy * WIDTH + dx)
    return scale_mask(frozenset(pixels))


def bounds(mask: frozenset[int]) -> list[int] | None:
    if not mask:
        return None
    points = [divmod(value, WIDTH) for value in mask]
    xs = [point[1] for point in points]
    ys = [point[0] for point in points]
    return [min(xs), min(ys), max(xs) + 1, max(ys) + 1]


def centroid(mask: frozenset[int]) -> list[float] | None:
    if not mask:
        return None
    points = [divmod(value, WIDTH) for value in mask]
    return [sum(x for y, x in points) / len(points),
            sum(y for y, x in points) / len(points)]


def edges(mask: frozenset[int]) -> frozenset[int]:
    result = set()
    for value in mask:
        y, x = divmod(value, WIDTH)
        if any(not (0 <= nx < WIDTH and 0 <= ny < HEIGHT) or
               ny * WIDTH + nx not in mask
               for nx, ny in ((x - 1, y), (x + 1, y),
                              (x, y - 1), (x, y + 1))):
            result.add(value)
    return frozenset(result)


def components(mask: frozenset[int]) -> int:
    remaining = set(mask)
    count = 0
    while remaining:
        count += 1
        queue = deque((remaining.pop(),))
        while queue:
            value = queue.popleft()
            y, x = divmod(value, WIDTH)
            for nx, ny in ((x - 1, y), (x + 1, y),
                           (x, y - 1), (x, y + 1)):
                candidate = ny * WIDTH + nx
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and \
                        candidate in remaining:
                    remaining.remove(candidate)
                    queue.append(candidate)
    return count


def ratio_intersection(left: frozenset[int], right: frozenset[int]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def visual_change(previous: frozenset[int] | None,
                  current: frozenset[int]) -> float:
    if previous is None:
        return 0.0
    union = previous | current
    return len(previous ^ current) / len(union) if union else 0.0


def captured_edge_support(mask: frozenset[int], frame: int,
                          pivot_x: int, baseline_y: int) -> float:
    """Corroborate the isolated Saturn layer against its captured crop."""
    image = Image.open(
        REFERENCE / "saturn-frames" / f"{frame:05d}.png").convert("RGB")
    crop = Image.new("RGB", (WIDTH, HEIGHT), "black")
    box = (pivot_x - PIVOT_X, baseline_y - BASELINE_Y,
           pivot_x + (WIDTH - PIVOT_X), baseline_y + (HEIGHT - BASELINE_Y))
    x0, y0 = max(0, box[0]), max(0, box[1])
    x1, y1 = min(image.width, box[2]), min(image.height, box[3])
    crop.paste(image.crop((x0, y0, x1, y1)), (x0 - box[0], y0 - box[1]))
    pixels = crop.load()
    luminance = [[sum(pixels[x, y]) / 3.0 for x in range(WIDTH)]
                 for y in range(HEIGHT)]
    captured_edges = set()
    for y in range(1, HEIGHT - 1):
        for x in range(1, WIDTH - 1):
            gradient = max(
                abs(luminance[y][x + 1] - luminance[y][x - 1]),
                abs(luminance[y + 1][x] - luminance[y - 1][x]))
            if gradient >= 24.0:
                captured_edges.add(y * WIDTH + x)
    expected = edges(mask)
    hits = 0
    for value in expected:
        y, x = divmod(value, WIDTH)
        if any((y + dy) * WIDTH + x + dx in captured_edges
               for dy in range(-2, 3) for dx in range(-2, 3)
               if 0 <= x + dx < WIDTH and 0 <= y + dy < HEIGHT):
            hits += 1
    return hits / len(expected) if expected else 0.0


def shift(mask: frozenset[int], dx: int, dy: int) -> frozenset[int]:
    result = set()
    for value in mask:
        y, x = divmod(value, WIDTH)
        x += dx
        y += dy
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            result.add(y * WIDTH + x)
    return frozenset(result)


def compare_pair(source_mask: frozenset[int], target_mask: frozenset[int],
                 source_pivot: tuple[int, int], target_pivot: tuple[int, int],
                 previous_source: frozenset[int] | None,
                 previous_target: frozenset[int] | None) -> dict:
    source_edge, target_edge = edges(source_mask), edges(target_mask)
    source_center, target_center = centroid(source_mask), centroid(target_mask)
    source_bounds, target_bounds = bounds(source_mask), bounds(target_mask)
    centroid_delta = (math.dist(source_center, target_center)
                      if source_center and target_center else 999.0)
    source_change = visual_change(previous_source, source_mask)
    target_change = visual_change(previous_target, target_mask)
    return {
        "source_bbox": source_bounds,
        "saturn_bbox": target_bounds,
        "source_area": len(source_mask),
        "saturn_area": len(target_mask),
        "silhouette_iou": round(ratio_intersection(source_mask, target_mask), 6),
        "centroid_offset": round(centroid_delta, 6),
        "source_lowest_visible": source_bounds[3] - 1 if source_bounds else None,
        "saturn_lowest_visible": target_bounds[3] - 1 if target_bounds else None,
        "source_components": components(source_mask),
        "saturn_components": components(target_mask),
        "edge_similarity": round(ratio_intersection(source_edge, target_edge), 6),
        "source_adjacent_change": round(source_change, 6),
        "saturn_adjacent_change": round(target_change, 6),
        "pivot_offset": [target_pivot[0] - source_pivot[0],
                         target_pivot[1] - source_pivot[1]],
    }


def metric_flags(metric: dict, record_changed: bool,
                 source_visual_changed: bool) -> list[str]:
    flags = []
    if metric["saturn_area"] == 0:
        flags.append("actor_disappearance")
    if metric["silhouette_iou"] < 0.96:
        flags.append("silhouette_or_family_mismatch")
    if metric["source_components"] != metric["saturn_components"]:
        flags.append("connected_component_mismatch")
    if metric["centroid_offset"] > 0.75:
        flags.append("centroid_discontinuity")
    if metric["source_lowest_visible"] != metric["saturn_lowest_visible"]:
        flags.append("foot_or_baseline_mismatch")
    if metric["edge_similarity"] < 0.90:
        flags.append("edge_map_mismatch")
    if metric["pivot_offset"] != [0, 0]:
        flags.append("pivot_discontinuity")
    if metric.get("captured_edge_support", 1.0) < 0.45:
        flags.append("captured_actor_crop_mismatch")
    target_changed = metric["saturn_adjacent_change"] > 0.002
    if record_changed and not target_changed:
        flags.append("record_change_without_visible_change")
    if target_changed and not source_visual_changed:
        flags.append("visible_change_without_source_change")
    if source_visual_changed and not target_changed:
        flags.append("stale_pose")
    if abs(metric["source_adjacent_change"] -
           metric["saturn_adjacent_change"]) > 0.02:
        flags.append("temporal_silhouette_jump")
    return flags


def build_sequences() -> tuple[list[dict], dict[str, list[dict]]]:
    trace = json.loads((REFERENCE / "saturn-cadence-1-trace.json").read_text())
    repeat = json.loads(
        (REFERENCE / "saturn-cadence-1-trace-run-2.json").read_text())
    require([item["state"] for item in trace["frames"]] ==
            [item["state"] for item in repeat["frames"]],
            "paired Saturn cadence traces drifted")
    require([item["source_frame"] for item in trace["frames"]] ==
            list(range(FIRST_FRAME, LAST_FRAME + 1)),
            "Saturn cadence trace is incomplete")
    render = source.render_rows(source.RUN_A / "actor_render.tsv")
    rom = source.PROGRAM.read_bytes()
    archives = [TileArchive(path) for path in TILE_ARCHIVES]
    player_masks = rle_player_masks()
    sequences = {"player": [], "alien": []}
    records = []
    previous = {"player": (None, None, None), "alien": (None, None, None)}
    for item in trace["frames"]:
        frame = item["source_frame"]
        state = item["state"]
        frame_record = {"frame": frame, "actors": {}}
        for actor_name, source_name in (("player", "player"),
                                        ("alien", "street_alien")):
            if actor_name == "player" and not \
                    state["combat_player_presentation_active"]:
                continue
            # The source input edge is sampled before that frame's player
            # object-list build.  The accepted trace therefore presents the
            # player layer from source frame N+1 while the alien layer (whose
            # reaction writer has its own recorded delay) is indexed by N.
            render_frame = frame + 1 if actor_name == "player" else frame
            row = render[(render_frame, source_name)]
            actor = source.actor_from_row(row)
            source_record = int(row["anim_record"], 16)
            entries = source.emit_pose(
                rom, source.u32(rom, source_record + 4), actor)
            commands = source.decoded_commands(entries)
            pivot = source.actor_pivot(actor)
            source_mask = render_mask(commands, pivot, source_tile)
            if actor_name == "player":
                pose = state["combat_player_source_pose"]
                require(0 <= pose < len(player_masks),
                        f"frame {frame}: invalid Saturn player pose")
                target_mask = player_masks[pose]
                target_record = state["combat_player_source_anim_record"]
                target_pivot = (state["combat_player_source_pivot_x"],
                                state["combat_player_source_pivot_y"])
            else:
                target_record = state["combat_enemy_render_anim_record"]
                target_entries = source.emit_pose(
                    rom, source.u32(rom, target_record + 4), actor)
                target_commands = source.decoded_commands(target_entries)
                target_mask = render_mask(
                    target_commands, pivot,
                    lambda code: tile_lookup(archives, code))
                target_pivot = pivot
            prev_source, prev_target, prev_record = previous[actor_name]
            metric = compare_pair(
                source_mask, target_mask, pivot, target_pivot,
                prev_source, prev_target)
            if actor_name == "player":
                capture_x = state["combat_player_x"]
                capture_baseline = (state["combat_player_lane"] -
                                    state["combat_player_height"])
            else:
                capture_x = state["combat_enemy_x"]
                capture_baseline = (state["combat_enemy_lane"] -
                                    state["combat_enemy_height"])
            metric["captured_edge_support"] = round(captured_edge_support(
                target_mask, frame, capture_x, capture_baseline), 6)
            source_changed = metric["source_adjacent_change"] > 0.002
            flags = metric_flags(
                metric, prev_record is not None and source_record != prev_record,
                source_changed)
            if target_record != source_record:
                flags.append("reaction_early_or_late")
            actor_record = {
                "frame": frame,
                "actor": actor_name,
                "source_record": source_record,
                "saturn_record": target_record,
                "metrics": metric,
                "flags": sorted(set(flags)),
                "source_mask": source_mask,
                "target_mask": target_mask,
                "source_pivot": pivot,
                "target_pivot": target_pivot,
            }
            sequences[actor_name].append(actor_record)
            frame_record["actors"][actor_name] = actor_record
            previous[actor_name] = (source_mask, target_mask, source_record)
        records.append(frame_record)
    return records, sequences


def mutation_result(name: str, base: dict, target_mask=None,
                    target_pivot=None) -> dict:
    metric = compare_pair(
        base["source_mask"], target_mask or base["target_mask"],
        base["source_pivot"], target_pivot or base["target_pivot"],
        None, None)
    flags = metric_flags(metric, False, False)
    return {"name": name, "frame": base["frame"], "flags": flags,
            "result": "REJECTED" if flags else "NOT_REJECTED",
            "metrics": metric}


def negative_controls(sequences: dict[str, list[dict]]) -> list[dict]:
    alien = {item["frame"]: item for item in sequences["alien"]}
    wrong = mutation_result(
        "valid_wrong_alien_crop", alien[5190], alien[5329]["target_mask"])
    y_offset = mutation_result(
        "one_frame_y_offset", alien[5236], shift(alien[5236]["target_mask"], 0, 1))
    change_index = next(
        index for index in range(1, len(sequences["alien"]))
        if sequences["alien"][index]["source_mask"] !=
        sequences["alien"][index - 1]["source_mask"])
    stale_base = sequences["alien"][change_index]
    stale = mutation_result(
        "stale_repeated_pose", stale_base,
        sequences["alien"][change_index - 1]["target_mask"])
    reaction_frame = 5191
    reaction_replacement = next(
        item for item in sequences["alien"]
        if item["frame"] > reaction_frame and
        item["target_mask"] != alien[reaction_frame]["target_mask"])
    skipped = mutation_result(
        "skipped_reaction_pose", alien[reaction_frame],
        reaction_replacement["target_mask"])
    pivot_base = alien[5283]
    pivot = mutation_result(
        "pivot_jump", pivot_base,
        target_pivot=(pivot_base["target_pivot"][0] + 1,
                      pivot_base["target_pivot"][1]))
    results = [wrong, y_offset, stale, skipped, pivot]
    require(all(item["result"] == "REJECTED" for item in results),
            f"actor-image mutation escaped: {results}")
    return results


def strip_private(record: dict) -> dict:
    return {key: value for key, value in record.items()
            if key not in {"source_mask", "target_mask"}}


def mask_image(mask: frozenset[int], color: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "black")
    pixels = image.load()
    for value in mask:
        y, x = divmod(value, WIDTH)
        pixels[x, y] = color
    return image


def comparison_sheet(sequences: dict[str, list[dict]], mutations: list[dict],
                     path: Path) -> None:
    samples = [
        next(item for item in sequences["alien"] if item["frame"] == frame)
        for frame in (5190, 5236, 5283, 5329, 5400, 5469)
    ]
    sheet = Image.new("RGB", (WIDTH * 2, HEIGHT * len(samples)), "black")
    draw = ImageDraw.Draw(sheet)
    for row, item in enumerate(samples):
        left = mask_image(item["source_mask"], (255, 255, 255))
        right = mask_image(item["target_mask"], (255, 255, 255))
        sheet.paste(left, (0, row * HEIGHT))
        sheet.paste(right, (WIDTH, row * HEIGHT))
        draw.text((4, row * HEIGHT + 4), f"MAME alien {item['frame']}", fill="red")
        draw.text((WIDTH + 4, row * HEIGHT + 4),
                  f"Saturn alien {item['frame']}", fill="red")
    sheet.save(path)


def flagged_sheet(sequences: dict[str, list[dict]], path: Path) -> None:
    flagged = [item for actor in sequences.values()
               for item in actor if item["flags"]]
    if not flagged:
        Image.new("RGB", (WIDTH, HEIGHT), "black").save(path)
        return
    sheet = Image.new("RGB", (WIDTH * 4, HEIGHT * len(flagged)), "black")
    draw = ImageDraw.Draw(sheet)
    for row, item in enumerate(flagged):
        sequence = sequences[item["actor"]]
        index = sequence.index(item)
        previous = sequence[index - 1] if index else item
        images = (
            (previous["source_mask"], "MAME previous"),
            (item["source_mask"], "MAME current"),
            (previous["target_mask"], "Saturn previous"),
            (item["target_mask"], "Saturn current"),
        )
        for column, (mask, label_text) in enumerate(images):
            sheet.paste(mask_image(mask, (255, 255, 255)),
                        (column * WIDTH, row * HEIGHT))
            draw.text((column * WIDTH + 4, row * HEIGHT + 4),
                      f"{item['actor']} {item['frame']} {label_text}",
                      fill="red")
        draw.text((4, row * HEIGHT + HEIGHT - 14),
                  ", ".join(item["flags"]), fill="yellow")
    sheet.save(path)


def generate() -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    records, sequences = build_sequences()
    mutations = negative_controls(sequences)
    baseline_flags = [
        {"frame": item["frame"], "actor": item["actor"], "flags": item["flags"]}
        for actor in sequences.values() for item in actor if item["flags"]
    ]
    inspection_path = OUTPUT / "actor-image-direct-inspection.json"
    inspection = None
    inspected_pairs = set()
    expected_pairs = {(item["actor"], item["frame"])
                      for item in baseline_flags}
    if inspection_path.is_file():
        inspection = json.loads(inspection_path.read_text(encoding="utf-8"))
        inspected_pairs = {(item["actor"], item["frame"])
                           for item in inspection.get("findings", [])}
    inspection_complete = (inspection is not None and
                           inspection.get("result") == "PASS" and
                           inspected_pairs == expected_pairs)
    result = {
        "schema": 1,
        "task_id": "INTEGRATE-03-PLAYABLE-SLICE",
        "classification": (
            "calculated MAME source layers versus exact Saturn archive layers, "
            "corroborated by every paired Saturn framebuffer actor crop"),
        "horizontal_normalization": "pivot-normalized 352/384 X transform",
        "thresholds": {"silhouette_iou_min": 0.96,
                       "centroid_offset_max": 0.75,
                       "edge_similarity_min": 0.90,
                       "adjacent_change_delta_max": 0.02,
                       "captured_edge_support_min": 0.45},
        "frames_checked": LAST_FRAME - FIRST_FRAME + 1,
        "player_source_bound_frames_checked": len(sequences["player"]),
        "alien_frames_checked": len(sequences["alien"]),
        "baseline_flags": baseline_flags,
        "negative_controls": mutations,
        "result": ("PASS" if not baseline_flags or inspection_complete
                   else "FLAGGED_FOR_INSPECTION"),
        "physical_saturn": "UNRUN",
        "frames": [
            {"frame": record["frame"],
             "actors": {name: strip_private(actor)
                        for name, actor in record["actors"].items()}}
            for record in records
        ],
    }
    (OUTPUT / "actor-image-metrics.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    findings = {
        "schema": 2,
        "source": "independent MAME actor layers versus exact Saturn archive layers",
        "calculated_metrics": "actor-image-metrics.json",
        "automatically_flagged_pairs": baseline_flags,
        "negative_controls": mutations,
        "direct_inspection": ("COMPLETE" if inspection_complete else "PENDING"),
        "direct_inspection_report": (inspection_path.name
                                     if inspection_complete else None),
        "result": result["result"],
        "physical_saturn": "UNRUN",
    }
    (OUTPUT / "visual-findings.json").write_text(
        json.dumps(findings, indent=2) + "\n", encoding="utf-8")
    comparison_sheet(
        sequences, mutations, OUTPUT / "actor-silhouette-comparison.png")
    flagged_sheet(sequences, OUTPUT / "actor-flagged-pairs.png")
    return result


if __name__ == "__main__":
    report = generate()
    print("actor-image comparator:", report["result"],
          f"({report['frames_checked']} cadence frames, "
          f"{len(report['negative_controls'])} mutations rejected)")
