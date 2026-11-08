"""Contact sheet grouped by state bytes +4..+6: one row per state, up to N distinct poses, with the state's distinct-pose count from kinds.tsv.
usage: bystate.py OUT.png KIND SWAP RUNDIR [RUNDIR...]   ROM-derived output: E:/AvP/learning only."""
import collections, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__)); import render
outp, kind, mode, runs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
by, cnt = collections.defaultdict(list), collections.Counter()
for r in runs:
    for s in render.samples(r, kind):
        by[s[1]].append(s)
    for l in open(r + "/kinds.tsv"):
        p = l.rstrip("\n").split("\t")
        if p[0] == "STATE" and p[1] == kind:
            cnt[p[2]] = max(cnt[p[2]], int(p[3]))
N, C = 8, 112
sts = sorted(by)
W = Image.new("RGB", (110 + N * C, 18 + len(sts) * C), (40, 40, 48)); d = ImageDraw.Draw(W)
d.text((2, 2), f"{kind} by state (+4 +5 +6)  MAME 0.289 avspu capture, sample poses  swap={mode}", fill=(255, 255, 255))
for r, st in enumerate(sts):
    S = by[st]; pick = [S[int(i * len(S) / N)] for i in range(min(N, len(S)))]
    y = 18 + r * C
    d.text((2, y + 40), f"{st}\n{cnt[st]} poses", fill=(220, 220, 140))
    for i, (stg, _, sig, pals) in enumerate(pick):
        im = render.pose(sig, pals, mode)
        f = min(1, (C - 4) / max(im.width, im.height)); im = im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))))
        W.paste(im, (110 + i * C, y + C - 2 - im.height), im)
W.save(outp); print(kind, len(sts), "states")
