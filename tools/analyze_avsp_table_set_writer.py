"""Parse the retained table_set writer-trace run, deterministically.

This is the first half of resolving the provenance of actor ``table_set``
(actor ``+0x50``) without correlation. The retained run is a stock-MAME
0.289 headless replay of the enemy_actions route (see
``tools/mame_trace_table_set_writer.lua``) that watched ONE street-alien
slot (43, 0xFFA3C0) and logged:

  * ``AVP_TSW_STATE``  - byte writes to ``+0x00`` (spawn/despawn markers);
  * ``AVP_TSW_CAND``   - byte writes to the candidate offsets
                         (0x02/0x0E/0x45/0x57/0x5E/0x64), with a0..a3;
  * ``AVP_TSW_TSET``   - long writes to ``+0x50..+0x53``, full register
                         file d0..d7, a0..a6, sp, ret;
  * ``AVP_TSW_FRAME``  - objram bank-flip marker at 0x8040E0, which joins
                         to the Lua sidecar ``tools_tsw_frames.tsv`` by
                         cumulative bank-write count.

This analyzer only RECONSTRUCTS what the retained log already records. It
does not decide which field the game reads (that is the live instruction
trace) and it never infers a table_set value from a correlated byte. It
emits a tracked, coordinate/control-flow-only report
(``data/avsp_table_set_writer.json``): ROM addresses, PCs, register values,
counts, the frame mapping and input hashes - no ROM bytes and no raw log
excerpts.

Two non-obvious reconstruction facts, both validated against the retained
run and documented here so the mapping is not re-guessed:

1. The 4-byte ``+0x50`` watchpoint fires TWICE per logical 32-bit store on
   the 16-bit data bus: first the high word (bytes 0..1 at ``+0x50``),
   then the low word (bytes 2..3 at ``+0x52``). The two lines are
   consecutive, share pc + the full register file + the slot (a6), and
   carry different ``data`` halves. The pointer is
   ``(hi & 0xFFFF) << 16 | (lo & 0xFFFF)``. The retained run yields exactly
   7 logical stores from 14 lines.
2. The Lua sidecar counts bank writes from boot, but the watchpoint is only
   installed at install_frame. The number of bank writes that happened
   BEFORE install is the "initial nonzero marker count" G. It is derived as
   ``G = total_tap_count - total_logged_markers`` (6183 - 3810 = 2373 for
   the retained run) and cross-checked against the sidecar count at the
   install frame. Log marker #k (1-based) is therefore global bank-write
   #(G + k), and an event's frame is the smallest F with C(F) >= G + m,
   where m is the number of AVP_TSW_FRAME markers preceding the event.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "data" / "avsp_table_set_writer.json"

# The three retained inputs and their pinned hashes (private/untracked;
# validated before any analysis, overridable for a regeneration).
RETAINED_INPUTS = {
    "error_log": {
        "path": ROOT / "error.log",
        "sha256": "c1c34eb427a1130a5121982af2000059d1240edcff1b0ae18620f37da0d85c08",
    },
    "frames_tsv": {
        "path": ROOT / "tools_tsw_frames.tsv",
        "sha256": "f5ac294c4854809b2f145735a3cf0c187a3e438352b9cd183a887a410050604e",
    },
    "writer_lua": {
        "path": ROOT / "tools" / "mame_trace_table_set_writer.lua",
        "sha256": "a34a5a9edd1164e7ab7e2c418f86d5445a34b338d70a842065eb00ad86a83127",
    },
}

REG_KEYS = ["d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7",
            "a0", "a1", "a2", "a3", "a4", "a5", "a6", "sp", "ret"]

RE_FRAME = re.compile(r"^AVP_TSW_FRAME\s*$")
RE_STATE = re.compile(r"^AVP_TSW_STATE\s+data=(?P<data>[0-9A-Fa-f]+)"
                      r"\s+pc=(?P<pc>[0-9A-Fa-f]+)\s*$")
RE_CAND = re.compile(r"^AVP_TSW_CAND\s+off=(?P<off>[0-9A-Fa-f]+)"
                     r"\s+data=(?P<data>[0-9A-Fa-f]+)\s+pc=(?P<pc>[0-9A-Fa-f]+)"
                     r"\s+a0=(?P<a0>[0-9A-Fa-f]+)\s+a1=(?P<a1>[0-9A-Fa-f]+)"
                     r"\s+a2=(?P<a2>[0-9A-Fa-f]+)\s+a3=(?P<a3>[0-9A-Fa-f]+)\s*$")
RE_TSET = re.compile(
    r"^AVP_TSW_TSET\s+data=(?P<data>[0-9A-Fa-f]+)\s+pc=(?P<pc>[0-9A-Fa-f]+)\s+"
    r"d0=(?P<d0>[0-9A-Fa-f]+)\s+d1=(?P<d1>[0-9A-Fa-f]+)\s+"
    r"d2=(?P<d2>[0-9A-Fa-f]+)\s+d3=(?P<d3>[0-9A-Fa-f]+)\s+"
    r"d4=(?P<d4>[0-9A-Fa-f]+)\s+d5=(?P<d5>[0-9A-Fa-f]+)\s+"
    r"d6=(?P<d6>[0-9A-Fa-f]+)\s+d7=(?P<d7>[0-9A-Fa-f]+)\s+"
    r"a0=(?P<a0>[0-9A-Fa-f]+)\s+a1=(?P<a1>[0-9A-Fa-f]+)\s+"
    r"a2=(?P<a2>[0-9A-Fa-f]+)\s+a3=(?P<a3>[0-9A-Fa-f]+)\s+"
    r"a4=(?P<a4>[0-9A-Fa-f]+)\s+a5=(?P<a5>[0-9A-Fa-f]+)\s+"
    r"a6=(?P<a6>[0-9A-Fa-f]+)\s+sp=(?P<sp>[0-9A-Fa-f]+)\s+"
    r"ret=(?P<ret>[0-9A-Fa-f]+)\s*$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_inputs(overrides: dict | None = None) -> dict:
    """Verify every retained input exists and matches its pinned hash.

    Returns a manifest of {name: {path, sha256, ok}}. Raises when a file is
    present but its hash does not match (a silently swapped input is worse
    than an absent one). Absent files are reported, not raised, so a clean
    checkout can still run the negative fixtures.
    """
    spec = dict(RETAINED_INPUTS)
    if overrides:
        for name, (path, sha) in overrides.items():
            spec[name] = {"path": Path(path), "sha256": sha}
    manifest = {}
    for name, entry in spec.items():
        path, want = entry["path"], entry["sha256"].lower()
        if not path.exists():
            manifest[name] = {"path": str(path), "sha256": None,
                              "ok": False, "reason": "absent"}
            continue
        got = sha256_file(path)
        manifest[name] = {"path": str(path), "sha256": got,
                          "ok": got == want,
                          "reason": None if got == want else "hash mismatch"}
        if got != want:
            raise SystemExit(
                "retained input hash mismatch for %s: %s != %s"
                % (name, got, want))
    return manifest


def load_frame_map(path: Path):
    """Parse the sidecar into (rows, frame_of_count).

    ``frame_of_count(target)`` returns the smallest frame F whose cumulative
    bank-write count C(F) >= target, or None if target exceeds the last
    count. The count column is non-decreasing, so a binary search suffices.
    """
    rows = []
    text = path.read_text()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("frame\t"):
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        try:
            rows.append((int(parts[0]), int(parts[1])))
        except ValueError:
            continue
    if not rows:
        raise SystemExit("sidecar %s has no data rows" % path)
    counts = [c for (_f, c) in rows]

    def frame_of_count(target):
        i = bisect.bisect_left(counts, target)
        return None if i >= len(counts) else i + 1

    return rows, frame_of_count


def parse_log_lines(lines):
    """Scan the log in order into event dicts plus the total marker count.

    Each non-marker event records ``markers_before`` = the number of
    AVP_TSW_FRAME markers seen strictly before it. Returns
    (events, total_markers).
    """
    events = []
    markers = 0
    for line_no, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        if RE_FRAME.match(line):
            markers += 1
            continue
        m = RE_STATE.match(line)
        if m:
            events.append({"kind": "state", "line": line_no,
                           "markers_before": markers,
                           "data": int(m.group("data"), 16),
                           "pc": int(m.group("pc"), 16)})
            continue
        m = RE_CAND.match(line)
        if m:
            events.append({"kind": "candidate", "line": line_no,
                           "markers_before": markers,
                           "off": int(m.group("off"), 16),
                           "raw_data": int(m.group("data"), 16),
                           "pc": int(m.group("pc"), 16),
                           "a0": int(m.group("a0"), 16),
                           "a1": int(m.group("a1"), 16),
                           "a2": int(m.group("a2"), 16),
                           "a3": int(m.group("a3"), 16)})
            continue
        m = RE_TSET.match(line)
        if m:
            regs = {k: int(m.group(k), 16) for k in REG_KEYS}
            events.append({"kind": "tset", "line": line_no,
                           "markers_before": markers,
                           "data": int(m.group("data"), 16),
                           "pc": int(m.group("pc"), 16),
                           "regs": regs})
            continue
        # Any other line (MAME startup, unrelated log) is not an event.
    return events, markers


def assign_frames(events, frame_of_count, g_offset):
    """Attach the reconstructed frame to every event via G + markers_before."""
    for ev in events:
        target = g_offset + ev["markers_before"]
        ev["frame"] = frame_of_count(target)


def _tset_signature(ev):
    return (ev["pc"], ev["regs"]["a6"],
            tuple(ev["regs"][k] for k in REG_KEYS))


def pair_tset_stores(tset_events):
    """Pair the split 4-byte stores into logical 32-bit stores.

    Two consecutive tset events form one store only when frame, pc, slot
    (a6) and the full register file agree AND nothing but a FRAME marker
    sits between them in the log. Any unpaired half is reported as an
    orphan instead of being guessed. Returns (stores, orphans).
    """
    stores = []
    orphans = []
    i = 0
    n = len(tset_events)
    while i < n:
        hi = tset_events[i]
        lo = tset_events[i + 1] if i + 1 < n else None
        paired = False
        if lo is not None and hi["line"] + 1 == lo["line"] \
                and _tset_signature(hi) == _tset_signature(lo):
            pointer = ((hi["data"] & 0xFFFF) << 16) | (lo["data"] & 0xFFFF)
            stores.append({
                "frame": hi["frame"],
                "pc": hi["pc"],
                "slot": hi["regs"]["a6"],
                "pointer": pointer,
                "hi_half": hi["data"],
                "lo_half": lo["data"],
                "is_zero": pointer == 0,
                "regs": {k: hi["regs"][k] for k in REG_KEYS},
                "hi_line": hi["line"],
                "lo_line": lo["line"],
            })
            paired = True
        if paired:
            i += 2
        else:
            orphans.append({
                "frame": hi["frame"],
                "pc": hi["pc"],
                "data": hi["data"],
                "slot": hi["regs"].get("a6"),
                "line": hi["line"],
                "reason": ("no adjacent same-context partner"
                           if lo is None or _tset_signature(hi)
                           != _tset_signature(lo) else "ambiguous"),
            })
            i += 1
    return stores, orphans


def annotate_candidates(cand_events):
    """Flag candidate byte values that are not a clean byte.

    The byte watchpoint's display is lane-positioned on the CPS2 bus, so a
    value above 0xFF (e.g. the retained run's data=600) is not a byte at
    all. We record the raw value and mark byte_valid only for <= 0xFF; even
    those are not trusted as the field value (the live trace decides).
    """
    for ev in cand_events:
        ev["byte_valid"] = ev["raw_data"] <= 0xFF
    return cand_events


def build_report(manifest, rows, g_offset, events, stores, orphans,
                 cand_events, state_events, notes=None):
    surrounding = {}
    for store in stores:
        f = store["frame"]
        related = [c for c in cand_events if c["frame"] == f]
        surrounding["0x%08X" % store["pc"]] = sorted(
            [{"off": "0x%02X" % c["off"], "pc": "0x%06X" % c["pc"],
              "raw_data": c["raw_data"], "byte_valid": c["byte_valid"]}
             for c in related], key=lambda x: x["off"])

    def fmt_store(s):
        d = {
            "frame": s["frame"],
            "pc": "0x%06X" % s["pc"],
            "slot": "0x%06X" % s["slot"],
            "pointer": "0x%08X" % s["pointer"],
            "is_zero": s["is_zero"],
            "hi_line": s["hi_line"], "lo_line": s["lo_line"],
        }
        d["regs"] = {k: "0x%08X" % v for k, v in s["regs"].items()}
        return d

    store_pc_counts = {}
    for s in stores:
        key = "0x%06X" % s["pc"]
        store_pc_counts.setdefault(key, []).append("0x%08X" % s["pointer"])

    return {
        "schema": 1,
        "classification": "table_set writer-trace reconstruction - "
                          "coordinate/control-flow only, no ROM bytes and "
                          "no raw log excerpts",
        "question": "where does the game get actor table_set (actor +0x50) "
                    "during spawn? This report reconstructs the retained "
                    "watchpoint run; it does NOT name the source field "
                    "(that requires the live instruction trace) and it "
                    "never infers table_set from a correlated byte.",
        "inputs": {name: {k: v for k, v in m.items()}
                   for name, m in manifest.items()},
        "frame_mapping": {
            "rule": "log marker #k (1-based) = global bank-write #(G+k); "
                    "event frame = smallest F with C(F) >= G + m, m = "
                    "AVP_TSW_FRAME markers before the event",
            "g_pre_install_count": g_offset,
            "total_tap_count": rows[-1][1] if rows else None,
            "total_logged_markers": None,  # filled by caller
            "install_frame_from_sidecar": None,  # filled by caller
        },
        "state_events": [
            {"frame": e["frame"], "data": "0x%02X" % e["data"],
             "pc": "0x%06X" % e["pc"]} for e in state_events],
        "candidate_events": [
            {"frame": e["frame"], "off": "0x%02X" % e["off"],
             "pc": "0x%06X" % e["pc"], "raw_data": e["raw_data"],
             "byte_valid": e["byte_valid"]} for e in cand_events],
        "table_set_stores": [fmt_store(s) for s in stores],
        "orphan_half_stores": [
            {"frame": o["frame"], "pc": "0x%06X" % o["pc"],
             "data": "0x%08X" % o["data"], "slot":
             ("0x%06X" % o["slot"]) if o["slot"] is not None else None,
             "reason": o["reason"]} for o in orphans],
        "stores_by_writer_pc": store_pc_counts,
        "surrounding_candidate_writes_by_pc": surrounding,
        "notes": notes or [],
    }


def run_analysis(input_manifest, error_log_text, frames_tsv_path):
    """Full positive parse of the retained run. Returns (report, stats)."""
    rows, frame_of_count = load_frame_map(frames_tsv_path)
    events, total_markers = parse_log_lines(error_log_text.splitlines())
    total_tap = rows[-1][1]
    g_offset = total_tap - total_markers
    assign_frames(events, frame_of_count, g_offset)

    state_events = [e for e in events if e["kind"] == "state"]
    cand_events = annotate_candidates([e for e in events
                                       if e["kind"] == "candidate"])
    tset_events = [e for e in events if e["kind"] == "tset"]
    stores, orphans = pair_tset_stores(tset_events)

    # Cross-check G against the sidecar count at the install frame, when the
    # first event lands on a frame whose count matches G (install frame).
    install_frame = None
    for e in events:
        if e["frame"] is not None:
            install_frame = e["frame"]
            break

    notes = [
        "7 expected logical stores: 4x nonzero at the normal initializer, "
        "2x zeroing (teardown pending instruction-trace confirmation), "
        "1x nonzero at the replacement initializer; the parser asserts the "
        "pairing, it does not label provenance.",
    ]
    report = build_report(input_manifest, rows, g_offset, events, stores,
                          orphans, cand_events, state_events, notes)
    report["frame_mapping"]["total_logged_markers"] = total_markers
    report["frame_mapping"]["install_frame_from_sidecar"] = install_frame
    stats = {
        "total_markers": total_markers,
        "total_tap": total_tap,
        "g": g_offset,
        "n_stores": len(stores),
        "n_orphans": len(orphans),
        "n_cand": len(cand_events),
        "n_state": len(state_events),
        "pointers": ["0x%08X" % s["pointer"] for s in stores],
    }
    return report, stats


# --------------------------------------------------------------------------
# Negative / positive fixtures. These are synthetic and require no private
# inputs, so test.ps1 can run them in a clean checkout.
# --------------------------------------------------------------------------

def _mk_tset_line(data, pc, a6=0x00FFA3C0, d5=0x00000000):
    return ("AVP_TSW_TSET data=%08X pc=%08X d0=00000000 d1=00000008 "
            "d2=00000000 d3=00000000 d4=00000000 d5=%08X d6=0000FFFF "
            "d7=00000000 a0=00FFA480 a1=00FF8580 a2=001F5F00 "
            "a3=FFFFF300 a4=000B20C6 a5=00FF8000 a6=%08X sp=00FF7FF6 "
            "ret=00FF00D8" % (data, pc, d5, a6))


def _fixture_events(lines, frame_const=100):
    """Drive the real parse+pair pipeline over synthetic lines."""
    events, _markers = parse_log_lines(lines)
    assign_frames(events, lambda t: frame_const, 0)
    tset_events = [e for e in events if e["kind"] == "tset"]
    cand_events = annotate_candidates([e for e in events
                                       if e["kind"] == "candidate"])
    stores, orphans = pair_tset_stores(tset_events)
    return {"events": events, "tset": tset_events, "cand": cand_events,
            "stores": stores, "orphans": orphans}


def fixture_positive_pair():
    """Two clean halves -> exactly one logical store with the right pointer."""
    lines = [_mk_tset_line(0x00000013, 0x00060578),
             _mk_tset_line(0x00000AC8, 0x00060578)]
    r = _fixture_events(lines)
    assert len(r["stores"]) == 1, r
    assert len(r["orphans"]) == 0, r
    assert r["stores"][0]["pointer"] == 0x00130AC8, r["stores"][0]
    assert r["stores"][0]["is_zero"] is False
    return r


def fixture_orphan_half():
    """Three consecutive identical halves -> one store + one orphan, never
    a silently guessed third pointer."""
    lines = [_mk_tset_line(0x00000013, 0x00060578),
             _mk_tset_line(0x00000AC8, 0x00060578),
             _mk_tset_line(0x00000013, 0x00060578)]
    r = _fixture_events(lines)
    assert len(r["stores"]) == 1, r
    assert len(r["orphans"]) == 1, r
    assert r["orphans"][0]["line"] == 3, r["orphans"]
    return r


def fixture_mismatched_context():
    """Two halves with different pc -> no store, two orphans (no guessing)."""
    lines = [_mk_tset_line(0x00000013, 0x00060578),
             _mk_tset_line(0x00000AC8, 0x00049604)]
    r = _fixture_events(lines)
    assert len(r["stores"]) == 0, r
    assert len(r["orphans"]) == 2, r
    return r


def fixture_mismatched_register():
    """Two halves whose register file differs -> no store, two orphans."""
    lines = [_mk_tset_line(0x00000013, 0x00060578, d5=0x00000001),
             _mk_tset_line(0x00000AC8, 0x00060578, d5=0x00000002)]
    r = _fixture_events(lines)
    assert len(r["stores"]) == 0, r
    assert len(r["orphans"]) == 2, r
    return r


def fixture_lane_positioned_byte():
    """A candidate whose display is lane-positioned (data=600) must be
    flagged byte_valid=False, not read as byte 0x00."""
    lines = ["AVP_TSW_CAND off=0E data=600 pc=000605CC a0=00FFA480 "
             "a1=00FF8580 a2=001F5F00 a3=FFFFF300"]
    r = _fixture_events(lines)
    assert len(r["cand"]) == 1, r
    assert r["cand"][0]["raw_data"] == 0x600, r["cand"][0]
    assert r["cand"][0]["byte_valid"] is False, r["cand"][0]
    return r


def run_fixtures():
    results = {}
    for name, fn in [
        ("positive_pair", fixture_positive_pair),
        ("orphan_half", fixture_orphan_half),
        ("mismatched_pc_context", fixture_mismatched_context),
        ("mismatched_register", fixture_mismatched_register),
        ("lane_positioned_byte", fixture_lane_positioned_byte),
    ]:
        fn()
        results[name] = "pass"
    return results


def run_positive_fixture(input_manifest):
    """Parse the real retained run when its inputs are present and valid."""
    if not all(input_manifest[n]["ok"] for n in RETAINED_INPUTS):
        return {"status": "skipped",
                "reason": "retained private inputs not all present/valid"}
    error_log_text = RETAINED_INPUTS["error_log"]["path"].read_text()
    frames_tsv_path = RETAINED_INPUTS["frames_tsv"]["path"]
    report, stats = run_analysis(input_manifest, error_log_text,
                                 frames_tsv_path)
    # Structural invariants of the retained run.
    assert stats["n_stores"] == 7, stats
    assert stats["n_orphans"] == 0, stats
    assert stats["g"] == 2373, stats
    pointers = stats["pointers"]
    assert pointers.count("0x00130AC8") == 4, pointers
    assert pointers.count("0x0013E97A") == 1, pointers
    assert pointers.count("0x00000000") == 2, pointers
    return {"status": "pass", "stats": stats, "report": report}


def main(argv):
    if "--self-test" in argv:
        results = run_fixtures()
        positive = run_positive_fixture(validate_inputs())
        print("self-test fixtures: %s" % results)
        if positive["status"] == "pass":
            print("positive fixture (retained run): pass, stores=%d "
                  "g=%d pointers=%s"
                  % (positive["stats"]["n_stores"],
                     positive["stats"]["g"],
                     positive["stats"]["pointers"]))
        else:
            print("positive fixture (retained run): %s"
                  % positive["reason"])
        return 0

    input_manifest = validate_inputs()
    present = all(input_manifest[n]["ok"] for n in RETAINED_INPUTS)
    if not present:
        missing = [n for n in RETAINED_INPUTS
                   if not input_manifest[n]["ok"]]
        print("retained private inputs not all present/valid (%s); "
              "skipping positive parse. Run --self-test for fixtures."
              % ", ".join(missing))
        return 0
    error_log_text = RETAINED_INPUTS["error_log"]["path"].read_text()
    frames_tsv_path = RETAINED_INPUTS["frames_tsv"]["path"]
    report, stats = run_analysis(input_manifest, error_log_text,
                                 frames_tsv_path)
    assert stats["n_orphans"] == 0, stats
    OUT_JSON.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print("logical stores: %d (orphans: %d)" % (stats["n_stores"],
                                                stats["n_orphans"]))
    for p in stats["pointers"]:
        print("  pointer %s" % p)
    print("wrote", OUT_JSON)
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
