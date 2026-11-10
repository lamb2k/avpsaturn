#!/usr/bin/env python3
"""Sample master SH-2 PC over MCP while the bench window runs (ONE_EMULATOR).

Coarse: samples are as fast as MCP answers, so short routines are undercounted.
The rig reads one shared ini and one port, so this refuses to run beside another lane.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure_saturn_frame_cost as cost  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tool", default="")
    args = parser.parse_args()
    if subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower().count("yabasanshiro"):
        raise SystemExit("another lane owns the emulator")
    exe = next(cost.EXE.rglob("yabasanshiro.exe"))
    backup = args.output.with_suffix(".ini.bak")
    shutil.copy2(cost.INI, backup)
    cue = args.output.with_suffix(".cue")
    cue.write_text('FILE "%s" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n    POSTGAP 00:02:00\n'
                   'FILE "%s" WAVE\n  TRACK 02 AUDIO\n    PREGAP 00:02:00\n    INDEX 01 00:00:00\n'
                   % (cost.ROOT / "game.iso", cost.ROOT / "stage1_audio.wav"))
    cost.set_ini({"General\\CdRom": "1", "General\\CdRomISO": str(cue).replace("\\", "/"),
                  "Cartridge\\Type": "7", "autostart": "true", "Video\\VideoCore": "1",
                  "Sound\\SoundCore": "0", "Advanced\\SH2Interpreter": "3"})
    table = cost.symbols()
    names = sorted((addr, name) for name, addr in table.items() if 0x06004000 <= addr < 0x06100000)
    addrs = [a for a, _ in names]
    process = subprocess.Popen([str(exe), "-nb", "-a", "-i", str(cue)], cwd=str(cost.ROOT))
    counts, samples, tools = collections.Counter(), 0, ""
    try:
        mcp = cost.Mcp("http://127.0.0.1:9640/mcp")
        deadline = time.time() + 45
        while True:
            try:
                mcp.initialize()
                break
            except Exception:
                if time.time() > deadline:
                    raise
                time.sleep(0.5)
        listing = json.dumps(mcp._post("tools/list", {}))
        tool_names = re.findall(r'"name": "([a-z0-9_]+)"', listing)
        print(tool_names, flush=True)
        frame_at = table["avsp_diag_live_frame"]
        stop = time.time() + 120
        while time.time() < stop:
            try:
                frame = mcp.u32(frame_at)
            except RuntimeError:
                time.sleep(0.5)
                continue
            if frame >= 574 and frame < 0x7FFFFFFF:
                break
            if not 60 <= frame < 574:
                time.sleep(0.2)
                continue
            text = mcp.call(args.tool or "framebuffer_screenshot", **({} if args.tool else {"path": str(args.output.with_suffix(".png"))}))
            found = re.search(r"(?i)pc\W*(?:0x)?([0-9a-f]{6,8})", text)
            if not found:
                tools = text[:300]
                break
            pc = int(found.group(1), 16)
            index = bisect.bisect_right(addrs, pc) - 1
            counts[names[index][1] if index >= 0 and pc < 0x06100000 else hex(pc & 0xFFF00000)] += 1
            samples += 1
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(10)
        shutil.copy2(backup, cost.INI)
    result = {"tier": "ONE_EMULATOR", "samples": samples, "note": tools,
              "top": counts.most_common(30)}
    args.output.write_text(json.dumps(result, indent=1))
    print(json.dumps(result)[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
