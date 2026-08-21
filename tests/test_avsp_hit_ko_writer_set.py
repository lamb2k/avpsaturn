"""Focused committed-artifact contract for the class 0x1F HIT/KO writer set."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "map_avsp_hit_ko_writer_set.py"
REPORT = ROOT / "data" / "avsp_hit_ko_writer_set.json"
BOUNDARY = ROOT / "data" / "avsp_translation_boundary.json"

REQUIRED_FIELDS = {
    "state",
    "sub_state",
    "action",
    "anim_record",
    "anim_timer",
    "health",
    "hit_value",
}
EXACT_WINDOW = {
    "first_source_frame": 4080,
    "last_source_frame": 5469,
    "hit_semantic_sample_after": 5191,
    "ko_semantic_sample_after": 5330,
    "semantic_sample_count": 1390,
    "execution_interval_count": 1389,
    "synthetic_final_epoch": False,
}


def load_tool():
    spec = importlib.util.spec_from_file_location("hit_ko_writer_set", TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load production mapper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mutation_rejection_text(module, report, mutate):
    candidate = copy.deepcopy(report)
    mutate(candidate)
    try:
        module.validate_committed(candidate)
    except (AssertionError, AttributeError, IndexError, KeyError, TypeError, ValueError) as error:
        return str(error)
    return None


def mutation_is_rejected(module, report, mutate):
    return mutation_rejection_text(module, report, mutate) is not None


def recompute_integrity(module, report):
    module.refresh_report_bindings(report)
    return report["integrity"]


def module_hash(value):
    import hashlib

    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def selected_routine(report, entry):
    for routine in report["closure"]["selected_routines"]:
        if routine["entry_pc"] == entry:
            return routine
    raise AssertionError("required routine is absent: " + entry)


def changed_value(item):
    if isinstance(item, int):
        return item + 1
    return str(item) + "_corrupt"


def outside_selected_boundary_pc(report):
    selected = set(report["closure"]["selected_pcs"])
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    for unit in boundary["writer_boundary"]["units"]:
        candidate = unit["pc_first"]
        if candidate not in selected:
            return candidate
    raise AssertionError("accepted boundary has no non-selected PC")


def require_rejection(module, report, mutate, name, expected_invariant, failures):
    rejection = mutation_rejection_text(module, report, mutate)
    if rejection is None:
        failures.append(name + ": ACCEPTED")
    elif expected_invariant not in rejection:
        failures.append(
            name
            + ": rejected by "
            + repr(rejection)
            + ", not "
            + repr(expected_invariant)
        )


def main() -> int:
    module = load_tool()
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    module.validate_committed(report)
    failures = []

    helper_probe = copy.deepcopy(report)
    if recompute_integrity(module, helper_probe) != module.integrity(report):
        failures.append("focused integrity recomputation omits production hashes")

    # The correction must derive each field and bind the health/hit semantic
    # deltas to the executed writer instances, not merely list the field names.
    if set(report["coverage"]["actor_fields"]) != REQUIRED_FIELDS:
        failures.append("missing full seven-field coverage")
    transitions = report.get("field_transitions", {})
    for field, count in (("health", 4), ("hit_value", 42)):
        entries = transitions.get(field, [])
        if len(entries) != count:
            failures.append("missing exact %s transition coverage" % field)
            continue
        for entry in entries:
            if (
                entry.get("field") != field
                or "before_value" not in entry
                or "after_value" not in entry
                or not entry.get("writer_instances")
            ):
                failures.append("missing exact %s writer instance" % field)
                break

    # These controls must be rejected by the production validator, not by this
    # wrapper's literal assertions.  They intentionally preserve local JSON
    # shape wherever possible so the validator has to bind immutable evidence.
    require_rejection(
        module,
        report,
        lambda d: d["closure"]["selected_pcs"].append("0xfffffe"),
        "accepted selected PC outside accepted boundary",
        "accepted boundary PC membership",
        failures,
    )
    for anchor in ("first_source_frame", "last_source_frame", "hit_semantic_sample_after", "ko_semantic_sample_after"):
        require_rejection(
            module,
            report,
            lambda d, key=anchor: d["window"].__setitem__(key, d["window"][key] + 1),
            "accepted corrupted window anchor: " + anchor,
            "exact accepted anchors",
            failures,
        )
    require_rejection(
        module,
        report,
        lambda d: d["coverage"].__setitem__("computed_target_count", 999),
        "accepted fabricated computed-target count",
        "derived counts",
        failures,
    )
    require_rejection(
        module,
        report,
        lambda d: d["coverage"].__setitem__("event_exit_count", 999),
        "accepted fabricated event-exit count",
        "derived counts",
        failures,
    )
    def non_observed_edge(candidate):
        candidate["closure"]["selected_edges"][0]["target"] = candidate["closure"]["selected_pcs"][-1]
        recompute_integrity(module, candidate)

    def union_drift(candidate):
        candidate["closure"]["selected_pcs"].append(outside_selected_boundary_pc(candidate))
        recompute_integrity(module, candidate)

    def caller_drift(candidate):
        selected_routine(candidate, "0x01f6c6")["observed_callers"][0] = outside_selected_boundary_pc(candidate)
        recompute_integrity(module, candidate)

    def callee_drift(candidate):
        selected_routine(candidate, "0x01f6c6")["observed_callees"][0] = outside_selected_boundary_pc(candidate)
        recompute_integrity(module, candidate)

    require_rejection(module, report, non_observed_edge, "accepted non-observed internal edge", "immutable PC/edge/routine binding", failures)
    require_rejection(module, report, union_drift, "accepted routine/selected-PC union drift", "routine/selected-PC union", failures)
    require_rejection(module, report, caller_drift, "accepted caller relationship drift", "caller relationship", failures)
    require_rejection(module, report, callee_drift, "accepted callee relationship drift", "callee relationship", failures)

    def integrity_preserving_anchor_mutation(candidate):
        candidate["window"]["first_source_frame"] += 1
        recompute_integrity(module, candidate)

    require_rejection(
        module,
        report,
        integrity_preserving_anchor_mutation,
        "accepted synchronized integrity/hash anchor mutation",
        "exact accepted anchors",
        failures,
    )

    def preserved(candidate, mutate):
        mutate(candidate)
        recompute_integrity(module, candidate)

    invariant_controls = [
        (
            "changed private watchpoint-log hash",
            "private capture provenance",
            lambda d: preserved(d, lambda x: x["private_capture"].__setitem__("watchpoint_log_sha256", "0" * 64)),
        ),
        (
            "changed private sample hash",
            "private capture provenance",
            lambda d: preserved(d, lambda x: x["private_capture"].__setitem__("sample_sha256", "1" * 64)),
        ),
        (
            "changed private watchpoint-event count",
            "private capture provenance",
            lambda d: preserved(d, lambda x: x["private_capture"].__setitem__("watchpoint_event_count", x["private_capture"]["watchpoint_event_count"] + 1)),
        ),
        (
            "promoted evidence tier",
            "evidence tiers",
            lambda d: preserved(d, lambda x: x.__setitem__("evidence_tiers", ["PHYSICAL_SATURN", "STATIC_ANALYSIS", "MEASURED"])),
        ),
        (
            "reordered evidence tiers",
            "evidence tiers",
            lambda d: preserved(d, lambda x: x.__setitem__("evidence_tiers", ["STATIC_ANALYSIS", "MAME_TRACE", "MEASURED"])),
        ),
        (
            "missing evidence tier",
            "evidence tiers",
            lambda d: preserved(d, lambda x: x.__setitem__("evidence_tiers", ["MAME_TRACE", "STATIC_ANALYSIS"])),
        ),
        (
            "reversed instruction address space",
            "address-space attribution",
            lambda d: preserved(d, lambda x: x["address_spaces"].__setitem__("instructions_and_code_targets", "program")),
        ),
        (
            "reversed program address space",
            "address-space attribution",
            lambda d: preserved(d, lambda x: x["address_spaces"].__setitem__("rom_operands_and_animation_records", "opcodes")),
        ),
        (
            "changed HIT typed-exit writer PC",
            "HIT typed event exit",
            lambda d: preserved(d, lambda x: x["dependencies"]["typed_event_exits"][0].__setitem__("writer_pc", "0x01e88a")),
        ),
        (
            "changed HIT typed-exit interval",
            "HIT typed event exit",
            lambda d: preserved(d, lambda x: x["dependencies"]["typed_event_exits"][0].__setitem__("interval_start_frame", 5191)),
        ),
        (
            "changed KO typed-exit writer PC",
            "KO typed event exit",
            lambda d: preserved(d, lambda x: x["dependencies"]["typed_event_exits"][1].__setitem__("writer_pc", "0x01f254")),
        ),
        (
            "changed KO typed-exit interval",
            "KO typed event exit",
            lambda d: preserved(d, lambda x: x["dependencies"]["typed_event_exits"][1].__setitem__("interval_start_frame", 5330)),
        ),
        (
            "hidden top-level trace text",
            "unknown top-level key",
            lambda d: preserved(d, lambda x: x.__setitem__("auxiliary_evidence", "016526: move.l d0,(28,a6)")),
        ),
        (
            "hidden nested disassembly text",
            "unknown key at correlations.hit",
            lambda d: preserved(d, lambda x: x["correlations"]["hit"].__setitem__("operator_note", "016526: move.l d0,(28,a6)")),
        ),
    ]
    for name, invariant, mutate in invariant_controls:
        require_rejection(module, report, mutate, "accepted " + name, invariant, failures)

    if failures:
        raise AssertionError("writer-set correction RED findings: " + "; ".join(failures))

    dispatch_routine = selected_routine(report, "0x01f6c6")
    if not dispatch_routine["observed_callers"] or not dispatch_routine["observed_callees"]:
        raise AssertionError("writer dispatch lacks derived caller/callee closure")

    controls = [
        ("remove observed health writer", "writer observation counts", lambda d: d["writer_observations"]["health"].pop()),
        ("remove observed hit writer", "writer observation counts", lambda d: d["writer_observations"]["hit_value"].pop()),
        ("remove health dependency writer PC", "health/hit dependency closure", lambda d: d["dependencies"]
         ["health_hit_writer_dependencies"][0]["writer_pcs"].pop()),
        ("corrupt health before value", "immutable PC/edge/routine binding", lambda d: d["field_transitions"]["health"][0]
         .__setitem__("before_value", -999)),
        ("health writer destination", "health effective address", lambda d: d["writer_observations"]["health"][2]
         .__setitem__("destination", "0xffa044")),
        ("hit writer width", "hit_value effective address", lambda d: d["writer_observations"]["hit_value"][2]
         .__setitem__("write_width_bytes", 2)),
        ("health actual PC", "health effective address", lambda d: d["writer_observations"]["health"][2]
         .__setitem__("instruction_pc", "0xfffffe")),
        ("health register binding", "health live registers", lambda d: d["writer_observations"]["health"][2]
         ["dynamic_register_binding"].pop("a1")),
        ("remove HIT anim writer", "hit semantic binding", lambda d: d["correlations"]["hit"]["writer_instances"].pop()),
        ("remove KO anim writer", "ko semantic binding", lambda d: d["correlations"]["ko"]["writer_instances"].pop()),
        ("remove selected edge", "selected closure counts", lambda d: d["closure"]["selected_edges"].pop()),
        ("unresolved computed target", "unresolved dependency", lambda d: d["closure"]["unresolved_computed_targets"].append("0x000002")),
        ("unattributed dependency", "unresolved dependency", lambda d: d["closure"]["unattributed_dependencies"].append("0x000002")),
        ("PC outside boundary", "accepted boundary PC membership", lambda d: d["closure"]["selected_pcs"].__setitem__(0, "0xfffffe")),
        ("ROM dependency relabel", "ROM dependency schema", lambda d: d["dependencies"]["rom_data"][0].__setitem__("address_space", "opcodes")),
        ("remove actor field", "actor-field enumeration", lambda d: d["coverage"]["actor_fields"].remove("action")),
        ("shift HIT frame", "hit animation writer", lambda d: d["correlations"]["hit"]["writer_instances"][0].__setitem__("semantic_sample_after", 5192)),
        ("forbidden raw field", "unknown top-level key", lambda d: d.__setitem__("disassembly_text", "forbidden")),
        ("writer PC outside selected boundary", "hit animation writer", lambda d: d["correlations"]["hit"]
         ["writer_instances"][0].__setitem__("instruction_pc", "0xfffffe")),
        ("missing semantic before/after", "immutable integrity binding", lambda d: d["correlations"]["hit"]
         ["semantic_changes"][0].__setitem__("after", changed_value(d["correlations"]["hit"]
         ["semantic_changes"][0]["after"]))),
        ("corrupted routine entry", "routine membership", lambda d: selected_routine(d, "0x01f6c6")
         .__setitem__("entry_pc", "0x01651a")),
        ("corrupted routine member count", "routine membership", lambda d: selected_routine(d, "0x01f6c6")
         .__setitem__("member_pc_count", 1)),
        ("corrupted routine member hash", "routine membership", lambda d: selected_routine(d, "0x01f6c6")
         .__setitem__("member_pc_sha256", "0" * 64)),
        ("disconnected routine member", "routine membership", lambda d: selected_routine(d, "0x01f6c6")
         ["member_pcs"].append("0x01d0ac")),
        ("missing observed caller", "immutable PC/edge/routine binding", lambda d: selected_routine(d, "0x01f6c6")
         ["observed_callers"].pop()),
        ("missing observed callee", "immutable PC/edge/routine binding", lambda d: selected_routine(d, "0x01f6c6")
         ["observed_callees"].pop()),
        ("missing routine field write", "immutable PC/edge/routine binding", lambda d: selected_routine(d, "0x016518")
         ["actor_field_writes"].remove("anim_record")),
        ("changed target actor binding", "work-RAM dependency schema", lambda d: d["dependencies"]["work_ram"][0]
         .__setitem__("address", "0xffa0c0")),
        ("out-of-span HIT ROM address", "program dependencies", lambda d: d["dependencies"]["rom_data"][0]
         .__setitem__("address", "0x1ffffe")),
        ("changed typed event exit", "HIT typed event exit", lambda d: d["dependencies"]["typed_event_exits"][0]
         .__setitem__("event", "enemy_walk_event")),
        ("changed edge kind", "edge kind", lambda d: d["closure"]["selected_edges"][0]
         .__setitem__("kind", "not_an_edge")),
        ("edge absent from dynamic trace", "edge shape", lambda d: d["closure"]["selected_edges"][0]
         .__setitem__("target", "0x000002")),
        ("in-window writer exclusion", "exclusions", lambda d: d["exclusions"].append({
            "kind": "in_window_target_writer", "pc": "0x016526", "interval_start_frame": 5190})),
        ("sample execution alignment shifted", "hit animation writer", lambda d: d["correlations"]["hit"]
         ["writer_instances"][0].__setitem__("interval_start_frame", 5191)),
    ]
    for name, invariant, mutate in controls:
        require_rejection(
            module,
            report,
            lambda candidate, local=mutate: preserved(candidate, local),
            "production validator accepted mutation: " + name,
            invariant,
            failures,
        )
    if failures:
        raise AssertionError("writer-set correction findings: " + "; ".join(failures))
    if any(report["window"].get(key) != value for key, value in EXACT_WINDOW.items()):
        raise AssertionError("committed writer-set anchors differ from accepted window")
    print("HIT/KO writer-set committed artifact and correction controls passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
