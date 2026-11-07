# usage: capt.py RUN OUT [secs]: per-stage WAV clips from RUN/raw/legNNN.raw using the raw positions on STAGE lines. Reports level and silence per clip.
import pathlib, re, sys, wave
import numpy as np
run, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); secs = int(sys.argv[3]) if len(sys.argv) > 3 else 20
out.mkdir(parents=True, exist_ok=True)
seen = {}
for l in (run / 'rounds_proof.txt').read_text(errors='replace').splitlines():
    m = re.match(r'LOAD .*stage (0x[0-9a-f]+) .*raw (leg\d+\.raw) (\d+)', l) or re.match(r'STAGE (0x[0-9a-f]+) .*raw (leg\d+\.raw) (\d+)', l)
    if m and m[1] not in seen:
        seen[m[1]] = (m[2], int(m[3]))
BPS = 176400
print('stage leg start_s rms peak silent% lchan_rchan_diff')
for st, (leg, pos) in seen.items():
    pos = pos & ~3
    # A stage's first seconds are its load, silent on the capture: go forward to its sound, into later legs if needed.
    legs = sorted((run / 'raw').glob('leg*.raw')); k = [x.name for x in legs].index(leg); off = pos; d = None
    while k < len(legs):
        a = np.fromfile(legs[k], dtype='<i2', offset=off)
        e = np.abs(a.reshape(-1, 2)).max(axis=1)
        c_ = np.cumsum(e > 64); w_ = c_[22050:] - c_[:-22050] if len(e) > 22050 else np.zeros(1)
        i = np.flatnonzero(w_ > 2000)
        if len(i) and len(a) // 2 - i[0] > 44100 * 3:
            d = a[2 * int(i[0]):2 * int(i[0]) + secs * 88200]; pos = off + 4 * int(i[0]); leg = legs[k].name; break
        k += 1; off = 0
    if d is None:
        print(st, 'no sound found'); continue
    with wave.open(str(out / f'stage{int(st, 16):02x}.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(44100); w.writeframes(d.tobytes())
    x = d.astype(float); e = np.abs(x.reshape(-1, 2)).max(axis=1)
    print(st, leg, round(pos / BPS, 1), len(d) // 88200, 's rms', int(np.sqrt((x ** 2).mean())), 'peak', int(np.abs(x).max()), 'silent%', round(100 * (e < 8).mean(), 1), 'L-R', int(np.abs(x[::2] - x[1::2]).mean()))
