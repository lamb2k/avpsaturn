#!/usr/bin/env python
"""Wolverine's sounds in the stage sound packs (lane wv-sounds). Used by tools/wolverine/guest_rounds.py when the guest assets hold wv_sound/ (tools/wolverine/wv_sound.py build).

A stage sound pack (saturn/audio/build_pack.py, SAU1: header, 16 byte sfx rows sorted by command, music rows, 8 bit PCM) is made once per stage file, nearly full (SCSP RAM holds 504 KB of clips and most packs
have 2 to 4 KB spare). The pack of a Wolverine stage file is the base pack, rebuilt here:
  1. REMAP: rows of Schaefer's own sounds whose role Wolverine also has now play Wolverine's clip (same command, priority and channel, so the game's own calls need no change): his hurt voice 0x213,
     his KO scream 0x214, the select shout 0x264 (he says "Let's go, bub." when picked, owner 11-10), the special's pair 0x21c and 0x97 (Tornado Claw), the weapon sound 0x250. Schaefer's clips nothing else uses leave the pack.
  2. One new row per Wolverine sound at WV_CMD_BASE + id (saturn/guests/wolverine/wv_sound.h): the commands wv_sfx() sends. Clips are shared when identical.
  3. If the pack is past SCSP_ROOM, the rows with the fewest route uses (WORK/sound_rank.json, the same ranking rounds_config.py used) leave first, never a Wolverine row.
Rows keep their priority and channel mask; clip offsets are recomputed. The result for each stage file is WORK/audio/r{N}.bin and the stage file's audio_from points at it.
usage (inspection): wv_audio.py BASEPACK.bin ASSETDIR [OUT.bin]"""
import json
import pathlib
import struct
import sys
from collections import defaultdict

SCSP_ROOM = 0x7e000
# Each pair shares one clip. Process the longer Hunter entry first.
STAGE_HIT_CUES = {0x06: (0x0046, 0x0111, 0x010C, 0x0041, 0x004A)}
# sat_audio_swap copies PCM above the SCSP vectors. round_sound_ready
# copies the SAU1 header and tables into a separate buffer.
SCSP_PCM_ROOM = 0x80000 - 0x20
ROUND_SOUND_TABLE_ROOM = 0x2000
HDR = struct.Struct(">4sHHI")
ROW = struct.Struct(">HBBBBBBII")

# Schaefer's own command -> the Wolverine sound that plays in its place (name in wv_sound.py SOUNDS). Roles from the game's own code (docs/notes/AVP_WOLVERINE_SOUNDS_20261109.md):
# 0x213 the hurt voice the player routine sends when a hit lands on him (f_1a96e, table 0x1b7b4), 0x214 his KO scream (f_1b16e, 0x1b7c4), 0x264 stage 0 only (the select shout),
# 0x21c and 0x97 sent together when the special starts (f_24f04), 0x250 the weapon sound (table 0x1b814).
REMAP = {0x213: "HURT_A", 0x214: "KO", 0x264: "INTRO", 0x21c: "TORNADO", 0x97: "CLAW_H", 0x250: "CLAW_M"}


def parse(pack):
    magic, nsfx, nmusic, nclip = HDR.unpack_from(pack, 0)
    if magic != b"SAU1":
        raise ValueError("not a SAU1 pack")
    rows = []
    for i in range(nsfx):
        c, prio, mh, ml, tl, fl, pad, off, n = ROW.unpack_from(pack, HDR.size + 16 * i)
        rows.append(dict(cmd=c, prio=prio, mask=mh << 8 | ml, tl=tl, flags=fl, off=off, n=n, rate=pad))   # rate: the clip's rate code (coverage lane fix7c3, SAT_PACK_RATE; 0 = 11025 Hz)
    music = pack[HDR.size + 16 * nsfx:HDR.size + 16 * (nsfx + nmusic)]
    clips = pack[HDR.size + 16 * (nsfx + nmusic):HDR.size + 16 * (nsfx + nmusic) + nclip]
    return rows, bytes(music), bytes(clips)


def encode(rows, music, pcm):
    table = b"".join(ROW.pack(
        row["cmd"], row["prio"], row["mask"] >> 8, row["mask"] & 255,
        row["tl"], row["flags"], row["rate"], row["off"], row["n"],
    ) for row in sorted(rows, key=lambda row: row["cmd"]))
    header = HDR.pack(b"SAU1", len(rows), len(music) // ROW.size, len(pcm))
    return header + table + music + pcm


def free_guest_pcm(pack, need):
    """Use lower-rate guest one-shots only when they can free the requested space."""
    import numpy as np
    from .wv_sound import BP, CMD_BASE, SOUNDS

    rows, music, pcm = parse(pack)
    guest_commands = {CMD_BASE + sound["id"] for sound in SOUNDS}
    groups = defaultdict(list)
    for row in rows:
        groups[row["off"]].append(row)
    positions = sorted(groups)
    options = []
    previous_end = 0
    for offset, following in zip(positions, positions[1:] + [len(pcm)]):
        aliases = groups[offset]
        size = max(row["n"] for row in aliases)
        end = offset + ((size + 1) & ~1)
        separate = previous_end <= offset and end <= following and offset % 2 == 0
        previous_end = max(previous_end, end)
        commands = {row["cmd"] for row in aliases}
        if not separate or size < 63 or not commands.intersection(guest_commands):
            continue
        if any(row["flags"] or row["rate"] or
               (row["cmd"] not in REMAP and row["cmd"] not in guest_commands) for row in aliases):
            continue
        wave = np.frombuffer(pcm[offset:offset + size], dtype=np.int8).astype(float)
        rate, code, _ = BP.pick_rate(wave)
        if not code:
            continue
        lengths = [max(1, round(row["n"] * rate / 11025)) if row["n"] else 0 for row in aliases]
        filtered = np.convolve(wave, BP.decimator(rate, 11025), mode="same")
        reduced = np.interp(np.arange(max(lengths)) * (11025 / rate), np.arange(size), filtered)
        data = np.clip(np.rint(reduced), -128, 127).astype(np.int8).tobytes()
        padded = data + bytes(len(data) & 1)
        saving = end - offset - len(padded)
        if saving > 0:
            options.append((saving, offset, end, code, lengths, padded))

    selected = {}
    for saving, offset, end, code, lengths, data in sorted(options, reverse=True):
        selected[offset] = (end, code, lengths, data)
        need -= saving
        if need <= 0:
            break
    if need > 0:
        return None

    result = bytearray()
    cursor = 0
    for offset in positions:
        result.extend(pcm[cursor:offset])
        aliases = groups[offset]
        for row in aliases:
            row["off"] = len(result)
        cursor = offset
        if offset in selected:
            cursor, code, lengths, data = selected[offset]
            result.extend(data)
            for row, length in zip(aliases, lengths):
                row.update(rate=code, n=length)
    result.extend(pcm[cursor:])
    return encode(rows, music, result)


def load_assets(assets):
    assets = pathlib.Path(assets)
    j = json.loads((assets / "wv_sound.json").read_text())
    blob = (assets / "wv_sound.bin").read_bytes()
    for s in j["sounds"]:
        s["data"] = blob[s["off"]:s["off"] + s["n"]]
    return j


def build(pack, wv, rank=None, kind="stage", room=SCSP_ROOM, remap=REMAP, optional_commands=(), reserved_commands=()):
    """Fit optional effects into the usual mix, then use spare PCM RAM for reserved effects."""
    additions = (*optional_commands, *reserved_commands)
    rows, music, clips = parse(pack)
    mine = [s for s in wv["sounds"] if s.get("where", "stage") in (kind, "both")]
    by_name = {s["name"]: s for s in mine}
    new, optional = [], []
    report = dict(remapped=[], removed_bytes=0, dropped=[], added=0)
    for r in rows:
        r = dict(r, data=clips[r["off"]:r["off"] + r["n"]])
        w = by_name.get(remap.get(r["cmd"]))
        if w is not None:
            report["remapped"].append(hex(r["cmd"]))
            r.update(tl=w["tl"], flags=0, data=w["data"], n=w["n"], wv=True, rate=0)
        if r["cmd"] in additions and w is None:
            optional.append(r)
        else:
            new.append(r)
    base = wv["cmd_base"]
    for s in mine:
        new.append(dict(cmd=base + s["id"], prio=s["prio"], mask=s["mask"], tl=s["tl"], flags=0, data=s["data"], n=s["n"], wv=True))
        report["added"] += 1
    new.sort(key=lambda r: r["cmd"])

    def size(rs):
        clips = {r["data"] for r in rs}
        return HDR.size + 16 * len(rs) + len(music), sum(len(d) + (len(d) & 1) for d in clips)
    order = sorted((r for r in new if not r.get("wv")), key=lambda r: (rank or {}).get(r["cmd"], 0))
    while sum(size(new)) > room and order:
        d = order.pop(0)
        new.remove(d)
        report["dropped"].append((hex(d["cmd"]), (rank or {}).get(d["cmd"], 0), d["n"]))
    if sum(size(new)) > room:
        raise SystemExit("NO-GO: Wolverine sounds do not fit even with every other clip dropped")
    optional.sort(key=lambda r: additions.index(r["cmd"]))
    shared = {}
    for r in optional:
        if len(r["data"]) > len(shared.get(r["off"], b"")):
            shared[r["off"]] = r["data"]
    for r in optional:
        # An optional row can use a shorter part of another row's backing PCM.
        r["n"] = len(r["data"])
        r["data"] = shared.get(r["off"], r["data"])
        tables, samples = size(new + [r])
        if r["cmd"] in reserved_commands:
            fits = tables <= ROUND_SOUND_TABLE_ROOM and samples <= SCSP_PCM_ROOM
        else:
            fits = tables + samples <= room
        if fits:
            new.append(r)
        else:
            report.setdefault("optional_unfit", []).append(hex(r["cmd"]))
    if optional:
        new.sort(key=lambda r: r["cmd"])
    offs, blob = {}, bytearray()
    table = bytearray()
    for r in new:
        if r["data"] not in offs:
            offs[r["data"]] = len(blob)
            blob += r["data"]
            if len(blob) & 1:
                blob += bytes(1)
        table += ROW.pack(r["cmd"], r["prio"], r["mask"] >> 8, r["mask"] & 255, r["tl"], r["flags"], r.get("rate", 0), offs[r["data"]], min(r["n"], len(r["data"])))
    out = HDR.pack(b"SAU1", len(new), len(music) // 16, len(blob)) + bytes(table) + music + bytes(blob)
    report.update(size=len(out), room_left=SCSP_PCM_ROOM - len(blob) if reserved_commands else room - len(out), rows=len(new))
    return out, report


if __name__ == "__main__":
    base = pathlib.Path(sys.argv[1]).read_bytes()
    out, rep = build(base, load_assets(sys.argv[2]))
    print(rep)
    if len(sys.argv) > 3:
        pathlib.Path(sys.argv[3]).write_bytes(out)
