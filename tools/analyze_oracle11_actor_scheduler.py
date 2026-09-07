#!/usr/bin/env python3
"""Close the Round 1 non-player actor scheduler and lifecycle authority.

The decoded opcode image and private ORACLE-10 captures remain ignored.  This
tool emits only bounded source semantics, hashes, and counterfactual outcomes.
"""
from __future__ import annotations

import hashlib
import json
import sys
import csv
from collections import Counter
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


def interactive_readiness(opcodes: bytes) -> dict[str, object]:
    """Read-only implementation-gap audit; does not amend accepted authority.

    These bounded identities locate the missing contract. They do not license
    native implementation from disassembly or claim a verified tick policy.
    """
    windows = (
        (0x0011EA, 0x0011EC, "1ceeabf0c6a5a30bad12cdac0e3ab015a7188a42e6aebb556aad00bb9cd693ad"),
        (0x001060, 0x00106C, "3171b913384c360ab2d261089a5f08184d3a8c83585cf24942d8ce04748817ff"),
        (0x00808A, 0x0080B6, "5f2ab7570b4e2f33993224d1f93200d99b15e5f40dbb623cbe031cc1a0e003fa"),
        (0x008140, 0x008164, "9c47f48acc7abecc4de586864aefa5d0846f188aa88bab1e89ee724ebcb8e449"),
        (0x014B44, 0x014B92, "9a02807a79055309d019558970d588dfcd59f40de30b801522bc975912472acf"),
        (0x001092, 0x0010B0, "434d2236afa89ad8cff4be34d82ff1d0cafe42ded16426f817a7680c198732af"),
        (0x017090, 0x017176, "c0241a33d06237d9e317532523da6be772022b5b0776a4e65f75728d8242eab7"),
        (0x00C772, 0x00C7AA, "e627f7b48b0d427488075b2bd9998184b8b15b3903c731cfe984bbb25d2824bb"),
        (0x01613C, 0x016196, "00717a1058c3bddb27684f727105a92547ef2f43f390befa8f76ab17b18a8b0f"),
    )
    for start, end, expected in windows:
        require(sha256_bytes(opcodes[start:end]) == expected,
                f"interactive scheduler source window drift: 0x{start:06x}")
    return {
        "status": "BLOCKED_MISSING_EXECUTABLE_TICK_CONTRACT",
        "production_implementation_authorized_by_this_audit": False,
        "accepted_pool_order_unchanged": True,
        "source_windows": [source_window(opcodes, a, b) for a, b, _ in windows],
        "ruled_out": "0x0011ea is RTS, not a pool scheduler yield",
        "located_boundary": {
            "loop": "0x00808a..0x0080b6",
            "loop_tail": "0x008140..0x008164",
            "suspend_wrapper": "0x001060..0x00106c invokes trap 3",
            "observed_fields": ["0xff81a6:u8", "0xff8019:u8",
                                "0xff81bc:u8", "0xff025c:u32 task pointer",
                                "task+0x10:u8", "0xff8054:u8"],
        },
        "missing_implementation_fields": [
            "All writers and interrupt/reset ordering of 0xff81bc and 0xff81a6",
            "Trap-3 suspend/resume guard, task countdown and video-boundary ownership",
            "Route entry/exit calls that suspend within a pool traversal and resume it",
            "Input sampling, hitstop and source-phase-counter order across resumes",
            "Independent changed-input witness for the complete top-level invocation rule",
            "0x014b44 task-countdown owner: ff81b9 guard writers, excluded task index3 and trap4 continuation ordering",
        ],
        "unblock": "Bound the loop, trap-3 and owning interrupt/route continuations in existing Oracle/SPEC; validate retained or bounded independent source witnesses before native translation",
        "forbidden_substitute": "one update per displayed frame or captured phase counts",
        "next_dependency_safe_body": "class0e normal presentation archive/allowlist/no-op adapter, host body already implemented",
        "target_emulator_visual_retries": 0,
    }


def clock_guard_owner(row: dict[str, str]) -> str:
    """Attribute actual write taps, never opcode-prefetch counts, to a writer."""
    key = (row["address"], row["pc"], int(row["data"]), int(row["mask"]))
    owners = {
        ("ff81bc", "008090", 65535, 65280): "loop_00808a_set",
        ("ff81bc", "000e92", 0, 65280): "irq2_000e8c_clear",
        ("ff81a6", "001432", 0, 65280): "irq2_helper_00142e_clear",
    }
    require(row["event"] == "guard_write" and key in owners,
            "unowned scheduler guard write")
    return owners[key]


def validate_wake_write(row: dict[str, str], suppressed: bool = False) -> None:
    """Validate measured one-player control writes against bounded source code.

    Read values are pre-write. The helper is Oracle validation, not a native
    execution contract and not authority to replay these observations.
    """
    pc = row["pc"]
    counter, request = int(row["wake_counter"]), int(row["wake_request"])
    # (address, bus mask, value after selecting the addressed byte/word).
    writes = {
        "00c774": ("ff823a", 65280, 0), "00c778": ("ff81b8", 255, 0),
        "00c77c": ("ff1744", 65535, 0), "00c79a": ("ff823a", 65280, 0),
        "00c79e": ("ff81b8", 255, 0), "00c7a2": ("ff1744", 65535, 0),
        "017096": ("ff81b8", 255, 0), "0170ac": ("ff823a", 65280, 1),
        "0170e2": ("ff1744", 65535, 1), "0170ee": ("ff1744", 65535, 0),
        "0170f2": ("ff823a", 65280, 0), "0170f8": ("ff81b8", 255, 0),
        "0170fc": ("ff823a", 65280, 0), "017112": ("ff823a", 65280, 1),
        "01714e": ("ff1744", 65535, (counter + 1) & 65535),
        "01715a": ("ff81b8", 255, 0 if suppressed else 1),
        "017160": ("ff1744", 65535, 5), "017166": ("ff823a", 65280, 1),
        "01716e": ("ff1744", 65535, 0), "017172": ("ff81b8", 255, 0),
        "017176": ("ff823a", 65280, 0), "0174ba": ("ff823a", 65535, 0),
    }
    require(row["event"] == "control_write" and pc in writes,
            "unowned wake-control writer")
    address, mask, value = writes[pc]
    actual = (int(row["data"]) & mask) >> (8 if mask == 65280 else 0)
    require(row["address"] == address and int(row["mask"]) == mask and actual == value,
            "wake-control write arithmetic or field drift")
    if pc in ("0170ac", "017112"):
        require(int(row["participation"]) & 1 and int(row["input1"]) & 127,
                "wake-control participating input guard drift")
    if pc in ("01714e", "01715a", "017160", "017166"):
        require(request != 0, "wake-control request guard drift")
    if pc in ("01715a", "017160", "017166"):
        require(counter >= 5, "wake-control threshold guard drift")
    if pc in ("0170ee", "0170f2", "01716e", "017172", "017176"):
        require(request == 0, "wake-control release guard drift")


def wake_suppression_evidence(baseline_rows: list[dict[str, str]]) -> dict[str, object]:
    directory = ROOT / ".deps/mame/oracle11_scheduler_clock_m3"
    with (directory / "coffee_shop_scene_frames.tsv").open() as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    require([int(row["frame"]) for row in rows] == list(range(1972, 5567)),
            "incomplete source suppression run")
    difference = next(({"frame": int(a["frame"]), "fields": {
        key: [a[key], m[key]] for key in a if a[key] != m[key]}}
        for a, m in zip(baseline_rows, rows) if a != m), None)
    suppressions, secondary_ready, first_trigger = 0, 0, None
    pending = False
    with (directory / "coffee_shop_scheduler_clock.tsv").open() as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            if pending:
                require(row["event"] == "control_write" and row["pc"] == "01715a",
                        "source suppression did not reach its intended write")
                validate_wake_write(row, suppressed=True)
                pending = False
            if row["event"] == "wake_suppression":
                validate_wake_write(dict(row, event="control_write"))
                first_trigger = first_trigger if first_trigger is not None else int(row["frame"])
                suppressions += 1
                pending = True
            elif (row["event"], row["address"], row["pc"]) == (
                    "task_write", "ff00d8", "014b6a"):
                secondary_ready += 1
    require(suppressions > 0 and not pending, "source suppression never executed")
    require(secondary_ready == 0, "source secondary wake survived suppression")
    require(difference is not None and difference["frame"] >= first_trigger,
            "source suppression lacks an attributable downstream state difference")
    hashes = {}
    for name in ("coffee_shop_scheduler_clock.tsv", "coffee_shop_scene_frames.tsv"):
        with (directory / name).open("rb") as stream:
            hashes[name] = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"status": "VALID_SOURCE_CAUSAL_REJECTION", "native_mutation_kills": 0,
            "path": directory.relative_to(ROOT).as_posix(), "files_sha256": hashes,
            "source_trigger_suppressions": suppressions, "first_trigger_frame": first_trigger,
            "secondary_main_task_ready_writes": secondary_ready,
            "first_scene_difference": difference, "final_scene_state": rows[-1],
            "route_completion_required_of_this_negative_control": False}


def scheduler_clock_evidence(revision: int = 1) -> dict[str, object]:
    """Summarize ignored paired/changed-input evidence; NOT executable SPEC.

    This intentionally does not change the accepted pool-authority artifact.
    Fetch taps include prefetches. SP is the supervisor stack during these
    observations: the historical stack_return column is NOT a caller witness.
    """
    names = ("coffee_shop_scheduler_clock.tsv", "coffee_shop_scene_actors.tsv",
             "coffee_shop_scene_frames.tsv", "coffee_shop_scene_health_writes.tsv",
             "coffee_shop_rng_calls.tsv", "samples.tsv", "dispatches.tsv",
             "coffee_shop_type36_writes.tsv")
    require(revision in (1, 2, 3), "unknown scheduler probe revision")
    labels = tuple(letter + str(revision) for letter in ("a", "b", "p"))
    baseline, repeat, perturb = labels
    captures = {}
    scenes = {}
    for suffix in labels:
        directory = ROOT / ".deps/mame" / ("oracle11_scheduler_clock_" + suffix)
        identities = {}
        for name in names:
            with (directory / name).open("rb") as stream:
                identities[name] = hashlib.file_digest(stream, "sha256").hexdigest()
        with (directory / "coffee_shop_scene_frames.tsv").open() as stream:
            rows = list(csv.DictReader(stream, delimiter="\t"))
        require([int(row["frame"]) for row in rows] == list(range(1972, 5567)),
                "incomplete scheduler scene witness")
        edges = []
        for row in rows:
            state = int(row["route_state"])
            if not edges or edges[-1][1] != state:
                edges.append([int(row["frame"]), state])
        require([state for _, state in edges] == [2, 4, 6, 0, 2],
                "scheduler witness did not traverse Coffee Shop exit")
        scenes[suffix] = rows
        captures[suffix] = {"path": directory.relative_to(ROOT).as_posix(),
                            "files_sha256": identities, "route_edges": edges,
                            "final_state": rows[-1]}
    require(captures[baseline]["files_sha256"] == captures[repeat]["files_sha256"],
            "scheduler cold pair differs")
    first = next(({"frame": int(a["frame"]), "fields": {
        key: [a[key], p[key]] for key in a if a[key] != p[key]}}
        for a, p in zip(scenes[baseline], scenes[perturb]) if a != p), None)
    require(first is not None, "scheduler changed-input witness is equivalent")
    require(captures[baseline]["route_edges"] != captures[perturb]["route_edges"],
            "changed input did not alter route chronology")
    # Stream the large ledgers; do not retain millions of dictionaries in RAM.
    for suffix in (baseline, perturb):
        directory = ROOT / captures[suffix]["path"]
        events, guards, main_task_writes = Counter(), Counter(), Counter()
        control_writes, trap3_callers = Counter(), Counter()
        previous = 0
        with (directory / names[0]).open() as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                sequence = int(row["sequence"])
                require(sequence == previous + 1, "scheduler event sequence gap")
                previous = sequence
                lower = 0 if row["event"] == "control_write" else 1972
                require(lower <= int(row["frame"]) < 5566,
                        "scheduler event outside declared observation window")
                events[row["event"]] += 1
                if row["event"] == "guard_write":
                    guards[clock_guard_owner(row)] += 1
                elif row["event"] == "task_write" and row["address"] == "ff00d8":
                    main_task_writes[(row["pc"], row["data"], row["mask"])] += 1
                    if revision >= 2 and row["pc"] == "001082":
                        trap3_callers[int(row["user_plus60"])] += 1
                elif row["event"] == "control_write" and int(row["frame"]) >= 1972:
                    if revision == 3:
                        validate_wake_write(row)
                    control_writes[(row["pc"], row["address"], row["data"], row["mask"])] += 1
        require(all(guards[name] > 0 for name in (
            "loop_00808a_set", "irq2_000e8c_clear", "irq2_helper_00142e_clear")),
            "missing scheduler guard owner witness")
        captures[suffix].update(event_counts=dict(events), guard_writers=dict(guards),
            main_task_state_writers=[{"tap_pc": pc, "data": int(data),
                "mask": int(mask), "count": count}
                for (pc, data, mask), count in sorted(main_task_writes.items())])
        if revision >= 2:
            captures[suffix].update(
                scene_control_writers=[{"tap_pc": pc, "address": address,
                    "data": int(data), "mask": int(mask), "count": count}
                    for (pc, address, data, mask), count in sorted(control_writes.items())],
                main_task_trap3_callers=[{"return_pc": f"0x{pc:06x}", "count": count}
                    for pc, count in sorted(trap3_callers.items())])
    report = {
        "status": "PAIRED_AND_CHANGED_INPUT_WITNESSES_BOUND_TICK_CONTRACT_PARTIAL",
        "scope": "Coffee Shop source observation1972..5566, not Round1 completion",
        "captures": captures, "first_changed_scene_state": first,
        "accepted_pool_authority_changed": False,
        "native_implementation_authorized": False,
        "projection_limits": [
            "opcode_fetch is not an instruction invocation or scheduler tick",
            "stack_return reads supervisor SP, not the suspended user caller",
            "write-tap PC is the observation PC; source instruction precedes it",
        ],
        "remaining_blocker": "Bind ff81b9-controlled task-countdown program014b44 and trap4 plus route/task continuations and CPU-overrun versus explicit-yield behavior; no guessed per-video-frame invocation rule",
        "target_emulator_visual_retries": 0,
    }
    if revision == 3:
        report["source_wake_suppression"] = wake_suppression_evidence(scenes[baseline])
        report["source_identity"] = {
            "decoded_opcodes_sha256": sha256_bytes(OPCODES.read_bytes()),
            "program_sha256": sha256_bytes(PROGRAM.read_bytes()),
            "windows": interactive_readiness(OPCODES.read_bytes())["source_windows"],
            "pinned_mame_sha256": "af6966108d9b52c22465c6d50f4e5d50cc371b50f2d27dc443935f287aad37a3",
        }
        report["bounded_source_wake_rules"] = {
            "status": "SOURCE_WITNESSED_NOT_YET_EXECUTABLE_SPEC",
            "owners": ["0x017090..0x017176", "0x014b44..0x014b92"],
            "fields": {"0xff81b9": "u8 wake guard", "0xff823a": "u8 input request",
                       "0xff1744": "u16 counter", "0xff81bf": "u8 participation bits",
                       "0xff8064/66/68": "u8 raw controller input"},
            "initialization": "17090 clears wake guard, preserves prior request then ORs participating input; counter becomes1 if request is nonzero else0",
            "update": "170f2 clears guard/request; participating input masked127 sets request; increment u16 counter before unsigned compare5; at least5 sets guard1 and clamps counter5; absent input clears counter/guard/request",
            "secondary_task_scan": "014b44 only when wake guard nonzero: ascending16 tasks ff0058 stride32; state byte1 countdown decremented, zero becomesstate4; exclude index3 (descending DBRA counter12)",
            "continuation": "014b70 calls trap4 wrapper001092; resumes at014b76; task queue ordering and route/load continuation contract remain incomplete",
            "prohibited_native_substitute": "recorded frame or task-write count",
        }
        report["remaining_blocker"] = (
            "No executable source-to-native clock contract for CPU-throughput-dependent "
            "secondary task scans and IRQ preemption, or command-queue/result continuation "
            "01614a waiting on ff837b. Fixed per-video-frame invocation or authored "
            "acceleration would be a gameplay-timing adaptation, not proven source parity. "
            "No such adaptation is authorized by this evidence.")
        report["probe_passes"] = [
            "1: paired loop/IRQ/task write baseline and changed-input source route",
            "2: secondary guard writer and correct user-stack return provenance",
            "3: full wake guard/counter/input fields, repeat/perturb and causal suppression",
        ]
    return report


def main() -> None:
    if sys.argv[1:] in (["--scheduler-clock-evidence"], ["--scheduler-clock-evidence2"], ["--scheduler-clock-evidence3"]):
        revision = int(sys.argv[1][-1]) if sys.argv[1][-1].isdigit() else 1
        report = scheduler_clock_evidence(revision)
        filename = "oracle11_scheduler_clock" + (f"_v{revision}" if revision > 1 else "") + ".json"
        output = ROOT / "build/verification" / filename
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(canonical(report))
        print(f"Scheduler source witnesses: {report['status']}; {output}")
        return
    if sys.argv[1:] == ["--interactive-readiness"]:
        print(canonical(interactive_readiness(OPCODES.read_bytes())).decode("ascii"), end="")
        return
    require(not sys.argv[1:], "unknown scheduler analyzer arguments")
    report = build_report()
    OUT.write_bytes(canonical(report))
    print(f"ORACLE-11 actor scheduler/lifecycle: SOURCE_CLOSED ({len(report['pools'])} pools, {report['required_dispatch_count']} required dispatches)")


if __name__ == "__main__":
    main()
