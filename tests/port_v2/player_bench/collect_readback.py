#!/usr/bin/env python3
"""Pinned-Yaba PlayerSalvageBench input, VDP1, and diagnostic readback."""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageGrab


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from capture_frontend_cram import Mcp, capture_vdp1  # noqa: E402


# Pinned Yaba's configured digital-pad mapping is W/D/S/A for
# up/right/down/left (yabause.ini Input\\Port\\1\\Id\\1\\Controller\\2).
VK = {"RIGHT": 0x44, "DOWN": 0x53, "LEFT": 0x41, "UP": 0x57}
KEYEVENTF_KEYUP = 0x0002
SYMBOLS = (
    "avsp_diag_runtime_ready", "avsp_diag_player_frame",
    "avsp_diag_player_input_mask", "avsp_diag_player_input_edges",
    "avsp_diag_player_x", "avsp_diag_player_lane", "avsp_diag_player_facing",
    "avsp_diag_player_pose", "avsp_diag_player_pivot_y",
    "avsp_diag_player_render_count", "avsp_diag_player_canary_ok",
    "avsp_diag_player_asset_failures", "avsp_diag_player_disc_late_reads",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def portable(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def capture_window(bounds: tuple[int, int, int, int], path: Path) -> dict[str, str | int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    ImageGrab.grab(bbox=bounds, all_screens=True).save(path)
    return {"path": portable(path), "sha256": sha256(path), "bytes": path.stat().st_size}


def symbols(elf: Path, nm: Path) -> dict[str, int]:
    stdout = subprocess.run([str(nm), "--target=coff-sh", str(elf)],
                            check=True, capture_output=True, text=True).stdout
    result: dict[str, int] = {}
    for line in stdout.splitlines():
        bits = line.split()
        if len(bits) == 3 and bits[2].startswith("_"):
            result.setdefault(bits[2][1:], int(bits[0], 16))
    missing = [name for name in SYMBOLS if name not in result]
    if missing:
        raise RuntimeError(f"missing player diagnostic symbols: {', '.join(missing)}")
    return result


def process_record(pid: int) -> dict[str, str | int]:
    command = ("$p=Get-CimInstance Win32_Process -Filter \"ProcessId=%d\"; "
               "$p | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress") % pid
    raw = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command],
                         check=True, capture_output=True, text=True).stdout
    value = json.loads(raw)
    return {"pid": int(value["ProcessId"]), "executable": value["ExecutablePath"],
            "command_line": value["CommandLine"]}


def window(pid: int) -> tuple[int, tuple[int, int, int, int]]:
    user32 = ctypes.windll.user32
    found: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @callback_type
    def callback(hwnd: int, _: int) -> bool:
        found_pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(found_pid))
        if found_pid.value == pid and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
            return False
        return True

    user32.EnumWindows(callback, 0)
    if not found:
        raise RuntimeError("pinned emulator window is not visible")
    rect = wintypes.RECT()
    if not user32.GetWindowRect(found[0], ctypes.byref(rect)):
        raise RuntimeError("GetWindowRect failed")
    return found[0], (rect.left, rect.top, rect.right, rect.bottom)


def wait_window(pid: int, timeout: float) -> tuple[int, tuple[int, int, int, int]]:
    deadline = time.time() + timeout
    last_error: RuntimeError | None = None
    while time.time() < deadline:
        try:
            return window(pid)
        except RuntimeError as error:
            last_error = error
            time.sleep(0.25)
    raise TimeoutError("pinned emulator window did not become visible") from last_error


def sample(mcp: Mcp, syms: dict[str, int]) -> dict[str, int]:
    values: dict[str, int] = {}
    for name in SYMBOLS:
        key = "runtime_ready" if name == "avsp_diag_runtime_ready" else name.removeprefix("avsp_diag_player_")
        values[key] = mcp.u32(syms[name])
    return values


def wait_ready(mcp: Mcp, syms: dict[str, int], timeout: float) -> dict[str, int]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = sample(mcp, syms)
        if state["runtime_ready"] == 1 and state["frame"] >= 30:
            return state
        time.sleep(0.05)
    raise TimeoutError("player bench did not become runtime-ready")


def pulse(mcp: Mcp, syms: dict[str, int], hwnd: int, key: str, bit: int,
          timeout: float) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    user32 = ctypes.windll.user32
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.1)
    before = sample(mcp, syms)
    user32.keybd_event(VK[key], 0, 0, 0)
    deadline = time.time() + timeout
    live = None
    while time.time() < deadline:
        live = sample(mcp, syms)
        if live["input_mask"] & bit and live["input_edges"] & bit:
            break
        time.sleep(0.01)
    else:
        user32.keybd_event(VK[key], 0, KEYEVENTF_KEYUP, 0)
        raise TimeoutError(f"{key} input did not reach the Saturn pad sampler")
    target = live["frame"] + 8
    while time.time() < deadline and sample(mcp, syms)["frame"] < target:
        time.sleep(0.01)
    user32.keybd_event(VK[key], 0, KEYEVENTF_KEYUP, 0)
    while time.time() < deadline:
        after = sample(mcp, syms)
        if after["input_mask"] == 0 and after["frame"] > target:
            return before, live, after
        time.sleep(0.01)
    raise TimeoutError(f"{key} input did not release")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    inventory = json.loads((HERE / "inventory.json").read_text(encoding="utf-8"))
    build = json.loads((ROOT / f"build/port_v2/player_bench/run-{args.run}/build.json").read_text(encoding="ascii"))
    nm = ROOT / ".deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe"
    syms = symbols(ROOT / "game.elf", nm)
    missing = [name for name in inventory["required_readback_symbols"] if name not in syms]
    if missing:
        raise RuntimeError(f"inventory symbol missing: {', '.join(missing)}")
    mcp = Mcp("http://127.0.0.1:9640/mcp")
    deadline = time.time() + args.timeout
    while True:
        try:
            mcp.initialize()
            break
        except Exception:
            if time.time() >= deadline:
                raise
            time.sleep(0.25)
    hwnd, bounds = wait_window(args.emulator_pid, args.timeout)
    initial = wait_ready(mcp, syms, args.timeout)
    run_root = ROOT / f"build/port_v2/player_bench/run-{args.run}"
    movement_frames = [capture_window(bounds, run_root / "movement-initial.png")]
    right_before, right_live, right = pulse(mcp, syms, hwnd, "RIGHT", 2, args.timeout)
    movement_frames.append(capture_window(bounds, run_root / "movement-right.png"))
    down_before, down_live, down = pulse(mcp, syms, hwnd, "DOWN", 8, args.timeout)
    movement_frames.append(capture_window(bounds, run_root / "movement-down.png"))
    left_before, left_live, left = pulse(mcp, syms, hwnd, "LEFT", 1, args.timeout)
    movement_frames.append(capture_window(bounds, run_root / "movement-left.png"))
    if not (right["x"] > right_before["x"] and right["facing"] == 1):
        raise RuntimeError("right input did not move/facing-right the player")
    if not (down["lane"] > down_before["lane"]):
        raise RuntimeError("down input did not move the player lane")
    if not (left["x"] < left_before["x"] and left["facing"] == 0xFFFFFFFF):
        raise RuntimeError("left input did not move/facing-left the player")
    for state in (initial, right, down, left):
        expected_layers = 3 if state["pose"] != 0xFFFFFFFF else 2
        if not (state["runtime_ready"] == 1 and state["asset_failures"] == 0 and
                state["canary_ok"] == 1 and state["disc_late_reads"] == 0 and
                state["render_count"] == expected_layers):
            raise RuntimeError(f"player diagnostic invariant failed: {state}")
    if right_live["pose"] == 0xFFFFFFFF:
        raise RuntimeError("walk input did not exercise a player animation pose")
    mcp.call("pause")
    try:
        commands = capture_vdp1(mcp)
        screenshot = run_root / "emulator.png"
        screenshot_record = capture_window(bounds, screenshot)
    finally:
        mcp.call("resume")
    clip = run_root / "movement.gif"
    images = [Image.open(ROOT / frame["path"]).convert("RGB") for frame in movement_frames]
    try:
        images[0].save(clip, save_all=True, append_images=images[1:],
                       duration=350, loop=0)
    finally:
        for image in images:
            image.close()
    process = process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {
        "schema": 1, "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"], "source_commit": build["source_commit"],
        "compile_profile": build["compile_profile"],
        "manifest_sha256": build["artifacts"]["hardware_manifest"]["sha256"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "initial": initial,
        "input_cases": {"right": {"before": right_before, "during": right_live, "after": right},
                        "down": {"before": down_before, "during": down_live, "after": down},
                        "left": {"before": left_before, "during": left_live, "after": left}},
        "vdp1_command_count": len(commands),
        "emulator": {"identity": "Yaba Sanshiro 1.20.37-2986eb", "evidence_tier": "ONE_EMULATOR",
                     "process_id": process["pid"], "executable_sha256": sha256(executable),
                     "settings_sha256": sha256(settings), "command_line": process["command_line"]},
        "screenshot": screenshot_record,
        "movement_frames": movement_frames,
        "movement_clip": {"path": portable(clip), "sha256": sha256(clip),
                          "bytes": clip.stat().st_size, "frame_count": len(movement_frames)},
        "physical_saturn": "UNRUN", "result": "PASS",
    }
    output = ROOT / f"build/port_v2/player_bench/run-{args.run}/readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii", newline="\n")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
