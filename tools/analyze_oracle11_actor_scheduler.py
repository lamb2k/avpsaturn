#!/usr/bin/env python3
"""Close the Round 1 non-player actor scheduler and lifecycle authority.

The decoded opcode image and private ORACLE-10 captures remain ignored.  This
tool emits only bounded source semantics, hashes, and counterfactual outcomes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPCODES = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_opcodes_2m.bin"
PROGRAM = ROOT / ".deps" / "mame" / "actorprobe" / "decrypted_program_2m.bin"
ROUTE = ROOT / "data" / "oracle10_round1_route.json"
OUT = ROOT / "data" / "oracle11_actor_scheduler_lifecycle.json"

POOLS = (
    {
        "type": 12, "base": 0xFF9580, "capacity": 20, "stride": 0xC0,
        "init": 0x01729E, "scheduler": 0x01B974,
        "table": 0x01B9B6, "table_entries": 43,
        "allocate": 0x01769E, "release": 0x0176B4,
        "free_count": 0xFFEE80, "free_cursor": 0xFFEE58,
        "required_classes": (0x00, 0x01, 0x06, 0x1F),
        "scheduler_writes": ["+0x48 u8 countdown", "+0x47 u8 gated flag"],
    },
    {
        "type": 16, "base": 0xFFA480, "capacity": 20, "stride": 0x80,
        "init": 0x017376, "scheduler": 0x01B8BC,
        "table": 0x01B8EE, "table_entries": 10,
        "allocate": 0x01778C, "release": 0x0177A2,
        "free_count": 0xFFEE83, "free_cursor": 0xFFEE5E,
        "required_classes": (0x06,), "scheduler_writes": [],
    },
    {
        "type": 20, "base": 0xFFAE80, "capacity": 16, "stride": 0x80,
        "init": 0x017344, "scheduler": 0x01BC38,
        "table": 0x01BC7A, "table_entries": 24,
        "allocate": 0x0176F0, "release": 0x017706,
        "free_count": 0xFFEE85, "free_cursor": 0xFFEE62,
        "required_classes": (0x07, 0x08, 0x09, 0x0A),
        "scheduler_writes": [],
    },
    {
        "type": 24, "base": 0xFFB680, "capacity": 32, "stride": 0x80,
        "init": 0x0173AA, "scheduler": 0x01BA62,
        "table": 0x01BA94, "table_entries": 105,
        "allocate": 0x0177DA, "release": 0x0177F0,
        "free_count": 0xFFEE89, "free_cursor": 0xFFEE6A,
        "required_classes": (0x10, 0x3D, 0x43, 0x45, 0x49, 0x4B, 0x4E),
        "scheduler_writes": [],
    },
)

FRAME_ORDER = (
    (4, 0x01B846), (8, 0x01B916), (12, 0x01B974),
    (16, 0x01B8BC), (20, 0x01BC38), (24, 0x01BA62),
    (28, 0x01BCDA), (36, 0x01BD48),
)

# Exact decoded instruction prefixes reject a wrong ROM/decryption or a fitted
# pool description.  Full relevant windows are also hashed into the report.
PREFIXES = {
    0x01729E: "41ed6eea4ded15801b7c00146e80303c0013",
    0x017376: "41ed6f1a4ded24801b7c00146e83303c0013",
    0x017344: "41ed6f3a4ded2e801b7c00106e85303c000f",
    0x0173AA: "41ed6f7a4ded36801b7c00206e89303c001f",
    0x01769E: "4a2d6e80670e532d6e80306d6e5838583b486e58",
    0x0176B4: "70002c802d4000042d40000c2d40002c",
    0x01778C: "4a2d6e83670e532d6e83306d6e5e38583b486e5e",
    0x0177A2: "70002c802d4000042d40000c2d40002c",
    0x0176F0: "4a2d6e85670e532d6e85306d6e6238583b486e62",
    0x017706: "70002c802d4000042d40000c2d40002c",
    0x0177DA: "4a2d6e89670e532d6e89306d6e6a38583b486e6a",
    0x0177F0: "70002c802d4000042d40000c2d40002c",
    0x01B974: "303c0045720b4eb9000011ea7e134ded1580",
    0x01B8BC: "303c006572094eb9000011ea7e134ded2480",
    0x01BC38: "303c007472074eb9000011ea426d03f4426d04f4",
    0x01BA62: "303c007372084eb9000011ea7e1f4ded3680",
    0x00849E: "4eb90001b8464eb90001b9164eb90001b9744eb90001b8bc"
              "4eb90001bc384eb90001ba624eb90001bcda4eb90001bd48",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"


def read_u32(data: bytes, address: int) -> int:
    return int.from_bytes(data[address:address + 4], "big")


def source_window(data: bytes, start: int, end: int) -> dict[str, object]:
    return {
        "start": f"0x{start:06x}", "end_exclusive": f"0x{end:06x}",
        "bytes": end - start, "sha256": sha256_bytes(data[start:end]),
    }


def build_report() -> dict[str, object]:
    opcodes = OPCODES.read_bytes()
    program = PROGRAM.read_bytes()
    route = json.loads(ROUTE.read_text(encoding="utf-8"))
    require(len(opcodes) == 0x200000 and len(program) == 0x200000,
            "decoded source image size drift")
    for address, expected in PREFIXES.items():
        raw = bytes.fromhex(expected)
        require(opcodes[address:address + len(raw)] == raw,
                f"decoded source prefix drift at 0x{address:06x}")

    actors = {(int(row["class"], 16), row["type"])
              for row in route["actor_archetypes"]}
    pool_rows = []
    required_dispatch = []
    for pool in POOLS:
        table_end = pool["table"] + pool["table_entries"] * 4
        entries = [read_u32(opcodes, pool["table"] + index * 4)
                   for index in range(pool["table_entries"])]
        require(all(0 < routine < len(opcodes) for routine in entries),
                f"type-{pool['type']} dispatch pointer escaped source image")
        mappings = []
        for actor_class in pool["required_classes"]:
            require((actor_class, pool["type"]) in actors,
                    f"required class/type absent from full route: "
                    f"{actor_class:02x}/{pool['type']}")
            mappings.append({
                "class": f"0x{actor_class:02x}",
                "routine": f"0x{entries[actor_class]:06x}",
            })
            required_dispatch.append((pool["type"], actor_class,
                                      entries[actor_class]))
        last = pool["base"] + (pool["capacity"] - 1) * pool["stride"]
        pool_rows.append({
            "record_type": pool["type"],
            "source_base": f"0x{pool['base']:06x}",
            "last_slot": f"0x{last:06x}",
            "capacity": pool["capacity"], "stride": pool["stride"],
            "record_type_field": "+0x08 u8 initialized before activation",
            "active_field": "+0x00 u8; zero skips dispatch",
            "class_field": "+0x02 s8 extended to word then multiplied by four",
            "initializer": f"0x{pool['init']:06x}",
            "scheduler": f"0x{pool['scheduler']:06x}",
            "dispatch_table": f"0x{pool['table']:06x}",
            "dispatch_table_entries": pool["table_entries"],
            "dispatch_table_identity": source_window(
                opcodes, pool["table"], table_end),
            "required_round1_dispatch": mappings,
            "allocation": {
                "routine": f"0x{pool['allocate']:06x}",
                "free_count": f"0x{pool['free_count']:06x} u8",
                "free_cursor": f"0x{pool['free_cursor']:06x} low-word pointer",
                "rule": "if count is nonzero, decrement then pop the next low-word slot address into A4; otherwise return without allocating",
            },
            "release": {
                "routine": f"0x{pool['release']:06x}",
                "rule": "clear source-selected record fields, push A6 low-word address before the current cursor, increment free count",
                "order": "LIFO free-list reuse",
            },
            "update": {
                "order": "ascending address/index, exactly capacity slots",
                "guard": "dispatch only when +0x00 active is nonzero",
                "dispatch": "read signed class byte +0x02, multiply by four, PC-relative absolute-long table call",
                "bounds_rule": "no scheduler bounds check; allocation/initialization must preserve a valid source class",
                "scheduler_owned_writes": pool["scheduler_writes"],
                "rng_consumption": "none in scheduler; class routine owns any RNG calls",
            },
        })

    controls = route["control_captures"]
    require(controls["independently_launched"] is True and
            controls["byte_identical"] is True,
            "ORACLE-10 controls are not independent and byte-identical")
    counterfactuals = route["targeted_counterfactuals"]
    control_names = ("remove_class_1f", "remove_class_00",
                     "remove_class_01", "remove_class_06",
                     "remove_auxiliary_classes")
    for name in control_names:
        require(counterfactuals[name]["status"] == "PASS" and
                counterfactuals[name]["detected"] is True and
                counterfactuals[name]["semantic_difference"] is not None,
                f"scheduler counterfactual did not alter source state: {name}")

    report = {
        "schema": "oracle11-actor-scheduler-lifecycle-v1",
        "status": "SOURCE_CLOSED",
        "scope": "Round 1 non-player record types 12, 16, 20, and 24; player update authority is deliberately deferred to the player family",
        "source_identity": {
            "decoded_opcodes_sha256": sha256_bytes(opcodes),
            "decrypted_program_sha256": sha256_bytes(program),
            "scheduler_call_order": source_window(opcodes, 0x00849E, 0x0084CE),
            "pool_initializer": source_window(opcodes, 0x01729E, 0x0174A4),
            "allocation_release": source_window(opcodes, 0x017654, 0x01790C),
        },
        "frame_scheduler": {
            "owner": "0x00849e..0x0084ce",
            "full_order": [{"record_type": kind,
                            "routine": f"0x{routine:06x}"}
                           for kind, routine in FRAME_ORDER],
            "required_round1_order": [12, 16, 20, 24],
            "rule": "each active pool is exhausted in ascending slot order before the next pool begins",
        },
        "pools": pool_rows,
        "required_dispatch_count": len(required_dispatch),
        "deterministic_source_controls": {
            "independently_launched": True,
            "byte_identical": True,
            "capture_a_samples_sha256": controls["capture_a"]["files"]["samples.tsv"]["sha256"],
            "capture_b_samples_sha256": controls["capture_b"]["files"]["samples.tsv"]["sha256"],
        },
        "targeted_counterfactuals": [{
            "name": name, "status": "PASS",
            "first_semantic_difference": counterfactuals[name]["semantic_difference"],
            "completed_round1": counterfactuals[name]["completed_round1"],
            "actor_events_sha256": counterfactuals[name]["actor_events_sha256"],
        } for name in control_names],
        "closure": {
            "classification": "SOURCE_CLOSED",
            "entry_exit": "pool allocation/pop and release/push routines recovered",
            "state_dispatch": "active guard, class-table indexing, call, slot increment, and pool order recovered",
            "types_signedness": "active/type/count are u8; class is sign-extended s8; slot pointers are low-word work-RAM addresses",
            "reads_writes": "scheduler and pool-specific release field sets are bound by decoded routines",
            "rng": "no scheduler RNG; consumption remains with each class authority",
            "mutation_control": "tests reject stride, scheduler order, dispatch mapping, free-list, and classification mutations",
            "remaining_unknowns": [],
        },
        "protected_boundaries": {
            "production_runtime_writes": 0,
            "frontend_active": False,
            "user09_status": "CHANGES_REQUESTED",
            "salvage08_active": False,
            "physical_saturn": "UNRUN",
        },
    }
    validate(report)
    return report


def validate(report: dict[str, object]) -> None:
    require(report["schema"] == "oracle11-actor-scheduler-lifecycle-v1",
            "schema drift")
    require(report["status"] == "SOURCE_CLOSED" and
            report["closure"]["classification"] == "SOURCE_CLOSED" and
            report["closure"]["remaining_unknowns"] == [],
            "scheduler family is not source closed")
    pools = report["pools"]
    require([(row["record_type"], row["capacity"], row["stride"])
             for row in pools] ==
            [(12, 20, 0xC0), (16, 20, 0x80),
             (20, 16, 0x80), (24, 32, 0x80)],
            "required pool topology drift")
    require(report["frame_scheduler"]["required_round1_order"] ==
            [12, 16, 20, 24], "required scheduler order drift")
    require(report["required_dispatch_count"] == 16,
            "required dispatch mapping count drift")
    for row in pools:
        require(row["release"]["order"] == "LIFO free-list reuse",
                "free-list semantics drift")
        require(row["update"]["order"].startswith("ascending address"),
                "slot update order drift")
        require(len(row["required_round1_dispatch"]) > 0 and
                len(row["dispatch_table_identity"]["sha256"]) == 64,
                "dispatch evidence missing")
    controls = report["deterministic_source_controls"]
    require(controls["independently_launched"] is True and
            controls["byte_identical"] is True and
            controls["capture_a_samples_sha256"] ==
            controls["capture_b_samples_sha256"],
            "deterministic controls drift")
    require(len(report["targeted_counterfactuals"]) == 5 and
            all(row["status"] == "PASS" and
                row["first_semantic_difference"] is not None
                for row in report["targeted_counterfactuals"]),
            "counterfactual coverage drift")
    boundary = report["protected_boundaries"]
    require(boundary == {
        "production_runtime_writes": 0, "frontend_active": False,
        "user09_status": "CHANGES_REQUESTED", "salvage08_active": False,
        "physical_saturn": "UNRUN",
    }, "protected boundary drift")


def main() -> None:
    report = build_report()
    OUT.write_bytes(canonical(report))
    print(f"ORACLE-11 actor scheduler/lifecycle: SOURCE_CLOSED ({len(report['pools'])} pools, {report['required_dispatch_count']} required dispatches)")


if __name__ == "__main__":
    main()
