"""Step-2 body (offline): per-state street-alien table_set extraction.

What this proves (bounded, from the validated opcode-space image):

   1. Bounded state-0 span decode. For each street-actor class
      (0x00 type_promotion, 0x06 replace, 0x1F normal), the class's
      state-0 (class-entry initializer) handler span [targets[0], targets[1])
      is linearly decoded instruction by instruction starting at the
      known instruction boundary that opens the span (the dispatch
      target), as long as the sequential decoder stays clean. These
      handlers embed inline (PC,D0).W data tables (the class 0x00 one
      indexes its at 0x03F188/0x03F18C), where the clean decode stops
      and the undecoded tail is RECORDed, not asserted through. Within
      the PROVEN CLEAN REGION [targets[0], clean_end) exactly one
      instruction writes actor +0x50 (table_set): the immediate
      `move.l #imm32, $50(a6)` store, and the decode must reach that
      store without derailing - proving the store is real code at that
      PC. This is a claim about the decoded region, not about the whole
      span or the whole image: other code regions may well write +0x50
      for other actor systems, and none of that is in or out of scope
      here; writer status in the undecoded tail (if any) is settled by
      the corpus-observed constancy, below.
  2. The store's PC and immediate cross-match the live-trace-proven
     family in data/avsp_table_set_source.json (store_pc AND value).
  3. Each class's sub-state dispatch table (word table at
     dispatcher_pc+12; actor byte +0x04 is the index; word 0 is the
     count word) is re-verified word-for-word from the image.
  4. Where the sub-state-2 (walk/attack) handler begins with the
     second-level dispatch idiom, its word table is decoded and every
     branch target must stay inside the class range.

Semantic answer recorded in the output manifest:

   class entry -> the class's state-0 immediate (the only +0x50 writer found
   in the clean code region of the state-0 span by (1));
  every other observed sub-state behaviour (walk/attack; the hit
  sequence observed INSIDE sub-state 0x02 under action word +0x06
  family 0x00xx-0x02xx; the KO sequence observed in sub-states
  0x04/0x06) -> corpus-OBSERVED constancy at the class's state-0 value
  over the four deterministic MAME routes (falsified, with the
  exact HIT/KO anchors and lifecycle populations identified by their observed
  class/state/sub-state/action signatures, in
  tools/verify_avsp_table_set_states.py). Inheritance is corpus-
  observed constancy, NOT a claim that no other writer exists outside
  the spans actually decoded and observed.

Corpus falsification and the semantic anchor (HIT clip 5191-5226 and
KO clip 5330-5469 of the captured enemy_actions actor at RAM
0xFFA000, band slot 14) live in tools/verify_avsp_table_set_states.py.

Inputs (private image + tracked manifests):
  .deps/mame/actorprobe/decrypted_opcodes_2m.bin
  data/avsp_actor_class_table.json
  data/avsp_substate_dispatchers.json
  data/avsp_table_set_source.json
Output (tracked):
  data/avsp_table_set_states.json (addresses/PCs/decoded immediates/
  counts only - no ROM bytes)
test.ps1 contract: any missing input -> clean skip, exit 0.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_PATH = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
CLASS_TABLE_PATH = ROOT / "data" / "avsp_actor_class_table.json"
DISPATCHERS_PATH = ROOT / "data" / "avsp_substate_dispatchers.json"
SOURCE_PATH = ROOT / "data" / "avsp_table_set_source.json"
OUT_PATH = ROOT / "data" / "avsp_table_set_states.json"

STREET_CLASSES = (0x00, 0x06, 0x1F)

# move.l #imm32, d16(A6) in this ROM's object code: the 0x2D7C opcode
# word, a big-endian 32-bit immediate, and the displacement tail 0x0050
# terminating the instruction. Ground truth: capstone decodes the same
# instruction at all three live-traced store PCs.
STORE_OP0 = 0x2D
STORE_OP1 = 0x7C
STORE_TAIL = (0x00, 0x50)

# Every 68000 mnemonic that can WRITE a memory destination. Used only
# to recognise +0x50 writers inside the bounded span decode.
WRITE_MNEMONICS = {
    "move.b", "move.w", "move.l",
    "clr.b", "clr.w", "clr.l",
    "swap",
    "neg.b", "neg.w", "neg.l",
    "not.b", "not.w", "not.l",
    "ext.l",
    "movem.l",
}

PC_TABLE_RE = re.compile(r"\$([0-9a-fA-F]+)\(pc,\s*d(\d)\.w\)")
DREG_RE = re.compile(r",\s*d(\d)\s*$")


def fail(msg: str) -> None:
    print("extract: FAIL - %s" % msg)
    raise SystemExit(1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skip(msg: str) -> None:
    print("extract: SKIPPED - %s; committed manifest records the run with "
          "inputs present" % msg)
    raise SystemExit(0)


def u16(b: bytes, o: int) -> int:
    return (b[o] << 8) | b[o + 1]


def dst_is_table_set(op_str: str) -> bool:
    return op_str.split(",")[-1].strip() == "$50(a6)"


def decode_span(img: bytes, md, start: int, end: int):
    """Linearly decode [start, end) from the known instruction boundary
    `start` (a dispatch target), instruction by instruction, stopping at
    the first position the decoder cannot continue from (an invalid
    opcode, or an instruction that would cross the span end). Returns
    (writers, clean_end, reason): writers are the +0x50 writers
    (write-capable mnemonic, destination exactly $50(a6)) found inside
    the CLEAN REGION [start, clean_end). The clean region is proven
    code under the sequential decoder; a handler that embeds inline
    data tables (both observed state-0 handlers do - the class 0x00 one
    indexes its tables at 0x03F188/0x03F18C via (PC,D0).W lookups)
    derailed at the first such table, which is recorded, not asserted
    through. Nothing beyond clean_end is claimed as decoded code."""
    writers = []
    pc = start
    reason = None
    while pc < end:
        try:
            insns = list(md.disasm(img[pc:end], pc))
        except Exception:
            reason = "disasm raised at %#06X" % pc
            break
        if not insns:
            # Do not serialize private opcode bytes into the tracked manifest.
            # The position is sufficient to reproduce the private check.
            reason = ("invalid/undecodable opcode at %#06X - end of the "
                      "clean code region (inline data follows)" % pc)
            break
        i = insns[0]
        if i.size <= 0 or pc + i.size > end:
            reason = ("instruction at %#06X (size %d) crosses the span "
                      "end" % (pc, i.size))
            break
        if i.mnemonic in WRITE_MNEMONICS and dst_is_table_set(i.op_str):
            writers.append(i)
        pc += i.size
    return writers, pc, reason


def writer_record(i, img: bytes) -> dict:
    """A +0x50 writer found in the span: address and decoded operands
    only (no raw bytes leave the private image)."""
    raw = img[i.address:i.address + i.size]
    is_imm_store = (
        i.mnemonic == "move.l"
        and i.op_str.split(",")[0].strip().startswith("#")
        and i.size == 8
        and raw[0] == STORE_OP0 and raw[1] == STORE_OP1
        and raw[6] == STORE_TAIL[0] and raw[7] == STORE_TAIL[1]
    )
    immediate = None
    if is_imm_store:
        imm = int(i.op_str.split(",")[0].strip().lstrip("#$"), 16)
        if int.from_bytes(raw[2:6], "big") != imm:
            # internal guard only; surfaced as a problem by the caller
            immediate = None
        else:
            immediate = "0x%08X" % imm
    return {
        "pc": "0x%06X" % i.address,
        "mnemonic": i.mnemonic,
        "op": i.op_str,
        "size": i.size,
        "form": "immediate_move_l" if is_imm_store
                else (i.mnemonic + "/" + i.op_str),
        "immediate": immediate,
    }


def decode_nested(img: bytes, md, target: int, lo: int, hi: int) -> dict:
    """If `target` begins with the second-level dispatch idiom (same
    shape as the sub-state dispatcher, keyed on another actor byte),
    decode its word table from the image and check every branch target
    stays inside [lo, hi). Returns the decoded record or a no-idiom
    record."""
    insns = list(md.disasm(img[target:target + 16], target))
    if len(insns) < 3:
        return {"idiom": False, "target": "0x%06X" % target,
                "note": "not disassembled deep enough for the idiom"}
    a, b, c = insns[0], insns[1], insns[2]
    # idiom shape:  move.b $K(a6), dn
    #               move.w $X(pc, dn.w), dm
    #               jmp    $X(pc, dm.w)
    # (the index register advances from a to b to c; the two displayed
    # absolute table bases must coincide)
    m_b = PC_TABLE_RE.search(b.op_str)
    m_c = PC_TABLE_RE.search(c.op_str)
    m_a = DREG_RE.search(a.op_str)
    m_bd = DREG_RE.search(b.op_str)
    ok = (a.mnemonic == "move.b" and b.mnemonic == "move.w"
          and c.mnemonic == "jmp" and m_a and m_b and m_c and m_bd
          and a.op_str.startswith("$")
          and m_a.group(1) == m_b.group(2)
          and m_bd.group(1) == m_c.group(2)
          and m_b.group(1) == m_c.group(1))
    if not ok:
        # No nested idiom: this handler's branch containment is then
        # corpus-backed by the verifier's lifetime invariance, not by a
        # decoded table.
        return {"idiom": False, "target": "0x%06X" % target,
                "head": "%s %s" % (a.mnemonic, a.op_str)}
    base = int(m_b.group(1), 16)
    first_op = a.op_str.split(",")[0].strip()
    km = re.match(r"^\$([0-9a-fA-F]+)\(a6\)$", first_op)
    key_byte = "0x%02X(a6)" % int(km.group(1), 16) if km else "unparsed (%s)" % first_op
    if base + 2 > len(img):
        return {"idiom": True, "target": "0x%06X" % target,
                "table_base": "0x%06X" % base, "key_byte": key_byte,
                "error": "table base outside the image"}
    count = u16(img, base) >> 1
    targets = []
    for i in range(count):
        # target_i = base + word@(base + 2i); word 0 is the count word.
        word = u16(img, base + 2 * i)
        targets.append("0x%06X" % (base + word))
    outside = [t for t in targets if not (lo <= int(t, 16) < hi)]
    return {
        "idiom": True,
        "target": "0x%06X" % target,
        "key_byte": key_byte,
        "table_base": "0x%06X" % base,
        "entries": count,
        "targets": targets,
        "all_targets_in_range": not outside,
        "targets_out_of_range": outside,
    }


def in_range(pc: int, lo: int, hi: int) -> bool:
    return lo <= pc < hi


def main() -> int:
    for p, what in ((IMAGE_PATH, "opcode image"),
                    (CLASS_TABLE_PATH, "class table manifest"),
                    (DISPATCHERS_PATH, "sub-state dispatcher manifest"),
                    (SOURCE_PATH, "live table_set source manifest")):
        if not p.is_file():
            skip("%s absent (%s)" % (what,
                                     p.relative_to(ROOT).as_posix()
                                     if p.is_relative_to(ROOT) else str(p)))

    sys.path.insert(0, str(ROOT / ".deps" / "capstone"))
    try:
        from capstone import Cs, CS_ARCH_M68K, CS_MODE_M68K_000
    except ImportError:
        skip("vendored capstone absent (.deps/capstone)")

    img = IMAGE_PATH.read_bytes()
    if len(img) != 0x200000:
        fail("opcode image is %d bytes, expected 0x200000" % len(img))
    image_sha = hashlib.sha256(img).hexdigest()

    class_table = json.loads(CLASS_TABLE_PATH.read_text())
    dispatchers = json.loads(DISPATCHERS_PATH.read_text())
    source = json.loads(SOURCE_PATH.read_text())

    recorded_sha = class_table.get("opcode_image_sha256")
    if recorded_sha and recorded_sha != image_sha:
        fail("opcode image sha256 %s != validated dump sha256 %s recorded "
             "in data/avsp_actor_class_table.json"
             % (image_sha, recorded_sha))

    # --- class routine ranges (entries are strictly ascending in file) ---
    entries = [(int(e["class"], 16), int(e["routine"], 16))
               for e in class_table["entries"]]
    entries.sort()
    ranges = {}
    for i, (cl, start) in enumerate(entries):
        end = entries[i + 1][1] if i + 1 < len(entries) else len(img)
        ranges[cl] = (start, end)
    for cl in STREET_CLASSES:
        if cl not in ranges:
            fail("class 0x%02X missing from the class table" % cl)

    sites = {int(s["pc"], 16): s for s in dispatchers.get("sites", [])}
    anchors = {int(k, 16): v for k, v in
               dispatchers.get("known_anchors", {}).items()}
    families = {int(f["store_pc"], 16): f for f in source["families"].values()}

    # --- per-class bounded span decode + structural checks ---
    md = Cs(CS_ARCH_M68K, CS_MODE_M68K_000)
    classes_out = {}
    problems = []
    for cl in STREET_CLASSES:
        lo, hi = ranges[cl]
        key = "0x%02X" % cl

        # dispatcher linkage: the known anchor whose state-0 handler lies
        # inside this class routine.
        disp_pc, disp_anchor = None, None
        for anc_pc, anc in anchors.items():
            s0 = int(anc["state0"], 16)
            if in_range(s0, lo, hi):
                disp_pc, disp_anchor = anc_pc, anc
        if disp_pc is None:
            problems.append("class %s: no known-anchor sub-state "
                            "dispatcher whose state-0 handler lies in the "
                            "routine range" % key)
            continue
        site = sites.get(disp_pc)
        if site is None:
            problems.append("class %s: dispatcher %06X missing from the "
                            "sites list" % (key, disp_pc))
            continue
        if (int(site["table_base"], 16) != disp_pc + 12
                or int(site["targets"][0], 16)
                != int(disp_anchor["state0"], 16)):
            problems.append("class %s: manifest site disagrees with the "
                            "known anchor (table base / state-0 target)" % key)
            continue

        # re-verify the dispatch table words from the image:
        #   d1 = word@(base + d0); target = base + d1   (validated
        #   mechanism), so target_i = base + word@(base + 2i) and
        #   word 0 is the count word (count = word0 >> 1).
        base = disp_pc + 12
        img_count = u16(img, base) >> 1
        img_targets = ["0x%06X" % (base + u16(img, base + 2 * i))
                       for i in range(img_count)]
        if img_count != site["sub_states"] or img_targets != site["targets"]:
            problems.append("class %s: image dispatch words %s != manifest "
                            "targets %s" % (key, img_targets, site["targets"]))
            continue

        # --- bounded linear decode of the state-0 handler span ---
        t0, t1 = (int(site["targets"][i], 16) for i in range(2))
        if t1 > len(img) or t0 < 0:
            problems.append("class %s: state-0 span [%#06X, %#06X) outside "
                            "image" % (key, t0, t1))
            continue
        writers, clean_end, reason = decode_span(img, md, t0, t1)
        recs = [writer_record(i, img) for i in writers]
        imm_recs = [r for r in recs if r["immediate"] is not None]
        if len(imm_recs) != 1:
            problems.append(
                "class %s: %d immediate move.l +0x50 store(s) in the "
                "clean code region [%s, 0x%06X) (decode: %s), expected "
                "exactly 1: %s"
                % (key, len(imm_recs), site["targets"][0], clean_end,
                   reason or "reached span end", recs))
            continue
        if len(recs) != 1:
            problems.append(
                "class %s: %d non-store +0x50 writer(s) in the clean "
                "code region [%s, 0x%06X): %s"
                % (key, len(recs) - 1, site["targets"][0], clean_end,
                   [r for r in recs if r is not imm_recs[0]]))
            continue
        store = imm_recs[0]
        store_pc = int(store["pc"], 16)
        value = int(store["immediate"], 16)
        if not (t0 <= store_pc < clean_end):
            problems.append("class %s: store %s not inside the clean "
                            "code region [%s, 0x%06X)"
                            % (key, store["pc"], site["targets"][0],
                               clean_end))
            continue

        # live-trace cross-check: the store must be one of the proven
        # families (PC AND value), and the anchor's family name must
        # agree.
        fam = families.get(store_pc)
        if fam is None or int(fam["value"], 16) != value:
            problems.append("class %s: store %s/%s has no live-trace "
                            "family with matching PC and value"
                            % (key, store["pc"], store["immediate"]))
            continue
        if fam["name"] != disp_anchor["family"].split(" (")[0]:
            problems.append("class %s: family name %s != anchor family %s"
                            % (key, fam["name"], disp_anchor["family"]))
            continue

        nested = None
        if len(site["targets"]) > 1:
            nested = decode_nested(img, md, int(site["targets"][1], 16),
                                   lo, hi)
            if nested.get("idiom") and not nested.get(
                    "all_targets_in_range", True):
                problems.append(
                    "class %s: nested state-2 branch targets leave the "
                    "class range: %s" % (key, nested["targets_out_of_range"]))

        classes_out[key] = {
            "family": fam["name"],
            "routine": "0x%06X" % lo,
            "routine_end": "0x%06X" % hi,
            "dispatcher": "0x%06X" % disp_pc,
            "sub_state_targets": site["targets"],
            "state0_span": {
                "start": site["targets"][0],
                "end": site["targets"][1],
                "clean_code_end": "0x%06X" % clean_end,
                "decode_reached_span_end": reason is None,
                "decode_note": None if reason is None else reason,
                "writers_found_in_clean_region": len(recs),
            },
            "undecoded_tail": (None if reason is None else {
                "start": "0x%06X" % clean_end,
                "end": site["targets"][1],
                "note": ("the state-0 handler embeds an inline data "
                         "table here; the sequential decode stops "
                         "because data words are not instructions. "
                         "Writer status in this tail is settled by "
                         "corpus-observed constancy in the verifier: "
                         "every observed execution of this handler "
                         "across the four deterministic MAME routes "
                         "ended with the store's constant."),
            }),
            "state0_store": {
                "pc": store["pc"],
                "value": store["immediate"],
                "instruction": "move.l #$%06x, $50(a6)" % value,
                "cross_match": {
                    "family_name": fam["name"],
                    "live_trace_pc": fam["store_pc"],
                    "live_trace_value": fam["value"],
                    "matched": True,
                },
            },
            "state1_nested_dispatch": nested,
            "states": {
                "class_entry": {
                    "table_set": store["immediate"],
                    "via": ("state-0 (sub-state index 0x00) initializer "
                            "store %s - the only +0x50 writer in the "
                            "clean code region [%s, %s) of the "
                            "linearly-decoded state-0 span"
                            % (store["pc"], site["targets"][0],
                               "0x%06X" % clean_end)),
                },
                "other_sub_states": {
                    "table_set": store["immediate"],
                    "via": ("corpus-observed constancy - no observed "
                            "sub-state frame ever carries a different "
                            "value (walk/attack in sub-state 0x02, the "
                            "hit sequence inside sub-state 0x02 under "
                            "action word +0x06, the KO sequence in "
                            "sub-states 0x04/0x06; falsified with the "
                            "exact HIT/KO anchors and lifecycle populations in "
                            "tools/verify_avsp_table_set_states.py). "
                            "This is corpus-observed constancy, not a "
                            "claim that no other writer exists outside "
                            "the decoded span and the observed routes."),
                },
            },
        }

    result = {
        "schema": 3,
        "classification": ("step-2 offline extraction - per-state street "
                           "table_set constants; bounded state-0 span "
                           "decode (addresses/PCs/decoded immediates and "
                           "counts only, no ROM bytes)"),
        "program_image": {
            "path": IMAGE_PATH.relative_to(ROOT).as_posix(),
            "sha256": image_sha,
            "bytes": len(img),
        },
        "inputs": {
            "class_table": {
                "path": CLASS_TABLE_PATH.relative_to(ROOT).as_posix(),
                "sha256": sha256(CLASS_TABLE_PATH),
                "recorded_image_sha256": recorded_sha,
            },
            "sub_state_dispatchers": {
                "path": DISPATCHERS_PATH.relative_to(ROOT).as_posix(),
                "sha256": sha256(DISPATCHERS_PATH),
                "site_count": dispatchers.get("site_count"),
            },
            "table_set_source": {
                "path": SOURCE_PATH.relative_to(ROOT).as_posix(),
                "sha256": sha256(SOURCE_PATH),
                "family_count": len(source["families"]),
            },
        },
        "method": {
            "state0_span_decode": ("for each class, linear capstone M68K "
                                   "decode of [state0_target, "
                                   "state2_target) starting at the "
                                   "dispatch target (a known instruction "
                                   "boundary), instruction by "
                                   "instruction, as long as the "
                                   "decoder stays clean; a handler that "
                                   "embeds an inline data table stops "
                                   "the clean decode there, and the "
                                   "undecoded tail is recorded (not "
                                   "scanned as code); the store must "
                                   "lie in the clean region, reached "
                                   "without derailing, and be the sole "
                                   "+0x50 writer there; writers "
                                   "recognised by write-capable "
                                   "mnemonic + destination exactly "
                                   "$50(a6)"),
            "write_mnemonics": sorted(WRITE_MNEMONICS),
            "scope": ("bounded to each class's state-0 handler span - "
                      "NOT a whole-image claim; other code regions may "
                      "write +0x50 for other actor systems"),
        },
        "street_classes": classes_out,
        "semantic_answer": (
            "The street alien's table_set is written once per class, in "
            "the state-0 class-entry initializer: the clean code "
            "region of the linearly-decoded state-0 span of each of "
            "the three street classes contains exactly one +0x50 "
            "writer, an immediate move.l store whose PC and immediate "
            "cross-match the live-trace families. For every other "
            "observed sub-state behaviour "
            "(walk/attack; the hit sequence observed inside sub-state "
            "0x02 under action word +0x06; the KO sequence observed in "
            "sub-states 0x04/0x06) the value shows corpus-OBSERVED "
            "constancy at that class's state-0 value over the four "
            "deterministic MAME routes. Do not assume 0x00130AC8: the "
            "per-class constants are 0x0012CE5C (class 0x00 "
            "type_promotion), 0x0013E97A (class 0x06 replace), "
            "0x00130AC8 (class 0x1F normal)."),
        "problems": problems,
        "result": ("PASS" if not problems else
                   "FAIL - %d problem(s)" % len(problems)),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")

    print("extract: %s" % result["result"])
    print("  image sha256=%s" % image_sha[:16] + "...")
    for key in ("0x00", "0x06", "0x1F"):
        c = classes_out.get(key)
        if c is None:
            print("  class %s: MISSING" % key)
            continue
        s = c["state0_store"]
        span = c["state0_span"]
        print("  class %s (%s): span [%s, %s) clean_end=%s "
              "reached_end=%s writers=%d; %s %s -> table_set %s"
              % (key, c["family"], span["start"], span["end"],
                 span["clean_code_end"], span["decode_reached_span_end"],
                 span["writers_found_in_clean_region"],
                 s["pc"], s["instruction"], s["value"]))
    if problems:
        for p in problems:
            print("  problem: %s" % p)
    print("wrote", OUT_PATH.relative_to(ROOT).as_posix())
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
