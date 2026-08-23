#!/usr/bin/env python3
"""Pinned-Yaba stage, camera, CRAM, priority, and final-scanout readback."""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import time
from pathlib import Path

from PIL import ImageGrab


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from capture_frontend_cram import Mcp  # noqa: E402


VDP2_VRAM = 0x25E00000
VDP1_VRAM = 0x25C00000
CRAM = 0x25F00000
BMPNA_OFFSET = 0x2C
SHADOW_REGISTERS = (
    ("TVMD", 0x00), ("BGON", 0x20), ("CHCTLA", 0x28),
    ("CHCTLB", 0x2A), ("PNCN0", 0x30), ("PNCN1", 0x32),
    ("PLSZ", 0x3A), ("MPOFN", 0x3C), ("MPABN0", 0x40),
    ("MPCDN0", 0x42), ("MPABN1", 0x44), ("MPCDN1", 0x46),
    ("SCXIN0", 0x70), ("SCYIN0", 0x74), ("SCXIN1", 0x80),
    ("SCYIN1", 0x84), ("SPCTL", 0xE0), ("CRAOFA", 0xE4),
    ("PRISA", 0xF0), ("PRISB", 0xF2), ("PRINA", 0xF8),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def portable(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def symbols(elf: Path, nm: Path, required: list[str]) -> dict[str, int]:
    output = subprocess.run([str(nm), "--target=coff-sh", str(elf)],
                            check=True, capture_output=True, text=True).stdout
    result = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2].startswith("_"):
            result.setdefault(parts[2][1:], int(parts[0], 16))
    missing = [name for name in required + ["slBMPalette"] if name not in result]
    if missing:
        raise RuntimeError(f"missing stage symbols: {', '.join(missing)}")
    return result


def process_record(pid: int) -> dict[str, str | int]:
    command = ("$p=Get-CimInstance Win32_Process -Filter \"ProcessId=%d\"; "
               "$p | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress") % pid
    raw = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command],
                         check=True, capture_output=True, text=True).stdout
    value = json.loads(raw)
    return {"pid": int(value["ProcessId"]), "executable": value["ExecutablePath"],
            "command_line": value["CommandLine"]}


def window_bounds(pid: int, timeout: float) -> tuple[int, int, int, int]:
    user32 = ctypes.windll.user32
    deadline = time.time() + timeout
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p,
                                      ctypes.c_void_p)
    while time.time() < deadline:
        found: list[int] = []

        @callback_type
        def callback(hwnd: int, _: int) -> bool:
            found_pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(found_pid))
            if found_pid.value == pid and user32.IsWindowVisible(hwnd):
                found.append(hwnd)
                return False
            return True

        user32.EnumWindows(callback, 0)
        if found:
            rect = wintypes.RECT()
            if user32.GetWindowRect(found[0], ctypes.byref(rect)):
                return rect.left, rect.top, rect.right, rect.bottom
        time.sleep(0.25)
    raise TimeoutError("pinned emulator window did not become visible")


def u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big")


def expected_palette(fixture: bytes, plane: int, frame: int) -> bytes:
    values = [u16(fixture, 48 + plane * 512 + index * 2)
              for index in range(1, 256)]
    if plane == 0:
        period = u16(fixture, 48 + 1024)
        first_flip = u16(fixture, 48 + 1026)
        entries = u16(fixture, 48 + 1028)
        cycle = 48 + 1030
        step = ((((frame - first_flip) // period) + 1) & 1
                if period > 0 and frame >= first_flip else 0)
        for entry in range(entries):
            at = cycle + entry * 6
            index = u16(fixture, at)
            values[index - 1] = u16(fixture, at + 2 + step * 2)
    return b"".join(struct.pack(">H", value) for value in values)


def vram_canaries(mcp: Mcp, fixture: bytes) -> list[dict[str, object]]:
    result = []
    for plane, char_vram, pnt_vram in ((0, 0x00000, 0x40000),
                                       (1, 0x20000, 0x44000)):
        at = 8 + plane * 20
        char_count = u16(fixture, at + 8)
        char_offset = u32(fixture, at + 12)
        for label, offset in (("first", 0),
                              ("middle", (char_count // 2) * 64),
                              ("last", (char_count - 1) * 64)):
            expected = fixture[char_offset + offset:char_offset + offset + 64]
            live = mcp.read(VDP2_VRAM + char_vram + offset, 64)
            result.append({"plane": plane, "kind": f"char_{label}",
                           "match": live == expected})
        pnt_offset = u32(fixture, at + 16)
        expected = b"".join(struct.pack(">H", u16(fixture, pnt_offset + i * 2) * 2)
                            for i in range(32))
        live = mcp.read(VDP2_VRAM + pnt_vram, 64)
        result.append({"plane": plane, "kind": "pnt_first32",
                       "match": live == expected})
    return result


def vdp1_classes(mcp: Mcp) -> dict[str, int]:
    classes: dict[str, int] = {}
    address = VDP1_VRAM
    for _ in range(2048):
        command = mcp.read(address, 32)
        control = int.from_bytes(command[0:2], "big")
        if control & 0x8000:
            break
        if (control & 0xF) <= 4 and not (control & 0x4000):
            colour = int.from_bytes(command[6:8], "big")
            key = str((colour >> 13) & 3)
            classes[key] = classes.get(key, 0) + 1
        jump = (control >> 12) & 3
        if jump == 1:
            address = VDP1_VRAM + int.from_bytes(command[2:4], "big") * 8
        else:
            address += 32
    return classes


def snapshot(mcp: Mcp, syms: dict[str, int], shadow: int,
             fixture: bytes) -> dict[str, object]:
    frame = mcp.u32(syms["avsp_diag_street_frame"])
    scroll = mcp.read(syms["avsp_diag_street_scx"], 8)
    registers = {name: mcp.u16(shadow + offset)
                 for name, offset in SHADOW_REGISTERS}
    offsets = {"nbg0": registers["CRAOFA"] & 7,
               "nbg1": (registers["CRAOFA"] >> 4) & 7}
    palette = {}
    for plane, name in enumerate(("nbg0", "nbg1")):
        base_entry = offsets[name] * 256
        live = mcp.read(CRAM + (base_entry + 1) * 2, 255 * 2)
        expected = expected_palette(fixture, plane, frame)
        palette[name] = {"offset": offsets[name],
                         "sha256": hashlib.sha256(live).hexdigest(),
                         "expected_sha256": hashlib.sha256(expected).hexdigest(),
                         "match": live == expected}
    canaries = vram_canaries(mcp, fixture)
    status = mcp.call("debug_status")
    match = re.search(r"^frame:\s+(\d+)$", status, re.MULTILINE)
    state = {
        "emulator_frame": int(match.group(1)) if match else -1,
        "relative_frame": frame,
        "scroll_x": [int.from_bytes(scroll[:4], "big"),
                     int.from_bytes(scroll[4:], "big")],
        "objects": mcp.u32(syms["avsp_diag_street_objects"]),
        "runtime_ready": mcp.u32(syms["avsp_diag_runtime_ready"]),
        "interface_version": mcp.u32(syms["avsp_diag_stage_interface_version"]),
        "layer_count": mcp.u32(syms["avsp_diag_stage_layer_count"]),
        "source_width": mcp.u32(syms["avsp_diag_stage_source_width"]),
        "output_width": mcp.u32(syms["avsp_diag_stage_output_width"]),
        "priority_lock_ok": mcp.u32(syms["avsp_diag_stage_priority_lock_ok"]),
        "palette_cycle_state": mcp.u32(syms["avsp_diag_stage_palette_cycle_state"]),
        "scroll_steps": mcp.u32(syms["avsp_diag_stage_scroll_steps"]),
        "asset_failures": mcp.u32(syms["avsp_diag_stage_asset_failures"]),
        "disc_late_reads": mcp.u32(syms["avsp_diag_stage_disc_late_reads"]),
        "registers": {name: f"0x{value:04x}" for name, value in registers.items()},
        "priority": {"nbg0": registers["PRINA"] & 7,
                     "nbg1": (registers["PRINA"] >> 8) & 7,
                     "actor": (registers["PRISA"] >> 8) & 7,
                     "foreground": registers["PRISB"] & 7},
        "cram": palette,
        "vram_canaries": canaries,
        "vram_canaries_all_match": all(item["match"] for item in canaries),
        "vdp1_command_classes": vdp1_classes(mcp),
    }
    if "avsp_diag_stage_row_scroll_status" in syms:
        state["row_scroll_status"] = mcp.u32(
            syms["avsp_diag_stage_row_scroll_status"])
        state["render_submissions"] = mcp.u32(
            syms["avsp_diag_stage_render_submissions"])
        state["port_lock_ok"] = mcp.u32(
            syms["avsp_diag_stage_port_lock_ok"])
    return state


def wait_for_frame(mcp: Mcp, syms: dict[str, int], shadow: int,
                   fixture: bytes, target: int, timeout: float) -> dict[str, object]:
    address = hex(syms["avsp_diag_street_frame"])
    mcp.call("pause")
    mcp.call("breakpoint_add", cpu="master", type="memory", address=address,
             write=True, value=hex(target))
    try:
        mcp.call("resume")
        stopped = mcp.call("wait_for_stop", timeout_ms=int(timeout * 1000))
        if "stopped: true" not in stopped:
            raise TimeoutError(f"stage frame {target} was not reached")
        state = snapshot(mcp, syms, shadow, fixture)
        if state["relative_frame"] != target:
            raise RuntimeError(f"stage stopped at {state['relative_frame']}, expected {target}")
        return state
    finally:
        mcp.call("breakpoint_remove", cpu="master", type="memory", address=address)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--suite", choices=("stage_bench", "camera_stage"),
                        default="stage_bench")
    parser.add_argument("--emulator-pid", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()
    suite_here = ROOT / "tests/port_v2" / args.suite
    contract_name = ("stage_contract.json" if args.suite == "stage_bench" else
                     "approved_contract.json")
    inventory = json.loads((suite_here / "inventory.json").read_text(encoding="utf-8"))
    contract = json.loads((suite_here / contract_name).read_text(encoding="utf-8"))
    build = json.loads((ROOT / f"build/port_v2/{args.suite}/run-{args.run}/build.json").read_text(encoding="ascii"))
    fixture = (ROOT / "build/rp4_fixture/STRIPS.BIN").read_bytes()
    syms = symbols(ROOT / "game.elf",
                   ROOT / ".deps/joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe",
                   inventory["required_readback_symbols"])
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
    bounds = window_bounds(args.emulator_pid, args.timeout)
    while time.time() < deadline:
        if mcp.u32(syms["avsp_diag_runtime_ready"]) == 1:
            break
        time.sleep(0.05)
    else:
        raise TimeoutError("stage bench did not become runtime-ready")
    literal = mcp.u32(syms["slBMPalette"] + 0x10)
    if not 0x06000000 <= literal < 0x06100000:
        raise RuntimeError(f"invalid SGL shadow anchor: 0x{literal:08x}")
    shadow = literal - BMPNA_OFFSET
    fixed_first = wait_for_frame(mcp, syms, shadow, fixture, 20, args.timeout)
    before = wait_for_frame(mcp, syms, shadow, fixture, 45, args.timeout)
    after = wait_for_frame(mcp, syms, shadow, fixture, 46, args.timeout)
    run_root = ROOT / f"build/port_v2/{args.suite}/run-{args.run}"
    screenshot = run_root / "emulator.png"
    ImageGrab.grab(bbox=bounds, all_screens=True).save(screenshot)
    fixed_repeat = wait_for_frame(mcp, syms, shadow, fixture, 20, args.timeout)
    mcp.call("resume")
    expected_fixed = contract["fixed_frame"]
    threshold = contract["scroll_threshold"]
    if fixed_first["scroll_x"] != expected_fixed["scroll_x"] or \
            fixed_first["objects"] != expected_fixed["objects"]:
        raise RuntimeError("fixed stage checkpoint drifted")
    if before["scroll_x"] != threshold["before_scroll_x"] or \
            after["scroll_x"] != threshold["after_scroll_x"]:
        raise RuntimeError("stage scroll threshold drifted")
    for state in (fixed_first, before, after, fixed_repeat):
        if not (state["runtime_ready"] == 1 and state["interface_version"] == 1 and
                state["layer_count"] == 2 and state["source_width"] == 384 and
                state["output_width"] == 352 and state["priority_lock_ok"] == 1 and
                state["asset_failures"] == 0 and state["disc_late_reads"] == 0 and
                state["vram_canaries_all_match"] and
                all(value["match"] for value in state["cram"].values())):
            raise RuntimeError(f"stage readback invariant failed: {state}")
        if args.suite == "camera_stage" and not (
                state["row_scroll_status"] == 1 and
                state["port_lock_ok"] == 1 and
                state["render_submissions"] > 0):
            raise RuntimeError(f"camera/stage port invariant failed: {state}")
    process = process_record(args.emulator_pid)
    executable = Path(str(process["executable"]))
    settings = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
    report = {
        "schema": 1, "task_id": inventory["task_id"],
        "card_profile": inventory["card_profile"],
        "source_commit": build["source_commit"],
        "compile_profile": build["compile_profile"],
        "iso_sha256": build["artifacts"]["game_iso"]["sha256"],
        "fixed_samples": [fixed_first, fixed_repeat],
        "scroll_threshold": {"before": before, "after": after},
        "bounded_stability_frames": fixed_repeat["emulator_frame"] - fixed_first["emulator_frame"],
        "final_scanout": {"tvmd": after["registers"]["TVMD"],
                          "width": 352, "height": 224,
                          "screenshot": {"path": portable(screenshot),
                                         "sha256": sha256(screenshot),
                                         "bytes": screenshot.stat().st_size}},
        "emulator": {"identity": "Yaba Sanshiro 1.20.37-2986eb",
                     "evidence_tier": "ONE_EMULATOR", "process_id": process["pid"],
                     "executable_sha256": sha256(executable),
                     "settings_sha256": sha256(settings),
                     "command_line": process["command_line"]},
        "promoted_player_output": {"status": "REGRESSION_LOCK_ONLY",
                                   "reason": "stage bench does not render or alter the approved player"},
        "row_scroll_status": ("ADAPTED_UNCAPTURED" if
                              args.suite == "camera_stage" else
                              "SALVAGE_CONTRACT_UNCHANGED"),
        "physical_saturn": "UNRUN", "result": "PASS",
    }
    output = run_root / "readback.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="ascii", newline="\n")
    print(f"recorded {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
