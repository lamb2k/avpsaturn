import sys, csv, statistics as S, collections
rows = list(csv.DictReader(open(sys.argv[1]), delimiter='\t'))
for r in rows:
    for k in r: r[k] = float(r[k]) if '.' in r[k] else int(r[k], 16) if k == 'stage' else int(r[k])
# unwrap bytes
def unwrap(key):
    out, last, acc = [], None, 0
    for r in rows:
        v = r[key]
        if last is not None: acc += (v - last) & 255
        last = v; out.append(acc)
    return out
vb, tk = unwrap('vb'), unwrap('tk')
for i, r in enumerate(rows): r['vbu'], r['tku'] = vb[i], tk[i]
W = int(sys.argv[2]) if len(sys.argv) > 2 else 60
print("window", W)
# per stage summary (gameplay frames only: stage != 0)
by = collections.defaultdict(list)
for i, r in enumerate(rows):
    if r['stage']: by[r['stage']].append(i)
print("stage frames  vb_adv tick_adv  ticks/60vb  walks_done/60 | frames0tick frames2+tick ff81b9frames | enemies avg/max sprites avg/max busy_ms avg/p99/max")
for st, idx in sorted(by.items()):
    if len(idx) < 120: continue
    a, b = idx[0], idx[-1]
    dvb = rows[b]['vbu'] - rows[a]['vbu']; dtk = rows[b]['tku'] - rows[a]['tku']
    ff = sum(1 for i in idx if rows[i]['ff81b9'])
    z = sum(1 for i in idx if rows[i]['t808a'] == 0); m = sum(1 for i in idx if rows[i]['t808a'] >= 2)
    nff = [i for i in idx if not rows[i]['ff81b9']]
    walks = sum(rows[i]['i11ec'] for i in idx)
    en = [rows[i]['enemies'] for i in idx]; sp = [rows[i]['sprites'] for i in idx]
    bz = sorted(rows[i]['busy_ms'] for i in idx)
    print(f"{st:02x} {len(idx):6d} {dvb:6d} {dtk:6d}  {60*dtk/max(dvb,1):6.2f}  {60*walks/len(idx):7.1f} | {z:5d} {m:5d} {ff:5d} | {S.mean(en):4.1f}/{max(en)} {S.mean(sp):5.1f}/{max(sp)} {S.mean(bz):5.2f}/{bz[int(.99*len(bz))]:5.2f}/{bz[-1]:5.2f}")
# windows: worst ticks/60vb, with enemies
print("\nWorst windows (no fast-forward frames), by ticks per 60 vblanks, gameplay stage != 0")
wins = []
for a in range(0, len(rows) - W, W):
    seg = rows[a:a + W]
    if any(r['stage'] == 0 or r['ff81b9'] for r in seg): continue
    dvb = seg[-1]['vbu'] - seg[0]['vbu']; dtk = seg[-1]['tku'] - seg[0]['tku']
    if dvb < W - 2: continue
    wins.append((60 * dtk / dvb, a, seg[0]['stage'], S.mean(r['enemies'] for r in seg), max(r['enemies'] for r in seg), S.mean(r['sprites'] for r in seg), sum(r['busy_ms'] for r in seg) / W, sum(r['i11ec'] for r in seg) / W, sum(r['ovr'] for r in seg), sum(1 for r in seg if r['t808a'] == 0)))
wins.sort()
print("ticks/60  frame stage en_avg en_max sprites busy_ms/frame walks/frame overrun_events zero_tick_frames")
for w in wins[:15]: print(f"{w[0]:6.1f} {w[1]:6d} {w[2]:02x} {w[3]:5.1f} {w[4]:3d} {w[5]:5.1f} {w[6]:6.2f} {w[7]:6.1f} {w[8]:4d} {w[9]:4d}")
print("n windows", len(wins), "min", wins[0][0], "median", S.median(w[0] for w in wins), "max", wins[-1][0])
# crowded windows: enemies avg>=5
cw = [w for w in wins if w[3] >= 5]
print("crowded (avg enemies >=5): n", len(cw), "ticks/60 min/median/max", (min(w[0] for w in cw), S.median(w[0] for w in cw), max(w[0] for w in cw)) if cw else None)
