import sys, csv, statistics as S, collections
rows = list(csv.DictReader(open(sys.argv[1]), delimiter='\t'))
for r in rows:
    for k in r: r[k] = float(r[k]) if '.' in r[k] else int(r[k], 16) if k == 'stage' else int(r[k])
import sys
lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
hi = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
rows = [r for r in rows if lo <= r['frame'] < hi]
n = len(rows)
# mark hold frames: zero-start runs >=3, ff81b9 frames (+-2), stage 0
hold = [False] * n
i = 0
while i < n:
    if rows[i]['t808a'] == 0:
        j = i
        while j < n and rows[j]['t808a'] == 0: j += 1
        if j - i >= 3:
            for k in range(i, j): hold[k] = True
        i = j
    else: i += 1
for i, r in enumerate(rows):
    if r['stage'] == 0 or r['ff81b9']:
        for k in range(max(0, i - 2), min(n, i + 3)): hold[k] = True
segs = []; i = 0
while i < n:
    if hold[i]: i += 1; continue
    j = i
    while j < n and not hold[j]: j += 1
    segs.append((i, j)); i = j
print("active gameplay segments (no hold >=3 frames, no fast-forward, in a stage):", len(segs), "frames", sum(j - i for i, j in segs), "of", n)
tot_f = tot_t = 0; ticks_hist = collections.Counter(); crowd = collections.Counter()
cum = collections.defaultdict(lambda: [0, 0, 0, 0, 0])   # frames, starts, zero-frames, overrun events, frames with >=2 starts
for i, j in segs:
    for k in range(i, j):
        r = rows[k]; c = r['t808a']
        ticks_hist[c] += 1
        e = min(int(r['enemies']), 8)
        cc = cum[e]; cc[0] += 1; cc[1] += c; cc[2] += (c == 0); cc[3] += r['ovr']; cc[4] += (c >= 2)
        tot_f += 1; tot_t += c
print(f"ticks per vblank in active gameplay frames: {tot_t}/{tot_f} = {60*tot_t/tot_f:.2f} per 60 vblanks")
print("starts per frame histogram", dict(sorted(ticks_hist.items())))
print("\nby enemies on screen (distinct enemy actors in the object list; 8 = 8 or more):")
print("enemies frames  ticks/60vb  zero-start-frames  overrun-events  frames>=2-starts  avg-busy-ms  p99-busy  max-busy")
for e in sorted(cum):
    f, t, z, o, m = cum[e]
    b = sorted(rows[k]['busy_ms'] for i, j in segs for k in range(i, j) if min(int(rows[k]['enemies']), 8) == e)
    print(f"{e:5d} {f:6d} {60*t/f:9.2f} {z:8d} ({100*z/f:4.1f}%) {o:6d} {m:6d} {S.mean(b):8.2f} {b[int(.99*len(b))]:8.2f} {b[-1]:8.2f}")
# the worst active segments: ticks lost = vblanks - starts (including catch-up)
print("\nactive segments >=120 frames with the lowest tick rate:")
res = []
for i, j in segs:
    if j - i < 120: continue
    t = sum(rows[k]['t808a'] for k in range(i, j)); res.append((60 * t / (j - i), i, j - i, S.mean(rows[k]['enemies'] for k in range(i, j)), sum(rows[k]['ovr'] for k in range(i, j)), rows[i]['stage']))
res.sort()
for r in res[:10]: print(f"ticks/60 {r[0]:.2f} frame {r[1]} len {r[2]} enemies avg {r[3]:.1f} overrun-events {r[4]} stage {r[5]:02x}")
print("segments >=120:", len(res), "median", S.median(r[0] for r in res))
# frames the tick time exceeded a frame: busy_ms>16.77
over = [rows[k] for i, j in segs for k in range(i, j) if rows[k]['max_ms'] > 16.77]
print("ticks longer than one frame (16.77 ms):", len(over), "max", max((r['max_ms'] for r in over), default=0))
mx = sorted(r['max_ms'] for i, j in segs for k in range(i, j) for r in [rows[k]] if r['ndur'])
print("single-tick duration ms: median %.2f p90 %.2f p99 %.2f max %.2f" % (mx[len(mx)//2], mx[int(.9*len(mx))], mx[int(.99*len(mx))], mx[-1]))
