"""The stage's first frame (lane perf2, 2026-11-11): usage first_frame.py CUE ELF TAG STAGE(hex) CHAR  (a SAT_PERF_STAGES build, Yaba cache ON, port 9742)
The review's hypothesis: when no slot is free, cache_find scans the whole slot array on every refused lookup, so a first picture with more distinct scroll 1 tiles than the cache holds
costs 20 and more ticks a cell. The two counters that decide it, read as deltas over the stage entry: sat_gfx_stats.refused_layer and sat_gfx_pf[4] (scan iterations for a free slot).
Also the stage timers of the draw that set gfx_peak (caught by polling gfx_peak while the stage loads) and the pf counters for the whole entry."""
import sys, time, os, json
sys.path.insert(0, 'E:/AvP/worktrees/perf2/tools/perf')
import pf2 as pf
cue, elf, tag, stage, ch = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4], 16), sys.argv[5]
os.makedirs(f"{pf.D}/peak", exist_ok=True)
y = pf.boot(cue, tag, "true"); Y = pf.Y(y.pid, elf); Y.ready()
S = Y.s; u = lambda a: int.from_bytes(Y.m.read(a, 4), "big")
POS = {1: (0, 0), 2: (1, 0), 8: (0, 1), 4: (1, 1)}; BIT = {"w": 1, "s": 2, "l": 8, "h": 4}
def pfc(): return [u(S["sat_gfx_pf"] + i * 4) for i in range(5)]
def refused(): return u(S["sat_gfx_stats"] + 44)
c0 = pfc(); r0 = refused(); pk0 = u(S["sat_dbg"] + 72)
print("before: pf", c0, "refused_layer", r0, "gfx_peak", pk0, flush=True)
Y.m.call("memory_write", address=hex(S['sat_home_warp']), size="long", value=hex(stage))
want = BIT[ch]; t0 = time.time(); caught = None; seen_peak = pk0
for k in ("start", "none", "start", "none"):
    if k != "none": Y.pulse(k)
    time.sleep(1.2)
while time.time() - t0 < 300:
    pk = u(S["sat_dbg"] + 72)
    if pk > seen_peak + 5000 and pk > 20000 and not caught:
        Y.m.call("pause"); time.sleep(0.3)
        stg = [u(S["sat_gfx_stage"] + i * 4) for i in range(13)]
        c1 = pfc(); gs = Y.m.read(S["sat_gfx_stats"], 56)
        caught = dict(peak=pk, gfx_ticks=u(S["sat_dbg"] + 60), vb=Y.vb(), stage=hex(Y.arc(0xff81e8)), stg=stg, pf_delta=[b - a for a, b in zip(c0, c1)], refused_delta=refused() - r0,
                      layer_uploads=int.from_bytes(gs[18:20], "big"), commands=int.from_bytes(gs[6:8], "big"))
        print("CAUGHT", json.dumps(caught), flush=True)
        Y.m.call("framebuffer_screenshot", path=f"{pf.D}/peak/{tag}_firstframe.png")
        Y.m.call("resume")
    st = Y.arc(0xff81e8); mode = Y.arc(0xff8001, 1); g09 = Y.arc(0xff8009, 1); cc = Y.arc(0xff81cc, 1) & 15
    if st == stage and mode == 2 and Y.arc(0xff8380, 1): break
    if st == 2 and mode == 2 and Y.arc(0xff8380, 1): Y.w(0xff81e9, "byte", stage & 255)
    elif st == 0 and g09 == 2 and cc:
        if cc == want: Y.pulse("a", gap=1.0)
        elif cc in POS:
            (x, yy), (wx, wy) = POS[cc], POS[want]
            Y.pulse("right" if wx > x else "left" if wx < x else ("down" if wy > yy else "up"), gap=0.8)
    else: Y.pulse("a", gap=0.9)
    time.sleep(0.1)
time.sleep(3)
c1 = pfc()
print("after entry: pf delta", [b - a for a, b in zip(c0, c1)], "refused_layer delta", refused() - r0, "gfx_peak", u(S["sat_dbg"] + 72), "stage", hex(Y.arc(0xff81e8)), flush=True)
json.dump(dict(caught=caught, pf_delta=[b - a for a, b in zip(c0, c1)], refused_delta=refused() - r0, gfx_peak=u(S["sat_dbg"] + 72)), open(f"{pf.D}/peak/{tag}.json", "w"))
y.terminate()
