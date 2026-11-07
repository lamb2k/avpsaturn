#!/usr/bin/env python
"""Lane rounds: one disc file per stage word: sound set, then ROM restores, then tile pack, as regions the loader reads in order (saturn/rt/boot.c).
Pack format: tools/satgfx_pack.py; sprites fill the main part on the cart, then continue in ROM stretches this stage, the next stage and the front end do not read, through a table in the pack.
A stretch overwritten by any file is restored by every file whose stage reads it, so what any stage reads is always the ROM's bytes.
ROM-derived output: stays under E:/AvP/learning."""
import pathlib, struct, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import satgfx_pack
SEC = 2048
HEAD = 4 + 12 * 4 + 8 * 4
ROMB = 0x02400000


def sectors(b):
    return bytes(b) + bytes(-len(b) % SEC)


def plan(raw, keys, main_room, free):
    """Returns (pack parts) or None if over. free: [[rom offset, bytes]] for this stage, in order of use."""
    try:
        data, _ = satgfx_pack.pack(raw, keys)
    except AssertionError:   # past the 14 bit payload index
        return None
    secs = [struct.unpack_from(">III", data, 4 + i * 12) for i in range(4)]
    ends = [secs[i + 1][1] if i < 3 else len(data) for i in range(4)]
    tile = [data[secs[i][2]:ends[i]] for i in range(4)]
    key = [data[secs[i][1]:secs[i][2]] for i in range(4)]
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
        for a, n in free:
            if not need:
                break
            take = min(need, (n & -SEC) // 128)   # whole sectors: the loader pads a region to a sector, which must stay in the stretch
            if take:
                segs.append((first, a, take)); first += take; need -= take
        if need:
            return None
        if len(segs) <= tries:
            break
    else:
        return None
    return dict(key=key, tile=tile, secs=secs, inmain=inmain, segs=segs)


def assemble(p, pack_addr):
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
        regions.append((ROMB + a, tile[0][(first) * 128:(first + take) * 128]))
    return regions


def fit(raw, keys, main_room, free, rank=None):
    """Fits a stage. If it must drop sprite keys, drops the fewest, least used first (rank: key -> use, higher kept; unranked keys count 0, then highest key first).
    Returns (plan, keys dropped as a list)."""
    k = [set(s) for s in keys]
    p = plan(raw, k, main_room, free)
    if p:
        return p, []
    rank = rank or {}
    order = sorted(k[0], key=lambda x: (rank.get(x, 0), -x))
    lo, hi = 0, len(order)   # lo does not fit, hi does
    best = None
    while hi - lo > 1:
        m = (lo + hi) // 2
        q = plan(raw, [k[0] - set(order[:m]), k[1], k[2], k[3]], main_room, free)
        if q:
            hi, best = m, q
        else:
            lo = m
    return best or plan(raw, [set(), k[1], k[2], k[3]], main_room, free), order[:hi]


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
