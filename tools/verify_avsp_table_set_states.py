"""Step-2 check (semantic anchor + corpus falsification): per-state
street-alien table_set constancy.

Falsifies the semantic answer recorded in
data/avsp_table_set_states.json: each street-actor class (0x00
type_promotion, 0x06 replace, 0x1F normal - actors of type 0x0C in the
0xFF9580..0xFFA580 master-loop band) carries its table_set
(actor +0x50) at the per-class constant written by the state-0
(class-entry initializer) handler, and no observed sub-state ever changes it.

Checks:
  A: private offline instruction-form check - at each manifest store PC the
     opcode image holds 2D 7C <imm32 BE> 00 50 and the immediate equals the
     manifest value; the image sha256 matches the extractor manifest's
     program-image record.
  B: semantic anchor - the clip actor cited in
     data/enemy_action_capture.json (RAM 0xffa000, enemy_actions band
     slot 14) is validated frame by frame: every frame of its HIT clip and
     its KO clip shows the actor active, of one single street class, type
     0x0C, carrying that class's state-0 table_set constant. The observed
     animation-record pointers and full field histograms of the two clips
     are recorded. Broader corpus matches are labelled anchor-record
     signatures, never semantic HIT/KO populations.
  C: corpus invariance + lifecycle accounting - every active street actor frame in
     all four deterministic MAME routes (enemy_actions, stalker_actions,
     boss_actions, boss_ko; 32 KiB work RAM captures) has table_set ==
     expected[class]; zero mismatches, type 0x0C invariance, per-route
     street presence, four exclusive lifecycle categories (route-start
     adoption, inactive-to-active activation, active class transition,
     same-class continuation), field histograms, and exact-anchor record
     signature counts.
  D: negative controls - corrupt each populated class's expected value and
     require mismatches in its lifetime and every nonempty lifecycle or
     anchor-record-signature population.
  E: live cross-check - every manifest store (pc + value + family name)
     matches a live-trace family in data/avsp_table_set_source.json, and
     no family is left unmatched.
  F: extractor-manifest internal consistency (schema 3) - per class,
     states.class_entry.table_set == states.other_sub_states.table_set == the
     state-0 store value, the corpus-OBSERVED wording is present in
     other_sub_states.via, exactly one +0x50 writer is recorded in the
     clean code region, an undecoded tail (when the clean decode stopped
     before the span end) is recorded with a note, and the store PC sits
     inside the clean code region.

Inputs (any missing -> clean skip, exit 0):
  data/avsp_table_set_states.json
  data/avsp_table_set_source.json
  data/enemy_action_capture.json
  .deps/mame/actorprobe/decrypted_opcodes_2m.bin
  .deps/mame/{enemy_actions,stalker_actions,boss_actions,boss_ko}/workram_*.bin
Output (tracked):
  data/avsp_table_set_states_verification.json
Exit codes: 0 pass or skip, 1 fail.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACTOR_PATH = ROOT / "data" / "avsp_table_set_states.json"
SOURCE_PATH = ROOT / "data" / "avsp_table_set_source.json"
CAPTURE_PATH = ROOT / "data" / "enemy_action_capture.json"
IMAGE_PATH = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
ROUTEDIR = ROOT / ".deps" / "mame"
OUT_PATH = ROOT / "data" / "avsp_table_set_states_verification.json"

ROUTES = ("enemy_actions", "stalker_actions", "boss_actions", "boss_ko")
ANCHOR_ROUTE = "enemy_actions"
FRAME_SIZE = 0x8000
BAND_OFF = 0x1580
SLOTS = 20
STRIDE = 0xC0
BAND_RAM_BASE = 0xFF9580   # = 0xFF8000 + BAND_OFF (workram file base)
STREET_CLASSES = (0x00, 0x06, 0x1F)
EXPECTED_TYPE = 0x0C
STORE_PREFIX = (0x2D, 0x7C)
STORE_SUFFIX = (0x00, 0x50)
MISMATCH_CAP = 20


def skip(msg: str) -> None:
    print("verify: SKIPPED - %s; commit the extractor + this tool together so "
          "the check runs once inputs exist" % msg)
    raise SystemExit(0)


def fail(msg: str) -> None:
    print("verify: FAIL - %s" % msg)
    raise SystemExit(1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def u16(b: bytes, o: int) -> int:
    return (b[o] << 8) | b[o + 1]


def u32(b: bytes, o: int) -> int:
    return (u16(b, o) << 16) | u16(b, o + 2)


def slot_of_ram(ram: int):
    d = ram - BAND_RAM_BASE
    if d < 0 or d % STRIDE or (d // STRIDE) >= SLOTS:
        return None
    return d // STRIDE


def load_routes() -> dict:
    """route -> list of (frame_no, bytes); fail on malformed captures."""
    out = {}
    for route in ROUTES:
        files = sorted((ROUTEDIR / route).glob("workram_*.bin"))
        if not files:
            skip("route %s has no workram_*.bin captures" % route)
        frames = []
        for p in files:
            try:
                fn = int(p.stem.rsplit("_", 1)[1])
            except ValueError:
                fail("route %s: unparseable capture name %s" % (route, p.name))
            data = p.read_bytes()
            if len(data) != FRAME_SIZE:
                fail("route %s: %s is %d bytes, expected %d"
                     % (route, p.name, len(data), FRAME_SIZE))
            frames.append((fn, data))
        frames.sort()
        if len({fn for fn, _ in frames}) != len(frames):
            fail("route %s: duplicate frame numbers" % route)
        out[route] = frames
    return out


def slot_fields(w: bytes, slot: int) -> dict:
    o = BAND_OFF + slot * STRIDE
    return {
        "active": bool(w[o]),
        "state": w[o],
        "class": w[o + 2],
        "sub_state": w[o + 4],
        "action": u16(w, o + 6),
        "type": w[o + 8],
        "anim_record": u32(w, o + 0x1C),
        "table_set": u32(w, o + 0x50),
    }


def hex_hist(counter: dict, width: int) -> dict:
    return {("0x%%0%dX" % width) % k: v for k, v in sorted(counter.items())}


def new_field_histograms() -> dict:
    return {k: {} for k in ("route", "class", "state", "sub_state",
                             "action", "anim_record", "table_set")}


def add_histogram(hist: dict, route: str, f: dict) -> None:
    values = {
        "route": route,
        "class": "0x%02X" % f["class"],
        "state": "0x%02X" % f["state"],
        "sub_state": "0x%02X" % f["sub_state"],
        "action": "0x%04X" % f["action"],
        "anim_record": "0x%08X" % f["anim_record"],
        "table_set": "0x%08X" % f["table_set"],
    }
    for key, value in values.items():
        hist[key][value] = hist[key].get(value, 0) + 1


def clip_signature(frames, route, slot, lo, hi, problems, clip_name):
    """Validate every frame of a cited clip; return the observed
    signature (class/type/sub-states/action words/state bytes) or None
    when the clip cannot support a population definition."""
    by = {fn: w for fn, w in frames}
    cls = None
    sses = set()
    actions = set()
    states = set()
    records = set()
    hist = new_field_histograms()
    verified = 0
    mismatch = 0
    for fn in range(lo, hi + 1):
        w = by.get(fn)
        if w is None:
            problems.append("B: %s clip: frame %d missing from route %s"
                            % (clip_name, fn, route))
            return None
        f = slot_fields(w, slot)
        if not f["active"]:
            problems.append("B: %s clip: actor inactive at frame %d"
                            % (clip_name, fn))
            return None
        if cls is None:
            cls = f["class"]
        elif f["class"] != cls:
            problems.append("B: %s clip: class changes mid-clip at frame %d"
                            % (clip_name, fn))
            return None
        if cls not in STREET_CLASSES:
            problems.append("B: %s clip: actor class 0x%02X is not a street "
                            "class" % (clip_name, cls))
            return None
        if f["type"] != EXPECTED_TYPE:
            problems.append("B: %s clip: actor type 0x%02X != 0x%02X at "
                            "frame %d" % (clip_name, f["type"], EXPECTED_TYPE,
                                          fn))
            return None
        if f["table_set"] != expected_value[cls]:
            mismatch += 1
        sses.add(f["sub_state"])
        actions.add(f["action"])
        states.add(f["state"])
        records.add(f["anim_record"])
        add_histogram(hist, route, f)
        verified += 1
    if mismatch:
        problems.append("B: %s clip: %d frame(s) carry a table_set that is "
                        "not the class 0x%02X constant"
                        % (clip_name, mismatch, cls))
    return {
        "clip": clip_name,
        "frame": {"start": lo, "end": hi, "count": hi - lo + 1},
        "class": "0x%02X" % cls,
        "type": "0x%02X" % EXPECTED_TYPE,
        "sub_states": ["0x%02X" % s for s in sorted(sses)],
        "action_words": ["0x%04X" % a for a in sorted(actions)],
        "animation_records": ["0x%08X" % a for a in sorted(records)],
        "state_bytes": ["0x%02X" % s for s in sorted(states)],
        "field_histograms": hist,
        "frames_verified": verified,
        "table_set_mismatches": mismatch,
    }


expected_value = {}   # class int -> table_set int (filled in main)


def make_popdef(anchor_class: int, hit_sig: dict, ko_sig: dict):
    hit_records = {int(s, 16) for s in hit_sig["animation_records"]}
    ko_records = {int(s, 16) for s in ko_sig["animation_records"]}
    return {
        "class": anchor_class,
        "hit_records": sorted(hit_records),
        "ko_records": sorted(ko_records),
    }


def signature_population_of(popdef, f: dict) -> str:
    """Return a conservative record-signature population label.

    A record observed during an exact HIT/KO clip is not thereby proven to
    mean HIT/KO everywhere else. The broad corpus labels deliberately retain
    the anchor provenance instead of promoting correlation to semantics.
    """
    if f["class"] != popdef["class"]:
        return ""
    if f["anim_record"] in popdef["hit_records"]:
        return "hit_anchor_record_signature"
    if f["anim_record"] in popdef["ko_records"]:
        return "ko_anchor_record_signature"
    return ""


def scan_corpus(routes: dict, expected: dict, popdef) -> dict:
    """Per-slot scan with exclusive lifecycle accounting."""
    stats = {r: {"frames": 0, "street_frames": 0,
                 "mismatch_count": 0, "mismatches": []}
             for r in ROUTES}
    per_class = {
        cl: {
            "lifetime": 0,
            "mismatches": 0,
            "lifecycle": {k: 0 for k in
                          ("route_start_adoption", "activation",
                           "class_transition", "continuation")},
            "lifecycle_mismatches": {k: 0 for k in
                                     ("route_start_adoption", "activation",
                                      "class_transition", "continuation")},
            "field_histograms": new_field_histograms(),
            "sub_state_action_histogram": {},
        }
        for cl in STREET_CLASSES
    }
    signature_pops = {
        p: {"frames": 0, "mismatches": 0,
            "field_histograms": new_field_histograms()}
        for p in ("hit_anchor_record_signature",
                  "ko_anchor_record_signature")
    }
    type_violations = []
    for route in ROUTES:
        frames = routes[route]
        prev = [{"active": False, "class": None} for _ in range(SLOTS)]
        for idx, (fn, w) in enumerate(frames):
            stats[route]["frames"] += 1
            first = (idx == 0)
            for s in range(SLOTS):
                f = slot_fields(w, s)
                if not f["active"]:
                    prev[s] = {"active": False, "class": None}
                    continue
                cl = f["class"]
                if cl not in STREET_CLASSES:
                    prev[s] = {"active": True, "class": cl}
                    continue
                if f["type"] != EXPECTED_TYPE:
                    type_violations.append(
                        {"route": route, "frame": fn, "slot": s,
                         "class": "0x%02X" % cl,
                         "type": "0x%02X" % f["type"]})
                c = per_class[cl]
                c["lifetime"] += 1
                add_histogram(c["field_histograms"], route, f)
                ss_key = "0x%02X" % f["sub_state"]
                ak = "0x%04X" % f["action"]
                awk = c["sub_state_action_histogram"].setdefault(ss_key, {})
                awk[ak] = awk.get(ak, 0) + 1

                if first:
                    lifecycle = "route_start_adoption"
                elif not prev[s]["active"]:
                    lifecycle = "activation"
                elif prev[s]["class"] != cl:
                    lifecycle = "class_transition"
                else:
                    lifecycle = "continuation"
                c["lifecycle"][lifecycle] += 1
                stats[route]["street_frames"] += 1
                want = expected[cl]
                mm = f["table_set"] != want
                if mm:
                    c["mismatches"] += 1
                    c["lifecycle_mismatches"][lifecycle] += 1
                    r = stats[route]
                    r["mismatch_count"] += 1
                    if len(r["mismatches"]) < MISMATCH_CAP:
                        r["mismatches"].append(
                            {"frame": fn, "slot": s,
                             "class": "0x%02X" % cl,
                             "table_set": "0x%08X" % f["table_set"],
                             "expected": "0x%08X" % want})
                if popdef is not None:
                    pop = signature_population_of(popdef, f)
                    if pop:
                        signature_pops[pop]["frames"] += 1
                        add_histogram(signature_pops[pop]["field_histograms"],
                                      route, f)
                        if mm:
                            signature_pops[pop]["mismatches"] += 1
                prev[s] = {"active": True, "class": cl}
    return {
        "stats": stats,
        "per_class": per_class,
        "signature_populations": signature_pops,
        "type_violations": type_violations,
    }


def lifecycle_total(c: dict) -> int:
    return sum(c["lifecycle"].values())


def main() -> int:
    global expected_value
    for p, what in ((EXTRACTOR_PATH, "extractor manifest "
                      "(run tools/extract_avsp_table_set_states.py first)"),
                    (SOURCE_PATH, "live table_set source manifest"),
                    (CAPTURE_PATH, "semantic anchor capture manifest"),
                    (IMAGE_PATH, "opcode image")):
        if not p.is_file():
            skip("%s absent (%s)" % (what, p.as_posix()))

    extractor = json.loads(EXTRACTOR_PATH.read_text())
    source = json.loads(SOURCE_PATH.read_text())
    capture = json.loads(CAPTURE_PATH.read_text())
    img = IMAGE_PATH.read_bytes()
    if len(img) != 0x200000:
        fail("opcode image is %d bytes, expected 0x200000" % len(img))
    image_sha = hashlib.sha256(img).hexdigest()

    classes = extractor.get("street_classes", {})
    if sorted(classes) != ["0x00", "0x06", "0x1F"]:
        fail("extractor manifest lists classes %s" % sorted(classes))
    for cl_key, c in classes.items():
        expected_value[int(cl_key, 16)] = int(c["state0_store"]["value"], 16)
    expected = dict(expected_value)

    problems = []

    # --- check A: offline byte pattern + image anchor ---
    rec_sha = (extractor.get("program_image") or {}).get("sha256")
    if rec_sha and rec_sha != image_sha:
        problems.append("A: image sha256 %s != extractor manifest program-"
                        "image sha256 %s" % (image_sha, rec_sha))
    for cl_key, c in classes.items():
        st = c["state0_store"]
        pc = int(st["pc"], 16)
        want = int(st["value"], 16)
        if pc + 8 > len(img):
            problems.append("A: class %s store %s outside image"
                            % (cl_key, st["pc"]))
            continue
        raw = img[pc:pc + 8]
        if (raw[0], raw[1]) != STORE_PREFIX or \
                (raw[6], raw[7]) != STORE_SUFFIX:
            problems.append("A: class %s store %s bytes are not the "
                            "2D 7C imm32 00 50 form" % (cl_key, st["pc"]))
        elif int.from_bytes(raw[2:6], "big") != want:
            problems.append("A: class %s store %s immediate does not match "
                            "manifest value %s" % (cl_key, st["pc"],
                                                   st["value"]))

    # --- check B: semantic anchor (enemy_action_capture.json clip actor) ---
    actor = capture.get("actor", {})
    actor_ram = int(actor.get("actor_address", "0x0") or 0, 16)
    anchor_slot = slot_of_ram(actor_ram)
    if anchor_slot is None:
        problems.append("B: actor address %s is not inside the "
                        "0xFF9580 band (stride 0x%02X, %d slots)"
                        % (actor.get("actor_address"), STRIDE, SLOTS))
        anchor_slot = None
    clips = {c.get("name"): c for c in capture.get("clips", [])}
    hit_clip = clips.get("hit")
    ko_clip = clips.get("ko")
    anchor = {
        "route": ANCHOR_ROUTE,
        "actor_address": actor.get("actor_address"),
        "slot": anchor_slot,
        "actor_id": actor.get("actor_id"),
    }
    hit_sig = ko_sig = None
    popdef = None
    routes = load_routes()
    if anchor_slot is not None and hit_clip and ko_clip:
        frames = routes[ANCHOR_ROUTE]
        hit_sig = clip_signature(frames, ANCHOR_ROUTE, anchor_slot,
                                 hit_clip["start_frame"],
                                 hit_clip["end_frame"], problems, "hit")
        ko_sig = clip_signature(frames, ANCHOR_ROUTE, anchor_slot,
                                ko_clip["start_frame"],
                                ko_clip["end_frame"], problems, "ko")
        # disappears_at_frame: the KO sequence must end with the actor
        # leaving the slot (captured ground truth).
        gone = actor.get("disappears_at_frame")
        if gone is not None:
            by = {fn: w for fn, w in frames}
            w = by.get(gone)
            if w is None or (BAND_OFF + anchor_slot * STRIDE) < len(w) \
                    and w[BAND_OFF + anchor_slot * STRIDE] != 0:
                problems.append("B: actor not inactive at the captured "
                                "disappears_at_frame %s" % gone)
        if hit_sig and ko_sig:
            if hit_sig["class"] != ko_sig["class"]:
                problems.append("B: hit and ko clips show different classes "
                                "(%s vs %s)"
                                % (hit_sig["class"], ko_sig["class"]))
            elif {int(s, 16) for s in hit_sig["animation_records"]} & \
                    {int(s, 16) for s in ko_sig["animation_records"]}:
                problems.append("B: hit and ko clip animation-record sets "
                                "overlap; record signatures are not separable")
            else:
                popdef = make_popdef(int(hit_sig["class"], 16), hit_sig,
                                     ko_sig)
        anchor["hit_clip"] = hit_sig
        anchor["ko_clip"] = ko_sig
    else:
        problems.append("B: anchor inputs incomplete (actor address / hit "
                        "clip / ko clip missing from the capture manifest)")

    # --- check C: corpus invariance + lifecycle/signature populations ---
    res = scan_corpus(routes, expected, popdef)
    total_mismatches = sum(r["mismatch_count"] for r in res["stats"].values())
    if total_mismatches:
        first = next((m for r in ROUTES
                      for m in res["stats"][r]["mismatches"]), None)
        problems.append("C: %d active street frame(s) carry a table_set that "
                        "is not the per-class state-0 constant (first: %s)"
                        % (total_mismatches, json.dumps(first)))
    if res["type_violations"]:
        problems.append("C: street-class actor frame(s) with type != 0x0C: "
                        "%s" % res["type_violations"][:5])
    for route in ROUTES:
        if res["stats"][route]["street_frames"] == 0:
            problems.append("C: route %s has no active street frames" % route)
    if popdef is not None:
        ac = "0x%02X" % popdef["class"]
        c = res["per_class"][popdef["class"]]
        if c["lifetime"] < 1:
            problems.append("C: anchor class %s lifetime 0 < 1" % ac)
        for pop in ("hit_anchor_record_signature",
                    "ko_anchor_record_signature"):
            if res["signature_populations"][pop]["frames"] < 1:
                problems.append("C: anchor class %s %s has 0 frames"
                                % (ac, pop))
        if hit_sig and hit_sig["table_set_mismatches"]:
            problems.append("C: hit clip table_set mismatches: %d"
                            % hit_sig["table_set_mismatches"])
        if ko_sig and ko_sig["table_set_mismatches"]:
            problems.append("C: ko clip table_set mismatches: %d"
                            % ko_sig["table_set_mismatches"])
    if res["per_class"][0x06]["field_histograms"]["sub_state"].get(
            "0x04", 0) < 1:
        problems.append("C: class 0x06 lifecycle-signature sub-state 0x04 "
                        "frames 0 < 1")
    if res["per_class"][0x00]["lifetime"] < 1:
        problems.append("C: class 0x00 lifetime 0 < 1")
    if popdef is None:
        problems.append("C: anchor record populations unavailable (check B "
                        "failed); population coverage skipped")
    coverage = {
        "0x00": "lifetime >= 1; exclusive lifecycle sum == lifetime",
        "0x06": ("lifetime >= 1; exclusive lifecycle sum == lifetime; "
                 "sub-state 0x04 lifecycle-signature >= 1"),
        "0x1F": ("lifetime >= 1; exclusive lifecycle sum == lifetime; "
                 "exact HIT/KO anchors fully validated; both anchor-record "
                 "signature populations nonempty"),
    }
    for cl, c in res["per_class"].items():
        if lifecycle_total(c) != c["lifetime"]:
            problems.append("C: class 0x%02X lifecycle total %d != lifetime %d"
                            % (cl, lifecycle_total(c), c["lifetime"]))

    # --- check D: one negative control for every populated class ---
    controls = {}
    for idx, cl in enumerate(STREET_CLASSES):
        corrupt = dict(expected)
        corrupt_value = expected[STREET_CLASSES[(idx + 1) % len(STREET_CLASSES)]]
        corrupt[cl] = corrupt_value
        res_c = scan_corpus(routes, corrupt, popdef)
        base_c = res["per_class"][cl]
        test_c = res_c["per_class"][cl]
        lifecycle_failures = [
            name for name, frames in base_c["lifecycle"].items()
            if frames > 0 and test_c["lifecycle_mismatches"].get(name, 0) < 1
        ]
        signature_mismatches = {}
        if popdef is not None and popdef["class"] == cl:
            for name, base_pop in res["signature_populations"].items():
                if base_pop["frames"] > 0:
                    signature_mismatches[name] = \
                        res_c["signature_populations"][name]["mismatches"]
                    if signature_mismatches[name] < 1:
                        lifecycle_failures.append(name)
        if test_c["mismatches"] != base_c["lifetime"]:
            problems.append("D: class 0x%02X control mismatches %d != "
                            "lifetime %d" % (cl, test_c["mismatches"],
                                             base_c["lifetime"]))
        if lifecycle_failures:
            problems.append("D: class 0x%02X control missed populated "
                            "population(s) %s" % (cl, lifecycle_failures))
        controls["0x%02X" % cl] = {
            "corrupted_value": "0x%08X" % corrupt_value,
            "lifetime_frames": base_c["lifetime"],
            "mismatches": test_c["mismatches"],
            "lifecycle_mismatches": test_c["lifecycle_mismatches"],
            "anchor_record_signature_mismatches": signature_mismatches,
        }

    # --- check E: live-trace family cross-check ---
    fams = {int(f["store_pc"], 16): f
            for f in source.get("families", {}).values()}
    matched = set()
    for cl_key, c in classes.items():
        st = c["state0_store"]
        pc = int(st["pc"], 16)
        fam = fams.get(pc)
        if fam is None:
            problems.append("E: class %s store %s has no live-trace family"
                            % (cl_key, st["pc"]))
            continue
        matched.add(pc)
        if int(fam["value"], 16) != int(st["value"], 16):
            problems.append("E: class %s store %s value %s != live-trace "
                            "family value %s"
                            % (cl_key, st["pc"], st["value"], fam["value"]))
        if fam.get("name") != c.get("family"):
            problems.append("E: class %s family %s != live-trace family name "
                            "%s" % (cl_key, c.get("family"), fam.get("name")))
    orphaned = sorted(set(fams) - matched)
    if orphaned:
        problems.append("E: live-trace families with no street-class store: "
                        "%s" % ["0x%06X" % p for p in orphaned])

    # --- check F: extractor-manifest internal consistency (schema 3) ---
    for cl_key, c in classes.items():
        class_entry = int(c["states"]["class_entry"]["table_set"], 16)
        other = c["states"]["other_sub_states"]
        store_v = int(c["state0_store"]["value"], 16)
        if not (class_entry == int(other["table_set"], 16) == store_v):
            problems.append("F: class %s class-entry/other/store values differ: "
                            "%s/%s/%s" % (cl_key,
                                         c["states"]["class_entry"]["table_set"],
                                         other["table_set"],
                                         c["state0_store"]["value"]))
        if "corpus-observed" not in other.get("via", "").lower():
            problems.append("F: class %s other_sub_states.via lacks the "
                            "corpus-OBSERVED wording" % cl_key)
        span = c.get("state0_span", {})
        if span.get("writers_found_in_clean_region") != 1:
            problems.append("F: class %s clean-region +0x50 writer count %s "
                            "!= 1" % (cl_key,
                                      span.get("writers_found_in_clean_region")))
        tail = c.get("undecoded_tail")
        if not span.get("decode_reached_span_end", True):
            if not tail or not tail.get("note"):
                problems.append("F: class %s clean decode stopped early but "
                                "the undecoded tail is not recorded with a "
                                "note" % cl_key)
        if tail and (tail.get("start") != span.get("clean_code_end")
                     or tail.get("end") != span.get("end")):
            problems.append("F: class %s undecoded tail bounds disagree with "
                            "the span record" % cl_key)
        pc = int(c["state0_store"]["pc"], 16)
        t0 = int(span.get("start", "0x0"), 16)
        ce = int(span.get("clean_code_end", "0x0"), 16)
        if not (t0 <= pc < ce):
            problems.append("F: class %s store %s outside the clean code "
                            "region [%s, %s)"
                            % (cl_key, c["state0_store"]["pc"],
                               span.get("start"), span.get("clean_code_end")))

    result = "PASS" if not problems else "FAIL"
    signature_out = None
    if popdef is not None:
        signature_out = {
            "definition": {
                "class": "0x%02X" % popdef["class"],
                "hit_anchor_record_signature": (
                    "animation record in the exact HIT clip set %s; this is "
                    "a record-signature population, not a semantic HIT claim"
                    % ["0x%08X" % s for s in popdef["hit_records"]]),
                "ko_anchor_record_signature": (
                    "animation record in the exact KO clip set %s; this is "
                    "a record-signature population, not a semantic KO claim"
                    % ["0x%08X" % s for s in popdef["ko_records"]]),
            },
            **res["signature_populations"],
        }
    out = {
        "schema": 3,
        "classification": ("semantic anchor + corpus falsification of "
                           "per-state table_set constancy - counts, addresses, "
                           "decoded instruction forms and field histograms "
                           "only; no ROM bytes"),
        "result": result,
        "problems": problems,
        "image_sha256": image_sha,
        "extractor_manifest_sha256": sha256(EXTRACTOR_PATH),
        "anchor_capture_manifest_sha256": sha256(CAPTURE_PATH),
        "expected_table_set": {"0x%02X" % k: "0x%08X" % v
                               for k, v in sorted(expected.items())},
        "anchor": anchor,
        "anchor_record_signature_populations": signature_out,
        "corpus": {r: {"frames": s["frames"],
                       "street_frames": s["street_frames"],
                       "mismatches": s["mismatch_count"],
                       "mismatch_samples": s["mismatches"]}
                   for r, s in res["stats"].items()},
        "per_class": res["per_class"],
        "negative_controls": controls,
        "check_A": ("private opcode-image instruction-form and immediate "
                    "validation; no opcode bytes serialized"),
        "check_B": "semantic anchor: cited clip actor (RAM 0xffa000, slot %s) "
                   "valid per-frame on the HIT and KO clips; animation-record "
                   "sets separable" % (anchor_slot,),
        "check_C": ("per-slot constancy, exclusive lifecycle accounting and "
                    "anchor-record-signature populations over %s"
                    % ", ".join(ROUTES)),
        "check_D": ("one corrupted-constant control per populated class; "
                    "each must fail its lifetime and every nonempty claimed "
                    "population"),
        "check_E": "manifest stores cross-match live-trace families",
        "check_F": ("manifest internal consistency (schema 3: class-entry == "
                    "other == store value, corpus-observed wording, one "
                    "clean-region writer, recorded undecoded tail, store "
                    "inside the clean region)"),
        "coverage_requirements": coverage,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")

    print("verify: %s" % result)
    tot_frames = sum(s["frames"] for s in res["stats"].values())
    tot_street = sum(s["street_frames"] for s in res["stats"].values())
    print("  corpus: %d frames / %d active street frames over %s"
          % (tot_frames, tot_street, ", ".join(ROUTES)))
    if popdef is not None:
        print("  anchor: %s slot %d (actor %s)"
              % (anchor["route"], anchor_slot, anchor["actor_address"]))
        if hit_sig:
            print("    HIT clip %d-%d: class %s ss=%s actions=%s"
                  % (hit_clip["start_frame"], hit_clip["end_frame"],
                     hit_sig["class"],
                     ",".join(hit_sig["sub_states"]),
                     ",".join(hit_sig["action_words"])))
        if ko_sig:
            print("    KO  clip %d-%d: class %s ss=%s"
                  % (ko_clip["start_frame"], ko_clip["end_frame"],
                     ko_sig["class"], ",".join(ko_sig["sub_states"])))
        print("    record signatures: " + ", ".join(
            "%s=%d/%d" % (p, rec["frames"], rec["mismatches"])
            for p, rec in sorted(res["signature_populations"].items())))
    for cl_key in ("0x00", "0x06", "0x1F"):
        c = res["per_class"][int(cl_key, 16)]
        print("  class %s: lifetime=%d lifecycle=%s control=%d"
              % (cl_key, c["lifetime"],
                 ", ".join("%s=%d" % kv for kv in
                           sorted(c["lifecycle"].items())),
                 controls[cl_key]["mismatches"]))
    print("  corpus mismatches: %d" % total_mismatches)
    if problems:
        for p in problems:
            print("  problem: %s" % p)
    print("wrote", OUT_PATH.relative_to(ROOT).as_posix())
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
