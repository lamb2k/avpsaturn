"""Parse trace.log (loading lane Ymir): timeline in emulated seconds (EMULATED). usage: an.py [trace.log] [--iso ls.txt] [--frames]"""
import sys, re, bisect, collections
FRAME_S = 1.0 / 59.8261   # NTSC, 262.5 lines x 455... as the Ymir run shows: 478660 master cycles per frame at 28.636 MHz (16.715 ms)
def load(path):
    vb, fr, swap, pad, seek, sect, bful = [], [], [], [], [], [], []
    for l in open(path, errors='replace'):
        p = l.split()
        if len(p) < 2: continue
        c = int(p[0]); k = p[1]
        if k == 'VB': vb.append(c)
        elif k == 'FR': fr.append((c, p[2], int(p[3][3:]), int(p[4][3:]), int(p[5][2:])))
        elif k == 'SWAP': swap.append(c)
        elif k == 'PAD': pad.append((c, int(p[2], 16)))
        elif k == 'SEEK': seek.append((c, int(p[2][3:], 16), int(p[3][5:], 16)))
        elif k == 'SECT': sect.append((c, int(p[2], 16)))
        elif k == 'BUFFULL': bful.append((c, int(p[2], 16)))
    return dict(vb=vb, fr=fr, swap=swap, pad=pad, seek=seek, sect=sect, bful=bful)
class Clock:
    """count -> seconds, piecewise linear between vblank-in stamps (frame k is at k * FRAME_S)"""
    def __init__(self, vb): self.vb = vb
    def t(self, c):
        i = bisect.bisect_right(self.vb, c) - 1
        if i < 0: return 0.0
        if i + 1 >= len(self.vb): return (i + (c - self.vb[i]) / 478660.0) * FRAME_S
        return (i + (c - self.vb[i]) / (self.vb[i + 1] - self.vb[i])) * FRAME_S
    def frame(self, c): return bisect.bisect_right(self.vb, c) - 1
def runs(d):
    ck = Clock(d['vb'])
    out = []   # CD bursts of consecutive sectors
    cur = None
    for c, fad in d['sect']:
        if cur and fad == cur['last'] + 1 and ck.t(c) - ck.t(cur['c1']) < 0.2:
            cur['last'] = fad; cur['n'] += 1; cur['c1'] = c
        else:
            if cur: out.append(cur)
            cur = dict(c0=c, c1=c, first=fad, last=fad, n=1)
    if cur: out.append(cur)
    return out, ck
def frame_states(d):
    """per frame: 'B' blank (>=99.5% pixels equal to the first one and dark), 'S' same hash as the frame before, 'L' live"""
    st = []; prev = None
    for c, h, nz, eq, n in d['fr']:
        if n and eq >= 0.97 * n and nz <= 0.03 * n: s = 'B'
        elif n and eq >= 0.97 * n: s = 'C'     # one colour, not black
        elif h == prev: s = 'S'
        else: s = 'L'
        prev = h; st.append((c, s))
    return st
if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'E:/AvP/learning/lane-loading/ymir/trace.log'
    d = load(path); rn, ck = runs(d)
    print('frames', len(d['vb']), 'emulated seconds', round(ck.t(d['vb'][-1]), 1), 'sectors', len(d['sect']), 'seeks', len(d['seek']))
    for r in rn:
        print(f"CD t={ck.t(r['c0']):8.2f}..{ck.t(r['c1']):8.2f}  LBA {r['first']-150:7d}..{r['last']-150:7d}  n={r['n']:5d}  rate={r['n']/max(ck.t(r['c1'])-ck.t(r['c0']),1e-3):6.1f}/s")

def segments(d, ck, minlen=0.0):
    st = frame_states(d); segs = []
    for c, s in st:
        t = ck.t(c)
        if segs and segs[-1][0] == s: segs[-1][2] = t; segs[-1][3] += 1
        else: segs.append([s, t, t, 1])
    return [x for x in segs if (x[2] - x[1]) >= minlen]
