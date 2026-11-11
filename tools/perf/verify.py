"""Exactness / look check of SAT_S1_MEMO and SAT_S1_BLANKROWS on a SAT_PERF_STAGES build: usage verify.py CUE ELF TAG STAGE
1. verify bytes on: free play (random input, 40 s wall), then read sat_s1m (memo hits/misses/diffs, blank rows skipped/diffs).
2. still pair from one save state: memo off vs on (both settle on the same static picture), pixel diff of the last frame."""
import sys, time, random, os, json, glob
sys.path.insert(0, 'E:/AvP/learning/lane-perf')
import pf
cue, elf, tag, stage = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4], 16)
out = f"{pf.D}/verify/{tag}"; os.makedirs(out, exist_ok=True)
y = pf.boot(cue, tag, "true"); Y = pf.Y(y.pid, elf); Y.ready()
Y.m.call("memory_write", address=hex(Y.s['sat_home_warp']), size="long", value=hex(stage))
POS = {1: (0, 0)}
for k in ("start", "none", "start", "none"):
    if k != "none": Y.pulse(k)
    time.sleep(1.2)
POS = {1: (0, 0), 2: (1, 0), 8: (0, 1), 4: (1, 1)}; want = 1; t0 = time.time()
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
print("entered stage", hex(Y.arc(0xff81e8)), flush=True)
time.sleep(4)
S = Y.s
def wb(name, v): Y.m.call("memory_write", address=hex(S[name]), size="byte", value=hex(v))
def cnt(): return [int.from_bytes(Y.m.read(S['sat_s1m'] + i * 4, 4), "big") for i in range(6)]
wb('sat_s1_memo_verify', 1); wb('sat_s1_memo_off', 0)
c0 = cnt(); rnd = random.Random(9); t0 = time.time()
while time.time() - t0 < 40:
    r = rnd.random(); ks = {"right"} if r < .45 else ({"left"} if r < .6 else set())
    if rnd.random() < .3: ks |= {"b"}
    if rnd.random() < .1: ks |= {"a"}
    Y.set(sorted(ks)); time.sleep(0.3)
Y.set([]); Y.m.call("pause"); time.sleep(0.5)
c1 = cnt()
print("sat_s1m delta (memo hits, misses, memo DIFFS, story-box calls, blank rows skipped, blank DIFFS):", [b - a for a, b in zip(c0, c1)], "stage", hex(Y.arc(0xff81e8)), flush=True)
json.dump(dict(c0=c0, c1=c1), open(f"{out}/counters.json", "w"))
# still pair
Y.m.call("save_state", slot=3)
shots = {}
for off in (0, 1):
    Y.m.call("load_state", slot=3); time.sleep(0.6)
    wb('sat_s1_memo_off', off); wb('sat_s1_memo_verify', 0)
    Y.m.call("framebuffer_burst", directory=f"{out}/b{off}", frames=70, prefix="b")
    pngs = sorted(glob.glob(f"{out}/b{off}/*.png")); shots[off] = pngs[-1] if pngs else None
try:
    from PIL import Image, ImageChops
    a = Image.open(shots[0]).convert("RGB"); b = Image.open(shots[1]).convert("RGB")
    d = ImageChops.difference(a, b); n = sum(1 for p in d.get_flattened_data() if p != (0, 0, 0)) if hasattr(d, "get_flattened_data") else sum(1 for p in d.getdata() if p != (0, 0, 0))
    print("still pair (memo off vs on, same save state, frame 70): differing pixels", n, "bbox", d.getbbox(), shots, flush=True)
except Exception as e: print("still pair failed", e)
y.terminate()
