#!/usr/bin/env python3
"""coalesce_replay.py STORE.BIN [--old] : replays boot.c load_regions (SAT_LOAD_COALESCE) on every round file of a STORE.BIN against a memory model and compares the final memory of
every region with plain sequential loading. --old replays the first version (no coal_big rule), which corrupted the pack room of 157 of 287 files (found 11-12 by this script;
the first SAT_LOAD_SUM was blind to it: a rotating sum cancels where regions overlap). Prints the files that differ. Exit 1 on any."""
import struct, sys
path = sys.argv[1]; old = '--old' in sys.argv
st = open(path, 'rb'); st.seek(0)
magic, n = struct.unpack('>II', st.read(8)); hs = 2 if n > 255 else 1
st.seek(0); hdr = st.read(2048 * hs); tab = hs * 2048
COAL, base = 64, 0x02400000
def runlist(i):
    first, cnt = struct.unpack('>II', hdr[8 + 8 * i:16 + 8 * i]); out = []
    for j in range(first, first + cnt):
        st.seek(tab + 4 * j); w = struct.unpack('>I', st.read(4))[0]; out.append((w >> 14, w & 0x3fff))
    return out
bad = []; grouped = 0
for r in range(n):
    data = b''.join((st.seek(q * 2048), st.read(c * 2048))[1] for q, c in runlist(r))
    cnt = struct.unpack('>I', data[:4])[0]
    regs = [struct.unpack('>II', data[4 + 8 * i:12 + 8 * i]) for i in range(cnt)]
    ref = bytearray(0x400000); mem = bytearray(0x400000); p = 2048
    for d, b in regs:
        if d != 1: ref[d - base:d - base + b] = data[p:p + b]; p += b
    i = 0; p = 2048; big = False
    while i < cnt:
        d, b = regs[i]
        if d == 1: i += 1; continue
        secs = b // 2048
        if i >= 2 and (old or not big) and 0 < secs <= COAL and regs[0][0] != 1 and regs[1][0] == 1 and regs[0][1] >= 65536:
            room = regs[0][1] // 2048; tot = 0; j = i
            while j < cnt and regs[j][0] != 1 and regs[j][0] & 3 == 0 and regs[j][1] % 2048 == 0 and 0 < regs[j][1] // 2048 <= COAL and tot + regs[j][1] // 2048 <= room:
                tot += regs[j][1] // 2048; j += 1
            if j - i >= 2:
                grouped += 1
                stage = regs[0][0]; mem[stage - base:stage - base + tot * 2048] = data[p:p + tot * 2048]; q = 0
                for k in range(i, j):
                    dk, bk = regs[k]; mem[dk - base:dk - base + bk] = mem[stage - base + q:stage - base + q + bk]; q += bk
                p += tot * 2048; i = j; continue
        mem[d - base:d - base + b] = data[p:p + b]; p += b
        if i >= 2 and secs > COAL: big = True
        i += 1
    if any(d != 1 and mem[d - base:d - base + b] != ref[d - base:d - base + b] for d, b in regs): bad.append(r)
print(f'{path}: {n} files, {grouped} staged groups, {len(bad)} files whose final memory differs from sequential loading', bad[:20])
sys.exit(1 if bad else 0)
