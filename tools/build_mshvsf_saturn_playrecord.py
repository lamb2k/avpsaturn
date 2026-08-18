#!/usr/bin/env python3
"""Build a private Yaba Sanshiro controller replay for MSHvSF research."""

from __future__ import annotations

import argparse
import json
import zlib
from pathlib import Path


BUTTON_BITS = {
    "up": (2, 0x10),
    "right": (2, 0x80),
    "down": (2, 0x20),
    "left": (2, 0x40),
    "start": (2, 0x08),
    "a": (2, 0x04),
    "b": (2, 0x01),
    "c": (2, 0x02),
    "x": (3, 0x40),
    "y": (3, 0x20),
    "z": (3, 0x10),
    "l": (3, 0x08),
    "r": (3, 0x80),
}

NEUTRAL_PORT1 = [0xF1, 0x02, 0xFF, 0xFF]
DISCONNECTED_PORT2 = [0xF0]


def port1_state(buttons: tuple[str, ...] = ()) -> list[int]:
    state = NEUTRAL_PORT1.copy()
    for button in buttons:
        byte_index, mask = BUTTON_BITS[button]
        state[byte_index] &= ~mask
    return state


def event(
    frame: int,
    buttons: tuple[str, ...] = (),
    port2_buttons: tuple[str, ...] | None = None,
) -> dict[str, object]:
    return {
        "frame": frame,
        "port1": port1_state(buttons),
        "port2": (
            DISCONNECTED_PORT2
            if port2_buttons is None
            else port1_state(port2_buttons)
        ),
    }


def frontend_probe(end_frame: int) -> list[dict[str, object]]:
    events = [event(1)]
    # Broad, non-mechanical probe: repeated Start and face-button pulses prove
    # controller delivery and advance legal/title/menu states. Gameplay action
    # timing is built only after the resulting screenshots identify the route.
    for frame in range(480, min(end_frame - 30, 4200), 120):
        buttons = ("start",) if (frame // 120) % 2 == 0 else ("a", "b", "c")
        events.append(event(frame, buttons))
        events.append(event(frame + 5))
    events.append(event(end_frame))
    return events


def two_player_probe(end_frame: int) -> list[dict[str, object]]:
    events = [event(1, port2_buttons=())]

    def pulse(frame: int, p1: tuple[str, ...], p2: tuple[str, ...]) -> None:
        events.append(event(frame, p1, p2))
        events.append(event(frame + 5, port2_buttons=()))

    # The first probe established the Saturn title at frame 2100 and accepted
    # P1 Start at 2160. Test a simultaneous P1/P2 join, then advance each side
    # with one B edge at a time so screenshots expose every accepted state.
    pulse(2160, ("start",), ("start",))
    for frame in range(2280, min(end_frame - 30, 3480), 90):
        pulse(frame, ("b",), ("b",))
    events.append(event(end_frame, port2_buttons=()))
    return events


def versus_probe(end_frame: int) -> list[dict[str, object]]:
    events = [event(1, port2_buttons=())]

    def pulse(
        frame: int,
        p1: tuple[str, ...] = (),
        p2: tuple[str, ...] = (),
        duration: int = 5,
    ) -> None:
        events.append(event(frame, p1, p2))
        events.append(event(frame + duration, port2_buttons=()))

    # Skip the licensed intros with Start edges at the cadence proven by the
    # first probe. The 1920 edge opens the title menu; choose Versus with one
    # Down/B pair, then expose both selectors with isolated B edges.
    for frame in range(480, 1921, 240):
        pulse(frame, ("start",))
    pulse(2040, ("down",), duration=30)
    pulse(2100, ("start",), duration=30)
    for frame in range(2340, min(end_frame - 30, 3540), 120):
        pulse(frame, ("a", "b", "c"), ("a", "b", "c"), duration=20)
    events.append(event(end_frame, port2_buttons=()))
    return events


def saturn_ryu_first_pass(end_frame: int) -> list[dict[str, object]]:
    events = [event(1, port2_buttons=())]

    def pulse(
        frame: int,
        p1: tuple[str, ...] = (),
        p2: tuple[str, ...] = (),
        duration: int = 20,
    ) -> None:
        events.append(event(frame, p1, p2))
        events.append(event(frame + duration, port2_buttons=()))

    for frame in range(480, 1921, 240):
        pulse(frame, ("start",), duration=5)
    pulse(2040, ("down",), duration=30)
    pulse(2100, ("start",), duration=30)
    # Ryu/Ken versus Spider-Man/Captain America.
    for frame in (2340, 2460):
        pulse(frame, ("a", "b", "c"), ("a", "b", "c"))
    # Force the left-side Manual option and the right-side Turbo option before
    # confirming the shared stage. Face buttons are the proven setup confirms.
    pulse(2580, ("left",), ("left",))
    pulse(2620, ("a", "b", "c"), ("a", "b", "c"))
    pulse(2700, ("right",), ("right",))
    pulse(2740, ("a", "b", "c"), ("a", "b", "c"))
    pulse(2820, ("a", "b", "c"), ("a", "b", "c"))

    # Gameplay begins near frame 3360 and settles by 3540. Keep P2 neutral.
    events.append(event(3600, ("right",), ()))
    events.append(event(3645, port2_buttons=()))
    pulse(3690, ("up",), duration=8)
    pulse(3820, ("x",), duration=8)

    events.append(event(end_frame, port2_buttons=()))
    return events


def write_record(
    output_dir: Path, backup_path: Path, end_frame: int, route: str
) -> None:
    if end_frame < 600:
        raise ValueError("end-frame must be at least 600")
    backup = backup_path.read_bytes()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "backup.bin.gz").write_bytes(zlib.compress(backup, level=9))
    route_builder = {
        "frontend-probe": frontend_probe,
        "two-player-probe": two_player_probe,
        "versus-probe": versus_probe,
        "saturn-ryu-first-pass": saturn_ryu_first_pass,
    }[route]
    first_pass_anchors = (
        420,
        1920,
        1980,
        2160,
        2340,
        2460,
        2580,
        2700,
        2820,
        3060,
        3300,
        3540,
        3600,
        3620,
        3644,
        3690,
        3720,
        3780,
        3820,
        3824,
        3828,
        3832,
        3840,
        3850,
        3900,
    )
    screenshots = (
        [frame for frame in first_pass_anchors if frame < end_frame]
        if route == "saturn-ryu-first-pass"
        else list(range(300, end_frame, 60))
    )
    record = {
        "setting": {
            "isUseBios": False,
            "date": "_1998_09_03_12_00_00",
        },
        "records": route_builder(end_frame),
        "screenshots": screenshots,
    }
    (output_dir / "record.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {len(record['records'])} controller states and "
        f"{len(screenshots)} screenshot anchors to {output_dir}."
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--end-frame", type=int, default=4800)
    parser.add_argument(
        "--route",
        choices=(
            "frontend-probe",
            "two-player-probe",
            "versus-probe",
            "saturn-ryu-first-pass",
        ),
        default="frontend-probe",
    )
    args = parser.parse_args()
    write_record(
        args.output_dir.resolve(), args.backup.resolve(), args.end_frame, args.route
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
