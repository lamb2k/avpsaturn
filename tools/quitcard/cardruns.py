"""cardruns.py RUN...  : runs of NOW LOADING card frames (FR nz 300..1500, same hash) in trace.log, with start time, length, and the CD reads (sector bursts) inside; plus quit-to-title time (last PAD A of a pause quit to the end of the front end read burst)"""
import sys
sys.path.insert(0, 'E:/AvP/learning/lane-quitcard/ymr')
import an
for run in sys.argv[1:]:
    d = an.load(f'E:/AvP/learning/lane-quitcard/ymr/runs/{run}/trace.log'); ck = an.Clock(d['vb'])
    rn, _ = an.runs(d)
    out = []; cur = None
    for c, h, nz, eq, n in d['fr']:
        card = 300 <= nz <= 1500
        if card and cur and cur['h'] == h: cur['c1'] = c; cur['n'] += 1
        elif card: cur = dict(h=h, c0=c, c1=c, n=1); out.append(cur)
        else: cur = None
    print(run)
    for o in out:
        if o['n'] < 8: continue
        sec = [r for r in rn if o['c0'] - 2e6 <= r['c0'] <= o['c1'] + 2e6]
        print(f"  card from {ck.t(o['c0']):7.2f}s (frame {ck.frame(o['c0'])}) for {ck.t(o['c1']) - ck.t(o['c0']):5.2f}s, {o['n']} samples, CD bursts inside: {len(sec)}, sectors {sum(r['n'] for r in sec)}")
