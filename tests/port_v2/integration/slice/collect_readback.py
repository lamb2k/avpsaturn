#!/usr/bin/env python3
"""Pinned-Yaba semantic and scanout readback for INTEGRATE-03."""

import argparse
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

from PIL import ImageGrab


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tools = load_module(
    "enemy_bench_readback", ROOT / "tests/port_v2/enemy_bench/collect_readback.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed(mcp, address):
    return tools.signed32(mcp.u32(address))


def state(mcp, syms):
    result = {}
    for symbol in syms:
        name = symbol.removeprefix("avsp_diag_")
        result[name] = signed(mcp, syms[symbol])
    return result


def wait_frame(mcp, syms, target, ceiling, timeout):
    symbol = "avsp_diag_slice_frame"
    deadline = time.time() + timeout
    mcp.call("resume")
    current = signed(mcp, syms[symbol])
    while current < target and time.time() < deadline:
        current = signed(mcp, syms[symbol])
        if current < target:
            time.sleep(0.002)
    if current < target:
        raise TimeoutError(f"slice frame {target} was not reached")
    mcp.call("pause")
    result = state(mcp, syms)
    if not target <= result["slice_frame"] <= ceiling:
        raise RuntimeError(
            f"slice stopped at {result['slice_frame']}, expected "
            f"review window {target}-{ceiling}")
    return result


def require_fields(actual, expected, label):
    for name, value in expected.items():
        if actual[name] != value:
            raise RuntimeError(
                f"{label} drifted: {name}={actual[name]} expected {value}")


def validate_hit(actual):
    require_fields(actual, {
        "runtime_ready": 1, "slice_interface_version": 2,
        "slice_ready": 1, "slice_actor_count": 2,
        "slice_combat_events": 1, "slice_enemy_health": 63,
        "slice_hit_count": 1, "slice_ko_count": 0,
        "slice_hud_render_count": 4, "slice_pcm_events": 1,
        "slice_pcm_active": 1, "slice_cdda_active": 1,
        "slice_cdda_transitions": 1, "slice_late_reads": 0,
        "slice_asset_failures": 0, "slice_fallback_used": 0,
        "slice_canaries_ok": 1,
        "slice_physical_saturn": 0, "stage_port_lock_ok": 1,
        "hud_port_lock_ok": 1, "slice_review_phase": 3,
        "slice_semantic_hit": 1, "slice_semantic_ko": 0,
        "slice_enemy_class_id": 31, "slice_enemy_archetype_id": 31,
        "slice_enemy_asset_set_id": 2,
        "slice_enemy_animation_set_id": 2,
        "slice_enemy_palette_bank": 19,
        "slice_enemy_animation_record": 0x0012DD50,
        "slice_defender_id": 31,
    }, "playable-slice HIT")
    if actual["slice_stability_frames"] != actual["slice_frame"] + 1:
        raise RuntimeError("HIT frame and stability counter disagree")
    if actual["enemy_render_count"] <= 0 or \
            actual["slice_stage_submissions"] < 3 or \
            actual["pcm_submit_count"] < 1 or actual["cdda_submit_count"] != 1:
        raise RuntimeError("HIT frame lacks a promoted presentation/audio submit")


def validate_ko(actual):
    require_fields(actual, {
        "runtime_ready": 1, "slice_interface_version": 2,
        "slice_ready": 1, "slice_actor_count": 2,
        "slice_combat_events": 4, "slice_enemy_health": -1,
        "slice_hit_count": 1, "slice_ko_count": 1,
        "slice_hud_render_count": 4, "slice_pcm_events": 1,
        "slice_pcm_active": 0, "slice_cdda_active": 1,
        "slice_cdda_transitions": 1, "slice_late_reads": 0,
        "slice_asset_failures": 0, "slice_fallback_used": 0,
        "slice_canaries_ok": 1,
        "slice_physical_saturn": 0, "slice_review_phase": 4,
        "slice_semantic_hit": 0, "slice_semantic_ko": 1,
        "slice_enemy_class_id": 31, "slice_enemy_archetype_id": 31,
        "slice_enemy_asset_set_id": 2,
        "slice_enemy_animation_set_id": 2,
        "slice_enemy_palette_bank": 16,
        "slice_enemy_animation_record": 0x0012E268,
        "slice_defender_id": 31,
    }, "playable-slice KO")
    if actual["slice_stability_frames"] != actual["slice_frame"] + 1:
        raise RuntimeError("KO frame and stability counter disagree")
    if actual["enemy_render_count"] <= 0 or \
            actual["combat_transition_anim_record"] != 0x0012E268:
        raise RuntimeError("KO frame lacks the promoted enemy transition")


def validate_final(actual):
    require_fields(actual, {
        "runtime_ready": 1, "slice_ready": 1,
        "slice_combat_events": 4, "slice_enemy_health": -1,
        "slice_cdda_active": 0, "slice_cdda_transitions": 2,
        "slice_late_reads": 0, "slice_asset_failures": 0,
        "slice_fallback_used": 0, "slice_canaries_ok": 1,
        "slice_physical_saturn": 0,
        "slice_review_phase": 4, "slice_semantic_ko": 1,
        "slice_enemy_class_id": 31, "slice_enemy_archetype_id": 31,
        "slice_enemy_asset_set_id": 2,
        "slice_enemy_animation_set_id": 2,
        "slice_enemy_palette_bank": 16,
        "slice_player_world_x": 446,
        "slice_camera_world_x": 161,
        "slice_player_screen_x": 109,
    }, "playable-slice final")
    if actual["slice_stability_frames"] != actual["slice_frame"] + 1:
        raise RuntimeError("final frame and stability counter disagree")
    if not -176 <= actual["slice_player_screen_x"] <= 175:
        raise RuntimeError("post-KO player hold left the visible aperture")


def validate_scene_anchor(actual):
    if actual["slice_player_screen_x"] != \
            actual["slice_player_world_x"] - \
            actual["slice_camera_world_x"] + \
            actual["slice_aperture_origin_x"] or \
            actual["slice_enemy_screen_x"] != \
            actual["slice_enemy_world_x"] - \
            actual["slice_camera_world_x"] + \
            actual["slice_aperture_origin_x"] or \
            actual["slice_layer0_scroll_x"] != \
            actual["slice_camera_world_x"]:
        raise RuntimeError("actor and stage camera anchors diverged")
    if actual["slice_player_delta_screen_x"] != \
            actual["slice_player_delta_world_x"] - \
            actual["slice_delta_camera_world_x"] or \
            actual["slice_enemy_delta_screen_x"] != \
            actual["slice_enemy_delta_world_x"] - \
            actual["slice_delta_camera_world_x"]:
        raise RuntimeError("per-frame world-to-screen delta invariant drifted")
    if actual["slice_player_actor_id"] != 1 or \
            actual["slice_player_role"] != 1 or \
            actual["slice_player_archetype_id"] != 1 or \
            actual["slice_player_asset_set_id"] != 1 or \
            actual["slice_player_animation_set_id"] != 1 or \
            actual["slice_enemy_actor_id"] != 31 or \
            actual["slice_enemy_role"] != 2:
        raise RuntimeError("two-actor integration identity contract drifted")
    if actual["slice_player_object_identity"] == 0 or \
            actual["slice_player_tile_identity"] == 0:
        raise RuntimeError("player rendered identity is empty")
    if actual["slice_enemy_object_count"] <= 0 or \
            actual["slice_enemy_object_identity"] == 0 or \
            actual["slice_enemy_tile_identity"] == 0:
        raise RuntimeError("enemy object/tile identity is empty")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--checkpoint", choices=("hit", "ko", "final"),
                        required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    build = json.loads((ROOT / inventory["build_root"] /
                        f"run-{args.run}/build.json").read_text())
    required = inventory["required_readback_symbols"]
    all_symbols = tools.symbols(required)
    syms = {name: all_symbols[name] for name in required}
    mcp = tools.Mcp("http://127.0.0.1:9640/mcp")
    deadline = time.time() + args.timeout
    while True:
        try:
            mcp.initialize()
            break
        except Exception:
            if time.time() >= deadline:
                raise
            time.sleep(0.25)
    mcp.call("set_debug_option", cpu_core="dynarec")
    mcp.call("pause")
    bounds = tools.window_bounds(args.emulator_pid, args.timeout)
    run_root = ROOT / inventory["build_root"] / f"run-{args.run}"
    checkpoint_contract = {
        "hit": (605, 630, validate_hit),
        "ko": (2480, 2999, validate_ko),
        "final": (3000, 3059, validate_final),
    }
    target, ceiling, validator = checkpoint_contract[args.checkpoint]
    checkpoint_state = wait_frame(
        mcp, syms, target, ceiling, args.timeout)
    validator(checkpoint_state)
    validate_scene_anchor(checkpoint_state)
    screenshot = None
    if args.checkpoint in ("hit", "ko"):
        screenshot_path = run_root / f"{args.checkpoint}.png"
        ImageGrab.grab(bbox=bounds, all_screens=True).save(screenshot_path)
        screenshot = {
            "path": screenshot_path.relative_to(ROOT).as_posix(),
            "sha256": sha(screenshot_path),
            "bytes": screenshot_path.stat().st_size,
        }
    process = tools.process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    checkpoint_report = {
        "checkpoint": args.checkpoint,
        "source_commit": build["source_commit"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "state": checkpoint_state,
        "screenshot": screenshot,
        "process": {
            "process_id": process["pid"],
            "executable_sha256": sha(executable),
            "settings_sha256": sha(settings),
            "command_line": process["command_line"],
        },
    }
    checkpoint_path = run_root / f"{args.checkpoint}-checkpoint.json"
    checkpoint_path.write_text(
        json.dumps(checkpoint_report, indent=2, sort_keys=True) + "\n")
    print(f"recorded {checkpoint_path.relative_to(ROOT)}")

    if args.checkpoint != "final":
        return

    checkpoints = {}
    for name in ("hit", "ko", "final"):
        path = run_root / f"{name}-checkpoint.json"
        checkpoints[name] = json.loads(path.read_text(encoding="ascii"))
        if checkpoints[name]["checkpoint"] != name or \
                checkpoints[name]["source_commit"] != build["source_commit"] or \
                checkpoints[name]["iso_sha256"] != \
                build["artifacts"]["game_iso"]["sha256"]:
            raise RuntimeError(f"{name} checkpoint identity drifted")
    report = {
        "schema": 1, "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": build["source_commit"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "hit_state": checkpoints["hit"]["state"],
        "ko_state": checkpoints["ko"]["state"],
        "final_state": checkpoints["final"]["state"],
        "screenshots": {
            "hit": checkpoints["hit"]["screenshot"],
            "ko": checkpoints["ko"]["screenshot"]},
        "emulator": {"identity": "Yaba Sanshiro 1.20.37-2986eb",
                     "evidence_tier": "ONE_EMULATOR",
                     "checkpoint_processes": {
                         name: checkpoints[name]["process"]
                         for name in ("hit", "ko", "final")}},
        "physical_saturn": "UNRUN", "result": "PASS"}
    output = run_root / "readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
