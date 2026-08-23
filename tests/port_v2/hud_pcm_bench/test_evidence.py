#!/usr/bin/env python3
"""Validate paired HudPcmSalvageBench target and emulator evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="ascii"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_common(state: dict[str, object], contract: dict[str, object]) -> None:
    palette = contract["hud_palette"]
    expected = {
        "runtime_ready": 1,
        "interface_version": contract["interface_version"],
        "hud_asset_failures": 0,
        "pcm_audio_failures": 0,
        "pcm_underruns": 0,
        "canary_ok": 1,
        "disc_late_reads": 0,
        "p2_hud_binding_ok": 1,
        "hud_palette_binding_ok": palette["binding_ok"],
        **{f"hud_palette_{name}": value["saturn_cram"]
           for name, value in palette["semantic_colors"].items()},
    }
    for name, value in expected.items():
        require(state[name] == value,
                f"HUD/PCM {name} was {state[name]}, expected {value}")


def check_hud(state: dict[str, object], expected: dict[str, object]) -> None:
    mapping = {
        "relative_frame": "frame",
        "hud_state": "state",
        "health": "health",
        "energy": "energy",
        "health_fill": "health_fill",
        "energy_fill": "energy_fill",
        "hud_render_count": "render_count",
    }
    for actual_name, expected_name in mapping.items():
        require(state[actual_name] == expected[expected_name],
                f"HUD {actual_name} drifted at {expected['frame']}")


def check_player2_hud(state: dict[str, object],
                      expected: dict[str, object]) -> None:
    mapping = {
        "relative_frame": "frame",
        "p2_hud_state": "state",
        "p2_health": "health",
        "p2_energy": "energy",
        "p2_health_fill": "health_fill",
        "p2_energy_fill": "energy_fill",
        "p2_hud_render_count": "render_count",
    }
    for actual_name, expected_name in mapping.items():
        require(state[actual_name] == expected[expected_name],
                f"P2 HUD {actual_name} drifted at {expected['frame']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("hud_pcm_bench", "hud", "pcm"),
                        default="hud_pcm_bench")
    args = parser.parse_args()
    suite_relative = "audio/pcm" if args.suite == "pcm" else args.suite
    suite_here = ROOT / "tests/port_v2" / suite_relative
    contract_name = ("hud_pcm_contract.json" if
                     args.suite == "hud_pcm_bench" else
                     "approved_contract.json")
    inventory = json.loads((suite_here / "inventory.json").read_text(
        encoding="utf-8"))
    contract = json.loads((suite_here / contract_name).read_text(
        encoding="utf-8"))
    builds = [load(f"build/port_v2/{args.suite}/run-{run}/build.json")
              for run in (1, 2)]
    normals = [load(f"build/port_v2/{args.suite}/run-{run}/iso-normalization.json")
               for run in (1, 2)]
    reads = [load(f"build/port_v2/{args.suite}/run-{run}/readback.json")
             for run in (1, 2)]

    require(builds[0]["source_commit"] == builds[1]["source_commit"],
            "repeat source commit drifted")
    require(builds[0]["source_tree"] == builds[1]["source_tree"],
            "repeat source tree drifted")
    require(builds[0]["compile_profile"] == inventory["compile_profile"] and
            builds[0]["manifest_profile"] == inventory["manifest_profile"],
            "HUD/PCM build profile drifted")
    require(normals[0]["normalized_iso_sha256"] ==
            normals[1]["normalized_iso_sha256"],
            "normalized HUD/PCM ISO is not deterministic")
    require(builds[0]["iso_members"] == builds[1]["iso_members"],
            "repeat HUD/PCM or regression-lock payload drifted")
    require(builds[0]["local_build_dependency_sha256"] ==
            builds[1]["local_build_dependency_sha256"] ==
            contract["local_build_dependency_sha256"],
            "local staged-loader dependency drifted")
    for name, expected in contract["payload_sha256"].items():
        require(builds[0]["iso_members"][name]["sha256"] == expected,
                f"HUD/PCM payload identity drifted: {name}")
    require(builds[0]["approved_stage_contract_sha256"] ==
            contract["approved_stage_contract_sha256"],
            "approved stage regression lock drifted")

    for report, build, normalization in zip(reads, builds, normals):
        require(report["result"] == "PASS" and
                report["physical_saturn"] == "UNRUN",
                "HUD/PCM result failed or overstated physical evidence")
        require(report["emulator"]["evidence_tier"] == "ONE_EMULATOR",
                "HUD/PCM emulator tier drifted")
        require(report["source_commit"] == build["source_commit"] and
                report["iso_sha256"] == build["artifacts"]["game_iso"]["sha256"],
                "HUD/PCM readback/build identity mismatch")
        require(normalization["production_payload_changed"] is False and
                normalization["normalized_iso_sha256"] ==
                build["artifacts"]["game_iso"]["sha256"],
                "ISO normalization changed or was not bound to the build")

        states = report["samples"]
        for state in states.values():
            check_common(state, contract)
        for label in ("zero", "mid", "full", "pcm_only"):
            check_hud(states[label], contract["hud_states"][label])
            check_player2_hud(
                states[label], contract["player2_hud_states"][label])

        together = states["together"]
        require((together["relative_frame"], together["phase"],
                 together["hud_state"], together["pcm_event_count"],
                 together["pcm_event_frame"], together["pcm_start_frame"],
                 together["pcm_end_frame"], together["pcm_active"],
                 together["pcm_channel_observed"]) ==
                (180, 1, 1, 1, 147, 150, -1, 1, 1),
                "combined HUD/PCM checkpoint drifted")
        pcm_only = states["pcm_only"]
        require((pcm_only["phase"], pcm_only["hud_state"],
                 pcm_only["hud_render_count"], pcm_only["pcm_event_count"],
                 pcm_only["pcm_event_frame"], pcm_only["pcm_start_frame"],
                 pcm_only["pcm_active"]) ==
                (3, -1, 0, 2, 387, 390, 1),
                "PCM-only checkpoint drifted")
        negative = states["negative"]
        require((negative["relative_frame"], negative["pcm_end_frame"],
                 negative["pcm_active"], negative["negative_rejections"]) ==
                (460, 440, 0, len(contract["negative_controls"])),
                "runtime negative controls did not reject deterministically")
        repeat = states["repeat_zero"]
        require(repeat["relative_frame"] == 20 and repeat["phase"] == 0 and
                repeat["pcm_event_count"] == 0,
                "bounded repeat checkpoint drifted")
        require(report["bounded_stability_frames"] > 0,
                "bounded stability interval was not observed")
        if args.suite in ("hud", "pcm"):
            for state in states.values():
                require(state["hud_production_interface_version"] ==
                        contract["production_interface_version"],
                        "HUD production interface version drifted")
                require(state["hud_port_lock_ok"] == 1,
                        "HUD semantic port lock failed")

        screenshot = ROOT / report["final_scanout"]["screenshot"]["path"]
        require(screenshot.is_file() and sha256(screenshot) ==
                report["final_scanout"]["screenshot"]["sha256"],
                "HUD/PCM screenshot is missing or changed")
        with Image.open(screenshot) as image:
            colours = image.convert("RGB").getcolors(
                maxcolors=image.width * image.height)
        require(colours is not None and len(colours) >= 8,
                "HUD/PCM screenshot has no rendered HUD")
        if args.suite == "pcm":
            for state in states.values():
                require(state["pcm_production_interface_version"] ==
                        contract["production_interface_version"],
                        "PCM production interface version drifted")
                require(state["pcm_port_lock_ok"] == 1 and
                        state["pcm_allocation_ok"] == 1,
                        "PCM port or SCSP allocation lock failed")
            require(states["together"]["pcm_semantic_active"] == 1 and
                    states["together"]["pcm_submit_count"] == 1,
                    "first semantic PCM start did not submit")
            require(states["full"]["pcm_semantic_active"] == 0 and
                    states["full"]["pcm_submit_count"] == 2,
                    "first semantic PCM stop did not submit")
            require(states["pcm_only"]["pcm_semantic_active"] == 1 and
                    states["pcm_only"]["pcm_submit_count"] == 3,
                    "second semantic PCM start did not submit")
            require(states["negative"]["pcm_semantic_active"] == 0 and
                    states["negative"]["pcm_submit_count"] == 4,
                    "second semantic PCM stop did not submit")
    if args.suite in ("hud", "pcm"):
        for label in reads[0]["samples"]:
            left = {key: value for key, value in
                    reads[0]["samples"][label].items()
                    if key != "emulator_frame"}
            right = {key: value for key, value in
                     reads[1]["samples"][label].items()
                     if key != "emulator_frame"}
            require(left == right,
                    f"paired semantic HUD state drifted at {label}")
        left_image = ROOT / reads[0]["final_scanout"]["screenshot"]["path"]
        right_image = ROOT / reads[1]["final_scanout"]["screenshot"]["path"]
        require(sha256(left_image) == sha256(right_image),
                "paired HUD screenshots differ")
    print(f"{inventory['card_profile']} evidence: PASS")


if __name__ == "__main__":
    main()
