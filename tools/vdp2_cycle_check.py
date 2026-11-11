#!/usr/bin/env python3
"""VDP2 VRAM access cycle validator, a build gate (hwboot lane fix7, 2026-11-11).

Checks the VRAM access cycle pattern the game writes (saturn/gfx/sat_vdp2_cfg.h) against Sega's VDP2 User's Manual, chapter 3:
  Table 3.2  pattern name reads per cycle: 1 at 1x, 2 at 1/2 reduction, 4 at 1/4 (NBG0..NBG3, one count per bank that holds the layer's map)
  Table 3.3  character pattern reads per cycle: 16 colours 1 / 2 / 4, 256 colours 2 / 4, 2048 and 32768 colours 4, 16.7 M colours 8 (1x / 1/2 / 1/4)
  Table 3.4  legal character pattern timings for each pattern name timing (normal resolution, 1x1 and 2x2 cells)
  split banks: the CPU command must be set in bank 0 and bank 1 at the same timing, and the timing in front of a CPU run must be no access in both
  pattern name reads in at most two banks, one of A0/B0 and one of A1/B1
Short counts, illegal slots, cells in a bank with no cell read of the layer and broken CPU pairs are errors (exit 1). Extra reads and no CPU slot at all are warnings.
Also: every write of the covered registers elsewhere in saturn/ must use the cfg macros or be listed in tools/vdp2_writers_allow.txt.
usage: vdp2_cycle_check.py [--root DIR] [--cyc A0L,A0U,A1L,A1U,B0L,B0U,B1L,B1U] [--fit 0|1] [--quiet] [--vectors]
  --cyc/--fit check a given word set instead of the cfg (used by the tests); --vectors prints the shipped-game vectors from Ymir's comments (information only).
"""
import argparse, pathlib, re, sys

BANKS = ["A0", "A1", "B0", "B1"]
BANK_BASE = {"A0": 0x00000, "A1": 0x20000, "B0": 0x40000, "B1": 0x60000}
# Table 3.4, normal resolution: character pattern timings allowed for each pattern name timing
LEGAL = {0: {0, 1, 2, 4, 5, 6, 7}, 1: {0, 1, 2, 3, 5, 6, 7}, 2: {0, 1, 2, 3, 6, 7}, 3: {0, 1, 2, 3, 7},
         4: {0, 1, 2, 3}, 5: {1, 2, 3}, 6: {2, 3}, 7: {3}}
CODE_NAME = {0: "N0PN", 1: "N1PN", 2: "N2PN", 3: "N3PN", 4: "N0CG", 5: "N1CG", 6: "N2CG", 7: "N3CG", 0xc: "N0CE", 0xd: "N1CE", 0xe: "CPU", 0xf: "NA"}
COLOUR_COUNT = {16: (1, 2, 4), 256: (2, 4, None), 2048: (4, None, None), 32768: (4, None, None), 16777216: (8, None, None)}


def ev(expr, macros, depth=0):
    expr = re.sub(r"/\*.*?\*/", "", expr).strip()
    for _ in range(8):
        new = re.sub(r"\bSAT_\w+\b", lambda m: "(" + macros[m.group(0)] + ")" if m.group(0) in macros else m.group(0), expr)
        if new == new:
            pass
        if new == expr:
            break
        expr = new
    expr = re.sub(r"(0x[0-9a-fA-F]+|\d+)[uUlL]+", r"\1", expr)
    if not re.fullmatch(r"[0-9a-fA-Fx()+\-*|<>& ]+", expr):
        raise ValueError("cannot evaluate: " + expr)
    return eval(expr, {"__builtins__": {}})


def fit_filtered_macros(cfg_text, fit):
    """Resolve the #if SAT_GFX_FIT == 1 / #else / #endif parts of the cfg for a given fit."""
    out, stack = [], []
    active = True
    for line in cfg_text.splitlines():
        s = line.strip()
        if s.startswith("#ifndef") or s.startswith("#ifdef"):
            stack.append(("plain", active)); out.append(line if active else ""); continue
        m = re.match(r"#if\s+SAT_GFX_FIT\s*==\s*(\d+)", s)
        if m:
            stack.append(("fit", active, int(m.group(1)) == fit)); active = active and (int(m.group(1)) == fit); continue
        if s.startswith("#if"):
            stack.append(("plain", active)); continue
        if s.startswith("#else"):
            if stack and stack[-1][0] == "fit":
                active = stack[-1][1] and not stack[-1][2]
            continue
        if s.startswith("#endif"):
            if stack:
                top = stack.pop()
                active = top[1]
            continue
        if active:
            out.append(line)
    return "\n".join(out)


def words_to_codes(words):
    """words: A0L,A0U,A1L,A1U,B0L,B0U,B1L,B1U -> {bank: [8 codes]} (low word = T0..T3, high = T4..T7, one nibble each, T0 in the top nibble)."""
    codes = {}
    for i, b in enumerate(BANKS):
        lo, hi = words[2 * i], words[2 * i + 1]
        codes[b] = [(lo >> 12) & 15, (lo >> 8) & 15, (lo >> 4) & 15, lo & 15, (hi >> 12) & 15, (hi >> 8) & 15, (hi >> 4) & 15, hi & 15]
    return codes


def banks_of(lo, hi):
    return {b for b in BANKS if lo < BANK_BASE[b] + 0x20000 and hi > BANK_BASE[b]}


def layer_model(cfg, fit_zm, old_layout=False):
    """Per NBG: char size, colours, reduction, map ranges, cell ranges."""
    ev_ = lambda n: ev(n, cfg)
    chctla, chctlb = ev_("SAT_V2_CHCTLA"), ev_("SAT_V2_CHCTLB")
    plsz, pnc = ev_("SAT_V2_PLSZ"), [ev_("SAT_V2_PNC%d" % i) for i in range(4)]
    mp = [(ev_("SAT_V2_MPAB%d" % i), ev_("SAT_V2_MPCD%d" % i)) for i in range(4)]
    layers = []
    for n in range(4):
        ch = chctla if n < 2 else chctlb
        sh = 0 if n % 2 == 0 else 8
        if n < 2:
            big = (ch >> (0 + sh)) & 1; bitmap = (ch >> (1 + sh)) & 1; cc = (ch >> (4 + sh)) & 7
        else:
            big = (ch >> (0 if n == 2 else 4)) & 1; bitmap = 0; cc = (ch >> (1 if n == 2 else 5)) & 1
        colours = {0: 16, 1: 256, 2: 2048, 3: 32768, 4: 16777216}.get(cc, None) if n < 2 else {0: 16, 1: 256}[cc]
        word2 = ((pnc[n] >> 15) & 1) == 0
        page_bytes = (64 * 64 if not big else 32 * 32) * (4 if word2 else 2)
        pages = {0: 1, 1: 2, 2: 2, 3: 4}[(plsz >> (2 * n)) & 3]
        red = 1
        if n < 2:
            hf, qt = (fit_zm >> (0 + 8 * n)) & 1, (fit_zm >> (1 + 8 * n)) & 1
            red = 4 if qt else (2 if hf else 1)
        starts = set()
        regs = mp[n]
        for w in regs:
            for v in (w & 0xff, (w >> 8) & 0xff):
                starts.add((v & ~(pages - 1)) * page_bytes if pages > 1 else v * page_bytes)
        maps = sorted((s, s + pages * page_bytes) for s in starts)
        layers.append(dict(n=n, big=big, colours=colours, bitmap=bitmap, red=red, maps=maps, word2=word2))
    # cell ranges from the cfg layout
    layers[0]["cells"] = [(ev_("SAT_V2_CELL_S2"), ev_("SAT_V2_CLEAR_S2") + 0x80)]
    layers[1]["cells"] = [(ev_("SAT_V2_CELL_S3"), ev_("SAT_V2_CLEAR_S3") + 0x80)]
    layers[2]["cells"] = [(ev_("SAT_V2_CELL_S1"), 0x20000)]
    layers[3]["cells"] = [(ev_("SAT_V2_CELL_S1"), 0x20000)]
    if old_layout:   # fix5/fix6 memory layout: NBG0 map at 0 (A0), its cells 0x20000 to 0x3ffff, scroll 2 and 3 blank names pointing at the scroll 1 slab (A0)
        layers[0]["maps"] = [(0x0000, 0x4000)]
        layers[0]["cells"] = [(0x20000, 0x40000), (0x18000, 0x18080)]
        layers[1]["cells"] = [(0x40000, 0x80000), (0x18000, 0x18080)]
    for L in layers:
        L["req_pn"] = L["red"]
        cnt = COLOUR_COUNT.get(L["colours"])
        idx = {1: 0, 2: 1, 4: 2}[L["red"]]
        L["req_cg"] = cnt[idx] if cnt else None
    return layers


def check(codes, layers, enabled, ramctl, label, errs, warns, info, vcell_ok=False):
    split_a, split_b = bool(ramctl & 0x100), bool(ramctl & 0x200)
    for b, row in codes.items():
        for t, c in enumerate(row):
            if c in (0xc, 0xd) and vcell_ok:
                info.append(f"{label}: {b} T{t} vertical cell scroll read ({CODE_NAME[c]}), not judged")
            elif c in (0xc, 0xd):
                errs.append(f"{label}: {b} T{t} uses vertical cell scroll reads, not modelled")
    bank_list = [b for b in BANKS if not ((b == "A1" and not split_a) or (b == "B1" and not split_b))]
    pn_banks = set()
    for n in sorted(enabled):
        L = layers[n]
        pn_t = {b: [t for t, c in enumerate(codes[b]) if c == n] for b in bank_list}
        cg_t = {b: [t for t, c in enumerate(codes[b]) if c == n + 4] for b in bank_list}
        mbanks = set()
        for lo, hi in L["maps"]:
            mbanks |= banks_of(lo, hi)
        cbanks = set()
        for lo, hi in L["cells"]:
            cbanks |= banks_of(lo, hi)
        if not split_a:
            mbanks = {"A0" if b in ("A0", "A1") else b for b in mbanks}; cbanks = {"A0" if b in ("A0", "A1") else b for b in cbanks}
        if not split_b:
            mbanks = {"B0" if b in ("B0", "B1") else b for b in mbanks}; cbanks = {"B0" if b in ("B0", "B1") else b for b in cbanks}
        if L["req_cg"] is None:
            errs.append(f"{label}: NBG{n} {L['colours']} colours at 1/{L['red']} reduction is not allowed (Table 3.3)")
            continue
        if L["red"] == 2 and L["colours"] > 256:
            errs.append(f"{label}: NBG{n} 1/2 reduction allows at most 256 colours")
        for b in sorted(mbanks):
            k = len(pn_t[b])
            if k < L["req_pn"]:
                errs.append(f"{label}: NBG{n} has {k} pattern name read(s) in {b} where its map lives, Table 3.2 needs {L['req_pn']}")
            elif k > L["req_pn"]:
                warns.append(f"{label}: NBG{n} has {k} pattern name reads in {b}, {L['req_pn']} needed")
        for b in bank_list:
            if pn_t[b] and b not in mbanks:
                warns.append(f"{label}: NBG{n} has pattern name reads in {b} where it has no map")
            if pn_t[b]:
                pn_banks.add(b)
        for b in sorted(cbanks):
            k = len(cg_t[b])
            if k < L["req_cg"]:
                errs.append(f"{label}: NBG{n} has {k} cell read(s) in {b} where its cells live, Table 3.3 needs {L['req_cg']}")
            elif k > L["req_cg"]:
                warns.append(f"{label}: NBG{n} has {k} cell reads in {b}, {L['req_cg']} needed")
        for b in bank_list:
            if cg_t[b] and b not in cbanks:
                warns.append(f"{label}: NBG{n} has cell reads in {b} where it has no cells")
        all_pn = sorted({t for b in bank_list for t in pn_t[b]})
        all_cg = sorted({t for b in bank_list for t in cg_t[b]})
        if not (n < 2 and 0 in all_pn):   # Table 3.4 page text: NBG0/NBG1 names at T0 put no limit on cell timings
            for p in all_pn:
                for c in all_cg:
                    if c not in LEGAL[p]:
                        errs.append(f"{label}: NBG{n} cell read at T{c} is not allowed with a name read at T{p} (Table 3.4)")
    for pair, split in ((("A0", "A1"), split_a), (("B0", "B1"), split_b)):
        b0, b1 = pair
        if split:
            for t in range(8):
                c0, c1 = codes[b0][t], codes[b1][t]
                if (c0 == 0xe) != (c1 == 0xe):
                    errs.append(f"{label}: CPU read/write at T{t} in only one of {b0}/{b1}; split banks need it in both")
            cpu = [t for t in range(8) if codes[b0][t] == 0xe and codes[b1][t] == 0xe]
            for t in cpu:
                if (t - 1) % 8 in cpu:
                    continue   # inside a run: only the first needs the no access slot in front
                pt = (t - 1) % 8
                if not (codes[b0][pt] == 0xf and codes[b1][pt] == 0xf):
                    errs.append(f"{label}: CPU run at T{t} of {b0}/{b1} is not preceded by no access in both banks (T{pt} is {CODE_NAME.get(codes[b0][pt])}/{CODE_NAME.get(codes[b1][pt])})")
        else:
            cpu = [t for t in range(8) if codes[b0][t] == 0xe]
            for t in cpu:
                if (t - 1) % 8 not in cpu and codes[b0][(t - 1) % 8] != 0xf:
                    errs.append(f"{label}: CPU run at T{t} of {b0} is not preceded by no access")
        if not cpu:
            warns.append(f"{label}: no CPU slot in {b0}/{b1}: SH-2 writes to that VRAM can only finish in the blanking periods")
        else:
            info.append(f"{label}: CPU slots {b0}/{b1}: T{','.join(map(str, cpu))}")
    for b in pn_banks:
        pass
    if ("A0" in pn_banks and "B0" in pn_banks) or ("A1" in pn_banks and "B1" in pn_banks):
        errs.append(f"{label}: pattern name reads in both {sorted(pn_banks)}: only one of A0/B0 and one of A1/B1 allowed")


def run_check(root, words_override=None, fit_override=None, quiet=False, old_layout=False):
    cfg_path = root / "saturn" / "gfx" / "sat_vdp2_cfg.h"
    text = cfg_path.read_text(encoding="utf-8", errors="replace")
    errs, warns, info = [], [], []
    fits = [fit_override] if fit_override is not None else [1, 0]
    for fit in fits:
        cfg = parse_cfg_text(fit_filtered_macros(text, fit))
        zm = ev("SAT_V2_ZMCTL", cfg)
        if (zm == 0x0101) != (fit == 1):
            errs.append(f"fit {fit}: ZMCTL {zm:#06x} does not match the fit")
        words = words_override or [ev(f"SAT_CYC_{b}", cfg) for b in ("A0L", "A0U", "A1L", "A1U", "B0L", "B0U", "B1L", "B1U")]
        ramctl = ev("SAT_V2_RAMCTL", cfg)
        if ramctl != 0x1300:
            errs.append(f"fit {fit}: RAMCTL {ramctl:#06x}, the checker models 0x1300 (both banks split, CRAM mode 1)")
        layers = layer_model(cfg, zm, old_layout)
        codes = words_to_codes(words)
        for label, enabled in ((f"fit{fit} play (NBG0-2)", {0, 1, 2}), (f"fit{fit} menus/readout (NBG0-3)", {0, 1, 2, 3})):
            check(codes, layers, enabled, ramctl, label, errs, warns, info)
        # the boot display: no layer reads VRAM; the diag cycles are all no access
    return errs, warns, info


def check_reveal(root):
    """The post-credits reveal (saturn/rt/reveal.c) owns the screen with one NBG0 bitmap, 512 x 256, 256 colours, half reduction when the fit is on: no names, Table 3.3 needs 4 cell reads
    in each bank that holds the bitmap (frames at A1 0x20000 and B0 0x40000). The source sets 0x4444 in A1, B0 and B1 (8 reads each): more than needed, which shipped games also do for bitmaps
    (Ymir's CalcAccessPatterns cases 5 and 6, real consoles). Reported as a warning; the check only makes sure that source still looks like that, so a change gets reviewed."""
    errs, warns = [], []
    p = root / "saturn" / "rt" / "reveal.c"
    if not p.exists():
        return errs, warns
    t = p.read_text(encoding="utf-8", errors="replace")
    if "V2(0x10) = 0xffff; V2(0x12) = 0xffff;" not in t or "for (i = 0x14; i <= 0x1e; i += 2) V2(i) = 0x4444;" not in t or "V2(0x28) = 0x0012;" not in t:
        errs.append("reveal.c: the reveal screen's access cycles changed; update check_reveal in tools/vdp2_cycle_check.py after reviewing them against Tables 3.2 to 3.4")
    else:
        warns.append("reveal screen: NBG0 256 colour bitmap at 1/2 reduction has 8 cell reads per bank (4 needed): extra reads, tolerated by shipped games")
    return errs, warns


def parse_cfg_text(t):
    macros = {}
    for line in t.splitlines():
        m = re.match(r"\s*#define\s+(SAT_\w+)\s+(.+?)\s*(?:/\*.*)?$", line)
        if m and "(" not in m.group(1):
            macros[m.group(1)] = m.group(2).strip()
    return macros


WATCH = {0x0e, 0x10, 0x12, 0x14, 0x16, 0x18, 0x1a, 0x1c, 0x1e, 0x28, 0x2a, 0x30, 0x32, 0x34, 0x36, 0x3a, 0x40, 0x42, 0x44, 0x46, 0x48, 0x4a, 0x4c, 0x4e, 0x98}
WRITE_RX = re.compile(r"\b(?:VDP2R|VDP2L|V2R|V2|sat_gfx_vdp2_latch)\(\s*(0x[0-9a-fA-F]+)\s*(?:\)\s*=\s*([^;]+);|,\s*([^;]+)\);)")


def scan_writers(root, allow):
    problems, seen = [], 0
    for path in sorted((root / "saturn").rglob("*.[ch]")):
        rel = path.relative_to(root).as_posix()
        skip_depth, in_skip, depth = 0, False, 0
        for no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            s = line.strip()
            if s.startswith("#if"):
                depth += 1
                if s.startswith("#ifdef AVP_CYC_DIAG") and not in_skip:
                    in_skip, skip_depth = True, depth
            elif s.startswith("#endif"):
                if in_skip and depth == skip_depth:
                    in_skip = False
                depth -= 1
            if in_skip:
                continue
            for m in WRITE_RX.finditer(line):
                off = int(m.group(1), 16)
                if off not in WATCH:
                    continue
                rhs = (m.group(2) or m.group(3) or "").strip()
                seen += 1
                if re.search(r"\bSAT_(CYC|V2)_\w+", rhs):
                    continue
                if any(rel == a[0] and a[1] in line for a in allow):
                    continue
                problems.append(f"{rel}:{no}: write of VDP2 {off:#05x} = {rhs} is not a cfg macro and not in vdp2_writers_allow.txt")
    return problems, seen


def load_allow(root):
    allow = []
    p = root / "tools" / "vdp2_writers_allow.txt"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                f = [x.strip() for x in line.split("|")]
                if len(f) >= 3:
                    allow.append(f)
    return allow


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(pathlib.Path(__file__).resolve().parents[1]))
    ap.add_argument("--cyc")
    ap.add_argument("--fit", type=int)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--old-layout", action="store_true", help="the fix5/fix6 memory layout (NBG0 map in A0), for the words that ran on the console")
    a = ap.parse_args()
    root = pathlib.Path(a.root)
    words = [int(x, 16) for x in a.cyc.split(",")] if a.cyc else None
    if words and len(words) != 8:
        print("need 8 words"); return 2
    errs, warns, info = run_check(root, words, a.fit, old_layout=a.old_layout)
    wp = []
    if not words:
        wp, seen = scan_writers(root, load_allow(root))
        info.append(f"register writers scanned: {seen} covered writes")
    errs += wp
    if not words:
        re_, rw_ = check_reveal(root)
        errs += re_; warns += rw_
    for e in errs:
        print("ERROR", e)
    if not a.quiet:
        for w in warns:
            print("warning", w)
        for i in info:
            print("info", i)
    print("vdp2_cycle_check:", "FAIL (%d errors)" % len(errs) if errs else "PASS")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
