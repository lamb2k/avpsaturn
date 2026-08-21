"""Derive the bounded AVSP class-1F HIT/KO writer closure from private evidence.

Only typed values, PCs, addresses, counts, and hashes are committed.  The
trace, opcode image, samples, and watchpoint log remain private under .deps.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps/mame/vertical_slice/cold_run_1"
CTX = ROOT / ".deps/mame/vertical_slice/hit_ko_writer_context_watchpoint_5"
TRACE, LEDGER = RAW / "maincpu.trace", RAW / "semantic_ledger.jsonl"
LOG, SAMPLES = CTX / "error.log", CTX / "target_actor_samples.tsv"
OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps/mame/actorprobe/decrypted_program_2m.bin"
BOUNDARY = ROOT / "data/avsp_translation_boundary.json"
CONTRACT = ROOT / "data/avsp_vertical_slice_contract.json"
ORACLE = ROOT / "data/avsp_vertical_slice_oracle_manifest.json"
OUT = ROOT / "data/avsp_hit_ko_writer_set.json"
FIRST, LAST, HIT, KO, ACTOR = 4080, 5469, 5191, 5330, 0xFFA000
FIELDS = ("state", "sub_state", "action", "anim_record", "anim_timer", "health", "hit_value")
EXPECTED_COUNTS = {"state": 7, "sub_state": 16, "action": 57, "anim_record": 274, "anim_timer": 704, "health": 4, "hit_value": 42}
EXPECTED = {
    "contract": "74016fb2e73c2ae00144fa062662b37e0f575a3ee3ff3b7a420b1ed0f55a4638",
    "oracle": "106fffb92cc5a14acf5fdae7eb14d33b7d9206b9f9ecffcbac67a6fc326696d2",
    "ledger": "f6e813169a05388ce265d6406382efaa1801fe8c838beb0fdab03bda7725d1a1",
    "boundary": "95e002b7f6d48e8aafbe5e201a370b6dc7c3c5559e7d2253901d0473c0c7b0f4",
    "trace": "9bbbc28715668348aeb4d206b7381073123c5b22ec9e2f2557bda1622e142f5f",
    "opcodes": "e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501",
    "program": "0c14f4094d25787401aa949657620ff495ae8606c1cfd8ae2d059b94c3d478e9",
}
# Filled after one successful private-evidence generation, then frozen.
IMMUTABLE_BINDING = {
    "accepted_boundary_pc_count": 7314,
    "field_transition_sha256": "415ef74b56a7e2e0324ca3ad06e5796c7f3b0bde192249dcfba79765e0f80e36",
    "selected_edge_sha256": "14727b9d183fef87b2eeb6916f192c421d3cc57d06583ae875e82c50d98ce822",
    "selected_pc_sha256": "c3ce5b93a2f0b2fb0aab096c1800a185051977911e198b11f0a4e9a8bc400da9",
    "selected_routine_sha256": "63c35753fabd8d833c469b8737cace5df06a42668babe8e2d2382924491e25cf",
    "writer_observation_sha256": "5568b8b83c8281dad5dd791f535367c190e4eed88984ef42d54199a6de035895",
}
LINE = re.compile(r"^([0-9a-fA-F]{6,8}):")
IRQ = re.compile(r"^\(interrupted at [0-9a-fA-F]{4,8}, IRQ \d+\)$")
MARK = re.compile(r"AVP_HIT_KO_INTERVAL_START (\d+)")
WP = re.compile(r"AVP_HIT_KO_WP .* field=(\w+) addr=([0-9A-F]+) data=([0-9A-F]+) pc=([0-9A-F]+) d0=([0-9A-F]+) d1=([0-9A-F]+) a0=([0-9A-F]+) a1=([0-9A-F]+) a2=([0-9A-F]+) a3=([0-9A-F]+) a4=([0-9A-F]+) a5=([0-9A-F]+) a6=([0-9A-F]+) a7=([0-9A-F]+)")
FORBIDDEN = {"raw", "bytes", "opcode_words", "disassembly", "disassembly_text", "trace_text", "trace_lines", "state_dump", "screenshot"}


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def tsha(path): return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
def h(value): return f"0x{value:06x}"
def jhash(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def phash(pcs): return hashlib.sha256("\n".join(sorted(set(pcs))).encode()).hexdigest()
def word(image, pc): return int.from_bytes(image[pc:pc + 2], "big")
def s16(value): return value - 0x10000 if value & 0x8000 else value


def rows():
    out = {}
    for line in SAMPLES.read_text(encoding="utf-8").splitlines()[1:]:
        p = line.split("\t")
        if len(p) != 10: raise ValueError("private target sample lacks seven-field layout")
        out[int(p[0])] = {"state": int(p[1]), "class": int(p[2]), "sub_state": int(p[3]), "action": int(p[4]), "type": int(p[5]), "anim_record": int(p[6]), "anim_timer": int(p[7]), "health": int(p[8]), "hit_value": int(p[9])}
    if sorted(out) != list(range(FIRST, LAST + 1)): raise ValueError("private samples are not 1,390 frames")
    return out


def trace():
    out, frame = {}, FIRST - 1
    for line in TRACE.open(encoding="utf-8", errors="replace"):
        line = line.strip()
        if IRQ.match(line): frame += 1; out.setdefault(frame, []); continue
        match = LINE.match(line)
        if match and FIRST <= frame < LAST: out.setdefault(frame, []).append(int(match.group(1), 16))
    if sorted(out) != list(range(FIRST, LAST)): raise ValueError("trace is not 1,389 intervals")
    return out


def watchpoints():
    out, frame = {}, None
    for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        marker = MARK.search(line)
        if marker: frame = int(marker.group(1)); out.setdefault(frame, []); continue
        match = WP.search(line)
        if not match: continue
        if frame is None: raise ValueError("watchpoint event before marker")
        values = [int(value, 16) for value in match.groups()[1:]]
        registers = {"d0": values[3], "d1": values[4], **{f"a{i}": values[5 + i] for i in range(8)}}
        out[frame].append({"field": match.group(1), "destination": values[0], "data": values[1], "reported_pc": values[2], "registers": registers})
    if sorted(out) != list(range(FIRST, LAST)): raise ValueError("watchpoint markers are incomplete")
    return out


def source_extensions(mode, register, size):
    if mode in (0, 1, 2, 3, 4): return 0
    if mode in (5, 6): return 1
    if mode != 7: raise ValueError("invalid source EA")
    if register in (0, 2, 3): return 1
    if register == 1: return 2
    if register == 4: return 2 if size == 4 else 1
    raise ValueError("invalid source EA register")


def memory_ea(image, mode, register, extension_pc):
    if mode == 2: return f"a{register}", 0
    if mode == 5: return f"a{register}", s16(word(image, extension_pc))
    return None


def store(image, pc):
    """Decode only exercised 68000 stores from destination EA plus live state."""
    opcode, top = word(image, pc), word(image, pc) >> 12
    if top in (1, 2, 3):
        size = {1: 1, 2: 4, 3: 2}[top]
        sm, sr, dm, dr = (opcode >> 3) & 7, opcode & 7, (opcode >> 6) & 7, (opcode >> 9) & 7
        ea = memory_ea(image, dm, dr, pc + 2 + 2 * source_extensions(sm, sr, size))
        if ea: return {"width": size, "ea": ea, "source": f"d{sr}" if sm == 0 else (f"a{sr}" if sm == 1 else None)}
    if (opcode & 0xF000) in (0x9000, 0xD000) and opcode & 0x0100:
        size = {0: 1, 1: 2, 2: 4}.get((opcode >> 6) & 3)
        ea = memory_ea(image, (opcode >> 3) & 7, opcode & 7, pc + 2) if size else None
        if ea: return {"width": size, "ea": ea, "source": f"d{(opcode >> 9) & 7}"}
    if opcode & 0xF000 == 0x5000 and (opcode >> 6) & 3 != 3:
        size = {0: 1, 1: 2, 2: 4}[(opcode >> 6) & 3]
        ea = memory_ea(image, (opcode >> 3) & 7, opcode & 7, pc + 2)
        if ea: return {"width": size, "ea": ea, "source": None}
    if opcode & 0xFFC0 == 0x4200:
        size = {0: 1, 1: 2, 2: 4}.get((opcode >> 6) & 3)
        ea = memory_ea(image, (opcode >> 3) & 7, opcode & 7, pc + 2) if size else None
        if ea: return {"width": size, "ea": ea, "source": None}
    return None


def decode_event(image, event, pcs):
    candidates = []
    for pc in sorted(set(pcs)):
        if not event["reported_pc"] - 16 <= pc < event["reported_pc"]: continue
        decoded = store(image, pc)
        if not decoded: continue
        register, displacement = decoded["ea"]
        address = (event["registers"][register] + displacement) & 0xFFFFFFFF
        if (address & 0xFFFFFF) == (event["destination"] & 0xFFFFFF): candidates.append((pc, decoded))
    if not candidates: raise ValueError(f"missing effective address for {event['field']} at {h(event['reported_pc'])}")
    # MAME reports the successor PC.  A same-interval earlier store can address
    # the same actor field (the KO health clamp does), so select the nearest
    # preceding decoded instruction and reject a tie rather than guessing.
    nearest = min(event["reported_pc"] - pc for pc, _ in candidates)
    candidates = [item for item in candidates if event["reported_pc"] - item[0] == nearest]
    if len(candidates) != 1: raise ValueError(f"ambiguous effective address for {event['field']} at {h(event['reported_pc'])}")
    return candidates[0]


def instance(field, event, decoded):
    pc, operation = decoded
    register, displacement = operation["ea"]
    binding = {register: h(event["registers"][register])}
    if operation["source"] in ("d0", "d1"): binding[operation["source"]] = h(event["registers"][operation["source"]])
    width, value = operation["width"], event["data"] & ((1 << (operation["width"] * 8)) - 1)
    if field == "health" and width == 2: value = s16(value)
    return {"instruction_pc": h(pc), "watchpoint_reported_pc": h(event["reported_pc"]), "destination": h(event["destination"]), "field": field, "write_width_bytes": width, "write_value": value, "effective_address_register": register, "effective_address_displacement": displacement, "dynamic_register_binding": binding}


def deltas(sample_rows, field): return [(frame, sample_rows[frame][field], sample_rows[frame + 1][field]) for frame in range(FIRST, LAST) if sample_rows[frame][field] != sample_rows[frame + 1][field]]
def edge_kind(image, pc):
    opcode = word(image, pc)
    if opcode == 0x4E75: return "return"
    if (opcode & 0xFF00) == 0x6100 or (opcode & 0xFFC0) == 0x4E80: return "call"
    if (opcode & 0xFFC0) == 0x4EC0: return "computed_jump"
    if (opcode & 0xF000) == 0x6000: return "conditional_branch"
    return "fallthrough"


def path(sequence, anchors):
    cursor = 0
    for anchor in anchors: cursor = sequence.index(anchor, cursor) + 1
    pointer = [0x16518, 0x1651C, 0x1651E, 0x16522, 0x16526, 0x1652A, 0x1652E, 0x16534]
    start = sequence.index(anchors[0])
    for index in range(cursor, len(sequence) - len(pointer) + 1):
        if sequence[index:index + len(pointer)] == pointer: return sequence[start:index + len(pointer)]
    raise ValueError("pointer-selection routine is absent from selected path")


def context(epochs, observations, pc):
    pcs, pairs = set(), set()
    intervals = {item["interval_start_frame"] for item in observations if item["instruction_pc"] == h(pc)}
    for interval in sorted(intervals):
        sequence = epochs[interval]
        for index, candidate in enumerate(sequence):
            if candidate != pc: continue
            window = sequence[max(0, index - 5):index + 8]
            pcs.update(window); pairs.update(zip(window, window[1:]))
    if pc not in pcs: raise ValueError("writer site missing from dynamic context")
    return sorted(pcs), pairs


def routine(entry, pcs, callers=(), callees=(), writes=(), exits=(), role=None):
    out = {"entry_pc": h(entry), "member_pc_count": len(set(pcs)), "member_pc_sha256": phash(h(pc) for pc in pcs), "member_pcs": sorted({h(pc) for pc in pcs}), "observed_callers": sorted({h(pc) for pc in callers}), "observed_callees": sorted({h(pc) for pc in callees}), "actor_field_reads": [], "actor_field_writes": sorted(set(writes)), "rom_data_reads": [], "work_ram_references": [h(ACTOR)], "event_exits": list(exits)}
    if role: out["closure_role"] = role
    return out


def accepted_pcs():
    pcs = {item["pc_first"] for item in json.loads(BOUNDARY.read_text(encoding="utf-8"))["writer_boundary"]["units"]}
    if len(pcs) != 7314: raise ValueError("accepted boundary PC count differs")
    return pcs


def build():
    identities = {"contract": tsha(CONTRACT), "oracle": tsha(ORACLE), "ledger": sha(LEDGER), "boundary": tsha(BOUNDARY), "trace": sha(TRACE), "opcodes": sha(OPCODES), "program": sha(PROGRAM)}
    if identities != EXPECTED: raise ValueError("settled input identity mismatch")
    sample_rows, epochs, watched, image = rows(), trace(), watchpoints(), OPCODES.read_bytes()
    observations = {"health": [], "hit_value": []}
    for frame in range(FIRST, LAST):
        for event in watched[frame]:
            if event["field"] not in observations: continue
            item = instance(event["field"], event, decode_event(image, event, epochs[frame]))
            item["interval_start_frame"] = frame
            observations[event["field"]].append(item)
    transitions = {"health": [], "hit_value": []}
    for field in transitions:
        for frame, before, after in deltas(sample_rows, field):
            writers = [copy.deepcopy(item) for item in observations[field] if item["interval_start_frame"] == frame]
            if not writers: raise ValueError(f"{field} transition lacks same-interval writer")
            transitions[field].append({"field": field, "interval_start_frame": frame, "semantic_sample_after": frame + 1, "before_value": before, "after_value": after, "writer_instances": writers})

    def anim_anchor(name, after):
        frame = after - 1
        events = [event for event in watched[frame] if event["field"] == "anim_record" and event["destination"] in {ACTOR + 0x1C, ACTOR + 0x1E}]
        decoded = [decode_event(image, event, epochs[frame]) for event in events if event["destination"] == ACTOR + 0x1C]
        if len(events) != 2 or len(decoded) != 1 or {pc for pc, _ in decoded} != {0x16526} or {op["width"] for _, op in decoded} != {4}: raise ValueError(name + " animation store is not the required long write")
        return {"interval_start_frame": frame, "semantic_sample_after": after, "instruction_pc": "0x016526", "watchpoint_reported_pc": h(events[0]["reported_pc"]), "target_actor_base": h(ACTOR), "destination": h(ACTOR + 0x1C), "field": "anim_record", "write_width_bytes": 4, "write_mask": "0xffffffff", "before_value": sample_rows[frame]["anim_record"], "after_value": sample_rows[after]["anim_record"], "watchpoint_bus_event_count": 2, "dynamic_register_binding": {"a0": h(events[0]["registers"]["a0"]), "a6": h(ACTOR)}}

    hit, ko = anim_anchor("HIT", HIT), anim_anchor("KO", KO)
    hit_path, ko_path = path(epochs[HIT - 1], [0x1E888, 0x1E8A4]), path(epochs[KO - 1], [0x1F250, 0x1F254, 0x9D3C4])
    dispatch = [0x1F6C6, 0x1F6C8, 0x1F6CA, 0x1F6CE, 0x1F6D2, 0x1F6D6, 0x1F710, 0x1F712, 0x1F714, 0x1F718, 0x1F71C]
    pointer = [0x16518, 0x1651C, 0x1651E, 0x16522, 0x16526, 0x1652A, 0x1652E, 0x16534]
    routines = [routine(hit_path[0], hit_path, callees=[0x1F6C6], writes=["action", "anim_record", "anim_timer"], exits=["enemy_hit_event"], role="hit_transition"), routine(ko_path[0], ko_path, callees=[0x1F6C6], writes=["state", "sub_state", "anim_record", "anim_timer"], exits=["enemy_ko_event"], role="ko_transition"), routine(0x1F6C6, dispatch, callers=[0x1E8E6, 0x1F2BE], callees=[0x16518], role="animation_dispatch"), routine(0x16518, pointer, callers=[0x1F71C], writes=["anim_record", "anim_timer"], role="animation_pointer_selection")]
    pairs, role_pcs = set(zip(hit_path, hit_path[1:])) | set(zip(ko_path, ko_path[1:])), {}
    for field, items in observations.items():
        for text in sorted({item["instruction_pc"] for item in items}):
            pc = int(text, 16); pcs, local_pairs = context(epochs, items, pc)
            pairs.update(local_pairs); role_pcs.setdefault(field, []).append(text)
            routines.append(routine(pc, pcs, writes=[field], role=field + "_writer_context"))
    selected = sorted({pc for item in routines for pc in item["member_pcs"]})
    boundary = accepted_pcs()
    if not set(selected) <= boundary: raise ValueError("selected PC outside accepted boundary")
    edges = [{"source": h(source), "target": h(target), "kind": edge_kind(image, source)} for source, target in sorted(pairs) if h(source) in set(selected) and h(target) in set(selected)]
    counts = {field: len(deltas(sample_rows, field)) for field in FIELDS}
    if counts != EXPECTED_COUNTS: raise ValueError("seven-field transition count differs")
    report = {"schema": 3, "artifact": "avsp_hit_ko_writer_set", "target": {"set": "avspu", "revision": "USA 940520", "class": 31, "type": 12}, "evidence_tiers": ["MAME_TRACE", "STATIC_ANALYSIS", "MEASURED"], "inputs": {key + "_sha256": value for key, value in identities.items()}, "private_capture": {"watchpoint_log_sha256": sha(LOG), "sample_sha256": sha(SAMPLES), "watchpoint_event_count": sum(len(value) for value in watched.values())}, "address_spaces": {"instructions_and_code_targets": "opcodes", "rom_operands_and_animation_records": "program"}, "window": {"first_source_frame": FIRST, "last_source_frame": LAST, "semantic_sample_count": 1390, "execution_interval_count": 1389, "hit_semantic_sample_after": HIT, "ko_semantic_sample_after": KO, "alignment": "interval N executes from semantic sample N to N+1", "synthetic_final_epoch": False}, "correlations": {"hit": {"semantic_changes": [{"field": "action", "before": sample_rows[HIT - 1]["action"], "after": sample_rows[HIT]["action"]}, {"field": "anim", "before": sample_rows[HIT - 1]["anim_record"], "after": sample_rows[HIT]["anim_record"]}, {"field": "timer", "before": sample_rows[HIT - 1]["anim_timer"], "after": sample_rows[HIT]["anim_timer"]}], "writer_instances": [hit], "closes_gap_external_repoint_ownership": True}, "ko": {"semantic_changes": [{"field": "state", "before": sample_rows[KO - 1]["state"], "after": sample_rows[KO]["state"]}, {"field": "sub", "before": sample_rows[KO - 1]["sub_state"], "after": sample_rows[KO]["sub_state"]}, {"field": "anim", "before": sample_rows[KO - 1]["anim_record"], "after": sample_rows[KO]["anim_record"]}, {"field": "timer", "before": sample_rows[KO - 1]["anim_timer"], "after": sample_rows[KO]["anim_timer"]}], "writer_instances": [ko], "closes_gap_external_repoint_ownership": True}}, "field_transitions": transitions, "writer_observations": observations, "coverage": {"actor_fields": list(FIELDS), "field_transition_counts": counts, "writer_observation_counts": {field: len(items) for field, items in observations.items()}, "computed_target_count": sum(edge["kind"] == "computed_jump" for edge in edges), "event_exit_count": 2, "selected_pc_count": len(selected), "selected_edge_count": len(edges), "selected_routine_count": len(routines)}, "closure": {"selected_pcs": selected, "selected_edges": edges, "selected_routines": routines, "unresolved_computed_targets": [], "unattributed_dependencies": []}, "dependencies": {"rom_data": [{"purpose": "HIT animation record", "address": h(hit["after_value"]), "address_space": "program", "span": ["0x120000", "0x130000"]}, {"purpose": "KO animation record", "address": h(ko["after_value"]), "address_space": "program", "span": ["0x120000", "0x130000"]}], "work_ram": [{"purpose": "class_1f_type_0c_enemy_actor", "address": "0xffa000", "class": 31, "type": 12}], "typed_event_exits": [{"event": "enemy_hit_event", "interval_start_frame": HIT - 1, "writer_pc": "0x01e888"}, {"event": "enemy_ko_event", "interval_start_frame": KO - 1, "writer_pc": "0x01f250"}], "health_hit_writer_dependencies": [{"field": "health", "instruction_space": "opcodes", "required_register_bindings": ["a1", "a6", "d1"], "writer_pcs": sorted(role_pcs["health"])}, {"field": "hit_value", "instruction_space": "opcodes", "required_register_bindings": ["a1", "a6", "d0"], "writer_pcs": sorted(role_pcs["hit_value"])}]}, "exclusions": ["out_of_window_routes", "other_actor_classes", "production_lifted_c"], "forbidden_content_present": False}
    report["integrity"] = integrity(report)
    report["accepted_boundary_binding"] = binding(report, boundary)
    validate_committed(report)
    return report


def integrity(report): return {"semantic_sha256": jhash({key: report["correlations"][key]["semantic_changes"] for key in ("hit", "ko")}), "routine_sha256": jhash(report["closure"]["selected_routines"]), "edge_sha256": jhash(report["closure"]["selected_edges"]), "field_transition_sha256": jhash(report["field_transitions"]), "writer_observation_sha256": jhash(report["writer_observations"])}
def binding(report, boundary): return {"accepted_boundary_pc_count": len(boundary), "selected_pc_sha256": phash(report["closure"]["selected_pcs"]), "selected_edge_sha256": jhash(report["closure"]["selected_edges"]), "selected_routine_sha256": jhash(report["closure"]["selected_routines"]), "field_transition_sha256": report["integrity"]["field_transition_sha256"], "writer_observation_sha256": report["integrity"]["writer_observation_sha256"]}


def walk(value):
    if isinstance(value, dict):
        for key, item in value.items(): yield str(key).lower(); yield from walk(item)
    elif isinstance(value, list):
        for item in value: yield from walk(item)


def validate_committed(report):
    if report.get("schema") != 3 or report.get("artifact") != "avsp_hit_ko_writer_set": raise ValueError("schema")
    if report.get("target") != {"set": "avspu", "revision": "USA 940520", "class": 31, "type": 12}: raise ValueError("target")
    if report.get("inputs") != {key + "_sha256": value for key, value in EXPECTED.items()}: raise ValueError("settled inputs")
    window = {"first_source_frame": FIRST, "last_source_frame": LAST, "semantic_sample_count": 1390, "execution_interval_count": 1389, "hit_semantic_sample_after": HIT, "ko_semantic_sample_after": KO, "alignment": "interval N executes from semantic sample N to N+1", "synthetic_final_epoch": False}
    if report.get("window") != window: raise ValueError("exact accepted anchors")
    coverage, transitions, observed = report.get("coverage", {}), report.get("field_transitions", {}), report.get("writer_observations", {})
    if tuple(coverage.get("actor_fields", ())) != FIELDS or coverage.get("field_transition_counts") != EXPECTED_COUNTS: raise ValueError("seven-field coverage")
    for field, count in (("health", 4), ("hit_value", 42)):
        if len(transitions.get(field, [])) != count or not observed.get(field): raise ValueError(field + " transition coverage")
        for item in transitions[field]:
            if item.get("field") != field or item.get("semantic_sample_after") != item.get("interval_start_frame", -1) + 1 or "before_value" not in item or "after_value" not in item or not item.get("writer_instances"): raise ValueError(field + " before/after writer binding")
    if coverage.get("writer_observation_counts") != {field: len(observed[field]) for field in ("health", "hit_value")}: raise ValueError("writer observation counts")
    closure, selected, routines, edges = report.get("closure", {}), report.get("closure", {}).get("selected_pcs", []), report.get("closure", {}).get("selected_routines", []), report.get("closure", {}).get("selected_edges", [])
    boundary = accepted_pcs()
    if not selected or len(selected) != len(set(selected)) or not set(selected) <= boundary: raise ValueError("accepted boundary PC membership")
    entries, union = [item.get("entry_pc") for item in routines], set()
    if not entries or len(entries) != len(set(entries)): raise ValueError("unique routine entries")
    for item in routines:
        members = item.get("member_pcs", [])
        if item.get("member_pc_count") != len(members) or item.get("member_pc_sha256") != phash(members) or item.get("entry_pc") not in members or len(members) != len(set(members)) or not set(members) <= set(selected): raise ValueError("routine membership")
        union.update(members)
    if union != set(selected): raise ValueError("routine/selected-PC union")
    if not edges or any(edge.get("source") not in selected or edge.get("target") not in selected or edge.get("kind") not in {"fallthrough", "call", "return", "computed_jump", "conditional_branch"} for edge in edges): raise ValueError("edge shape")
    if len({(edge["source"], edge["target"], edge["kind"]) for edge in edges}) != len(edges): raise ValueError("edge uniqueness")
    for item in routines:
        members = set(item["member_pcs"])
        if any(not any(edge["source"] == caller and edge["target"] == item["entry_pc"] for edge in edges) for caller in item["observed_callers"]): raise ValueError("caller relationship")
        if any(not any(edge["source"] in members and edge["target"] == callee for edge in edges) for callee in item["observed_callees"]): raise ValueError("callee relationship")
    if closure.get("unresolved_computed_targets") or closure.get("unattributed_dependencies"): raise ValueError("unresolved dependency")
    if (coverage.get("selected_pc_count"), coverage.get("selected_edge_count"), coverage.get("selected_routine_count")) != (len(selected), len(edges), len(routines)): raise ValueError("selected closure counts")
    if coverage.get("computed_target_count") != sum(edge["kind"] == "computed_jump" for edge in edges) or coverage.get("event_exit_count") != len(report.get("dependencies", {}).get("typed_event_exits", [])): raise ValueError("derived counts")
    for name, after in (("hit", HIT), ("ko", KO)):
        correlation = report.get("correlations", {}).get(name, {}); changes = {item["field"]: (item["before"], item["after"]) for item in correlation.get("semantic_changes", [])}; writers = correlation.get("writer_instances", [])
        if "anim" not in changes or not correlation.get("closes_gap_external_repoint_ownership") or len(writers) != 1: raise ValueError(name + " semantic binding")
        writer = writers[0]
        if (writer.get("interval_start_frame"), writer.get("semantic_sample_after"), writer.get("instruction_pc"), writer.get("target_actor_base"), writer.get("destination"), writer.get("field"), writer.get("write_width_bytes"), writer.get("write_mask"), writer.get("before_value"), writer.get("after_value")) != (after - 1, after, "0x016526", "0xffa000", "0xffa01c", "anim_record", 4, "0xffffffff", changes["anim"][0], changes["anim"][1]): raise ValueError(name + " animation writer")
    for field, widths, destination in (("health", {2}, "0xffa040"), ("hit_value", {1, 4}, "0xffa02c")):
        for item in observed[field]:
            if item.get("field") != field or item.get("destination") != destination or item.get("write_width_bytes") not in widths or item.get("instruction_pc") not in selected: raise ValueError(field + " effective address")
            registers = item.get("dynamic_register_binding", {})
            if field == "health" and item.get("effective_address_register") not in {"a1", "a6"}: raise ValueError("health effective-address register")
            if field == "health" and item.get("instruction_pc") == "0x01d58a" and not {"a1", "d1"} <= set(registers): raise ValueError("health live registers")
            if field == "hit_value" and item.get("effective_address_register") not in {"a1", "a6"}: raise ValueError("hit live registers")
    dependencies = report.get("dependencies", {}); rom = dependencies.get("rom_data", [])
    if len(rom) != 2 or any(item.get("address_space") != "program" or not int(item["span"][0], 16) <= int(item["address"], 16) < int(item["span"][1], 16) for item in rom): raise ValueError("program dependencies")
    if dependencies.get("work_ram") != [{"purpose": "class_1f_type_0c_enemy_actor", "address": "0xffa000", "class": 31, "type": 12}]: raise ValueError("actor dependency")
    if {item.get("event") for item in dependencies.get("typed_event_exits", [])} != {"enemy_hit_event", "enemy_ko_event"} or len(dependencies.get("typed_event_exits", [])) != 2: raise ValueError("event exits")
    writer_dependencies = {item.get("field"): item for item in dependencies.get("health_hit_writer_dependencies", [])}
    if set(writer_dependencies) != {"health", "hit_value"} or len(writer_dependencies) != 2: raise ValueError("health/hit dependencies")
    expected_dependency_registers = {"health": ["a1", "a6", "d1"], "hit_value": ["a1", "a6", "d0"]}
    for field, expected_registers in expected_dependency_registers.items():
        dependency = writer_dependencies[field]
        observed_pcs = sorted({item["instruction_pc"] for item in observed[field]})
        observed_registers = {register for item in observed[field] for register in item.get("dynamic_register_binding", {})}
        if dependency.get("instruction_space") != "opcodes" or dependency.get("writer_pcs") != observed_pcs or dependency.get("required_register_bindings") != expected_registers or not set(expected_registers) <= observed_registers: raise ValueError("health/hit dependency closure")
    if report.get("integrity") != integrity(report): raise ValueError("integrity")
    expected_binding = binding(report, boundary)
    if report.get("accepted_boundary_binding") != expected_binding: raise ValueError("accepted-boundary binding")
    if IMMUTABLE_BINDING is not None and expected_binding != IMMUTABLE_BINDING: raise ValueError("immutable PC/edge/routine binding")
    if any(isinstance(item, dict) and item.get("kind") == "in_window_target_writer" for item in report.get("exclusions", [])): raise ValueError("in-window writer exclusion")
    if report.get("forbidden_content_present") is not False or FORBIDDEN & set(walk(report)): raise ValueError("forbidden content")


def self_test():
    report = build()
    health_a1 = next(item for item in report["writer_observations"]["health"] if item["instruction_pc"] == "0x01d58a")
    mutations = [lambda x: x["correlations"]["hit"]["writer_instances"].pop(), lambda x: x["correlations"]["ko"]["writer_instances"].pop(), lambda x: x["field_transitions"]["health"].pop(), lambda x: x["writer_observations"]["hit_value"].pop(), lambda x: x["field_transitions"]["health"][0].__setitem__("after_value", -999), lambda x: x["writer_observations"]["health"][0].__setitem__("destination", "0xffa044"), lambda x: x["writer_observations"]["hit_value"][0].__setitem__("write_width_bytes", 2), lambda x: x["writer_observations"]["health"][0].__setitem__("instruction_pc", "0xfffffe"), lambda x: next(item for item in x["writer_observations"]["health"] if item["instruction_pc"] == health_a1["instruction_pc"])["dynamic_register_binding"].pop("a1"), lambda x: x["dependencies"]["health_hit_writer_dependencies"][0]["writer_pcs"].pop(), lambda x: x["window"].__setitem__("hit_semantic_sample_after", HIT + 1), lambda x: x["closure"]["selected_pcs"].append("0xfffffe"), lambda x: x["closure"]["selected_edges"].pop(), lambda x: x["closure"]["selected_routines"][2].__setitem__("member_pc_count", 1), lambda x: x["coverage"].__setitem__("event_exit_count", 999), lambda x: x["exclusions"].append({"kind": "in_window_target_writer"}), lambda x: x.__setitem__("trace_text", "forbidden")]
    for mutate in mutations:
        candidate = copy.deepcopy(report); mutate(candidate)
        try: validate_committed(candidate)
        except (AttributeError, KeyError, TypeError, ValueError): continue
        raise AssertionError("production validator accepted committed-artifact control")
    print("HIT/KO writer-set self-test and committed-artifact controls passed")


def scratch_mutation_test():
    sample_rows, watched = rows(), watchpoints()
    altered_rows = copy.deepcopy(sample_rows); altered_rows[5190]["health"] += 1
    altered_watch = copy.deepcopy(watched)
    altered_watch[5189] = [item for item in altered_watch[5189] if item["field"] != "hit_value"]
    original_rows, original_watchpoints = globals()["rows"], globals()["watchpoints"]
    try:
        globals()["rows"] = lambda: altered_rows
        try: build()
        except (KeyError, TypeError, ValueError): pass
        else: raise AssertionError("accepted end-to-end private health mutation")
        globals()["rows"] = original_rows
        globals()["watchpoints"] = lambda: altered_watch
        try: build()
        except (KeyError, TypeError, ValueError): pass
        else: raise AssertionError("accepted end-to-end private hit watchpoint removal")
    finally:
        globals()["rows"] = original_rows
        globals()["watchpoints"] = original_watchpoints
    print("end-to-end private health mutation and hit watchpoint-removal controls rejected")


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--self-test", action="store_true"); parser.add_argument("--generate", action="store_true"); parser.add_argument("--scratch-mutation-test", action="store_true"); args = parser.parse_args()
    if args.self_test: self_test()
    elif args.generate:
        report = build(); OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"); validate_committed(json.loads(OUT.read_text(encoding="utf-8"))); print(f"wrote {OUT} sha256={sha(OUT)}")
    elif args.scratch_mutation_test: scratch_mutation_test()
    else: parser.error("choose a command")


if __name__ == "__main__": main()
