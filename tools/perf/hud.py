"""HUD check: boot a disc, enter a stage, play (free running, scripted random input), screenshots of the running game. usage: hud.py CUE ELF TAG STAGE CHAR CACHE SECONDS"""
import sys, time, random, os
sys.path.insert(0, 'E:/AvP/learning/lane-perf')
import pf
cue, elf, tag, stage, ch, cache, secs = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4], 16), sys.argv[5], sys.argv[6], int(sys.argv[7])
out = f"{pf.D}/hud_shots/{tag}"; os.makedirs(out, exist_ok=True)
y = pf.boot(cue, tag, cache); Y = pf.Y(y.pid, elf); Y.ready()
POS = {1: (0, 0), 2: (1, 0), 8: (0, 1), 4: (1, 1)}; BIT = {"w": 1, "s": 2, "l": 8, "h": 4}
Y.m.call("memory_write", address=hex(Y.s['sat_home_warp']), size="long", value=hex(stage))
want = BIT[ch]; t0 = time.time()
for k in ("start", "none", "start", "none"):
    if k != "none": Y.pulse(k)
    time.sleep(1.2)
while time.time() - t0 < 300:
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
print("in stage", hex(Y.arc(0xff81e8)), flush=True)
rnd = random.Random(5); t0 = time.time(); n = 0; last = 0
while time.time() - t0 < secs:
    r = rnd.random(); ks = {"right"} if r < .45 else ({"left"} if r < .6 else set())
    if rnd.random() < .5: ks |= {"b"}
    if rnd.random() < .15: ks |= {"a"}
    Y.set(sorted(ks)); time.sleep(0.3)
    if time.time() - last > 4:
        last = time.time(); n += 1
        print(Y.m.call("framebuffer_screenshot", path=f"{out}/play_{n:02d}.png").replace("\n", " | ")[:200], flush=True)
Y.set([])
y.terminate()
