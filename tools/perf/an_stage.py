#!/usr/bin/env python
"""usage: an_stage.py GS.LOG V0 V1   (lane perf-pic)  Per slave draw, the FRT ticks at the STAGE points of sat_gfx_draw (the 'S vb idx ticks' lines the profiling Ymir logs for HW_STAGE):
[0] start after the palette/stamp set-up, [4] before the sprite build, [5] after it (the plot starts next), [1] after the menu/readout part, [2] before the wait for the layer half,
[3] end of the draw. Prints mean / median / p90 / max of each phase in ticks (a field is about 3,500)."""
import re, sys, statistics
V0, V1 = int(sys.argv[2]), int(sys.argv[3])
cur = {}; draws = []
for l in open(sys.argv[1], errors='replace'):
    if l.startswith('S '):
        t = l.split(); vb, i, v = int(t[1]), int(t[2]), int(t[3])
        if i > 12: continue
        if i == 0 and cur: draws.append(cur); cur = {}
        cur['vb'] = vb; cur[i] = v
if cur: draws.append(cur)
D = [d for d in draws if V0 <= d['vb'] <= V1 and all(k in d for k in (0, 4, 5, 1, 2, 3))]
P = [d for d in D if all(k in d for k in (6, 7, 8, 9))]   # PERF_STAGES builds only
print('draws', len(D))
def stat(name, f):
    x = sorted(f(d) for d in D); n = len(x)
    print('%-38s mean %6.0f  median %6d  p90 %6d  max %6d' % (name, statistics.mean(x), x[n // 2], x[int(.9 * n)], x[-1]))
stat('set-up to sprite build start (0..4)', lambda d: d[4] - d[0])
stat('sprite build (4..5)', lambda d: d[5] - d[4])
stat('plot start, menus, readout (5..1)', lambda d: d[1] - d[5])
stat('rowscroll to layer wait (1..2)', lambda d: d[2] - d[1])
stat('layers incl. wait for master (2..3)', lambda d: d[3] - d[2])
stat('whole draw (0..3)', lambda d: d[3] - d[0])

if P:
    print('PERF_STAGES build: layers split, draws with all stamps: %d' % len(P))
    def stat2(name, f, L=P):
        x = sorted(f(d) for d in L); n = len(x)
        print('%-38s mean %6.0f  median %6d  p90 %6d  max %6d' % (name, statistics.mean(x), x[n // 2], x[int(.9 * n)], x[-1]))
    stat2('wait for the master layer half (2..6)', lambda d: d[6] - d[2])
    stat2('scroll 2 (6..7)', lambda d: d[7] - d[6])
    stat2('scroll 3 (7..8)', lambda d: d[8] - d[7])
    stat2('scroll 1 (8..9)', lambda d: d[9] - d[8])
    S1 = [d for d in P if d[9] - d[8] > 40]
    if S1:
        print('scroll 1 draws that did work: %d of %d (%.0f%%)' % (len(S1), len(P), 100.0 * len(S1) / len(P)))
        stat2('  scroll 1 when drawn (8..9)', lambda d: d[9] - d[8], S1)
        stat2('  its home_maps_rows (8..10)', lambda d: d[10] - d[8] if d[10] >= d[8] else 0, S1)
        stat2('  its row loop (10..12)', lambda d: d[12] - d[10] if d[12] >= d[10] else 0, S1)
        stat2('  of which home_row_map ticks', lambda d: d[11], S1)
