#!/usr/bin/env python
"""usage: an_pic.py GS.LOG [V0 V1] [--windows]   (lane perf-pic)
Reads the profiling Ymir's gs.log (one 'V' line per vblank, one 'D' line per slave draw: vblank, FRT ticks of the draw) and prints, over the vblank window V0..V1
(default: the whole log after the first 300 vblanks of the stage), per 60 vblanks: TICK (game ticks), MISS (overruns), DONE (60 - MISS), PIC (pictures swapped), SKIP (gfx skips),
and the distribution of the slave's draw length in FRT ticks (a field is about 3,500 ticks): mean, median, p90, max and the share of draws over one field."""
import re, sys, statistics
def load(path):
    V, D = [], []
    for l in open(path, errors='replace'):
        if l.startswith('V '):
            d = dict(re.findall(r'(\w+)=(\S+)', l)); d['vb'] = int(l.split()[1]); V.append(d)
        elif l.startswith('D '):
            t = l.split(); D.append((int(t[1]), int(t[2])))
    return V, D
def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    V, D = load(a[0])
    if len(a) >= 3: v0, v1 = int(a[1]), int(a[2])
    else:
        st = [r['vb'] for r in V if r['st'] not in ('00',)]
        v0 = (st[0] + 300) if st else V[0]['vb']; v1 = V[-1]['vb']
    W = [r for r in V if v0 <= r['vb'] <= v1]
    if len(W) < 61: print('window too short', len(W)); return
    n = W[-1]['vb'] - W[0]['vb']
    def df(k): return int(W[-1][k]) - int(W[0][k])
    # t8 wraps at 256: use tw (tick writes, a counter)
    tick = df('tw') * 60.0 / n; miss = df('ovr') * 60.0 / n; pic = df('pics') * 60.0 / n; skp = df('skp') * 60.0 / n
    print('window vb %d..%d (%d vblanks) st=%s' % (W[0]['vb'], W[-1]['vb'], n, W[-1]['st']))
    print('TICK %.1f  MISS %.1f  DONE %.1f  PIC %.1f  SKIP %.1f   (per 60 vblanks)' % (tick, miss, 60 - miss, pic, skp))
    dd = [t for (v, t) in D if v0 <= v <= v1]
    if dd:
        dd2 = sorted(dd); p = lambda q: dd2[min(len(dd2) - 1, int(q * len(dd2)))]
        print('slave draws %d: mean %.0f median %d p90 %d p99 %d max %d FRT ticks; over a field (3500): %.1f%%' % (len(dd), statistics.mean(dd), p(.5), p(.9), p(.99), dd2[-1], 100.0 * sum(1 for t in dd if t > 3500) / len(dd)))
    if '--windows' in sys.argv:
        for i in range(0, len(W) - 60, 60):
            x, y = W[i], W[i + 60]
            print('  vb %d: TICK %d MISS %d PIC %d SKIP %d' % (x['vb'], int(y['tw']) - int(x['tw']), int(y['ovr']) - int(x['ovr']), int(y['pics']) - int(x['pics']), int(y['skp']) - int(x['skp'])))
main()
