#!/usr/bin/env python
"""Run the Saturn image under Yaba for a bounded time and read the runtime's debug block over MCP. Tier: EMULATOR.
usage: run_yaba.py [WORK] [seconds] [dump.bin]"""
import json, os, pathlib, re, socket, struct, subprocess, sys, time
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from capture_frontend_cram import Mcp
WORK = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "E:/AvP/learning/lane-satrt")
SECS = float(sys.argv[2]) if len(sys.argv) > 2 else 40
DUMP = sys.argv[3] if len(sys.argv) > 3 else None
JO = pathlib.Path("E:/AvP/worktrees/saturn-hw/.deps")
EXE = JO / "emulators/yabasanshiro-1.20.37-2986eb-debug-rig-mcp-da2ffb34/yabasanshiro-1.20.37-2986eb-debug-rig-mcp-d7767591/yabasanshiro.exe"
NM = JO / "joengine/Compiler/WINDOWS/sh-elf/bin/nm.exe"
INI = pathlib.Path(os.environ["APPDATA"]) / "YabaSanshiro/yabause.ini"
STATS = ">I" + "H" * 14 + "I" * 6
FIELDS = "magic stage vblanks ff8018 task_runs idle_calls task_stack_high fatal fatal_detail fatal_task a0 a1 a7 exc_pc exc_pr gfx_ticks irq_ticks game_ticks gfx_peak irq_peak game_peak overruns obj_flips snap_ticks snap_peak gfx_skips".split()


def port_busy():
    s = socket.socket()
    s.settimeout(0.3)
    busy = s.connect_ex(("127.0.0.1", 9640)) == 0
    s.close()
    return busy


while port_busy():
    print("Yaba lock held, waiting"); time.sleep(10)
syms = {}
for l in subprocess.run([str(NM), str(WORK / "sat.elf")], capture_output=True, text=True).stdout.splitlines():
    p = l.split()
    if len(p) == 3:
        syms[p[2].lstrip("_")] = int(p[0], 16)
import bisect
_t = sorted((v, k) for k, v in syms.items()); _k = [x[0] for x in _t]
def sym_of(a):
    i = bisect.bisect_right(_k, a) - 1
    return f"{_t[i][1]}+{a - _k[i]:#x}" if i >= 0 else hex(a)
orig = INI.read_bytes()
(WORK / "shots").mkdir(exist_ok=True)
lines = orig.decode("latin-1").splitlines()
set_ = {"Video\VideoCore": "1", "Sound\SoundCore": "0", "General\CdRomISO": str(WORK / "sat.cue").replace("\\", "/"), "autostart": "true", "Cartridge\Type": "7", "General\EnableEmulatedBios": "true"}
out = [f"{l.split('=')[0]}={set_[l.split('=')[0]]}" if l.split("=")[0] in set_ else l for l in lines]
INI.write_bytes(("\n".join(out) + "\n").encode("latin-1"))
proc = subprocess.Popen([str(EXE)], cwd=str(EXE.parent))
try:
    m = Mcp("http://127.0.0.1:9640/mcp")
    t0 = time.time()
    while True:
        try:
            m.initialize(); break
        except Exception:
            if time.time() - t0 > 30: raise
            time.sleep(0.3)
    if os.environ.get("LIST_TOOLS"): print("tools", [x["name"] for x in m._post("tools/list", {})["result"]["tools"]], flush=True)
    shots = sorted(int(x) for x in os.environ.get("SHOTS", "").split(",") if x)
    stats_names = "frames objects commands commands_peak uploads uploads_peak slots slots_peak layer_uploads layer_writes s1_peak s2_peak s3_peak colours top_bank missing ref_cmd ref_spr ref_layer ref_bank nonmono".split()
    last = 0
    tick_us = 128 / 26.8741  # 352 mode clock 26.8741 MHz
    while time.time() - t0 < SECS:
        time.sleep(0.25)
        b = m.read(syms["sat_dbg"], 4 * len(FIELDS))
        d = {f: int.from_bytes(b[i * 4:i * 4 + 4], "big") for i, f in enumerate(FIELDS)}
        if os.environ.get("UNTIL_VBLANK") and d["vblanks"] >= int(os.environ["UNTIL_VBLANK"]):
            break
        while shots and d["vblanks"] >= shots[0]:
            n = shots.pop(0)
            m.call("framebuffer_screenshot", path=str(WORK / "shots" / f"y{n:05d}.png"))
            print("shot", n, "at vblank", d["vblanks"], flush=True)
        if time.time() - last > 4:
            last = time.time()
            raw = m.read(syms["sat_gfx_stats"], struct.calcsize(STATS))
            print(round(time.time() - t0), {k: d[k] for k in ("stage", "vblanks", "task_runs", "idle_calls", "overruns", "gfx_skips", "obj_flips", "task_stack_high", "fatal", "fatal_detail", "fatal_task")},
                  "ms(emulator-only)", {k: round(d[k] * tick_us / 1000, 2) for k in ("gfx_ticks", "irq_ticks", "game_ticks", "gfx_peak", "irq_peak", "game_peak", "snap_ticks", "snap_peak")},
                  "gfx", dict(zip(stats_names, struct.unpack(STATS, raw))), "ff8018", m.read(syms["RAMB"] + 0x8018, 2).hex(), "stages", [int.from_bytes(m.read(syms["sat_gfx_stage"] + i * 4, 4), "big") for i in range(6)], flush=True)
        if d["fatal"]:
            print("fatal", hex(d["fatal"]), hex(d["fatal_detail"]), "symbols", sym_of(d["exc_pc"]), sym_of(d["exc_pr"]))
            s = m.read(syms["sat_boot_stack"] + 8192 - 1600, 1600) if d["fatal_task"] > 15 else m.read(syms["task_stacks"] + (d["fatal_task"] + 1) * 4096 - 1600, 1600)
            words = [int.from_bytes(s[i:i + 4], "big") for i in range(0, 1600, 4)]
            print("stack", [sym_of(w) for w in words if 0x06014000 <= w < 0x060fff00 or 0x00200000 <= w < 0x00300000 or 0x02400000 <= w < 0x02800000][:60])
            print("cpu", m.read(syms["sat_cpu"], 84).hex())
            break
    if "sat_prof" in syms:
        raw = m.read(syms["sat_prof"], 24 + 768)
        hd = struct.unpack(">6I", raw[:24])
        def row(i):
            h = struct.unpack(">128H", raw[24 + i * 256:24 + (i + 1) * 256])
            n = sum(h)
            if not n: return None
            bucket = 128 * tick_us / 1000
            cum, p95 = 0, 0
            for b, c in enumerate(h):
                cum += c
                if cum >= n * 0.95: p95 = b; break
            return dict(n=n, mean=round(sum((b + .5) * c for b, c in enumerate(h)) / n * bucket, 2), p95=round((p95 + 1) * bucket, 2), top=round((max(b for b, c in enumerate(h) if c) + 1) * bucket, 2))
        for name, size in (("sat_irq_stack", 8192), ("sat_slave_stack", 1024)):
            s = m.read(syms[name], size)
            print(name, "used", size - (len(s) - len(s.lstrip(b"\0"))), "of", size)
        if "sat_gfx_census" in syms:
            cw = struct.unpack(">41I", m.read(syms["sat_gfx_census"], 41 * 4))
            print("CENSUS", dict(zip("tiles offscreen empty commands runs banks banks_peak peak_frame missing_n".split(), cw)), "missing(section<<28|key)", [hex(x) for x in cw[9:9 + min(cw[8], 32)]], flush=True)
        print("PROF(MODELLED, Yaba FRT)", dict(zip("from to ticks done over skipped".split(), hd)), {k: row(i) for i, k in enumerate(("frame", "gfx", "snap"))}, flush=True)
    if "sat_speed" in syms:
        names = "frames upload_ticks uploads layer_uploads missing clean_frames clean_ticks clean_commands dirty_ticks commands peak_upload_ticks".split()
        print("SPEED", dict(zip(names, struct.unpack(">11I", m.read(syms["sat_speed"], 44)))), flush=True)
    if "sat_pcn" in syms:
        n = int.from_bytes(m.read(syms["sat_pcn"], 4), "big")
        (WORK / "pcs.bin").write_bytes(m.read(0x02557000, n * 8))
        print("PCS", n, flush=True)
    import bisect, re
    table = sorted((v, k) for k, v in syms.items())
    keys = [x[0] for x in table]
    print("pad raw", hex(int.from_bytes(m.read(syms["sat_pad_raw"], 4), "big")))
    print("status", m.call("debug_status")[:600])
    print("cpu", m.read(syms["sat_cpu"], 84).hex())
    m.call("pause")
    for _ in range(1):
        s = m.call("registers_get", cpu="master")
        print("regs", s[:900])
        pc = re.search(r"pc\W+(?:0x)?([0-9a-fA-F]+)", s, re.I); pr = re.search(r"pr\W+(?:0x)?([0-9a-fA-F]+)", s, re.I)
        if pc: print("pc", sym_of(int(pc[1], 16)))
        if pr: print("pr", sym_of(int(pr[1], 16)))
    m.call("resume")
    if DUMP:
        m.call("pause")
        pathlib.Path(DUMP).write_bytes(m.read(syms["RAMB"], 0x10000))
        pathlib.Path(DUMP + ".obj").write_bytes(m.read(syms["SAT_OBJ"], 0x4000))
        print("dump at vblank", int.from_bytes(m.read(syms["sat_dbg"] + 8, 4), "big"))
        m.call("resume")
    try:
        m.call("framebuffer_screenshot", path=str(WORK / "yaba.png"))
    except Exception as e:
        print("no shot", e)
finally:
    proc.kill(); proc.wait(10)
    # Lanes share this file: the campaign's settings go back whatever this run found.
    text = orig.decode("latin-1")
    for key, value in ((r"Video\VideoCore", "4"), (r"Sound\SoundCore", "1")):
        text = re.sub(rf"(?m)^{re.escape(key)}=.*$", (key + "=" + value).replace(chr(92), chr(92) * 2), text)
    INI.write_bytes(text.encode("latin-1"))
