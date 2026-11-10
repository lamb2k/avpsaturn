import json, sys
def bursts(path):
    B = json.load(open(path)); out = []
    for b in B:
        sh = b['shas']; n = len(sh)
        use = sh[3:]   # first 3 frames after a pause carry no sprites in Yaba
        chg = sum(1 for i in range(1, len(use)) if use[i] != use[i - 1])
        c0, c1 = b['c0'], b['c1']; dv = c1['vb'] - c0['vb']
        out.append(dict(seg=b['seg'], frames=n, vb=dv, composite_changes=chg, usable=len(use) - 1, swaps=c1['shown'] - c0['shown'], draws=c1['done'] - c0['done'], skips=c1['skips'] - c0['skips'],
                        flips=c1['flips'] - c0['flips'], over=c1['over'] - c0['over'], held=c1['waits'] - c0['waits']))
    return out
if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p)
        for o in bursts(p): print('  ', o)
