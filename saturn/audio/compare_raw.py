#!/usr/bin/env python
"""Real capture against MAME: the SCSP's own output (raw s16le stereo 44.1 kHz from the patched Yaba, yaba_wav_dump.patch), not a modelled mix.
usage: compare_raw.py WORK RAW     WORK holds ref.wav and ref.tsv (MAME, same script). Reports silence, offset by best 10 ms envelope alignment, envelope correlation and level per second window.
Tier: EMULATOR output compared to MAME. Not a listening test and not hardware."""
import pathlib, sys, wave
import numpy as np
RATE = 44100
work, raw = pathlib.Path(sys.argv[1]), sys.argv[2]
with wave.open(str(work / "ref.wav")) as w:
    ref = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, 2).astype(np.float32)
ref = ref[int(float(open(work / "ref.tsv").readline().split()[1]) * RATE):]
cap = np.fromfile(raw, dtype="<i2").reshape(-1, 2).astype(np.float32)


def env(x, step=441):
    n = len(x) // step
    e = np.sqrt(((x[:n * step].astype(np.float64) ** 2).mean(axis=1)).reshape(n, step).mean(axis=1))
    return e


er, ec = env(ref), env(cap)
print("seconds capture", round(len(cap) / RATE, 1), "ref", round(len(ref) / RATE, 1))
print("capture peak", int(np.abs(cap).max()), "rms", round(float(np.sqrt((cap.astype(np.float64) ** 2).mean())), 1), "windows above -60 dB %", round(100 * float((ec > 32).mean()), 1))
print("ref peak", int(np.abs(ref).max()), "rms", round(float(np.sqrt((ref.astype(np.float64) ** 2).mean())), 1), "windows above -60 dB %", round(100 * float((er > 32).mean()), 1))
n = min(len(er), 3000)
a = er[:n]
best = max(range(0, max(1, len(ec) - n)), key=lambda d: float(np.dot(a, ec[d:d + n])))
b = ec[best:best + n]
print("best offset s", best / 100, "whole envelope corr", round(float(np.corrcoef(a, b)[0, 1]), 3), "level dB", round(20 * float(np.log10((b.mean() + 1) / (a.mean() + 1))), 1))
rows = []
for s in range(0, n - 100, 100):
    x, y = a[s:s + 100], b[s:s + 100]
    if x.max() > 200 and x.std() > 0 and y.std() > 0:
        rows.append(float(np.corrcoef(x, y)[0, 1]))
print("1 s windows with sound", len(rows), "median corr", round(float(np.median(rows)), 3) if rows else None, "p10", round(float(np.percentile(rows, 10)), 3) if rows else None)
