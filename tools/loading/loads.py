"""loads.py TRACE [ISO_TRACK1] : EMULATED CD timeline grouped into loads (bursts of reads with < 1.0 s between them). Names the file from the ISO directory and, for STORE.BIN, the round file from its run table."""
import sys, json, bisect
sys.path.insert(0, 'E:/AvP/learning/lane-loading/ymir')
import an
trace = sys.argv[1]
files = sorted((int(l.split()[0]), int(l.split()[2]), l.split()[-1]) for l in open('E:/AvP/learning/lane-loading/ls_P5.txt'))
store0 = [f for f in files if f[2] == 'STORE.BIN'][0][0]
runs = json.load(open('E:/AvP/learning/lane-loading/store_runs.json'))
rmap = {}
for r, rr in runs.items():
    for a, n in rr: rmap[store0 + a] = (int(r), a, n)
def name(lba):
    for a, n, nm in files:
        if a <= lba < a + n: return nm
    return '?'
def rnd(lba):
    best = None
    for a, (r, off, n) in rmap.items():
        if a <= lba < a + n: return r
    return None
d = an.load(trace); rn, ck = an.runs(d)
groups = []
for r in rn:
    if groups and ck.t(r['c0']) - ck.t(groups[-1][-1]['c1']) < 1.0: groups[-1].append(r)
    else: groups.append([r])
seek_t = [ck.t(c) for c, _, _ in d['seek']]
pad = [(ck.t(c), m) for c, m in d['pad'] if m]
for g in groups:
    t0, t1 = ck.t(g[0]['c0']), ck.t(g[-1]['c1'])
    n = sum(r['n'] for r in g)
    ns = sum(1 for t in seek_t if t0 - 0.3 <= t <= t1)
    nm = {}
    for r in g:
        lba = r['first'] - 150; k = name(lba)
        if k == 'STORE.BIN': k = 'R%03s' % (rnd(lba) if rnd(lba) is not None else '?')
        nm[k] = nm.get(k, 0) + r['n']
    lastpad = max([t for t, m in pad if t <= t0 + 0.0] or [0])
    print(f"t={t0:8.2f}..{t1:8.2f} dur={t1-t0:6.2f}s sectors={n:5d} seeks~{ns:2d} runs={len(g):2d}  {nm}  ({n/max(t1-t0,1e-3):5.1f} sect/s)  lastpad@{lastpad:.2f}")
