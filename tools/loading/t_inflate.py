import ctypes, zlib, os, random, time, sys
dll = ctypes.CDLL('E:/AvP/learning/lane-loading/lz/lzhost.dll')
dll.lz_host_inflate.restype = ctypes.c_long
dll.lz_host_inflate.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_ulong]
def raw(d, level=9, strat=zlib.Z_DEFAULT_STRATEGY):
    co = zlib.compressobj(level, zlib.DEFLATED, -15, 9, strat); return co.compress(d) + co.flush()
def dec(z, n):
    buf = ctypes.create_string_buffer(n + 16); src = z + bytes(8)
    r = dll.lz_host_inflate(src, buf, n); return r, buf.raw[:n]
bad = 0; tot = 0; t0 = time.time()
random.seed(1)
tests = []
tests.append(b''); tests.append(b'a'); tests.append(bytes(range(256)) * 8); tests.append(os.urandom(5000)); tests.append(b'abc' * 3000)
for name in ('R020', 'R286', 'LW', 'ROM', 'HW', 'OPX'):
    d = open(f'samples/{name}.bin', 'rb').read()
    tests.append(d[:200000])
    for p in range(0, min(len(d), 400000), 2048): tests.append(d[p:p + 2048])
    for p in range(0, min(len(d), 400000), 8192 * 3): tests.append(d[p:p + 8192 * 3])
for d in tests:
    for lvl, st in ((9, 0), (6, 0), (1, 0), (9, zlib.Z_HUFFMAN_ONLY), (9, zlib.Z_FIXED), (0, 0)):
        if not d and lvl == 0: continue
        z = raw(d, lvl, st); r, out = dec(z, len(d)); tot += 1
        if r != len(d) or out != d: bad += 1; print('MISMATCH', len(d), lvl, st, r) if bad < 10 else None
print('streams', tot, 'bad', bad, round(time.time() - t0, 1), 's')
