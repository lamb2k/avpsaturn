#!/usr/bin/env python
"""Summarise E:/AvP/learning/mame/<run>/probe.tsv from learn_audio_probe.lua. usage: learn_audio_ring.py RUN [first last]"""
import collections, csv, sys
run = sys.argv[1]
lo, hi = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 10**9)
rows = list(csv.reader(open(f"E:/AvP/learning/mame/{run}/probe.tsv"), delimiter="\t"))[1:]
ent, snd, ticks, fr, q = [], [], collections.Counter(), {}, collections.deque()
lat = collections.Counter(); bpf = collections.Counter(); epf = collections.Counter(); spf = collections.Counter()
worst = []
for r in rows:
    f = int(r[0])
    if r[1] == "E":
        q.append((f, r[3]))
        if lo <= f <= hi: epf[f] += 1
    elif r[1] == "S":
        ef, cmd = q.popleft()
        if lo <= f <= hi:
            spf[f] += 1; lat[f - ef] += 1
            worst.append((f - ef, f, cmd))
    elif r[1] == "T":
        if lo <= f <= hi: ticks[f] += 1
    elif r[1] == "F" and lo <= f <= hi:
        h, t = int(r[2], 16), int(r[3], 16)
        bl = ((t - h) & 0x3f0) // 16
        bpf[bl] += 1
        fr[f] = (bl, r[4], r[5], r[6], r[7])
print(run, "window", lo, hi if hi < 10**9 else "end", "frames", len(fr))
print("enqueued", sum(epf.values()), "sent", sum(spf.values()), "left in ring", len(q))
print("max enqueued in a frame", max(epf.values(), default=0), "max sent in a frame", max(spf.values(), default=0))
print("frame-end backlog histogram", sorted(bpf.items()))
print("enqueue-to-send latency in frames", sorted(lat.items()))
print("worst", sorted(worst, reverse=True)[:5])
print("ticks per frame", sorted(collections.Counter(ticks.values()).items()))
print("handshake at frame end", collections.Counter(v[1] for v in fr.values()), "ff81ad*256+b0", collections.Counter(v[3] for v in fr.values()))
print("frames with ff81b9 nonzero", sum(1 for v in fr.values() if v[2] != "0"))
z = collections.Counter(((int(v[4], 16) >> 8) - (int(v[4], 16) & 255)) & 255 for v in fr.values()); print("z80 ring backlog bytes", sorted(z.items()))
