#!/usr/bin/env python3
"""Capture the complete REPAIR-09 Saturn exchange at cadence 1."""

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from PIL import Image, ImageGrab

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
PACKAGE = ROOT / "build/feedback/REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


combat = load_module("combat_readback", HERE / "collect_readback.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aperture(image):
    """Normalize the pinned 800x509 client aperture to Saturn 352x224."""
    if image.size != (816, 718):
        raise ValueError(f"unexpected pinned-emulator window size {image.size}")
    client = image.crop((8, 149, 808, 658))
    return client.resize((352, 224), Image.Resampling.NEAREST)


def validate_visual_frame(state, frame):
    expected = {
        "runtime_ready": 1,
        "integration_approval_locks_ok": 1,
        "integration_actor_count": 2,
        "integration_render_order_ok": 1,
        "integration_canaries_ok": 1,
        "integration_asset_failures": 0,
        "integration_disc_late_reads": 0,
        "combat_interface_version": 2,
        "combat_frame": frame,
        "combat_presented_frame": frame,
        "combat_failures": 0,
        "combat_canary_ok": 1,
        "player_canary_ok": 1,
        "player_asset_failures": 0,
        "player_disc_late_reads": 0,
        "enemy_canary_ok": 1,
        "enemy_asset_failures": 0,
        "enemy_disc_late_reads": 0,
        "enemy_tile_bank_misses": 0,
        "enemy_tile_rank_misses": 0,
        "combat_tile_sprite_misses": 0,
    }
    for name, value in expected.items():
        if state[name] != value:
            raise RuntimeError(
                f"visual frame {frame} drifted: {name}={state[name]} "
                f"expected {value}")
    if state["player_render_count"] <= 0 or state["enemy_render_count"] <= 0:
        raise RuntimeError(f"visual frame {frame} omitted a visible actor")
    if (state["combat_enemy_render_object_identity"] !=
            state["combat_enemy_source_object_identity"] or
            state["combat_enemy_render_tile_identity"] !=
            state["combat_enemy_source_tile_identity"]):
        raise RuntimeError(
            f"visual frame {frame} detached alien pixels from source identity")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--run", type=int, choices=(1, 2), default=1)
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    syms = combat.tools.symbols(inventory["required_readback_symbols"])
    mcp = combat.tools.Mcp("http://127.0.0.1:9640/mcp")
    deadline = time.time() + args.timeout
    while True:
        try:
            mcp.initialize()
            break
        except Exception:
            if time.time() >= deadline:
                raise
            time.sleep(0.25)
    mcp.call("set_debug_option", cpu_core="interpreter")
    mcp.call("pause")
    bounds = combat.tools.window_bounds(args.emulator_pid, args.timeout)
    suffix = "" if args.run == 1 else "-run-2"
    frame_root = PACKAGE / f"saturn-frames{suffix}"
    frame_root.mkdir(parents=True, exist_ok=True)
    trace = []
    checkpoint = PACKAGE / f"saturn-cadence-1-trace{suffix}.jsonl"
    with checkpoint.open("w", encoding="ascii", newline="\n") as stream:
        # The Saturn renderer consumes the measured one-frame-delayed source
        # presentation: diagnostic 169 is source render frame 5173, and
        # diagnostic 465 is source render frame 5469.
        for diagnostic_frame in range(169, 466):
            state = combat.wait_frame(mcp, syms, diagnostic_frame, args.timeout)
            validate_visual_frame(state, diagnostic_frame)
            source_frame = diagnostic_frame + 5004
            path = frame_root / f"{source_frame:05d}.png"
            full = ImageGrab.grab(bbox=bounds, all_screens=True).convert("RGB")
            aperture(full).save(path, optimize=False)
            item = {
                "source_frame": source_frame,
                "diagnostic_frame": diagnostic_frame,
                "sha256": sha(path),
                "state": state,
            }
            trace.append(item)
            stream.write(json.dumps(item, sort_keys=True) + "\n")
            stream.flush()
    output = PACKAGE / f"saturn-cadence-1-trace{suffix}.json"
    output.write_text(json.dumps({
        "schema": 1,
        "task_id": "REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION",
        "classification": "pinned-emulator cadence-1 visual/semantic trace",
        "repeat_run": args.run,
        "source_frame_range": [5173, 5469],
        "diagnostic_frame_range": [169, 465],
        "frames": trace,
        "physical_saturn": "UNRUN",
    }, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"captured {len(trace)} Saturn frames to {frame_root}")


if __name__ == "__main__":
    main()
