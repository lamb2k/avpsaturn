import sys, time
sys.path.insert(0, 'E:/AvP/learning/lane-perf')
import pf
y = pf.boot('E:/AvP/package-integration/perf_hud_1/perf_hud_1.cue', 'hud_dbg2', 'true'); Y = pf.Y(y.pid, 'E:/AvP/learning/lane-perf/keep/w3h_sat.elf'); Y.ready()
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
time.sleep(6)
Y.m.call("pause"); time.sleep(0.5)
print("cell P  ", Y.m.read(0x25E00000 + 0x18000 + 927 * 32, 32).hex())
print("cell pnl", Y.m.read(0x25E00000 + 0x18000 + 938 * 32, 32).hex())
print("cell 0  ", Y.m.read(0x25E00000 + 0x18000, 16).hex())
print("cram62  ", Y.m.read(0x25F00000 + 992 * 2, 64).hex())
for a in (0x25F80020, 0x25F80028, 0x25F8002a, 0x25F80010, 0x25F80012, 0x25F80036, 0x25F8004c, 0x25F8004e, 0x25F800f8, 0x25F800fa, 0x25F80070):
    try: print(hex(a), Y.m.read(a, 2).hex())
    except Exception as e: print(hex(a), 'err', e)
print("shot", Y.m.call("framebuffer_screenshot", path="E:/AvP/learning/lane-perf/hud_shots/dbg2.png").replace("\n"," | ")[:100])
y.terminate()
