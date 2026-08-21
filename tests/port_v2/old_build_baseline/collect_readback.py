#!/usr/bin/env python3
"""Collect one pinned-emulator OldBuildBaseline readback and screenshot."""

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

from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from capture_frontend_cram import Mcp, load_symbols  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def process_record(pid: int) -> dict[str, str | int]:
    command = (
        "$p=Get-CimInstance Win32_Process -Filter \"ProcessId=%d\"; "
        "if($p){$p | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress}"
        % pid
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        check=True, capture_output=True, text=True).stdout.strip()
    if not result:
        raise RuntimeError(f"emulator process {pid} is not running")
    raw = json.loads(result)
    return {
        "pid": int(raw["ProcessId"]),
        "executable": str(raw["ExecutablePath"]),
        "command_line": str(raw["CommandLine"]),
    }


def find_window(pid: int) -> tuple[int, int, int, int]:
    user32 = ctypes.windll.user32
    found: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p,
                                      ctypes.c_void_p)

    @callback_type
    def callback(hwnd: int, _: int) -> bool:
        window_pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
        if window_pid.value == pid and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
            return False
        return True

    user32.EnumWindows(callback, 0)
    if not found:
        raise RuntimeError(f"no visible emulator window for process {pid}")
    rect = wintypes.RECT()
    if not user32.GetWindowRect(found[0], ctypes.byref(rect)):
        raise RuntimeError("GetWindowRect failed")
    return rect.left, rect.top, rect.right, rect.bottom


def sample(mcp: Mcp, symbols: dict[str, int]) -> dict[str, object]:
    scx = mcp.read(symbols["avsp_diag_street_scx"], 8)
    values = {
        "runtime_ready": mcp.u32(symbols["avsp_diag_runtime_ready"]),
        "world_frame": mcp.u32(symbols["avsp_diag_world_frame"]),
        "street_frame": mcp.u32(symbols["avsp_diag_street_frame"]),
        "street_scx": [int.from_bytes(scx[:4], "big"),
                       int.from_bytes(scx[4:], "big")],
        "street_objects": mcp.u32(symbols["avsp_diag_street_objects"]),
        "frontend_late_reads": mcp.u32(
            symbols["avsp_diag_frontend_late_reads"]),
        "frontend_missing_assets": mcp.u32(
            symbols["avsp_diag_frontend_missing_assets"]),
        "frontend_rle_errors": mcp.u32(
            symbols["avsp_diag_frontend_rle_errors"]),
        "frontend_palette_errors": mcp.u32(
            symbols["avsp_diag_frontend_palette_errors"]),
    }
    values["asset_failure_count"] = (
        (0 if values["runtime_ready"] else 1)
        + int(values["frontend_missing_assets"])
        + int(values["frontend_rle_errors"])
        + int(values["frontend_palette_errors"])
    )
    return values


def wait_for_relative_frame(mcp: Mcp, symbols: dict[str, int], period: int,
                            target: int, after: int, timeout: float) -> dict[str, object]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        frame = mcp.u32(symbols["avsp_diag_street_frame"])
        ready = mcp.u32(symbols["avsp_diag_runtime_ready"])
        objects = mcp.u32(symbols["avsp_diag_street_objects"])
        if ready == 1 and objects > 0 and frame > after and frame % period == target:
            mcp.call("pause")
            state = sample(mcp, symbols)
            if int(state["street_frame"]) % period == target:
                return state
            mcp.call("resume")
        time.sleep(0.01)
    raise TimeoutError(f"did not reach fixture-relative frame {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    inventory = json.loads((HERE / "inventory.json").read_text(encoding="utf-8"))
    build_path = ROOT / f"build/port_v2/old_build_baseline/run-{args.run}/build.json"
    build = json.loads(build_path.read_text(encoding="ascii"))
    fixture = (ROOT / "build/rp4_fixture/STRIPS.BIN").read_bytes()
    period = int.from_bytes(fixture[6:8], "big")
    target = 20

    nm = ROOT / ".deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe"
    symbols = load_symbols(ROOT / "game.elf", nm)
    missing = [name for name in inventory["required_readback_symbols"]
               if name not in symbols]
    if missing:
        raise RuntimeError(f"missing diagnostic symbols: {', '.join(missing)}")

    mcp = Mcp("http://127.0.0.1:9640/mcp")
    deadline = time.time() + args.timeout
    while True:
        try:
            mcp.initialize()
            break
        except Exception:
            if time.time() >= deadline:
                raise
            time.sleep(0.5)

    first = wait_for_relative_frame(mcp, symbols, period, target, -1,
                                    args.timeout)
    mcp.call("resume")
    second = wait_for_relative_frame(
        mcp, symbols, period, target, int(first["street_frame"]), args.timeout)

    output_root = ROOT / f"build/port_v2/old_build_baseline/run-{args.run}"
    screenshot = output_root / "emulator.png"
    bbox = find_window(args.emulator_pid)
    ImageGrab.grab(bbox=bbox, all_screens=True).save(screenshot)

    process = process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    command_line = str(process["command_line"])
    cue_match = re.search(r'-i\s+"([^"]+\.cue)"', command_line, re.IGNORECASE)
    if not cue_match:
        raise RuntimeError("emulator command line has no explicit cue")
    launch_cue = Path(cue_match.group(1))
    cue_text = launch_cue.read_text(encoding="ascii")
    expected_iso = str((ROOT / "game.iso").resolve())
    if expected_iso not in cue_text:
        raise RuntimeError("emulator launch cue does not name this worktree's ISO")

    report = {
        "schema": 1,
        "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": build["source_commit"],
        "compile_profile": build["compile_profile"],
        "manifest_profile": build["manifest_profile"],
        "manifest_sha256": build["artifacts"]["hardware_manifest"]["sha256"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "fixture_period": period,
        "target_relative_frame": target,
        "samples": [first, second],
        "bounded_stability_frames": int(second["street_frame"]) - int(first["street_frame"]),
        "emulator": {
            "identity": "Yaba Sanshiro 1.20.37-2986eb",
            "evidence_tier": "ONE_EMULATOR",
            "process_id": process["pid"],
            "executable_sha256": sha256(executable),
            "settings_sha256": sha256(settings),
            "command_line": command_line,
            "launch_cue": str(launch_cue),
            "launch_cue_sha256": sha256(launch_cue),
        },
        "screenshot": {
            "path": str(screenshot.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(screenshot),
            "bytes": screenshot.stat().st_size,
        },
        "actor_position": {
            "status": "NOT_APPLICABLE",
            "reason": "OldBuildBaseline isolates the stage fixture; actor positions belong to SALVAGE-01 and SALVAGE-02."
        },
        "result": "PASS",
        "physical_saturn": "UNRUN",
    }
    output = output_root / "readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"recorded {output.relative_to(ROOT)}")
    mcp.call("resume")


if __name__ == "__main__":
    main()
