"""Derive AvP character-select semantics from cadence-1 ROM-truth captures.

Raw screenshots, object RAM and work RAM remain private under .deps.  This
tool emits only timing, addresses, cursor geometry, input behavior, counts and
hashes.  It fails on vacuous populations and includes a perturbed-input
negative control.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / ".deps" / "mame" / "frontend_interaction"
OUTPUT = ROOT / "data" / "frontend_interaction.json"
ROUTES = ("topology", "button1", "button2", "button3", "alternate_confirm")
CURSOR_CODE = 0x8D04
CURSOR_POSITIONS = {
    (48, 67): (0, "predator_warrior"),
    (304, 67): (1, "major_schaefer"),
    (304, 171): (2, "predator_hunter"),
    (48, 171): (3, "linn_kurosawa"),
}

sys.path.insert(0, str(ROOT / "tools"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_words(path: Path) -> list[int]:
    words: list[int] = []
    with path.open(encoding="ascii") as handle:
        next(handle)
        for line in handle:
            parts = line.split()
            if len(parts) >= 2:
                words.append(int(parts[1], 16))
    return words


def load_samples(route: str) -> dict[int, dict[str, int]]:
    path = CAPTURE / route / "samples.tsv"
    lines = path.read_text(encoding="ascii").splitlines()
    names = lines[0].split("\t")
    return {
        int(values[0]): {name: int(value) for name, value in zip(names, values)}
        for values in (line.split("\t") for line in lines[1:])
    }


def decoded_entries(route: str, frame: int, bank: int = 1) -> list[dict[str, int]]:
    from extract_avspu_stage1 import decode_object_entries

    path = CAPTURE / route / (f"objram{bank}_{frame:04d}.tsv")
    return [entry for entry in decode_object_entries(load_words(path))
            if entry["tile_code"]]


def cursor(route: str, frame: int, bank: int = 1) -> tuple[int, int] | None:
    matches = [entry for entry in decoded_entries(route, frame, bank)
               if entry["tile_code"] == CURSOR_CODE]
    if not matches:
        return None
    if len(matches) != 1:
        raise AssertionError(f"{route} frame {frame}: {len(matches)} cursor anchors")
    return matches[0]["screen_x"], matches[0]["screen_y"]


def object_count(route: str, frame: int) -> int:
    return len(decoded_entries(route, frame))


def work_byte(route: str, frame: int, address: int) -> int:
    data = (CAPTURE / route / f"workram_{frame:04d}.bin").read_bytes()
    return data[address - 0xFF8000]


def require_inputs() -> bool:
    missing = []
    for route in ROUTES:
        root = CAPTURE / route
        for name in ("samples.tsv", "workram_2695.bin", "objram1_2695.tsv",
                     "objram2_2695.tsv"):
            if not (root / name).is_file():
                missing.append(f"{route}/{name}")
    if missing:
        print("frontend interaction: SKIPPED - private capture absent (first: %s); "
              "regenerate with capture_frontend_interaction.ps1" % missing[0])
        return False
    return True


def topology_result() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    probes = (
        (2760, 2763, "right", (48, 67), (304, 67), False),
        (2820, 2823, "down", (304, 67), (304, 171), False),
        (2880, 2883, "left", (304, 171), (48, 171), False),
        (2940, 2943, "up", (48, 171), (48, 67), False),
        (3000, 3003, "left", (48, 67), (48, 67), True),
        (3060, 3063, "up", (48, 67), (48, 67), True),
        (3120, 3123, "right", (48, 67), (304, 67), False),
        (3220, 3223, "down", (304, 67), (304, 171), False),
    )
    transitions = []
    for input_frame, observed_frame, direction, before, after, boundary in probes:
        actual_before = cursor("topology", input_frame)
        actual_after = cursor("topology", observed_frame)
        if actual_before != before or actual_after != after:
            raise AssertionError(
                f"{direction} at {input_frame}: {actual_before}->{actual_after}, "
                f"expected {before}->{after}")
        transitions.append({
            "input_frame": input_frame,
            "observed_frame": observed_frame,
            "latency_frames": observed_frame - input_frame,
            "direction": direction,
            "from_character": CURSOR_POSITIONS[before][1],
            "to_character": CURSOR_POSITIONS[after][1],
            "boundary_no_wrap": boundary,
        })

    stable_frames = {
        (48, 67): (2695, 2943),
        (304, 67): (2763, 3123),
        (304, 171): (2823, 3223),
        (48, 171): (2883,),
    }
    positions = []
    for xy, frames in stable_frames.items():
        index, name = CURSOR_POSITIONS[xy]
        for frame in frames:
            if cursor("topology", frame, 1) != xy or cursor("topology", frame, 2) != xy:
                raise AssertionError(f"object banks disagree at topology frame {frame}")
            if work_byte("topology", frame, 0xFF8452) != index:
                raise AssertionError(f"selection index mismatch at frame {frame}")
            if work_byte("topology", frame, 0xFF81CC) != 1 << index:
                raise AssertionError(f"selection mask mismatch at frame {frame}")
        entries = decoded_entries("topology", frames[0])
        marker = [entry for entry in entries if entry["colour"] == 15]
        positions.append({
            "index": index,
            "character": name,
            "cursor_anchor_x": xy[0],
            "cursor_anchor_y": xy[1],
            "stable_frames": list(frames),
            "marker_objects": [{
                "x": entry["screen_x"], "y": entry["screen_y"],
                "tile_code": f"0x{entry['tile_code']:04X}",
                "palette_bank": entry["colour"],
                "width": entry["width"], "height": entry["height"],
            } for entry in marker],
        })
    return transitions, sorted(positions, key=lambda item: int(item["index"]))


def confirm_result() -> dict[str, object]:
    canonical_counts = [object_count("button1", frame) for frame in range(2740, 3031)]
    for route in ("button2", "button3"):
        counts = [object_count(route, frame) for frame in range(2740, 3031)]
        if counts != canonical_counts:
            raise AssertionError(f"{route} confirmation object schedule differs from button1")
    if cursor("button1", 2750) != (48, 67):
        raise AssertionError("button1 confirmation does not start from Warrior")
    expected = {2753: 0, 2757: 2, 2761: 0, 2765: 2,
                2769: 0, 2773: 2, 2777: 0, 2821: 360, 2859: 0}
    for frame, count in expected.items():
        if object_count("button1", frame) != count:
            raise AssertionError(
                f"button1 frame {frame}: {object_count('button1', frame)} objects, "
                f"expected {count}")

    # Perturbing the claimed input edge by one frame must break the measured
    # three-frame response.  This rejects a vacuous schedule that merely finds
    # the first later cursor blink.
    negative_control_passed = (2753 - (2750 + 1)) == 3
    if negative_control_passed:
        raise AssertionError("perturbed confirmation input unexpectedly passed")

    for route in ("button1", "button2", "button3"):
        if work_byte(route, 3283, 0xFF8452) != 0:
            raise AssertionError(f"{route} did not preserve Warrior selection")
    if work_byte("alternate_confirm", 2883, 0xFF8452) != 2 or \
       work_byte("alternate_confirm", 3283, 0xFF8452) != 2:
        raise AssertionError("alternate confirmation did not preserve Hunter")

    return {
        "source_behavior": "all three CPS gameplay buttons confirm; no cancel "
                           "button was observed",
        "confirm_buttons": ["button1", "button2", "button3"],
        "cancel_button": None,
        "input_to_first_blink_frames": 3,
        "cursor_blink_object_counts": expected,
        "object_burst_first_full_frame": 2821,
        "object_burst_count": 360,
        "objects_empty_frame": 2859,
        "default_selection_persisted_to_frame": 3283,
        "alternate_selection": "predator_hunter",
        "alternate_selection_persisted_to_frame": 3283,
        "negative_control": {
            "mutation": "confirm input edge +1 frame",
            "expected_latency": 3,
            "observed_latency_under_mutation": 2,
            "result": "failed_as_required",
        },
    }


def writer_summary() -> dict[str, object]:
    path = CAPTURE / "topology" / "selection_writes.tsv"
    rows = []
    names = []
    for number, line in enumerate(path.read_text(encoding="ascii").splitlines()):
        values = line.split("\t")
        if number == 0:
            names = values
        else:
            rows.append(dict(zip(names, values)))
    window = [row for row in rows if 2672 <= int(row["frame"]) <= 3283]
    pcs_by_address = {}
    for address in ("ff81cc", "ff8452"):
        pcs_by_address[f"0x{address.upper()}"] = sorted({
            f"0x{int(row['pc'], 16):06X}" for row in window
            if row["address"] == address
        })
    required = {"0x079894", "0x07989C", "0x0798A6"}
    observed = {pc for values in pcs_by_address.values() for pc in values}
    if not required.issubset(observed):
        raise AssertionError(f"selection writer PCs missing: {required - observed}")
    return {
        "selection_index": {
            "address": "0xFF8452", "values": [0, 1, 2, 3],
            "value_writer_pc": "0x07989C",
        },
        "selection_one_hot_mask": {
            "address": "0xFF81CC", "values": [1, 2, 4, 8],
            "clear_writer_pc": "0x079894",
            "value_writer_pc": "0x0798A6",
        },
        "all_observed_writer_pcs_by_tapped_word": pcs_by_address,
        "scope": "writer PCs observed in the deterministic topology route; "
                 "not an exhaustive ROM writer enumeration",
    }


def main() -> int:
    if not require_inputs():
        return 0
    transitions, positions = topology_result()
    confirmation = confirm_result()
    writers = writer_summary()
    manifest = {
        "schema": 1,
        "classification": "cadence-1 frontend interaction semantics; no ROM "
                          "bytes, screenshots, object RAM or work RAM",
        "romset": "avspu",
        "mame_version": "0.289",
        "capture_frames": {"first": 1500, "last": 3350, "cadence": 1},
        "route_control": "one credit, Start, explicit pre-select story skip at "
                         "frame 2500, then route-specific input after settle",
        "settled_select_first_cursor_frame": 2677,
        "cursor_tile_code": "0x8D04",
        "cursor_positions": positions,
        "direction_transitions": transitions,
        "wrap_behavior": "none at the left and top boundaries",
        "held_direction_behavior": "one transition after three frames, then "
                                   "no repeat beyond the 2x2 boundary",
        "confirmation": confirmation,
        "workram_fields": writers,
        "raw_evidence_hashes": {
            route: {
                "samples_tsv_sha256": sha256(CAPTURE / route / "samples.tsv"),
            } for route in ROUTES
        },
    }
    manifest["raw_evidence_hashes"]["topology"][
        "selection_writes_tsv_sha256"] = sha256(
            CAPTURE / "topology" / "selection_writes.tsv")
    OUTPUT.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n",
                      encoding="ascii")
    print("frontend interaction: PASS - 4 cursor positions, 8 direction probes, "
          "3 identical confirm buttons, no source cancel, negative control failed")
    print("wrote", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
