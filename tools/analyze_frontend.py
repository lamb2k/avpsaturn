"""Validate and characterize the deterministic CPS2 opening capture."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT = ROOT / ".deps" / "mame" / "frontend"
FIRST_FRAME = 1320
LAST_FRAME = 2160
CADENCE = 2
EXPECTED_SIZE = (384, 224)
SATURN_WIDTH = 352


def rle_size(payload: bytes) -> int:
    if not payload:
        return 0
    size = 0
    run_value = payload[0]
    run_count = 1
    for value in payload[1:]:
        if value == run_value and run_count < 255:
            run_count += 1
        else:
            size += 2
            run_value = value
            run_count = 1
    return size + 2


def fit_indices(pixels: list[tuple[int, int, int]],
                palette: dict[tuple[int, int, int], int]) -> bytes:
    output = bytearray(SATURN_WIDTH * EXPECTED_SIZE[1])
    for y in range(EXPECTED_SIZE[1]):
        row = y * EXPECTED_SIZE[0]
        target = y * SATURN_WIDTH
        for x in range(SATURN_WIDTH):
            source_x = (
                x * (EXPECTED_SIZE[0] - 1) + (SATURN_WIDTH - 1) // 2
            ) // (SATURN_WIDTH - 1)
            output[target + x] = palette[pixels[row + source_x]]
    return bytes(output)


def fit_values(values: list[int]) -> bytes:
    output = bytearray(SATURN_WIDTH * EXPECTED_SIZE[1])
    for y in range(EXPECTED_SIZE[1]):
        row = y * EXPECTED_SIZE[0]
        target = y * SATURN_WIDTH
        for x in range(SATURN_WIDTH):
            source_x = (
                x * (EXPECTED_SIZE[0] - 1) + (SATURN_WIDTH - 1) // 2
            ) // (SATURN_WIDTH - 1)
            output[target + x] = values[row + source_x]
    return bytes(output)


def delta_sizes(fitted: list[bytes]) -> dict[str, int]:
    totals = {
        "strict_runs": 4 + rle_size(fitted[0]),
        "coalesced_runs": 4 + rle_size(fitted[0]),
        "xor_rle": 4 + rle_size(fitted[0]),
    }
    prior = fitted[0]
    for current in fitted[1:]:
        strict_commands = 0
        strict_data = 0
        coalesced_commands = 0
        coalesced_data = 0
        for y in range(EXPECTED_SIZE[1]):
            row = y * SATURN_WIDTH
            x = 0
            while x < SATURN_WIDTH:
                if current[row + x] == prior[row + x]:
                    x += 1
                    continue
                count = 1
                while (x + count < SATURN_WIDTH and count < 255 and
                       current[row + x + count] != prior[row + x + count]):
                    count += 1
                strict_commands += 1
                strict_data += count
                x += count
            x = 0
            while x < SATURN_WIDTH:
                if current[row + x] == prior[row + x]:
                    x += 1
                    continue
                end = x + 1
                last_change = x
                while end < SATURN_WIDTH and end - x < 255:
                    if current[row + end] != prior[row + end]:
                        last_change = end
                    elif end - last_change > 4:
                        break
                    end += 1
                count = last_change - x + 1
                coalesced_commands += 1
                coalesced_data += count
                x += count
        totals["strict_runs"] += 2 + strict_commands * 4 + strict_data
        totals["coalesced_runs"] += (
            2 + coalesced_commands * 4 + coalesced_data)
        totals["xor_rle"] += 2 + rle_size(
            bytes(a ^ b for a, b in zip(prior, current)))
        prior = current
    return totals


def stable_delta_sizes(selected: list[int],
                       frame_pixels: dict[int, list[tuple[int, int, int]]],
                       union_order: list[tuple[int, int, int]]) -> dict[str, int] | None:
    if len(union_order) > 255:
        return None
    palette = {colour: index + 1 for index, colour in enumerate(union_order)}
    fitted = [fit_indices(frame_pixels[frame], palette) for frame in selected]
    return delta_sizes(fitted)


def read_palette(frame: int) -> list[tuple[int, int, int]]:
    colours: list[tuple[int, int, int]] = []
    with (CAPTURE_ROOT / f"palette_{frame:04d}.tsv").open(
            encoding="ascii") as fh:
        next(fh)
        for line in fh:
            _, argb_text = line.rstrip().split("\t")
            argb = int(argb_text, 16)
            colours.append(((argb >> 16) & 0xff,
                            (argb >> 8) & 0xff,
                            argb & 0xff))
    return colours


def pen_identity_delta(selected: list[int],
                       frame_pixels: dict[int, list[tuple[int, int, int]]]
                       ) -> dict[str, object]:
    frame_pens: list[list[int]] = []
    palette_tables: list[list[tuple[int, int, int]]] = []
    used_pens: set[int] = set()
    missing = 0
    for frame in selected:
        palette = read_palette(frame)
        palette_tables.append(palette)
        colour_to_pen: dict[tuple[int, int, int], int] = {}
        for pen, colour in enumerate(palette):
            colour_to_pen.setdefault(colour, pen)
        pens = []
        for pixel in frame_pixels[frame]:
            pen = colour_to_pen.get(pixel)
            if pen is None:
                missing += 1
                pen = 0
            pens.append(pen)
            used_pens.add(pen)
        frame_pens.append(pens)
    if len(used_pens) > 255:
        return {"used_source_pens": len(used_pens), "missing_pixels": missing,
                "delta_bytes": None}
    pen_to_index = {pen: index + 1
                    for index, pen in enumerate(sorted(used_pens))}
    fitted = [fit_values([pen_to_index[pen] for pen in pens])
              for pens in frame_pens]
    sizes = delta_sizes(fitted)
    palette_update_bytes = 0
    prior_colours: dict[int, tuple[int, int, int]] = {}
    for palette in palette_tables:
        changed = 0
        for pen in used_pens:
            colour = palette[pen]
            if prior_colours.get(pen) != colour:
                changed += 1
                prior_colours[pen] = colour
        palette_update_bytes += 2 + changed * 4
    return {
        "used_source_pens": len(used_pens),
        "missing_pixels": missing,
        "pixel_delta_bytes": sizes,
        "palette_update_bytes": palette_update_bytes,
        "coalesced_total_bytes":
            sizes["coalesced_runs"] + palette_update_bytes,
    }


def main() -> None:
    expected_frames = list(range(FIRST_FRAME, LAST_FRAME + 1, CADENCE))
    with (CAPTURE_ROOT / "samples.tsv").open(newline="", encoding="ascii") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    frames = [int(row["frame"]) for row in rows]
    if frames != expected_frames:
        raise ValueError("dense frontend frame schedule changed")

    unique_rgb: dict[str, int] = {}
    timeline: list[dict[str, int | str]] = []
    frame_pixels: dict[int, list[tuple[int, int, int]]] = {}
    global_colours: set[tuple[int, int, int]] = set()
    local_colour_max = 0
    exact_local_rle_total = 0
    last_hash = ""
    pose_runs = 0

    for frame in expected_frames:
        path = CAPTURE_ROOT / f"frontend_{frame:04d}.png"
        with Image.open(path) as source:
            image = source.convert("RGB")
        if image.size != EXPECTED_SIZE:
            raise ValueError(f"frontend frame {frame} changed size: {image.size}")
        rgb = image.tobytes()
        digest = hashlib.sha256(rgb).hexdigest()
        if hasattr(image, "get_flattened_data"):
            pixels = list(image.get_flattened_data())
        else:
            pixels = list(image.getdata())
        frame_pixels[frame] = pixels
        colours = list(dict.fromkeys(pixels))
        local_colour_max = max(local_colour_max, len(colours))
        global_colours.update(colours)
        if len(colours) > 255:
            raise ValueError(f"frontend frame {frame} needs {len(colours)} colours")
        index = {colour: value + 1 for value, colour in enumerate(colours)}
        indexed = bytes(index[pixel] for pixel in pixels)
        exact_local_rle_total += rle_size(indexed) + len(colours) * 3
        if digest != last_hash:
            pose_runs += 1
            last_hash = digest
        unique_rgb.setdefault(digest, frame)
        timeline.append({
            "frame": frame,
            "sha256_rgb": digest,
            "first_identical_frame": unique_rgb[digest],
            "colours": len(colours),
        })

    windows = (
        ("menu_hold", 1320, 1768),
        ("start_transition", 1770, 1798),
        ("character_confirm", 1800, 2038),
        ("round_1_title", 2040, 2160),
    )
    window_reports = []
    for name, first, last in windows:
        selected = [frame for frame in expected_frames if first <= frame <= last]
        union: set[tuple[int, int, int]] = set()
        union_order: list[tuple[int, int, int]] = []
        hashes: set[str] = set()
        changed_pixels = 0
        prior: list[tuple[int, int, int]] | None = None
        for frame in selected:
            pixels = frame_pixels[frame]
            for pixel in pixels:
                if pixel not in union:
                    union.add(pixel)
                    union_order.append(pixel)
            hashes.add(hashlib.sha256(bytes(channel for pixel in pixels
                                             for channel in pixel)).hexdigest())
            if prior is not None:
                changed_pixels += sum(a != b for a, b in zip(prior, pixels))
            prior = pixels
        window_reports.append({
            "name": name,
            "first_frame": first,
            "last_frame": last,
            "sample_count": len(selected),
            "unique_full_frames": len(hashes),
            "colour_union": len(union),
            "changed_pixels_between_samples": changed_pixels,
            "stable_palette_delta_bytes": stable_delta_sizes(
                selected, frame_pixels, union_order),
            "source_pen_delta": pen_identity_delta(
                selected, frame_pixels) if name in
                {"start_transition", "character_confirm"} else None,
        })

    report = {
        "source": {
            "romset": "avspu",
            "mame_version": "0.289",
            "first_frame": FIRST_FRAME,
            "last_frame": LAST_FRAME,
            "cadence": CADENCE,
            "width": EXPECTED_SIZE[0],
            "height": EXPECTED_SIZE[1],
        },
        "frame_count": len(expected_frames),
        "unique_full_frames": len(unique_rgb),
        "pose_runs": pose_runs,
        "maximum_colours_in_one_frame": local_colour_max,
        "global_colour_union": len(global_colours),
        "independent_palette_rle_bytes": exact_local_rle_total,
        "windows": window_reports,
        "timeline": timeline,
    }
    output = ROOT / "data" / "frontend_capture.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(
        "Validated dense frontend: "
        f"{report['frame_count']} samples, "
        f"{report['unique_full_frames']} unique frames, "
        f"{report['pose_runs']} pose runs, "
        f"max {local_colour_max} colours/frame, "
        f"global union {len(global_colours)}, "
        f"independent-palette RLE {exact_local_rle_total} bytes"
    )
    for window in window_reports:
        print(
            f"  {window['name']}: {window['sample_count']} samples, "
            f"{window['unique_full_frames']} unique, "
            f"union {window['colour_union']} colours, "
            f"{window['changed_pixels_between_samples']} changed pixels, "
            f"stable delta {window['stable_palette_delta_bytes']} bytes"
        )


if __name__ == "__main__":
    main()
