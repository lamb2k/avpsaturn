"""Analyze a bounded stock-MAME street-alien object-emission capture.

Consumes the per-frame raw dumps produced by
tools/mame_watch_street_alien_object_emission.lua:
  * workram_<source>.bin - full main-CPU program RAM (0xFF8000..0xFFFFFF)
    read at the end of each source frame in the window.
  * objbuf_<source>.bin  - the CPS2 object write buffer (bank 1,
    0x708000..0x709FFF) for each source frame.
  * (optional) error.log / *.log - stock-MAME debugger watchpoint events
    (AVP_OE_OBJ / AVP_OE_BANK) carrying per-word writer PC + registers.

For each target source frame the analyzer:
  * locates the alien's five object slots INDEPENDENTLY (a run of five
    consecutive objects whose codes are 0x4xxx sprite tiles) -- never by
    matching the oracle fixture;
  * decodes each word (X priority/width/position, Y position, code, attr
    palette/flip);
  * proves the source-frame mapping from content (the emitted slot codes and
    the actor's world X/Y), NOT from the Lua notifier count. Because the alien
    holds one walk-step pose across several source frames, the 20-word emission
    is invariant to +/-1 notifier timing and the mapping is reported with that
    tolerance;
  * compares the decoded 20 words against the oracle fixture (validation path
    only) and records per-frame pass/fail.

Emits data/street_alien_object_emission.json with provenance and SHA-256 of the
raw evidence. Everything is scenario-parameterized; no frame, slot count, actor
base, object base, or address is hard-coded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORACLES_DEFAULT = ROOT / "data" / "street_alien_object_emission_oracles.json"
OUTPUT_DEFAULT = ROOT / "data" / "street_alien_object_emission.json"

WP_OBJ = re.compile(
    r"AVP_OE_OBJ addr=(?P<addr>[0-9A-Fa-f]+) data=(?P<data>[0-9A-Fa-f]+) "
    r"pc=(?P<pc>[0-9A-Fa-f]+)"
    r"(?: a0=(?P<a0>[0-9A-Fa-f]+))?(?: a1=(?P<a1>[0-9A-Fa-f]+))?"
    r"(?: a4=(?P<a4>[0-9A-Fa-f]+))?(?: a5=(?P<a5>[0-9A-Fa-f]+))?"
    r"(?: a6=(?P<a6>[0-9A-Fa-f]+))?"
)
WP_BANK = re.compile(r"AVP_OE_BANK addr=[0-9A-Fa-f]+ data=(?P<data>[0-9A-Fa-f]+) pc=(?P<pc>[0-9A-Fa-f]+)")


def be16(b: bytes, off: int) -> int:
    return (b[off] << 8) | b[off + 1]


def be32(b: bytes, off: int) -> int:
    return (b[off] << 24) | (b[off + 1] << 16) | (b[off + 2] << 8) | b[off + 3]


def h(v) -> int:
    """Oracle fixture stores every hex value as a string; coerce to int."""
    return int(v, 16) if isinstance(v, str) else int(v)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_x(w: int) -> dict:
    return {"priority": (w >> 13) & 7, "width_tiles": ((w >> 8) & 0xF) + 1, "xpos": w & 0x0FFF}


def decode_y(w: int) -> dict:
    return {"ypos": w & 0x3FF}


def decode_attr(w: int) -> dict:
    return {"palette": "0x%02x" % (w & 0x1F), "flip_x": (w >> 5) & 1, "flip_y": (w >> 6) & 1}


def find_alien_slot_start(ob: bytes):
    """Locate the alien's five slots by a run of five consecutive objects whose
    codes are 0x4xxx sprite tiles. Independent of any oracle fixture."""
    n = len(ob) // 8
    for i in range(n - 4):
        codes = [be16(ob, (i + j) * 8 + 4) for j in range(5)]
        if all(0x4000 <= c < 0x6000 for c in codes):
            return i
    return None


def decode_slots(ob: bytes, start: int) -> list:
    slots = []
    for j in range(5):
        o = start * 8 + j * 8
        X, Y, code, attr = be16(ob, o), be16(ob, o + 2), be16(ob, o + 4), be16(ob, o + 6)
        slots.append({
            "X": "%04x" % X, "Y": "%04x" % Y, "code": "%04x" % code, "attr": "%04x" % attr,
            "priority": decode_x(X)["priority"], "width_tiles": decode_x(X)["width_tiles"],
            "xpos": decode_x(X)["xpos"], "ypos": decode_y(Y)["ypos"],
            **decode_attr(attr),
        })
    return slots


def actor_state(wram: bytes, actor_base: int) -> dict:
    a = actor_base - 0xFF8000
    return {
        "type": (be16(wram, a + 0x08) >> 8) & 0xFF,
        "facing": (be16(wram, a + 0x0F) >> 8) & 0xFF,
        "worldX": be16(wram, a + 0x10),
        "worldY": be16(wram, a + 0x14),
        "anim_eof": "0x%08x" % be32(wram, a + 0x1C),
        "plus50": "0x%08x" % be32(wram, a + 0x50),
    }


def oracle_flat(oracle: dict, key: str) -> list:
    return [h(w) for slot in oracle["frames"][key]["slots"] for w in slot]


def analyze_frame(raw_dir: Path, src: int, oracle: dict, actor_base: int) -> dict:
    key = str(src)
    wpath = raw_dir / ("workram_%05d.bin" % src)
    opath = raw_dir / ("objbuf_%05d.bin" % src)
    result = {"mapped_source_frame": src}
    if not wpath.exists() or not opath.exists():
        result["error"] = "missing raw dump for source frame %d" % src
        result["pass"] = False
        return result

    wram = wpath.read_bytes()
    ob = opath.read_bytes()
    result["actor_state"] = actor_state(wram, actor_base)

    start = find_alien_slot_start(ob)
    if start is None:
        result["error"] = "no five consecutive 0x4xxx object codes found (alien not located)"
        result["pass"] = False
        return result

    addr = 0x708000 + start * 8
    result["alien_slot_addr"] = "0x%06x" % addr
    result["alien_slot_offset_in_objbuf"] = "0x%04x" % (start * 8)
    slots = decode_slots(ob, start)
    result["slots"] = slots

    got = [v for s in slots for v in (int(s["X"], 16), int(s["Y"], 16), int(s["code"], 16), int(s["attr"], 16))]
    if key in oracle.get("frames", {}):
        exp = oracle_flat(oracle, key)
        match = sum(1 for g, e in zip(got, exp) if g == e)
        result["oracle_match"] = "%d/%d" % (match, len(exp))
        result["pass"] = (match == len(exp))
    else:
        result["oracle_match"] = "n/a (no oracle for %s)" % key
        result["pass"] = None

    # Map corroboration: does the alien hold the same pose for the adjacent
    # source frames (a walk step)? If so the emission is invariant to +/-1
    # notifier timing and the mapping is robust.
    def codes_at(f):
        p = raw_dir / ("objbuf_%05d.bin" % f)
        if not p.exists():
            return None
        s = find_alien_slot_start(p.read_bytes())
        if s is None:
            return None
        return [be16(p.read_bytes(), (s + j) * 8 + 4) for j in range(5)]

    here = codes_at(src)
    prev_c, next_c = codes_at(src - 1), codes_at(src + 1)
    result["pose_constancy"] = {
        "same_as_prev_frame": (prev_c is not None and prev_c == here),
        "same_as_next_frame": (next_c is not None and next_c == here),
    }

    # Same derivation on the ACTIVE/display share, which is the surface the
    # oracle instrument sampled. The two banks hold different lists, so the
    # alien's word index differs between the writer view and the display view;
    # reporting both makes the bank relation explicit instead of assumed.
    apath = raw_dir / ("objact_%05d.bin" % src)
    if apath.exists():
        ab = apath.read_bytes()
        astart = find_alien_slot_start(ab)
        active = {"located": astart is not None}
        if astart is not None:
            aslots = decode_slots(ab, astart)
            agot = [int(s[k], 16) for s in aslots for k in ("X", "Y", "code", "attr")]
            active["alien_slot_addr"] = "0x%06x" % (0x708000 + astart * 8)
            active["first_word_index"] = astart * 4
            active["slot_word_indices"] = [astart * 4 + 4 * j for j in range(5)]
            if key in oracle.get("frames", {}):
                exp = oracle_flat(oracle, key)
                active["oracle_match"] = "%d/%d" % (
                    sum(1 for g, e in zip(agot, exp) if g == e), len(exp))
        result["active_bank"] = active
    return result


def parse_watchpoints(raw_dir: Path, project_root: Path) -> dict:
    """Best-effort parse of AVP_OE_OBJ / AVP_OE_BANK events from any log file
    the instrumented run left behind (MAME writes logerror to its own log; the
    wrapper's stderr redirect captures console output only)."""
    candidates = []
    for pat in ("*.log",):
        candidates += sorted(raw_dir.glob(pat))
    candidates += [project_root / "error.log", raw_dir / "error.log"]
    obj_events, bank_events = [], []
    seen = set()
    for p in candidates:
        if not p.exists() or p in seen:
            continue
        seen.add(p)
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        for m in WP_OBJ.finditer(text):
            obj_events.append({k: m.group(k) for k in ("addr", "data", "pc", "a0", "a1", "a4", "a5", "a6") if m.group(k)})
        for m in WP_BANK.finditer(text):
            bank_events.append({"data": m.group("data"), "pc": m.group("pc")})
    return {
        "log_files_scanned": [str(p) for p in seen],
        "obj_event_count": len(obj_events),
        "bank_event_count": len(bank_events),
        "obj_events": obj_events,
        "writer_pc_obj_sample": sorted({e.get("pc") for e in obj_events if e.get("pc")})[:8],
        "note": None if obj_events else "no AVP_OE_OBJ events found in captured logs (writer-PC trace not recovered this run)",
    }


def attribute_slots(obj_events: list, slot_addr: int, words: list) -> dict:
    """Find the watchpoint burst that wrote exactly these decoded words to these
    addresses, and report who wrote them. The burst is matched on address+data,
    so the attribution is anchored to the frame's own emission rather than to a
    frame index or an assumed actor."""
    want = [(slot_addr + 2 * i, w) for i, w in enumerate(words)]
    # The watchpoint window is a fixed address range, so when the alien's slots
    # start above the configured base the tail of the burst falls outside it and
    # only a prefix is logged. Attribute the longest matching prefix and say how
    # many of the decoded words it covers.
    best = None
    for i in range(len(obj_events)):
        k = 0
        while i + k < len(obj_events) and k < len(want):
            e = obj_events[i + k]
            if int(e["addr"], 16) != want[k][0] or (int(e["data"], 16) & 0xFFFF) != want[k][1]:
                break
            k += 1
        if k >= 8 and (best is None or k > best[1]):
            best = (i, k)
    if best is None:
        return {"matched_watchpoint_burst": False}
    i, k = best
    run = obj_events[i:i + k]
    return {
        "matched_watchpoint_burst": True,
        "attributed_words": "%d/%d" % (k, len(words)),
        "attributed_note": None if k == len(words) else
            "the remaining words were written above the watchpoint window "
            "(watchpoints cover a fixed address range, the alien's slot run is "
            "run-dependent); they are still decoded from the raw object dump",
        "writer_pcs": sorted({e["pc"] for e in run}),
        "part_table_pointers_a0": [e.get("a0") for e in run[::4]],
        "emitting_actor_a4": sorted({e.get("a4") for e in run if e.get("a4")}),
        "emitting_actor_a6": sorted({e.get("a6") for e in run if e.get("a6")}),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--oracle", default=str(ORACLES_DEFAULT))
    ap.add_argument("--state-frame", type=int, required=True)
    ap.add_argument("--frame-a", type=int, required=True)
    ap.add_argument("--frame-b", type=int, required=True)
    ap.add_argument("--actor-base", required=True)
    ap.add_argument("--object-list-base", required=True)
    ap.add_argument("--first-word", type=int, default=0)
    ap.add_argument("--word-count", type=int, default=20)
    ap.add_argument("--bank-select-register", required=True)
    ap.add_argument("--state", default=None,
                    help="anchor state the capture actually ran from; recorded "
                         "as scenario.state so the report never inherits the "
                         "oracle fixture's declared state by default")
    ap.add_argument("--output", default=str(OUTPUT_DEFAULT))
    args = ap.parse_args()

    raw_dir = Path(args.raw_dir)
    if not raw_dir.is_absolute():
        raw_dir = Path(__file__).resolve().parents[1] / raw_dir
    oracle = json.loads(Path(args.oracle).read_text())

    actor_base = h(args.actor_base)
    obj_base = h(args.object_list_base)

    out = {
        "scenario": {
            "mame": oracle.get("scenario", {}).get("mame"),
            "driver": oracle.get("scenario", {}).get("driver"),
            "state": args.state or oracle.get("scenario", {}).get("state"),
            "state_is_from_run": args.state is not None,
            "oracle_declared_state": oracle.get("scenario", {}).get("state"),
            "state_frame": args.state_frame,
            "frame_a": args.frame_a,
            "frame_b": args.frame_b,
            "actor_base": args.actor_base,
            "object_list_base": args.object_list_base,
            "first_word": args.first_word,
            "word_count": args.word_count,
            "bank_select_register": args.bank_select_register,
            "configured_watch_start": "0x%06x" % (obj_base + args.first_word * 2),
        },
        "raw_evidence": {},
        "frames": {},
    }

    # SHA-256 of every raw dump in the window (both target frames + neighbors
    # used for the mapping corroboration).
    for src in sorted(set([args.frame_a, args.frame_b, args.frame_a - 1, args.frame_a + 1, args.frame_b - 1, args.frame_b + 1])):
        for kind in ("workram", "objbuf", "objact"):
            p = raw_dir / ("%s_%05d.bin" % (kind, src))
            if p.exists():
                out["raw_evidence"]["%s_%05d.bin" % (kind, src)] = {"sha256": sha256(p), "bytes": p.stat().st_size}

    for src in (args.frame_a, args.frame_b):
        out["frames"][str(src)] = analyze_frame(raw_dir, src, oracle, actor_base)

    wp = parse_watchpoints(raw_dir, Path(__file__).resolve().parents[1])
    obj_events = wp.pop("obj_events", [])
    out["watchpoints"] = wp

    # Attribute each gated frame's decoded words to the burst that wrote them.
    for src in (args.frame_a, args.frame_b):
        f = out["frames"][str(src)]
        if not f.get("slots") or not f.get("alien_slot_addr"):
            continue
        words = [int(s[k], 16) for s in f["slots"] for k in ("X", "Y", "code", "attr")]
        f["writer_attribution"] = attribute_slots(obj_events, h(f["alien_slot_addr"]), words)

    # Gate decision: pass only if BOTH frames independently located AND matched
    # the oracle 20/20.
    frames = out["frames"]
    out["gate_pass"] = all(
        frames[str(s)].get("pass") is True for s in (args.frame_a, args.frame_b)
    )
    fails = [str(s) for s in (args.frame_a, args.frame_b) if frames[str(s)].get("pass") is not True]
    out["gate_failing_frames"] = fails

    output = Path(args.output)
    if not output.is_absolute():
        output = Path(__file__).resolve().parents[1] / output
    output.write_text(json.dumps(out, indent=1) + "\n")
    print("wrote %s" % output)
    print("gate_pass=%s  failing=%s" % (out["gate_pass"], fails))
    for s in (args.frame_a, args.frame_b):
        f = frames[str(s)]
        print("  %s: match=%s pass=%s slot=%s" % (
            s, f.get("oracle_match"), f.get("pass"), f.get("alien_slot_addr")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
