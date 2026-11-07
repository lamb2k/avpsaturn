# usage: clipmatch.py RUN CLIPS: for each MAME-rendered clip in CLIPS, best normalized correlation anywhere in the Saturn capture (RUN/raw). Sound effects only; music is CD audio mixed in. Tier: EMULATOR against MAME, not a listening test.
import pathlib, sys, wave
import numpy as np
run, clips = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
R = 22050
def down(x, rate):
    n = int(len(x) * R / rate)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)
cap = np.concatenate([np.fromfile(f, dtype='<i2').reshape(-1, 2).mean(axis=1)[::2] for f in sorted((run / 'raw').glob('leg*.raw'))]).astype(np.float32)
cap -= cap.mean()
N = 1 << int(np.ceil(np.log2(len(cap) + R * 8)))
F = np.fft.rfft(cap, N)
c2 = np.cumsum(cap.astype(np.float64) ** 2)
rows = []
for c in sorted(clips.glob('*.wav')):
    with wave.open(str(c)) as w:
        rate, ch, d = w.getframerate(), w.getnchannels(), w.readframes(w.getnframes())
    x = np.frombuffer(d, dtype='<i2').astype(np.float32).reshape(-1, ch).mean(axis=1)
    x = down(x, rate)
    e = np.abs(x); nz = np.flatnonzero(e > 200)
    if len(nz) < R // 20:
        continue
    x = x[nz[0]:nz[-1] + 1][:R * 2]; x = x - x.mean(); m = len(x)
    xc = np.fft.irfft(F * np.conj(np.fft.rfft(x, N)), N)[:len(cap) - m]
    en = c2[m:len(cap)] - c2[:len(cap) - m]
    r = xc[:len(en)] / np.sqrt(np.maximum(en, 1) * (x.astype(np.float64) ** 2).sum())
    r[en < 1e5] = 0
    rows.append((c.stem, float(r.max()), int(r.argmax()) / R))
    print(c.stem, round(rows[-1][1], 3), 'at capture s', round(rows[-1][2], 1), flush=True)
v = np.array([q[1] for q in rows])
print('clips', len(v), 'median', round(float(np.median(v)), 3), '>=0.8', int((v >= .8).sum()), '>=0.5', int((v >= .5).sum()))
