#!/usr/bin/env python3
"""Validate paired PlayerEnemyIntegration build and emulator evidence."""

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def require(value, message):
    if not value:
        raise AssertionError(message)


def load(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_state(state, contract, expected):
    player = state["player"]
    enemy = state["enemy"]
    integration = state["integration"]
    require(state["runtime_ready"] == 1, "integration was not runtime-ready")
    require((state["requested_enemy_frame"], enemy["relative_frame"],
             enemy["phase"], enemy["x"]) ==
            (expected["frame"], expected["frame"],
             expected["phase"], expected["x"]),
            "enemy schedule drifted")
    require((enemy["class_id"], enemy["palette_bank"], enemy["lane"],
             enemy["facing"], enemy["object_count"], enemy["render_count"]) ==
            (31, 17, 200, -1, 5, 32), "enemy approved view drifted")
    require(enemy["approval_lock_ok"] == enemy["loader_adapter_ok"] == 1,
            "enemy promotion lock drifted")
    require(player["interface_version"] == player["approval_lock_ok"] ==
            player["loader_adapter_ok"] == 1, "player promotion lock drifted")
    require(player["render_count"] in (2, 3), "player layer count drifted")
    require(0 <= player["cel_left"] < player["cel_right"] <= 192 and
            0 <= player["cel_top"] < player["cel_bottom"] <= 192,
            "player cel bounds drifted")
    require(integration["interface_version"] == 1 and
            integration["approval_locks_ok"] == 1 and
            integration["loader_order_ok"] == 1 and
            integration["actor_count"] == contract["actor_count"] and
            integration["render_order_ok"] == 1,
            "integration interface/order drifted")
    require(integration["render_command_count"] ==
            player["render_count"] + enemy["render_count"],
            "combined render count drifted")
    require(integration["canaries_ok"] == 1 and
            integration["asset_failures"] == 0 and
            integration["disc_late_reads"] == 0,
            "integration memory/asset invariant drifted")


def main():
    inventory = json.loads((HERE / "inventory.json").read_text())
    contract = json.loads((HERE / "approved_contract.json").read_text())
    base = inventory["build_root"]
    builds = [load(f"{base}/run-{run}/build.json") for run in (1, 2)]
    normals = [load(f"{base}/run-{run}/iso-normalization.json")
               for run in (1, 2)]
    reads = [load(f"{base}/run-{run}/readback.json") for run in (1, 2)]
    require(builds[0]["result"] == builds[1]["result"] == "PASS",
            "integration build record failed")
    require(builds[0]["source_commit"] == builds[1]["source_commit"],
            "repeat source commit drifted")
    require(builds[0]["source_tree"] == builds[1]["source_tree"],
            "repeat source tree drifted")
    require(builds[0]["compile_profile"] == inventory["compile_profile"],
            "compile profile drifted")
    require(builds[0]["manifest_profile"] == inventory["manifest_profile"],
            "manifest profile drifted")
    require(builds[0]["asset_members"] == builds[1]["asset_members"],
            "approved asset payloads drifted between repeats")
    require(builds[0]["approved_lock_sha256"] ==
            builds[1]["approved_lock_sha256"] == contract["approved_lock_sha256"],
            "approved component lock identity drifted")
    require(normals[0]["normalized_iso_sha256"] ==
            normals[1]["normalized_iso_sha256"],
            "normalized integration ISO is not deterministic")
    for build, normal, report in zip(builds, normals, reads):
        require(normal["production_payload_changed"] is False,
                "normalizer changed a production payload")
        require(build["artifacts"]["game_iso"]["sha256"] ==
                normal["normalized_iso_sha256"] == report["iso_sha256"],
                "build/readback ISO identity drifted")
        require(report["source_commit"] == build["source_commit"],
                "build/readback commit identity drifted")
        require(report["result"] == "PASS" and
                report["physical_saturn"] == "UNRUN" and
                report["emulator"]["evidence_tier"] == "ONE_EMULATOR",
                "evidence tier/result drifted")
        for label, expected in contract["enemy"]["samples"].items():
            check_state(report["samples"][label], contract, expected)
        right = report["player_input"]["right"]
        require(right["during"]["input_mask"] & 2 and
                right["during"]["input_edges"] & 2,
                "right input edge was not sampled")
        require(right["after"]["x"] > right["before"]["x"] and
                right["after"]["facing"] == 1 and
                right["during"]["render_count"] == 3,
                "player movement/walk layers drifted")
        for state in report["samples"].values():
            require(state["integration"]["render_command_count"] ==
                    contract["idle_render_commands"],
                    "sampled idle combined render count drifted")
        require(report["vdp1_command_count"] >= contract["idle_render_commands"],
                "VDP1 command list is too short")
        screenshot = ROOT / report["screenshot"]["path"]
        require(screenshot.is_file() and sha(screenshot) ==
                report["screenshot"]["sha256"], "screenshot identity drifted")
        with Image.open(screenshot) as image:
            colours = image.convert("RGB").getcolors(
                maxcolors=image.width * image.height)
        require(colours is not None and len(colours) >= 16,
                "integration screenshot has no rendered scene")
    print("PlayerEnemyIntegration evidence: PASS")


if __name__ == "__main__":
    main()
