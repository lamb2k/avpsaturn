#!/usr/bin/env python3
"""Exhaustive interleaving test of the display-register record protocol in saturn/gfx/sat_gfx.c (lat_publish by the slave, lat_apply by the master). MODELLED: the two routines are
transcribed step by step (each uncached load or store is one step) and the whole reachable state space of "slave publishes up to three records, master applies once" is searched; no C is
run (there is no host gcc on this PC). Claim checked: when the master's apply ends, the registers on the chip are a complete published record (or untouched).
The previous routine (fix7 as staged: write each register while reading it, verify afterwards, up to four tries) is modelled too and must FAIL the same check, so the test is known to be able to see a mixed record.
usage: python tests/lat_protocol_test.py"""
import sys

N = 3                                                    # registers modelled (the code has 0x88; the protocol does not depend on the count)
RECORDS = [(10, 11, 12), (20, 21, 22), (30, 31, 32)]     # three pictures' complete states
INIT_CHIP = (None, None, None)


def slave_program():
    prog = []
    for r in range(len(RECORDS)):
        prog.append(("q", r)); prog.append(("odd", r))
        for i in range(N):
            prog.append(("pub", r, i)); prog.append(("pv", r, i))
        prog.append(("even", r))
    return prog


SLAVE = slave_program()


def slave_step(st):
    """st = (si, sq, seq, pub, pv); returns the new tuple."""
    si, sq, seq, pub, pv = st
    op = SLAVE[si]
    if op[0] == "q": sq = seq
    elif op[0] == "odd": seq = sq + 1
    elif op[0] == "pub": pub = pub[:op[2]] + (RECORDS[op[1]][op[2]],) + pub[op[2] + 1:]
    elif op[0] == "pv": pv = pv[:op[2]] + (1,) + pv[op[2] + 1:]
    elif op[0] == "even": seq = sq + 2
    return (si + 1, sq, seq, pub, pv)


def master_step(m, mem, variant):
    """m = (stage, t, i, q, snap, sv, chip); mem = (seq, pub, pv). Returns the new m."""
    stage, t, i, q, snap, sv, chip = m
    seq, pub, pv = mem
    if variant == "new":
        if stage == "start":
            if t >= 4: return ("done", t, i, q, snap, sv, chip)
            return ("chk", t, i, seq, snap, sv, chip)
        if stage == "chk":
            if q & 1: return ("start", t + 1, 0, q, snap, sv, chip)
            return ("copy", t, 0, q, snap, sv, chip)
        if stage == "copy":
            snap = snap[:i] + (pub[i],) + snap[i + 1:]; sv = sv[:i] + (pv[i],) + sv[i + 1:]
            return ("verify" if i + 1 == N else "copy", t, i + 1, q, snap, sv, chip)
        if stage == "verify":
            if seq != q: return ("start", t + 1, 0, q, snap, sv, chip)
            return ("write", t, 0, q, snap, sv, chip)
        if stage == "write":
            if sv[i]: chip = chip[:i] + (snap[i],) + chip[i + 1:]
            return ("done" if i + 1 == N else "write", t, i + 1, q, snap, sv, chip)
    else:   # old routine
        if stage == "start":
            if t >= 4: return ("done", t, i, q, snap, sv, chip)
            return ("chk", t, i, seq, snap, sv, chip)
        if stage == "chk":
            if q & 1: return ("start", t + 1, 0, q, snap, sv, chip)
            return ("loop", t, 0, q, snap, sv, chip)
        if stage == "loop":
            if pv[i]: chip = chip[:i] + (pub[i],) + chip[i + 1:]
            return ("verify" if i + 1 == N else "loop", t, i + 1, q, snap, sv, chip)
        if stage == "verify":
            if seq == q: return ("done", t, i, q, snap, sv, chip)
            return ("start", t + 1, 0, q, snap, sv, chip)
    raise AssertionError(stage)


def complete(chip):
    return chip == INIT_CHIP or chip in RECORDS


def explore(variant):
    s0 = (0, 0, 0, (0,) * N, (0,) * N)
    m0 = ("start", 0, 0, 0, (0,) * N, (0,) * N, INIT_CHIP)
    seen = {(s0, m0)}
    todo = [(s0, m0)]
    terminals, bad, example = 0, 0, None
    while todo:
        s, m = todo.pop()
        if m[0] == "done":
            terminals += 1
            if not complete(m[6]):
                bad += 1
                example = example or (s, m[6])
            continue
        nxt = []
        if s[0] < len(SLAVE):
            ss = slave_step(s); nxt.append((ss, m))
        mm = master_step(m, (s[2], s[3], s[4]), variant)
        nxt.append((s, mm))
        for n in nxt:
            if n not in seen:
                seen.add(n); todo.append(n)
    return len(seen), terminals, bad, example


def main():
    states, term, bad, _ = explore("new")
    print(f"new routine: {states} states, {term} terminal states, {bad} with a mixed record on the chip")
    states_o, term_o, bad_o, ex = explore("old")
    print(f"old routine: {states_o} states, {term_o} terminal states, {bad_o} with a mixed record on the chip" + (f", e.g. chip {ex[1]}" if ex else ""))
    ok = bad == 0 and bad_o > 0 and term > 100
    print("lat_protocol_test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
