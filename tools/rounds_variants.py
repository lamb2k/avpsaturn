#!/usr/bin/env python
"""Lane packs: per-character variants of the stage files. A variant holds the same candidates as the one-for-all file, but what will not fit is dropped with other characters' material first.
SPEC json: {"chars": {"1": {"routes": [census dirs], "walks": [walk dirs]}, "2": ..., "4": ..., "8": ...}, "pair": {"routes": [...], "walks": [...]}, "pair_exact": 3}. Keys are bits of the game's character mask, ff81cc. pair data is a two-player run; pair_exact is the pair it measured.
usage: rounds_variants.py rank WORK SPEC   merges each variant's key ranks into WORK/key_rank.json (after tools/rounds_rank.py). rounds_config.py imports this for sound. ROM-derived output: E:/AvP/learning only."""
import collections, glob, json, pathlib, sys
SOLO = (1, 2, 4, 8)
MASKS = (*SOLO, 3, 5, 9, 6, 10, 12)   # variant index - 1. Three characters use the one-for-all file, variant 0.
NONE = [{}, {}]


def _route(d):
    """stage -> [key -> sections that drew it, command -> enqueues]"""
    r = collections.defaultdict(lambda: [collections.Counter(), collections.Counter()])
    for f in glob.glob(d + "/sections/*.tiles.txt"):
        s = int(pathlib.Path(f).name[:4], 16) & 0xff
        for l in open(f):
            a, k = l.split()
            if a == "0":
                r[s][0][int(k, 16)] += 1
    for f in glob.glob(d + "/sections/*.sounds.txt"):
        s = int(pathlib.Path(f).name[:4], 16) & 0xff
        for l in open(f):
            a, n = l.split()
            r[s][1][int(a, 16) & 0xffff] += int(n)
    return r


def _walk(d):
    """stage -> [keys, commands]; stage 0x100: seen on KO and continue, any stage."""
    r = collections.defaultdict(lambda: [set(), set()])
    for f in glob.glob(d + "/s[0-9a-f][0-9a-f].txt") + glob.glob(d + "/k00.txt"):
        n = pathlib.Path(f).stem
        s = 0x100 if n[0] == "k" else int(n[1:], 16)
        for l in open(f):
            p = l.split()
            if p[0] == "0":
                r[s][0].add(int(p[1], 16))
            elif p[0] == "m":
                r[s][1].add(int(p[1], 16) & 0xffff)
    return r


class Data:
    def __init__(self, spec):
        S = json.load(open(spec))
        self.pair_exact = S.get("pair_exact", 0)
        self.route, self.walk = {}, {}
        for who, c in [*((int(k), v) for k, v in S["chars"].items()), ("pair", S["pair"])]:
            self.route[who] = [_route(d) for d in c["routes"]]
            self.walk[who] = [_walk(d) for d in c["walks"]]
        # A key only ever seen with one character in the whole game is that character's own.
        seen = {c: set() for c in SOLO}
        for c in SOLO:
            for r in self.route[c]:
                for v in r.values():
                    seen[c] |= set(v[0])
            for w in self.walk[c]:
                for v in w.values():
                    seen[c] |= v[0]
        self.own = {c: seen[c] - set().union(*(seen[o] for o in SOLO if o != c)) for c in SOLO}

    def _who(self, mask):
        return [c for c in SOLO if mask & c]

    def key_rank(self, stage, mask, cands):
        """Key -> score, higher kept. Own route, own walk, own KO, pair run, others' shared material, last what belongs only to a character not playing."""
        me = self._who(mask)
        n = collections.Counter()
        for c in me:
            for r in self.route[c]:
                for k, x in r.get(stage, NONE)[0].items():
                    n[k] += 1000000 * x
            for w in self.walk[c]:
                for k in w.get(stage, NONE)[0]:
                    n[k] += 100000
                for k in w.get(0x100, NONE)[0]:
                    n[k] += 50000
        if len(me) > 1:   # what the second player adds; for a pair not measured, a stand-in below the two characters' own material
            for r in self.route["pair"]:
                for k, x in r.get(stage, NONE)[0].items():
                    n[k] += (1000000 if mask == self.pair_exact else 10000) * x
            for w in self.walk["pair"]:
                for k in w.get(stage, NONE)[0]:
                    n[k] += 100000 if mask == self.pair_exact else 5000
        for c in SOLO:
            if c in me:
                continue
            for r in self.route[c]:
                for k in r.get(stage, NONE)[0]:
                    if k not in self.own[c]:
                        n[k] += 1000
            for w in self.walk[c]:
                for k in w.get(stage, NONE)[0]:
                    if k not in self.own[c]:
                        n[k] += 100
        return {k: n[k] for k in cands}

    def sound_score(self, stage, mask, cands, any_sound):
        me = self._who(mask)
        n = collections.Counter()
        for c in SOLO:
            mine = c in me
            for r in self.route[c]:
                for k, x in r.get(stage, NONE)[1].items():
                    n[k] += x * (100000 if mine else 1)
            if mine:
                for w in self.walk[c]:
                    for k in w.get(stage, NONE)[1]:
                        n[k] += 5000
                    for k in w.get(0x100, NONE)[1]:
                        n[k] += 2000
        if len(me) > 1:
            for r in self.route["pair"]:
                for k, x in r.get(stage, NONE)[1].items():
                    n[k] += x * (100000 if mask == self.pair_exact else 100)
            for w in self.walk["pair"]:
                for k in w.get(stage, NONE)[1]:
                    n[k] += 5000 if mask == self.pair_exact else 300
        return {c: n[c] + (500 if c in any_sound else 0) for c in cands}


if __name__ == "__main__" and sys.argv[1] == "rank":
    W = pathlib.Path(sys.argv[2])
    D = Data(sys.argv[3])
    R = json.loads((W / "rounds.json").read_text())
    rk = json.loads((W / "key_rank.json").read_text())
    for f in R["files"]:
        if "mask" in f:
            rk[f["name"]] = {str(k): v for k, v in D.key_rank(f["stages"][0], f["mask"], f["keys"][0]).items()}
    (W / "key_rank.json").write_text(json.dumps(rk))
    print("variant ranks", sum("mask" in f for f in R["files"]))
