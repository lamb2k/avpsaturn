"""Catch the draw that sets gfx_peak above 30,000 ticks (a PERF_STAGES build): usage peak_stg.py CUE ELF TAG"""
import sys, time, os
sys.path.insert(0, 'E:/AvP/learning/lane-perf')
import pf
cue, elf, tag = sys.argv[1], sys.argv[2], sys.argv[3]
y = pf.boot(cue, tag, "true"); Y = pf.Y(y.pid, elf); Y.ready(vb=300)
S = Y.s; u = lambda a: int.from_bytes(Y.m.read(a, 4), "big")
time.sleep(15)
Y.pulse("start"); t0 = time.time(); last = 0
while time.time() - t0 < 240:
    for k in ("a", "start"):
        pass
    pk = u(S["sat_dbg"] + 72)
    if pk > 30000:
        Y.m.call("pause"); time.sleep(0.3)
        stg = [u(S["sat_gfx_stage"] + i * 4) for i in range(13)]
        gs = Y.m.read(S["sat_gfx_stats"], 24)
        print("peak", pk, "gfx_ticks", u(S["sat_dbg"] + 60), "vb", Y.vb(), "stage", hex(Y.arc(0xff81e8)), "stg", stg,
              "uploads", int.from_bytes(gs[10:12], "big"), "layer_uploads", int.from_bytes(gs[18:20], "big"), "pieces", int.from_bytes(gs[6:8], "big"), flush=True)
        Y.m.call("framebuffer_screenshot", path=f"{pf.D}/peak/{tag}_peak.png")
        break
    if time.time() - last > 3: Y.pulse("a", gap=0.2); last = time.time()
    time.sleep(0.05)
else: print("no peak above 30000; gfx_peak", u(S["sat_dbg"] + 72), "stage", hex(Y.arc(0xff81e8)))
y.terminate()
