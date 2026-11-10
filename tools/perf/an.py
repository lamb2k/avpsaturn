import json, sys, statistics as S
def pct(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(round(p * (len(v) - 1))))] if v else 0
def seg_stats(L, label):
    L = L[5:]   # drop the first steps after a pause/load (stepped-frame artefact)
    if len(L) < 10: return None
    a, b = L[0], L[-1]; n = b['vb'] - a['vb']
    if n <= 0: return None
    d = lambda k: b[k] - a[k]
    # draws (slave pictures finished): done increments; ticks = gfx at that row
    ev = [r['gfx'] for i, r in enumerate(L[1:], 1) if r['done'] != L[i - 1]['done']]
    comp = sum(1 for i in range(1, len(L)) if L[i]['h'] != L[i - 1]['h'])
    med = int(S.median(ev)) if ev else 0
    return dict(seg=label, vb=n, swaps=round(d('shown') / n * 60, 1), draws=round(d('done') / n * 60, 1), held=round(d('waits') / n * 100, 1), skip=round(d('skips') / n * 100, 1),
                gameflips=round(d('flips') / n * 60, 1), overruns=d('over'), composite_changes=round(comp / (len(L) - 1) * 60, 1),
                gfx_med=med, gfx_p95=pct(ev, .95), gfx_max=max(ev) if ev else 0, heavy=sum(1 for g in ev if g > 5000), ndraw=len(ev),
                game_med=int(S.median([r['game'] for r in L])), snap_med=int(S.median([r['snap'] for r in L if r['snap'] > 100] or [0])))
def run(path):
    D = json.load(open(path)); log = D['log']; out = []
    for seg, lab in (('A', 'A idle'), ('W', 'W walk right'), ('F', 'F attack on the spot')):
        L = [r for r in log if r['seg'] == seg]
        s = seg_stats(L, lab)
        if s: out.append(s)
    f = D['free']
    if len(f) == 2:
        a, b = f; n = b['vb'] - a['vb']; d = lambda k: b[k] - a[k]
        out.append(dict(seg='C free', vb=n, swaps=round(d('shown') / n * 60, 1), draws=round(d('done') / n * 60, 1), held=round(d('waits') / n * 100, 1), skip=round(d('skips') / n * 100, 1),
                        gameflips=round(d('flips') / n * 60, 1), overruns=d('over'), wall=round(b['wall'] - a['wall'], 1)))
    return D, out
if __name__ == '__main__':
    for p in sys.argv[1:]:
        D, out = run(p); print(p, D['cache'], D['stage'])
        for o in out: print('  ', o)
