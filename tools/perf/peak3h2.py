import sys, time, os
sys.path.insert(0, 'E:/AvP/learning/lane-perf')
import pf
cue, elf, tag = sys.argv[1], sys.argv[2], sys.argv[3]
out = f"{pf.D}/peak/{tag}"; os.makedirs(out, exist_ok=True)
y = pf.boot(cue, tag, "true"); Y = pf.Y(y.pid, elf); Y.ready(vb=300)
u = lambda a: int.from_bytes(Y.m.read(a, 4), "big")
def rd(label):
    d = Y.m.read(Y.s["sat_dbg"], 104); g = lambda o: int.from_bytes(d[o:o+4], "big")
    print(f"{label}: vb {g(8)} gfx {g(60)} gfx_peak {g(72)} snap_peak {g(96)} game_peak {g(80)} stage {Y.arc(0xff81e8):x} mode {Y.arc(0xff8001,1)}", flush=True)
time.sleep(20); rd("title idle")
shot = lambda n: Y.m.call("framebuffer_screenshot", path=f"{out}/{n}.png")
shot("0_title")
for k, nm in (("down", "1_down"), ("down", "2_down"), ("down", "3_down"), ("a", "4_a_stageselect"), ("down", "5_down"), ("up", "6_up")):
    Y.pulse(k); time.sleep(4); rd(nm); shot(nm)
time.sleep(10); rd("after 10s"); shot("6_later")
y.terminate()
