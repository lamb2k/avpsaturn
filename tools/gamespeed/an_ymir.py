import sys, re, statistics as S
W = int(sys.argv[2]) if len(sys.argv) > 2 else 60
rows = []
for l in open(sys.argv[1]):
    if not l.startswith('V '): continue
    d = {k: int(v, 16) if k == 'st' else int(v) for k, v in re.findall(r'(\w+)=(\S+)', l)}
    d['vb'] = int(l.split()[1]); rows.append(d)
# drop duplicated vb
seen = set(); R = []
for r in rows:
    if r['vb'] in seen: continue
    seen.add(r['vb']); R.append(r)
rows = R
print('vblank lines', len(rows), 'vb', rows[0]['vb'], '->', rows[-1]['vb'])
gap = sum(1 for a, b in zip(rows, rows[1:]) if b['vb'] != a['vb'] + 1)
print('gaps in the vblank sequence:', gap)
# gameplay frames: st != 0
g = [r for r in rows if r['st'] != 0]
print('gameplay (stage word nonzero) lines', len(g))
print('window', W, ' per-window: ticks/60vb  walks_completed/60vb(idle)  MISS(ovr)  SKIP  PIC/60  cmds(max c0,c1)  gt(frt at walk done)  ff')
out = []
for a in range(0, len(g) - W, W):
    s, e = g[a], g[a + W]
    dv = e['vb'] - s['vb']
    if dv != W: continue
    tw = e['tw'] - s['tw']; v8 = (e['t8'] - s['t8']) & 255
    out.append(dict(vb=s['vb'], st=s['st'], ticks=tw * 60 / dv, idle=(e['idle'] - s['idle']) * 60 / dv, miss=e['ovr'] - s['ovr'], skip=e['skp'] - s['skp'], pic=(e['pics'] - s['pics']) * 60 / dv,
                    cmds=max(max(r['c0'], r['c1']) for r in g[a:a + W]), gt=S.mean(r['gt'] for r in g[a:a + W]), ff=max(r['ff'] for r in g[a:a + W]), cut=(e['tkskip'] - s['tkskip']), tkrun=(e['tkrun'] - s['tkrun'])))
for o in out: print("vb %6d st %02x ticks/60 %6.2f walks/60 %7.1f MISS %3d (DONE %2d) SKIP %3d PIC %5.1f cmds %4d gt %6.0f ff %d CUT %d" % (o['vb'], o['st'], o['ticks'], o['idle'], o['miss'], 60 - o['miss'], o['skip'], o['pic'], o['cmds'], o['gt'], o['ff'], o['cut']))
if out:
    print('ticks/60: min %.2f median %.2f max %.2f' % (min(o['ticks'] for o in out), S.median(o['ticks'] for o in out), max(o['ticks'] for o in out)))
    print('PIC: min %.1f median %.1f max %.1f ; MISS min %d median %.1f max %d' % (min(o['pic'] for o in out), S.median(o['pic'] for o in out), max(o['pic'] for o in out), min(o['miss'] for o in out), S.median(o['miss'] for o in out), max(o['miss'] for o in out)))
