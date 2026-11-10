"""Select-screen check: after the pick, is "Let's go, bub." played once, in full, and not again when the game moves on? usage: select_check.py RUN [CMDHEX=207]
Window: the raw SCSP dump from the 'select pick' event to the 'in stage' event (events json). Prints the loud runs and a sliding match of the MAME render of the command (10 ms RMS envelope)."""
import json
import sys
import wave

import numpy as np

RUN = sys.argv[1]
cmd = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x207
base = "E:/AvP/learning/lane-wv-sounds/"
SR = 44100
raw = np.fromfile(base + f"yaba/{RUN}.raw", dtype="<i2").reshape(-1, 2).astype(np.float64).mean(axis=1)
ev = {e["name"]: e for e in json.load(open(base + f"yaba/{RUN}.events.json"))}
a, b = ev["select pick"]["raw"] // 4, ev["in stage"]["raw"] // 4
seg = raw[a:b]
print("window %.1f s" % (len(seg) / SR))
W = 441


def env(x):
    n = len(x) // W
    return np.sqrt((x[:n * W].reshape(n, W) ** 2).mean(axis=1))


e = env(seg)
loud = np.nonzero(e > 150)[0]
runs, s = [], None
for i, k in enumerate(loud):
    if s is None:
        s = p = k
    elif k - p > 15:
        runs.append((s, p)); s = p = k
    else:
        p = k
if s is not None:
    runs.append((s, p))
for s, p in runs:
    print("run at %.2f s for %.2f s peak rms %d" % (s * W / SR, (p - s + 1) * W / SR, e[s:p + 1].max()))
w = wave.open(base + "cat/wav/%04x.wav" % cmd)
r = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64).reshape(-1, 2).mean(axis=1)
k = w.getframerate() / SR
r = np.interp(np.arange(0, len(r) / k) * k, np.arange(len(r)), r)
er = env(r)
n = len(er)
hits = []
for i in range(0, len(e) - n):
    c = np.corrcoef(e[i:i + n], er)[0, 1] if e[i:i + n].std() > 0 else 0
    hits.append(c)
hits = np.array(hits)
peaks = [i for i in range(1, len(hits) - 1) if hits[i] > 0.8 and hits[i] >= hits[i - 1] and hits[i] >= hits[i + 1]]
print("render length %.2f s; matches (corr > 0.8) at s:" % (n * W / SR), [(round(i * W / SR, 2), round(float(hits[i]), 3)) for i in peaks])
if peaks:
    i = peaks[0]
    y = seg[i * W:i * W + n * W]
    print("first match: level %+.1f dB, tail 30 ms rms %d (render %d)" % (20 * np.log10(np.sqrt((y ** 2).mean()) / np.sqrt((r[:n * W] ** 2).mean())), np.sqrt((y[-1323:] ** 2).mean()), np.sqrt((r[n * W - 1323:n * W] ** 2).mean())))
