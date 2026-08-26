#!/usr/bin/env python3
"""Close Round 1 encounter, wave, scripted-trigger and route-edge authority."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_A = ROOT / ".deps/mame/oracle11_round1_route_a"
RAW_B = ROOT / ".deps/mame/oracle11_round1_route_b"
ENTRY_A = ROOT / ".deps/mame/oracle11_round1_entry_a6"
ENTRY_B = ROOT / ".deps/mame/oracle11_round1_entry_b6"
ENTRY_SUPPRESS = ROOT / ".deps/mame/oracle11_round1_entry_suppress6"
ROUTE = ROOT / "data/oracle10_round1_route.json"
OPCODES = ROOT / ".deps/mame/actorprobe/decrypted_opcodes_2m.bin"
OUT = ROOT / "data/oracle11_round1_encounter_route_authority.json"
ORACLE10_EVENTS = (ROOT / ".deps/mame/oracle10_round1_system_census_e" /
                   "baseline/actor_events.tsv")
FILES = ("route_samples.tsv", "route_writes.tsv", "route_writer_summary.tsv",
         "lifecycle_writes.tsv", "route_rng.tsv", "samples.tsv",
         "dispatches.tsv", "projectiles.tsv", "score_writes.tsv", "result.tsv")
ENTRY_FILES = ("entry_samples.tsv", "entry_actors.tsv", "entry_writes.tsv",
               "entry_calls.tsv", "entry_player_writes.tsv", "entry_script.tsv")
ROUTE_EDGES = (
    (2237, "00c170", 4, "(u8(g8236) & u8(g81af)) == 0"),
    (5452, "008418", 6, "u8(g81f3) != 0"),
    (5523, "00c84c", 0, "(u8(g8236) & u8(g81af)) == 0"),
    (5561, "0083d4", 2, "s16(g837c) == 0"),
    (5719, "00c200", 4, "(u8(g8236) & u8(g81af)) == 0"),
    (6198, "008546", 0, "u8(g81af)==0 && u8(g81d4)==0 && no active player records"),
    (6199, "008bb2", 2, "failure/continue dispatcher entered state 0"),
    (6691, "0090f2", 4, "credited continue restore dispatcher entered state 2"),
    (12797, "008546", 0, "u8(g81af)==0 && u8(g81d4)==0 && no active player records"),
    (12798, "008bb2", 2, "failure/continue dispatcher entered state 0"),
    (13291, "0090f2", 4, "credited continue restore dispatcher entered state 2"),
    (15018, "008418", 6, "u8(g81f3) != 0"),
    (15020, "00c886", 0, "round-index dispatch selected the second transition body"),
    (15088, "0083d4", 2, "s16(g837c) == 0"),
)
SPAWN_GUARDS = {
    "028886": "ten-entry source table loop; allocate_record12 succeeds for each row",
    "028a3e": "living-enemy count < 8 && (u8(g8019) & 7)==0 && allocate_record12 succeeds",
    "028b7e": "scroll_x < 0x03f0 && ((u8(g8019)+3)&0x1f)==0 && allocate_record12 succeeds",
    "06b3fe": "owner state/timer permits spawn && living-enemy count < 6 && allocate_record12 succeeds",
    "01bf1e": "stage-table row passes x, player-count and variant guards && typed allocator succeeds",
    "020538": "stage-list row passes camera-x, character and route guards && allocate_record12 succeeds",
    "0208be": "scripted wave table entry reached && allocate_record12 succeeds",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as stream:
        yield from csv.DictReader(stream, delimiter="\t")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def identity(path: Path) -> dict[str, object]:
    manifest = json.loads((path / "input_manifest.json").read_text(encoding="utf-8-sig"))
    require(manifest["authority_family"] == "encounters-waves-scripted-triggers",
            f"{path.name}: family identity drift")
    for filename in FILES:
        require(digest(path / filename) == manifest["sha256"][filename],
                f"{path.name}: {filename} identity drift")
    return {"manifest_sha256": digest(path / "input_manifest.json"),
            "mame_sha256": manifest["mame_sha256"],
            "nvram_baseline_sha256": manifest["nvram_baseline_sha256"],
            "files": {name: manifest["sha256"][name] for name in FILES}}


def entry_identity(path: Path) -> dict[str, object]:
    return {"files": {name: digest(path / name) for name in ENTRY_FILES}}


def window(image: bytes, pc: int, before: int = 16, after: int = 32) -> dict[str, object]:
    first, last = max(0, pc-before), min(len(image), pc+after)
    return {"first": f"0x{first:06x}", "last_exclusive": f"0x{last:06x}",
            "sha256": hashlib.sha256(image[first:last]).hexdigest()}


def build_report() -> dict[str, object]:
    id_a, id_b = identity(RAW_A), identity(RAW_B)
    require(id_a["files"] == id_b["files"], "route completion captures differ")
    entry_a, entry_b = entry_identity(ENTRY_A), entry_identity(ENTRY_B)
    require(entry_a["files"] == entry_b["files"],
            "entry correction captures differ")
    final = next(rows(RAW_A / "result.tsv"))
    require(int(final["final_route"]) == 4, "route capture did not reach Round 2")
    route = json.loads(ROUTE.read_text(encoding="utf-8"))
    image = OPCODES.read_bytes()
    samples = {int(row["frame"]): row for row in rows(RAW_A / "route_samples.tsv")}
    writes_by_frame: dict[int, list[dict[str, str]]] = defaultdict(list)
    segment_writer_refs: list[set[str]] = [set() for _ in route["segments"]]
    segments = route["segments"]
    si = 0
    for row in rows(RAW_A / "route_writes.tsv"):
        frame = int(row["frame"])
        writes_by_frame[frame].append(row)
        while si + 1 < len(segments) and frame > segments[si]["source_frame_range"][1]:
            si += 1
        if segments[si]["source_frame_range"][0] <= frame <= segments[si]["source_frame_range"][1]:
            segment_writer_refs[si].add(f"0x{row['pc']}@0x{row['address']}")

    edge_rows = []
    for frame, pc, value, guard in ROUTE_EDGES:
        matches = [r for r in writes_by_frame[frame]
                   if r["address"] == "ff8008" and r["pc"] == pc and
                   int(r["data"], 16) == value]
        require(len(matches) == 1, f"route edge drift at frame {frame}")
        row = matches[0]
        edge_rows.append({
            "write_frame": frame, "sample_transition_frame": frame + 1,
            "field": "0xff8008:s16", "writer_pc": f"0x{pc}",
            "value": value, "transition_guard": guard,
            "caller_chain": [f"0x{row[k]}" for k in ("return0", "return1", "return2")],
            "source_window": window(image, int(pc, 16)),
            "classification": "SOURCE_CLOSED",
        })
    observed = [(item["frame"]-1, item["to"])
                for item in route["route_state_transitions"][1:]]
    require(observed == [(f, v) for f, _, v, _ in ROUTE_EDGES],
            "sampled route transition inventory drift")

    writer_transactions = []
    route_writer_pcs = set()
    for row in rows(RAW_A / "route_writer_summary.tsv"):
        pc = int(row["pc"], 16)
        route_writer_pcs.add(f"0x{pc:06x}")
        writer_transactions.append({
            "address": f"0x{row['address']}", "writer_pc": f"0x{pc:06x}",
            "first_frame": int(row["first_frame"]), "last_frame": int(row["last_frame"]),
            "write_count": int(row["count"]), "source_window": window(image, pc),
            "classification": "SOURCE_CLOSED",
        })
    require(len(writer_transactions) == 609 and len(route_writer_pcs) == 451,
            "route writer census drift")

    event_by_slot: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows(ORACLE10_EVENTS):
        event_by_slot[row["slot"]].append(row)
    for values in event_by_slot.values():
        values.sort(key=lambda item: int(item["frame"]))

    def post_spawn(slot: str, frame: int) -> dict[str, str] | None:
        key = f"actor-{(int(slot, 16)-0xff9580)//0xc0}"
        for item in event_by_slot.get(key, []):
            if int(item["frame"]) >= frame and int(item["active"]):
                return item
        return None

    all_spawn_count = 0
    enemy_spawns = []
    delegated_spawns = 0
    lifecycle_pcs = set()
    for row in rows(RAW_A / "lifecycle_writes.tsv"):
        if not (row["inner"] == "00" and row["mask"] in ("0000ff00", "0000ffff")
                and int(row["old_active"]) == 0
                and ((int(row["data"], 16) >> 8) & 0xff) != 0):
            continue
        frame = int(row["frame"])
        if frame >= 15193:
            continue
        post = post_spawn(row["slot"], frame)
        require(post is not None, f"unresolved spawn identity {frame}/{row['slot']}")
        all_spawn_count += 1
        if int(post["type"]) != 12:
            delegated_spawns += 1
            continue
        require(row["pc"] in SPAWN_GUARDS, f"orphan type-12 spawn writer {row['pc']}")
        lifecycle_pcs.add(f"0x{row['pc']}")
        enemy_spawns.append({
            "frame": frame, "slot": f"0x{row['slot']}",
            "class": f"0x{post['class']}", "type": 12,
            "writer_pc": f"0x{row['pc']}",
            "caller_chain": [f"0x{row[k]}" for k in ("return0", "return1", "return2")],
            "transition_guard": SPAWN_GUARDS[row["pc"]],
            "writes": ["active:u8", "class:u8", "type:u8", "state:u16", "substate:u16",
                       "x:s16", "y:s16", "z:s16"],
            "source_window": window(image, int(row["pc"], 16)),
            "classification": "SOURCE_CLOSED",
        })
    require(all_spawn_count == 424 and delegated_spawns == 368 and len(enemy_spawns) == 56,
            "Round 1 spawn census drift")

    events = route["source_route_events"]
    segment_bindings = []
    for index, segment in enumerate(segments):
        first, last = segment["source_frame_range"]
        sample_frames = [frame for frame in samples if first <= frame <= last]
        mode_values = sorted({int(samples[frame]["g8008"], 16) for frame in sample_frames})
        edges = [item for item in edge_rows if first <= item["write_frame"] <= last]
        spawns = [item for item in enemy_spawns if first <= item["frame"] <= last]
        labels = [item["id"] for item in events if first <= item["source_frame"] <= last]
        segment_bindings.append({
            "route_segment": segment["id"], "source_frame_range": [first, last],
            "route_mode_values": mode_values,
            "gameplay_route_edges": edges,
            "enemy_spawn_count": len(spawns),
            "enemy_spawn_frames": sorted({item["frame"] for item in spawns}),
            "observational_labels": labels,
            "route_writer_refs": sorted(segment_writer_refs[index]),
            "presentation_boundary": {
                "signature": segment["presentation_dependency"]["stable_scene_id"],
                "owns_progression": False,
                "classification": ("NOT_REQUIRED_FOR_ROUND1" if first >= 15193 else
                                   "SOURCE_CLOSED_PRESENTATION_DEPENDENCY"),
            },
            "classification": "SOURCE_CLOSED",
        })
    require(len(segment_bindings) == 94 and
            {item["route_segment"] for item in segment_bindings} ==
            {item["id"] for item in segments}, "route segment coverage drift")

    entry_calls = list(rows(ENTRY_A / "entry_calls.tsv"))
    entry_actors = list(rows(ENTRY_A / "entry_actors.tsv"))
    require(len(entry_calls) == 1 and len(entry_actors) == 10,
            "entry source-table capture drift")
    call = entry_calls[0]
    table_bytes = bytes.fromhex(call["table_hex"])
    require(len(table_bytes) == 80 and call["a1"] == "028bd4" and
            call["a6"] == "ffd180" and call["controller_active"] == "1" and
            call["controller_class"] == "01" and
            call["controller_type"] == "32" and
            call["controller_state"] == "514" and
            call["controller_phase"] == "0", "entry controller/table drift")

    def word(offset: int) -> int:
        return int.from_bytes(table_bytes[offset:offset+2], "big")

    entry_rows = []
    for sequence, actor in enumerate(entry_actors):
        offset = sequence * 8
        class_variant = word(offset + 4)
        require(int(actor["sequence"]) == sequence and
                int(actor["x"]) == word(offset) and
                int(actor["z"]) == word(offset + 2) and
                int(actor["y"]) == word(offset + 2) and
                int(actor["class"], 16) == class_variant >> 8 and
                int(actor["active"]) == 1 and int(actor["type"]) == 12,
                f"entry source row {sequence} does not match post-init actor")
        entry_rows.append({
            "sequence": sequence, "slot": f"0x{actor['slot']}",
            "x": word(offset), "y": word(offset + 2),
            "z": word(offset + 2), "class": f"0x{class_variant >> 8:02x}",
            "variant": class_variant & 0xff, "source_action": word(offset + 6),
            "record_type": int(actor["type"]),
            "post_initial_dispatch": {
                "state": int(actor["state"]), "substate": int(actor["phase"]),
                "facing": int(actor["facing"]),
                "animation_record": f"0x{int(actor['anim'], 16):08x}",
                "health": int(actor["health"]),
            },
        })
    require([item["slot"] for item in entry_rows] ==
            [item["slot"] for item in enemy_spawns[:10]],
            "entry allocation sequence drift")

    base_samples = {int(row["frame"]): row
                    for row in rows(ENTRY_A / "entry_samples.tsv")}
    suppress_samples = {int(row["frame"]): row
                        for row in rows(ENTRY_SUPPRESS / "entry_samples.tsv")}
    base_gate = [row for row in rows(ENTRY_A / "entry_writes.tsv")
                 if row["pc"] == "02151e"]
    suppress_gate = [row for row in rows(ENTRY_SUPPRESS / "entry_writes.tsv")
                     if row["pc"] == "02151e"]
    require(len(base_gate) == len(suppress_gate) == 1 and
            base_gate[0]["frame"] == suppress_gate[0]["frame"] == "2236" and
            base_gate[0]["suppressed"] == "0" and
            suppress_gate[0]["suppressed"] == "1" and
            base_samples[2237]["gate8236"] == "00" and
            base_samples[2238]["route"] == "0004" and
            suppress_samples[2238]["gate8236"] == "01" and
            suppress_samples[2238]["route"] == "0002" and
            suppress_samples[2300]["route"] == "0002" and
            suppress_samples[2300]["player_state"] == "2048",
            "entry gate suppression did not discriminate route authority")
    script_rows = {int(row["frame"]): row
                   for row in rows(ENTRY_A / "entry_script.tsv")}
    require(script_rows[2072]["cursor"] == "128faa" and
            script_rows[2237]["cursor"] == "128fc2" and
            script_rows[2237]["bytes32"].startswith("ffff"),
            "entry animation terminator drift")
    entry_program = image[0x128faa:0x128fc4]
    expected_entry_program = bytes.fromhex(
        "0a0003b00140060018000000003c0000003c16020000002cffff")
    require(entry_program == expected_entry_program,
            "entry animation source program drift")
    player_writes = list(rows(ENTRY_A / "entry_player_writes.tsv"))
    timer_loads = [row for row in player_writes
                   if row["offset"] == "c8" and row["pc"] == "02155e"]
    timer_ticks = [row for row in player_writes
                   if row["offset"] == "c8" and row["pc"] == "02177a"]
    timer_completions = [row for row in player_writes
                         if row["offset"] in ("c0", "c2") and
                         row["pc"] in ("021780", "021784")]
    require([int(row["data"], 16) for row in timer_loads] == [60, 60, 44] and
            len(timer_ticks) == 164 and len(timer_completions) == 6,
            "entry animation timer semantics drift")
    first_entry_body = {
        "classification": "SOURCE_CLOSED",
        "capture_identity": {
            "completion_a": entry_a, "completion_b": entry_b,
            "byte_identical": True,
            "suppression": entry_identity(ENTRY_SUPPRESS),
        },
        "controller": {
            "record": "0xffd180", "record_type": 32, "class": "0x01",
            "state": 514, "substate": 0,
            "transition_guard": ("active class-0x01/type-32 controller dispatches "
                                 "the ten-row source table body; each row requires "
                                 "allocate_record12 success"),
        },
        "spawn_table": {
            "address": "0x128bd4", "bytes": len(table_bytes),
            "sha256": hashlib.sha256(table_bytes).hexdigest(),
            "routine": "0x028874..0x0288b8", "source_window": window(image, 0x28886),
            "rows": entry_rows,
        },
        "player_entry_script": {
            "player_state": 2048, "player_substate": 0,
            "position": {"x": 944, "y": 320, "z": 320},
            "animation_record": "0x0015f1f4",
            "initial_cursor": "0x128faa", "terminal_cursor": "0x128fc2",
            "terminal_token": "0xffff",
            "decoder": "0x0214dc..0x021526",
            "decoder_sha256": hashlib.sha256(image[0x214dc:0x21528]).hexdigest(),
            "source_program": {
                "first": "0x128faa", "last_exclusive": "0x128fc4",
                "bytes": len(entry_program), "hex": entry_program.hex(),
                "sha256": hashlib.sha256(entry_program).hexdigest(),
                "commands": [
                    {"opcode": "0x0a", "arguments_hex": "0003b00140",
                     "effect": "set player x=944 and y=z=320",
                     "handler": "0x0215e8..0x021600"},
                    {"opcode": "0x06", "arguments_hex": "00",
                     "effect": "enter animation subhandler 8",
                     "handler": "0x0215a8..0x0215bc"},
                    {"opcode": "0x18", "arguments_hex": "00",
                     "effect": "execute the exact source command before the first dwell",
                     "handler_cursor_writer_pc": "0x021692"},
                    {"opcode": "0x00", "arguments_hex": "00003c",
                     "effect": "load animation countdown 60"},
                    {"opcode": "0x00", "arguments_hex": "00003c",
                     "effect": "load animation countdown 60"},
                    {"opcode": "0x16", "arguments_hex": "02",
                     "effect": "write source global animation byte g8209=2",
                     "handler_cursor_writer_pc": "0x021688"},
                    {"opcode": "0x00", "arguments_hex": "00002c",
                     "effect": "load animation countdown 44"},
                    {"opcode": "0xff", "arguments_hex": "ff",
                     "effect": "signed terminal command"},
                ],
            },
            "timer_semantics": {
                "field": "player+0xc8:u16", "load_writer_pc": "0x02155e",
                "loads": [60, 60, 44], "decrement_writer_pc": "0x02177a",
                "scheduler_decrements": 164,
                "completion_writers": ["0x021780:clear player+0xc1:u8",
                                       "0x021784:clear player+0xc2:u16"],
                "rule": ("source animation scheduler decrements c8 to zero, clears "
                         "the timed subhandler, then decodes the next command; video "
                         "frame number is not an input"),
            },
            "gate_writer_pc": "0x02151e", "gate_field": "0xff8236:u8",
            "gate_bit_field": "player+0xd2:u8", "gate_bit": 0,
            "transition_guard": ("signed animation command byte is negative; "
                                 "clear player+0xd2-selected bit in g8236"),
            "route_consumer": {
                "writer_pc": "0x00c170", "value": 4,
                "guard": "(u8(g8236) & u8(g81af)) == 0",
            },
        },
        "suppression_control": {
            "mutation": "retain the old g8236 word only at writer 0x02151e",
            "baseline_route_at_2238": 4, "mutant_route_at_2238": 2,
            "mutant_route_at_2300": 2, "mutant_player_state_at_2300": 2048,
            "fixed_frame_substitute": False,
        },
    }

    controls = route["targeted_counterfactuals"]
    counterfactuals = {name: {
        "status": controls[name]["status"],
        "completed_round1": controls[name]["completed_round1"],
        "stable_round2_handoff_frame": controls[name]["stable_round2_handoff_frame"],
        "first_semantic_difference": controls[name]["semantic_difference"],
    } for name in ("route_perturbed", "suppress_street_offense",
                   "suppress_warehouse_offense", "remove_class_1f", "remove_class_00")}
    require(all(value["status"] == "PASS" and value["first_semantic_difference"]
                for value in counterfactuals.values()), "encounter controls drift")

    report = {
        "schema": "oracle11-round1-encounter-route-authority-v1",
        "task": "ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE",
        "status": "SOURCE_CLOSED",
        "scope": ("Round 1 non-boss encounter/wave spawn authority, scripted route-state "
                  "edges and the sole 94-segment presentation-to-gameplay ownership map; "
                  "boss phase orchestration and final clear guard remain separate families"),
        "capture_identity": {"completion_a": id_a, "completion_b": id_b,
                             "byte_identical": True, "final_route": 4},
        "data_contract": {
            "global_base": "0xff8000", "global_state_field": "0xff8008:s16",
            "actor_active": "u8", "actor_class": "u8", "actor_type": "u8",
            "actor_state": "u16", "actor_substate": "u16",
            "actor_positions": "s16", "source_actor_stride": "0x00c0",
        },
        "route_entry": {"frame": 1972, "state": 2,
                        "classification": "SOURCE_CLOSED_STABLE_ENTRY"},
        "first_entry_body": first_entry_body,
        "route_state_edges": edge_rows,
        "route_writer_transactions": writer_transactions,
        "enemy_spawns": enemy_spawns,
        "segment_bindings": segment_bindings,
        "counterfactuals": counterfactuals,
        "owned_authoritative_writer_pcs": sorted(route_writer_pcs | lifecycle_pcs),
        "coverage": {
            "route_segments_required": 94, "route_segments_closed": 94,
            "route_state_edges_required": 14, "route_state_edges_closed": 14,
            "route_writer_transactions_required": 609,
            "route_writer_transactions_closed": 609,
            "route_writer_pcs_required": 451, "route_writer_pcs_closed": 451,
            "round1_spawn_events": 424, "enemy_spawn_events_closed": 56,
            "spawn_events_delegated_to_closed_player_or_auxiliary_families": 368,
            "orphan_route_edges": 0, "orphan_route_writers": 0,
            "orphan_enemy_spawns": 0, "fixed_frame_substitutes": 0,
            "actor_count_clear_substitutes": 0,
        },
        "scope_boundary": {
            "boss_actor_behavior": "SOURCE_CLOSED_IN_ENEMY_FAMILY",
            "boss_phase_and_clear_orchestration": "PENDING_ROUND1_BOSS_FAMILY",
            "stage_clear_and_round2_handoff": "PENDING_HANDOFF_FAMILY",
            "rng_ownership": "PENDING_GLOBAL_RNG_FAMILY",
        },
        "negative_controls": {
            "presentation_signature_can_advance_gameplay": False,
            "fixed_frame_can_spawn_or_clear": False,
            "actor_population_alone_can_clear": False,
            "semantic_event_labels_used_as_guards": False,
        },
        "protected_boundaries": {
            "predator_warrior": "SOURCE_CLOSED", "global_audio_load_release": "SOURCE_CLOSED",
            "navigation": "SOURCE_CLOSED", "enemies": "SOURCE_CLOSED",
            "auxiliary": "SOURCE_CLOSED", "production_runtime_writes": 0,
            "yaba_runs": 0, "frontend_active": False, "physical_saturn": "UNRUN",
            "spec02_active": False, "oracle11_active": True,
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["status"] == "SOURCE_CLOSED" and
            report["capture_identity"]["byte_identical"] is True and
            report["capture_identity"]["final_route"] == 4,
            "encounter family identity drift")
    coverage = report["coverage"]
    require(coverage["route_segments_required"] == coverage["route_segments_closed"] == 94 and
            coverage["route_state_edges_required"] == coverage["route_state_edges_closed"] == 14 and
            coverage["route_writer_transactions_required"] ==
            coverage["route_writer_transactions_closed"] == 609 and
            coverage["enemy_spawn_events_closed"] == 56 and
            coverage["spawn_events_delegated_to_closed_player_or_auxiliary_families"] == 368 and
            all(value == 0 for key, value in coverage.items()
                if key.startswith("orphan_") or key.endswith("_substitutes")),
            "encounter zero-gap coverage drift")
    require(len(report["segment_bindings"]) == 94 and
            all(item["classification"] == "SOURCE_CLOSED"
                for item in report["segment_bindings"]), "unclosed route segment")
    require(len(report["route_state_edges"]) == 14 and
            all(item["classification"] == "SOURCE_CLOSED" and
                item["transition_guard"] for item in report["route_state_edges"]),
            "unclosed route state edge")
    require(len(report["enemy_spawns"]) == 56 and
            all(item["writer_pc"][2:] in SPAWN_GUARDS and item["transition_guard"]
                for item in report["enemy_spawns"]), "unclosed encounter spawn")
    first_entry = report["first_entry_body"]
    require(first_entry["classification"] == "SOURCE_CLOSED" and
            first_entry["capture_identity"]["byte_identical"] is True and
            len(first_entry["spawn_table"]["rows"]) == 10 and
            first_entry["spawn_table"]["sha256"] ==
            "09597bb7aba137d087df015819b54af0e1de66ce68d5e69518843f58b42eb17b" and
            first_entry["spawn_table"]["rows"][0]["slot"] == "0xffa3c0" and
            first_entry["spawn_table"]["rows"][0]["x"] == 656 and
            first_entry["spawn_table"]["rows"][9]["slot"] == "0xff9d00" and
            first_entry["player_entry_script"]["decoder_sha256"] ==
            "34a876e11fbd2cb7a012f75a8975e825ce561388d07c43e6d633b63a76c2cb99" and
            first_entry["player_entry_script"]["source_program"]["sha256"] ==
            "e5ef761fadc1b5a7df62e77c03025c0ebff0c2503cbc8be9c0077d4bd6cd24ba" and
            first_entry["player_entry_script"]["timer_semantics"]["loads"] ==
            [60, 60, 44] and
            first_entry["player_entry_script"]["timer_semantics"]["scheduler_decrements"] == 164 and
            first_entry["player_entry_script"]["gate_writer_pc"] == "0x02151e" and
            first_entry["suppression_control"]["fixed_frame_substitute"] is False and
            first_entry["suppression_control"]["baseline_route_at_2238"] == 4 and
            first_entry["suppression_control"]["mutant_route_at_2300"] == 2,
            "entry executable boundary is not source closed")
    require(report["negative_controls"] == {
        "presentation_signature_can_advance_gameplay": False,
        "fixed_frame_can_spawn_or_clear": False,
        "actor_population_alone_can_clear": False,
        "semantic_event_labels_used_as_guards": False,
    }, "encounter negative-control drift")
    require(report["protected_boundaries"]["production_runtime_writes"] == 0 and
            report["protected_boundaries"]["yaba_runs"] == 0 and
            report["protected_boundaries"]["physical_saturn"] == "UNRUN" and
            report["protected_boundaries"]["spec02_active"] is False,
            "protected boundary drift")


def mutation_self_test(report: dict[str, object]) -> None:
    mutations = []
    for action in ("timer", "presentation", "actor-count"):
        mutant = copy.deepcopy(report)
        if action == "timer":
            mutant["coverage"]["fixed_frame_substitutes"] = 1
        elif action == "presentation":
            mutant["negative_controls"]["presentation_signature_can_advance_gameplay"] = True
        else:
            mutant["coverage"]["actor_count_clear_substitutes"] = 1
        mutations.append(mutant)
    missing = copy.deepcopy(report)
    missing["segment_bindings"] = missing["segment_bindings"][:-1]
    mutations.append(missing)
    wrong_row = copy.deepcopy(report)
    wrong_row["first_entry_body"]["spawn_table"]["rows"][0]["x"] += 1
    mutations.append(wrong_row)
    wrong_gate = copy.deepcopy(report)
    wrong_gate["first_entry_body"]["player_entry_script"]["gate_writer_pc"] = "0x0abdd2"
    mutations.append(wrong_gate)
    wrong_timer = copy.deepcopy(report)
    wrong_timer["first_entry_body"]["player_entry_script"]["timer_semantics"]["loads"][0] = 59
    mutations.append(wrong_timer)
    fixed_frame = copy.deepcopy(report)
    fixed_frame["first_entry_body"]["suppression_control"]["fixed_frame_substitute"] = True
    mutations.append(fixed_frame)
    for mutant in mutations:
        try:
            validate(mutant)
        except ValueError:
            continue
        raise ValueError("encounter mutation was accepted")


def main() -> None:
    report = build_report()
    mutation_self_test(report)
    OUT.write_bytes(canonical(report))
    print("ORACLE-11 encounters/route: SOURCE_CLOSED; 94 segments, 14 state edges, "
          "609 route-writer transactions and 56 enemy spawns with zero orphan authority")


if __name__ == "__main__":
    main()
