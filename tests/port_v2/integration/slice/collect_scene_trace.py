#!/usr/bin/env python3
"""Capture synchronized semantic/visual QA evidence for INTEGRATE-03."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from PIL import Image, ImageGrab


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tools = load_module(
    "enemy_bench_scene_trace",
    ROOT / "tests/port_v2/enemy_bench/collect_readback.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed(mcp, address):
    return tools.signed32(mcp.u32(address))


def snapshot(mcp, syms):
    return {
        symbol.removeprefix("avsp_diag_"): signed(mcp, address)
        for symbol, address in syms.items()
    }


def wait_exact_frame(mcp, syms, target, timeout):
    address = hex(syms["avsp_diag_slice_frame"])
    mcp.call("pause")
    mcp.call("breakpoint_add", cpu="master", type="memory",
             address=address, write=True, value=hex(target))
    try:
        mcp.call("resume")
        stopped = mcp.call("wait_for_stop", timeout_ms=int(timeout * 1000))
        if "stopped: true" not in stopped:
            raise TimeoutError(f"slice frame {target} was not reached")
        result = snapshot(mcp, syms)
        if result["slice_frame"] != target:
            raise RuntimeError(
                f"slice frame mismatch: {result['slice_frame']} != {target}")
        return result
    finally:
        mcp.call("breakpoint_remove", cpu="master", type="memory",
                 address=address)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def validate_sample(sample):
    frame = sample["slice_frame"]
    require(sample["runtime_ready"] == 1 and
            sample["slice_interface_version"] == 2 and
            sample["slice_ready"] == 1 and
            sample["slice_actor_count"] == 2,
            f"frame {frame}: slice runtime/actor contract drifted")
    require(sample["slice_player_actor_id"] == 1 and
            sample["slice_player_role"] == 1 and
            sample["slice_player_archetype_id"] == 1 and
            sample["slice_player_asset_set_id"] == 1 and
            sample["slice_player_animation_set_id"] == 1 and
            sample["slice_enemy_actor_id"] == 31 and
            sample["slice_enemy_role"] == 2 and
            sample["slice_enemy_class_id"] == 31 and
            sample["slice_enemy_archetype_id"] == 31 and
            sample["slice_enemy_asset_set_id"] == 2 and
            sample["slice_enemy_animation_set_id"] == 2,
            f"frame {frame}: actor identity changed or stalker was substituted")
    aperture = sample["slice_aperture_origin_x"]
    camera = sample["slice_camera_world_x"]
    require(sample["slice_player_screen_x"] ==
            sample["slice_player_world_x"] - camera + aperture and
            sample["slice_enemy_screen_x"] ==
            sample["slice_enemy_world_x"] - camera + aperture,
            f"frame {frame}: world-to-screen camera transform drifted")
    require(sample["slice_player_delta_screen_x"] ==
            sample["slice_player_delta_world_x"] -
            sample["slice_delta_camera_world_x"] and
            sample["slice_enemy_delta_screen_x"] ==
            sample["slice_enemy_delta_world_x"] -
            sample["slice_delta_camera_world_x"],
            f"frame {frame}: camera delta invariant drifted")
    require(sample["slice_layer0_scroll_x"] == camera,
            f"frame {frame}: actor and stage camera progressions differ")
    require(sample["slice_player_object_identity"] != 0 and
            sample["slice_player_tile_identity"] != 0 and
            sample["slice_enemy_object_count"] > 0 and
            sample["slice_enemy_object_identity"] != 0 and
            sample["slice_enemy_tile_identity"] != 0,
            f"frame {frame}: a rendered actor identity is empty")
    contact = sample["slice_collision_result"]
    if contact:
        require(sample["slice_player_attack_active"] == 1 and
                sample["slice_attacker_id"] == 1 and
                sample["slice_defender_id"] == 31 and
                sample["slice_health_after"] < sample["slice_health_before"],
                f"frame {frame}: contact is not causal player-to-alien damage")
    else:
        require(sample["slice_health_after"] == sample["slice_health_before"],
                f"frame {frame}: damage occurred without contact")
    require(not sample["slice_semantic_hit"] or
            (sample["slice_enemy_action"] == 3 and
             sample["slice_defender_id"] == 31),
            f"frame {frame}: visual HIT lacks semantic HIT")
    require(not sample["slice_semantic_ko"] or
            (sample["slice_enemy_action"] == 4 and
             sample["slice_defender_id"] == 31),
            f"frame {frame}: visual KO lacks semantic KO")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--no-clip", action="store_true")
    args = parser.parse_args()

    inventory = json.loads((HERE / "inventory.json").read_text())
    build_root = ROOT / inventory["build_root"] / f"run-{args.run}"
    build = json.loads((build_root / "build.json").read_text())
    all_symbols = tools.symbols(inventory["required_readback_symbols"])
    syms = {name: all_symbols[name]
            for name in inventory["required_readback_symbols"]}
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

    exact = {
        20, 40, 45, 46, 60, 300, 320, 339,
        588, 599, 600, 601, 620, 637,
        900, 1188, 1199, 1200, 1201,
        1500, 1788, 1799, 1800, 1801,
        2100, 2388, 2399, 2400, 2401, 2420, 2480, 2560,
    }
    targets = sorted(set(range(20, 2561, 10)) | exact)
    key_frames = {20, 45, 46, 320, 588, 599, 600, 601, 620, 637,
                  1188, 1200, 1788, 1800, 2388, 2400, 2420, 2480}
    samples = []
    images = []
    key_images = {}
    for target in targets:
        sample = wait_exact_frame(mcp, syms, target, args.timeout)
        validate_sample(sample)
        samples.append(sample)
        if not args.no_clip:
            image = ImageGrab.grab(bbox=bounds, all_screens=True).convert("RGB")
            images.append(image.convert(
                "P", palette=Image.Palette.ADAPTIVE, colors=256))
            if target in key_frames:
                path = build_root / f"scene-{target:04d}.png"
                image.save(path)
                key_images[str(target)] = {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": sha(path),
                    "bytes": path.stat().st_size,
                }

    require([sample["slice_frame"] for sample in samples] == targets,
            "trace frames are not continuous and ordered")
    contacts = [sample for sample in samples
                if sample["slice_collision_result"]]
    camera_values = [sample["slice_camera_world_x"] for sample in samples]
    require(camera_values == sorted(camera_values),
            "gameplay camera reset or reversed during the coherent scene")
    by_frame = {sample["slice_frame"]: sample for sample in samples}
    require(by_frame[45]["slice_player_world_x"] ==
            by_frame[46]["slice_player_world_x"] and
            by_frame[46]["slice_player_screen_x"] <
            by_frame[45]["slice_player_screen_x"],
            "stationary world actor did not move opposite the camera pan")
    require([sample["slice_frame"] for sample in contacts] ==
            [600, 1200, 1800, 2400],
            "trace does not contain the four causal contacts exactly once")
    require([sample["slice_health_after"] for sample in contacts] ==
            [63, 39, 8, -1],
            "trace contact damage sequence drifted")
    require(all(-176 <= sample["slice_player_screen_x"] <= 175 and
                -176 <= sample["slice_enemy_screen_x"] <= 175
                for sample in contacts),
            "a causal contact has a participant outside the visible aperture")
    require(any(sample["slice_semantic_hit"] for sample in samples) and
            any(sample["slice_semantic_ko"] for sample in samples),
            "trace does not span semantic HIT and KO")

    clip = None
    if images:
        clip_path = build_root / "scene-after.gif"
        images[0].save(
            clip_path, save_all=True, append_images=images[1:],
            duration=167, loop=0, optimize=False, disposal=2)
        clip = {
            "path": clip_path.relative_to(ROOT).as_posix(),
            "sha256": sha(clip_path),
            "bytes": clip_path.stat().st_size,
            "sample_count": len(images),
            "sample_interval_frames": 10,
            "playback_fps": 6,
        }

    report = {
        "schema": 1,
        "task_id": inventory["task_id"],
        "source_commit": build["source_commit"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "evidence_tier": "ONE_EMULATOR_SYNCHRONIZED_TRACE",
        "physical_saturn": "UNRUN",
        "world_to_screen_contract":
            "screen_x = world_x - camera_world_x + aperture_origin_x",
        "sample_frames": targets,
        "samples": samples,
        "contacts": [sample["slice_frame"] for sample in contacts],
        "key_images": key_images,
        "clip": clip,
        "result": "PASS",
    }
    output = build_root / "scene-trace.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"recorded {output.relative_to(ROOT)}")
    if clip:
        print(f"recorded {clip['path']}")


if __name__ == "__main__":
    main()
