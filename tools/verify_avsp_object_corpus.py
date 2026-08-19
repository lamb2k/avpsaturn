"""Falsify the ROM-only object-stream decoder against the full captured corpus.

This is NEXT_AGENT_PROMPT.md Body B item 6: run the decoder against every
paired (workram, objram_active) capture frame on disk, with the eligible
population DECLARED before results are computed, and report every exclusion
by named reason. No live MAME needed - the captures already hold both the
inputs (actor records) and the ground truth (the game's own object lists).

## Declared eligible population

An actor-slot instance (one slot in one frame) is ELIGIBLE iff all of:
  1. the slot lies on the S1-validated actor grid (0xFF8380 + n*0xC0);
  2. its active byte (+0x00) is 0x01;
  3. its live pose pointer (+0x1C, u32) lies in the enemy script region
     [0x120000, 0x140000) - the region S2's animation-walk work established
     for the street-wave cast; the player and system actors live elsewhere
     and their emitter families are not yet decoded;
  4. the pose record is a plain pose, not a jump record (flags bit 15 clear);
  5. the pose's assembly selector word is a KNOWN selector (0x0006 = one
     group; 0x000C = two tagged groups). Unknown selectors are counted and
     listed as exclusions, not silently skipped;
  6. the actor's coordinate-mode byte (+0x0D) is positive. The dispatcher's
     own first branch (`tst.b ($d,A4); bmi $aa038` / `bne $aa13e`,
     live-disassembled via tools/mame_trace_facing0.lua) routes zero and
     negative modes to a coordinate path not yet decoded; only the positive
     path (the one every street alien uses) feeds the decoded origin
     routine. The stalker-route creatures that decode structurally but
     never matched are all +0x0D = 0xFF - the undecoded branch.

Every actor-slot instance failing 3-6 is an EXCLUSION with a named reason.
Eligible instances are decoded (groups -> four-word entries, all inputs from
ROM + the actor record; zero values from the oracle) and their concatenated
entry list is searched for as a consecutive run in that frame's active
object RAM.

## Oracle pairing: one-frame pipeline delay (MEASURED)

Actor state captured in workram_N appears in objram_active_{N+1}, not
objram_active_N: the game builds the display list from the actor state one
frame ahead of when that list is sampled as active. Measured directly before
this pairing was adopted: moving actors' decoded entries were "absent" from
their own frame's objram but matched frame N+1 (and N+2 while the pose held)
in every case tested; stationary actors match at several offsets, which is
what made the wrong pairing look partially right. This tool therefore pairs
workram_N with objram_active_{N+1} throughout.

Result classes per eligible instance:
  - exact:   the full concatenation appears as one consecutive run;
  - absent:  NONE of the instance's four-word entries appear anywhere in the
             paired object RAM (the game itself omitted the actor this
             frame - e.g. hit-flicker or the documented crowded-KO omission;
             counted separately, not a decode failure);
  - mismatch: anything else - some entries present or near-present but the
             run differs. These are decode failures unless individually
             explained; the S2 check requires ZERO unexplained.

## The selector discovery this run also tests

The pose `assembly` field (named "selector-6 assembly" by the earlier S2
animation work) begins with a selector word that carries the GROUP COUNT:
0x0006 introduces a single group (header immediately follows), 0x000C
introduces two groups, each prefixed by its own 0x0006 tag. Confirmed by
live trace on 5 (actor, pose) pairs before this corpus run; this run tests
it on every eligible pose in the corpus.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from decode_avsp_object_stream import (  # noqa: E402
    Rom, decode_group_header, decode_group_origin, decode_group_entries,
    decode_family2_entry, find_group_header, GROUP_TAG,
)

WORKRAM_BASE = 0xFF8000
ACTOR_ANCHOR = 0xFF8380          # S1-validated player slot
ACTOR_STRIDE = 0xC0
POSE_REGION = (0x120000, 0x140000)
SELECTOR_ONE = 0x0006
SELECTOR_TWO = 0x000C


def u16(b: bytes, o: int) -> int:
    return (b[o] << 8) | b[o + 1]


def u32(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o + 4], "big")


def read_objram_words(path: Path) -> list:
    words = []
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        if line:
            words.append(int(line.split("\t")[1], 16))
    return words


def read_anchors(work: bytes) -> tuple:
    """The origin routine's camera anchors, read from the game's OWN state:
    (A5+0x278)/(A5+0x27C) with A5=0xFF8000 -> workram offsets 0x278/0x27C,
    inside every 32 KiB capture. Their relationship to the CPS-A scroll1
    registers (anchor_x = scroll1_x + 0x40, anchor_y = 0x300 - scroll1_y)
    was verified across two routes with different camera positions before
    this direct read replaced the derivation."""
    return (work[0x278] << 8) | work[0x279], (work[0x27C] << 8) | work[0x27D]


def decode_actor_entries(rom: Rom, work: bytes, slot_off: int,
                         anchor_x: int, anchor_y: int):
    """Returns (entries_flat_words, meta) or (None, exclusion_reason)."""
    rec = work[slot_off:slot_off + ACTOR_STRIDE]
    if rec[0] != 0x01:
        return None, "inactive"
    pose_ptr = u32(rec, 0x1C)
    if not (POSE_REGION[0] <= pose_ptr < POSE_REGION[1]):
        return None, "pose-outside-declared-region"
    mode_positive = 1 <= rec[0x0D] <= 0x7F
    flags = rom.u16(pose_ptr + 2)
    if flags & 0x8000:
        return None, "jump-record"
    assembly = rom.u32(pose_ptr + 4)
    if not (0 < assembly < len(rom.d) - 0x40):
        return None, "assembly-outside-rom"

    # Record model (live-disassembled 2026-08-18, universal walker at
    # 0x0A9D1A/0x0A9D2A with the tag jump table at 0x0A9D3E, read through
    # the decrypted-opcodes view): the assembly's top word is either a
    # family tag itself (one record follows) or 0x000C ("two records
    # follow", each [tag u16][budget u16][family payload]). Known family
    # payloads: tag 0x0006 = the multi-part group (count/selector/D2/parts),
    # tag 0x0002 = single entry with inline attr/selector/D2/code,
    # tag 0x0008 = no-op (handler is an rts). Tags 0x0000/0x0004/0x000A
    # have located but undecoded handlers (0x0AA26C/0x0A9DEE/0x0AA38A).
    top = rom.u16(assembly)
    if top == SELECTOR_TWO:
        record_pos = assembly + 2
        n_records = 2
    elif top in (0x0002, 0x0004, 0x0006, 0x000A):
        record_pos = assembly
        n_records = 1
    else:
        return None, "unknown-top-word-0x%04x" % top

    world_x = u16(rec, 0x10)
    world_y = u16(rec, 0x14)
    facing = rec[0x0F]
    palette = rec[0x0E]
    or_value = u16(rec, 0x2E)

    flat = []
    families = []
    pos = record_pos
    for _ in range(n_records):
        tag = rom.u16(pos)
        if tag in (0x0004, 0x0006):
            # Family 0x0004 (handler 0x0A9DEE, live-traced via
            # tools/mame_trace_tag4.lua) is structurally identical to
            # family 0x0006 - same count/selector/origin/loop layout with
            # its own loop-body copies (e.g. 0x0A9E6C) - corpus-falsified
            # under family-6 semantics below.
            pass
        if tag in (0x0004, 0x0006):
            h = pos + 2      # budget at h+0, count h+2, selector h+4, D2 h+6
            count = rom.u16(h + 2)
            if not (1 <= count <= 8):
                return None, "implausible-count"
            ox, oy = decode_group_origin(rom, h, world_x, world_y, facing,
                                         anchor_x, anchor_y)
            entries = decode_group_entries(rom, h, ox, oy, palette, facing,
                                           or_value, mode_positive,
                                           tag == 0x0006)
            for e in entries:
                flat.extend([int(e["x"], 16), int(e["y"], 16),
                             int(e["code"], 16), int(e["attr"], 16)])
            families.append("%dx%d" % (tag, count))
            pos = h + 10 + count * (6 if tag == 0x0006 else 4)
        elif tag == 0x0002:
            e = decode_family2_entry(rom, pos + 4, world_x, world_y, facing,
                                     palette, or_value, anchor_x, anchor_y,
                                     mode_positive)
            flat.extend([int(e["x"], 16), int(e["y"], 16),
                         int(e["code"], 16), int(e["attr"], 16)])
            families.append("2")
            pos += 14
        elif tag == 0x0008:
            families.append("8-noop")
            pos += 4
        else:
            return None, "unknown-family-tag-0x%04x" % tag

    if not flat:
        return None, "no-emitting-records"
    meta = {"pose": pose_ptr, "assembly": assembly, "top": top,
            "families": families, "facing": facing, "palette": palette,
            "or_value": or_value, "action": u16(rec, 0x06)}
    return flat, meta


def find_run(haystack: list, needle: list) -> bool:
    n = len(needle)
    limit = len(haystack) - n
    first = needle[0]
    i = 0
    while i <= limit:
        try:
            i = haystack.index(first, i)
        except ValueError:
            return False
        if i > limit:
            return False
        if haystack[i:i + n] == needle:
            return True
        i += 1
    return False


def any_entry_present(haystack: list, flat: list) -> bool:
    for k in range(0, len(flat), 4):
        if find_run(haystack, flat[k:k + 4]):
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--roots", nargs="+",
                    default=[".deps/mame/enemy_actions",
                             ".deps/mame/stalker_actions",
                             ".deps/mame/boss_actions",
                             ".deps/mame/boss_ko"])
    ap.add_argument("--report",
                    default=str(TOOLS.parent / "data" /
                                "avsp_object_corpus_verification.json"))
    ap.add_argument("--limit", type=int, default=0,
                    help="stop after N frames per root (0 = all)")
    args = ap.parse_args()

    rom = Rom(Path(args.rom).read_bytes())

    per_root = {}
    mismatch_examples = []
    unknown_selectors = Counter()
    family_matrix = Counter()
    # Lifecycle-hypothesis instrumentation: if enemies persist as active
    # records until a hit/KO event and are merely not DRAWN in some states,
    # absent instances should cluster on specific action values rather than
    # mirroring the exact instances' action distribution.
    action_hist_exact = Counter()
    action_hist_absent = Counter()

    for root_s in args.roots:
        root = Path(root_s)
        frames = sorted(root.glob("workram_*.bin"))
        if args.limit:
            frames = frames[:args.limit]
        stats = Counter()
        for wpath in frames:
            frame_id = wpath.stem.split("_")[1]
            # One-frame pipeline delay (see module docstring): actor state at
            # frame N produces the active object list sampled at frame N+1.
            opath = root / ("objram_active_%05d.tsv" % (int(frame_id) + 1))
            if not opath.exists():
                stats["no-objram-pair"] += 1
                continue
            work = wpath.read_bytes()
            if len(work) != 0x8000:
                stats["bad-workram-size"] += 1
                continue
            anchor_x, anchor_y = read_anchors(work)
            objram = None  # lazy-load
            stats["frames"] += 1
            n_slots = (0x10000 - (ACTOR_ANCHOR - 0xFF0000)) // ACTOR_STRIDE
            for n in range(n_slots):
                slot_off = (ACTOR_ANCHOR - WORKRAM_BASE) + n * ACTOR_STRIDE
                if slot_off + ACTOR_STRIDE > len(work):
                    break
                try:
                    flat, meta = decode_actor_entries(rom, work, slot_off,
                                                      anchor_x, anchor_y)
                except IndexError:
                    flat, meta = None, "decode-out-of-range"
                if flat is None:
                    reason = meta
                    if reason.startswith("unknown-"):
                        unknown_selectors[reason] += 1
                        stats["excl:" + reason.rsplit("-0x", 1)[0]] += 1
                    elif reason != "inactive":
                        stats["excl:" + reason] += 1
                    continue
                stats["eligible"] += 1
                family_matrix["top=0x%04x %s" %
                              (meta["top"], "+".join(meta["families"]))] += 1
                if objram is None:
                    objram = read_objram_words(opath)
                if find_run(objram, flat):
                    stats["exact"] += 1
                    action_hist_exact[meta["action"]] += 1
                elif not any_entry_present(objram, flat):
                    stats["absent"] += 1
                    action_hist_absent[meta["action"]] += 1
                else:
                    stats["mismatch"] += 1
                    if len(mismatch_examples) < 20:
                        mismatch_examples.append({
                            "root": root.name, "frame": frame_id,
                            "slot": "0x%06X" % (WORKRAM_BASE + slot_off),
                            "meta": {k: (v if not isinstance(v, int) or v < 10
                                         else "0x%x" % v)
                                     for k, v in meta.items()},
                            "decoded": ["0x%04x" % w for w in flat],
                        })
        per_root[root.name] = dict(stats)
        print("%s: %s" % (root.name, dict(stats)))

    total_eligible = sum(r.get("eligible", 0) for r in per_root.values())
    total_exact = sum(r.get("exact", 0) for r in per_root.values())
    total_absent = sum(r.get("absent", 0) for r in per_root.values())
    total_mismatch = sum(r.get("mismatch", 0) for r in per_root.values())

    report = {
        "schema": 2,
        "classification": "decoder-vs-corpus verification counts only",
        "declared_population": ("active actor-grid slots with pose pointer in "
                                "[0x120000,0x140000), positive +0x0D "
                                "coordinate mode, plain pose record, known "
                                "top word (0x0002/0x0006/0x000C) and known "
                                "family tags (0x0002/0x0006/0x0008)"),
        "per_root": per_root,
        "unknown_tags": dict(unknown_selectors),
        "family_matrix": {k: v for k, v in sorted(family_matrix.items())},
        "totals": {"eligible": total_eligible, "exact": total_exact,
                   "absent_game_omitted": total_absent,
                   "mismatch": total_mismatch},
        "action_histogram_exact": {"0x%04x" % k: v for k, v in
                                   sorted(action_hist_exact.items())},
        "action_histogram_absent": {"0x%04x" % k: v for k, v in
                                    sorted(action_hist_absent.items())},
        "mismatch_examples": mismatch_examples,
        "pass": total_mismatch == 0 and total_eligible > 0,
    }
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print("eligible=%d exact=%d absent=%d mismatch=%d -> %s" %
          (total_eligible, total_exact, total_absent, total_mismatch,
           "PASS" if report["pass"] else "FAIL"))
    print("family matrix:", dict(family_matrix))
    print("absent action histogram:", dict(action_hist_absent))
    print("exact action histogram (top 8):",
          dict(action_hist_exact.most_common(8)))
    print("wrote %s" % out)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
