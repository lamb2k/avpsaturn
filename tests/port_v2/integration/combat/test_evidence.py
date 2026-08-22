#!/usr/bin/env python3
"""Validate paired INTEGRATE-02 build and pinned-emulator evidence."""

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build/port_v2/integration/combat"


def load(path):
    return json.loads(path.read_text(encoding="ascii"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    builds = [load(BUILD / f"run-{run}/build.json") for run in (1, 2)]
    normals = [load(BUILD / f"run-{run}/iso-normalization.json")
               for run in (1, 2)]
    reads = [load(BUILD / f"run-{run}/readback.json") for run in (1, 2)]
    overlay = load(HERE / "tile_overlay_contract.json")
    require(builds[0] == builds[1], "combat target builds are not identical")
    require(normals[0]["normalized_iso_sha256"] ==
            normals[1]["normalized_iso_sha256"],
            "normalized combat ISO is not deterministic")
    require(reads[0]["iso_sha256"] == reads[1]["iso_sha256"] ==
            normals[0]["normalized_iso_sha256"],
            "combat build/readback ISO identities disagree")
    for key in ("events", "hit_state", "final_state"):
        require(reads[0][key] == reads[1][key],
                f"combat deterministic {key} drifted")
    for report in reads:
        require(report["result"] == "PASS" and
                report["physical_saturn"] == "UNRUN" and
                report["emulator"]["evidence_tier"] == "ONE_EMULATOR",
                "combat evidence tier/result drifted")
        require(report["hit_state"]["combat_frame"] == 185 and
                report["hit_state"]["combat_presented_frame"] == 185 and
                report["final_state"]["combat_frame"] == 860 and
                report["final_state"]["combat_presented_frame"] == 860,
                "combat readback was not sampled at exact frames")
        for state in (report["hit_state"], report["final_state"]):
            require(state["enemy_tile_bank_misses"] == 0 and
                    state["enemy_tile_rank_misses"] == 0 and
                    state["combat_missing_code_count"] == 0,
                    "combat source tile coverage regressed")
        for shot in report["screenshots"].values():
            path = ROOT / shot["path"]
            require(path.is_file() and sha(path) == shot["sha256"],
                    "combat screenshot identity drifted")
            with Image.open(path) as image:
                colours = image.convert("RGB").getcolors(
                    maxcolors=image.width * image.height)
                require(image.width > 300 and image.height > 200 and
                        colours is not None and len(colours) >= 16,
                        "combat screenshot is empty")
    member = builds[0]["asset_members"]["/SPR4/COMBAT.BIN"]
    require(member == {"bytes": overlay["archive_bytes"],
                       "sha256": overlay["archive_sha256"]},
            "combat tile overlay identity drifted")
    require(builds[0]["asset_members"]["/SPR4/TILES.BIN"]["sha256"] ==
            overlay["approved_base_archive_sha256"],
            "approved street tile archive changed")
    require(builds[0]["asset_members"]["/SPR4/TILES.BIN"]["bytes"] +
            member["bytes"] <= 0x50000,
            "combat tile assets exceed the existing cartridge carve")
    print("INTEGRATE-02 paired emulator evidence: PASS")


if __name__ == "__main__":
    main()
