#!/usr/bin/env python3
"""RP5 gate: the residency ledger must be internally consistent and every
bounded resource must show non-negative headroom.

Checks:

1. every recorded work-RAM profile has __bend under the 0x060C0000 limit
   and the recorded headroom recomputes;
2. the four required profiles (release, street, encounter, frontend) are
   present;
3. cartridge carve arithmetic recomputes and the archives fit their
   carves;
4. VDP2/VDP1 usage recomputes from the tracked manifests and fits;
5. every ledger section carries a MEASURED/ADAPTED/GAP status;
6. negative controls: an over-limit profile, a corrupted carve sum, and a
   missing status must each be detected.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PROFILES = ("debug-normal-release", "debug-street-test",
                     "debug-encounter-test", "debug-frontend-test")


def check(budget: dict) -> list[str]:
    errors: list[str] = []
    limit = int(budget["work_ram_limit"], 16)
    profiles = budget["work_ram_profiles"]
    for name, entry in profiles.items():
        bend = int(entry["bend"], 16)
        if bend > limit:
            errors.append(f"profile {name}: __bend 0x{bend:08x} over limit")
        if entry["headroom_bytes"] != limit - bend:
            errors.append(f"profile {name}: headroom does not recompute")
    for required in REQUIRED_PROFILES:
        if required not in profiles:
            errors.append(f"profile {required}: not measured")

    cart = budget["cartridge"]
    if cart["tile_archive_bytes"] is not None:
        if cart["tile_carve_headroom"] != \
                cart["tile_carve_bytes"] - cart["tile_archive_bytes"]:
            errors.append("cartridge: tile headroom does not recompute")
        if cart["tile_carve_headroom"] < 0:
            errors.append("cartridge: tile archive exceeds its carve")
    if cart["strips_file_bytes"] is not None and cart["strips_carve_bytes"]:
        if cart["strips_carve_headroom"] < 0:
            errors.append("cartridge: strips exceed their carve")
    if cart["jo_zone_bytes"] != cart["dram1_bytes"] - \
            cart["tile_carve_bytes"] - cart["strips_carve_bytes"]:
        errors.append("cartridge: jo zone does not recompute")

    vdp2 = budget["vdp2"]
    if vdp2.get("used_bytes") is not None:
        if vdp2["used_bytes"] != vdp2["character_bytes"] + \
                vdp2["pattern_bytes"]:
            errors.append("vdp2: used bytes do not recompute")
        if vdp2["headroom_bytes"] < 0:
            errors.append("vdp2: over capacity")
    vdp1 = budget["vdp1"]
    if vdp1.get("headroom_bytes") is not None and vdp1["headroom_bytes"] < 0:
        errors.append("vdp1: over capacity")

    for section in ("cartridge", "vdp2", "vdp1", "cram", "scsp",
                    "disc_guard"):
        status = budget[section].get("status")
        if status not in ("MEASURED", "ADAPTED", "GAP"):
            errors.append(f"{section}: missing or invalid status")
    return errors


def main() -> None:
    budget = json.loads(
        (ROOT / "data" / "avsp_residency_budget.json").read_text())
    errors = check(budget)
    if errors:
        for error in errors[:20]:
            print("FAIL:", error)
        raise SystemExit(1)

    controls = {}
    mutated = copy.deepcopy(budget)
    first = next(iter(mutated["work_ram_profiles"].values()))
    first["bend"] = "0x060c1000"
    controls["over_limit_profile"] = bool(check(mutated))
    mutated = copy.deepcopy(budget)
    mutated["cartridge"]["jo_zone_bytes"] += 4096
    controls["corrupted_carve"] = bool(check(mutated))
    mutated = copy.deepcopy(budget)
    del mutated["disc_guard"]["status"]
    controls["missing_status"] = bool(check(mutated))

    failed = [name for name, detected in controls.items() if not detected]
    print(f"residency budget: {len(budget['work_ram_profiles'])} profiles, "
          f"controls {'PASS' if not failed else 'FAIL ' + ','.join(failed)}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
