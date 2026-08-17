#!/usr/bin/env python3
"""Validate the private Stage 1 evidence ledger and emit Saturn C route data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "data" / "stage1_route.json"
DEFAULT_OUTPUT = ROOT / "generated" / "avsp_stage1_route.h"
IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def fail(message: str) -> None:
    raise ValueError(message)


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        fail(f"not a valid PNG with an IHDR header: {path}")
    return struct.unpack(">II", header[16:24])


def capture_path(ledger: dict, capture_ref: str) -> Path:
    try:
        namespace, filename = capture_ref.split(":", 1)
    except ValueError:
        fail(f"capture reference must use namespace:filename: {capture_ref}")
    roots = {
        "opening": ledger["capture"]["opening_root"],
        "continuation": ledger["capture"]["continuation_root"],
    }
    if namespace not in roots:
        fail(f"unknown capture namespace {namespace!r}")
    if Path(filename).name != filename:
        fail(f"capture filename may not escape its configured root: {capture_ref}")
    return ROOT / roots[namespace] / filename


def validate_route_samples(ledger: dict) -> None:
    capture = ledger["capture"]
    root = ROOT / capture["continuation_root"]
    sample_path = root / "route_samples.tsv"
    if not sample_path.is_file():
        fail(f"missing complete-route metadata: {sample_path}")

    with sample_path.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    expected_frames = list(range(
        capture["continuation_first_frame"],
        capture["continuation_last_frame"] + 1,
        capture["continuation_step"],
    ))
    actual_frames = [int(row["frame"]) for row in rows]
    if actual_frames != expected_frames:
        fail("complete-route sample frames are missing, duplicated, or out of order")
    for row in rows:
        frame = int(row["frame"])
        bank = int(row["active_object_bank"])
        if bank not in (1, 2):
            fail(f"frame {frame}: invalid active CPS2 object bank {bank}")
        for stem in ("objram_active", "palette"):
            path = root / f"{stem}_{frame:05d}.tsv"
            if not path.is_file():
                fail(f"frame {frame}: missing {path.name}")


def validate_ledger(ledger: dict, verify_captures: bool) -> None:
    if ledger.get("schema_version") != 1:
        fail("stage1 route schema_version must be 1")
    if ledger.get("stage") != 1:
        fail("stage1 route ledger must describe stage 1")

    capture = ledger.get("capture", {})
    if capture.get("source_width") != 384 or capture.get("source_height") != 224:
        fail("CPS2 route evidence must retain the 384x224 active picture")
    if capture.get("continuation_step") != 60:
        fail("complete-route continuation must use the verified 60-frame sample step")

    phases = ledger.get("required_runtime_phases", [])
    if not phases or len(phases) != len(set(phases)):
        fail("required_runtime_phases must be a non-empty unique ordered list")
    for phase in phases:
        if not IDENTIFIER_RE.fullmatch(phase):
            fail(f"invalid runtime phase identifier: {phase!r}")

    events = ledger.get("events", [])
    if not events:
        fail("stage1 route ledger has no events")
    ids: set[str] = set()
    frames: list[int] = []
    seen_phases: list[str] = []
    reinforcement_count = 0
    for event in events:
        event_id = event.get("id", "")
        if not IDENTIFIER_RE.fullmatch(event_id):
            fail(f"invalid event identifier: {event_id!r}")
        if event_id in ids:
            fail(f"duplicate route event id: {event_id}")
        ids.add(event_id)

        frame = event.get("frame")
        if not isinstance(frame, int) or frame <= 0:
            fail(f"{event_id}: frame must be a positive integer")
        frames.append(frame)

        phase = event.get("runtime_phase")
        if phase not in phases:
            fail(f"{event_id}: unknown runtime phase {phase!r}")
        if phase not in seen_phases:
            seen_phases.append(phase)

        kind = event.get("kind", "")
        if not IDENTIFIER_RE.fullmatch(kind):
            fail(f"{event_id}: invalid event kind {kind!r}")
        if kind == "reinforcement":
            reinforcement_count += 1
        digest = event.get("sha256", "")
        if not SHA256_RE.fullmatch(digest):
            fail(f"{event_id}: invalid lowercase SHA-256 digest")
        if not event.get("observation"):
            fail(f"{event_id}: missing visual observation")

        path = capture_path(ledger, event.get("capture", ""))
        if verify_captures:
            if not path.is_file():
                fail(f"{event_id}: missing capture {path}")
            if png_dimensions(path) != (capture["source_width"], capture["source_height"]):
                fail(f"{event_id}: capture is not 384x224: {path}")
            actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual_digest != digest:
                fail(f"{event_id}: capture hash mismatch for {path.name}")

    if frames != sorted(frames) or len(frames) != len(set(frames)):
        fail("route event frames must be unique and strictly increasing")
    if seen_phases != phases:
        fail(f"runtime phase order mismatch: expected {phases}, observed {seen_phases}")
    if events[0]["id"] != "main_menu" or frames[0] != capture["frontend_start_frame"]:
        fail("route must begin at the verified cold-traversal main menu anchor")
    round_title = next((event for event in events if event["id"] == "round_1_title"), None)
    if round_title is None or round_title["frame"] != capture["round_1_title_frame"]:
        fail("route must retain the verified Round 1 title anchor")
    if events[-1]["id"] != "round_2_boundary" or frames[-1] != capture["round_2_title_frame"]:
        fail("route must end at the verified Round 2 title boundary")
    if reinforcement_count < 2:
        fail("route must retain evidence for recurring boss-room Stalker reinforcements")

    incidents = ledger.get("capture_incidents", [])
    incident_frames = [incident.get("frame") for incident in incidents]
    if incident_frames != sorted(incident_frames):
        fail("capture incidents must be ordered by frame")
    if not all(incident.get("kind") == "continue" for incident in incidents):
        fail("only route-distorting continue incidents belong in capture_incidents")

    timing = ledger.get("native_timing", {})
    required_timings = (
        "precision_frames",
        "round_title_frames",
        "barricade_intro_frames",
        "door_dialogue_frames",
        "interior_transition_frames",
        "boss_intro_frames",
        "boss_defeat_frames",
        "stage_clear_frames",
        "results_frames",
        "intermission_frames",
    )
    for name in required_timings:
        value = timing.get(name)
        if not isinstance(value, int) or value <= 0:
            fail(f"native_timing.{name} must be a positive integer")
    if timing["precision_frames"] != capture["continuation_step"]:
        fail("native timing precision must match the complete-route sample step")
    for name in required_timings[1:]:
        if timing[name] % timing["precision_frames"] != 0:
            fail(f"native_timing.{name} exceeds the evidence precision")

    if verify_captures:
        validate_route_samples(ledger)


def c_identifier(value: str) -> str:
    return value.upper()


def generate_header(ledger: dict) -> str:
    phases = ledger["required_runtime_phases"]
    kinds: list[str] = []
    for event in ledger["events"]:
        if event["kind"] not in kinds:
            kinds.append(event["kind"])

    lines = [
        "/* Generated from data/stage1_route.json; do not hand-edit. */",
        "#ifndef AVSP_STAGE1_ROUTE_H",
        "#define AVSP_STAGE1_ROUTE_H",
        "",
        "typedef enum",
        "{",
    ]
    for index, phase in enumerate(phases):
        suffix = "," if index + 1 < len(phases) else ""
        lines.append(f"    AVSP_STAGE1_PHASE_{c_identifier(phase)} = {index}{suffix}")
    lines.extend(["} AvspStage1Phase;", "", "typedef enum", "{"])
    for index, kind in enumerate(kinds):
        suffix = "," if index + 1 < len(kinds) else ""
        lines.append(f"    AVSP_STAGE1_EVENT_{c_identifier(kind)} = {index}{suffix}")
    lines.extend([
        "} AvspStage1EventKind;",
        "",
        "typedef struct",
        "{",
        "    unsigned short source_frame;",
        "    unsigned char phase;",
        "    unsigned char kind;",
        "} AvspStage1RouteEvent;",
        "",
        f"#define AVSP_STAGE1_ROUTE_EVENT_COUNT {len(ledger['events'])}",
        f"#define AVSP_STAGE1_SOURCE_START_FRAME {ledger['capture']['frontend_start_frame']}",
        f"#define AVSP_STAGE1_SOURCE_END_FRAME {ledger['capture']['round_2_title_frame']}",
        "",
        "static const AvspStage1RouteEvent avsp_stage1_route_events[AVSP_STAGE1_ROUTE_EVENT_COUNT] =",
        "{",
    ])
    timing = ledger["native_timing"]
    timing_lines = [
        f"#define AVSP_STAGE1_TIMING_PRECISION_FRAMES {timing['precision_frames']}",
        f"#define AVSP_STAGE1_ROUND_TITLE_FRAMES {timing['round_title_frames']}",
        f"#define AVSP_STAGE1_BARRICADE_INTRO_FRAMES {timing['barricade_intro_frames']}",
        f"#define AVSP_STAGE1_DOOR_DIALOGUE_FRAMES {timing['door_dialogue_frames']}",
        f"#define AVSP_STAGE1_INTERIOR_TRANSITION_FRAMES {timing['interior_transition_frames']}",
        f"#define AVSP_STAGE1_BOSS_INTRO_FRAMES {timing['boss_intro_frames']}",
        f"#define AVSP_STAGE1_BOSS_DEFEAT_FRAMES {timing['boss_defeat_frames']}",
        f"#define AVSP_STAGE1_STAGE_CLEAR_FRAMES {timing['stage_clear_frames']}",
        f"#define AVSP_STAGE1_RESULTS_FRAMES {timing['results_frames']}",
        f"#define AVSP_STAGE1_INTERMISSION_FRAMES {timing['intermission_frames']}",
        "",
    ]
    lines[lines.index("static const AvspStage1RouteEvent avsp_stage1_route_events[AVSP_STAGE1_ROUTE_EVENT_COUNT] ="):lines.index("static const AvspStage1RouteEvent avsp_stage1_route_events[AVSP_STAGE1_ROUTE_EVENT_COUNT] =")] = timing_lines
    for index, event in enumerate(ledger["events"]):
        suffix = "," if index + 1 < len(ledger["events"]) else ""
        lines.append(
            "    {%d, AVSP_STAGE1_PHASE_%s, AVSP_STAGE1_EVENT_%s}%s /* %s */" % (
                event["frame"],
                c_identifier(event["runtime_phase"]),
                c_identifier(event["kind"]),
                suffix,
                event["id"],
            )
        )
    lines.extend(["};", "", "#endif", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-captures", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    validate_ledger(ledger, args.verify_captures)
    if not args.check_only:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(generate_header(ledger), encoding="ascii", newline="\n")
        print(f"Generated {args.output}")
    print(
        "Verified %d Stage 1 anchors from frame %d through the Round 2 boundary at %d."
        % (
            len(ledger["events"]),
            ledger["events"][0]["frame"],
            ledger["events"][-1]["frame"],
        )
    )


if __name__ == "__main__":
    main()
