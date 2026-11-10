#!/usr/bin/env python
"""Lane rounds: one disc file per stage word: sound set, then ROM restores, then tile pack, as regions the loader reads in order (saturn/rt/boot.c).
Pack format: tools/satgfx_pack.py; sprites fill the main part on the cart, then continue in ROM stretches this stage, the next stage and the front end do not read, through a table in the pack.
A stretch overwritten by any file is restored by every file whose stage reads it, so what any stage reads is always the ROM's bytes.
ROM-derived output: stays under E:/AvP/learning."""
import bisect, pathlib, struct, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import satgfx_pack
SEC = 2048
HEAD = 4 + 12 * 4 + 8 * 4
ROMB = 0x02400000


def sectors(b):
    return bytes(b) + bytes(-len(b) % SEC)


def seg_len(p, i):
    """Bytes of spill segment i of a plan."""
    return p["seg_bytes"][i] if p.get("rowtrim") else p["segs"][i][2] * 128


def plan_rowtrim(key, tile, secs, main_room, free):
    """SGP2: the sprite tiles are records of 4 + 8 n bytes (satgfx_pack.record). Same shape as plan(): the first payloads in main, the rest in the free runs, whole sectors."""
    t0, sizes, off = tile[0], [], 0
    while off < len(t0):
        size = 4 + 8 * bin(struct.unpack_from(">H", t0, off)[0]).count("1")
        sizes.append(size); off += size
    pos = [0]
    for s in sizes:
        pos.append(pos[-1] + s)
    n_tiles = len(sizes)
    # header (the 84 bytes, 8 for the two offset table pointers), key tables, spill table, the two offset tables, scroll tiles, 4 byte alignment slack
    fixed = HEAD + 8 + sum(len(k) for k in key) + sum((len(tile[i]) + 3) & ~3 for i in (1, 2, 3)) + (((n_tiles + 1023) >> 10) << 2) + ((n_tiles * 2 + 3) & ~3) + 16
    segs, seg_bytes = [], []
    for tries in range(len(free) + 1):
        room = main_room - fixed - 4 - 8 * tries
        if room < 0:
            return None
        inmain = bisect.bisect_right(pos, room) - 1
        inmain = min(inmain, n_tiles)
        segs, seg_bytes, first = [], [], inmain
        for r in free:
            if first >= n_tiles:
                break
            a, n = r[0], r[1]
            cap = n if len(r) > 2 and r[2] else n & -SEC
            last = bisect.bisect_right(pos, pos[first] + cap) - 1
            last = min(last, n_tiles)
            if last > first:
                segs.append((first, a, last - first)); seg_bytes.append(pos[last] - pos[first]); first = last
        if first < n_tiles:
            return None
        if len(segs) <= tries:
            break
    else:
        return None
    return dict(key=key, tile=tile, secs=secs, inmain=inmain, segs=segs, rowtrim=True, pos=pos, seg_bytes=seg_bytes, n_tiles=n_tiles)


def plan(raw, keys, main_room, free, rowtrim=False):
    """Returns (pack parts) or None if over. free: [[rom offset, bytes]] for this stage, in order of use."""
    try:
        data, _ = satgfx_pack.pack(raw, keys, rowtrim)
    except AssertionError:   # past the payload index of a section
        return None
    secs = [struct.unpack_from(">III", data, 4 + i * 12) for i in range(4)]
    ends = [secs[i + 1][1] if i < 3 else len(data) for i in range(4)]
    tile = [data[secs[i][2]:ends[i]] for i in range(4)]
    key = [data[secs[i][1]:secs[i][2]] for i in range(4)]
    if rowtrim:
        return plan_rowtrim(key, tile, secs, main_room, free)
    fixed = HEAD + sum(len(k) for k in key) + sum((len(tile[i]) + 3) & ~3 for i in (1, 2, 3))
    n_tiles = len(tile[0]) // 128
    # room in main, keeping 8 bytes of table per stretch
    segs, left = [], None
    for tries in range(len(free) + 1):
        room = main_room - fixed - 4 - 8 * tries
        if room < 0:
            return None
        inmain = min(n_tiles, room // 128)
        left = n_tiles - inmain
        segs, need, first = [], left, inmain
        for r in free:
            if not need:
                break
            a, n = r[0], r[1]
            # whole sectors: the loader pads a region to a sector, which must stay in the stretch. A run that ends in a page the file keeps may spill 1 KB into it
            # (r[2]): assemble() fills that tail with the ROM's own bytes for the page, which the file needs there anyway.
            take = min(need, (n if len(r) > 2 and r[2] else n & -SEC) // 128)
            if take:
                segs.append((first, a, take)); first += take; need -= take
        if need:
            return None
        if len(segs) <= tries:
            break
    else:
        return None
    return dict(key=key, tile=tile, secs=secs, inmain=inmain, segs=segs)


def assemble(p, pack_addr, rom=None):
    """rom: the ROM image (offsets as the free runs). A spill region is padded to its sector with the ROM's bytes after it, not zeros: where the sector reaches into
    the page after a run, that page holds what the file keeps there."""
    if p.get("rowtrim"):
        return assemble_rowtrim(p, pack_addr, rom)
    key, tile, secs, inmain, segs = p["key"], p["tile"], p["secs"], p["inmain"], p["segs"]
    main = bytearray(HEAD)
    keyoff = []
    for k in key:
        keyoff.append(len(main)); main += k
    table = len(main)
    main += struct.pack(">I", len(segs))
    for first, a, take in segs:
        main += struct.pack(">II", first, (ROMB + a - pack_addr) & 0xffffffff)
    at = {}
    for i in (1, 2, 3):
        main += bytes(-len(main) % 4)
        at[i] = len(main); main += tile[i]
    main += bytes(-len(main) % 4)
    at[0] = len(main); main += tile[0][:inmain * 128]
    hdr, tail = [struct.pack(">I", 0x53475031)], []
    for i in range(4):
        hdr.append(struct.pack(">III", secs[i][0], keyoff[i], at[i]))
        tail.append(struct.pack(">II", inmain if i == 0 else 0xffffffff, table if i == 0 else 0))
    main[:HEAD] = b"".join(hdr) + b"".join(tail)
    regions = [(pack_addr, bytes(main))]
    off = inmain * 128
    for first, a, take in segs:
        d = tile[0][(first) * 128:(first + take) * 128]
        if rom is not None and len(d) % SEC:
            d += bytes(rom[a + len(d):a + len(d) + (-len(d) % SEC)])
        regions.append((ROMB + a, d))
    return regions


def assemble_rowtrim(p, pack_addr, rom=None):
    """SGP2 regions: magic SGP2, the SGP1 head, then at 84 the offset of the u32 stream positions of every 1024th payload and at 88 the offset of a u16 for each payload (its position from that base in 4 byte units). Order in main: head, key tables, spill table, offset tables, scroll tiles, the sprite records that fit."""
    key, tile, secs, inmain, segs, pos = p["key"], p["tile"], p["secs"], p["inmain"], p["segs"], p["pos"]
    n = p["n_tiles"]
    main = bytearray(HEAD + 8)
    keyoff = []
    for k in key:
        keyoff.append(len(main)); main += k
    table = len(main)
    main += struct.pack(">I", len(segs))
    for first, a, take in segs:
        main += struct.pack(">II", first, (ROMB + a - pack_addr) & 0xffffffff)
    main += bytes(-len(main) % 4)
    offs_at = len(main)
    bases = [pos[b << 10] for b in range((n + 1023) >> 10)]
    main += b"".join(struct.pack(">I", b) for b in bases)
    offs16_at = len(main)
    for i in range(n):
        d = pos[i] - bases[i >> 10]
        assert d % 4 == 0 and d >> 2 < 0x10000
        main += struct.pack(">H", d >> 2)
    at = {}
    for i in (1, 2, 3):
        main += bytes(-len(main) % 4)
        at[i] = len(main); main += tile[i]
    main += bytes(-len(main) % 4)
    at[0] = len(main); main += tile[0][:pos[inmain]]
    hdr, tail = [struct.pack(">I", 0x53475032)], []
    for i in range(4):
        hdr.append(struct.pack(">III", secs[i][0], keyoff[i], at[i]))
        tail.append(struct.pack(">II", inmain if i == 0 else 0xffffffff, table if i == 0 else 0))
    main[:HEAD + 8] = b"".join(hdr) + b"".join(tail) + struct.pack(">II", offs_at, offs16_at)
    regions = [(pack_addr, bytes(main))]
    for (first, a, take), nbytes in zip(segs, p["seg_bytes"]):
        d = tile[0][pos[first]:pos[first] + nbytes]
        if rom is not None and len(d) % SEC:
            d += bytes(rom[a + len(d):a + len(d) + (-len(d) % SEC)])
        regions.append((ROMB + a, d))
    return regions


def fit(raw, keys, main_room, free, rank=None, rowtrim=False):
    """Fits a stage. If it must drop sprite keys, drops the fewest, least used first (rank: key -> use, higher kept; unranked keys count 0, then highest key first).
    Returns (plan, keys dropped as a list)."""
    k = [set(s) for s in keys]
    p = plan(raw, k, main_room, free, rowtrim)
    if p:
        return p, []
    rank = rank or {}
    order = sorted(k[0], key=lambda x: (rank.get(x, 0), -x))
    lo, hi = 0, len(order)   # lo does not fit, hi does
    best = None
    while hi - lo > 1:
        m = (lo + hi) // 2
        q = plan(raw, [k[0] - set(order[:m]), k[1], k[2], k[3]], main_room, free, rowtrim)
        if q:
            hi, best = m, q
        else:
            lo = m
    return best or plan(raw, [set(), k[1], k[2], k[3]], main_room, free, rowtrim), order[:hi]


def write_file(out, audio, restores, regions):
    audio = sectors(audio)
    regs = [(regions[0][0], audio), (1, b"")] + restores + regions
    head = struct.pack(">I", len(regs))
    body = bytearray()
    for a, d in regs:
        d = sectors(d) if a != 1 else b""
        head += struct.pack(">II", a, len(d))
        body += d
    if len(head) > SEC:
        raise SystemExit("round file: too many regions")
    pathlib.Path(out).write_bytes(sectors(head) + body)
    return SEC + len(body)
