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

SCSP_ROOM = 0x7e000
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


def load_assets(assets):
    assets = pathlib.Path(assets)
    j = json.loads((assets / "wv_sound.json").read_text())
    blob = (assets / "wv_sound.bin").read_bytes()
    for s in j["sounds"]:
        s["data"] = blob[s["off"]:s["off"] + s["n"]]
    return j


def build(pack, wv, rank=None, kind="stage", room=SCSP_ROOM, remap=REMAP, optional_commands=()):
    """Build the normal guest mix, then fit any optional commands in its remaining room."""
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
        if r["cmd"] in optional_commands and w is None:
            optional.append(r)
        else:
            new.append(r)
    base = wv["cmd_base"]
    for s in mine:
        new.append(dict(cmd=base + s["id"], prio=s["prio"], mask=s["mask"], tl=s["tl"], flags=0, data=s["data"], n=s["n"], wv=True))
        report["added"] += 1
    new.sort(key=lambda r: r["cmd"])

    def size(rs):
        seen = {}
        for r in rs:
            seen.setdefault(r["data"], 0)
        return HDR.size + 16 * (len(rs) + len(music) // 16) + sum(len(d) + (len(d) & 1) for d in seen)
    order = sorted((r for r in new if not r.get("wv")), key=lambda r: (rank or {}).get(r["cmd"], 0))
    while size(new) > room and order:
        d = order.pop(0)
        new.remove(d)
        report["dropped"].append((hex(d["cmd"]), (rank or {}).get(d["cmd"], 0), d["n"]))
    if size(new) > room:
        raise SystemExit("NO-GO: Wolverine sounds do not fit even with every other clip dropped")
    for r in optional:
        if size(new + [r]) <= room:
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
        table += ROW.pack(r["cmd"], r["prio"], r["mask"] >> 8, r["mask"] & 255, r["tl"], r["flags"], r.get("rate", 0), offs[r["data"]], len(r["data"]))
    out = HDR.pack(b"SAU1", len(new), len(music) // 16, len(blob)) + bytes(table) + music + bytes(blob)
    report.update(size=len(out), room_left=room - len(out), rows=len(new))
    return out, report


if __name__ == "__main__":
    base = pathlib.Path(sys.argv[1]).read_bytes()
    out, rep = build(base, load_assets(sys.argv[2]))
    print(rep)
    if len(sys.argv) > 3:
        pathlib.Path(sys.argv[3]).write_bytes(out)
