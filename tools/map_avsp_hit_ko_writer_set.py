"""Derive the bounded AVSP class-1F HIT/KO writer closure from private evidence.

Only typed values, PCs, addresses, counts, and hashes are committed.  The
trace, opcode image, samples, and watchpoint log remain private under .deps.

Schema 4 corrections: every seven-field transition binds its exact decoded
writer instances with per-byte reconstruction; control flow is a call-rooted
closure derived from a per-interval 68000 call-stack walk that treats every
in-interval RTE as a task-scheduler context switch (a typed exit); and the
actor-field, ROM-data, work-RAM, edge, and exclusion dependencies are derived
from the decoded stores and the dynamic walk instead of being asserted.
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
# Byte layout inside the class-1F actor block, verified during generation by
# reconstructing all 1,104 semantic transitions from the decoded bus bytes.
FIELD_LAYOUT = {
    "state": {"byte_offset": 0x00, "byte_width": 1, "signed": False},
    "sub_state": {"byte_offset": 0x04, "byte_width": 2, "signed": False},
    "action": {"byte_offset": 0x06, "byte_width": 2, "signed": False},
    "anim_record": {"byte_offset": 0x1C, "byte_width": 4, "signed": False},
    "anim_timer": {"byte_offset": 0x2A, "byte_width": 2, "signed": False},
    "health": {"byte_offset": 0x40, "byte_width": 2, "signed": True},
    "hit_value": {"byte_offset": 0x2C, "byte_width": 1, "signed": False},
}
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
IMMUTABLE_CLAIMS = {
    "evidence_tiers": ("MAME_TRACE", "STATIC_ANALYSIS", "MEASURED"),
    "private_capture": {
        "watchpoint_log_sha256": "ab3955f11b0d8c9ca7947d014162412232f233ef3a20e6383a6d5cce613b7827",
        "sample_sha256": "4a68d6f5e955711365f2a197ee0b6dac6527f4d4d1ef7519c7809239622a5cab",
        "watchpoint_event_count": 1446,
        "decoded_store_instance_count": 1159,
    },
    "address_spaces": {
        "instructions_and_code_targets": "opcodes",
        "rom_operands_and_animation_records": "program",
    },
    "typed_event_exits": (
        ("enemy_hit_event", 5190, "0x01e888"),
        ("enemy_ko_event", 5329, "0x01f250"),
    ),
    "task_root_entry": "0x0080b4",
    "anim_anchor_pc": "0x016526",
}
# Filled after one successful private-evidence generation, then frozen.  These
# bind the public closure rather than carrying any private raw evidence.
IMMUTABLE_INTEGRITY = {
    "semantic_sha256": "1704a55a33d987c9e0914aa806c4bb9340ec817dcc03cbe776f6c6db0b12fe1c",
    "routine_sha256": "794a0b3a5febfeed22a992051715820b20ed5f4aa96fd868c380bd887f65a994",
    "edge_sha256": "a6465782c021ebca0f2784c4f1add73f4c3bdfcfb391ba5e4a65f637115499e4",
    "field_transition_sha256": "e3a7eedc0a770b99a4d4b5f36807f9d2e8113f0cadb078403b839e7502da1c8b",
    "writer_instance_sha256": "25fe93fd2aa49a27c2a6626028671e99ab6702fc47d0d0419e7943388f3c692f",
    "dependency_sha256": "12f0277f6456bf2065aa51218a4afc3586ee5c0e5abc0ef43144c9c7dfef353b",
    "exclusion_sha256": "f5e92ab2d3b54d08449f3cf3eac31dce7b93d000d18c4802f98872eb2043d473",
}
IMMUTABLE_BINDING = {
    "accepted_boundary_pc_count": 7314,
    "selected_pc_sha256": "e6a162490b2e6bab15de17e3e39d0825a70228939de39e8a6e129d3bb15617ea",
    "selected_edge_sha256": "a6465782c021ebca0f2784c4f1add73f4c3bdfcfb391ba5e4a65f637115499e4",
    "selected_routine_sha256": "794a0b3a5febfeed22a992051715820b20ed5f4aa96fd868c380bd887f65a994",
    "field_transition_sha256": "e3a7eedc0a770b99a4d4b5f36807f9d2e8113f0cadb078403b839e7502da1c8b",
    "writer_instance_sha256": "25fe93fd2aa49a27c2a6626028671e99ab6702fc47d0d0419e7943388f3c692f",
    "dependency_sha256": "12f0277f6456bf2065aa51218a4afc3586ee5c0e5abc0ef43144c9c7dfef353b",
    "exclusion_sha256": "f5e92ab2d3b54d08449f3cf3eac31dce7b93d000d18c4802f98872eb2043d473",
}
LINE = re.compile(r"^([0-9a-fA-F]{6,8}):")
TRACE_INSTRUCTION = re.compile(r"^([0-9a-fA-F]{6,8}):\s+([.a-zA-Z0-9]+)(?:\s+(.*))?$")
IRQ = re.compile(r"^\(interrupted at [0-9a-fA-F]{4,8}, IRQ \d+\)$")
MARK = re.compile(r"AVP_HIT_KO_INTERVAL_START (\d+)")
WP = re.compile(r"AVP_HIT_KO_WP .* field=(\w+) addr=([0-9A-F]+) data=([0-9A-F]+) pc=([0-9A-F]+) d0=([0-9A-F]+) d1=([0-9A-F]+) a0=([0-9A-F]+) a1=([0-9A-F]+) a2=([0-9A-F]+) a3=([0-9A-F]+) a4=([0-9A-F]+) a5=([0-9A-F]+) a6=([0-9A-F]+) a7=([0-9A-F]+)")
FORBIDDEN = {"raw", "bytes", "opcode_words", "disassembly", "disassembly_text", "trace_text", "trace_lines", "state_dump", "screenshot"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX6 = re.compile(r"^0x[0-9a-f]{6}$")
HEX8 = re.compile(r"^0x[0-9a-f]{8}$")
HEX2 = re.compile(r"^0x[0-9a-f]{2}$")
EDGE_KINDS = {"fallthrough", "call", "return", "computed_jump", "branch", "rte"}
EXIT_KEYS = ("return", "context_switch", "interval_end", "context_return")
ROLES = {"writer_owner", "dispatch_chain", "task_root"}
ACTOR_OFFSET = re.compile(r"\(([-$0-9a-fA-F]+),A[456]\)")
ABSOLUTE = re.compile(r"\$([0-9a-fA-F]{4,8})\.l")
KNOWN_ACTOR_OFFSETS = {
    0x00: "state", 0x02: "class_id", 0x04: "sub_state", 0x06: "action",
    0x08: "type", 0x0F: "facing", 0x10: "world_x", 0x14: "world_y",
    0x18: "world_z", 0x1C: "anim_record", 0x2A: "anim_timer",
    0x2C: "hit_value", 0x2D: "hit_source", 0x40: "health", 0x50: "table_set",
    0x67: "attacker_id", 0x68: "per_attacker_latch", 0x70: "suppress",
    0xD1: "latch_index",
}


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def tsha(path): return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
def h(value): return f"0x{value:06x}"
def h2(value): return f"0x{value:02x}"
def jhash(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
def phash(pcs): return hashlib.sha256("\n".join(sorted(set(pcs))).encode()).hexdigest()
def word(image, pc): return int.from_bytes(image[pc:pc + 2], "big")
def s16(value): return value - 0x10000 if value & 0x8000 else value


def parse_offset(text):
    text = text.strip().lower()
    try: return int(text[1:], 16) if text.startswith("$") else int(text, 10)
    except ValueError: return None


def trace_metadata():
    """Return only stable parsed operand metadata; never retain trace lines."""
    out = {}
    for raw in TRACE.open(encoding="utf-8", errors="replace"):
        match = TRACE_INSTRUCTION.match(raw.strip())
        if not match: continue
        pc, mnemonic, operand = int(match.group(1), 16), match.group(2).lower(), (match.group(3) or "").strip()
        info = out.setdefault(pc, {"count": 0, "mnemonic": mnemonic, "operand": operand})
        if (info["mnemonic"], info["operand"]) != (mnemonic, operand): raise ValueError("ambiguous trace operand metadata")
        info["count"] += 1
    return out


def is_direct_control_operand(mnemonic, operand):
    if "(" in operand: return False
    return mnemonic in {"bsr", "jsr", "jmp", "bra"}


def derive_operand_dependencies(metadata, selected):
    actor, rom, work_ram = {}, {}, {}
    for pc in sorted(int(value, 16) for value in selected):
        info = metadata.get(pc)
        if info is None: raise ValueError("selected PC lacks trace operand metadata")
        for match in ACTOR_OFFSET.finditer(info["operand"]):
            field = KNOWN_ACTOR_OFFSETS.get(parse_offset(match.group(1)))
            if field: actor.setdefault(field, {}).setdefault(pc, info["count"])
        if is_direct_control_operand(info["mnemonic"], info["operand"]): continue
        for match in ABSOLUTE.finditer(info["operand"]):
            address = int(match.group(1), 16)
            target = rom if address <= 0x1FFFFF else (work_ram if 0xFF0000 <= address <= 0xFFFFFF else None)
            if target is not None: target[address] = target.get(address, 0) + info["count"]
    actor_report = {}
    for field, refs in sorted(actor.items()):
        pcs = sorted(h(pc) for pc in refs)
        actor_report[field] = {"reference_pcs": pcs, "reference_pc_sha256": phash(pcs), "execution_count": sum(refs.values())}
    def absolute_report(values):
        addresses = sorted(h(address) for address in values)
        return {"address_count": len(addresses), "address_sha256": phash(addresses), "min_address": addresses[0] if addresses else None, "max_address": addresses[-1] if addresses else None, "execution_count": sum(values.values())}
    return actor_report, absolute_report(rom), absolute_report(work_ram)


def referenced_actor_fields(metadata, pcs):
    fields = set()
    for pc in pcs:
        for match in ACTOR_OFFSET.finditer(metadata[int(pc, 16)]["operand"]):
            field = KNOWN_ACTOR_OFFSETS.get(parse_offset(match.group(1)))
            if field: fields.add(field)
    return sorted(fields)


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
    if opcode & 0xFF00 == 0x4200 and (opcode >> 6) & 3 != 3:
        size = {0: 1, 1: 2, 2: 4}[(opcode >> 6) & 3]
        ea = memory_ea(image, (opcode >> 3) & 7, opcode & 7, pc + 2)
        if ea: return {"width": size, "ea": ea, "source": None}
    return None


def edge_kind(image, pc):
    opcode = word(image, pc)
    if opcode & 0xFF00 == 0x6100 or opcode & 0xFFC0 == 0x4E80: return "call"
    if opcode in (0x4E75, 0x4E77): return "return"
    if opcode == 0x4E73: return "rte"
    if opcode & 0xFFC0 == 0x4EC0: return "computed_jump"
    if opcode & 0xF000 == 0x6000 or opcode & 0xF0F8 == 0x50C8: return "branch"
    return "other"


def group_bus_events(events):
    """Merge consecutive bus events of one multi-word store: identical
    successor PC and register snapshot with the destination advancing by 2."""
    groups = []
    for event in events:
        if groups:
            last = groups[-1][-1]
            if (event["reported_pc"] == last["reported_pc"] and event["registers"] == last["registers"]
                    and event["destination"] == last["destination"] + 2):
                groups[-1].append(event)
                continue
        groups.append([event])
    return groups


def decode_group(image, group, pcs):
    base, registers, reported = group[0]["destination"], group[0]["registers"], group[0]["reported_pc"]
    candidates = []
    for pc in sorted(pcs):
        if not reported - 16 <= pc < reported: continue
        decoded = store(image, pc)
        if not decoded: continue
        register, displacement = decoded["ea"]
        if (registers[register] + displacement) & 0xFFFFFF != base & 0xFFFFFF: continue
        if (2 if decoded["width"] == 4 else 1) < len(group): continue
        candidates.append((pc, decoded))
    if not candidates: raise ValueError(f"missing effective address at {h(reported)}")
    # MAME reports the successor PC.  A same-interval earlier store can address
    # the same actor field, so select the nearest preceding decoded instruction
    # and reject a tie rather than guessing.
    nearest = min(reported - pc for pc, _ in candidates)
    candidates = [item for item in candidates if reported - item[0] == nearest]
    if len(candidates) != 1: raise ValueError(f"ambiguous effective address at {h(reported)}")
    return candidates[0]


def written_bytes(group, decoded):
    out = {}
    for event in group:
        offset = event["destination"] - ACTOR
        if decoded["width"] == 1:
            out[offset] = event["data"] & 0xFF
        else:
            out[offset] = (event["data"] >> 8) & 0xFF
            out[offset + 1] = event["data"] & 0xFF
    return out


def walk_writer_ownership(epochs, watched, image):
    """Per-interval call-stack walk.  Calls push, returns pop, and every
    in-interval RTE is a task-scheduler context switch that terminates the
    whole simulated context (the derived typed exit).  Returns the decoded
    writer instances with call-rooted ownership plus the owning/chain entries."""
    instances, owners, chains, roots = [], set(), set(), {}
    for frame in sorted(epochs):
        if frame not in watched or not watched[frame]: continue
        sequence = epochs[frame]
        pcs = set(sequence)
        pending = {}
        for order, group in enumerate(group_bus_events(watched[frame])):
            pc, decoded = decode_group(image, group, pcs)
            pending.setdefault(pc, []).append((order, group, decoded))
        made = {}
        # frame: [entry, flagged, by_call, instance_indexes]
        stack = [[sequence[0], False, False, []]]
        root_kind = "interval_start"
        count = len(sequence)
        for position in range(count):
            pc = sequence[position]
            if pc in pending and pending[pc]:
                order, group, decoded = pending[pc].pop(0)
                top = stack[-1]
                register, displacement = decoded["ea"]
                binding = {register: h(group[0]["registers"][register])}
                if decoded["source"] in ("d0", "d1"): binding[decoded["source"]] = h(group[0]["registers"][decoded["source"]])
                item = {
                    "interval_start_frame": frame, "sequence_in_interval": order,
                    "instruction_pc": h(pc), "watchpoint_reported_pc": h(group[0]["reported_pc"]),
                    "destination": h(group[0]["destination"]), "write_width_bytes": decoded["width"],
                    "bus_event_count": len(group), "fields": sorted({event["field"] for event in group}),
                    "written_bytes": {h2(offset): value for offset, value in sorted(written_bytes(group, decoded).items())},
                    "effective_address_register": register, "effective_address_displacement": displacement,
                    "dynamic_register_binding": binding,
                    "owner_entry_pc": h(top[0]), "owner_entered_by_call": top[2], "owner_exit": None,
                }
                made[(frame, order)] = item
                top[3].append(item)
                if not top[1]:
                    top[1] = True
                    for ancestor in stack[:-1]: chains.add(ancestor[0])
                owners.add(top[0])
                roots.setdefault(root_kind, set()).add(stack[0][0])
                if not pending[pc]: del pending[pc]
            kind = edge_kind(image, pc)
            following = sequence[position + 1] if position + 1 < count else None
            if following is None:
                for entry in stack:
                    for item in entry[3]: item["owner_exit"] = "interval_end"
                break
            if kind == "call":
                stack.append([following, False, True, []])
            elif kind == "return":
                if len(stack) > 1:
                    left = stack.pop()
                    for item in left[3]: item["owner_exit"] = "return"
                else:
                    for item in stack[0][3]: item["owner_exit"] = "context_return"
                    stack[0] = [following, False, False, []]
                    root_kind = "task_return_resume"
            elif kind == "rte":
                for entry in stack:
                    for item in entry[3]: item["owner_exit"] = "context_switch"
                stack = [[following, False, False, []]]
                root_kind = "task_rte_resume"
        if pending: raise ValueError("writer instance without executed occurrence")
        for _, item in sorted(made.items()): instances.append(item)
    for index, item in enumerate(instances):
        if item["owner_exit"] is None: raise ValueError("writer instance without derived owner exit")
        item["index"] = index
    return instances, owners, chains, roots


def walk_closure(epochs, image, selected_units, writer_occurrences):
    """Aggregate, over all in-window intervals, per-unit top-of-stack members,
    dynamic callers/callees, exit accounting, executed edges inside the
    closure, external-callee sites, and the writer-free proof inputs."""
    members = {unit: set() for unit in selected_units}
    all_members, all_callees = {}, {}
    callers = {unit: set() for unit in selected_units}
    callees = {unit: set() for unit in selected_units}
    external = {}
    exits = {unit: {key: 0 for key in EXIT_KEYS} for unit in selected_units}
    pairs, pair_counts = {}, {}
    loop_discontinuities = []
    for frame in sorted(epochs):
        sequence = epochs[frame]
        # Carry the directly selected call whose external subtree is being
        # proved writer-free.  A shared routine can reach an actor writer in
        # one invocation and be writer-free in another, so routine-union
        # reachability is not evidence about this exact dynamic call site.
        stack = [[sequence[0], None]]
        count = len(sequence)
        for position in range(count):
            pc = sequence[position]
            top, external_origin = stack[-1]
            if (external_origin is not None
                    and top in writer_occurrences.get((frame, pc), set())):
                external[external_origin]["writer_seen"] = True
            all_members.setdefault(top, set()).add(pc)
            if top in selected_units: members[top].add(pc)
            kind = edge_kind(image, pc)
            following = sequence[position + 1] if position + 1 < count else None
            if following is None:
                if top in selected_units: exits[top]["interval_end"] += 1
                break
            if kind == "other" and not pc + 2 <= following <= pc + 12:
                if top in selected_units:
                    loop_discontinuities.append((frame, pc, following, top))
                continue
            if top in selected_units:
                pairs[(pc, following)] = "fallthrough" if kind == "other" else kind
                pair_counts[(pc, following)] = pair_counts.get((pc, following), 0) + 1
            if kind == "call":
                all_callees.setdefault(top, set()).add(following)
                child_origin = external_origin
                if top in selected_units:
                    callees[top].add(following)
                    if following not in selected_units:
                        record = external.setdefault(following, {"sites": set(), "writer_seen": False})
                        record["sites"].add((top, pc))
                        child_origin = following
                if top in selected_units and following in selected_units:
                    callers[following].add((top, pc))
                stack.append([following, child_origin])
            elif kind == "return":
                if len(stack) > 1:
                    left = stack.pop()[0]
                    if left in selected_units: exits[left]["return"] += 1
                else:
                    if stack[0][0] in selected_units: exits[stack[0][0]]["context_return"] += 1
                    stack[0] = [following, None]
            elif kind == "rte":
                for entry, _ in stack:
                    if entry in selected_units: exits[entry]["context_switch"] += 1
                stack = [[following, None]]
    union = set()
    for unit in selected_units: union |= members[unit]
    edges = {pair: kind for pair, kind in pairs.items() if pair[0] in union and pair[1] in union}
    outgoing = [
        {"source": h(source), "target": h(target), "kind": pairs[(source, target)], "occurrence_count": pair_counts[(source, target)]}
        for source, target in sorted(pairs)
        if source in union and target not in union
    ]
    collapse_rows = ["%d:%s:%s:%s" % (frame, h(source), h(target), h(entry)) for frame, source, target, entry in loop_discontinuities]
    collapse_dependency = {
        "kind": "mame_trace_repeat_collapse",
        "occurrence_count": len(collapse_rows),
        "unique_pair_count": len({(source, target) for _, source, target, _ in loop_discontinuities}),
        "occurrence_sha256": hashlib.sha256("\n".join(collapse_rows).encode()).hexdigest(),
    }
    scheduler = {entry for entry in external if any(edge_kind(image, pc) == "rte" for pc in all_members.get(entry, ()))}

    external_records = {
        entry: {
            "sites": sorted(record["sites"]),
            "writer_free": not record["writer_seen"],
            "scheduler": entry in scheduler,
        }
        for entry, record in external.items()
    }
    return members, callers, callees, exits, edges, outgoing, external_records, collapse_dependency


def field_deltas(sample_rows, field):
    return [(frame, sample_rows[frame][field], sample_rows[frame + 1][field]) for frame in range(FIRST, LAST) if sample_rows[frame][field] != sample_rows[frame + 1][field]]


def field_value_from_overlay(field, overlay, fallback):
    layout = FIELD_LAYOUT[field]
    offset, width = layout["byte_offset"], layout["byte_width"]
    value = 0
    for i in range(width):
        byte = overlay.get(offset + i)
        if byte is None: byte = (fallback >> (8 * (width - 1 - i))) & 0xFF
        value = (value << 8) | byte
    if layout["signed"] and value & (1 << (8 * width - 1)): value -= 1 << (8 * width)
    return value


def bind_transitions(sample_rows, instances):
    by_interval = {}
    for item in instances: by_interval.setdefault(item["interval_start_frame"], []).append(item)
    transitions = {field: [] for field in FIELDS}
    for field in FIELDS:
        layout = FIELD_LAYOUT[field]
        span = range(layout["byte_offset"], layout["byte_offset"] + layout["byte_width"])
        for frame, before, after in field_deltas(sample_rows, field):
            overlay, last_writer, indices = {}, {}, []
            for item in sorted(by_interval.get(frame, []), key=lambda entry: entry["sequence_in_interval"]):
                touched = {int(key, 16): value for key, value in item["written_bytes"].items() if int(key, 16) in span}
                if not touched: continue
                overlay.update(touched)
                indices.append(item["index"])
                for offset in touched: last_writer[offset] = item["instruction_pc"]
            if not indices: raise ValueError(field + " transition lacks same-interval writer")
            if field_value_from_overlay(field, overlay, before) != after: raise ValueError(field + " transition reconstruction differs")
            transitions[field].append({
                "field": field, "interval_start_frame": frame, "semantic_sample_after": frame + 1,
                "before_value": before, "after_value": after,
                "writer_instance_indices": indices,
                "surviving_writer_pcs": sorted(set(last_writer.values())),
            })
    return transitions


def accepted_pcs():
    pcs = {int(item["pc_first"], 16) for item in json.loads(BOUNDARY.read_text(encoding="utf-8"))["writer_boundary"]["units"]}
    if len(pcs) != 7314: raise ValueError("accepted boundary PC count differs")
    return pcs


def build():
    identities = {"contract": tsha(CONTRACT), "oracle": tsha(ORACLE), "ledger": sha(LEDGER), "boundary": tsha(BOUNDARY), "trace": sha(TRACE), "opcodes": sha(OPCODES), "program": sha(PROGRAM)}
    if identities != EXPECTED: raise ValueError("settled input identity mismatch")
    sample_rows, epochs, watched, image = rows(), trace(), watchpoints(), OPCODES.read_bytes()
    metadata = trace_metadata()
    program_size = PROGRAM.stat().st_size
    if {row["type"] for row in sample_rows.values()} != {12} or {row["class"] for row in sample_rows.values()} != {0, 31}: raise ValueError("target actor class/type identity differs")

    instances, owners, chains, roots = walk_writer_ownership(epochs, watched, image)
    if set(roots) != {"task_return_resume"} or roots["task_return_resume"] != {int(IMMUTABLE_CLAIMS["task_root_entry"], 16)}:
        raise ValueError("writer ownership is not rooted at the derived task-return context")
    if any(not item["owner_entered_by_call"] for item in instances): raise ValueError("writer owner is not call-rooted")
    task_root = int(IMMUTABLE_CLAIMS["task_root_entry"], 16)
    selected_units = owners | chains | {task_root}
    writer_occurrences = {}
    for item in instances:
        key = (item["interval_start_frame"], int(item["instruction_pc"], 16))
        writer_occurrences.setdefault(key, set()).add(int(item["owner_entry_pc"], 16))
    # A direct external invocation that dynamically contains one of the exact
    # decoded writer occurrences is part of the call-rooted closure, even when
    # the same shared callee is writer-free at other call sites.  Add only those
    # observed invocation roots and iterate to a fixed point; the remaining
    # outgoing calls then have an occurrence-specific writer-free proof.
    for _ in range(8):
        members, callers, callees, exits, edges, outgoing_edges, external_records, collapse_dependency = walk_closure(epochs, image, selected_units, writer_occurrences)
        writer_bearing = {entry for entry, record in external_records.items() if not record["writer_free"]}
        member_union = {pc for unit in selected_units for pc in members[unit]}
        embedded_call_entries = {entry for entry in external_records if entry in member_union}
        additions = writer_bearing | embedded_call_entries
        if not additions: break
        selected_units |= additions
    else:
        raise ValueError("writer-bearing external closure did not converge")
    for entry, record in sorted(external_records.items()):
        if not record["writer_free"]: raise ValueError("external callee is not writer-free outside the selection")
    transitions = bind_transitions(sample_rows, instances)
    counts = {field: len(transitions[field]) for field in FIELDS}
    if counts != EXPECTED_COUNTS: raise ValueError("seven-field transition count differs")

    def anchor(after, fields):
        interval = after - 1
        anim = [item for item in instances if item["interval_start_frame"] == interval and "anim_record" in item["fields"] and item["write_width_bytes"] == 4]
        anim = [item for item in anim if field_value_from_overlay("anim_record", {int(k, 16): v for k, v in item["written_bytes"].items()}, 0) == sample_rows[after]["anim_record"]]
        if len({item["instruction_pc"] for item in anim}) != 1 or anim[-1]["instruction_pc"] != IMMUTABLE_CLAIMS["anim_anchor_pc"]:
            raise ValueError("animation anchor writer differs from the settled repoint instruction")
        return {"semantic_changes": [{"field": name, "before": sample_rows[interval][name], "after": sample_rows[after][name]} for name in fields], "anim_writer_instance_index": anim[-1]["index"], "closes_gap_external_repoint_ownership": True}

    correlations = {"hit": anchor(HIT, ("action", "anim_record", "anim_timer")), "ko": anchor(KO, ("state", "sub_state", "anim_record", "anim_timer"))}
    typed_exits = []
    for event, interval, expected_pc in IMMUTABLE_CLAIMS["typed_event_exits"]:
        field = "action" if event == "enemy_hit_event" else "sub_state"
        transition = next(item for item in transitions[field] if item["interval_start_frame"] == interval)
        first_pc = instances[transition["writer_instance_indices"][0]]["instruction_pc"]
        if first_pc != expected_pc: raise ValueError("typed event exit writer differs from the settled claim")
        typed_exits.append({"event": event, "interval_start_frame": interval, "writer_pc": first_pc})

    owner_units = {int(item["owner_entry_pc"], 16) for item in instances}
    if owner_units != owners: raise ValueError("owner accounting differs")
    field_writes = {}
    for item in instances:
        entry = item["owner_entry_pc"]
        field_writes.setdefault(entry, set()).update(item["fields"])
    routines = []
    for entry in sorted(selected_units):
        role = "writer_owner" if entry in owners else ("task_root" if entry == task_root else "dispatch_chain")
        unit_members = sorted(h(pc) for pc in members[entry])
        routines.append({
            "entry_pc": h(entry), "closure_role": role,
            "member_pc_count": len(unit_members), "member_pc_sha256": phash(unit_members), "member_pcs": unit_members,
            "observed_callers": [{"caller_entry_pc": h(caller), "call_site_pc": h(site)} for caller, site in sorted(callers[entry])],
            "observed_selected_callees": sorted(h(callee) for callee in callees[entry] if callee in selected_units),
            "actor_field_references": referenced_actor_fields(metadata, unit_members),
            "actor_field_writes": sorted(field_writes.get(h(entry), set())),
            "exit_counts": dict(exits[entry]),
        })
    selected = sorted({pc for item in routines for pc in item["member_pcs"]})
    actor_references, static_rom_operands, static_work_ram_operands = derive_operand_dependencies(metadata, selected)
    boundary = accepted_pcs()
    if not {int(pc, 16) for pc in selected} <= boundary: raise ValueError("selected PC outside accepted boundary")
    selected_edges = [{"source": h(source), "target": h(target), "kind": kind} for (source, target), kind in sorted(edges.items())]
    anim_pointers = sorted({field_value_from_overlay("anim_record", {int(k, 16): v for k, v in item["written_bytes"].items()}, 0) for item in instances if "anim_record" in item["fields"] and item["write_width_bytes"] == 4 and item["bus_event_count"] == 2})
    if not anim_pointers or anim_pointers[-1] >= program_size: raise ValueError("animation record pointer outside program image")
    field_offsets = {field: sorted({key for item in instances if field in item["fields"] for key in item["written_bytes"] if int(key, 16) in range(FIELD_LAYOUT[field]["byte_offset"], FIELD_LAYOUT[field]["byte_offset"] + FIELD_LAYOUT[field]["byte_width"])}) for field in FIELDS}
    external_callees = [{
        "callee_entry_pc": h(entry),
        "classification": "task_scheduler" if record["scheduler"] else "writer_free",
        "call_sites": [{"caller_entry_pc": h(caller), "call_site_pc": h(site)} for caller, site in record["sites"]],
        "writer_free_outside_selection": record["writer_free"],
    } for entry, record in sorted(external_records.items())]
    scheduler_exits = [item for item in external_callees if item["classification"] == "task_scheduler"]
    field_dependencies = [{
        "field": field, "instruction_space": "opcodes",
        "writer_pcs": sorted({item["instruction_pc"] for item in instances if field in item["fields"]}),
        "effective_address_registers": sorted({item["effective_address_register"] for item in instances if field in item["fields"]}),
        "source_registers": sorted({register for item in instances if field in item["fields"] for register in item["dynamic_register_binding"] if register.startswith("d")}),
    } for field in FIELDS]

    report = {
        "schema": 4, "artifact": "avsp_hit_ko_writer_set",
        "target": {"set": "avspu", "revision": "USA 940520", "class": 31, "type": 12},
        "evidence_tiers": list(IMMUTABLE_CLAIMS["evidence_tiers"]),
        "inputs": {key + "_sha256": value for key, value in identities.items()},
        "private_capture": {
            "watchpoint_log_sha256": sha(LOG), "sample_sha256": sha(SAMPLES),
            "watchpoint_event_count": sum(len(value) for value in watched.values()),
            "decoded_store_instance_count": len(instances),
        },
        "address_spaces": dict(IMMUTABLE_CLAIMS["address_spaces"]),
        "window": {"first_source_frame": FIRST, "last_source_frame": LAST, "semantic_sample_count": 1390, "execution_interval_count": 1389, "hit_semantic_sample_after": HIT, "ko_semantic_sample_after": KO, "alignment": "interval N executes from semantic sample N to N+1", "synthetic_final_epoch": False},
        "actor_field_layout": {field: dict(FIELD_LAYOUT[field]) for field in FIELDS},
        "correlations": correlations,
        "field_transitions": transitions,
        "writer_instances": instances,
        "closure": {
            "task_root": {"entry_pc": IMMUTABLE_CLAIMS["task_root_entry"], "kind": "task_return_resume", "writer_instance_count": len(instances)},
            "selected_pcs": selected,
            "selected_edges": selected_edges,
            "selected_routines": routines,
            "unresolved_computed_targets": [],
            "unattributed_dependencies": [],
        },
        "dependencies": {
            "rom_data": [
                {"purpose": "class_1f_animation_records", "address_space": "program", "derived_from": "anim_record_writer_values", "pointer_count": len(anim_pointers), "min_address": h(anim_pointers[0]), "max_address": h(anim_pointers[-1]), "pointer_sha256": phash(h(value) for value in anim_pointers)},
                {"purpose": "hit_animation_record", "address": h(sample_rows[HIT]["anim_record"]), "address_space": "program"},
                {"purpose": "ko_animation_record", "address": h(sample_rows[KO]["anim_record"]), "address_space": "program"},
                {"purpose": "selected_closure_static_rom_operands", "address_space": "program", "derived_from": "pinned_trace_operands", **static_rom_operands},
            ],
            "work_ram": [{"purpose": "class_1f_type_0c_enemy_actor", "address": h(ACTOR), "class": 31, "type": 12, "written_byte_offsets": field_offsets, "static_absolute_operands": static_work_ram_operands}],
            "actor_field_references": actor_references,
            "typed_event_exits": typed_exits,
            "task_scheduler_exits": [{"callee_entry_pc": item["callee_entry_pc"], "call_sites": item["call_sites"]} for item in scheduler_exits],
            "field_writer_dependencies": field_dependencies,
            "external_callees": external_callees,
            "outgoing_control_edges": outgoing_edges,
            "trace_collapse_dependency": collapse_dependency,
        },
        "coverage": {
            "actor_fields": list(FIELDS),
            "field_transition_counts": counts,
            "writer_instance_count": len(instances),
            "writer_instance_counts_by_field": {field: sum(1 for item in instances if field in item["fields"]) for field in FIELDS},
            "computed_target_count": sum(1 for item in selected_edges if item["kind"] == "computed_jump"),
            "event_exit_count": len(typed_exits),
            "selected_pc_count": len(selected),
            "selected_edge_count": len(selected_edges),
            "selected_routine_count": len(routines),
            "external_callee_count": len(external_callees),
            "task_scheduler_exit_count": len(scheduler_exits),
            "outgoing_control_edge_count": len(outgoing_edges),
            "trace_loop_collapse_discontinuity_count": collapse_dependency["occurrence_count"],
        },
        "exclusions": [
            {"kind": "out_of_window_routes"},
            {"kind": "other_actor_classes"},
            {"kind": "production_lifted_c"},
            {"kind": "external_writer_free_callees", "count": sum(1 for item in external_callees if item["classification"] == "writer_free")},
            {"kind": "task_scheduler_context_switch", "count": len(scheduler_exits)},
            {"kind": "actor_field_reference_direction", "reason": "static_operand_references_plus_exact_write_watchpoints"},
            {"kind": "mame_trace_repeat_collapse", "occurrence_count": collapse_dependency["occurrence_count"], "unique_pair_count": collapse_dependency["unique_pair_count"], "occurrence_sha256": collapse_dependency["occurrence_sha256"]},
        ],
        "forbidden_content_present": False,
    }
    refresh_report_bindings(report, boundary)
    validate_committed(report)
    return report


def integrity(report):
    return {
        "semantic_sha256": jhash({key: report["correlations"][key]["semantic_changes"] for key in ("hit", "ko")}),
        "routine_sha256": jhash(report["closure"]["selected_routines"]),
        "edge_sha256": jhash(report["closure"]["selected_edges"]),
        "field_transition_sha256": jhash(report["field_transitions"]),
        "writer_instance_sha256": jhash(report["writer_instances"]),
        "dependency_sha256": jhash(report["dependencies"]),
        "exclusion_sha256": jhash(report["exclusions"]),
    }


def binding(report, boundary):
    return {
        "accepted_boundary_pc_count": len(boundary),
        "selected_pc_sha256": phash(report["closure"]["selected_pcs"]),
        "selected_edge_sha256": jhash(report["closure"]["selected_edges"]),
        "selected_routine_sha256": jhash(report["closure"]["selected_routines"]),
        "field_transition_sha256": report["integrity"]["field_transition_sha256"],
        "writer_instance_sha256": report["integrity"]["writer_instance_sha256"],
        "dependency_sha256": report["integrity"]["dependency_sha256"],
        "exclusion_sha256": report["integrity"]["exclusion_sha256"],
    }


def refresh_report_bindings(report, boundary=None):
    if boundary is None: boundary = accepted_pcs()
    report["integrity"] = integrity(report)
    report["accepted_boundary_binding"] = binding(report, boundary)
    return report


def walk(value):
    if isinstance(value, dict):
        for key, item in value.items(): yield str(key).lower(); yield from walk(item)
    elif isinstance(value, list):
        for item in value: yield from walk(item)


def exact_keys(value, keys, path):
    if not isinstance(value, dict): raise ValueError("object required at " + path)
    unknown = set(value) - set(keys)
    if unknown:
        label = "unknown top-level key" if not path else "unknown key at " + path
        raise ValueError(label + ": " + sorted(unknown)[0])
    missing = set(keys) - set(value)
    if missing: raise ValueError("missing required key at " + path + ": " + sorted(missing)[0])


def exact_hash(value, path):
    if not isinstance(value, str) or not HEX64.fullmatch(value): raise ValueError("SHA-256 format at " + path)


def exact_pc(value, path):
    if not isinstance(value, str) or not HEX6.fullmatch(value): raise ValueError("PC/address format at " + path)


def exact_int(value, path):
    if not isinstance(value, int) or isinstance(value, bool): raise ValueError("integer required at " + path)


def register_bindings(value, path):
    if not isinstance(value, dict) or not set(value) <= {"d0", "d1", "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"}:
        raise ValueError("register binding schema at " + path)
    for register, address in value.items():
        if not isinstance(register, str) or not isinstance(address, str) or not (HEX6.fullmatch(address) or HEX8.fullmatch(address)):
            raise ValueError("register binding format at " + path)


def caller_site(item, path):
    exact_keys(item, {"caller_entry_pc", "call_site_pc"}, path)
    exact_pc(item["caller_entry_pc"], path + ".caller_entry_pc")
    exact_pc(item["call_site_pc"], path + ".call_site_pc")


def writer_instance_schema(item, path):
    keys = {"index", "interval_start_frame", "sequence_in_interval", "instruction_pc", "watchpoint_reported_pc", "destination", "write_width_bytes", "bus_event_count", "fields", "written_bytes", "effective_address_register", "effective_address_displacement", "dynamic_register_binding", "owner_entry_pc", "owner_entered_by_call", "owner_exit"}
    exact_keys(item, keys, path)
    for name in ("index", "interval_start_frame", "sequence_in_interval", "write_width_bytes", "bus_event_count", "effective_address_displacement"):
        exact_int(item[name], path + "." + name)
    for name in ("instruction_pc", "watchpoint_reported_pc", "destination", "owner_entry_pc"):
        exact_pc(item[name], path + "." + name)
    if not isinstance(item["fields"], list) or not item["fields"] or any(field not in FIELDS for field in item["fields"]): raise ValueError("writer instance field at " + path)
    if item["fields"] != sorted(set(item["fields"])): raise ValueError("writer instance field order at " + path)
    if item["write_width_bytes"] not in (1, 2, 4) or item["bus_event_count"] not in (1, 2): raise ValueError("writer instance width at " + path)
    if not isinstance(item["written_bytes"], dict) or not item["written_bytes"]: raise ValueError("writer instance bytes at " + path)
    for key, value in item["written_bytes"].items():
        if not isinstance(key, str) or not HEX2.fullmatch(key): raise ValueError("written byte offset format at " + path)
        exact_int(value, path + ".written_bytes")
        if not 0 <= value <= 0xFF: raise ValueError("written byte range at " + path)
    if item["effective_address_register"] not in {f"a{i}" for i in range(8)}: raise ValueError("effective-address register at " + path)
    register_bindings(item["dynamic_register_binding"], path + ".dynamic_register_binding")
    if item["owner_entered_by_call"] is not True: raise ValueError("writer owner is not call-rooted at " + path)
    if item["owner_exit"] not in {"return", "context_switch"}: raise ValueError("owner exit kind at " + path)


def validate_report_structure(report):
    top = {"schema", "artifact", "target", "evidence_tiers", "inputs", "private_capture", "address_spaces", "window", "actor_field_layout", "correlations", "field_transitions", "writer_instances", "closure", "dependencies", "coverage", "exclusions", "forbidden_content_present", "integrity", "accepted_boundary_binding"}
    exact_keys(report, top, "")
    exact_keys(report["target"], {"set", "revision", "class", "type"}, "target")
    exact_keys(report["inputs"], {key + "_sha256" for key in EXPECTED}, "inputs")
    exact_keys(report["private_capture"], set(IMMUTABLE_CLAIMS["private_capture"]), "private_capture")
    exact_keys(report["address_spaces"], set(IMMUTABLE_CLAIMS["address_spaces"]), "address_spaces")
    exact_keys(report["window"], {"first_source_frame", "last_source_frame", "semantic_sample_count", "execution_interval_count", "hit_semantic_sample_after", "ko_semantic_sample_after", "alignment", "synthetic_final_epoch"}, "window")
    exact_keys(report["actor_field_layout"], set(FIELDS), "actor_field_layout")
    for field in FIELDS:
        layout = report["actor_field_layout"][field]
        exact_keys(layout, {"byte_offset", "byte_width", "signed"}, "actor_field_layout." + field)
        exact_int(layout["byte_offset"], "actor_field_layout." + field)
        exact_int(layout["byte_width"], "actor_field_layout." + field)
        if not isinstance(layout["signed"], bool): raise ValueError("field layout at actor_field_layout." + field)
    exact_keys(report["correlations"], {"hit", "ko"}, "correlations")
    for name, allowed_fields in (("hit", {"action", "anim_record", "anim_timer"}), ("ko", {"state", "sub_state", "anim_record", "anim_timer"})):
        correlation = report["correlations"][name]
        exact_keys(correlation, {"semantic_changes", "anim_writer_instance_index", "closes_gap_external_repoint_ownership"}, "correlations." + name)
        if not isinstance(correlation["semantic_changes"], list): raise ValueError("correlation list schema at " + name)
        exact_int(correlation["anim_writer_instance_index"], "correlations." + name + ".anim_writer_instance_index")
        for change in correlation["semantic_changes"]:
            exact_keys(change, {"field", "before", "after"}, "correlations." + name + ".semantic_changes")
            if change["field"] not in allowed_fields: raise ValueError("semantic field at correlations." + name)
            exact_int(change["before"], "correlations." + name + ".before")
            exact_int(change["after"], "correlations." + name + ".after")
    exact_keys(report["field_transitions"], set(FIELDS), "field_transitions")
    for field in FIELDS:
        for index, transition in enumerate(report["field_transitions"][field]):
            path = "field_transitions." + field + "[" + str(index) + "]"
            exact_keys(transition, {"field", "interval_start_frame", "semantic_sample_after", "before_value", "after_value", "writer_instance_indices", "surviving_writer_pcs"}, path)
            if transition["field"] != field: raise ValueError("transition schema at " + field)
            for name in ("interval_start_frame", "semantic_sample_after", "before_value", "after_value"): exact_int(transition[name], path + "." + name)
            if not isinstance(transition["writer_instance_indices"], list) or not transition["writer_instance_indices"]: raise ValueError(field + " transition writer binding")
            for value in transition["writer_instance_indices"]: exact_int(value, path + ".writer_instance_indices")
            if not isinstance(transition["surviving_writer_pcs"], list) or not transition["surviving_writer_pcs"]: raise ValueError(field + " transition writer binding")
            for value in transition["surviving_writer_pcs"]: exact_pc(value, path + ".surviving_writer_pcs")
    if not isinstance(report["writer_instances"], list) or not report["writer_instances"]: raise ValueError("writer instance list")
    for index, item in enumerate(report["writer_instances"]):
        writer_instance_schema(item, "writer_instances[" + str(index) + "]")
    closure = report["closure"]
    exact_keys(closure, {"task_root", "selected_pcs", "selected_edges", "selected_routines", "unresolved_computed_targets", "unattributed_dependencies"}, "closure")
    exact_keys(closure["task_root"], {"entry_pc", "kind", "writer_instance_count"}, "closure.task_root")
    exact_pc(closure["task_root"]["entry_pc"], "closure.task_root.entry_pc")
    exact_int(closure["task_root"]["writer_instance_count"], "closure.task_root.writer_instance_count")
    for index, pc in enumerate(closure["selected_pcs"]): exact_pc(pc, "closure.selected_pcs[" + str(index) + "]")
    for name in ("unresolved_computed_targets", "unattributed_dependencies"):
        for index, pc in enumerate(closure[name]): exact_pc(pc, "closure." + name + "[" + str(index) + "]")
    for edge in closure["selected_edges"]:
        exact_keys(edge, {"source", "target", "kind"}, "closure.selected_edges")
        exact_pc(edge["source"], "closure.selected_edges.source"); exact_pc(edge["target"], "closure.selected_edges.target")
        if edge["kind"] not in EDGE_KINDS: raise ValueError("edge kind")
    routine_keys = {"entry_pc", "closure_role", "member_pc_count", "member_pc_sha256", "member_pcs", "observed_callers", "observed_selected_callees", "actor_field_references", "actor_field_writes", "exit_counts"}
    for routine_item in closure["selected_routines"]:
        exact_keys(routine_item, routine_keys, "closure.selected_routines")
        exact_pc(routine_item["entry_pc"], "routine.entry_pc"); exact_int(routine_item["member_pc_count"], "routine.member_pc_count"); exact_hash(routine_item["member_pc_sha256"], "routine.member_pc_sha256")
        if routine_item["closure_role"] not in ROLES: raise ValueError("routine role")
        for pc in routine_item["member_pcs"]: exact_pc(pc, "routine.member_pcs")
        for caller in routine_item["observed_callers"]: caller_site(caller, "routine.observed_callers")
        for pc in routine_item["observed_selected_callees"]: exact_pc(pc, "routine.observed_selected_callees")
        if any(field not in KNOWN_ACTOR_OFFSETS.values() for field in routine_item["actor_field_references"]): raise ValueError("routine actor-field attribution")
        if any(field not in FIELDS for field in routine_item["actor_field_writes"]): raise ValueError("routine actor-field attribution")
        exact_keys(routine_item["exit_counts"], set(EXIT_KEYS), "routine.exit_counts")
        for value in routine_item["exit_counts"].values(): exact_int(value, "routine.exit_counts")
    dependencies = report["dependencies"]
    exact_keys(dependencies, {"rom_data", "work_ram", "actor_field_references", "typed_event_exits", "task_scheduler_exits", "field_writer_dependencies", "external_callees", "outgoing_control_edges", "trace_collapse_dependency"}, "dependencies")
    rom = dependencies["rom_data"]
    if len(rom) != 4: raise ValueError("ROM dependency schema")
    exact_keys(rom[0], {"purpose", "address_space", "derived_from", "pointer_count", "min_address", "max_address", "pointer_sha256"}, "dependencies.rom_data[0]")
    if rom[0]["purpose"] != "class_1f_animation_records" or rom[0]["address_space"] != "program" or rom[0]["derived_from"] != "anim_record_writer_values": raise ValueError("ROM dependency schema")
    exact_int(rom[0]["pointer_count"], "rom_data.pointer_count"); exact_pc(rom[0]["min_address"], "rom_data.min_address"); exact_pc(rom[0]["max_address"], "rom_data.max_address"); exact_hash(rom[0]["pointer_sha256"], "rom_data.pointer_sha256")
    for item, purpose in ((rom[1], "hit_animation_record"), (rom[2], "ko_animation_record")):
        exact_keys(item, {"purpose", "address", "address_space"}, "dependencies.rom_data")
        if item["purpose"] != purpose or item["address_space"] != "program": raise ValueError("ROM dependency schema")
        exact_pc(item["address"], "dependencies.rom_data.address")
    exact_keys(rom[3], {"purpose", "address_space", "derived_from", "address_count", "address_sha256", "min_address", "max_address", "execution_count"}, "dependencies.rom_data[3]")
    if rom[3]["purpose"] != "selected_closure_static_rom_operands" or rom[3]["address_space"] != "program" or rom[3]["derived_from"] != "pinned_trace_operands": raise ValueError("ROM dependency schema")
    for name in ("address_count", "execution_count"): exact_int(rom[3][name], "dependencies.rom_data[3]." + name)
    exact_hash(rom[3]["address_sha256"], "dependencies.rom_data[3].address_sha256")
    for name in ("min_address", "max_address"):
        if rom[3][name] is not None: exact_pc(rom[3][name], "dependencies.rom_data[3]." + name)
    if len(dependencies["work_ram"]) != 1: raise ValueError("work-RAM dependency schema")
    actor = dependencies["work_ram"][0]
    exact_keys(actor, {"purpose", "address", "class", "type", "written_byte_offsets", "static_absolute_operands"}, "dependencies.work_ram")
    if actor["purpose"] != "class_1f_type_0c_enemy_actor" or actor["address"] != h(ACTOR) or actor["class"] != 31 or actor["type"] != 12: raise ValueError("work-RAM dependency schema")
    exact_keys(actor["written_byte_offsets"], set(FIELDS), "work_ram.written_byte_offsets")
    for field in FIELDS:
        offsets = actor["written_byte_offsets"][field]
        if not isinstance(offsets, list) or not offsets: raise ValueError("work-RAM dependency schema")
        for offset in offsets:
            if not isinstance(offset, str) or not HEX2.fullmatch(offset): raise ValueError("work-RAM dependency schema")
    exact_keys(actor["static_absolute_operands"], {"address_count", "address_sha256", "min_address", "max_address", "execution_count"}, "dependencies.work_ram.static_absolute_operands")
    for name in ("address_count", "execution_count"): exact_int(actor["static_absolute_operands"][name], "dependencies.work_ram.static_absolute_operands." + name)
    exact_hash(actor["static_absolute_operands"]["address_sha256"], "dependencies.work_ram.static_absolute_operands.address_sha256")
    for name in ("min_address", "max_address"):
        if actor["static_absolute_operands"][name] is not None: exact_pc(actor["static_absolute_operands"][name], "dependencies.work_ram.static_absolute_operands." + name)
    for field, item in dependencies["actor_field_references"].items():
        if field not in KNOWN_ACTOR_OFFSETS.values(): raise ValueError("actor-field reference schema")
        exact_keys(item, {"reference_pcs", "reference_pc_sha256", "execution_count"}, "dependencies.actor_field_references")
        for pc in item["reference_pcs"]: exact_pc(pc, "dependencies.actor_field_references.reference_pcs")
        exact_hash(item["reference_pc_sha256"], "dependencies.actor_field_references.reference_pc_sha256")
        exact_int(item["execution_count"], "dependencies.actor_field_references.execution_count")
    for item in dependencies["typed_event_exits"]:
        exact_keys(item, {"event", "interval_start_frame", "writer_pc"}, "dependencies.typed_event_exits")
        exact_int(item["interval_start_frame"], "dependencies.typed_event_exits.interval_start_frame"); exact_pc(item["writer_pc"], "dependencies.typed_event_exits.writer_pc")
    for item in dependencies["task_scheduler_exits"]:
        exact_keys(item, {"callee_entry_pc", "call_sites"}, "dependencies.task_scheduler_exits")
        exact_pc(item["callee_entry_pc"], "dependencies.task_scheduler_exits.callee_entry_pc")
        for site in item["call_sites"]: caller_site(site, "dependencies.task_scheduler_exits.call_sites")
    for item in dependencies["field_writer_dependencies"]:
        exact_keys(item, {"field", "instruction_space", "writer_pcs", "effective_address_registers", "source_registers"}, "dependencies.field_writer_dependencies")
        if item["field"] not in FIELDS or item["instruction_space"] != "opcodes": raise ValueError("field writer dependency schema")
        for pc in item["writer_pcs"]: exact_pc(pc, "field writer dependency PC")
        if any(register not in {f"a{i}" for i in range(8)} for register in item["effective_address_registers"]): raise ValueError("field writer dependency schema")
        if any(register not in {"d0", "d1"} for register in item["source_registers"]): raise ValueError("field writer dependency schema")
    for item in dependencies["external_callees"]:
        exact_keys(item, {"callee_entry_pc", "classification", "call_sites", "writer_free_outside_selection"}, "dependencies.external_callees")
        exact_pc(item["callee_entry_pc"], "dependencies.external_callees.callee_entry_pc")
        if item["classification"] not in {"writer_free", "task_scheduler"}: raise ValueError("external callee schema")
        if item["writer_free_outside_selection"] is not True: raise ValueError("external callee attribution")
        for site in item["call_sites"]: caller_site(site, "dependencies.external_callees.call_sites")
    for item in dependencies["outgoing_control_edges"]:
        exact_keys(item, {"source", "target", "kind", "occurrence_count"}, "dependencies.outgoing_control_edges")
        exact_pc(item["source"], "dependencies.outgoing_control_edges.source"); exact_pc(item["target"], "dependencies.outgoing_control_edges.target")
        if item["kind"] not in EDGE_KINDS: raise ValueError("outgoing edge kind")
        exact_int(item["occurrence_count"], "dependencies.outgoing_control_edges.occurrence_count")
    collapse = dependencies["trace_collapse_dependency"]
    exact_keys(collapse, {"kind", "occurrence_count", "unique_pair_count", "occurrence_sha256"}, "dependencies.trace_collapse_dependency")
    if collapse["kind"] != "mame_trace_repeat_collapse": raise ValueError("trace collapse dependency")
    exact_int(collapse["occurrence_count"], "dependencies.trace_collapse_dependency.occurrence_count"); exact_int(collapse["unique_pair_count"], "dependencies.trace_collapse_dependency.unique_pair_count"); exact_hash(collapse["occurrence_sha256"], "dependencies.trace_collapse_dependency.occurrence_sha256")
    coverage = report["coverage"]
    exact_keys(coverage, {"actor_fields", "field_transition_counts", "writer_instance_count", "writer_instance_counts_by_field", "computed_target_count", "event_exit_count", "selected_pc_count", "selected_edge_count", "selected_routine_count", "external_callee_count", "task_scheduler_exit_count", "outgoing_control_edge_count", "trace_loop_collapse_discontinuity_count"}, "coverage")
    if coverage["actor_fields"] != list(FIELDS): raise ValueError("actor-field enumeration")
    exact_keys(coverage["field_transition_counts"], set(FIELDS), "coverage.field_transition_counts")
    exact_keys(coverage["writer_instance_counts_by_field"], set(FIELDS), "coverage.writer_instance_counts_by_field")
    for mapping in (coverage["field_transition_counts"], coverage["writer_instance_counts_by_field"]):
        for value in mapping.values(): exact_int(value, "coverage count")
    for name in ("writer_instance_count", "computed_target_count", "event_exit_count", "selected_pc_count", "selected_edge_count", "selected_routine_count", "external_callee_count", "task_scheduler_exit_count", "outgoing_control_edge_count", "trace_loop_collapse_discontinuity_count"):
        exact_int(coverage[name], "coverage." + name)
    if not isinstance(report["exclusions"], list): raise ValueError("exclusions")
    for item in report["exclusions"]:
        if not isinstance(item, dict) or "kind" not in item: raise ValueError("exclusions")
    exact_keys(report["integrity"], {"semantic_sha256", "routine_sha256", "edge_sha256", "field_transition_sha256", "writer_instance_sha256", "dependency_sha256", "exclusion_sha256"}, "integrity")
    exact_keys(report["accepted_boundary_binding"], {"accepted_boundary_pc_count", "selected_pc_sha256", "selected_edge_sha256", "selected_routine_sha256", "field_transition_sha256", "writer_instance_sha256", "dependency_sha256", "exclusion_sha256"}, "accepted_boundary_binding")
    for mapping, path in ((report["integrity"], "integrity"), (report["accepted_boundary_binding"], "accepted_boundary_binding")):
        for name, value in mapping.items():
            if name != "accepted_boundary_pc_count": exact_hash(value, path + "." + name)
            else: exact_int(value, path + "." + name)
    if report["forbidden_content_present"] is not False: raise ValueError("forbidden content")


def validate_committed(report):
    validate_report_structure(report)
    if report.get("schema") != 4 or report.get("artifact") != "avsp_hit_ko_writer_set": raise ValueError("schema")
    if report.get("target") != {"set": "avspu", "revision": "USA 940520", "class": 31, "type": 12}: raise ValueError("target")
    if report.get("inputs") != {key + "_sha256": value for key, value in EXPECTED.items()}: raise ValueError("settled inputs")
    if tuple(report.get("evidence_tiers", ())) != IMMUTABLE_CLAIMS["evidence_tiers"]: raise ValueError("evidence tiers")
    if report.get("private_capture") != IMMUTABLE_CLAIMS["private_capture"]: raise ValueError("private capture provenance")
    if report.get("address_spaces") != IMMUTABLE_CLAIMS["address_spaces"]: raise ValueError("address-space attribution")
    window = {"first_source_frame": FIRST, "last_source_frame": LAST, "semantic_sample_count": 1390, "execution_interval_count": 1389, "hit_semantic_sample_after": HIT, "ko_semantic_sample_after": KO, "alignment": "interval N executes from semantic sample N to N+1", "synthetic_final_epoch": False}
    if report.get("window") != window: raise ValueError("exact accepted anchors")
    if report.get("actor_field_layout") != {field: dict(FIELD_LAYOUT[field]) for field in FIELDS}: raise ValueError("field layout")

    instances = report["writer_instances"]
    for index, item in enumerate(instances):
        if item["index"] != index: raise ValueError("writer instance index binding")
        if not FIRST <= item["interval_start_frame"] < LAST: raise ValueError("writer instance interval")
        layouts = [FIELD_LAYOUT[field] for field in item["fields"]]
        spans = {offset for layout in layouts for offset in range(layout["byte_offset"], layout["byte_offset"] + layout["byte_width"])}
        if not {int(key, 16) for key in item["written_bytes"]} & spans: raise ValueError("writer instance binding")
    ordering = [(item["interval_start_frame"], item["sequence_in_interval"]) for item in instances]
    if ordering != sorted(ordering) or len(set(ordering)) != len(ordering): raise ValueError("writer instance ordering")

    transitions = report["field_transitions"]
    coverage = report["coverage"]
    if tuple(coverage["actor_fields"]) != FIELDS or coverage["field_transition_counts"] != EXPECTED_COUNTS: raise ValueError("seven-field coverage")
    for field in FIELDS:
        if len(transitions[field]) != EXPECTED_COUNTS[field]: raise ValueError(field + " transition coverage")
        layout = FIELD_LAYOUT[field]
        span = range(layout["byte_offset"], layout["byte_offset"] + layout["byte_width"])
        for transition in transitions[field]:
            if transition["semantic_sample_after"] != transition["interval_start_frame"] + 1: raise ValueError(field + " transition alignment")
            overlay, last_writer = {}, {}
            previous = -1
            for index in transition["writer_instance_indices"]:
                if not 0 <= index < len(instances): raise ValueError(field + " transition writer binding")
                item = instances[index]
                if item["interval_start_frame"] != transition["interval_start_frame"]: raise ValueError(field + " transition writer binding")
                if item["sequence_in_interval"] <= previous: raise ValueError(field + " transition writer binding")
                previous = item["sequence_in_interval"]
                touched = {int(key, 16): value for key, value in item["written_bytes"].items() if int(key, 16) in span}
                if not touched: raise ValueError(field + " transition writer binding")
                overlay.update(touched)
                for offset in touched: last_writer[offset] = item["instruction_pc"]
            if field_value_from_overlay(field, overlay, transition["before_value"]) != transition["after_value"]: raise ValueError(field + " transition reconstruction")
            if transition["surviving_writer_pcs"] != sorted(set(last_writer.values())): raise ValueError(field + " transition writer binding")
    if coverage["writer_instance_count"] != len(instances) or coverage["writer_instance_counts_by_field"] != {field: sum(1 for item in instances if field in item["fields"]) for field in FIELDS}: raise ValueError("writer instance counts")

    closure = report["closure"]
    selected, routines, edges = closure["selected_pcs"], closure["selected_routines"], closure["selected_edges"]
    boundary = accepted_pcs()
    if not selected or len(selected) != len(set(selected)) or not {int(pc, 16) for pc in selected} <= boundary: raise ValueError("accepted boundary PC membership")
    entries, union = [item["entry_pc"] for item in routines], set()
    if not entries or len(entries) != len(set(entries)) or entries != sorted(entries): raise ValueError("unique routine entries")
    by_entry = {item["entry_pc"]: item for item in routines}
    for item in routines:
        members = item["member_pcs"]
        if item["member_pc_count"] != len(members) or item["member_pc_sha256"] != phash(members) or members != sorted(members) or len(members) != len(set(members)) or not set(members) <= set(selected): raise ValueError("routine membership")
        union.update(members)
    if union != set(selected): raise ValueError("routine/selected-PC union")
    if not edges or any(edge["source"] not in selected or edge["target"] not in selected or edge["kind"] not in EDGE_KINDS for edge in edges): raise ValueError("edge shape")
    if len({(edge["source"], edge["target"], edge["kind"]) for edge in edges}) != len(edges): raise ValueError("edge uniqueness")
    call_edges = {(edge["source"], edge["target"]) for edge in edges if edge["kind"] == "call"}
    for item in routines:
        for caller in item["observed_callers"]:
            if caller["caller_entry_pc"] not in by_entry or caller["call_site_pc"] not in by_entry[caller["caller_entry_pc"]]["member_pcs"]: raise ValueError("caller relationship")
            if (caller["call_site_pc"], item["entry_pc"]) not in call_edges: raise ValueError("caller relationship")
        for callee in item["observed_selected_callees"]:
            if callee not in by_entry: raise ValueError("callee relationship")
            if not any(source in item["member_pcs"] and target == callee for source, target in call_edges): raise ValueError("callee relationship")
        if item["closure_role"] != "task_root" and not item["observed_callers"]: raise ValueError("caller relationship")
    task_root = closure["task_root"]
    if task_root != {"entry_pc": IMMUTABLE_CLAIMS["task_root_entry"], "kind": "task_return_resume", "writer_instance_count": len(instances)}: raise ValueError("task root binding")
    if task_root["entry_pc"] not in by_entry or by_entry[task_root["entry_pc"]]["closure_role"] != "task_root": raise ValueError("task root binding")

    owner_writes = {}
    for item in instances:
        owner = by_entry.get(item["owner_entry_pc"])
        if owner is None or owner["closure_role"] != "writer_owner": raise ValueError("writer owner selection")
        if item["instruction_pc"] not in owner["member_pcs"]: raise ValueError("writer owner membership")
        owner_writes.setdefault(item["owner_entry_pc"], set()).update(item["fields"])
    for item in routines:
        expected_writes = sorted(owner_writes.get(item["entry_pc"], set()))
        if item["actor_field_writes"] != expected_writes: raise ValueError("routine actor-field attribution")
        if item["closure_role"] == "writer_owner" and not expected_writes: raise ValueError("writer owner selection")

    if closure["unresolved_computed_targets"] or closure["unattributed_dependencies"]: raise ValueError("unresolved dependency")
    if (coverage["selected_pc_count"], coverage["selected_edge_count"], coverage["selected_routine_count"]) != (len(selected), len(edges), len(routines)): raise ValueError("selected closure counts")
    dependencies = report["dependencies"]
    if coverage["computed_target_count"] != sum(edge["kind"] == "computed_jump" for edge in edges) or coverage["event_exit_count"] != len(dependencies["typed_event_exits"]): raise ValueError("derived counts")
    if coverage["external_callee_count"] != len(dependencies["external_callees"]) or coverage["task_scheduler_exit_count"] != len(dependencies["task_scheduler_exits"]): raise ValueError("derived counts")
    if coverage["outgoing_control_edge_count"] != len(dependencies["outgoing_control_edges"]): raise ValueError("derived counts")

    reference_fields_by_pc = {}
    for field, attribution in dependencies["actor_field_references"].items():
        if attribution["reference_pc_sha256"] != phash(attribution["reference_pcs"]) or attribution["execution_count"] <= 0: raise ValueError("actor-field dependency derivation")
        for pc in attribution["reference_pcs"]:
            if pc not in selected: raise ValueError("actor-field dependency derivation")
            reference_fields_by_pc.setdefault(pc, set()).add(field)
    if not set(FIELDS) <= set(dependencies["actor_field_references"]): raise ValueError("actor-field dependency derivation")
    for item in routines:
        expected_references = sorted({field for pc in item["member_pcs"] for field in reference_fields_by_pc.get(pc, set())})
        if item["actor_field_references"] != expected_references: raise ValueError("routine actor-field attribution")

    for name, after in (("hit", HIT), ("ko", KO)):
        correlation = report["correlations"][name]
        changes = {item["field"]: (item["before"], item["after"]) for item in correlation["semantic_changes"]}
        if "anim_record" not in changes or not correlation["closes_gap_external_repoint_ownership"]: raise ValueError(name + " semantic binding")
        index = correlation["anim_writer_instance_index"]
        if not 0 <= index < len(instances): raise ValueError(name + " semantic binding")
        item = instances[index]
        overlay = {int(key, 16): value for key, value in item["written_bytes"].items()}
        if (item["interval_start_frame"], item["instruction_pc"], item["write_width_bytes"], item["bus_event_count"]) != (after - 1, IMMUTABLE_CLAIMS["anim_anchor_pc"], 4, 2) or "anim_record" not in item["fields"]: raise ValueError(name + " animation writer")
        if field_value_from_overlay("anim_record", overlay, 0) != changes["anim_record"][1]: raise ValueError(name + " animation writer")
        for change in correlation["semantic_changes"]:
            field_transitions = [transition for transition in transitions[change["field"]] if transition["interval_start_frame"] == after - 1]
            if len(field_transitions) != 1 or (field_transitions[0]["before_value"], field_transitions[0]["after_value"]) != (change["before"], change["after"]): raise ValueError(name + " semantic binding")

    typed_exits = dependencies["typed_event_exits"]
    expected_typed_exits = [{"event": event, "interval_start_frame": interval, "writer_pc": pc} for event, interval, pc in IMMUTABLE_CLAIMS["typed_event_exits"]]
    if typed_exits != expected_typed_exits: raise ValueError("HIT typed event exit" if len(typed_exits) < 1 or typed_exits[0] != expected_typed_exits[0] else "KO typed event exit")
    for exit_item, field in zip(typed_exits, ("action", "sub_state")):
        matching = [transition for transition in transitions[field] if transition["interval_start_frame"] == exit_item["interval_start_frame"]]
        label = "HIT typed event exit" if exit_item["event"] == "enemy_hit_event" else "KO typed event exit"
        if len(matching) != 1: raise ValueError(label)
        first = instances[matching[0]["writer_instance_indices"][0]]
        if first["instruction_pc"] != exit_item["writer_pc"]: raise ValueError(label)

    field_dependencies = {item["field"]: item for item in dependencies["field_writer_dependencies"]}
    if list(field_dependencies) != list(FIELDS): raise ValueError("field writer dependency closure")
    for field in FIELDS:
        dependency = field_dependencies[field]
        expected_pcs = sorted({item["instruction_pc"] for item in instances if field in item["fields"]})
        expected_registers = sorted({item["effective_address_register"] for item in instances if field in item["fields"]})
        expected_sources = sorted({register for item in instances if field in item["fields"] for register in item["dynamic_register_binding"] if register.startswith("d")})
        if dependency["writer_pcs"] != expected_pcs or dependency["effective_address_registers"] != expected_registers or dependency["source_registers"] != expected_sources: raise ValueError("field writer dependency closure")
        if not expected_pcs: raise ValueError("field writer dependency closure")

    actor = dependencies["work_ram"][0]
    for field in FIELDS:
        layout = FIELD_LAYOUT[field]
        span = range(layout["byte_offset"], layout["byte_offset"] + layout["byte_width"])
        expected_offsets = sorted({key for item in instances if field in item["fields"] for key in item["written_bytes"] if int(key, 16) in span})
        if actor["written_byte_offsets"][field] != expected_offsets: raise ValueError("work-RAM dependency derivation")
    for item in instances:
        base = int(item["destination"], 16)
        if not ACTOR <= base < ACTOR + 0x42: raise ValueError("work-RAM dependency derivation")

    rom = dependencies["rom_data"]
    anim_pointers = sorted({field_value_from_overlay("anim_record", {int(key, 16): value for key, value in item["written_bytes"].items()}, 0) for item in instances if "anim_record" in item["fields"] and item["write_width_bytes"] == 4 and item["bus_event_count"] == 2})
    if rom[0]["pointer_count"] != len(anim_pointers) or rom[0]["min_address"] != h(anim_pointers[0]) or rom[0]["max_address"] != h(anim_pointers[-1]) or rom[0]["pointer_sha256"] != phash(h(value) for value in anim_pointers): raise ValueError("program dependencies")
    hit_after = {change["field"]: change["after"] for change in report["correlations"]["hit"]["semantic_changes"]}
    ko_after = {change["field"]: change["after"] for change in report["correlations"]["ko"]["semantic_changes"]}
    if rom[1]["address"] != h(hit_after["anim_record"]) or rom[2]["address"] != h(ko_after["anim_record"]): raise ValueError("program dependencies")
    if not int(rom[0]["min_address"], 16) <= int(rom[1]["address"], 16) <= int(rom[0]["max_address"], 16): raise ValueError("program dependencies")
    if not int(rom[0]["min_address"], 16) <= int(rom[2]["address"], 16) <= int(rom[0]["max_address"], 16): raise ValueError("program dependencies")
    static_rom = rom[3]
    if static_rom["address_count"]:
        if static_rom["execution_count"] <= 0 or not 0 <= int(static_rom["min_address"], 16) <= int(static_rom["max_address"], 16) <= 0x1FFFFF: raise ValueError("program dependencies")
    elif static_rom["execution_count"] or static_rom["min_address"] is not None or static_rom["max_address"] is not None:
        raise ValueError("program dependencies")
    static_work = actor["static_absolute_operands"]
    if static_work["address_count"]:
        if static_work["execution_count"] <= 0 or not 0xFF0000 <= int(static_work["min_address"], 16) <= int(static_work["max_address"], 16) <= 0xFFFFFF: raise ValueError("work-RAM dependency derivation")
    elif static_work["execution_count"] or static_work["min_address"] is not None or static_work["max_address"] is not None:
        raise ValueError("work-RAM dependency derivation")

    external_by_entry = {item["callee_entry_pc"]: item for item in dependencies["external_callees"]}
    if len(external_by_entry) != len(dependencies["external_callees"]): raise ValueError("external callee attribution")
    for item in dependencies["external_callees"]:
        if item["callee_entry_pc"] in by_entry: raise ValueError("external callee attribution")
        if not item["call_sites"]: raise ValueError("external callee attribution")
        for site in item["call_sites"]:
            if site["caller_entry_pc"] not in by_entry or site["call_site_pc"] not in by_entry[site["caller_entry_pc"]]["member_pcs"]: raise ValueError("external callee attribution")
    scheduler_entries = [item["callee_entry_pc"] for item in dependencies["external_callees"] if item["classification"] == "task_scheduler"]
    if [item["callee_entry_pc"] for item in dependencies["task_scheduler_exits"]] != scheduler_entries: raise ValueError("task scheduler exit binding")
    for scheduled, item in zip(dependencies["task_scheduler_exits"], (entry for entry in dependencies["external_callees"] if entry["classification"] == "task_scheduler")):
        if scheduled["call_sites"] != item["call_sites"]: raise ValueError("task scheduler exit binding")
    outgoing = dependencies["outgoing_control_edges"]
    if outgoing != sorted(outgoing, key=lambda item: (item["source"], item["target"], item["kind"])) or len({(item["source"], item["target"], item["kind"]) for item in outgoing}) != len(outgoing): raise ValueError("outgoing edge derivation")
    if any(item["source"] not in selected or item["target"] in selected or item["occurrence_count"] <= 0 for item in outgoing): raise ValueError("outgoing edge derivation")
    expected_external_calls = {(site["call_site_pc"], item["callee_entry_pc"]) for item in dependencies["external_callees"] for site in item["call_sites"]}
    actual_external_calls = {(item["source"], item["target"]) for item in outgoing if item["kind"] == "call"}
    if actual_external_calls != expected_external_calls: raise ValueError("outgoing edge derivation")
    if any(item["kind"] not in {"call", "return", "rte"} for item in outgoing): raise ValueError("unresolved outgoing edge")
    collapse = dependencies["trace_collapse_dependency"]
    if collapse["occurrence_count"] != coverage["trace_loop_collapse_discontinuity_count"] or collapse["unique_pair_count"] <= 0 or collapse["occurrence_count"] < collapse["unique_pair_count"]: raise ValueError("trace collapse dependency")

    kinds = [item.get("kind") for item in report["exclusions"]]
    if kinds != ["out_of_window_routes", "other_actor_classes", "production_lifted_c", "external_writer_free_callees", "task_scheduler_context_switch", "actor_field_reference_direction", "mame_trace_repeat_collapse"]: raise ValueError("exclusions")
    if report["exclusions"][3].get("count") != sum(1 for item in dependencies["external_callees"] if item["classification"] == "writer_free"): raise ValueError("exclusions")
    if report["exclusions"][4].get("count") != len(dependencies["task_scheduler_exits"]): raise ValueError("exclusions")
    if report["exclusions"][5].get("reason") != "static_operand_references_plus_exact_write_watchpoints": raise ValueError("exclusions")
    if report["exclusions"][6] != collapse: raise ValueError("exclusions")
    if any(item.get("kind") == "in_window_target_writer" for item in report["exclusions"]): raise ValueError("exclusions")

    if report["integrity"] != integrity(report): raise ValueError("integrity")
    expected_binding = binding(report, boundary)
    if report["accepted_boundary_binding"] != expected_binding: raise ValueError("accepted-boundary binding")
    if IMMUTABLE_BINDING is not None and expected_binding != IMMUTABLE_BINDING: raise ValueError("immutable PC/edge/routine binding")
    if IMMUTABLE_INTEGRITY is not None and report["integrity"] != IMMUTABLE_INTEGRITY: raise ValueError("immutable integrity binding")
    if report.get("forbidden_content_present") is not False or FORBIDDEN & set(walk(report)): raise ValueError("forbidden content")


def require_invariant_rejection(report, name, invariant, mutate):
    candidate = copy.deepcopy(report)
    mutate(candidate)
    refresh_report_bindings(candidate)
    try:
        validate_committed(candidate)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as error:
        if invariant in str(error): return
        raise AssertionError(name + " rejected by " + repr(str(error)) + ", not " + repr(invariant))
    raise AssertionError("production validator accepted committed-artifact control: " + name)


def self_test():
    report = build()
    mutations = [
        ("missing HIT anim writer index", "hit animation writer", lambda x: x["correlations"]["hit"].__setitem__("anim_writer_instance_index", 0)),
        ("missing KO anim writer index", "ko animation writer", lambda x: x["correlations"]["ko"].__setitem__("anim_writer_instance_index", 0)),
        ("missing health transition", "health transition coverage", lambda x: x["field_transitions"]["health"].pop()),
        ("missing anim_timer transition", "anim_timer transition coverage", lambda x: x["field_transitions"]["anim_timer"].pop()),
        ("dropped transition writer instance", "state transition writer binding", lambda x: x["field_transitions"]["state"][0].__setitem__("writer_instance_indices", [])),
        ("changed health after", "health transition reconstruction", lambda x: x["field_transitions"]["health"][0].__setitem__("after_value", -999)),
        ("corrupted written byte", "hit_value transition reconstruction", lambda x: x["writer_instances"][x["field_transitions"]["hit_value"][0]["writer_instance_indices"][0]]["written_bytes"].__setitem__("0x2c", 0xAB)),
        ("writer instance interval shift", "transition writer binding", lambda x: x["writer_instances"][0].__setitem__("interval_start_frame", x["writer_instances"][0]["interval_start_frame"] + 1)),
        ("owner not call-rooted", "writer owner is not call-rooted", lambda x: x["writer_instances"][0].__setitem__("owner_entered_by_call", False)),
        ("owner exit relabel", "owner exit kind", lambda x: x["writer_instances"][0].__setitem__("owner_exit", "interval_end")),
        ("successor PC drift", "immutable PC/edge/routine binding", lambda x: x["writer_instances"][0].__setitem__("watchpoint_reported_pc", "0xfffffe")),
        ("HIT bus-event count drift", "hit animation writer", lambda x: x["writer_instances"][x["correlations"]["hit"]["anim_writer_instance_index"]].__setitem__("bus_event_count", 1)),
        ("live register binding removed", "immutable PC/edge/routine binding", lambda x: x["writer_instances"][0].__setitem__("dynamic_register_binding", {})),
        ("owner outside routines", "writer owner selection", lambda x: x["writer_instances"][0].__setitem__("owner_entry_pc", "0x0080b4")),
        ("HIT anchor", "exact accepted anchors", lambda x: x["window"].__setitem__("hit_semantic_sample_after", HIT + 1)),
        ("field layout corruption", "field layout", lambda x: x["actor_field_layout"]["state"].__setitem__("byte_width", 2)),
        ("selected PC outside boundary", "accepted boundary PC membership", lambda x: x["closure"]["selected_pcs"].append("0xfffffe")),
        ("selected edge removal", "selected closure counts", lambda x: x["closure"]["selected_edges"].pop()),
        ("unresolved computed target", "unresolved dependency", lambda x: x["closure"]["unresolved_computed_targets"].append("0x000002")),
        ("routine member count", "routine membership", lambda x: x["closure"]["selected_routines"][2].__setitem__("member_pc_count", 1)),
        ("task root corruption", "task root binding", lambda x: x["closure"]["task_root"].__setitem__("entry_pc", "0x0080b6")),
        ("event count", "derived counts", lambda x: x["coverage"].__setitem__("event_exit_count", 999)),
        ("ROM dependency relabel", "ROM dependency schema", lambda x: x["dependencies"]["rom_data"][1].__setitem__("address_space", "opcodes")),
        ("ROM dependency purpose drift", "ROM dependency schema", lambda x: x["dependencies"]["rom_data"][1].__setitem__("purpose", "asserted_hit_record")),
        ("actor reference removal", "actor-field dependency derivation", lambda x: x["dependencies"]["actor_field_references"].pop("state")),
        ("outgoing edge removal", "derived counts", lambda x: x["dependencies"]["outgoing_control_edges"].pop()),
        ("outgoing edge retarget", "outgoing edge derivation", lambda x: x["dependencies"]["outgoing_control_edges"][0].__setitem__("target", x["closure"]["selected_pcs"][0])),
        ("trace collapse exclusion drift", "exclusions", lambda x: x["dependencies"]["trace_collapse_dependency"].__setitem__("occurrence_sha256", "0" * 64)),
        ("external callee flag", "external callee attribution", lambda x: x["dependencies"]["external_callees"][0].__setitem__("writer_free_outside_selection", False)),
        ("field dependency drop", "field writer dependency closure", lambda x: x["dependencies"]["field_writer_dependencies"][0]["writer_pcs"].pop()),
        ("in-window exclusion", "exclusions", lambda x: x["exclusions"].append({"kind": "in_window_target_writer"})),
        ("raw key", "unknown top-level key", lambda x: x.__setitem__("trace_text", "forbidden")),
    ]
    for name, invariant, mutate in mutations:
        require_invariant_rejection(report, name, invariant, mutate)
    print("HIT/KO writer-set self-test and invariant-specific committed-artifact controls passed")


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
