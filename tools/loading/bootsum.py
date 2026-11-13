#!/usr/bin/env python
"""bootsum.py PLAIN_DIR LZ_DIR LZ_RUN_LOG [PLAIN_RUN_LOG]: the boot images in memory against the uncompressed build.

A test build with -DSAT_LOAD_SUM records, for each boot file in load order (COLD1, HW, LW, OPX, ROM), the multiplicative sum (sum * 0x9e3779b1 + word, boot.c SAT_LOAD_SUM) and byte count of the bytes the loader
left at the file's address (sat_ld_diag[8 + 2n], [9 + 2n], boot.c boot_note). A route reads them from the running Ymir (`y:0:20` with GS_SELFTEST=1) and the run log has the PEEK line.
This script checks, per file:
  1. the compressed file on the LZ disc, decoded with zlib alone (the 'LZB1' container: raw_total, tail, nblk, (raw, compressed) pairs, streams padded to sectors), equals the plain file (padded to whole sectors);
  2. the LZ build's sum in memory equals the sum of those bytes (the loader writes whole sectors);
  3. (optional) the plain build's sum in memory equals the sum of the plain file's bytes (it writes the file's exact size).
PLAIN_DIR / LZ_DIR hold the five files as the two builds wrote them (wd/disc/*.BIN). Exit 1 on any difference."""
import sys, struct, zlib

NAMES = ["COLD1", "HW", "LW", "OPX", "ROM"]
M = 0xffffffff


def msum(b):
    b = b[:len(b) // 4 * 4]
    s = 0
    for (w,) in struct.iter_unpack(">I", b):
        s = (s * 0x9e3779b1 + w) & M
    return s


def peek(log):
    for l in open(log, errors="replace"):
        if "PEEK diag[0]" in l:
            w = [int(x, 16) for x in l.split("PEEK diag[0]")[1].split()]
    return [(w[8 + 2 * i], w[9 + 2 * i]) for i in range(5)]


def decode(f):
    if f[:4] != b"LZB1":
        return f
    raw_total, tail, nb = struct.unpack_from(">III", f, 4)
    pairs = struct.unpack_from(">%dI" % (2 * nb), f, 16)
    off, out = 2048, b""
    for k in range(nb):
        r, c = pairs[2 * k], pairs[2 * k + 1]
        out += zlib.decompress(f[off:off + c], -15)[:r]
        off += (c + 2047) // 2048 * 2048
    assert len(out) == raw_total
    return out


def main():
    pd, ld, lzlog = sys.argv[1:4]
    pllog = sys.argv[4] if len(sys.argv) > 4 else None
    lzmem = peek(lzlog); plmem = peek(pllog) if pllog else None
    bad = 0
    for i, n in enumerate(NAMES):
        plain = open(f"{pd}/{n}.BIN", "rb").read(); lzf = open(f"{ld}/{n}.BIN", "rb").read()
        padded = plain + bytes((-len(plain)) % 2048)
        same = decode(lzf) == padded
        okl = lzmem[i] == (msum(padded), len(padded))
        okp = plmem is None or plmem[i] == (msum(plain), len(plain))
        print(f"{n:6s} plain {len(plain):8d} B, on the LZ disc {len(lzf):8d} B ({'LZB1' if lzf[:4] == b'LZB1' else 'plain'}); decoded == plain {same}; LZ memory sum {lzmem[i][0]:08x} over {lzmem[i][1]} B ok {okl}"
              + ("" if plmem is None else f"; plain memory sum {plmem[i][0]:08x} over {plmem[i][1]} B ok {okp}"))
        bad += (not same) + (not okl) + (not okp)
    print("boot images:", "ALL EQUAL" if not bad else f"{bad} DIFFERENCES")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
