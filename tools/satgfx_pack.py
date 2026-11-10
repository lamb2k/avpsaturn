#!/usr/bin/env python
"""Lane satgfx: tile pack for saturn/gfx, from the graphics region. ROM-derived output: stays under E:/AvP/learning/lane-satgfx.

Format SGP1, big endian: magic, then per section (sprite, scroll 1, 2, 3) count, key table offset, data offset, then per section split index, spill offset. Key word = key << 16 |
payload index in the sprite section, key << 14 | index in the scroll sections (scroll 1 keys need 18 bits); an index of all ones means no visible pen. Identical payloads are stored once. Texture pens: 15 -> 0, p -> p + 1.
Sprite: 16 rows of 8 bytes. Scroll 1: one 8x8 cell, key = code << 1 | column bit 5. Scroll 2: four cells TL TR BL BR, key = code.
Scroll 3: four such 16 pixel characters, key = code.
"""
import struct


def pens(raw, off, w, h, stride):
    out = []
    for y in range(h):
        row = []
        for g in range(w // 8):
            o = off + y * stride + g * 4
            b = raw[o:o + 4]
            for x in range(8):
                m = 0x80 >> x
                row.append((b[3] & m != 0) << 3 | (b[2] & m != 0) << 2 | (b[1] & m != 0) << 1 | (b[0] & m != 0))
        out.append(row)
    return out


def tex(px):
    out = bytearray()
    for row in px:
        for x in range(0, len(row), 2):
            out.append((((row[x] + 1) & 15) << 4) | ((row[x + 1] + 1) & 15))
    return bytes(out)


def part(px, y, x, h, w):
    return [r[x:x + w] for r in px[y:y + h]]


def cells16(px):
    return tex(part(px, 0, 0, 8, 8)) + tex(part(px, 0, 8, 8, 8)) + tex(part(px, 8, 0, 8, 8)) + tex(part(px, 8, 8, 8, 8))


def payload(raw, sec, key):
    if sec == 0:
        px = pens(raw, key * 0x80, 16, 16, 8)
        pl = tex(px)
    elif sec == 1:
        full = pens(raw, 0x800000 + (key >> 1) * 0x40, 16, 8, 8)
        px = part(full, 0, 8 if key & 1 else 0, 8, 8)
        pl = tex(px)
    elif sec == 2:
        px = pens(raw, 0x800000 + key * 0x80, 16, 16, 8)
        pl = cells16(px)
    else:
        px = pens(raw, 0x800000 + key * 0x200, 32, 32, 16)
        pl = b"".join(cells16(part(px, y, x, 16, 16)) for y, x in ((0, 0), (0, 16), (16, 0), (16, 16)))
    return pl, any(p != 15 for r in px for p in r)


def record(pl, mode=1):
    """mode 2 (SAT_TILE_ROWTRIM=2): u32 mask, bit 31 = long 0 of the 32 longs of the payload, set = the long is not zero, then those longs (4 + 4 n bytes)."""
    if mode == 2:
        longs = [pl[i:i + 4] for i in range(0, 128, 4)]
        mask = 0
        for i, l in enumerate(longs):
            if l != bytes(4):
                mask |= 0x80000000 >> i
        return struct.pack(">I", mask) + b"".join(l for l in longs if l != bytes(4))

    """Row masked sprite tile (SGP2, saturn/gfx/sat_gfx.c rowtrim_decode): u16 mask (bit 15 = row 0, set = the row has a visible pen), u16 0, then 8 bytes for each set bit.
    A cleared row is eight zero bytes in the plain 128 byte payload (texture pen 0 is transparent)."""
    rows = [pl[i:i + 8] for i in range(0, 128, 8)]
    mask = 0
    for r, row in enumerate(rows):
        if row != bytes(8):
            mask |= 0x8000 >> r
    return struct.pack(">HH", mask, 0) + b"".join(row for row in rows if row != bytes(8))


def expand(rec, mode=1):
    """The 128 byte payload of a record."""
    if mode == 2:
        mask = struct.unpack_from(">I", rec)[0]
        out, at = bytearray(), 4
        for i in range(32):
            if mask & (0x80000000 >> i):
                out += rec[at:at + 4]; at += 4
            else:
                out += bytes(4)
        return bytes(out)
    mask = struct.unpack_from(">H", rec)[0]
    out, at = bytearray(), 4
    for r in range(16):
        if mask & (0x8000 >> r):
            out += rec[at:at + 8]; at += 8
        else:
            out += bytes(8)
    return bytes(out)


def pack(raw, used, rowtrim=False):
    """used: four sets of keys. Returns (bytes, [(keys, payload bytes)] per section). rowtrim: the sprite section holds records (see record), not 128 byte payloads."""
    secs = []
    for s in range(4):
        seen, data, keys = {}, bytearray(), []
        ks = 16 if s == 0 else 14
        blank = (1 << ks) - 1
        for k in sorted(used[s]):
            pl, vis = payload(raw, s, k)
            if not vis:
                keys.append(k << ks | blank)
                continue
            if pl not in seen:
                seen[pl] = len(seen)
                data += record(pl, rowtrim) if rowtrim and s == 0 else pl
            keys.append(k << ks | seen[pl])
        assert len(seen) < blank and all(k >> 32 == 0 for k in keys)
        secs.append((keys, bytes(data)))
    hdr = struct.pack(">I", 0x53475031)
    off = 4 + 12 * 4 + 8 * 4   # four (split index, spill offset) pairs follow the sections; see satint_pack.py
    body = bytearray()
    for keys, data in secs:
        ko = off + len(body)
        body += b"".join(struct.pack(">I", k) for k in keys)
        do = off + len(body)
        body += data
        body += b"\0" * (-len(body) % 4)
        hdr += struct.pack(">III", len(keys), ko, do)
    hdr += struct.pack(">II", 0xffffffff, 0) * 4
    return hdr + bytes(body), [(len(k), len(d)) for k, d in secs]
