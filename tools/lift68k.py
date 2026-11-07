#!/usr/bin/env python
"""Throwaway 68000-to-C lifter, first-gate version. Output is ROM-derived: E:/AvP/learning/lift only.

usage: lift68k.py OUTDIR MODE [ADDR ...|@file]    MODE: mem = registers in a global struct; local = cached in locals
One C function per recovered function, flat big-endian memory through a page map, a5 known constant.
Flags are C locals with per-function liveness; stored to the struct only where a caller reads them.
Limits, reported in stats.json: unhandled mnemonics, stack-return manipulation, unresolved indirect jumps.
"""
import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.argv, _argv = sys.argv[:1] + ["style"], sys.argv
import importlib.util
spec = importlib.util.spec_from_file_location("cfg", pathlib.Path(__file__).parent / "learn_cfg68k.py")
cfg = importlib.util.module_from_spec(spec)
_saved = sys.modules.get("__main__")
spec.loader.exec_module(cfg)
sys.argv = _argv

D = json.load(open(cfg.OUT / "cfg.json"))
SEEN = {int(k, 16): v for k, v in D["seen"].items()}
FUNCS = set(D["funcs"])
TABLES = {int(k, 16): v for k, v in D["tables"].items()}
NATIVE = {0xd86}                 # replaced by the native kernel
stats = collections.Counter()
ABORTS = set()
unh = collections.Counter()
COND = {"eq": "fz", "ne": "!fz", "cc": "!fc", "hs": "!fc", "cs": "fc", "lo": "fc", "pl": "!fn", "mi": "fn",
        "vc": "!fv", "vs": "fv", "hi": "(!fc&&!fz)", "ls": "(fc||fz)", "ge": "(fn==fv)", "lt": "(fn!=fv)",
        "gt": "(!fz&&fn==fv)", "le": "(fz||fn!=fv)", "t": "1", "f": "0", "ra": "0"}
FLAGS_OF = {"eq": "z", "ne": "z", "cc": "c", "hs": "c", "cs": "c", "lo": "c", "pl": "n", "mi": "n", "vc": "v", "vs": "v",
            "hi": "cz", "ls": "cz", "ge": "nv", "lt": "nv", "gt": "znv", "le": "znv"}
CT = {1: "u8", 2: "u16", 4: "u32"}
ST = {1: "s8", 2: "s16", 4: "s32"}
MASK = {1: "0xffu", 2: "0xffffu", 4: "0xffffffffu"}


def split_ops(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([":
            depth += 1
        if ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def num(s):
    s = s.strip()
    neg = s.startswith("-")
    s = s.lstrip("-").lstrip("$")
    v = int(s, 16)
    return -v if neg else v


class Fn:
    def __init__(self, entry):
        self.entry = entry
        self.body = {}
        self.labels = set()
        self.lines = []
        self.tmp = 0
        self.regs = set()

    def reg(self, r):
        self.regs.add(r)
        return r


def reg_read(fn, r, size):
    fn.reg(r)
    return f"(({CT[size]}){r})"


def reg_write(fn, r, size, v):
    fn.reg(r)
    if size == 4 or r[0] == "a":
        return f"{r}=(u32)({v});" if size == 4 else f"{r}=(u32)(s32)(s16)({v});"
    m = {1: "0xffffff00u", 2: "0xffff0000u"}[size]
    return f"{r}=({r}&{m})|(({CT[size]})({v}));"


def is_io(c):
    return c is not None and (0x400000 <= c < 0x410000 or 0x618000 <= c < 0x61a000 or 0x800000 <= c < 0x810000 or 0x660000 <= c < 0x664000)


def mem_read(addr, size, const=None):
    if is_io(const):
        return f"(({CT[size]})IOR{size * 8}(0x{const:x}u))"
    if const is not None and const >= 0xff0000:
        return f"RAM{size * 8}(0x{const - 0xff0000:x})"
    if const is not None and const < 0x200000:
        return f"ROM{size * 8}(0x{const:x})"
    return f"RD{size * 8}({addr})"


def mem_write(addr, size, v, const=None):
    if is_io(const):
        return f"IOW{size * 8}(0x{const:x}u,({CT[size]})({v}));"
    if const is not None and const >= 0xff0000:
        return f"RAMW{size * 8}(0x{const - 0xff0000:x},({CT[size]})({v}));"
    return f"WR{size * 8}({addr},({CT[size]})({v}));"


class Operand:
    """Parsed 68000 operand: pre and post statements, plus read and write forms."""

    def __init__(self, fn, text, size):
        self.fn, self.t, self.size = fn, text, size
        self.pre, self.post = [], []
        t = text
        self.kind = None
        self.const = None
        self.pcrel = False             # pc-relative reads go through the board's opcode space
        step = 2 if size == 1 and t.startswith(("-(a7", "(a7")) else size
        if t.startswith("#"):
            self.kind, self.val = "imm", num(t[1:]) & 0xffffffff
        elif re.fullmatch(r"[da][0-7]", t):
            self.kind, self.r = "reg", t
        elif (m := re.fullmatch(r"\(a([0-7])\)\+", t)):
            r = fn.reg(f"a{m[1]}")
            self.kind, self.addr = "mem", f"t{fn.tmp}"
            self.pre.append(f"u32 t{fn.tmp}={r};{r}+={step};")
            fn.tmp += 1
        elif (m := re.fullmatch(r"-\(a([0-7])\)", t)):
            r = fn.reg(f"a{m[1]}")
            self.kind, self.addr = "mem", r
            self.pre.append(f"{r}-={step};")
        elif (m := re.fullmatch(r"\(a([0-7])\)", t)):
            self.kind, self.addr = "mem", fn.reg(f"a{m[1]}")
        elif (m := re.fullmatch(r"(-?\$[0-9a-f]+)\(a([0-7])\)", t)):
            d = num(m[1])
            if m[2] == "5":
                self.kind, self.const = "mem", (0xff8000 + d) & 0xffffff
                self.addr = f"0x{self.const:x}u"
            else:
                self.kind, self.addr = "mem", f"({fn.reg('a' + m[2])}+({d}))"
        elif (m := re.fullmatch(r"(?:(-?\$[0-9a-f]+))?\(a([0-7]),\s*([da][0-7])\.([wl])\)", t)):
            d = num(m[1]) if m[1] else 0
            ix = fn.reg(m[3])
            ix = f"(s32)(s16){ix}" if m[4] == "w" else ix
            self.kind, self.addr = "mem", f"({fn.reg('a' + m[2])}+({d})+{ix})"
        elif (m := re.fullmatch(r"\$([0-9a-f]+)\(pc\)", t)):
            self.kind, self.const = "mem", int(m[1], 16)
            self.addr = f"0x{self.const:x}u"
            self.pcrel = True
        elif (m := re.fullmatch(r"\$([0-9a-f]+)\(pc,\s*([da][0-7])\.([wl])\)", t)):
            ix = fn.reg(m[2])
            ix = f"(s32)(s16){ix}" if m[3] == "w" else ix
            self.kind, self.addr = "mem", f"(0x{int(m[1], 16):x}u+{ix})"
            self.pcrel = True
        elif (m := re.fullmatch(r"\$([0-9a-f]+)\.([wl])", t)):
            v = int(m[1], 16)
            if m[2] == "w" and v >= 0x8000:
                v |= 0xff0000
            self.kind, self.const = "mem", v & 0xffffff
            self.addr = f"0x{self.const:x}u"
        else:
            raise ValueError("operand " + t)

    def read(self):
        if self.kind == "imm":
            return f"(({CT[self.size]})0x{self.val:x}u)"
        if self.kind == "reg":
            return reg_read(self.fn, self.r, self.size)
        if self.pcrel:
            return f"OP{self.size * 8}({self.addr})"
        return mem_read(self.addr, self.size, self.const)

    def write(self, v):
        if self.kind == "reg":
            return reg_write(self.fn, self.r, self.size, v)
        return mem_write(self.addr, self.size, v, self.const)


def nz(size, v):
    return f"fz=(({CT[size]})({v}))==0;fn=(({ST[size]})({v}))<0;"


def fl(live, want, text):
    return text if want & live else ""


def base_cc(m):
    return m[1:] if m.startswith("b") else m[2:] if m.startswith("db") else m[1:]


def uses_defs(i):
    """Flag use and def sets of one instruction, for liveness."""
    m = i.mnemonic.split(".")[0]
    use, defs = set(), set()
    if m in ("move", "andi", "ori", "eori") and ("sr" in i.op_str or "ccr" in i.op_str):
        return set("zncvx"), set("zncvx")
    if (m[0] == "b" and m[1:] in FLAGS_OF) or (m[0] == "s" and m[1:] in FLAGS_OF):
        use = set(FLAGS_OF[m[1:]])
    elif m.startswith("db") and m[2:] in FLAGS_OF:
        use = set(FLAGS_OF[m[2:]])
    elif m in ("addx", "subx", "negx", "roxl", "roxr", "abcd", "sbcd", "nbcd"):
        use = {"x", "z"}
    if m in ("move", "moveq", "and", "andi", "or", "ori", "eor", "eori", "not", "clr", "tst", "ext", "swap", "mulu", "muls",
             "divu", "divs", "rol", "ror"):
        defs = {"z", "n", "c", "v"}
    elif m in ("add", "addi", "addq", "sub", "subi", "subq", "neg", "addx", "subx", "negx", "abcd", "sbcd", "lsl", "lsr", "asl", "asr", "roxl", "roxr"):
        defs = set("zncvx")
    elif m in ("cmp", "cmpi", "cmpa", "cmpm"):
        defs = {"z", "n", "c", "v"}
    elif m in ("btst", "bset", "bclr", "bchg"):
        defs = {"z"}
    if m in ("addq", "subq") and re.search(r",\s*a[0-7]$", i.op_str):
        defs = set()
    return use, defs


def collect(entry):
    """Instructions of the function: follow branches and tables, stop at other function entries."""
    body, labels = {}, set()
    work = [entry]
    while work:
        a = work.pop()
        while a not in body and a in SEEN:
            if a != entry and (a in FUNCS or a in NATIVE):
                break
            i = cfg.insn(a)
            body[a] = i
            m = i.mnemonic.split(".")[0]
            nxt = a + i.size
            if m == "bra" or (m[0] == "b" and m[1:] in FLAGS_OF) or m.startswith("db"):
                t = cfg.hexval(i.op_str.split(",")[-1])
                labels.add(t)
                work.append(t)
                if m == "bra":
                    break
            elif m == "jmp":
                pc = re.search(r"\$([0-9a-f]+)\(pc,", i.op_str)
                if pc and int(pc[1], 16) in TABLES:
                    for t in TABLES[int(pc[1], 16)]:
                        labels.add(t)
                        work.append(t)
                break
            elif m in ("rts", "rte", "rtr", "stop"):
                break
            a = nxt
    return body, labels


def lift(entry, ccret, mode):
    body, labels = collect(entry)
    fn = Fn(entry)
    order = sorted(body)
    # successors for flag liveness
    succ = {}
    for a in order:
        i = body[a]
        m = i.mnemonic.split(".")[0]
        s = []
        nxt = a + i.size
        if m == "bra":
            s = [cfg.hexval(i.op_str)]
        elif (m[0] == "b" and m[1:] in FLAGS_OF) or m.startswith("db"):
            s = [cfg.hexval(i.op_str.split(",")[-1]), nxt]
        elif m == "jmp":
            pc = re.search(r"\$([0-9a-f]+)\(pc,", i.op_str)
            s = list(TABLES.get(int(pc[1], 16), [])) if pc else []
        elif m in ("rts", "rte", "rtr", "stop"):
            s = []
        else:
            s = [nxt]
        succ[a] = s
    live = {a: set() for a in order}
    changed = True
    while changed:
        changed = False
        for a in reversed(order):
            i = body[a]
            m = i.mnemonic.split(".")[0]
            u, d = uses_defs(i)
            out = set()
            for s in succ[a]:
                if s in live:
                    out |= live[s]
                else:
                    out |= set("zncvx")     # a tail call or a split function may read them
            if m == "rts" and entry in ccret:
                out |= {"z", "n", "c", "v"}
            new = u | (out - d)
            if m in ("jsr", "bsr"):
                new = out - {"z", "n", "c", "v", "x"} if False else new
            if new != live[a]:
                live[a] = new
                changed = True
    code = []
    for a in order:
        i = body[a]
        m0 = i.mnemonic
        m = m0.split(".")[0]
        sz = {"b": 1, "w": 2, "l": 4}.get(m0.split(".")[1] if "." in m0 else "", None)
        out = set()
        for s in succ[a]:
            out |= live.get(s, set("zncvx"))
        if m == "rts" and entry in ccret:
            out |= {"z", "n", "c", "v"}
        lab = f"L{a:x}:;" if a in labels or (a == entry and order[0] != entry) else ""
        stats["insns"] += 1
        try:
            st = emit(fn, a, i, m, sz, out, ccret, entry)
        except (ValueError, TypeError, AttributeError, KeyError, IndexError):
            unh[m] += 1
            ABORTS.add(a)
            st = f"UNHANDLED(0x{a:x});"
        code.append(f"{lab}P(0x{a:x}u);{{{st}}}")
        nxt = a + i.size
        if nxt not in body and succ[a] and nxt in succ[a]:
            code.append(f"{{CCOUT();f_{nxt:x}();return;}}")
    if order and order[0] != entry:
        code.insert(0, f"goto L{entry:x};")
    if live.get(entry):
        code.insert(0, "{CCAFTER();}")
    return fn, code


def call(fn, t):
    return f"f_{t:x}();"


def emit(fn, a, i, m, sz, live, ccret, entry):
    ops = split_ops(i.op_str)
    nxt = a + i.size
    if m in ("rte", "rtr"):
        ABORTS.add(a)
        return "RTE();"
    if m == "rts":
        return "CCOUT();return;" if entry in ccret and m == "rts" else "return;"
    if m == "nop":
        return ""
    if m == "bra":
        t = cfg.hexval(ops[0])
        return f"goto L{t:x};" if t in fn_body_targets(entry) else f"CCOUT();f_{t:x}();return;"
    if m[0] == "b" and m[1:] in FLAGS_OF:
        t = cfg.hexval(ops[0])
        go = f"goto L{t:x};" if t in fn_body_targets(entry) else f"{{CCOUT();f_{t:x}();return;}}"
        return f"if({COND[m[1:]]}){go}"
    if m.startswith("db"):
        t = cfg.hexval(ops[1])
        r = fn.reg(ops[0])
        go = f"goto L{t:x};" if t in fn_body_targets(entry) else f"{{CCOUT();f_{t:x}();return;}}"
        c = COND[m[2:]]
        return f"if(!{c}){{{r}=({r}&0xffff0000u)|(u16)({r}-1);if((u16){r}!=0xffff){go}}}"
    if m in ("jsr", "bsr", "jmp"):
        tail = m == "jmp"
        pc = re.search(r"\$([0-9a-f]+)\(pc,\s*([da][0-7])", i.op_str)
        if pc and int(pc[1], 16) in TABLES:
            t0 = int(pc[1], 16)
            ix = fn.reg(pc[2])
            cases = []
            seen_off = set()
            offs = []
            if t0 in SEEN and cfg.insn(t0) is not None and cfg.insn(t0).mnemonic.startswith(("bra", "jmp", "b")) and not cfg.insn(t0).mnemonic.startswith("btst"):   # table of branch instructions: the index register is a byte offset into it
                p = t0
                for t in TABLES[t0]:
                    offs.append((p - t0, t))
                    p += cfg.insn(p).size
            else:                       # word offsets: the register already holds target minus table start
                offs = [(t - t0, t) for t in TABLES[t0]]
            for off, t in offs:
                if off in seen_off:
                    continue
                seen_off.add(off)
                if tail:
                    go = f"goto L{t:x};" if t in fn_body_targets(entry) else f"CCOUT();f_{t:x}();return;"
                else:
                    go = f"f_{t:x}();break;"
                cases.append(f"case {off}:{go}")
            return f"switch((s16){ix}){{{''.join(cases)}default:BADJUMP(0x{a:x});}}" + ("" if tail else CCIN(live))
        t = cfg.hexval(ops[0]) if re.fullmatch(r"\$[0-9a-f]+(\.[lw]|\(pc\))?", ops[0]) else None
        if t is not None:
            if tail:
                return "CCOUT();" + call(fn, t) + "return;"
            return call(fn, t) + CCIN(live)
        stats["indirect_calls"] += 1
        o = Operand(fn, ops[0].replace("(a", "(a"), 4) if False else None
        rr = re.fullmatch(r"\(a([0-7])\)", ops[0])
        if rr:
            return f"DISPATCH({fn.reg(f'a{rr[1]}')});" + CCIN(live) + ("return;" if tail else "")
        o = Operand(fn, ops[0], 4)
        return "".join(o.pre) + f"DISPATCH({o.addr});" + CCIN(live) + ("return;" if tail else "")
    if m == "trap":
        return f"f_trap{num(ops[0][1:])}();" + CCIN(live)
    if m == "movem":
        return emit_movem(fn, i, ops, sz)
    if m == "lea":
        s = Operand(fn, ops[0], 4)
        return "".join(s.pre) + f"{fn.reg(ops[1])}={s.addr};"
    if m == "pea":
        s = Operand(fn, ops[0], 4)
        return "".join(s.pre) + f"a7-=4;WR32(a7,{s.addr});" if fn.reg("a7") else ""
    if m == "swap":
        r = fn.reg(ops[0])
        return f"{r}=({r}<<16)|({r}>>16);" + fl_nz(live, 4, r)
    if m == "exg":
        r0, r1 = fn.reg(ops[0]), fn.reg(ops[1])
        return f"{{u32 t={r0};{r0}={r1};{r1}=t;}}"
    if m == "ext":
        r = fn.reg(ops[0])
        if sz == 2:
            return reg_write(fn, r, 2, f"(s16)(s8){r}") + fl_nz(live, 2, r)
        return f"{r}=(u32)(s32)(s16){r};" + fl_nz(live, 4, r)
    if m == "move" and ops[1] == "ccr" and ops[0][0] == "#":
        k = num(ops[0][1:])
        return "".join(f"{f}={(k >> b) & 1};" for f, b in (("fc", 0), ("fv", 1), ("fz", 2), ("fn", 3), ("fx", 4)))
    if m in ("moveq", "move", "movea"):
        if "sr" in ops or "ccr" in ops or "usp" in ops:
            stats["sr_ops"] += 1
            ABORTS.add(a)
            return "SYSREG();"
        if m == "moveq":
            s, sz = None, 4
            q = num(ops[0][1:]) & 0xff
            v = f"0x{(q - 256 if q >= 128 else q) & 0xffffffff:x}u"
            return reg_write(fn, fn.reg(ops[1]), 4, v) + fl_nz(live, 4, ops[1])
        s = Operand(fn, ops[0], sz)
        d = Operand(fn, ops[1], sz)
        v = s.read() if ops[1][0] != "a" else f"(s32)({ST[sz]})({s.read()})"
        if m == "movea" or re.fullmatch(r"a[0-7]", ops[1]):
            return "".join(s.pre) + (f"{fn.reg(ops[1])}=(u32)(s32)({ST[sz]})({s.read()});")
        return "".join(s.pre) + f"{{{CT[sz]} v={s.read()};" + "".join(d.pre) + d.write("v") + fl_nz(live, sz, "v") + "}"
    if m == "clr":
        d = Operand(fn, ops[0], sz)
        return "".join(d.pre) + d.write("0") + (("fz=1;fn=0;fc=0;fv=0;" if live else ""))
    if m == "tst":
        s = Operand(fn, ops[0], sz)
        return "".join(s.pre) + f"{{{CT[sz]} v={s.read()};" + fl_nz(live, sz, "v") + "}"
    if m in ("and", "andi", "or", "ori", "eor", "eori"):
        if "ccr" in ops:  # the condition codes are real state: abcd/sbcd/addx read X
            k = num(ops[0][1:])
            return "".join(f"{f}={ {'a': f'{f}&&{(k >> b) & 1}', 'o': f'{f}||{(k >> b) & 1}', 'e': f'(!!{f})^{(k >> b) & 1}'}[m[0]] };" for f, b in (("fc", 0), ("fv", 1), ("fz", 2), ("fn", 3), ("fx", 4)))
        if "sr" in ops or "ccr" in ops:
            stats["sr_ops"] += 1
            ABORTS.add(a)
            return "SYSREG();"
        s = Operand(fn, ops[0], sz)
        d = Operand(fn, ops[1], sz)
        op = {"a": "&", "o": "|", "e": "^"}[m[0]]
        return "".join(s.pre) + f"{{{CT[sz]} s={s.read()};" + "".join(d.pre) + f"{CT[sz]} v={d.read()}{op}s;" + d.write("v") + fl_nz(live, sz, "v") + "}"
    if m == "not":
        d = Operand(fn, ops[0], sz)
        return "".join(d.pre) + f"{{{CT[sz]} v=~{d.read()};" + d.write("v") + fl_nz(live, sz, "v") + "}"
    if m in ("add", "addi", "addq", "sub", "subi", "subq", "cmp", "cmpi", "cmpa", "adda", "suba"):
        return emit_arith(fn, m, sz, ops, live)
    if m == "neg":
        d = Operand(fn, ops[0], sz)
        return "".join(d.pre) + f"{{{CT[sz]} s={d.read()};{CT[sz]} v=({CT[sz]})(0-s);" + d.write("v") + fl_nz(live, sz, "v") + \
            ("fc=s!=0;fx=fc;" if live & set("cx") else "") + ("fv=(s&v)>>" + str(sz * 8 - 1) + ";" if "v" in live else "") + "}"
    if m in ("lsl", "lsr", "asl", "asr", "rol", "ror", "roxl", "roxr"):
        return emit_shift(fn, m, sz, ops, live)
    if m in ("mulu", "muls"):
        s = Operand(fn, ops[0], 2)
        r = fn.reg(ops[1])
        t = "u32)(u16" if m == "mulu" else "s32)(s16"
        return "".join(s.pre) + f"{r}=(u32)(({t})({r})*({t})({s.read()}));" + fl_nz(live, 4, r)
    if m in ("divu", "divs"):
        s = Operand(fn, ops[0], 2)
        r = fn.reg(ops[1])
        return "".join(s.pre) + f"{{int ov=0;{r}=f_div{m[3]}({r},{s.read()},&ov);fv=ov;fc=0;if(!ov){{fz=(u16){r}==0;fn=(s16){r}<0;}}}}"
    if m in ("btst", "bset", "bclr", "bchg"):
        isreg = re.fullmatch(r"d[0-7]", ops[1]) is not None
        w = 4 if isreg else 1
        d = Operand(fn, ops[1], w)
        bit = f"({num(ops[0][1:])}&{w * 8 - 1})" if ops[0].startswith("#") else f"({fn.reg(ops[0])}&{w * 8 - 1})"
        act = {"btst": "", "bset": d.write(f"v|(1u<<{bit})"), "bclr": d.write(f"v&~(1u<<{bit})"), "bchg": d.write(f"v^(1u<<{bit})")}[m]
        return "".join(d.pre) + f"{{{CT[w]} v={d.read()};" + ("fz=!((v>>" + bit + ")&1);" if "z" in live else "") + act + "}"
    if m[0] == "s" and m[1:] in COND:
        d = Operand(fn, ops[0], 1)
        return "".join(d.pre) + d.write(f"({COND[m[1:]]})?0xff:0")
    if m in ("addx", "subx"):
        s = Operand(fn, ops[0], sz)
        d = Operand(fn, ops[1], sz)
        op = "+" if m == "addx" else "-"
        return "".join(s.pre + d.pre) + f"{{{CT[sz]} s={s.read()},o={d.read()},v=o{op}s{op}fx;" + d.write("v") + \
            ("if(v)fz=0;fn=(" + ST[sz] + ")v<0;" if live else "") + ("{int ox=fx;fx=fc=CARRY" + op.replace("+", "A").replace("-", "S") + "(o,s,v,ox);}") + (f"fv=(({ST[sz]})((o^s)&(o^v)))<0;" if m == "subx" else f"fv=(({ST[sz]})((o^v)&(s^v)))<0;") + "}"
    if m == "movep":
        tomem = ops[0][0] == "d"
        mm = re.fullmatch(r"(-?\$[0-9a-f]+)?\(a([0-7])\)", ops[1] if tomem else ops[0])
        if not mm:
            raise ValueError(m)
        disp = num(mm[1]) if mm[1] else 0
        b = fn.reg("a" + mm[2])
        r = fn.reg(ops[0] if tomem else ops[1])
        parts = []
        for k in range(sz):
            sh = (sz - 1 - k) * 8
            ad = f"({b}+({disp + 2 * k}))"
            parts.append(f"WR8({ad},(u8)({r}>>{sh}));" if tomem else f"v|=(u32)RD8({ad})<<{sh};")
        if tomem:
            return "".join(parts)
        return "{u32 v=0;" + "".join(parts) + reg_write(fn, r, sz, "v") + "}"
    if m == "negx":
        d = Operand(fn, ops[0], sz)
        return "".join(d.pre) + f"{{{CT[sz]} s={d.read()},v=({CT[sz]})(0-s-fx);" + d.write("v") + "if(v)fz=0;" + f"fn=({ST[sz]})v<0;fv=(({ST[sz]})(s&v))<0;fc=fx=(s|fx)!=0;}}"
    if m in ("abcd", "sbcd"):
        s = Operand(fn, ops[0], 1)
        d = Operand(fn, ops[1], 1)
        h = "f_abcd" if m == "abcd" else "f_sbcd"
        return "".join(s.pre + d.pre) + f"{{u32 v={h}({d.read()},{s.read()},&fx);" + d.write("v") + "if((u8)v)fz=0;fc=fx;}"
    raise ValueError(m)


def CCIN(live):
    return "CCAFTER();" if live & {"z", "n", "c", "v"} else ""


def fl_nz(live, sz, v):
    out = nz(sz, v) if live & {"z", "n"} else ""
    if "c" in live:
        out += "fc=0;"
    if "v" in live:
        out += "fv=0;"
    return out


def emit_arith(fn, m, sz, ops, live):
    s = Operand(fn, ops[0], sz)
    d = Operand(fn, ops[1], sz if not re.fullmatch(r"a[0-7]", ops[1]) else 4)
    toa = re.fullmatch(r"a[0-7]", ops[1]) is not None
    sub = m[0] != "a"
    pre = "".join(s.pre) + "".join(d.pre)
    if toa:
        ext = f"(u32)(s32)({ST[sz]})({s.read()})"
        r = fn.reg(ops[1])
        if m.startswith("cmp"):
            c = f"{{u32 s={ext},o={r},v=o-s;" + fl_nz(live, 4, "v") + \
                ("fc=o<s;" if "c" in live else "") + ("fv=(s32)((o^s)&(o^v))<0;" if "v" in live else "") + "}"
            return pre + c
        return pre + f"{r}{'-' if sub else '+'}={ext};"
    t, st = CT[sz], ST[sz]
    b = sz * 8 - 1
    body = f"{{{t} s={s.read()},o={d.read()},v=({t})(o{'-' if sub else '+'}s);"
    if not m.startswith("cmp"):
        body += d.write("v")
    body += fl_nz(live, sz, "v")
    if live & {"c", "x"}:
        body += ("fc=o<s;" if sub else "fc=v<o;")
        if not m.startswith("cmp"):
            body += "fx=fc;"
    if "v" in live:
        body += (f"fv=(({st})((o^s)&(o^v)))<0;" if sub else f"fv=(({st})((o^v)&(s^v)))<0;")
    return pre + body + "}"


def emit_shift(fn, m, sz, ops, live):
    if len(ops) == 1:
        d = Operand(fn, ops[0], 2)
        n = "1"
        sz = 2
    else:
        d = Operand(fn, ops[1], sz)
        n = str(num(ops[0][1:])) if ops[0].startswith("#") else f"({fn.reg(ops[0])}&63)"
    t, st = CT[sz], ST[sz]
    bits = sz * 8
    e = {"lsl": f"SHL{bits}(o,n)", "lsr": f"SHR{bits}(o,n)", "asl": f"SHL{bits}(o,n)", "asr": f"ASR{bits}(o,n)",
         "rol": f"ROL{bits}(o,n)", "ror": f"ROR{bits}(o,n)", "roxl": f"ROXL{bits}(o,n)", "roxr": f"ROXR{bits}(o,n)"}[m]
    out = "".join(d.pre) + f"{{{t} o={d.read()};int n={n};{t} v={e};" + d.write("v") + fl_nz(live, sz, "v")
    if m in ("rol", "ror"):
        if "c" in live:
            out += f"fc=n?(v>>{'0' if m == 'rol' else bits - 1})&1:0;"
    elif m in ("roxl", "roxr"):
        out += "fc=fx;"
    elif live & {"c", "x"}:
        if m[-1] == "l":
            out += f"if(n){{fc=n<={bits}?(o>>({bits}-n))&1:0;fx=fc;}}else fc=0;"
        elif m == "lsr":
            out += f"if(n){{fc=n<={bits}?(o>>(n-1))&1:0;fx=fc;}}else fc=0;"
        else:
            out += f"if(n){{fc=n<{bits}?(o>>(n-1))&1:(({ST[sz]})o<0);fx=fc;}}else fc=0;"
    if m == "asl" and "v" in live:
        out += f"{{int k;fv=0;for(k=1;k<=n&&k<={bits};k++)if(((o>>({bits}-1))^(o>>({bits}-1-k)))&1){{fv=1;break;}}if(n>={bits}&&o)fv=1;}}"
    return out + "}"


def emit_movem(fn, i, ops, sz):
    mask, mem, load = (ops[1], ops[0], True) if re.match(r"[da][0-7]", ops[1]) else (ops[0], ops[1], False)
    regs = []
    for part in mask.split("/"):
        m = re.fullmatch(r"([da])([0-7])(?:-[da]([0-7]))?", part)
        if not m:
            raise ValueError("movem")
        for k in range(int(m[2]), int(m[3] or m[2]) + 1):
            regs.append(f"{m[1]}{k}")
    pre = re.fullmatch(r"-\(a([0-7])\)", mem)
    post = re.fullmatch(r"\(a([0-7])\)\+", mem)
    out = []
    if pre:
        r = fn.reg(f"a{pre[1]}")
        out.append(f"{{u32 p={r},b={r};")
        for x in reversed(regs):
            fn.reg(x)
            val = "b" if x == r else x
            out.append(f"p-={sz};WR{sz * 8}(p,({CT[sz]}){val});")
        out.append(f"{r}=p;}}")
    elif post:
        r = fn.reg(f"a{post[1]}")
        out.append(f"{{u32 p={r};")
        for x in regs:
            fn.reg(x)
            v = f"RD{sz * 8}(p)"
            out.append(f"{x}=(u32)(s32)({ST[sz]}){v};p+={sz};" if sz == 2 else f"{x}={v};p+={sz};")
        out.append(f"{r}=p;}}")
    else:
        o = Operand(fn, mem, sz)
        out.append(f"{{u32 p={o.addr};")
        for x in regs:
            fn.reg(x)
            if load:
                v = f"RD{sz * 8}(p)"
                out.append(f"{x}=(u32)(s32)({ST[sz]}){v};p+={sz};" if sz == 2 else f"{x}={v};p+={sz};")
            else:
                out.append(f"WR{sz * 8}(p,({CT[sz]}){x});p+={sz};")
        out.append("}")
    return "".join(out)


_targets = {}


def fn_body_targets(entry):
    if entry not in _targets:
        body, labels = collect(entry)
        _targets[entry] = {t for t in labels if t in body}
    return _targets[entry]


def cc_return_set():
    out = set()
    for a in SEEN:
        i = cfg.insn(a)
        m = i.mnemonic.split(".")[0]
        if m in ("jsr", "bsr"):
            n = cfg.insn(a + i.size)
            t = cfg.hexval(i.op_str) if re.fullmatch(r"\$[0-9a-f]+(\.[lw]|\(pc\))?", i.op_str.strip()) else None
            if t is not None and n is not None:
                nm = n.mnemonic.split(".")[0]
                if (nm[0] == "b" and nm[1:] in FLAGS_OF):
                    out.add(t)
    # a fragment reached by tail from a flag-returning function returns the flags too
    tails = {}
    for f in FUNCS:
        try:
            body, _ = collect(f)
        except Exception:
            continue
        ts = set()
        for a2, i2 in body.items():
            m2 = i2.mnemonic.split(".")[0]
            n2 = a2 + i2.size
            if m2 not in ("bra", "jmp", "rts", "rte", "rtr", "stop") and n2 not in body and n2 in FUNCS:
                ts.add(n2)
            if m2 == "bra" or m2 == "jmp" or (m2[0] == "b" and m2[1:] in FLAGS_OF) or m2.startswith("db"):
                try:
                    t2 = cfg.hexval(i2.op_str.split(",")[-1])
                except Exception:
                    continue
                if t2 in FUNCS and t2 not in body:
                    ts.add(t2)
        tails[f] = ts
    work = list(out)
    while work:
        for t2 in tails.get(work.pop(), ()):
            if t2 not in out:
                out.add(t2)
                work.append(t2)
    return out


HEADER = """typedef unsigned char u8;typedef unsigned short u16;typedef unsigned int u32;
typedef signed char s8;typedef short s16;typedef int s32;
typedef struct{u32 d[8];u32 a[8];u32 ccz,ccn,ccc,ccv,ccx;}Cpu;
#ifdef HOST
extern Cpu *R;
extern u8 *PAGE[256];
extern u8 RAMB[];extern u8 ROMB[];extern u8 *OPB;
#ifdef PREEMPT
extern u32 irq_pc;extern void irq_check(u32);
extern int p_watch;
#define P(a) do{if((a)==irq_pc||p_watch)irq_check(a);}while(0)
#else
#define P(a)
#endif
static inline u32 be16r(const volatile u8*p){return (u32)p[0]<<8|p[1];}
static inline u32 be32r(const volatile u8*p){return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static inline void be16w(volatile u8*p,u32 v){p[0]=v>>8;p[1]=v;}
static inline void be32w(volatile u8*p,u32 v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
#define PB(a) (PAGE[((u32)(a)>>16)&0xff]+((u32)(a)&0xffff))
#define RAM8(o) (RAMB[o])
#define RAM16(o) ((u16)be16r(RAMB+(o)))
#define RAM32(o) be32r(RAMB+(o))
#define RAMW8(o,v) (RAMB[o]=(v))
#define RAMW16(o,v) be16w(RAMB+(o),(v))
#define RAMW32(o,v) be32w(RAMB+(o),(v))
#define OP8(a) (OPB[(u32)(a)&0x1fffff])
#define OP16(a) ((u16)be16r(OPB+((u32)(a)&0x1fffff)))
#define OP32(a) be32r(OPB+((u32)(a)&0x1fffff))
#define ROM8(o) (ROMB[o])
#define ROM16(o) ((u16)be16r(ROMB+(o)))
#define ROM32(o) be32r(ROMB+(o))
#define RD8(a) (*PB(a))
#define RD16(a) ((u16)be16r(PB(a)))
#define RD32(a) be32r(PB(a))
#define WR8(a,v) (*PB(a)=(v))
#define WR16(a,v) be16w(PB(a),(v))
#define WR32(a,v) be32w(PB(a),(v))
#else
register Cpu *R __asm__("r14");
extern u8 *PAGE[256];
extern u8 RAMB[];extern u8 ROMB[];extern u8 *OPB;
#ifdef PREEMPT
extern u32 irq_pc;extern void irq_check(u32);
extern int p_watch;
#define P(a) do{if((a)==irq_pc||p_watch)irq_check(a);}while(0)
#else
#define P(a)
#endif
#define RAM8(o) (*(volatile u8*)(RAMB+(o)))
#define RAM16(o) (*(volatile u16*)(RAMB+(o)))
#define RAM32(o) (*(volatile u32*)(RAMB+(o)))
#define OP8(a) (OPB[(u32)(a)&0x1fffff])
#define OP16(a) (*(const u16*)(OPB+((u32)(a)&0x1fffff)))
#define OP32(a) (*(const u32*)(OPB+((u32)(a)&0x1fffff)))
#define ROM8(o) (*(const u8*)(ROMB+(o)))
#define ROM16(o) (*(const u16*)(ROMB+(o)))
#define ROM32(o) (*(const u32*)(ROMB+(o)))
#define PA(t,a) ((t*)(PAGE[((a)>>16)&0xff]+((a)&0xffff)))
#define RD8(a) (*PA(volatile u8,(u32)(a)))
#define RD16(a) (*PA(volatile u16,(u32)(a)))
#define RD32(a) (*PA(volatile u32,(u32)(a)))
#define WR8(a,v) (*PA(volatile u8,(u32)(a))=(v))
#define WR16(a,v) (*PA(volatile u16,(u32)(a))=(v))
#define WR32(a,v) (*PA(volatile u32,(u32)(a))=(v))
#define RAMW8(o,v) (RAM8(o)=(v))
#define RAMW16(o,v) (RAM16(o)=(v))
#define RAMW32(o,v) (RAM32(o)=(v))
#endif
#define SHL8(o,n) ((n)>=8?0:(u8)((o)<<(n)))
#define SHL16(o,n) ((n)>=16?0:(u16)((o)<<(n)))
#define SHL32(o,n) ((n)>=32?0:((o)<<(n)))
#define SHR8(o,n) ((n)>=8?0:(u8)((o)>>(n)))
#define SHR16(o,n) ((n)>=16?0:(u16)((o)>>(n)))
#define SHR32(o,n) ((n)>=32?0:((o)>>(n)))
#define ASR8(o,n) ((u8)((s8)(o)>>((n)>7?7:(n))))
#define ASR16(o,n) ((u16)((s16)(o)>>((n)>15?15:(n))))
#define ASR32(o,n) ((u32)((s32)(o)>>((n)>31?31:(n))))
#define ROL8(o,n) ((u8)(((o)<<((n)&7))|((o)>>((8-(n))&7))))
#define ROL16(o,n) ((u16)(((o)<<((n)&15))|((o)>>((16-(n))&15))))
#define ROL32(o,n) (((o)<<((n)&31))|((o)>>((32-(n))&31)))
#define ROR8(o,n) ROL8(o,(8-(n))&7)
#define ROR16(o,n) ROL16(o,(16-(n))&15)
#define ROR32(o,n) ROL32(o,(32-(n))&31)
extern u32 f_roxl(u32,int,int,int*);
#define ROXL8(o,n) ((u8)f_roxl(o,n,8,&fx))
#define ROXL16(o,n) ((u16)f_roxl(o,n,16,&fx))
#define ROXL32(o,n) f_roxl(o,n,32,&fx)
#define ROXR8(o,n) ((u8)f_roxl(o,n,-8,&fx))
#define ROXR16(o,n) ((u16)f_roxl(o,n,-16,&fx))
#define ROXR32(o,n) f_roxl(o,n,-32,&fx)
extern u32 f_abcd(u32,u32,int*),f_sbcd(u32,u32,int*);extern u32 f_divu(u32,u32,int*),f_divs(u32,u32,int*);extern void f_dispatch(u32),f_badjump(u32),f_sysreg(void),f_unhandled(u32);
#define DIVU(a,b) f_divu(a,b)
#define DIVS(a,b) f_divs(a,b)
#define BADJUMP(a) f_badjump(a)
#define DISPATCH(a) f_dispatch(a)
extern u32 IOR8(u32),IOR16(u32),IOR32(u32);extern void IOW8(u32,u32),IOW16(u32,u32),IOW32(u32,u32);
#ifdef LIFT_TEST
#define RTE() f_sysreg()
#else
#define RTE() return
#endif
#define SYSREG() f_sysreg()
#define UNHANDLED(a) f_unhandled(a)
#define CCOUT() (R->ccz=fz,R->ccn=fn,R->ccc=fc,R->ccv=fv,R->ccx=fx)
#define CCAFTER() (fz=R->ccz,fn=R->ccn,fc=R->ccc,fv=R->ccv,fx=R->ccx)
#define CARRYA(o,s,v,x) ((u32)(v)<(u32)(o)||(x&&(u32)(v)==(u32)(o)))
#define CARRYS(o,s,v,x) ((u32)(o)<(u32)(s)||(x&&(u32)(o)==(u32)(s)))
"""


def render(fn, code, mode):
    regs = sorted(fn.regs)
    head = f"void f_{fn.entry:x}(void){{int fz=0,fn=0,fc=0,fv=0,fx=0;"
    defs = []
    if mode == "local":
        head += "".join(f"u32 {r}=R->{r[0]}[{r[1]}];" for r in regs)
        wb = "".join(f"R->{r[0]}[{r[1]}]={r};" for r in regs)
        rl = "".join(f"{r}=R->{r[0]}[{r[1]}];" for r in regs)
        text = []
        for c in code:
            c = re.sub(r"(f_[0-9a-z]+\(\);|f_dispatch\([^;]*\);|DISPATCH\([^;]*\);)", lambda m: wb + m[1] + rl, c)
            c = c.replace("return;", wb + "return;")
            text.append(c)
        code = text
    else:
        for r in regs:
            defs.append(f"#define {r} (R->{r[0]}[{r[1]}])")
    und = [f"#undef {r}" for r in regs] if mode != "local" else []
    return "\n".join(defs + [head] + code + ["}"] + und) + "\n"


def main():
    out = pathlib.Path(_argv[1])
    mode = _argv[2]
    addrs = _argv[3:]
    if addrs and addrs[0].startswith("@"):
        addrs = pathlib.Path(addrs[0][1:]).read_text().split()
    addrs = [int(a, 16) for a in addrs if int(a, 16) not in NATIVE] or sorted(FUNCS - NATIVE)
    out.mkdir(parents=True, exist_ok=True)
    ccret = cc_return_set()
    calls = set()
    text = []
    for a in addrs:
        fn, code = lift(a, ccret, mode)
        t = render(fn, code, mode)
        # A 68000 branch to an odd address is an address error, never a function: such targets come from data decoded as code.
        t = re.sub(r"(?<![0-9a-zA-Z_])f_([0-9a-f]*[13579bdf])[(][)];", lambda m: f"UNHANDLED(0x{m[1]});", t)
        calls |= set(re.findall(r"\bf_([0-9a-f]+)\(\)", t))
        calls |= set(re.findall(r"\bf_(trap\d+)\(\)", t))
        text.append(t)
    decl = "".join(f"extern void f_{c}(void);\n" for c in sorted(calls))
    (out / f"lifted_{mode}.c").write_text(HEADER + decl + "".join(text))
    stats["functions"] = len(addrs)
    stats["cc_return_funcs"] = len(ccret)
    (out / f"aborts_{mode}.txt").write_text(" ".join(f"{a:x}" for a in sorted(ABORTS)))
    json.dump(dict(stats=stats, unhandled=unh.most_common()), open(out / f"stats_{mode}.json", "w"), indent=0)
    print(dict(stats), unh.most_common(15))


if __name__ == "__main__":
    main()
