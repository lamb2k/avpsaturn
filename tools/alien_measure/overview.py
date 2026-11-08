"""Overview: one row per kind, first N distinct poses spread over its samples. usage: overview.py RUNDIR OUT.png PREFIX..."""
import sys
from PIL import Image, ImageDraw
sys.path.insert(0, __import__("os").path.dirname(__file__)); import render
run, outp, pre = sys.argv[1], sys.argv[2], sys.argv[3:]
kinds = sorted({l.split("\t")[1] for l in open(run + "/samples.tsv") if any(l.split("\t")[1].startswith(p) for p in pre)})
N, C = 10, 96
W = Image.new("RGB", (60 + N * C, len(kinds) * C), (40, 40, 48)); d = ImageDraw.Draw(W)
for r, k in enumerate(kinds):
    S = render.samples(run, k)
    pick = [S[int(i * len(S) / N)] for i in range(min(N, len(S)))]
    d.text((2, r * C + 40), k, fill=(255, 255, 255))
    for i, (stg, st, sig, pals) in enumerate(pick):
        im = render.pose(sig, pals, "none")
        f = min(1, (C - 4) / max(im.width, im.height)); im = im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))))
        W.paste(im, (60 + i * C, r * C + C - im.height), im)
W.save(outp); print(len(kinds))
