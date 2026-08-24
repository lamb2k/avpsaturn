#!/usr/bin/env python3
"""Independent MAME source-event contract for Repair 09.

The expected identities below come from the two byte-identical cadence-1 MAME
captures.  They are deliberately not regenerated from Saturn output.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
CONTRACT = ROOT / "data/avsp_source_combat_presentation_contract.json"
CACHE = ROOT / ".deps/mame/source_bound_combat/PCMBT.RLE"

EXPECTED = (
    (1, 5190, 8, "0x1600f8", "ee766bd52f91fe10187416d281bb9f3329391f84ff5a72eca93e5ce4527d1f24",
     "53e26b806b696e6222aa93f35c3ea344159e80e196512633ee86be37ea9d76ef",
     "0x12eb4c", "0x12dd50", "61c1223c9874d20311be20e081423bd1b0dbaed44661faccc28ff2b817cdd33f",
     "e3894d39fc1282584e6a2b059e45a48e670266036ae9fe5bf8554be7af6a3d69"),
    (2, 5236, 8, "0x16014c", "12e3f997e83f0a1f4be802aa34431457e5c101116437680eef3cc39187846b1e",
     "42f832db62d027b59d4a8096081c8de2829b06f514c4c0f2e93fc9f263640c2f",
     "0x12eb1c", "0x12dd28", "e52465b83b30da50d27b0b3058e35af94fccc3ffb2a2c46363c58f00d4ba5825",
     "422f8da6f547cea715d1199f757bec46f715dbaf344acc5c20a60dbb6259fdc5"),
    (3, 5283, 10, "0x1601c0", "145b01b71728db79565be26179aebeadbfa3d98793fe7c1135d34eabc76b9af8",
     "c584258f556ba32e208ee39bc08ddf664d07c4e87c5636f95184edbaa9e42f33",
     "0x12eb0c", "0x12dd3c", "f12b7a5fe904c80fdd4fd5bb9eaee1e986ed5e377634262a6daa440f89496986",
     "47eddb0a67d92847c87c39c175414a261b77500677de6cef9f599f9f0ebcaff0"),
    (4, 5329, 12, "0x160234", "10e9d30e5060f719a5e036653b4a4e0d6be2d554e70fab89d99d38067d7a0661",
     "714cbeadeb5e130853dafad974895a73f1aa8090d0b692f839b91f82f8a6be9c",
     "0x12eb1c", "0x12e214", "e52465b83b30da50d27b0b3058e35af94fccc3ffb2a2c46363c58f00d4ba5825",
     "422f8da6f547cea715d1199f757bec46f715dbaf344acc5c20a60dbb6259fdc5"),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate(contract: dict) -> None:
    source = contract["source"]
    require(source["byte_identical_reruns"], "MAME reruns are not identical")
    require(source["pinned_oracle_subset_match"], "pinned oracle subset drifted")
    require(contract["contact_offsets"] == [0, 46, 93, 139],
            "source-relative contact timing drifted")
    require(contract["event_pipeline"].startswith("one event binds selector"),
            "event pipeline no longer states the coherent binding")
    timeline = contract["source_enemy_timeline"]
    require(timeline["semantic_first"] == 5173 and
            timeline["semantic_last"] == 5469 and
            timeline["row_count"] == 297 and
            timeline["sequence_sha256"] ==
            "53e2066246f1487d5759504aa6dfd2e1e418dd6b7743f20b83726f9f4e441bc2",
            "cadence-1 street-alien timeline drifted")
    require(len(contract["events"]) == 4, "source event count drifted")
    for event, expected in zip(contract["events"], EXPECTED):
        (selector, frame, hit_value, player_record, player_object, player_tile,
         alien_contact_record, alien_reaction_record, alien_object,
         alien_tile) = expected
        require(event["attack_selector"] == selector and
                event["attack_sequence_step"] == selector,
                "selector is no longer bound to its attack sequence")
        require(event["contact_frame"] == frame,
                "contact frame is no longer source-relative")
        require(event["health_after"] < event["health_before"],
                "source contact no longer supplies damage")
        collision = event["collision"]
        require(collision["player_table_set"] == "0x11ae02" and
                collision["attack_selector"] == selector and
                collision["hit_value"] == hit_value and
                collision["enemy_table_set"] == "0x130ac8" and
                collision["hurt_selector"] == 1 and
                collision["overlap_result"] is True and
                event["hit_value"] == hit_value,
                "collision selector, overlap, hit value, and damage detached")
        player = event["player"]
        contact = event["enemy_contact"]
        reaction = event["enemy_reaction"]
        require((player["animation_record"],
                 player["object_identity_sha256"],
                 player["tile_identity_sha256"]) ==
                (player_record, player_object, player_tile),
                "rendered player attack is detached from the source event")
        require(contact["slot"] == "0xffa000" and
                contact["class_id"] == 31 and contact["type"] == 12 and
                contact["palette"] == 19 and reaction["palette"] == 19,
                "street-alien identity or palette drifted")
        require(contact["animation_record"] == alien_contact_record and
                reaction["animation_record"] == alien_reaction_record and
                reaction["object_identity_sha256"] == alien_object and
                reaction["tile_identity_sha256"] == alien_tile,
                "alien reaction is detached from the damaging source event")
        require(reaction["source_render_frame"] ==
                reaction["first_visible_frame"] + 1,
                "measured alien render-pipeline delay drifted")
    archive = contract["source_player_archive"]
    require(CACHE.is_file(), "pinned source player archive is missing")
    payload = CACHE.read_bytes()
    require(len(payload) == archive["bytes"] and
            hashlib.sha256(payload).hexdigest() == archive["sha256"],
            "pinned source player archive identity drifted")
    require(contract["physical_saturn"] == "UNRUN",
            "non-physical evidence was relabeled as physical Saturn proof")


def expect_rejection(contract: dict, mutate, label: str) -> None:
    wrong = copy.deepcopy(contract)
    mutate(wrong)
    try:
        validate(wrong)
    except AssertionError:
        print(f"REPAIR-09 {label}: REJECTED")
        return
    raise AssertionError(f"{label} mutation was accepted")


def main() -> None:
    contract = json.loads(CONTRACT.read_text())
    validate(contract)
    expect_rejection(contract,
                     lambda value: value["events"][0].update(attack_selector=2),
                     "wrong selector")
    expect_rejection(contract,
                     lambda value: value["events"][0]["player"].update(
                        object_identity_sha256=EXPECTED[1][4]),
                     "wrong nonzero player object family")
    expect_rejection(contract,
                     lambda value: value["events"][0]["player"].update(
                        tile_identity_sha256=EXPECTED[1][5]),
                     "wrong nonzero player tile family")
    expect_rejection(contract,
                     lambda value: value["events"][0]["enemy_reaction"].update(
                        object_identity_sha256=EXPECTED[1][8]),
                     "wrong nonzero alien object family")
    expect_rejection(contract,
                     lambda value: value["events"][0]["enemy_reaction"].update(
                        tile_identity_sha256=EXPECTED[1][9]),
                     "wrong nonzero alien tile family")
    expect_rejection(contract,
                     lambda value: value["events"][0]["enemy_reaction"].update(
                         palette=18),
                     "wrong alien palette")
    print("REPAIR-09 coherent source-event presentation contract: PASS")


if __name__ == "__main__":
    main()
