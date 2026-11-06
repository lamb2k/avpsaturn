#!/usr/bin/env python
"""Run the Saturn image under Yaba for a bounded time and read the runtime's debug block over MCP. Tier: EMULATOR.
usage: run_yaba.py [WORK] [seconds] [dump.bin]"""
import json, os, pathlib, re, socket, subprocess, sys, time
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
FIELDS = "magic stage vblanks ff8018 task_runs idle_calls task_stack_high fatal fatal_detail fatal_task a0 a1 a7 exc_pc exc_pr".split()


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
    prev = None
    while time.time() - t0 < SECS:
        time.sleep(4)
        b = m.read(syms["sat_dbg"], 4 * len(FIELDS))
        d = {f: int.from_bytes(b[i * 4:i * 4 + 4], "big") for i, f in enumerate(FIELDS)}
        diag = m.read(0x06013fe0, 20).hex()
        print(round(time.time() - t0), json.dumps({k: hex(v) for k, v in d.items()}), "loader", diag, "ff8018", m.read(syms["RAMB"] + 0x8018, 4).hex(), flush=True)
        if d["fatal"]:
            print("fatal symbols", sym_of(d["exc_pc"]), sym_of(d["exc_pr"]))
            s = m.read(syms["sat_boot_stack"] + 8192 - 1600, 1600) if d["fatal_task"] > 15 else m.read(syms["task_stacks"] + (d["fatal_task"] + 1) * 8192 - 1600, 1600)
            words = [int.from_bytes(s[i:i + 4], "big") for i in range(0, 1600, 4)]
            print("stack", [sym_of(w) for w in words if 0x06014000 <= w < 0x060fff00 or 0x00200000 <= w < 0x002f0000][:60])
            if os.environ.get("REGS"): print("cpu", m.read(syms["sat_cpu"], 84).hex())
            break
    import bisect, re
    table = sorted((v, k) for k, v in syms.items())
    keys = [x[0] for x in table]
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
        pathlib.Path(DUMP + ".obj").write_bytes(m.read(syms["SAT_OBJ"] + 0x8000, 0x2000))
        print("dump at vblank", int.from_bytes(m.read(syms["sat_dbg"] + 8, 4), "big"))
        m.call("resume")
    try:
        m.call("framebuffer_screenshot", path=str(WORK / "yaba.png"))
    except Exception as e:
        print("no shot", e)
finally:
    proc.kill(); proc.wait(10)
    INI.write_bytes(orig)
