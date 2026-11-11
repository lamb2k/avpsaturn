"""Catch the draw that sets gfx_peak above 30,000 ticks (a PERF_STAGES build) through the menus (title, character select, stage select): usage peak_stg2.py CUE ELF TAG. Lane perf2: also pf[0..4] and refused_layer deltas since the title (the stage first frame hypothesis)."""
import sys, time, os
sys.path.insert(0, 'E:/AvP/worktrees/perf2/tools/perf')
import pf2 as pf
cue, elf, tag = sys.argv[1], sys.argv[2], sys.argv[3]
y = pf.boot(cue, tag, "true"); Y = pf.Y(y.pid, elf); Y.ready(vb=300)
S = Y.s; u = lambda a: int.from_bytes(Y.m.read(a, 4), "big")
time.sleep(15)
c0 = [u(S['sat_gfx_pf'] + i * 4) for i in range(5)]; r0 = u(S['sat_gfx_stats'] + 44)
Y.pulse("start"); t0 = time.time(); last = 0
while time.time() - t0 < 240:
    for k in ("a", "start"):
        pass
    pk = u(S["sat_dbg"] + 72)
    if pk > 30000:
        Y.m.call("pause"); time.sleep(0.3)
        stg = [u(S["sat_gfx_stage_last" if "sat_gfx_stage_last" in S else "sat_gfx_stage"] + i * 4) for i in range(13)]; c1 = [u(S["sat_gfx_pf"] + i * 4) for i in range(5)]
        gs = Y.m.read(S["sat_gfx_stats"], 56)
        print("peak", pk, "gfx_ticks", u(S["sat_dbg"] + 60), "vb", Y.vb(), "stage", hex(Y.arc(0xff81e8)), "stg", stg,
              "uploads", int.from_bytes(gs[10:12], "big"), "layer_uploads", int.from_bytes(gs[18:20], "big"), "pieces", int.from_bytes(gs[6:8], "big"), "pf_delta", [b - a for a, b in zip(c0, c1)], "refused_layer_delta", u(S["sat_gfx_stats"] + 44) - r0, flush=True)
        Y.m.call("framebuffer_screenshot", path=f"{pf.D}/peak/{tag}_peak.png")
        break
    if time.time() - last > 3: Y.pulse("a", gap=0.2); last = time.time()
    time.sleep(0.05)
else: print("no peak above 30000; gfx_peak", u(S["sat_dbg"] + 72), "stage", hex(Y.arc(0xff81e8)))
y.terminate()
