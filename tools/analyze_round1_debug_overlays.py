"""Validate private Round 1 debug captures and emit a compact tracked manifest."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAME = ROOT / ".deps" / "mame"
OUTPUT = ROOT / "data" / "round1_debug_overlays.json"
SAMPLE_BYTES = 0x2D00

MODES = {
    "hitboxes": {
        "row2": 0x80,
        "seed": MAME / "debugoverlay_hitboxes",
        "capture": MAME / "round1_debug_hitboxes",
        "first": 4201,
        "last": 15000,
        "cadence": 1,
        "evidence": {
            "street_aliens_and_player": ("seed", "coldboot_03000.png"),
            "stalker_and_chrysalis": ("capture", "overlay_13700.png"),
            "chrysalis_fight": ("capture", "overlay_14400.png"),
            "round1_results": ("capture", "overlay_15000.png"),
        },
    },
    "collision": {
        "row2": 0x40,
        "seed": MAME / "debugoverlay_collision",
        "capture": MAME / "round1_debug_collision",
        "first": 4201,
        "last": 17791,
        "cadence": 30,
        "evidence": {
            "first_street_room": ("seed", "coldboot_03000.png"),
            "chrysalis_fight": ("capture", "overlay_17491.png"),
            "post_boss_dialogue": ("capture", "overlay_17791.png"),
        },
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="ascii", newline="") as source:
        return list(csv.DictReader(source, delimiter="\t"))


def analyze_mode(name: str, settings: dict[str, object]) -> dict[str, object]:
    seed = Path(settings["seed"])
    capture = Path(settings["capture"])
    row2 = int(settings["row2"])
    first = int(settings["first"])
    last = int(settings["last"])
    cadence = int(settings["cadence"])

    seed_rows = read_tsv(seed / "samples.tsv")
    active_seed = [row for row in seed_rows if int(row["frame"]) >= 1230]
    if not active_seed or any(
        int(row["debug_enable"], 16) == 0
        or int(row["dip_row2"], 16) & row2 != row2
        for row in active_seed
    ):
        raise ValueError(f"{name}: debug flags did not remain active in seed")

    rows = read_tsv(capture / "samples.tsv")
    expected = (last - first) // cadence + 1
    if len(rows) != expected:
        raise ValueError(f"{name}: expected {expected} samples, found {len(rows)}")
    frames = [int(row["frame"]) for row in rows]
    if frames != list(range(first, last + 1, cadence)):
        raise ValueError(f"{name}: capture frame sequence changed")
    if any(
        int(row["debug_enable"], 16) == 0
        or int(row["dip_row2"], 16) & row2 != row2
        for row in rows
    ):
        raise ValueError(f"{name}: debug flags were lost during Round 1")

    state = capture / "actor_state.bin"
    expected_state_bytes = expected * SAMPLE_BYTES
    if state.stat().st_size != expected_state_bytes:
        raise ValueError(f"{name}: actor RAM byte count changed")

    evidence: dict[str, object] = {}
    for label, (location, filename) in settings["evidence"].items():
        path = (seed if location == "seed" else capture) / filename
        evidence[label] = {
            "raw_path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }

    return {
        "classification": "capture-exact debug evidence",
        "debug_row2_mask": f"{row2:02x}",
        "seed_active_from_frame": 1230,
        "round1_first_frame": first,
        "round1_last_frame": last,
        "cadence": cadence,
        "samples": expected,
        "actor_state_bytes": expected_state_bytes,
        "actor_state_sha256": sha256(state),
        "evidence": evidence,
    }


def main() -> None:
    result = {
        "schema": 1,
        "purpose": (
            "Private regression evidence for ROM-driven functional parity; "
            "raw captures are ignored and are not Saturn assets."
        ),
        "visual_review": {
            "hitboxes": ["player", "street aliens", "Stalker", "Chrysalis"],
            "collision": ["street rooms", "Chrysalis room", "post-boss boundary"],
        },
        "modes": {name: analyze_mode(name, settings) for name, settings in MODES.items()},
        "remaining_gate": (
            "Decode the displayed boxes into numerical actor-local geometry and "
            "replace the inferred contact schedules 21/55/97."
        ),
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(f"Validated Round 1 debug overlays: {OUTPUT}")


if __name__ == "__main__":
    main()
