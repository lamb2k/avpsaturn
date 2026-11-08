#!/usr/bin/env python
"""Lane avp-megaman: Mega Man's runtime tables for the Saturn kernel, from assets.py's remap.json (ROM-derived: written to the build's
gen directory at build time, never committed).
Writes OUT_INC with:
  MM_MOVES[n] {first step, steps}     in the order of saturn/guests/megaman/megaman.c (MM_MOVE_NAMES)
  MM_STEPS[]  {pose, frames}          the one trimmed set (owner 11-08), a cut pose's frames already on the pose before it
  MM_POSES[]  {first entry, entries}
  MM_ENT[]    {dx, dy, key, flags}    one 16x16 tile; dx/dy from the feet anchor; flags bit0 hflip, bit1 vflip, bits 2-3 row (0 body, 1 Rush, 2 shot)
  MM_PAL[tone][row][16]               CPS colour words (0xF000 | RGB nibbles), tone order capcom, soft, avp, dark
usage: gen_runtime.py REMAP_JSON OUT_INC"""
import json, sys

MOVES = ("idle", "walk", "walkback", "dash", "crouch", "jump", "lp", "hp", "hk", "slide", "buster", "rush", "throw", "hit_etc", "win",
         "shoot", "shot", "hit", "knockdown", "getup", "ko")


def split_hits(P, M):
    """MvC's hit window (hit_etc) holds his idle loop, stagger poses, the fall and the lying pose: split it into hit (stagger),
    knockdown (fall then lying), getup (the fall poses reversed, then standing) and ko (lying, held)."""
    idle = {pid for pid, *_ in M["idle"]}
    def h(p):
        e = [x for x in P[p] if x[5] == 0]
        return max(x[1] for x in e) + 16 - min(x[1] for x in e) if e else 0
    hit, fall, lying = [], [], []
    for pid, d, anc in M["hit_etc"]:
        if pid in idle:
            continue
        if h(pid) <= 48:
            if pid not in [x[0] for x in lying]: lying.append([pid, d, anc])
        elif h(pid) < 80:
            if pid not in [x[0] for x in fall]: fall.append([pid, d, anc])
        elif pid not in [x[0] for x in hit]:
            hit.append([pid, d, anc])
    stand = M["idle"][0] if M["idle"] else None
    M["hit"] = hit or M["idle"][:1]
    M["knockdown"] = fall + [[p, 40, a] for p, _, a in lying[:1]]
    M["getup"] = [[p, 6, a] for p, _, a in reversed(fall)] + ([stand] if stand else [])
    M["ko"] = [[p, 255, a] for p, _, a in lying[:1]] or M["knockdown"]
TONES = ("capcom", "soft", "avp", "dark")


def main():
    A = json.loads(open(sys.argv[1]).read())
    P, M = A["poses"], A["thinned_moves"]
    split_hits(P, M)
    used = sorted({pid for m in MOVES for pid, *_ in M.get(m, [])})
    pidx = {p: i for i, p in enumerate(used)}
    ents, poses = [], []
    for p in used:
        poses.append((len(ents), len(P[p])))
        for dx, dy, i, hf, vf, row in P[p]:
            assert -128 <= dx < 128 and -128 <= dy < 128
            ents.append((dx, dy, A["all_keys"][i], hf | vf << 1 | row << 2))
    steps, moves = [], []
    for m in MOVES:
        sq = M.get(m, [])
        moves.append((len(steps), len(sq)))
        steps += [(pidx[pid], min(d, 255)) for pid, d, _ in sq]
    pal = [[[0xf000 | (r >> 4) << 8 | (g >> 4) << 4 | (b >> 4) for r, g, b in row] for row in A["colours"][t]] for t in TONES]
    c = lambda rows: ",".join("{" + ",".join(map(str, r)) + "}" for r in rows)
    out = [f"#define MM_NMOVES {len(moves)}", f"#define MM_DEFAULT_TONE {TONES.index(A.get('default_colour', 'avp'))}",
           f"static const unsigned short MM_MOVES[{len(moves)}][2] = {{{c(moves)}}};",
           f"static const unsigned char MM_STEPS[{len(steps)}][2] = {{{c(steps)}}};",
           f"static const unsigned short MM_POSES[{len(poses)}][2] = {{{c(poses)}}};",
           f"static const struct {{ signed char dx, dy; unsigned short key; unsigned char flags; }} MM_ENT[{len(ents)}] = {{{c(ents)}}};",
           "static const unsigned short MM_PAL[4][3][16] = {" + ",".join("{" + c(t) + "}" for t in pal) + "};"]
    open(sys.argv[2], "w").write("\n".join(out) + "\n")
    print("megaman runtime: moves", len(moves), "steps", len(steps), "poses", len(poses), "entries", len(ents))


if __name__ == "__main__":
    main()
