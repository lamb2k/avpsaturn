"""expsum_all.py STORE.BIN : the expected SAT_LOAD_SUM of every round file (final memory of its regions read back in region order, sum = sum * 0x9e3779b1 + word), computed offline from the disc's STORE.BIN"""
import struct, sys, numpy as np
path = sys.argv[1]
st = open(path, 'rb')
magic, n = struct.unpack('>II', st.read(8)); hs = 2 if n > 255 else 1
st.seek(0); hdr = st.read(2048 * hs); tab = hs * 2048
base = 0x02400000
def runlist(i):
    first, cnt = struct.unpack('>II', hdr[8 + 8 * i:16 + 8 * i]); out = []
    for j in range(first, first + cnt):
        st.seek(tab + 4 * j); w = struct.unpack('>I', st.read(4))[0]; out.append((w >> 14, w & 0x3fff))
    return out
K = np.uint32(0x9e3779b1)
res = {}
for r in range(n):
    data = b''.join((st.seek(q * 2048), st.read(c * 2048))[1] for q, c in runlist(r))
    cnt = struct.unpack('>I', data[:4])[0]
    regs = [struct.unpack('>II', data[4 + 8 * i:12 + 8 * i]) for i in range(cnt)]
    mem = bytearray(0x400000); p = 2048
    for d, b in regs:
        if d != 1: mem[d - base:d - base + b] = data[p:p + b]; p += b
    words = []
    for d, b in regs:
        if d == 1: continue
        words.append(np.frombuffer(bytes(mem[d - base:d - base + b]), dtype='>u4').astype(np.uint32))
    w = np.concatenate(words); m = len(w)
    pw = np.empty(m, dtype=np.uint32); pw[-1] = 1
    # powers K^(m-1-i): build by doubling
    pw = np.ones(m, dtype=np.uint32); acc = np.uint32(1)
    # cumulative product from the end
    rev = np.full(m, K, dtype=np.uint32); rev[0] = 1
    pw = np.cumprod(rev, dtype=np.uint32)[::-1]
    s = int(np.sum(w.astype(np.uint64) * pw.astype(np.uint64), dtype=np.uint64)) & 0xffffffff
    res[r] = s
import json
json.dump({str(k): '%08x' % v for k, v in res.items()}, open('E:/AvP/learning/lane-perf-hw/expsum_P9.json', 'w'))
print(n, 'files')
