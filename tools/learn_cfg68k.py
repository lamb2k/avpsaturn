#!/usr/bin/env python
"""Recursive-descent code map of the private decrypted avspu program, plus style census.

usage: learn_cfg68k.py build     writes E:/AvP/learning/cfg.json (ROM-derived, stays on this PC)
       learn_cfg68k.py style     compiled-C versus hand-assembly census over reachable code
Roots: reset/IRQ/trap vectors, plus any extra roots listed in E:/AvP/learning/roots.txt.
Follows branches, calls, and pc-relative jump tables. Dispatch through RAM or through object
fields cannot be followed, so reachable is a lower bound; unresolved sites are counted.
"""
import collections
import json
import os
import pathlib
import re
import struct
import sys

import capstone

DEPS = pathlib.Path(os.environ.get(
    "AVP_DEPS", r"C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest-playable-loop-pivot\.deps"))
BASE = DEPS / "mame" / "actorprobe"
OP = (BASE / "decrypted_opcodes_2m.bin").read_bytes()
PR = (BASE / "decrypted_program_2m.bin").read_bytes()
OUT = pathlib.Path(os.environ.get("LEARN_OUT", r"E:\AvP\learning"))
MD = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_M68K_000 | capstone.CS_MODE_BIG_ENDIAN)
ROM_END = 0x200000
CODE_END = 0x100000
COND = {"beq", "bne", "bcc", "bcs", "bhi", "bls", "bge", "blt", "bgt", "ble", "bpl", "bmi", "bvc", "bvs",
        "bhs", "blo"}


def insn(a):
    if a < 0 or a + 2 > ROM_END or a & 1:
        return None
    for i in MD.disasm(OP[a:a + 12], a, 1):
        return i
    return None


def be16(a):
    return struct.unpack(">H", OP[a:a + 2])[0]


def sbe16(a):
    return struct.unpack(">h", OP[a:a + 2])[0]


def hexval(s):
    m = re.search(r"\$([0-9a-f]+)", s)
    return int(m.group(1), 16) if m else None


def base(m):
    return m.split(".")[0]


def plausible(a):
    i = insn(a)
    return i is not None


def table_offsets(t, limit=256):
    """Word-offset table relative to its own start. Ends at the lowest target or a bad entry."""
    out, low = [], ROM_END
    p = t
    while p < low and len(out) < limit:
        v = sbe16(p)
        tgt = t + v
        if v == 0 or tgt & 1 or tgt < 0x400 or tgt >= ROM_END or not plausible(tgt):
            break
        out.append(tgt)
        if v > 0:                      # a backward target is legal and says nothing about where the table ends
            low = min(low, tgt)
        p += 2
    return out


def table_longs(t, limit=256):
    out, p = [], t
    while len(out) < limit:
        v = struct.unpack(">I", OP[p:p + 4])[0]
        if v == 0 or v & 1 or v >= ROM_END or not plausible(v):
            break
        out.append(v)
        p += 4
    return out


def vectors():
    roots = {}
    for n in [1, 2, 3, 4, 5, 6, 7, 8, 9] + list(range(24, 32)) + list(range(32, 48)):
        v = struct.unpack(">I", PR[n * 4:n * 4 + 4])[0]
        if 0 < v < ROM_END and not v & 1:
            roots[v] = f"vec{n}"
    return roots


def validates(a, cap=500):
    """Linear decode from a must reach a terminator with no undecodable word."""
    n = 0
    while n < cap:
        i = insn(a)
        if i is None or i.mnemonic.startswith("dc."):
            return False
        if base(i.mnemonic) in ("rts", "rte", "rtr", "bra", "jmp"):
            return True
        a += i.size
        n += 1
    return False


def walk(root, seen_i, interior):
    """Direct flow only from root. Returns its instruction map, or None if it collides with accepted code."""
    out = {}
    work = [root]
    while work:
        a = work.pop()
        while a not in out and a not in seen_i:
            if a in interior:
                return None
            i = insn(a)
            if i is None or i.mnemonic.startswith("dc."):
                return None
            for k in range(a + 2, a + i.size, 2):
                if k in seen_i:
                    return None
            out[a] = i.size
            m = base(i.mnemonic)
            ops = i.op_str
            if m in ("bra", "bsr") or m in COND or m.startswith("db"):
                t = hexval(ops.split(",")[-1])
                if t is not None:
                    work.append(t)
            elif m in ("jsr", "jmp") and re.fullmatch(r"\$[0-9a-f]+(\.[lw]|\(pc\))?", ops.strip()):
                work.append(hexval(ops))
            if m in ("bra", "jmp", "rts", "rte", "rtr", "stop", "illegal"):
                break
            a += i.size
    return out


def filter_roots(certain, scanned):
    """Boundary rule: a scanned root must not overlap code already accepted. A bad split never joins the target list."""
    seen_i, interior = {}, set()
    def accept(w):
        for a, n in w.items():
            seen_i[a] = n
            for k in range(a + 2, a + n, 2):
                interior.add(k)
    for r in certain:
        w = walk(r, seen_i, interior)
        if w:
            accept(w)
    kept, dropped = {}, 0
    order = sorted(scanned, key=lambda r: (0 if "abs" in scanned[r] else 1 if "bsr" in scanned[r] else 2, r))
    for r in order:
        w = walk(r, seen_i, interior)
        if w is None:
            dropped += 1
            continue
        accept(w)
        kept[r] = scanned[r]
    print(f"scan roots kept {len(kept)}, dropped for overlap {dropped}")
    return kept


def scan_roots():
    """Raw scan of the encrypted-region opcode image for call/jump absolutes and pointer tables.
    Accepts a target only if linear decode from it terminates cleanly. Tier: scan, not proof."""
    roots = {}
    for p in range(0, CODE_END - 6, 2):
        w = be16(p)
        if w in (0x4eb9, 0x4ef9):
            v = struct.unpack(">I", OP[p + 2:p + 6])[0]
            if 0x400 <= v < CODE_END and not v & 1 and validates(v):
                roots[v] = "scan_abs"
        if w in (0x6100,):
            v = p + 2 + sbe16(p + 2)
            if 0x400 <= v < CODE_END and not v & 1 and validates(v) and validates(p + 4):
                roots[v] = "scan_bsr"
    # long pointer tables of 3+ code targets, in either image
    for img, name in ((OP, "op"), (PR, "pr")):
        p = 0x400
        while p < 0x200000 - 12:
            run = []
            q = p
            while q < 0x200000 - 4:
                v = struct.unpack(">I", img[q:q + 4])[0]
                if not (0x400 <= v < CODE_END) or v & 1 or not validates(v):
                    break
                run.append(v)
                q += 4
            if len(run) >= 3:
                for v in run:
                    roots[v] = "scan_table_" + name
                p = q
            else:
                p += 2
    return roots


def build(depth=0):
    roots = vectors()
    auto = set()
    if (OUT / "roots_auto.txt").exists() and depth:
        auto = {int(x, 16) for x in (OUT / "roots_auto.txt").read_text().split()}
        roots.update({v: "auto" for v in auto})
    # Task entries in code are found as lea/move pointers; add immediates that look like code on demand
    extra = pathlib.Path(__file__).parent / "roots.txt"
    if extra.exists():
        for line in extra.read_text().split():
            roots[int(line, 16)] = "extra"
    roots.update(filter_roots(list(roots), scan_roots()))
    work = list(roots)
    func_entries = set(roots)
    seen = {}
    unresolved = collections.Counter()
    tables = {}
    leas = {}
    while work:
        a = work.pop()
        prev = []
        while a not in seen:
            i = insn(a)
            if i is None:
                unresolved["undecodable"] += 1
                break
            m, ops = base(i.mnemonic), i.op_str
            seen[a] = i.size
            nxt = a + i.size
            stop = False
            if m in ("bra", "bsr", "jsr", "jmp") or m in COND or m.startswith("db"):
                pcidx = re.search(r"\$([0-9a-f]+)\(pc,\s*([ad]\d)", ops)
                target = None
                if m in ("bra", "bsr") or m in COND or m.startswith("db"):
                    target = hexval(ops.split(",")[-1])
                elif re.fullmatch(r"\$[0-9a-f]+(\.[lw])?", ops.strip()):
                    target = hexval(ops)
                elif re.fullmatch(r"\$[0-9a-f]+\(pc\)", ops.strip()):
                    target = hexval(ops)
                if target is not None:
                    work.append(target)
                    if m in ("bsr", "jsr"):
                        func_entries.add(target)
                elif pcidx:
                    t = int(pcidx.group(1), 16)
                    pr = prev[-1] if prev else None
                    if pr is not None and f"${t:x}(pc" in pr.op_str and pr.mnemonic.startswith("move.w"):
                        tg = table_offsets(t)      # move.w T(pc,dn),dm; jmp T(pc,dm)
                    else:
                        tg = [t2 for t2 in table_bra(t)]
                    if tg:
                        tables[t] = tg
                        work.extend(tg)
                        func_entries.update(tg) if m == "jsr" else None
                    else:
                        unresolved["pc_table_empty"] += 1
                else:
                    r = table_from_prev(prev, ops)
                    if r:
                        tables[r[0]] = r[1]
                        work.extend(r[1])
                        func_entries.update(r[1])
                    else:
                        unresolved[f"{m}_indirect"] += 1
                if m in ("bra", "jmp"):
                    stop = True
            elif m in ("rts", "rte", "rtr", "stop", "illegal"):
                stop = True
            elif m == "trap" and hexval(ops.replace("#", "$")) in (1, 2, 9):
                stop = True          # task exit traps do not return
            # code pointers loaded into registers (task entries, callbacks)
            if m in ("lea", "move", "movea", "pea"):
                v = hexval(ops.split(",")[0])
                if v is not None and "#" in ops.split(",")[0] and 0x400 <= v < ROM_END and not v & 1 and i.size >= 6:
                    leas[v] = a
                if m == "lea" and v is not None and 0x400 <= v < ROM_END:
                    leas.setdefault(v, a)
            prev.append(i)
            prev = prev[-4:]
            if stop:
                break
            a = nxt
    # Second and later passes: follow validated immediate/lea code pointers, as scan tier
    followed = [v for v in leas if v not in seen and validates(v)]
    if followed and depth < 6:
        (OUT / "roots_auto.txt").write_text(" ".join(f"{v:x}" for v in sorted(set(followed) | auto)))
        return build(depth + 1)
    insns = sum(1 for _ in seen)
    size = sum(seen.values())
    print(f"reachable: {insns} instructions, {size} bytes; functions {len(func_entries)}; tables {len(tables)}")
    print("unresolved:", dict(unresolved))
    print(f"immediate/lea ROM pointers not yet followed: {sum(1 for v in leas if v not in seen)}")
    json.dump(dict(seen={f"{k:x}": v for k, v in seen.items()}, funcs=sorted(func_entries),
                   tables={f"{k:x}": v for k, v in tables.items()},
                   leas={f"{k:x}": v for k, v in leas.items()}),
              open(OUT / "cfg.json", "w"))


def table_bra(t, limit=256):
    """jmp T(pc,dn) where T holds bra instructions."""
    out, p = [], t
    while len(out) < limit:
        i = insn(p)
        if i is None or base(i.mnemonic) not in ("bra", "jmp"):
            break
        v = hexval(i.op_str)
        if v is None:
            break
        out.append(v)
        p += i.size
    return out


def table_from_prev(prev, ops):
    """movea.l T(pc,dn),an / lea T,an + movea.l (an,dn),am ; jmp|jsr (am)"""
    r = re.search(r"\(a(\d)\)", ops)
    if not r:
        return None
    for p in reversed(prev):
        m = re.search(r"\$([0-9a-f]+)\(pc,\s*[ad]\d[^)]*\),\s*a" + r.group(1), p.op_str)
        if m and p.mnemonic.startswith("movea.l"):
            t = int(m.group(1), 16)
            tg = table_longs(t)
            return (t, tg) if tg else None
    return None


def style():
    d = json.load(open(OUT / "cfg.json"))
    addrs = sorted(int(k, 16) for k in d["seen"])
    funcs = set(d["funcs"])
    c = collections.Counter()
    prevm = None
    calls = 0
    after = 0
    ctop = collections.Counter()
    a5abs = 0
    for a in addrs:
        i = insn(a)
        m, ops = base(i.mnemonic), i.op_str
        c[m] += 1
        if m == "link":
            c["#link"] += 1
        if m == "movem":
            if "-(a7)" in ops:
                c["#movem_push"] += 1
        if prevm in ("jsr", "bsr"):
            calls += 1
            if (m in ("addq", "adda", "lea") and ops.rstrip().endswith("a7")) or "(a7)" in ops and m == "lea":
                after += 1
        if m in ("jsr", "bsr") and re.fullmatch(r"\$[0-9a-f]+\(pc\)", ops.strip()):
            nxt = insn(a + i.size)
            c["#jsr_pc"] += 1
            if nxt and base(nxt.mnemonic) == "nop":
                c["#jsr_pc_nop"] += 1
        if m == "jmp" and re.fullmatch(r"\$[0-9a-f]+\(pc\)", ops.strip()):
            nxt = insn(a + i.size)
            if nxt and base(nxt.mnemonic) == "nop":
                c["#jmp_pc_nop"] += 1
        if "(a5)" in ops:
            a5abs += 1
        prevm = m
    # fall-through entries: a call target directly preceded by a non-terminator
    fall = 0
    for f in funcs:
        for back in (2, 4, 6):
            if d["seen"].get(f"{f - back:x}") == back:
                i = insn(f - back)
                if base(i.mnemonic) not in ("rts", "rte", "bra", "jmp", "rtr"):
                    fall += 1
                break
    # results returned in condition codes: conditional branch directly after a call
    ccret = 0
    pushes = 0
    prev2 = None
    for a in addrs:
        i = insn(a)
        m = base(i.mnemonic)
        if prev2 in ("jsr", "bsr") and m in COND:
            ccret += 1
        if prev2 in ("jsr", "bsr") and m == "tst" and i.op_str.startswith("d0"):
            c["#tst_d0_after_call"] += 1
        if m in ("move", "pea") and i.op_str.rstrip().endswith("-(a7)"):
            pushes += 1
        prev2 = m
    print(f"cond branch directly after call {ccret}; tst d0 after call {c['#tst_d0_after_call']}; single pushes {pushes}")
    # tail jumps into the middle of another function's body
    print(f"instructions {len(addrs)} functions {len(funcs)}")
    print(f"link {c['link']}  unlk {c['unlk']}  movem-push {c['#movem_push']}")
    print(f"calls {calls}  stack cleanup right after call {after}")
    print(f"a5-relative operands {a5abs}")
    print(f"jsr pc-rel {c['#jsr_pc']}  of those followed by nop {c['#jsr_pc_nop']}; jmp pc-rel+nop {c['#jmp_pc_nop']}")
    print(f"call targets entered by fall-through {fall} of {len(funcs)}")
    print("top:", c.most_common(25))


if __name__ == "__main__":
    {"build": build, "style": style}[sys.argv[1]]()
