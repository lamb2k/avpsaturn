"""Summarize a bounded stock-MAME actor writer watchpoint trace."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ERROR_LOG = ROOT / "error.log"
OUTPUT = ROOT / "data" / "actor_writer_watchpoints.json"
PATTERN = re.compile(
    r"AVP_WP_(?P<kind>ANIM|ACTION|STATE) "
    r"addr=(?P<address>[0-9A-Fa-f]+) "
    r"data=(?P<data>[0-9A-Fa-f]+) "
    r"pc=(?P<pc>[0-9A-Fa-f]+)"
)


def main() -> None:
    events: list[dict[str, int | str]] = []
    for line in ERROR_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        match = PATTERN.search(line)
        if not match:
            continue
        event = {
            "kind": match.group("kind").lower(),
            "address": int(match.group("address"), 16),
            "data": int(match.group("data"), 16),
            "pc": int(match.group("pc"), 16),
        }
        events.append(event)
    if not events:
        raise ValueError(f"No AVP watchpoint events found in {ERROR_LOG}")

    by_kind = Counter(str(event["kind"]) for event in events)
    by_kind_pc: dict[str, Counter[str]] = defaultdict(Counter)
    by_kind_address: dict[str, Counter[str]] = defaultdict(Counter)
    for event in events:
        kind = str(event["kind"])
        by_kind_pc[kind][f"0x{int(event['pc']):06x}"] += 1
        by_kind_address[kind][f"0x{int(event['address']):06x}"] += 1

    report = {
        "schema": 1,
        "classification": "capture-exact stock-MAME debugger evidence",
        "source": {
            "state": "avspu_stage1_debug_hitboxes",
            "state_frame": 4200,
            "post_load_frames": 600,
            "watchpoint_api": "stock MAME 0.289 debugger:wpset",
            "raw_log": "error.log (ignored)",
        },
        "event_count": len(events),
        "counts_by_kind": dict(sorted(by_kind.items())),
        "writer_pcs_by_kind": {
            kind: dict(counter.most_common())
            for kind, counter in sorted(by_kind_pc.items())
        },
        "actor_addresses_by_kind": {
            kind: dict(counter.most_common())
            for kind, counter in sorted(by_kind_address.items())
        },
        "primary_animation_writer_pcs": [
            "0x01652a", "0x016550", "0x0165de", "0x016636"
        ],
        "next_step": (
            "Disassemble the primary animation writers and identify the state "
            "field offsets and call boundaries before translating them."
        ),
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(f"Validated {len(events)} stock-MAME actor writer events: {OUTPUT}")


if __name__ == "__main__":
    main()
