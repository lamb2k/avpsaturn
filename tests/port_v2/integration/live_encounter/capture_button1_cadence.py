#!/usr/bin/env python3
"""Capture exact native Predator Button1 frames from pinned Yaba."""

import argparse
import ctypes
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from PIL import Image, ImageGrab

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / "build/feedback/REIMPLEMENT-13-PREDATOR-BUTTON1/cadence-1-corrected"
spec = importlib.util.spec_from_file_location(
    "enemy_tools", ROOT / "tests/port_v2/enemy_bench/collect_readback.py")
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)

EXPECTED = {
    177: (0x15F1F4, 0x1626A4),
    178: (0x15E540, 0x161772),
    179: (0x15E540, 0x161772),
    180: (0x15E540, 0x161772),
    181: (0x15E550, 0x1618B2),
    182: (0x15E560, 0x161A0A),
    183: (0x15E560, 0x161A0A),
    184: (0x15E570, 0x1618B2),
    **{frame: (0x15E580, 0x161772) for frame in range(185, 196)},
    196: (0x15F1F4, 0x1626A4),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aperture(image):
    if image.size != (816, 718):
        raise ValueError(f"unexpected pinned-emulator window size {image.size}")
    return image.crop((8, 149, 808, 658)).resize(
        (352, 224), Image.Resampling.NEAREST)


def foreground(pid, timeout):
    bounds = tools.window_bounds(pid, timeout)
    user32 = ctypes.windll.user32
    class Point(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    user32.WindowFromPoint.argtypes = [Point]
    user32.WindowFromPoint.restype = ctypes.c_void_p
    hwnd = user32.WindowFromPoint(Point(bounds[0] + 16, bounds[1] + 16))
    if not hwnd:
        raise RuntimeError("Yaba window handle was not resolved")
    user32.ShowWindow(hwnd, 9)
    user32.SwitchToThisWindow(hwnd, True)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.08)
    return bounds


def wait_frame(mcp, syms, target, timeout):
    address = hex(syms["avsp_diag_live_frame"])
    deadline = time.time() + timeout
    mcp.call("pause")
    current = tools.signed32(mcp.u32(syms["avsp_diag_live_frame"]))
    if target - current > 10:
        mcp.call("resume")
        while time.time() < deadline:
            current = tools.signed32(mcp.u32(syms["avsp_diag_live_frame"]))
            if current >= target - 10:
                break
            time.sleep(0.002)
        mcp.call("pause")
        current = tools.signed32(mcp.u32(syms["avsp_diag_live_frame"]))
    if current > target:
        raise RuntimeError(f"target passed frame {target}: {current}")
    if current != target:
        mcp.call("breakpoint_add", cpu="master", type="memory",
                 address=address, write=True, value=hex(target))
        try:
            while current < target and time.time() < deadline:
                mcp.call("resume")
                stopped = mcp.call(
                    "wait_for_stop",
                    timeout_ms=max(1, int((deadline - time.time()) * 1000)))
                if "stopped: true" not in stopped:
                    raise TimeoutError(f"frame {target} was not reached")
                current = tools.signed32(
                    mcp.u32(syms["avsp_diag_live_frame"]))
        finally:
            mcp.call("breakpoint_remove", cpu="master", type="memory",
                     address=address)
    if current != target:
        raise RuntimeError(f"stopped at frame {current}, expected {target}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--first", type=int, default=min(EXPECTED))
    parser.add_argument("--last", type=int, default=max(EXPECTED))
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text())
    required = list(inventory["required_readback_symbols"])
    for name in ("avsp_diag_round1_native_player_render_commands",):
        if name not in required:
            required.append(name)
    syms = tools.symbols(required)
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
    mcp.call("set_debug_option", cpu_core="interpreter")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    trace = []
    selected = {frame: value for frame, value in EXPECTED.items()
                if args.first <= frame <= args.last}
    for frame, (record, assembly) in selected.items():
        wait_frame(mcp, syms, frame, args.timeout)
        state = {
            "frame": tools.signed32(mcp.u32(syms["avsp_diag_live_frame"])),
            "animation_record": mcp.u32(
                syms["avsp_diag_live_player_animation_record"]),
            "assembly": mcp.u32(syms["avsp_diag_live_player_assembly"]),
            "facing": tools.signed32(
                mcp.u32(syms["avsp_diag_live_player_facing"])),
            "native_player_render_commands": tools.signed32(mcp.u32(
                syms["avsp_diag_round1_native_player_render_commands"])),
            "forbidden_identity": tools.signed32(mcp.u32(
                syms["avsp_diag_round1_native_weapon_forbidden_identity"])),
            "tile_pin_exhaustions": tools.signed32(mcp.u32(
                syms["avsp_diag_round1_native_tile_pin_exhaustions"])),
        }
        if (state["animation_record"] != record or
            state["assembly"] != assembly or state["facing"] != 1 or
            (frame < 196 and state["native_player_render_commands"] <= 0) or
            state["forbidden_identity"] != 0 or
            state["tile_pin_exhaustions"] != 0):
            raise RuntimeError(f"Button1 frame {frame} drifted: {state}")
        bounds = foreground(args.emulator_pid, args.timeout)
        path = OUTPUT / f"frame-{frame:03d}.png"
        aperture(ImageGrab.grab(bbox=bounds, all_screens=True).convert(
            "RGB")).save(path, optimize=False)
        trace.append({"frame": frame, "sha256": sha(path), "state": state})
    (OUTPUT / "trace.json").write_text(json.dumps({
        "schema": 1,
        "task_id": "REIMPLEMENT-13-SOURCE-CLOSED-ROUND1",
        "classification": "exact process-bound Windows cadence-1 capture",
        "frames": trace,
        "physical_saturn": "UNRUN",
    }, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(f"captured {len(trace)} exact Button1 frames to {OUTPUT}")


if __name__ == "__main__":
    main()
