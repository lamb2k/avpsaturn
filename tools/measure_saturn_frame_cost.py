#!/usr/bin/env python3
"""Boot game.cue on the pinned debug-rig Yaba Sanshiro and read frame cost (ONE_EMULATOR).

Owns only the process it starts. Saves and restores yabause.ini. Yaba does not
model SH-2 bus wait states or VDP1 draw time, so ticks are not hardware timing.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from capture_frontend_cram import Mcp  # noqa: E402

EXE = ROOT / ".deps/emulators/yabasanshiro-1.20.37-2986eb-debug-rig-mcp-da2ffb34"
INI = Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
BIN = ROOT / ".deps/joengine/Compiler/WINDOWS/bin"
COST = ["fields", "callbacks", "late_callbacks", "peak_fields", "work_ticks", "work_peak",
        "work_sum_low", "tcr", "vdp1_busy_at_entry"]
EXTRA = ["avsp_diag_live_frame", "avsp_diag_round1_presentation_commands_peak",
         "__jo_current_palette_id"]


def symbols() -> dict[str, int]:
    out = subprocess.run([str(BIN / "sh-elf-nm.exe"), "--target=coff-sh", str(ROOT / "game.elf")],
                         capture_output=True, text=True, check=True).stdout
    table = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3:
            table[parts[2].lstrip("_") if parts[2].startswith("_") else parts[2]] = int(parts[0], 16)
    return table


def set_ini(values: dict[str, str]) -> None:
    lines = INI.read_text().splitlines()
    for key, value in values.items():
        hit = [i for i, line in enumerate(lines) if line.startswith(key + "=")]
        if hit:
            lines[hit[0]] = key + "=" + value
        else:
            lines.append(key + "=" + value)
    INI.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=240)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shot", type=Path)
    args = parser.parse_args()
    exe = next(EXE.rglob("yabasanshiro.exe"))
    backup = args.output.with_suffix(".ini.bak")
    shutil.copy2(INI, backup)
    cue = args.output.with_suffix(".cue")
    cue.write_text('FILE "%s" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n    POSTGAP 00:02:00\n'
                   'FILE "%s" WAVE\n  TRACK 02 AUDIO\n    PREGAP 00:02:00\n    INDEX 01 00:00:00\n'
                   % (ROOT / "game.iso", ROOT / "stage1_audio.wav"))
    set_ini({"General\\CdRom": "1", "General\\CdRomISO": str(cue).replace("\\", "/"),
             "Cartridge\\Type": "7", "autostart": "true", "Video\\VideoCore": "1",
             "Sound\\SoundCore": "0", "Advanced\\SH2Interpreter": "3"})
    table = symbols()
    process = subprocess.Popen([str(exe), "-nb", "-a", "-i", str(cue)], cwd=str(ROOT))
    samples, result = [], {"tier": "ONE_EMULATOR", "exe": exe.name, "boot": False}
    try:
        mcp = Mcp("http://127.0.0.1:9640/mcp")
        deadline = time.time() + 45
        while True:
            try:
                mcp.initialize()
                break
            except Exception:
                if time.time() > deadline or process.poll() is not None:
                    raise
                time.sleep(0.5)
        try:
            mcp.call("resume")
        except Exception:
            pass
        end = time.time() + args.seconds
        while time.time() < end and process.poll() is None:
            row = {"t": round(time.time(), 1)}
            for name in COST:
                row[name] = mcp.u32(table["avsp_diag_frame_cost_" + name])
            for name in EXTRA:
                if name in table:
                    row[name] = mcp.u32(table[name])
            samples.append(row)
            time.sleep(5)
        result["boot"] = bool(samples) and samples[-1]["callbacks"] > 0
        if args.shot:
            result["shot"] = mcp.call("framebuffer_screenshot", path=str(args.shot))[:200]
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(10)
        shutil.copy2(backup, INI)
    result["alive_at_end"] = True
    result["samples"] = samples
    args.output.write_text(json.dumps(result, indent=1))
    print(json.dumps(result["samples"][-1] if samples else result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
