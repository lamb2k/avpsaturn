#!/usr/bin/env python3
"""Tests for tools/align_gate.py, align_packs.py and ymir_misalign_gate.py: each control must be caught (a misaligned object, an unreviewed cast, an odd accessor offset, a misaligned
spill segment, a data line in the Ymir log) and the clean forms must pass. usage: python tests/align_gate_test.py"""
import argparse, pathlib, struct, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import align_gate as g, align_packs as ap, ymir_misalign_gate as yg

fails = 0
def expect(name, got, want):
    global fails
    ok = bool(got) == want
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  <-- got {got}"))
    fails += (not ok)

def repo_with(text, rel="saturn/rt/x.c"):
    d = pathlib.Path(tempfile.mkdtemp()); (d / "saturn" / "rt").mkdir(parents=True)
    (d / rel).write_text(text)
    return d

# offsets: be32(p + 6) and put16(p + 3) fail, be32(p + 8) and be16(p + 2) pass, a product inside parentheses is not an offset
for name, src, bad in (("be32 at +6", "u32 f(u8*p){return be32(p + 6);}", True), ("put16 at +3", "void f(u8*p){put16(p + 3, 1);}", True),
                       ("be32 at +8", "u32 f(u8*p){return be32(p + 8);}", False), ("be16 at +2", "u16 f(u8*p){return be16(p + 2);}", False),
                       ("be32 with (x + 58) * 32", "u32 f(u8*p){return be32(p + (SAT + 58) * 32 + n);}", False)):
    h = []; g.check_offsets(argparse.Namespace(repo=str(repo_with(src))), h)
    expect("offsets: " + name, h, bad)

# cast sites: an unreviewed cast fails, a reviewed one (by line hash) passes, a literal hardware address and the address of a typed object are skipped
src = "void f(u8*p){ u32 *q = (u32 *)p; }\nvoid h(void){ *(volatile u32 *)0x25fe0000 = 1; }\nvoid k(u32 v){ *(volatile u32 *)&v = 1; }\n"
r = repo_with(src)
lines = g.site_lines(r)
expect("sites: only the byte pointer cast is a site", len(lines) == 1, True)
a = argparse.Namespace(repo=str(r), sites=str(r / "none.txt")); h = []; g.check_sites(a, h)
expect("sites: unreviewed cast fails", h, True)
(r / "ok.txt").write_text(lines[0][3] + " reviewed: p is 4 aligned\n")
a = argparse.Namespace(repo=str(r), sites=str(r / "ok.txt")); h = []; g.check_sites(a, h)
expect("sites: reviewed cast passes", h, False)
(r / "saturn/rt/x.c").write_text(src.replace("(u32 *)p", "(u32 *)(p + 2)"))
h = []; g.check_sites(a, h)
expect("sites: an edited line needs a new review", h, True)

# round file: a spill segment at 2 mod 4 and an odd region destination are caught, an aligned one passes
def round_file(path, spill_rel, dest_pack=0x02654000, dest_spill=0x02400000):
    head_pack = struct.pack(">I", 0x53475033) + struct.pack(">III", 0, 120, 120) * 4
    head_pack += struct.pack(">II", 0xffffffff, 0) * 4
    head_pack = head_pack.ljust(84, b"\0") + struct.pack(">II", 120, 124)
    head_pack = head_pack.ljust(104, b"\0") + struct.pack(">I", 0)
    head_pack = head_pack.ljust(120, b"\0")
    tab = struct.pack(">I", 1) + struct.pack(">II", 5, spill_rel & 0xffffffff)
    # tail entry of section 0 points at the spill table
    pack = bytearray(head_pack); pack[52 + 4:52 + 8] = struct.pack(">I", 120)
    pack += tab
    pack = bytes(pack).ljust(2048, b"\0")
    regs = [(dest_pack, 2048, b"\0" * 2048), (dest_pack, 2048, pack)]
    head = struct.pack(">I", len(regs)) + b"".join(struct.pack(">II", d, n) for d, n, _ in regs)
    path.write_bytes(head.ljust(2048, b"\0") + b"".join(b for _, _, b in regs))
d = pathlib.Path(tempfile.mkdtemp()); (d / "disc").mkdir()
round_file(d / "disc" / "R001.BIN", 0x02400000 - 0x02654000 + 0x1000)
h = []; ap.check(d, h, pack_addr=0x02654000)
expect("round file: aligned spill passes", h, False)
round_file(d / "disc" / "R001.BIN", 0x02400000 - 0x02654000 + 0x1002)
h = []; ap.check(d, h, pack_addr=0x02654000)
expect("round file: spill at 2 mod 4 fails", h, True)

# Ymir log: instruction fetch artefacts pass, a data access fails
log = pathlib.Path(tempfile.mkdtemp()) / "m.log"
log.write_text("READ SH2-M PC=060A128E addr=060A128E 32-bit\nREAD SH2-S PC=00203682 addr=00203682 32-bit\n")
expect("ymir log: fetch artefacts only passes", yg.check(str(log)), False)
log.write_text("READ SH2-M PC=060A128E addr=060A128E 32-bit\nREAD SH2-S PC=027F1234 addr=027F6D86 32-bit\n")
expect("ymir log: a data access fails", yg.check(str(log)), True)

print("FAILED" if fails else "all passed", fails)
sys.exit(1 if fails else 0)
