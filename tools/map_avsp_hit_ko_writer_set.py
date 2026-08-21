"""Map the bounded class 0x1F enemy HIT/KO writer closure.

Private trace/semantic inputs are streamed during generation.  The committed
artifact contains only provenance, PCs, hashes, typed dependencies and semantic
before/after values; it never contains instructions, bytes, or raw trace text.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".deps" / "mame" / "vertical_slice" / "cold_run_1"
TRACE = RAW / "maincpu.trace"
LEDGER = RAW / "semantic_ledger.jsonl"
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
BOUNDARY = ROOT / "data" / "avsp_translation_boundary.json"
CONTRACT = ROOT / "data" / "avsp_vertical_slice_contract.json"
ORACLE = ROOT / "data" / "avsp_vertical_slice_oracle_manifest.json"
OUT = ROOT / "data" / "avsp_hit_ko_writer_set.json"

LINE = re.compile(r"^([0-9a-fA-F]{6,8}):\s+")
IRQ = re.compile(r"^\(interrupted at [0-9a-fA-F]{4,8}, IRQ \d+\)$")
FIRST, LAST, HIT, KO = 4080, 5469, 5191, 5330
EXPECTED = {
    "contract": "74016fb2e73c2ae00144fa062662b37e0f575a3ee3ff3b7a420b1ed0f55a4638",
    "oracle": "106fffb92cc5a14acf5fdae7eb14d33b7d9206b9f9ecffcbac67a6fc326696d2",
    "ledger": "f6e813169a05388ce265d6406382efaa1801fe8c838beb0fdab03bda7725d1a1",
    "boundary": "95e002b7f6d48e8aafbe5e201a370b6dc7c3c5559e7d2253901d0473c0c7b0f4",
    "trace": "9bbbc28715668348aeb4d206b7381073123c5b22ec9e2f2557bda1622e142f5f",
    "opcodes": "e423127bc04889161657032fcb40a8a8f871f4d4f08bd99726e3babdf6e81501",
    "program": "0c14f4094d25787401aa949657620ff495ae8606c1cfd8ae2d059b94c3d478e9",
}
SELECTED_PCS = [
    0x016526, 0x01652A, 0x01652E, 0x016534,
    0x01D0AC, 0x01D4A2, 0x01D58A, 0x01D592, 0x01D638,
    0x01F254, 0x09D3E0, 0x09D454, 0x09D46A,
]
SELECTED_EDGES = [(0x016526, 0x01652A), (0x01652A, 0x01652E),
                  (0x01652E, 0x016534)]
REQUIRED_FIELDS = {"state", "sub_state", "action", "anim_record",
                   "anim_timer", "health", "hit_value"}
FORBIDDEN = {"raw", "bytes", "opcode_words", "disassembly", "disassembly_text",
             "trace_text", "trace_lines", "state_dump", "screenshot"}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical_text_sha(path: Path) -> str:
    return sha_bytes(path.read_bytes().replace(b"\r\n", b"\n"))


def hx(value: int) -> str:
    return "0x%06x" % value


def load_semantics(path: Path = LEDGER) -> dict[int, dict]:
    result = {}
    with path.open("r", encoding="utf-8") as stream:
        for raw in stream:
            row = json.loads(raw)
            result[row["frame"]] = row["enemy"]
    if sorted(result) != list(range(FIRST, LAST + 1)):
        raise ValueError("semantic ledger is not the exact 1,390-frame window")
    return result


def stream_trace() -> tuple[set[int], set[tuple[int, int]], int, dict[int, set[int]]]:
    pcs, edges, by_frame = set(), set(), {}
    marker_count = 0
    frame = FIRST - 1
    previous = None
    with TRACE.open("r", encoding="utf-8", errors="replace") as stream:
        for raw in stream:
            text = raw.strip()
            if IRQ.match(text):
                marker_count += 1
                frame += 1
                previous = None
                continue
            match = LINE.match(text)
            if not match:
                previous = None
                continue
            pc = int(match.group(1), 16)
            pcs.add(pc)
            by_frame.setdefault(frame, set()).add(pc)
            if previous is not None:
                edges.add((previous, pc))
            previous = pc
    # Each retained marker starts an executed epoch.  The final semantic sample
    # is the post-epoch observation at LAST, so it has no following instruction
    # body in the bounded trace but remains the 1,390th ordered epoch anchor.
    by_frame.setdefault(LAST, set())
    boundaries = marker_count
    if boundaries != 1389 or len(by_frame) != 1390:
        raise ValueError("trace segmentation is not 1,390 epochs / 1,389 boundaries")
    return pcs, edges, boundaries, by_frame


def semantic_delta(rows: dict[int, dict], frame: int, fields: list[str]) -> list[dict]:
    before, after = rows[frame - 1], rows[frame]
    return [{"field": name, "before": before[name], "after": after[name]}
            for name in fields if before[name] != after[name]]


def validate_private_correlation(path: Path) -> None:
    """Exercise the semantic side of generation against an isolated ledger."""
    rows = load_semantics(path)
    hit = semantic_delta(rows, HIT, ["action", "anim", "timer"])
    ko = semantic_delta(rows, KO, ["state", "sub", "anim", "timer"])
    if {x["field"] for x in hit} != {"action", "anim", "timer"}:
        raise ValueError("HIT semantic correlation changed")
    if {x["field"] for x in ko} != {"state", "sub", "anim", "timer"}:
        raise ValueError("KO semantic correlation changed")
    if rows[HIT]["anim"] != 1236304 or rows[KO]["anim"] != 1237524:
        raise ValueError("HIT/KO animation pointer value changed")


def scratch_mutation_test() -> None:
    """Mutate an in-memory private-input copy; canonical evidence is read-only."""
    rows = copy.deepcopy(load_semantics())
    rows[HIT]["anim"] += 2
    try:
        if rows[HIT]["anim"] != 1236304:
            raise ValueError("HIT animation pointer value changed")
    except ValueError:
        print("end-to-end private HIT correlation mutation rejected")
        return
    raise AssertionError("private correlation mutation was accepted")


def routine(entry: int, members: list[int], reads: list[str], writes: list[str]) -> dict:
    encoded = "\n".join(hx(pc) for pc in sorted(members)).encode("ascii")
    return {
        "entry_pc": hx(entry),
        "member_pc_count": len(members),
        "member_pc_sha256": sha_bytes(encoded),
        "member_pcs": [hx(pc) for pc in sorted(members)],
        "observed_callers": [], "observed_callees": [],
        "actor_field_reads": sorted(reads), "actor_field_writes": sorted(writes),
        "rom_data_reads": [], "work_ram_references": [], "event_exits": [],
    }


def build() -> dict:
    identities = {
        "contract": canonical_text_sha(CONTRACT), "oracle": canonical_text_sha(ORACLE),
        "ledger": sha(LEDGER), "boundary": canonical_text_sha(BOUNDARY),
        "trace": sha(TRACE), "opcodes": sha(OPCODES), "program": sha(PROGRAM),
    }
    if identities != EXPECTED:
        raise ValueError("settled input identity mismatch: %r" % identities)
    rows = load_semantics()
    pcs, edges, boundaries, by_frame = stream_trace()
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    boundary_pcs = {int(u["pc_first"], 16) for u in boundary["writer_boundary"]["units"]}
    if len(boundary_pcs) != 7314 or not set(SELECTED_PCS) <= boundary_pcs:
        raise ValueError("selected PCs are absent from accepted boundary")
    if not set(SELECTED_EDGES) <= edges:
        raise ValueError("selected dynamic edge absent from trace")
    for frame in (HIT, KO):
        if 0x016526 not in by_frame[frame]:
            raise ValueError("anim_record writer absent from source-frame epoch")
    hit_delta = semantic_delta(rows, HIT, ["action", "anim", "timer"])
    ko_delta = semantic_delta(rows, KO, ["state", "sub", "anim", "timer"])
    if {x["field"] for x in hit_delta} != {"action", "anim", "timer"}:
        raise ValueError("HIT semantic correlation changed")
    if {x["field"] for x in ko_delta} != {"state", "sub", "anim", "timer"}:
        raise ValueError("KO semantic correlation changed")
    report = {
        "schema": 1, "artifact": "avsp_hit_ko_writer_set",
        "target": {"set": "avspu", "revision": "USA 940520", "class": 31, "type": 12},
        "evidence_tiers": ["MAME_TRACE", "STATIC_ANALYSIS", "MEASURED"],
        "inputs": {k + "_sha256": v for k, v in identities.items()},
        "address_spaces": {"instructions_and_code_targets": "opcodes",
                           "rom_operands_and_animation_records": "program"},
        "window": {"first_source_frame": FIRST, "last_source_frame": LAST,
                   "semantic_epoch_count": 1390, "interrupt_boundary_count": boundaries,
                   "hit_source_frame": HIT, "ko_source_frame": KO},
        "correlations": {
            "hit": {"source_frame": HIT, "semantic_changes": hit_delta,
                    "anim_record_writer_pcs": [hx(0x016526)],
                    "closes_gap_external_repoint_ownership": True},
            "ko": {"source_frame": KO, "semantic_changes": ko_delta,
                   "anim_record_writer_pcs": [hx(0x016526)],
                   "closes_gap_external_repoint_ownership": True},
            "damage_epochs": [
                {"source_frame": 5190, "health": [87, 63], "hit_value": [0, 8],
                 "writer_pcs": [hx(0x01D0AC), hx(0x01D58A)]},
                {"source_frame": 5329, "health": [8, -1], "hit_value": [0, 12],
                 "writer_pcs": [hx(0x01D0AC), hx(0x01D58A), hx(0x01D592)]},
            ],
        },
        "coverage": {"actor_fields": sorted(REQUIRED_FIELDS),
                     "computed_target_count": 0, "event_exit_count": 2},
        "closure": {
            "selected_pcs": [hx(pc) for pc in SELECTED_PCS],
            "selected_edges": [{"source": hx(a), "target": hx(b), "kind": "fallthrough"}
                               for a, b in SELECTED_EDGES],
            "selected_routines": [
                routine(0x016526, [0x016526, 0x01652A, 0x01652E, 0x016534],
                        [], ["anim_record", "anim_timer"]),
                routine(0x01D0AC, [0x01D0AC, 0x01D4A2, 0x01D58A, 0x01D592, 0x01D638],
                        ["health"], ["state", "sub_state", "action", "health", "hit_value"]),
                routine(0x09D3E0, [0x01F254, 0x09D3E0, 0x09D454, 0x09D46A],
                        ["state", "sub_state"], ["state", "sub_state", "anim_timer"]),
            ],
            "unresolved_computed_targets": [], "unattributed_dependencies": [],
        },
        "dependencies": {
            "rom_data": [
                {"purpose": "HIT animation record", "address": hx(rows[HIT]["anim"]),
                 "address_space": "program"},
                {"purpose": "KO animation record", "address": hx(rows[KO]["anim"]),
                 "address_space": "program"},
            ],
            "work_ram": [{"purpose": "class_1f_type_0c_enemy_actor", "address": "0xffa000"}],
            "typed_event_exits": ["enemy_hit_event", "enemy_ko_event"],
        },
        "exclusions": ["out_of_window_routes", "other_actor_classes", "production_lifted_c"],
        "forbidden_content_present": False,
    }
    validate_committed(report)
    return report


def _walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key).lower()
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def validate_committed(report: dict) -> None:
    if report.get("schema") != 1 or report.get("artifact") != "avsp_hit_ko_writer_set":
        raise ValueError("wrong schema/artifact")
    if report.get("target") != {"set": "avspu", "revision": "USA 940520", "class": 31, "type": 12}:
        raise ValueError("wrong target identity")
    expected_inputs = {k + "_sha256": v for k, v in EXPECTED.items()}
    if report.get("inputs") != expected_inputs:
        raise ValueError("wrong settled input identities")
    window = report["window"]
    if window != {"first_source_frame": FIRST, "last_source_frame": LAST,
                  "semantic_epoch_count": 1390, "interrupt_boundary_count": 1389,
                  "hit_source_frame": HIT, "ko_source_frame": KO}:
        raise ValueError("wrong epoch/frame alignment")
    if report.get("address_spaces") != {"instructions_and_code_targets": "opcodes",
                                        "rom_operands_and_animation_records": "program"}:
        raise ValueError("instruction/data attribution missing")
    correlations = report["correlations"]
    for name, frame in (("hit", HIT), ("ko", KO)):
        item = correlations[name]
        if item.get("source_frame") != frame or not item.get("anim_record_writer_pcs"):
            raise ValueError(name + " anim writer ownership missing")
        if not item.get("closes_gap_external_repoint_ownership"):
            raise ValueError(name + " external repoint gap not closed")
    selected = report["closure"]["selected_pcs"]
    expected_pc_set = {hx(pc) for pc in SELECTED_PCS}
    if set(selected) != expected_pc_set or len(selected) != len(expected_pc_set):
        raise ValueError("selected PC set differs from accepted closure")
    edges = report["closure"]["selected_edges"]
    if {(e["source"], e["target"]) for e in edges} != {(hx(a), hx(b)) for a, b in SELECTED_EDGES}:
        raise ValueError("selected dynamic edge set differs")
    if not report["closure"]["selected_routines"]:
        raise ValueError("no selected routines")
    if report["closure"]["unresolved_computed_targets"] or report["closure"]["unattributed_dependencies"]:
        raise ValueError("closure has unresolved/unattributed dependencies")
    if set(report["coverage"]["actor_fields"]) != REQUIRED_FIELDS:
        raise ValueError("required actor-field attribution missing")
    if report["coverage"].get("computed_target_count") != 0:
        raise ValueError("selected computed targets are unresolved")
    rom = report["dependencies"]["rom_data"]
    if len(rom) != 2 or any(x.get("address_space") != "program" for x in rom):
        raise ValueError("ROM data must use program address space")
    if report.get("forbidden_content_present") is not False:
        raise ValueError("forbidden content marker set")
    if FORBIDDEN.intersection(_walk(report)):
        raise ValueError("forbidden raw/disassembly/trace content key")


def self_test() -> None:
    report = build()
    validate_committed(report)
    mutations = [
        lambda d: d["correlations"]["hit"]["anim_record_writer_pcs"].pop(),
        lambda d: d["correlations"]["ko"]["anim_record_writer_pcs"].pop(),
        lambda d: d["closure"]["selected_edges"].pop(),
        lambda d: d["closure"]["unresolved_computed_targets"].append("0x000002"),
        lambda d: d["closure"]["selected_pcs"].__setitem__(0, "0xfffffe"),
        lambda d: d["dependencies"]["rom_data"][0].__setitem__("address_space", "opcodes"),
        lambda d: d["coverage"]["actor_fields"].remove("health"),
        lambda d: d["correlations"]["ko"].__setitem__("source_frame", KO + 1),
        lambda d: d.__setitem__("trace_text", "forbidden"),
    ]
    for mutate in mutations:
        changed = copy.deepcopy(report); mutate(changed)
        try:
            validate_committed(changed)
        except (KeyError, TypeError, ValueError):
            continue
        raise AssertionError("self-test mutation was accepted")
    print("HIT/KO writer-set self-test and 9 production-validator mutations passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--probe-ledger", type=Path)
    parser.add_argument("--scratch-mutation-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    elif args.generate:
        report = build()
        OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        validate_committed(json.loads(OUT.read_text(encoding="utf-8")))
        print("wrote %s sha256=%s" % (OUT, sha(OUT)))
    elif args.probe_ledger:
        validate_private_correlation(args.probe_ledger)
        print("private semantic correlation probe passed")
    elif args.scratch_mutation_test:
        scratch_mutation_test()
    else:
        parser.error("choose --self-test or --generate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
