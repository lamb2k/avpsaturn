import sys, time
sys.path.insert(0, 'E:/AvP/learning/lane-perf')
import pf
y = pf.boot('E:/AvP/package-integration/perf_hud_1/perf_hud_1.cue', 'hud_dbg', 'true'); Y = pf.Y(y.pid, 'E:/AvP/learning/lane-perf/keep/w3h_sat.elf'); Y.ready()
Y.m.call("memory_write", address=hex(Y.s['sat_home_warp']), size="long", value="0xe")
for k in ("start", "none", "start", "none"):
    if k != "none": Y.pulse(k)
    time.sleep(1.2)
t0 = time.time()
while time.time() - t0 < 300:
    st = Y.arc(0xff81e8); mode = Y.arc(0xff8001, 1); g09 = Y.arc(0xff8009, 1); cc = Y.arc(0xff81cc, 1) & 15
    if st == 0xe and mode == 2 and Y.arc(0xff8380, 1): break
    if st == 0 and g09 == 2 and cc:
        if cc == 1: Y.pulse("a", gap=1.0)
        else: Y.pulse("right", gap=0.8)
    else: Y.pulse("a", gap=0.9)
    time.sleep(0.1)
time.sleep(5)
Y.m.call("pause"); time.sleep(0.5)
u = lambda a: int.from_bytes(Y.m.read(a, 4), "big")
print("vb", Y.vb(), "fps_on", u(Y.s['fps_on']), "fps_next", u(Y.s['fps_next']), "sat_home_hold", u(Y.s['sat_home_hold']) if 'sat_home_hold' in Y.s else None)
print("st", [u(Y.s['st'] + i * 4) for i in range(10)])
print("text", Y.m.read(Y.s['text'], 50))
print("shadow", [hex(int.from_bytes(Y.m.read(Y.s['shadow'] + i * 2, 2), "big")) for i in range(8)])
row = Y.m.read(0x25E1E000 + 24 * 64 * 2, 48)
print("vdp2 map row24", row.hex())
print("snap.home?", "n/a")
y.terminate()
