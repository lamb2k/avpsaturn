#!/usr/bin/env python
"""Lane satgfx: tile pack for saturn/gfx, from the graphics region. ROM-derived output: stays under E:/AvP/learning/lane-satgfx.

Format SGP1, big endian: magic, then per section (sprite, scroll 1, 2, 3) count, key table offset, data offset. Key word = key << 14 |
payload index; index 0x3fff means no visible pen. Identical payloads are stored once. Texture pens: 15 -> 0, p -> p + 1.
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


def pack(raw, used):
    """used: four sets of keys. Returns (bytes, [(keys, payload bytes)] per section)."""
    secs = []
    for s in range(4):
        seen, data, keys = {}, bytearray(), []
        for k in sorted(used[s]):
            pl, vis = payload(raw, s, k)
            if not vis:
                keys.append(k << 14 | 0x3fff)
                continue
            if pl not in seen:
                seen[pl] = len(seen)
                data += pl
            keys.append(k << 14 | seen[pl])
        assert len(seen) < 0x3fff
        secs.append((keys, bytes(data)))
    hdr = struct.pack(">I", 0x53475031)
    off = 4 + 12 * 4
    body = bytearray()
    for keys, data in secs:
        ko = off + len(body)
        body += b"".join(struct.pack(">I", k) for k in keys)
        do = off + len(body)
        body += data
        body += b"\0" * (-len(body) % 4)
        hdr += struct.pack(">III", len(keys), ko, do)
    return hdr + bytes(body), [(len(k), len(d)) for k, d in secs]
