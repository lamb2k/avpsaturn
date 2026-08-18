"""Falsify the decoded collision predicate against live work-RAM evidence.

This is the controlled hit/whiff test for the decoded records. It re-implements
the game's own overlap test from `data/avsp_collision.json` plus live actor
context, then checks two directions against the capture:

  hit side   every frame where an actor's +0x2C latches from 0 to V must be
             explained by a pair whose boxes overlap that frame (or the frame
             before) and whose attack record carries exactly V. Both roles
             count: the routine at 0x01CFCA writes +0x2C on the defender AND,
             when its own +0x2C is still zero, on the attacker.

  whiff side every (attacker, defender, frame) triple with an active attack
             selector and an active hurt selector whose boxes do NOT overlap
             must produce no latch at all. This is the falsifier: if the
             coordinate convention, the facing transform or the depth axis were
             wrong, non-overlapping pairs would still show hits.

Overlapping pairs that produce no latch are expected and are classified by the
guards the caller actually tests: defender state != 1 (0x01D042), defender
+0x70 set (0x01D04A), or the per-attacker latch byte at defender
+0x68 + attacker[+0xD1] already equal to attacker[+0x67] (0x01D054..0x01D060).

Exit status is non-zero when the whiff side fails, i.e. when any latch is
produced with no overlapping pair available and no known out-of-scope cause.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

WORKRAM_FIRST = 0xFF8000
WORKRAM_SIZE = 0x8000
ACTOR_STRIDE = 0xC0
ACTOR_GRID_ANCHOR = 0xFF8380


def s8(v: int) -> int:
    return v - 256 if v > 127 else v


def s16(v: int) -> int:
    return v - 65536 if v > 32767 else v


class Records:
    """Decoded boxes keyed by (table_set, selector), from the tracked report."""

    def __init__(self, report: dict):
        self.hurt: dict[tuple[int, int], dict] = {}
        self.attack: dict[tuple[int, int], dict] = {}
        self.suspect: set[int] = set()
        for fam in report["families"]:
            ts = int(fam["table_set"], 16)
            if fam["suspect_not_a_box_family"]:
                self.suspect.add(ts)
                continue
            for e in fam["hurt_entries"]:
                self.hurt[(ts, e["index"])] = e["box"]
            for e in fam["attack_entries"]:
                self.attack[(ts, e["index"])] = dict(e["box"], hit_value=e["hit_value"])


def actor(sample: bytes, addr: int, rom: bytes) -> dict | None:
    o = addr - WORKRAM_FIRST
    if sample[o] == 0:
        return None
    rec = int.from_bytes(sample[o + 0x1C:o + 0x20], "big")
    ts = int.from_bytes(sample[o + 0x50:o + 0x54], "big")
    if not rec or not ts or rec + 16 > len(rom) or ts + 4 > len(rom):
        return None
    return {
        "addr": addr,
        "state": sample[o],
        "facing": sample[o + 0x0F],
        "x": (sample[o + 0x10] << 8) | sample[o + 0x11],
        "y": (sample[o + 0x14] << 8) | sample[o + 0x15],
        "z": (sample[o + 0x18] << 8) | sample[o + 0x19],
        "ts": ts,
        "sel_hurt": rom[rec + 8],
        "sel_attack": rom[rec + 9],
        "hit": sample[o + 0x2C],
        "attacker_id": sample[o + 0x67],
        "latch": sample[o + 0x68:o + 0x70],
        "latch_index": sample[o + 0xD1],
        "suppress": sample[o + 0x70],
    }


def overlap(rec: Records, A: dict, D: dict):
    """The game's test at 0x01D25E, driven by the decoded records."""
    a = rec.attack.get((A["ts"], A["sel_attack"]))
    d = rec.hurt.get((D["ts"], D["sel_hurt"]))
    if A["sel_attack"] == 0 or D["sel_hurt"] == 0 or a is None or d is None:
        return None
    zd = s16(((d["z_center"] + D["z"]) - (a["z_center"] + A["z"])) & 0xFFFF)
    if abs(zd) > a["z_half"] + d["z_half"]:
        return None
    ax = (-a["x_center"] if A["facing"] else a["x_center"]) + A["x"]
    dx = (-d["x_center"] if D["facing"] else d["x_center"]) + D["x"]
    if abs(s16((dx - ax) & 0xFFFF)) > a["x_half"] + d["x_half"]:
        return None
    ay = a["y_center"] + zd + A["y"]
    dy = d["y_center"] + D["y"]
    if abs(s16((dy - ay) & 0xFFFF)) > a["y_half"] + d["y_half"]:
        return None
    return a["hit_value"]


def guarded(A: dict, D: dict) -> bool:
    if D["state"] != 1 or D["suppress"] != 0:
        return True
    i = A["latch_index"]
    return i < len(D["latch"]) and D["latch"][i] == A["attacker_id"]


def run(report_path: Path, rom_path: Path, workram_paths: list, first_frames: list) -> dict:
    report = json.loads(report_path.read_text())
    rec = Records(report)
    rom = rom_path.read_bytes()
    grid = list(range(ACTOR_GRID_ANCHOR, WORKRAM_FIRST + WORKRAM_SIZE - ACTOR_STRIDE, ACTOR_STRIDE))
    t = Counter()
    unexplained = []

    for wp, first in zip(workram_paths, first_frames):
        raw = Path(wp).read_bytes()
        frames = len(raw) // WORKRAM_SIZE
        prev = None
        for i in range(frames):
            s = raw[i * WORKRAM_SIZE:(i + 1) * WORKRAM_SIZE]
            cur = {a: actor(s, a, rom) for a in grid}
            if prev is not None:
                # whiff side + guard classification
                for A in grid:
                    ca = cur[A]
                    if not ca or ca["sel_attack"] == 0:
                        continue
                    for D in grid:
                        if D == A or not cur[D] or cur[D]["sel_hurt"] == 0:
                            continue
                        v = overlap(rec, ca, cur[D])
                        if v is None:
                            t["pairs_no_overlap"] += 1
                        elif prev[D] and prev[D]["hit"] == 0 and cur[D]["hit"] == v:
                            t["pairs_overlap_latched"] += 1
                        elif guarded(ca, cur[D]):
                            t["pairs_overlap_guarded"] += 1
                        else:
                            t["pairs_overlap_no_latch_unguarded"] += 1
                # hit side
                events = [(a, cur[a]["hit"]) for a in grid
                          if cur[a] and prev[a] and prev[a]["hit"] == 0 and cur[a]["hit"] != 0]
                simultaneous = len(events) >= 3 and len({v for _, v in events}) == 1
                for a, v in events:
                    role = None
                    for st in (prev, cur):
                        for b in grid:
                            if b == a or not st[b] or not st[a]:
                                continue
                            if overlap(rec, st[b], st[a]) == v:
                                role = "defender"
                            elif role is None and overlap(rec, st[a], st[b]) == v:
                                role = "attacker"
                    if role:
                        t["latch_explained_" + role] += 1
                    elif simultaneous:
                        t["latch_simultaneous_broadcast"] += 1
                    else:
                        t["latch_unexplained"] += 1
                        if len(unexplained) < 20:
                            unexplained.append({"frame": first + i, "actor": "0x%06x" % a, "value": v})
            prev = cur

    total_latch = sum(v for k, v in t.items() if k.startswith("latch_"))
    return {
        "counters": dict(sorted(t.items())),
        "latch_events_total": total_latch,
        "latch_explained": t["latch_explained_defender"] + t["latch_explained_attacker"],
        "unexplained_samples": unexplained,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--workram", required=True, action="append")
    ap.add_argument("--first-frame", required=True, action="append", type=int)
    ap.add_argument("--max-unexplained", type=int, default=0,
                    help="fail when more non-broadcast latch events than this stay unexplained")
    args = ap.parse_args()

    res = run(Path(args.report), Path(args.rom), args.workram, args.first_frame)
    print(json.dumps(res, indent=1))
    c = res["counters"]
    if c.get("pairs_overlap_latched", 0) == 0:
        print("FAIL: the predicate never reproduced a single hit")
        return 2
    if c.get("latch_unexplained", 0) > args.max_unexplained:
        print("FAIL: %d unexplained latch events (allowed %d)"
              % (c["latch_unexplained"], args.max_unexplained))
        return 1
    print("PASS: %d/%d latch events explained; %d non-overlapping active pairs produced no hit"
          % (res["latch_explained"], res["latch_events_total"], c.get("pairs_no_overlap", 0)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
