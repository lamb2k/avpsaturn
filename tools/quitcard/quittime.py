"""quittime.py RUN [which]: quit to title = the last PAD A press of the run (routeA: the QUIT TO TITLE choice) to the last CD sector of the front end reload (bursts less than 2.5 s apart); also first frame of the card after the press"""
import sys
sys.path.insert(0, 'E:/AvP/learning/lane-quitcard/ymr')
import an
for run in sys.argv[1:]:
    d = an.load(f'E:/AvP/learning/lane-quitcard/ymr/runs/{run}/trace.log'); ck = an.Clock(d['vb']); rn, _ = an.runs(d)
    presses = [c for c, v in d['pad'] if v == 0x0400]
    c0 = presses[-1]
    after = [r for r in rn if r['c0'] >= c0]
    g = [after[0]]
    for r in after[1:]:
        if ck.t(r['c0']) - ck.t(g[-1]['c1']) < 2.5: g.append(r)
        else: break
    t_end = ck.t(g[-1]['c1']); t0 = ck.t(c0); t1 = ck.t(g[0]['c0'])
    nz = [(ck.t(c) - t0, n) for c, h, n, e, nn in d['fr'] if c >= c0 and ck.t(c) - t0 < 1.0]
    first_card = next((round(t, 3) for t, n in nz if 300 <= n <= 1500), None)
    first_black = next((round(t, 3) for t, n in nz if n < 300), None)
    print(f"{run}: press at {t0:.2f}s, first read {t1 - t0:.2f}s after, last sector {t_end - t0:.2f}s after the press; sectors {sum(r['n'] for r in g)} in {len(g)} bursts; first card frame {first_card}s, first black {first_black}s after the press")
