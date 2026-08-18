"""Decode AvP's actor-local collision records from the game's own tables.

Nothing here is inferred from damage frames, overlay pixels or capture timing.
The format comes from the 68000 routines themselves:

  hit test caller (0x01CF84..0x01CFC6, duplicated at 0x01D064..0x01D0A6)
    A0 = [A6 + 0x1C]            attacker animation record
    D2 = A0[+9]                 attack-box selector; 0 => actor cannot hit
    A0 = [A1 + 0x1C]            defender animation record
    D3 = A0[+8]                 hurt-box selector;   0 => actor cannot be hit
    A3 = [A6 + 0x50]            attacker table-set pointer
    A3 += word[A3 + 2]          -> attack-box table base
    A3 += D2 * 16               -> attack-box entry   (stride 16)
    A2 = [A1 + 0x50]            defender table-set pointer
    A2 += word[A2 + 0]          -> hurt-box table base
    A2 += D3 * 8                -> hurt-box entry     (stride 8)
    bsr 0x01D25E                -> overlap test, "bhi" means no overlap

  overlap test (0x01D25E..0x01D312), three axes of centre + half-extent:
    depth : d = (hurt[+4] + defender[+0x18]) - (attack[+4] + attacker[+0x18])
            miss when |d| > attack[+5] + hurt[+5]        (d is kept, signed)
    x     : ax = attack[+0], negated when attacker[+0x0F] != 0, + attacker[+0x10]
            dx = hurt[+0],   negated when defender[+0x0F] != 0, + defender[+0x10]
            miss when |dx - ax| > attack[+2] + hurt[+2]
    y     : ay = attack[+1] + d + attacker[+0x14]
            dy = hurt[+1] + defender[+0x14]
            miss when |dy - ay| > attack[+3] + hurt[+3]

  on a hit (0x01CFCA..): defender[+0x2C] = attack[+0x0E], and the attacker
  takes the same byte when its own +0x2C is still zero; attack[+0x0A] selects
  the knockback treatment; defender[+0x2D] = attacker[+0x67].

Bytes +0/+1/+4 are signed; +2/+3/+5 are unsigned half-extents. Coordinates are
actor-local, so a record is reusable by every actor that shares the family
table-set pointer at actor +0x50.

Inputs
  * a decrypted 68000 program image (private, never committed);
  * a work-RAM capture (private) used ONLY to census which table-set pointers
    and which selector values Round 1 actually reaches. The census bounds what
    is reported; it never supplies a coordinate.

Output
  * data/avsp_collision.json  - copyright-safe decoded report
  * generated/avsp_collision.h - native tables for the runtime (git-ignored)

The report is deterministic: two runs over the same inputs produce byte-identical
output, which `--verify-deterministic` checks by re-running in-process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DEFAULT = ROOT / "data" / "avsp_collision.json"
HEADER_DEFAULT = ROOT / "generated" / "avsp_collision.h"

ACTOR_STRIDE = 0xC0
WORKRAM_FIRST = 0xFF8000
WORKRAM_SIZE = 0x8000
ACTOR_GRID_ANCHOR = 0xFF8380   # the player slot; every other slot is anchor + n*0xC0

HURT_STRIDE = 8
ATTACK_STRIDE = 16

# Actor fields the collision path actually consumes. Nothing else is labelled.
ACTOR_FIELDS = {
    "state": 0x00,
    "type": 0x08,
    "facing": 0x0F,
    "world_x": 0x10,
    "world_y": 0x14,
    "world_z": 0x18,
    "animation_record": 0x1C,
    "hit_value": 0x2C,
    "hit_source": 0x2D,
    "table_set": 0x50,
    "attacker_id": 0x67,
    "per_attacker_latch": 0x68,
    "suppress": 0x70,
    "latch_index": 0xD1,
}


def s8(v: int) -> int:
    return v - 256 if v > 127 else v


def s16(v: int) -> int:
    return v - 65536 if v > 32767 else v


class Rom:
    def __init__(self, data: bytes):
        self.d = data

    def u8(self, o: int) -> int:
        return self.d[o]

    def s16(self, o: int) -> int:
        return s16((self.d[o] << 8) | self.d[o + 1])

    def ok(self, o: int, n: int) -> bool:
        return 0 <= o and o + n <= len(self.d)


def decode_box(rom: Rom, off: int) -> dict:
    """The six bytes every record shares, as centre + half-extent per axis."""
    return {
        "x_center": s8(rom.u8(off + 0)),
        "y_center": s8(rom.u8(off + 1)),
        "x_half": rom.u8(off + 2),
        "y_half": rom.u8(off + 3),
        "z_center": s8(rom.u8(off + 4)),
        "z_half": rom.u8(off + 5),
    }


def is_inactive(box: dict) -> bool:
    return box["x_half"] == 0 and box["y_half"] == 0


def decode_family(rom: Rom, table_set: int, max_hurt: int, max_attack: int) -> dict:
    hurt_rel = rom.s16(table_set + 0)
    attack_rel = rom.s16(table_set + 2)
    hurt_base = table_set + hurt_rel
    attack_base = table_set + attack_rel

    # When the attack table follows the hurt table the gap proves the hurt
    # count exactly; otherwise fall back to the observed selector bound.
    gap = attack_base - hurt_base
    if gap > 0 and gap % HURT_STRIDE == 0:
        hurt_count = gap // HURT_STRIDE
        hurt_count_evidence = "exact: attack table begins immediately after the hurt table"
    else:
        hurt_count = max_hurt + 1
        hurt_count_evidence = "observed bound: highest selector reached in the censused route"
    # The adjacency test is the only structural proof available for a family.
    # When it fails, the two words at +0/+2 are probably not this actor's box
    # table offsets at all, so the family is reported but explicitly suspect.
    suspect = not (gap > 0 and gap % HURT_STRIDE == 0)

    hurt = []
    for i in range(hurt_count):
        off = hurt_base + i * HURT_STRIDE
        if not rom.ok(off, HURT_STRIDE):
            break
        box = decode_box(rom, off)
        hurt.append({
            "index": i,
            "address": "0x%06x" % off,
            "box": box,
            "inactive": is_inactive(box),
            "role_byte_7": rom.u8(off + 7),
            "unknown_byte_6": rom.u8(off + 6),
        })

    attack = []
    for i in range(max_attack + 1):
        off = attack_base + i * ATTACK_STRIDE
        if not rom.ok(off, ATTACK_STRIDE):
            break
        box = decode_box(rom, off)
        attack.append({
            "index": i,
            "address": "0x%06x" % off,
            "box": box,
            "inactive": is_inactive(box),
            "hit_value": rom.u8(off + 0x0E),
            "knockback_mode": s8(rom.u8(off + 0x0A)),
            "unknown_bytes": [rom.u8(off + k) for k in (6, 7, 8, 9, 0x0B, 0x0C, 0x0D, 0x0F)],
        })

    return {
        "table_set": "0x%06x" % table_set,
        "hurt_table": "0x%06x" % hurt_base,
        "attack_table": "0x%06x" % attack_base,
        "hurt_entry_stride": HURT_STRIDE,
        "attack_entry_stride": ATTACK_STRIDE,
        "hurt_count": len(hurt),
        "hurt_count_evidence": hurt_count_evidence,
        "suspect_not_a_box_family": suspect,
        "suspect_reason": None if not suspect else
            "the attack table does not follow the hurt table at a whole number of 8-byte entries; "
            "treat the two words at +0/+2 as unproven for this actor family and do not consume it",
        "attack_count_reported": len(attack),
        "attack_count_evidence": "observed bound: highest attack selector reached in the censused route; the table's true length is NOT proven",
        "hurt_entries": hurt,
        "attack_entries": attack,
    }


def census(workram: bytes, rom: Rom) -> dict:
    """Which families and selector values Round 1 actually reaches.

    Reads only actor context; never a coordinate. Returns, per table-set
    pointer, the observed actor types, actor slots and selector maxima.
    """
    frames = len(workram) // WORKRAM_SIZE
    grid = list(range(ACTOR_GRID_ANCHOR, WORKRAM_FIRST + WORKRAM_SIZE - ACTOR_STRIDE, ACTOR_STRIDE))
    fams: dict[int, dict] = {}
    for f in range(frames):
        s = workram[f * WORKRAM_SIZE:(f + 1) * WORKRAM_SIZE]
        for a in grid:
            o = a - WORKRAM_FIRST
            if s[o + ACTOR_FIELDS["state"]] == 0:
                continue
            rec = int.from_bytes(s[o + 0x1C:o + 0x20], "big")
            ts = int.from_bytes(s[o + 0x50:o + 0x54], "big")
            if not rec or not ts or not rom.ok(rec, 16) or not rom.ok(ts, 4):
                continue
            e = fams.setdefault(ts, {"types": set(), "slots": set(), "max_hurt": 0,
                                     "max_attack": 0, "samples": 0})
            e["types"].add(s[o + ACTOR_FIELDS["type"]])
            e["slots"].add(a)
            e["max_hurt"] = max(e["max_hurt"], rom.u8(rec + 8))
            e["max_attack"] = max(e["max_attack"], rom.u8(rec + 9))
            e["samples"] += 1
    return fams


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def merge_census(dst: dict, src: dict) -> dict:
    for ts, e in src.items():
        d = dst.setdefault(ts, {"types": set(), "slots": set(), "max_hurt": 0,
                                "max_attack": 0, "samples": 0})
        d["types"] |= e["types"]
        d["slots"] |= e["slots"]
        d["max_hurt"] = max(d["max_hurt"], e["max_hurt"])
        d["max_attack"] = max(d["max_attack"], e["max_attack"])
        d["samples"] += e["samples"]
    return dst


def build_report(rom_path: Path, workram_paths: list) -> dict:
    rom_bytes = rom_path.read_bytes()
    rom = Rom(rom_bytes)
    fams: dict = {}
    census_inputs = []
    for wp in workram_paths:
        work = Path(wp).read_bytes()
        merge_census(fams, census(work, rom))
        census_inputs.append({"path": str(wp).replace("\\", "/"),
                              "sha256": sha256_bytes(work), "bytes": len(work)})

    families = []
    for ts in sorted(fams):
        e = fams[ts]
        fam = decode_family(rom, ts, e["max_hurt"], e["max_attack"])
        fam["observed"] = {
            "actor_types": sorted(e["types"]),
            "actor_slots": ["0x%06x" % s for s in sorted(e["slots"])],
            "actor_frame_samples": e["samples"],
            "max_hurt_selector": e["max_hurt"],
            "max_attack_selector": e["max_attack"],
        }
        families.append(fam)

    return {
        "schema": 1,
        "classification": "decoded game collision records - coordinates only, no ROM bytes",
        "method": "68000 routine decode; see tools/decode_avsp_collision.py docstring",
        "routines": {
            "selector_read_attack": "0x01CF88 (animation record +9)",
            "selector_read_hurt": "0x01CF94 (animation record +8)",
            "table_set_deref_attack": "0x01CF9C..0x01CFAC (actor +0x50, word +2, stride 16)",
            "table_set_deref_hurt": "0x01CFB0..0x01CFBE (actor +0x50, word +0, stride 8)",
            "overlap_test": "0x01D25E..0x01D312",
            "hit_apply": "0x01CFCA..0x01D036",
            "duplicate_caller": "0x01D064..0x01D110",
        },
        "actor_fields_consumed": {k: "+0x%02X" % v for k, v in sorted(ACTOR_FIELDS.items(), key=lambda kv: kv[1])},
        "actor_stride": "0x%02X" % ACTOR_STRIDE,
        "record_format": {
            "byte_0": "signed x centre, negated when the owner's facing byte is non-zero",
            "byte_1": "signed y centre",
            "byte_2": "unsigned x half-extent",
            "byte_3": "unsigned y half-extent",
            "byte_4": "signed z (depth) centre",
            "byte_5": "unsigned z half-extent",
            "hurt_byte_7": "role/type byte read at 0x01D314; meaning not yet proven",
            "attack_byte_0x0A": "knockback treatment: 0 none, positive compares world x, negative toggles bit 0",
            "attack_byte_0x0E": "value written to the defender's +0x2C on a hit",
        },
        "inputs": {
            "program_image": {"path": str(rom_path).replace("\\", "/"), "sha256": sha256_bytes(rom_bytes), "bytes": len(rom_bytes)},
            "census_workram": census_inputs,
        },
        "family_count": len(families),
        "families": families,
    }


def emit_header(report: dict, path: Path) -> None:
    lines = [
        "/* Generated by tools/decode_avsp_collision.py. Do not edit. */",
        "#ifndef AVSP_COLLISION_H",
        "#define AVSP_COLLISION_H",
        "",
        "typedef struct {",
        "    signed char x_center;",
        "    signed char y_center;",
        "    unsigned char x_half;",
        "    unsigned char y_half;",
        "    signed char z_center;",
        "    unsigned char z_half;",
        "} avsp_collision_box;",
        "",
        "typedef struct {",
        "    avsp_collision_box box;",
        "    unsigned char hit_value;",
        "    signed char knockback_mode;",
        "} avsp_collision_attack;",
        "",
    ]
    for fi, fam in enumerate(report["families"]):
        tag = fam["table_set"].replace("0x", "")
        lines.append("/* family %s: actor types %s */" % (fam["table_set"], fam["observed"]["actor_types"]))
        lines.append("static const avsp_collision_box avsp_hurt_%s[%d] = {" % (tag, len(fam["hurt_entries"])))
        for e in fam["hurt_entries"]:
            b = e["box"]
            lines.append("    { %4d, %4d, %3u, %3u, %4d, %3u }," % (
                b["x_center"], b["y_center"], b["x_half"], b["y_half"], b["z_center"], b["z_half"]))
        lines.append("};")
        lines.append("static const avsp_collision_attack avsp_attack_%s[%d] = {" % (tag, len(fam["attack_entries"])))
        for e in fam["attack_entries"]:
            b = e["box"]
            lines.append("    { { %4d, %4d, %3u, %3u, %4d, %3u }, %3u, %4d }," % (
                b["x_center"], b["y_center"], b["x_half"], b["y_half"], b["z_center"], b["z_half"],
                e["hit_value"], e["knockback_mode"]))
        lines.append("};")
        lines.append("")
    lines.append("typedef struct {")
    lines.append("    unsigned long table_set;")
    lines.append("    const avsp_collision_box *hurt;")
    lines.append("    unsigned short hurt_count;")
    lines.append("    const avsp_collision_attack *attack;")
    lines.append("    unsigned short attack_count;")
    lines.append("} avsp_collision_family;")
    lines.append("")
    trusted = [f for f in report["families"] if not f["suspect_not_a_box_family"]]
    lines.append("/* Trusted families only. Families whose attack table does not follow their")
    lines.append("   hurt table at a whole number of entries are omitted deliberately. */")
    lines.append("static const avsp_collision_family avsp_collision_families[%d] = {" % len(trusted))
    for fam in trusted:
        tag = fam["table_set"].replace("0x", "")
        lines.append("    { 0x%sUL, avsp_hurt_%s, %d, avsp_attack_%s, %d }," % (
            tag, tag, len(fam["hurt_entries"]), tag, len(fam["attack_entries"])))
    lines.append("};")
    lines.append("static const unsigned short avsp_collision_family_count = %d;" % len(trusted))
    lines.append("")
    lines += ["#endif /* AVSP_COLLISION_H */", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", required=True, help="decrypted 68000 program image (private)")
    ap.add_argument("--census-workram", required=True, action="append",
                    help="work-RAM capture used only to bound the report; repeatable")
    ap.add_argument("--report", default=str(REPORT_DEFAULT))
    ap.add_argument("--header", default=str(HEADER_DEFAULT))
    ap.add_argument("--verify-deterministic", action="store_true")
    args = ap.parse_args()

    rom_path = Path(args.rom)
    report = build_report(rom_path, args.census_workram)
    text = json.dumps(report, indent=1, sort_keys=True) + "\n"

    if args.verify_deterministic:
        again = json.dumps(build_report(rom_path, args.census_workram), indent=1, sort_keys=True) + "\n"
        if again != text:
            print("NON-DETERMINISTIC: two decodes differ")
            return 2
        print("deterministic: two decodes agree, sha256=%s" % sha256_bytes(text.encode()))

    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    emit_header(report, Path(args.header))
    print("wrote %s (sha256=%s)" % (out, sha256_bytes(text.encode())))
    print("wrote %s" % args.header)
    print("families=%d" % report["family_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
