#!/usr/bin/env python3
"""Validate paired exact-release INTEGRATE-03 emulator evidence."""

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
BUILD = ROOT / "build/port_v2/integration/slice"


def load(path):
    return json.loads(path.read_text(encoding="ascii"))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_state(report, name):
    state = dict(report[name])
    state.pop("slice_frame_stage", None)
    state.pop("slice_frame", None)
    state.pop("slice_stability_frames", None)
    state.pop("slice_stage_submissions", None)
    state.pop("slice_player_action_frame", None)
    state.pop("slice_enemy_action_frame", None)
    return state


def main():
    builds = [load(BUILD / f"run-{run}/build.json") for run in (1, 2)]
    normals = [load(BUILD / f"run-{run}/iso-normalization.json")
               for run in (1, 2)]
    reads = [load(BUILD / f"run-{run}/readback.json") for run in (1, 2)]
    traces = [load(BUILD / f"run-{run}/scene-trace.json")
              for run in (1, 2)]
    require(builds[0] == builds[1], "exact release builds are not identical")
    require(builds[0]["compile_profile"] == "release-normal-release" and
            builds[0]["manifest_profile"] == "normal-release" and
            builds[0]["exact_normal_release"] is True,
            "paired build is not the exact normal release")
    require(normals[0]["normalized_iso_sha256"] ==
            normals[1]["normalized_iso_sha256"],
            "normalized release ISO is not deterministic")
    for report, build, normal in zip(reads, builds, normals):
        require(report["result"] == "PASS" and
                report["physical_saturn"] == "UNRUN" and
                report["emulator"]["evidence_tier"] == "ONE_EMULATOR",
                "evidence result or tier drifted")
        require(report["iso_sha256"] ==
                build["artifacts"]["game_iso"]["sha256"] ==
                normal["normalized_iso_sha256"] and
                normal["production_payload_changed"] is False,
                "build, normalization, and readback identities disagree")
        for name in ("hit_state", "ko_state", "final_state"):
            state = report[name]
            require(state["runtime_ready"] == 1 and
                    state["slice_ready"] == 1 and
                    state["slice_actor_count"] == 2 and
                    state["slice_asset_failures"] == 0 and
                    state["slice_late_reads"] == 0 and
                    state["slice_fallback_used"] == 0 and
                    state["slice_canaries_ok"] == 1 and
                    state["slice_physical_saturn"] == 0 and
                    state["slice_init_stage"] == 17 and
                    state["stage_port_lock_ok"] == 1 and
                    state["hud_port_lock_ok"] == 1 and
                    state["pcm_port_lock_ok"] == 1 and
                    state["cdda_port_lock_ok"] == 1 and
                    state["enemy_render_count"] > 0 and
                    state["slice_stage_submissions"] ==
                    state["slice_stability_frames"] * 3,
                    f"{name} lost a promoted subsystem or safety invariant")
        require(605 <= report["hit_state"]["slice_frame"] <= 630 and
                report["hit_state"]["slice_combat_events"] == 1 and
                report["hit_state"]["slice_hit_count"] == 1 and
                report["hit_state"]["slice_review_phase"] == 3 and
                2480 <= report["ko_state"]["slice_frame"] <= 2999 and
                report["ko_state"]["slice_combat_events"] == 4 and
                report["ko_state"]["slice_ko_count"] == 1 and
                report["ko_state"]["slice_review_phase"] == 4 and
                3000 <= report["final_state"]["slice_frame"] <= 3059 and
                report["final_state"]["slice_cdda_active"] == 0 and
                report["final_state"]["slice_cdda_transitions"] == 2,
                "exact HIT, KO, or ownership checkpoint drifted")
        for state in (report["hit_state"], report["ko_state"],
                      report["final_state"]):
            require(state["slice_player_screen_x"] ==
                    state["slice_player_world_x"] -
                    state["slice_camera_world_x"] +
                    state["slice_aperture_origin_x"] and
                    state["slice_enemy_screen_x"] ==
                    state["slice_enemy_world_x"] -
                    state["slice_camera_world_x"] +
                    state["slice_aperture_origin_x"] and
                    state["slice_player_delta_screen_x"] ==
                    state["slice_player_delta_world_x"] -
                    state["slice_delta_camera_world_x"] and
                    state["slice_enemy_delta_screen_x"] ==
                    state["slice_enemy_delta_world_x"] -
                    state["slice_delta_camera_world_x"] and
                    state["slice_layer0_scroll_x"] ==
                    state["slice_camera_world_x"] and
                    state["slice_player_actor_id"] == 1 and
                    state["slice_player_role"] == 1 and
                    state["slice_player_archetype_id"] == 1 and
                    state["slice_player_asset_set_id"] == 1 and
                    state["slice_player_animation_set_id"] == 1 and
                    state["slice_enemy_actor_id"] == 31 and
                    state["slice_enemy_role"] == 2 and
                    state["slice_enemy_class_id"] == 31 and
                    state["slice_enemy_archetype_id"] == 31 and
                    state["slice_enemy_asset_set_id"] == 2 and
                    state["slice_enemy_animation_set_id"] == 2 and
                    state["slice_enemy_object_count"] > 0 and
                    state["slice_player_object_identity"] != 0 and
                    state["slice_player_tile_identity"] != 0 and
                    state["slice_enemy_object_identity"] != 0 and
                    state["slice_enemy_tile_identity"] != 0,
                    "scene anchor or actor identity trace drifted")
        for shot in report["screenshots"].values():
            path = ROOT / shot["path"]
            require(path.is_file() and sha(path) == shot["sha256"],
                    "scanout screenshot identity drifted")
            with Image.open(path) as image:
                colours = image.convert("RGB").getcolors(
                    maxcolors=image.width * image.height)
                require(image.width > 300 and image.height > 200 and
                        colours is not None and len(colours) >= 16,
                        "scanout screenshot is empty")
    for name in ("hit_state", "ko_state", "final_state"):
        require(stable_state(reads[0], name) == stable_state(reads[1], name),
                f"paired semantic state drifted at {name}")
    for trace, build in zip(traces, builds):
        require(trace["result"] == "PASS" and
                trace["fidelity"] == "ADAPTED" and
                trace["evidence_tier"] ==
                "ONE_EMULATOR_SYNCHRONIZED_TRACE" and
                trace["physical_saturn"] == "UNRUN" and
                trace["source_commit"] == build["source_commit"] and
                trace["iso_sha256"] ==
                build["artifacts"]["game_iso"]["sha256"] and
                trace["contacts"] == [600, 1200, 1800, 2400],
                "synchronized trace identity or contact sequence drifted")
        require(trace["adapted_scope"] ==
                "deterministic capability-slice movement and four-attack "
                "choreography; not production player control or enemy AI" and
                trace["post_ko_framing"] == {
                    "intentional_exit": False,
                    "player_world_x": 446,
                    "camera_world_x": 161,
                    "player_screen_x": 109,
                    "aperture": [-176, 175],
                    "result": "VISIBLE_HOLD",
                }, "ADAPTED label or post-KO framing contract drifted")
        require(trace["render_identity_contract"]["result"] == "PASS" and
                set(trace["render_identity_contract"]["phases"]) ==
                {"WALK", "HIT", "RECOVERY", "KO"} and
                trace["render_identity_mutation_control"] == "PASS_REJECTED",
                "exact rendered street-alien identity contract drifted")
        require(trace["sample_frames"] ==
                [sample["slice_frame"] for sample in trace["samples"]],
                "synchronized trace sample order drifted")
    require(traces[0]["samples"] == traces[1]["samples"],
            "paired synchronized semantic traces are not deterministic")
    clip = traces[0]["clip"]
    require(clip is not None and clip["sample_count"] >= 250,
            "continuous corrected-scene clip is missing or undersampled")
    clip_path = ROOT / clip["path"]
    require(clip_path.is_file() and sha(clip_path) == clip["sha256"] and
            clip_path.stat().st_size == clip["bytes"],
            "corrected-scene clip identity drifted")
    for image_record in traces[0]["key_images"].values():
        image_path = ROOT / image_record["path"]
        require(image_path.is_file() and
                sha(image_path) == image_record["sha256"],
                "synchronized key image identity drifted")
    print("INTEGRATE-03 paired exact-release emulator evidence: PASS")


if __name__ == "__main__":
    main()
