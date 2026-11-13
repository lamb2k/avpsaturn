#!/usr/bin/env python
"""usage: an_runs.py YMIRDIR NAME [NAME ...]   (lane perf-pic)  One line per profiled run: the window of its hwprof dump (reset to dump), stage word, TICK, MISS, PIC, SKIP per 60 vblanks, and the slave's draw length (FRT ticks, a field is about 3,500)."""
import os, re, sys, statistics
d = sys.argv[1]
print('%-22s %-9s %-4s %5s %5s %5s %5s | %6s %6s %6s %6s %6s' % ('run', 'window', 'st', 'TICK', 'MISS', 'PIC', 'SKIP', 'dmean', 'dmed', 'dp99', 'dmax', 'over%'))
for name in sys.argv[2:]:
    try:
        hp = open(os.path.join(d, 'hwprof_%s.txt' % name)).readline().split()
        v0, v1 = int(hp[2]), int(hp[4])
    except Exception:
        print('%-22s no hwprof dump' % name); continue
    V, D = [], []
    for l in open(os.path.join(d, 'runs', name, 'gs.log'), errors='replace'):
        if l.startswith('V '):
            x = dict(re.findall(r'(\w+)=(\S+)', l)); x['vb'] = int(l.split()[1]); V.append(x)
        elif l.startswith('D '):
            t = l.split(); D.append((int(t[1]), int(t[2])))
    W = [r for r in V if v0 <= r['vb'] <= v1]
    if len(W) < 61: print('%-22s window too short' % name); continue
    n = W[-1]['vb'] - W[0]['vb']; df = lambda k: (int(W[-1][k]) - int(W[0][k])) * 60.0 / n
    dd = sorted(t for (v, t) in D if v0 <= v <= v1) or [0]
    print('%-22s %-9s %-4s %5.1f %5.1f %5.1f %5.1f | %6.0f %6d %6d %6d %6.1f' % (name, '%d-%d' % (v0, v1), W[-1]['st'], df('tw'), df('ovr'), df('pics'), df('skp'), statistics.mean(dd), dd[len(dd) // 2], dd[int(.99 * len(dd))], dd[-1], 100.0 * sum(1 for t in dd if t > 3500) / len(dd)))
