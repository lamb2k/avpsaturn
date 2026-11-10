import json, sys, os, statistics as S
def pct(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(round(p * (len(v) - 1))))] if v else 0
def seg_rows(log, seg):
    L = [r for r in log if r['seg'] == seg][5:]
    if len(L) < 10: return None
    a, b = L[0], L[-1]; n = b['vb'] - a['vb']
    d = lambda k: b[k] - a[k]
    ev = [r['gfx'] for i, r in enumerate(L[1:], 1) if r['done'] != L[i - 1]['done']]
    heavy = [g for g in ev if g > 5000]
    return dict(n=n, swaps=d('shown') / n * 60, draws=d('done') / n * 60, held=d('waits') / n * 100, skip=d('skips') / n * 100, over=d('over'), flips=d('flips') / n * 60,
                med=pct(ev, .5), p95=pct(ev, .95), mx=max(ev) if ev else 0, hv=100 * len(heavy) / max(1, len(ev)), game=S.median([r['game'] for r in L]))
def burst_rows(path, seg):
    if not os.path.exists(path): return None
    B = [b for b in json.load(open(path)) if b['seg'] == seg]
    if not B: return None
    sw = sum(b['c1']['shown'] - b['c0']['shown'] for b in B); vb = sum(b['c1']['vb'] - b['c0']['vb'] for b in B)
    ch = 0; us = 0
    for b in B:
        u = b['shas'][3:]; ch += sum(1 for i in range(1, len(u)) if u[i] != u[i - 1]); us += len(u) - 1
    return dict(swaps=sw / vb * 60, comp=ch / max(1, us) * 60)
def run(tag):
    p = f"runs/{tag}/log.json"
    if not os.path.exists(p): return
    D = json.load(open(p)); L = D['log']; rows = []
    for seg, lab in (('A', 'idle'), ('W', 'walk right'), ('F', 'attack')):
        r = seg_rows(L, seg)
        if r: rows.append((lab, r))
    return D, rows
if __name__ == '__main__':
    print("| run | scene | pictures/s (kernel swaps) | draws/s | held % | skipped % | slave picture ticks med / p95 / max | heavy draws % | game frames/s | overruns |")
    print("| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |")
    for tag in sys.argv[1:]:
        x = run(tag)
        if not x: continue
        D, rows = x
        for lab, r in rows:
            print(f"| {tag} | {lab} | {r['swaps']:.1f} | {r['draws']:.1f} | {r['held']:.1f} | {r['skip']:.1f} | {r['med']} / {r['p95']} / {r['mx']} | {r['hv']:.0f} | {r['flips']:.1f} | {r['over']} |")
        f = D['free']
        if len(f) == 2:
            a, b = f; n = b['vb'] - a['vb']; d = lambda k: b[k] - a[k]
            print(f"| {tag} | free run (random input, {n} vblanks) | {d('shown')/n*60:.1f} | {d('done')/n*60:.1f} | {d('waits')/n*100:.1f} | {d('skips')/n*100:.1f} | | | {d('flips')/n*60:.1f} | {d('over')} |")
        for seg, lab in (('MA', 'burst idle'), ('MW', 'burst walk')):
            br = burst_rows(f"runs/{tag}/bursts.json", seg)
            if br: print(f"| {tag} | {lab} (emulator frames) | {br['swaps']:.1f} swaps; {br['comp']:.1f} frames differ | | | | | | | |")
