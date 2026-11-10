#!/usr/bin/env python
"""Healing factor check on a host-runner trace (tools/lift_runner/build_native_host.py --wvf 1 ... -DSAT_WV_HEAL, run with WVFTRACE=file WV_SEL=1).
usage: wvf_heal_check.py TRACE [--delay 180 --step 30 --amt 1] [--csv out.csv]
Trace lines (wv_features.c wvf_log): "<vblank> t <player> <state a<<16|b<<8|c> <health<<8 | timer>" (one per Wolverine player update; health is signed 16 bit shifted left by 8).
Checks, per player:
  - heal events (the timer drops to DELAY-STEP from DELAY-1, health +AMT): the state of every one must be 02 00 xx (stand, walk, jump, attacks, Berserker, special)
  - the timer is 0 on every update whose state is a hit (02 02), a grab (02 04), getting up (02 08), dying/continue (04, 08) or whose health is outside 0..100
  - the timer restarts (0) on the update after any health drop
Prints the counts and the health-over-time (vblank, health) at every change for the CSV."""
import argparse, collections


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace"); ap.add_argument("--delay", type=int, default=180); ap.add_argument("--step", type=int, default=30); ap.add_argument("--amt", type=int, default=1)
    ap.add_argument("--csv")
    a = ap.parse_args()
    prev = {}; heals = collections.Counter(); heal_states = collections.Counter(); viol = []; drops = 0; n = 0; firsts = {}
    rows = []
    for line in open(a.trace):
        p = line.split()
        if len(p) != 5 or p[1] != "t":
            continue
        v, pl, st, hb = int(p[0]), int(p[2]), int(p[3]), int(p[4])
        hp, t = hb >> 8, hb & 255
        n += 1
        sa, sb = st >> 16, (st >> 8) & 255
        ok_state = sa == 2 and sb == 0
        q = prev.get(pl)
        healed = False
        if q:
            qv, qhp, qt = q
            if t == a.delay - a.step and qt == a.delay - 1:
                healed = True
                heals[pl] += 1; heal_states[(pl, "%06x" % st)] += 1
                firsts.setdefault(pl, v)
                if not ok_state or hp <= qhp:   # hp above qhp + amt: a pick-up in the same update
                    viol.append((v, pl, "heal in state %06x hp %d->%d" % (st, qhp, hp)))
            if hp < qhp:
                drops += 1
                if t != 0:
                    viol.append((v, pl, "timer %d after a drop %d->%d" % (t, qhp, hp)))
        if (not ok_state or hp < 0 or hp >= 101) and t != 0 and not (healed and ok_state):   # the heal that reaches full health leaves the timer set until the next update
            viol.append((v, pl, "timer %d in state %06x hp %d" % (t, st, hp)))
        if not q or q[1] != hp:
            rows.append((v, pl, hp, st))
        prev[pl] = (v, hp, t)
    print("updates", n, "heal events", dict(heals), "health drops seen", drops, "violations", len(viol))
    for k, c in sorted(heal_states.items()):
        print("  heal in state", k[1], "player", k[0], "x", c)
    for x in viol[:20]:
        print("  VIOLATION", x)
    if a.csv:
        with open(a.csv, "w") as f:
            f.write("vblank,player,health,state\n")
            for r in rows:
                f.write("%d,%d,%d,%06x\n" % r)
    return 1 if viol else 0


if __name__ == "__main__":
    raise SystemExit(main())
