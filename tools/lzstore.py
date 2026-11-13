#!/usr/bin/env python
"""Compressed round files and boot files (SAT_LOAD_LZ, lane loading 2026-11-12). Used by tools/sector_store.py (rounds) and saturn/rt/build.py (boot files) when SAT_LOAD_LZ=1.
Codec: raw deflate (zlib level 9), decoded by saturn/rt/lzdec.h in the loader. Chosen by measurement (docs/notes/AVP_LOADING_LZ_20261112.md): on the shipped round files a byte-LZ (LZ4, LZSS) gives
0.79 to 0.87, order-0 Huffman 0.72, deflate 0.65 per 2 KB (0.64 per 64 KB); LW 0.57, ROM 0.46 per 8 KB.

ROUND FILES. A round file is a head sector (u32 region count, then (dest, bytes) pairs; dest 1 = the mark) followed by the regions' bytes. The tile region (the first region after the mark that is
larger than 64 sectors) is taken out of the stream and stored as compressed BLOCKS in a blob area of STORE.BIN; the head sector gets bit 0 of that region's byte count set and, at byte 1024, the unit table:
    u32 'LZ01', raw_total (bytes of the region), T (bytes at the end of the region the loader copies to scratch before decoding), nblk, then nblk pairs (raw bytes, compressed bytes), then nblk u32
    blob sectors (relative to the blob area; STORE.BIN header word at 8 + 8 * rounds gives the blob area's first sector).
Blocks are the distinct runs of the (deduplicated) tile data, so the sharing between the variants of a stage survives, compressed once. Each blob is padded to whole sectors. The loader reads a unit's blobs
into the END of the region's destination and decodes forward in place. T and the placement are proven per file by running the loader's own lz_unit (saturn/rt/lzdec.h, host DLL) on a buffer laid out
exactly like the loader's; a file whose tile region does not decode exactly, or does not fit, keeps its tile region in the plain stream.
BOOT FILES. A file of 'LZB1', raw_total, T, nblk, then nblk pairs (raw, compressed) in the first sector, then each block's stream padded to whole sectors; 32 KB raw blocks, in place at the end of the file's
destination, same proof."""
import ctypes, hashlib, os, pathlib, struct, subprocess, sys, zlib

SEC = 2048
HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
TMAX = 8192          # scratch bytes the loader keeps for the tail (boot.c lz_scr)
COAL = 64            # sectors: regions up to this size are 'tiny' (boot.c COAL_MAX)
MAGIC_LZ, MAGIC_LZB = 0x4c5a3031, 0x4c5a4231
_dll = None


def dll():
    global _dll
    if _dll:
        return _dll
    out = pathlib.Path(os.environ.get("LZ_DLL_DIR", HERE / "__lzbuild__")); out.mkdir(exist_ok=True)
    so = out / "lzhost.dll"
    src = [REPO / "tools/loading/lzhost.c", REPO / "saturn/rt/lzdec.h"]
    if not so.exists() or so.stat().st_mtime < max(p.stat().st_mtime for p in src):
        bat = out / "b.bat"
        bat.write_text(f'@echo off\r\ncall C:\\BuildTools\\VS2022\\VC\\Auxiliary\\Build\\vcvars64.bat >nul\r\ncd /d {out}\r\ncl /nologo /O2 /LD {REPO / "tools/loading/lzhost.c"} /I {REPO / "saturn/rt"} /Fe:{so} > b.log 2>&1\r\n')
        subprocess.run(["cmd", "/c", str(bat)], check=False)
        if not so.exists():
            raise SystemExit("lzstore: host DLL build failed (see " + str(out / "b.log") + ")")
    d = ctypes.CDLL(str(so))
    d.lz_host_inflate.restype = ctypes.c_long
    d.lz_host_inflate.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_ulong]
    d.lz_host_unit.restype = ctypes.c_int
    d.lz_host_unit.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong]
    _dll = d
    return d


def deflate(raw, strat=zlib.Z_DEFAULT_STRATEGY):
    co = zlib.compressobj(9, zlib.DEFLATED, -15, 9, strat)
    return co.compress(raw) + co.flush()


def pad(n):
    return (n + SEC - 1) // SEC * SEC


def place_and_check(raw, blocks):
    """blocks: list of (raw_bytes_k, stream_k). Finds the smallest tail T (bytes at the end of the region, at most TMAX) for which the loader's lz_unit decodes in place exactly; returns T or None."""
    total = len(raw)
    padded = sum(pad(len(s)) for _, s in blocks)
    if padded > total or total == 0:
        return None
    d = dll()
    blk = (ctypes.c_ulong * (2 * len(blocks)))()
    for k, (r, s) in enumerate(blocks):
        blk[2 * k] = r; blk[2 * k + 1] = len(s)
    tails = [t for t in (0, 512, 1024, 1536, 2048, 3072, 4096, 5120, 6144, 7168, 8192) if t <= TMAX]
    for T in tails:
        buf = ctypes.create_string_buffer(total + 16)
        ctypes.memset(buf, 0xAA, total)
        off = total - padded
        for _, s in blocks:
            ctypes.memmove(ctypes.addressof(buf) + off, s, len(s)); off += pad(len(s))
        r = d.lz_host_unit(buf, total, len(blocks), blk, T)
        if r == 0 and buf.raw[:total] == raw:
            return T
    return None


def dedup_pool(streams, dup):
    """The deduplicating layout of sector_store.build for a list of byte strings: (data sectors, per-stream runs [[q, n]] relative to the data start)."""
    data, where, rounds = [], {}, []
    CMAX = (1 << 14) - 1
    for b in streams:
        assert len(b) % SEC == 0
        h = [hashlib.blake2b(b[o:o + SEC], digest_size=16).digest() for o in range(0, len(b), SEC)]
        runs, i = [], 0

        def add(q, n):
            if runs and runs[-1][0] + runs[-1][1] == q and runs[-1][1] + n <= CMAX:
                runs[-1][1] += n
            else:
                runs.append([q, n])
        while i < len(h):
            j = i + 1
            if h[i] in where:
                while j < len(h) and h[j] in where and where[h[j]] == where[h[j - 1]] + 1:
                    j += 1
                if j - i > dup:
                    add(where[h[i]], j - i); i = j; continue
            else:
                while j < len(h) and h[j] not in where:
                    j += 1
            for k in range(i, j):
                where[h[k]] = len(data); data.append(b[k * SEC:(k + 1) * SEC]); add(len(data) - 1, 1)
            i = j
        rounds.append(runs)
    return data, rounds


def split_round(b):
    cnt = struct.unpack_from(">I", b)[0]
    regs = [list(struct.unpack_from(">II", b, 4 + 8 * i)) for i in range(cnt)]
    off, offs = SEC, []
    for d, n in regs:
        offs.append(off)
        if d != 1:
            off += n
    return regs, offs


def tile_index(regs):
    if len(regs) < 3 or regs[0][0] == 1 or regs[1][0] != 1 or regs[0][1] < 65536:
        return None
    for i in range(2, len(regs)):
        if regs[i][0] != 1 and regs[i][1] // SEC > COAL and regs[i][0] % 4 == 0 and regs[i][1] % SEC == 0:
            return i
    return None


def build_lz(files, dup=512):
    """files: round files (bytes). Returns (STORE.BIN bytes, info). Layout: header sector(s) as sector_store (+ one word: blob area start sector at 8 + 8 * rounds), run table, pool data, blob area."""
    n = len(files)
    parts = []
    for b in files:
        regs, offs = split_round(b)
        t = tile_index(regs)
        parts.append((regs, offs, t))
    # tile data of every file with a tile region, deduplicated into a tile pool; blocks = distinct runs
    tiles = {}
    for i, (b, (regs, offs, t)) in enumerate(zip(files, parts)):
        if t is not None:
            tiles[i] = b[offs[t]:offs[t] + regs[t][1]]
    order = sorted(tiles)
    pool, truns = dedup_pool([tiles[i] for i in order], 0)   # no in-line copies: a blob is read once per load either way
    # atomic segments: cut the tile pool at every place any file's run starts or ends, so each pool sector is compressed once and a run is a list of segments (more blocks per file, none twice)
    cuts = set()
    for runs in truns:
        for q, c in runs:
            cuts.add(q); cuts.add(q + c)
    cuts = sorted(cuts)
    import bisect
    def segments(q, c):
        i = bisect.bisect_left(cuts, q); out = []
        while cuts[i] < q + c:
            out.append((cuts[i], cuts[i + 1] - cuts[i])); i += 1
        return out
    PIECE = int(os.environ.get("LZ_PIECE", "32"))   # sectors of raw data per stream at most: the loader decodes a stream as soon as it has arrived, while the next ones are still being read
    def pieces(q, c):
        return [(q + o, min(PIECE, c - o)) for o in range(0, c, PIECE)]
    truns = [[list(pc) for q, c in runs for sg in segments(q, c) for pc in pieces(*sg)] for runs in truns]
    blocks = {}
    for ri, runs in zip(order, truns):
        for q, c in runs:
            if (q, c) not in blocks:
                raw = b"".join(pool[q:q + c])
                z = deflate(raw)
                if len(z) >= len(raw):
                    z = deflate(raw, zlib.Z_FIXED)   # any valid stream: a stored block when nothing is gained
                    co = zlib.compressobj(0, zlib.DEFLATED, -15); z = co.compress(raw) + co.flush()
                blocks[(q, c)] = (len(raw), z)
    # blob area: each distinct block once, sector aligned, in order of first use
    blob_off, blob_data, blob_sec = {}, [], 0
    for ri, runs in zip(order, truns):
        for key in runs:
            key = tuple(key)
            if key not in blob_off:
                z = blocks[key][1]; blob_off[key] = blob_sec
                blob_data.append(z + bytes(pad(len(z)) - len(z))); blob_sec += pad(len(z)) // SEC
    # per file: proof of the in-place decode; a file that fails keeps its tile region in the stream
    use_lz = {}
    for ri, runs in zip(order, truns):
        bl = [(blocks[tuple(r)][0], blocks[tuple(r)][1]) for r in runs]
        T = place_and_check(tiles[ri], bl)
        if T is not None:
            use_lz[ri] = (runs, T)
    streams = []
    for i, (b, (regs, offs, t)) in enumerate(zip(files, parts)):
        if i in use_lz:
            runs, T = use_lz[i]
            head = bytearray(b[:SEC])
            struct.pack_into(">I", head, 4 + 8 * t + 4, regs[t][1] | 1)
            info = [MAGIC_LZ, regs[t][1], T, len(runs)]
            for r in runs:
                bl = blocks[tuple(r)]
                info += [bl[0], len(bl[1])]
            info += [blob_off[tuple(r)] for r in runs]
            assert 4 * len(info) <= SEC - 1024
            struct.pack_into(">%dI" % len(info), head, 1024, *info)
            body = b[SEC:offs[t]] + b[offs[t] + regs[t][1]:]
            streams.append(bytes(head) + body)
        else:
            streams.append(b)
    data, rounds = dedup_pool(streams, dup)
    nruns = sum(len(r) for r in rounds)
    hs = -(-(8 + 8 * n + 4) // SEC)
    if hs > 2:
        raise SystemExit("lz store: too many rounds")
    run_secs = -(-nruns * 4 // SEC)
    base = hs + run_secs
    blob_base = base + len(data)
    if blob_base + blob_sec >= 1 << 18:
        raise SystemExit("lz store: too large")
    head = struct.pack(">II", 0x53535431, n)
    tab, first = bytearray(), 0
    for r in rounds:
        head += struct.pack(">II", first, len(r)); first += len(r)
        for q, c in r:
            tab += struct.pack(">I", (base + q) << 14 | c)
    head += struct.pack(">I", blob_base)
    out = head + bytes(hs * SEC - len(head)) + tab + bytes(run_secs * SEC - len(tab)) + b"".join(data) + b"".join(blob_data)
    info = dict(files=n, lz_files=len(use_lz), raw_files=n - len(use_lz), pool_sectors=len(data), blob_sectors=blob_sec, blocks=len(blocks), store_sectors=len(out) // SEC,
                tail_max=max([t for _, t in use_lz.values()] or [0]), tile_raw_sectors=sum(len(t) // SEC for t in tiles.values()))
    return out, streams, info


def rebuild_stream(store, i):
    """The plain stream of round i from the store (runs as sector_store.rebuild)."""
    magic, n = struct.unpack_from(">II", store)
    first, cnt = struct.unpack_from(">II", store, 8 + 8 * i)
    hs = -(-(8 + 8 * n + 4) // SEC)
    out = bytearray()
    for j in range(first, first + cnt):
        w = struct.unpack_from(">I", store, hs * SEC + 4 * j)[0]
        out += store[(w >> 14) * SEC:((w >> 14) + (w & 0x3fff)) * SEC]
    return bytes(out)


def rebuild_round(store, i):
    """The original round file from the store alone, decoding the tile blocks with zlib (independent of lzdec.h)."""
    magic, n = struct.unpack_from(">II", store)
    blob_base = struct.unpack_from(">I", store, 8 + 8 * n)[0]
    s = rebuild_stream(store, i)
    cnt = struct.unpack_from(">I", s)[0]
    regs = [list(struct.unpack_from(">II", s, 4 + 8 * k)) for k in range(cnt)]
    out = bytearray(s[:SEC]); pos = SEC
    for k, (d, b) in enumerate(regs):
        if d == 1:
            continue
        if b & 1:
            raw_total, T, nblk = struct.unpack_from(">III", s, 1024 + 4)
            pairs = struct.unpack_from(">%dI" % (2 * nblk), s, 1024 + 16)
            secs = struct.unpack_from(">%dI" % nblk, s, 1024 + 16 + 8 * nblk)
            tile = bytearray()
            for j in range(nblk):
                zb = store[(blob_base + secs[j]) * SEC:(blob_base + secs[j]) * SEC + pairs[2 * j + 1]]
                tile += zlib.decompress(zb, -15)
                assert len(tile) == sum(pairs[2 * x] for x in range(j + 1))
            assert len(tile) == raw_total
            out += tile
            b &= ~1
            out[4 + 8 * k + 4:4 + 8 * k + 8] = struct.pack(">I", b)
            out[1024:1024 + 4 * (4 + 3 * nblk)] = bytes(4 * (4 + 3 * nblk))
        else:
            out += s[pos:pos + b]; pos += b
    return bytes(out)


def expected_sum(f):
    """The loader's SAT_LOAD_SUM of a round file (boot.c): sum * 0x9e3779b1 + word over every region's bytes in the list order, read back from the memory the regions were loaded to (final contents, overlaps as loaded)."""
    regs, offs = split_round(f)
    base = 0x02400000
    mem = bytearray(0x400000); pos = SEC
    for d, b in regs:
        if d == 1:
            continue
        mem[d - base:d - base + b] = f[pos:pos + b]; pos += b
    s = 0
    for d, b in regs:
        if d == 1:
            continue
        o = d - base
        for w in struct.unpack(">%dI" % (b // 4), mem[o:o + b]):
            s = (s * 0x9e3779b1 + w) & 0xffffffff
    return s


def compress_boot(raw, blk=32768):
    """Boot file bytes -> compressed file bytes (header sector, streams padded to sectors), or None when it does not pay or the in-place proof fails."""
    raw = raw + bytes(pad(len(raw)) - len(raw))   # the plain loader writes whole sectors: the padding stays zero
    blocks = []
    for p in range(0, len(raw), blk):
        r = raw[p:p + blk]; z = deflate(r)
        if len(z) >= len(r):
            co = zlib.compressobj(0, zlib.DEFLATED, -15); z = co.compress(r) + co.flush()
        blocks.append((len(r), z))
    T = place_and_check(raw, blocks)
    if T is None:
        return None
    hdr = struct.pack(">IIII", MAGIC_LZB, len(raw), T, len(blocks)) + b"".join(struct.pack(">II", r, len(z)) for r, z in blocks)
    assert len(hdr) <= SEC
    out = hdr + bytes(SEC - len(hdr)) + b"".join(z + bytes(pad(len(z)) - len(z)) for _, z in blocks)
    return out if len(out) < len(raw) else None


def main():
    # usage: lzstore.py boot DISC_DIR FILE...   (compress the named boot files of the staged disc in place)
    if sys.argv[1] == "boot":
        disc = pathlib.Path(sys.argv[2])
        for name in sys.argv[3:]:
            p = disc / name; raw = p.read_bytes()
            if raw[:4] == struct.pack('>I', MAGIC_LZB):
                print('lzstore boot', name, 'already compressed'); continue
            z = compress_boot(raw)
            if z is None:
                print("lzstore boot", name, "left plain"); continue
            p.write_bytes(z)
            print("lzstore boot", name, len(raw) // SEC, "->", len(z) // SEC, "sectors", round(len(z) / len(raw), 3))


if __name__ == "__main__":
    main()
