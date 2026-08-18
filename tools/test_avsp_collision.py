"""Focused host tests for the decoded collision format.

These check the structure of `data/avsp_collision.json` and a small number of
anchors that would break immediately if the record layout, the table-set
dereference or the entry strides were wrong. They do not need the ROM image or
any capture, so they run anywhere the tracked report is present.

Run: python tools/test_avsp_collision.py [--report data/avsp_collision.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print("  ok   %s" % name)
    else:
        FAILURES.append("%s%s" % (name, (": " + detail) if detail else ""))
        print("  FAIL %s%s" % (name, (": " + detail) if detail else ""))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", default=str(ROOT / "data" / "avsp_collision.json"))
    args = ap.parse_args()
    report = json.loads(Path(args.report).read_text())

    print("structure")
    check("schema is 1", report.get("schema") == 1)
    check("no ROM bytes are present in the report",
          "rom_bytes" not in json.dumps(report))
    check("at least one family decoded", report["family_count"] > 0)

    trusted = [f for f in report["families"] if not f["suspect_not_a_box_family"]]
    suspect = [f for f in report["families"] if f["suspect_not_a_box_family"]]
    check("trusted families exist", len(trusted) > 0)
    check("suspect families carry a reason",
          all(f["suspect_reason"] for f in suspect))

    print("per-family invariants")
    for f in trusted:
        ts = f["table_set"]
        check("%s hurt stride is 8" % ts, f["hurt_entry_stride"] == 8)
        check("%s attack stride is 16" % ts, f["attack_entry_stride"] == 16)
        hurt_base = int(f["hurt_table"], 16)
        attack_base = int(f["attack_table"], 16)
        check("%s attack table follows the hurt table" % ts, attack_base > hurt_base)
        check("%s hurt count matches the gap" % ts,
              (attack_base - hurt_base) // 8 == f["hurt_count"],
              "gap %d, count %d" % (attack_base - hurt_base, f["hurt_count"]))
        for e in f["hurt_entries"]:
            check("%s hurt[%d] address" % (ts, e["index"]),
                  int(e["address"], 16) == hurt_base + e["index"] * 8)
            b = e["box"]
            check("%s hurt[%d] half-extents unsigned" % (ts, e["index"]),
                  0 <= b["x_half"] <= 255 and 0 <= b["y_half"] <= 255 and 0 <= b["z_half"] <= 255)
            check("%s hurt[%d] centres signed byte range" % (ts, e["index"]),
                  all(-128 <= b[k] <= 127 for k in ("x_center", "y_center", "z_center")))
        for e in f["attack_entries"]:
            check("%s attack[%d] address" % (ts, e["index"]),
                  int(e["address"], 16) == attack_base + e["index"] * 16)

    print("selector-0 records are inactive")
    # The callers reject selector 0 before any table read (0x01CF8C / 0x01CF98),
    # so entry 0 must never describe a live box.
    for f in trusted:
        if f["hurt_entries"]:
            check("%s hurt[0] inactive" % f["table_set"], f["hurt_entries"][0]["inactive"])
        if f["attack_entries"]:
            check("%s attack[0] inactive" % f["table_set"], f["attack_entries"][0]["inactive"])

    print("anchors proven by the falsification run")
    fam = {f["table_set"]: f for f in report["families"]}
    alien = fam.get("0x130ac8")
    check("street-alien family present", alien is not None)
    if alien:
        check("street-alien hurt table at 0x130acc", alien["hurt_table"] == "0x130acc")
        check("street-alien attack table at 0x130b4c", alien["attack_table"] == "0x130b4c")
        check("street-alien hurt table holds 16 entries", alien["hurt_count"] == 16)
        check("street-alien melee deals 10",
              any(e["hit_value"] == 10 for e in alien["attack_entries"]))
    player = fam.get("0x11ae02")
    check("player family present", player is not None)
    if player:
        check("player hurt table holds 24 entries", player["hurt_count"] == 24)
        idx11 = [e for e in player["attack_entries"] if e["index"] == 11]
        check("player attack selector 11 exists", len(idx11) == 1)
        if idx11:
            check("player attack selector 11 deals 3", idx11[0]["hit_value"] == 3,
                  "got %r" % idx11[0]["hit_value"])

    print()
    if FAILURES:
        print("%d check(s) failed" % len(FAILURES))
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
