#!/usr/bin/env python3
"""Active-P2 HUD source, asset, semantic-state and negative controls."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(contract: dict[str, object], source: dict[str, object]) -> None:
    require(contract["task_id"] == source["task_id"] ==
            "SALVAGE-05B-PLAYER-2-HUD", "P2 HUD task identity drifted")
    require(contract["interface_version"] == 3,
            "P2 HUD diagnostic interface drifted")
    require(source["capture"]["active_repeat_byte_identical"] is True and
            source["capture"]["active_file_count"] == 182,
            "P2 HUD source repeat is not deterministic")
    active = source["active_player2_hud"]
    require(active["top_asset"]["placement"] == [176, 0] and
            active["top_asset"]["size"] == [176, 40] and
            active["weapon_asset"]["placement"] == [220, 208] and
            active["weapon_asset"]["size"] == [120, 16],
            "P2 HUD placement drifted")
    require(active["health_field"]["rect"] == [213, 18, 132, 4] and
            active["weapon_field"]["rect"] == [264, 218, 59, 4],
            "P2 HUD semantic fields drifted")
    require(source["negative_control"]["rejected_binding"] ==
            contract["negative_control"]["rejected_asset"] and
            source["negative_control"]["frame_3000_sha256"] !=
            source["capture"]["active_evidence_sha256"]["frame_3000.png"],
            "PRESS START control did not reject active P2 HUD binding")
    require(contract["player2_payload_sha256"] == {
        active["top_asset"]["path"]: active["top_asset"]["sha256"],
        active["weapon_asset"]["path"]: active["weapon_asset"]["sha256"],
    }, "P2 HUD payload contract disagrees with source binding")
    require(contract["regression_payload_sha256"] ==
            source["regression_locks"], "P1/PCM locks drifted")
    require(contract["physical_saturn"] == source["physical_saturn"] ==
            "UNRUN", "physical evidence was overstated")


def static_and_private_evidence(contract: dict[str, object],
                                source: dict[str, object]) -> None:
    require(sha256(ROOT / contract["source_evidence"]) ==
            contract["source_evidence_sha256"],
            "P2 HUD tracked source evidence changed")
    require(sha256(ROOT / source["capture"]["tool"]) ==
            source["capture"]["tool_sha256"], "capture tool drifted")
    require(sha256(ROOT / source["conversion"]["tool"]) ==
            source["conversion"]["tool_sha256"], "extractor drifted")
    private = ROOT / ".deps/mame/player2_hud"
    active1 = private / "active_bind_1"
    active2 = private / "active_bind_2"
    for name, digest in source["capture"]["active_evidence_sha256"].items():
        require(sha256(active1 / name) == sha256(active2 / name) == digest,
                f"P2 HUD private repeat drifted: {name}")
    require(sha256(private / "prompt_bind/frame_3000.png") ==
            source["negative_control"]["frame_3000_sha256"],
            "P2 HUD prompt-control capture drifted")
    for name, digest in {**contract["player2_payload_sha256"],
                         **contract["regression_payload_sha256"]}.items():
        require(sha256(ROOT / "build/avsp_cd" / name.lstrip("/")) == digest,
                f"HUD/PCM generated payload drifted: {name}")
    main = (ROOT / "main.c").read_text(encoding="utf-8")
    for token in ("HUD2TOP.BIN", "HUD2HEAT.BIN",
                  "hud_pcm_player2_binding_valid",
                  "avsp_diag_hud_p2_binding_ok"):
        require(token in main, f"missing P2 HUD runtime wiring: {token}")
    require("jo_is_pad2" not in main,
            "P2 gameplay input entered the presentation-only card")


def negative_controls(contract: dict[str, object],
                      source: dict[str, object]) -> None:
    mutations = []
    wrong_prompt = copy.deepcopy(source)
    wrong_prompt["negative_control"]["frame_3000_sha256"] = \
        wrong_prompt["capture"]["active_evidence_sha256"]["frame_3000.png"]
    mutations.append((contract, wrong_prompt))
    wrong_placement = copy.deepcopy(source)
    wrong_placement["active_player2_hud"]["top_asset"]["placement"] = [0, 0]
    mutations.append((contract, wrong_placement))
    wrong_lock = copy.deepcopy(contract)
    wrong_lock["regression_payload_sha256"]["/AUDIO/MELEE.PCM"] = "0" * 64
    mutations.append((wrong_lock, source))
    for candidate_contract, candidate_source in mutations:
        try:
            validate(candidate_contract, candidate_source)
        except AssertionError:
            continue
        raise AssertionError("P2 HUD perturbation was not rejected")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    contract = json.loads((HERE / "player2_hud_contract.json").read_text(
        encoding="utf-8"))
    source = json.loads((ROOT / contract["source_evidence"]).read_text(
        encoding="utf-8"))
    validate(contract, source)
    if args.negative_control:
        negative_controls(contract, source)
        print("Player 2 HUD perturbation controls: PASS")
    else:
        static_and_private_evidence(contract, source)
        print("Player 2 HUD contract: PASS")


if __name__ == "__main__":
    main()
