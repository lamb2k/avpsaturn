"""Screenshot (env COOP=1: with the scripted second pad joined, SAT_INPUT_SCRIPT2 builds) of a stage, with the SAT_FPS_HUD readout when the build has it (lane perf2, 2026-11-11): usage shot_hud.py CUE ELF TAG STAGE(hex) CHAR [OUTPNG]
Enters the stage as run2.py does, lets it play 400 vblanks, saves the Yaba frame buffer (EMULATOR, cache on)."""
import sys, time, os
sys.path.insert(0, 'E:/AvP/worktrees/perf2/tools/perf')
import pf2 as pf
cue, elf, tag, stage, ch = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4], 16), sys.argv[5]
out = sys.argv[6] if len(sys.argv) > 6 else f"{pf.D}/hud_{tag}.png"
y = pf.boot(cue, tag, "true"); Y = pf.Y(y.pid, elf); Y.ready()
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
if os.environ.get('COOP') == '1':   # SAT_INPUT_SCRIPT2 build: arm the scripted second pad, give it 700 vblanks to join and walk
    Y.m.call("memory_write", address=hex(Y.s['sat_pad2_t0']), size="long", value=hex(Y.vb()))
    wait = 700
else: wait = 400
v = Y.vb()
while Y.vb() - v < wait: time.sleep(0.5)
Y.set(["right"]); time.sleep(2.0); Y.set([])
Y.m.call("pause"); time.sleep(0.5)
print(Y.m.call("framebuffer_screenshot", path=out).replace("\n", " | ")[:120])
y.terminate()
