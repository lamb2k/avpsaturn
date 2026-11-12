import sys, re, statistics as S
def load(p):
    R = {}
    for l in open(p):
        if not l.startswith('V '): continue
        d = {k: int(v, 16) if k == 'st' else int(v) for k, v in re.findall(r'(\w+)=(\S+)', l)}
        d['vb'] = int(l.split()[1]); R[d['vb']] = d
    return [R[k] for k in sorted(R)]
print("run   master-factor  fight-vblanks | ticks/60 (whole fight) worst-60vb-window | MISS/60 median max (DONE median min) | PIC/60 median min | SKIP/60 median | gt(FRT ticks, field=3503) median p90 max")
for name, f in zip(sys.argv[1::2], sys.argv[2::2]):
    rows = load(f'E:/AvP/learning/lane-perf/ymir_gs/runs/{name}/gs.log')
    g = [r for r in rows if r['st'] == 2]
    # fight region: from 300 vblanks after the stage word to the end
    g = g[300:]
    if len(g) < 200: print(name, 'too short', len(g)); continue
    dv = g[-1]['vb'] - g[0]['vb']; tk = g[-1]['tw'] - g[0]['tw']
    W = 60; ws = []
    for a in range(0, len(g) - W, 30):
        s, e = g[a], g[a + W]
        if e['vb'] - s['vb'] != W: continue
        ws.append(((e['tw'] - s['tw']), e['ovr'] - s['ovr'], (e['pics'] - s['pics']), e['skp'] - s['skp'], max(r['ff'] for r in g[a:a + W])))
    ws = [w for w in ws if w[4] == 0]
    # non-overlapping ff-free windows for the aggregate
    nz = ws[::2]
    agg = 60 * sum(w[0] for w in nz) / (60 * len(nz))
    gts = sorted(r['gt'] for r in g)
    print(f"{name:5s} {f:>5s} {dv:6d} | {agg:6.2f} {min(w[0] for w in ws):3d} | {S.median(w[1] for w in ws):5.1f} {max(w[1] for w in ws):3d} ({60-S.median(w[1] for w in ws):4.1f} {60-max(w[1] for w in ws):3d}) | {S.median(w[2] for w in ws):5.1f} {min(w[2] for w in ws):3d} | {S.median(w[3] for w in ws):5.1f} | {S.median(gts):6.0f} {gts[int(.9*len(gts))]:6d} {gts[-1]:6d}")
