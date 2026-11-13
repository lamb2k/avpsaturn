"""usage: busy.py YMIRDIR NAME...  master busy share from a hwprof dump: tasks / irq / idle cycles (CPU 0, 2, 3 of the profiling Ymir), slave cycles, plus TICK MISS PIC SKIP of the window"""
import os, re, sys
d = sys.argv[1]
print('%-18s %6s %6s %6s %6s %6s | %5s %5s %5s %5s | %6s' % ('run', 'vbl', 'tasks%', 'irq%', 'idle%', 'busy%', 'TICK', 'MISS', 'PIC', 'SKIP', 'slave%'))
for name in sys.argv[2:]:
    p = os.path.join(d, 'hwprof_%s.txt' % name)
    if not os.path.exists(p): print(name, 'missing'); continue
    cyc = {}; hp = None
    for l in open(p):
        t = l.split()
        if not t: continue
        if t[0] == 'WINDOW': hp = (int(t[2]), int(t[4]))
        if t[0] == 'CPU': cyc[int(t[1])] = int(t[5])
    tot = cyc[0] + cyc[2] + cyc[3]
    V = []
    for l in open(os.path.join(d, 'runs', name, 'gs.log'), errors='replace'):
        if l.startswith('V '):
            x = dict(re.findall(r'(\w+)=(\S+)', l)); x['vb'] = int(l.split()[1]); V.append(x)
    W = [r for r in V if hp[0] <= r['vb'] <= hp[1]]
    n = W[-1]['vb'] - W[0]['vb']; ticks = sum((int(b['t8']) - int(a['t8'])) % 256 for a, b in zip(W, W[1:]))
    df = lambda k: (int(W[-1][k]) - int(W[0][k])) * 60.0 / n
    print('%-18s %6d %6.1f %6.1f %6.1f %6.1f | %5.1f %5.1f %5.1f %5.1f | %6.1f' % (name, n, 100.0 * cyc[0] / tot, 100.0 * cyc[2] / tot, 100.0 * cyc[3] / tot, 100.0 * (cyc[0] + cyc[2]) / tot, ticks * 60.0 / n, df('ovr'), df('pics'), df('skp'), 100.0 * cyc[1] / (tot)))
