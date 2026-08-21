"""Focused committed-artifact contract for the class 0x1F HIT/KO writer set."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "map_avsp_hit_ko_writer_set.py"
REPORT = ROOT / "data" / "avsp_hit_ko_writer_set.json"


def load_tool():
    spec = importlib.util.spec_from_file_location("hit_ko_writer_set", TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load production mapper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def must_reject(module, report, mutate, name):
    candidate = copy.deepcopy(report)
    mutate(candidate)
    try:
        module.validate_committed(candidate)
    except (AssertionError, IndexError, KeyError, TypeError, ValueError):
        return
    raise AssertionError("production validator accepted mutation: " + name)


def selected_routine(report, entry):
    for routine in report["closure"]["selected_routines"]:
        if routine["entry_pc"] == entry:
            return routine
    raise AssertionError("required routine is absent: " + entry)


def changed_value(item):
    if isinstance(item, int):
        return item + 1
    return str(item) + "_corrupt"


def main() -> int:
    module = load_tool()
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    module.validate_committed(report)

    dispatch_routine = selected_routine(report, "0x01f6c6")
    if not dispatch_routine["observed_callers"] or not dispatch_routine["observed_callees"]:
        raise AssertionError("writer dispatch lacks derived caller/callee closure")

    controls = [
        ("remove HIT anim writer", lambda d: d["correlations"]["hit"]["writer_instances"].pop()),
        ("remove KO anim writer", lambda d: d["correlations"]["ko"]["writer_instances"].pop()),
        ("remove selected edge", lambda d: d["closure"]["selected_edges"].pop()),
        ("unresolved computed target", lambda d: d["closure"]["unresolved_computed_targets"].append("0x000002")),
        ("PC outside boundary", lambda d: d["closure"]["selected_pcs"].__setitem__(0, "0xfffffe")),
        ("ROM dependency relabel", lambda d: d["dependencies"]["rom_data"][0].__setitem__("address_space", "opcodes")),
        ("remove actor field", lambda d: d["coverage"]["actor_fields"].remove("action")),
        ("shift HIT frame", lambda d: d["correlations"]["hit"]["writer_instances"][0].__setitem__("semantic_sample_after", 5192)),
        ("forbidden raw field", lambda d: d.__setitem__("disassembly_text", "forbidden")),
        ("writer PC outside selected boundary", lambda d: d["correlations"]["hit"]
         ["writer_instances"][0].__setitem__("instruction_pc", "0xfffffe")),
        ("missing semantic before/after", lambda d: d["correlations"]["hit"]
         ["semantic_changes"][0].__setitem__("after", changed_value(d["correlations"]["hit"]
         ["semantic_changes"][0]["after"]))),
        ("corrupted routine entry", lambda d: selected_routine(d, "0x01f6c6")
         .__setitem__("entry_pc", "0x01651a")),
        ("corrupted routine member count", lambda d: selected_routine(d, "0x01f6c6")
         .__setitem__("member_pc_count", 1)),
        ("corrupted routine member hash", lambda d: selected_routine(d, "0x01f6c6")
         .__setitem__("member_pc_sha256", "0" * 64)),
        ("disconnected routine member", lambda d: selected_routine(d, "0x01f6c6")
         ["member_pcs"].append("0x01d0ac")),
        ("missing observed caller", lambda d: selected_routine(d, "0x01f6c6")
         ["observed_callers"].pop()),
        ("missing observed callee", lambda d: selected_routine(d, "0x01f6c6")
         ["observed_callees"].pop()),
        ("missing routine field write", lambda d: selected_routine(d, "0x016518")
         ["actor_field_writes"].remove("anim_record")),
        ("changed target actor binding", lambda d: d["dependencies"]["work_ram"][0]
         .__setitem__("address", "0xffa0c0")),
        ("out-of-span HIT ROM address", lambda d: d["dependencies"]["rom_data"][0]
         .__setitem__("address", "0x1ffffe")),
        ("changed typed event exit", lambda d: d["dependencies"]["typed_event_exits"]
         .__setitem__(0, "enemy_walk_event")),
        ("changed edge kind", lambda d: d["closure"]["selected_edges"][0]
         .__setitem__("kind", "call")),
        ("edge absent from dynamic trace", lambda d: d["closure"]["selected_edges"][0]
         .__setitem__("target", "0x000002")),
        ("in-window writer exclusion", lambda d: d["exclusions"].append({
            "kind": "in_window_target_writer", "pc": "0x016526", "interval_start_frame": 5190})),
        ("sample execution alignment shifted", lambda d: d["correlations"]["hit"]
         ["writer_instances"][0].__setitem__("interval_start_frame", 5191)),
    ]
    for name, mutate in controls:
        must_reject(module, report, mutate, name)
    print("HIT/KO writer-set committed artifact and 21 mutations passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
