"""Focused committed-artifact contract for the class 0x1F HIT/KO writer set.

Schema 4 correction contract: every seven-field transition must bind decoded
writer instances whose bytes reconstruct the semantic delta, the control-flow
closure must be call-rooted through returns or explicit typed exits, and the
actor-field / ROM / work-RAM / edge / exclusion dependencies must be derived.
Every control deep-copies the real committed artifact and requires the
production validator to reject it for the designated invariant.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "map_avsp_hit_ko_writer_set.py"
REPORT = ROOT / "data" / "avsp_hit_ko_writer_set.json"
BOUNDARY = ROOT / "data" / "avsp_translation_boundary.json"

REQUIRED_FIELDS = {"state", "sub_state", "action", "anim_record", "anim_timer", "health", "hit_value"}
EXPECTED_TRANSITIONS = {"state": 7, "sub_state": 16, "action": 57, "anim_record": 274, "anim_timer": 704, "health": 4, "hit_value": 42}
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


def recompute_integrity(module, report):
    module.refresh_report_bindings(report)
    return report["integrity"]


def selected_routine(report, entry):
    for routine in report["closure"]["selected_routines"]:
        if routine["entry_pc"] == entry:
            return routine
    raise AssertionError("required routine is absent: " + entry)


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
        failures.append(name + ": rejected by " + repr(rejection) + ", not " + repr(expected_invariant))


def main() -> int:
    module = load_tool()
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    module.validate_committed(report)
    failures = []

    helper_probe = copy.deepcopy(report)
    if recompute_integrity(module, helper_probe) != module.integrity(report):
        failures.append("focused integrity recomputation omits production hashes")

    # Blocker 1: exact writer ownership for every selected seven-field
    # transition, bound through decoded instances that reconstruct the delta.
    if set(report["coverage"]["actor_fields"]) != REQUIRED_FIELDS:
        failures.append("missing full seven-field coverage")
    transitions = report.get("field_transitions", {})
    instances = report.get("writer_instances", [])
    for field, count in sorted(EXPECTED_TRANSITIONS.items()):
        entries = transitions.get(field, [])
        if len(entries) != count:
            failures.append("missing exact %s transition coverage" % field)
            continue
        for entry in entries:
            indices = entry.get("writer_instance_indices")
            if (
                entry.get("field") != field
                or "before_value" not in entry
                or "after_value" not in entry
                or not indices
                or not entry.get("surviving_writer_pcs")
                or any(not 0 <= index < len(instances) for index in indices)
                or any(field not in instances[index].get("fields", []) for index in indices)
            ):
                failures.append("missing exact %s writer instance binding" % field)
                break

    # Blocker 2: call-rooted closure through returns or explicit typed exits.
    if not instances:
        failures.append("missing decoded writer instances")
    for item in instances:
        if item.get("owner_entered_by_call") is not True:
            failures.append("writer instance is not call-rooted: " + str(item.get("index")))
            break
        if item.get("owner_exit") not in {"return", "context_switch"}:
            failures.append("writer instance lacks derived return/typed exit: " + str(item.get("index")))
            break
    closure = report.get("closure", {})
    if closure.get("task_root", {}).get("kind") != "task_return_resume":
        failures.append("closure lacks derived task-root binding")
    roles = {routine["entry_pc"]: routine["closure_role"] for routine in closure.get("selected_routines", [])}
    for item in instances:
        if roles.get(item.get("owner_entry_pc")) != "writer_owner":
            failures.append("writer owner routine is not selected as writer_owner")
            break
    for routine in closure.get("selected_routines", []):
        if routine["closure_role"] != "task_root" and not routine.get("observed_callers"):
            failures.append("selected routine lacks derived caller: " + routine["entry_pc"])

    # Blocker 3: derived dependencies (external callees, scheduler exits,
    # per-field writer dependencies, work-RAM byte offsets, ROM pointer set).
    dependencies = report.get("dependencies", {})
    if not dependencies.get("external_callees"):
        failures.append("missing derived external-callee dependencies")
    if not dependencies.get("task_scheduler_exits"):
        failures.append("missing derived task-scheduler typed exits")
    dependency_fields = {item.get("field") for item in dependencies.get("field_writer_dependencies", [])}
    if dependency_fields != REQUIRED_FIELDS:
        failures.append("missing derived per-field writer dependencies")
    if not REQUIRED_FIELDS <= set(dependencies.get("actor_field_references", {})):
        failures.append("missing derived actor-field operand references")
    offsets = dependencies.get("work_ram", [{}])[0].get("written_byte_offsets", {})
    if set(offsets) != REQUIRED_FIELDS or any(not value for value in offsets.values()):
        failures.append("missing derived work-RAM byte offsets")
    rom = dependencies.get("rom_data", [])
    if not rom or rom[0].get("derived_from") != "anim_record_writer_values":
        failures.append("ROM dependency is not derived from writer values")
    outgoing = dependencies.get("outgoing_control_edges", [])
    if not outgoing or report["coverage"].get("outgoing_control_edge_count") != len(outgoing):
        failures.append("missing derived outgoing-control dependencies")
    collapse = dependencies.get("trace_collapse_dependency", {})
    if not collapse or report["exclusions"][-1] != collapse:
        failures.append("missing derived trace-collapse exclusion")

    if failures:
        raise AssertionError("writer-set correction RED findings: " + "; ".join(failures))

    # Card chapter 3 controls plus validator trust-boundary controls.  Each
    # must be rejected by the production validator for its designated
    # invariant, not by this wrapper's literal assertions.
    require_rejection(
        module, report,
        lambda d: d["closure"]["selected_pcs"].append("0xfffffe"),
        "accepted selected PC outside accepted boundary",
        "accepted boundary PC membership", failures)
    for anchor in ("first_source_frame", "last_source_frame", "hit_semantic_sample_after", "ko_semantic_sample_after"):
        require_rejection(
            module, report,
            lambda d, key=anchor: d["window"].__setitem__(key, d["window"][key] + 1),
            "accepted corrupted window anchor: " + anchor,
            "exact accepted anchors", failures)
    require_rejection(
        module, report,
        lambda d: d["coverage"].__setitem__("computed_target_count", 999),
        "accepted fabricated computed-target count", "derived counts", failures)
    require_rejection(
        module, report,
        lambda d: d["coverage"].__setitem__("event_exit_count", 999),
        "accepted fabricated event-exit count", "derived counts", failures)

    def preserved(candidate, mutate):
        mutate(candidate)
        recompute_integrity(module, candidate)

    def non_observed_edge(candidate):
        candidate["closure"]["selected_edges"][0]["target"] = candidate["closure"]["selected_pcs"][-1]
        recompute_integrity(module, candidate)

    def union_drift(candidate):
        candidate["closure"]["selected_pcs"].append(outside_selected_boundary_pc(candidate))
        candidate["closure"]["selected_pcs"].sort()
        recompute_integrity(module, candidate)

    def caller_drift(candidate):
        selected_routine(candidate, "0x01f6c6")["observed_callers"][0]["call_site_pc"] = outside_selected_boundary_pc(candidate)
        recompute_integrity(module, candidate)

    def callee_drift(candidate):
        routine = next(item for item in candidate["closure"]["selected_routines"] if item["observed_selected_callees"])
        routine["observed_selected_callees"][0] = outside_selected_boundary_pc(candidate)
        recompute_integrity(module, candidate)

    require_rejection(module, report, non_observed_edge, "accepted non-observed internal edge", "immutable PC/edge/routine binding", failures)
    require_rejection(module, report, union_drift, "accepted routine/selected-PC union drift", "routine/selected-PC union", failures)
    require_rejection(module, report, caller_drift, "accepted caller relationship drift", "caller relationship", failures)
    require_rejection(module, report, callee_drift, "accepted callee relationship drift", "callee relationship", failures)

    def integrity_preserving_anchor_mutation(candidate):
        candidate["window"]["first_source_frame"] += 1
        recompute_integrity(module, candidate)

    require_rejection(
        module, report, integrity_preserving_anchor_mutation,
        "accepted synchronized integrity/hash anchor mutation",
        "exact accepted anchors", failures)

    invariant_controls = [
        ("changed private watchpoint-log hash", "private capture provenance",
         lambda d: preserved(d, lambda x: x["private_capture"].__setitem__("watchpoint_log_sha256", "0" * 64))),
        ("changed private sample hash", "private capture provenance",
         lambda d: preserved(d, lambda x: x["private_capture"].__setitem__("sample_sha256", "1" * 64))),
        ("changed private watchpoint-event count", "private capture provenance",
         lambda d: preserved(d, lambda x: x["private_capture"].__setitem__("watchpoint_event_count", x["private_capture"]["watchpoint_event_count"] + 1))),
        ("changed decoded-instance count", "private capture provenance",
         lambda d: preserved(d, lambda x: x["private_capture"].__setitem__("decoded_store_instance_count", 1))),
        ("promoted evidence tier", "evidence tiers",
         lambda d: preserved(d, lambda x: x.__setitem__("evidence_tiers", ["PHYSICAL_SATURN", "STATIC_ANALYSIS", "MEASURED"]))),
        ("reordered evidence tiers", "evidence tiers",
         lambda d: preserved(d, lambda x: x.__setitem__("evidence_tiers", ["STATIC_ANALYSIS", "MAME_TRACE", "MEASURED"]))),
        ("missing evidence tier", "evidence tiers",
         lambda d: preserved(d, lambda x: x.__setitem__("evidence_tiers", ["MAME_TRACE", "STATIC_ANALYSIS"]))),
        ("reversed instruction address space", "address-space attribution",
         lambda d: preserved(d, lambda x: x["address_spaces"].__setitem__("instructions_and_code_targets", "program"))),
        ("reversed program address space", "address-space attribution",
         lambda d: preserved(d, lambda x: x["address_spaces"].__setitem__("rom_operands_and_animation_records", "opcodes"))),
        ("changed HIT typed-exit writer PC", "HIT typed event exit",
         lambda d: preserved(d, lambda x: x["dependencies"]["typed_event_exits"][0].__setitem__("writer_pc", "0x01e88a"))),
        ("changed HIT typed-exit interval", "HIT typed event exit",
         lambda d: preserved(d, lambda x: x["dependencies"]["typed_event_exits"][0].__setitem__("interval_start_frame", 5191))),
        ("changed KO typed-exit writer PC", "KO typed event exit",
         lambda d: preserved(d, lambda x: x["dependencies"]["typed_event_exits"][1].__setitem__("writer_pc", "0x01f254"))),
        ("changed KO typed-exit interval", "KO typed event exit",
         lambda d: preserved(d, lambda x: x["dependencies"]["typed_event_exits"][1].__setitem__("interval_start_frame", 5330))),
        ("hidden top-level trace text", "unknown top-level key",
         lambda d: preserved(d, lambda x: x.__setitem__("auxiliary_evidence", "016526: move.l d0,(28,a6)"))),
        ("hidden nested disassembly text", "unknown key at correlations.hit",
         lambda d: preserved(d, lambda x: x["correlations"]["hit"].__setitem__("operator_note", "016526: move.l d0,(28,a6)"))),
    ]
    for name, invariant, mutate in invariant_controls:
        require_rejection(module, report, mutate, "accepted " + name, invariant, failures)

    if failures:
        raise AssertionError("writer-set correction findings: " + "; ".join(failures))

    dispatch_routine = selected_routine(report, "0x01f6c6")
    if not dispatch_routine["observed_callers"]:
        raise AssertionError("writer dispatch lacks derived caller closure")

    def last_transition_instance(candidate, field, position=0):
        return candidate["writer_instances"][candidate["field_transitions"][field][position]["writer_instance_indices"][-1]]

    controls = [
        # card chapter 3 controls 1-9
        ("remove HIT anim writer binding", "hit animation writer",
         lambda d: d["correlations"]["hit"].__setitem__("anim_writer_instance_index", 0)),
        ("remove KO anim writer binding", "ko animation writer",
         lambda d: d["correlations"]["ko"].__setitem__("anim_writer_instance_index", 0)),
        ("remove selected edge", "selected closure counts", lambda d: d["closure"]["selected_edges"].pop()),
        ("unresolved computed target", "unresolved dependency", lambda d: d["closure"]["unresolved_computed_targets"].append("0x000002")),
        ("unattributed dependency", "unresolved dependency", lambda d: d["closure"]["unattributed_dependencies"].append("0x000002")),
        ("PC outside boundary", "accepted boundary PC membership", lambda d: d["closure"]["selected_pcs"].__setitem__(0, "0xfffffe")),
        ("ROM dependency relabel", "ROM dependency schema", lambda d: d["dependencies"]["rom_data"][1].__setitem__("address_space", "opcodes")),
        ("remove actor field", "actor-field enumeration", lambda d: d["coverage"]["actor_fields"].remove("action")),
        ("shift HIT writer alignment", "writer instance ordering",
         lambda d: d["writer_instances"][d["correlations"]["hit"]["anim_writer_instance_index"]].__setitem__("interval_start_frame", 5191)),
        ("forbidden raw field", "unknown top-level key", lambda d: d.__setitem__("disassembly_text", "forbidden")),
        # seven-field transition/writer binding controls
        ("drop state transition writers", "state transition writer binding",
         lambda d: d["field_transitions"]["state"][0].__setitem__("writer_instance_indices", [])),
        ("drop anim_timer transition writers", "anim_timer transition writer binding",
         lambda d: d["field_transitions"]["anim_timer"][0].__setitem__("writer_instance_indices", [])),
        ("corrupt health before value", "immutable PC/edge/routine binding",
         lambda d: d["field_transitions"]["health"][0].__setitem__("before_value", -999)),
        ("corrupt hit written byte", "hit_value transition reconstruction",
         lambda d: last_transition_instance(d, "hit_value")["written_bytes"].__setitem__("0x2c", 0xAB)),
        ("corrupt anim_record written byte", "anim_record transition reconstruction",
         lambda d: last_transition_instance(d, "anim_record")["written_bytes"].__setitem__("0x1f", 0xAB)),
        ("forge surviving writer PC", "sub_state transition writer binding",
         lambda d: d["field_transitions"]["sub_state"][0].__setitem__("surviving_writer_pcs", ["0x000002"])),
        ("cross-interval writer binding", "action transition writer binding",
         lambda d: d["field_transitions"]["action"][0]["writer_instance_indices"].append(
             d["field_transitions"]["action"][1]["writer_instance_indices"][0])),
        # call-rooted closure controls
        ("owner not call-rooted", "writer owner is not call-rooted",
         lambda d: d["writer_instances"][0].__setitem__("owner_entered_by_call", False)),
        ("owner exit relabel", "owner exit kind", lambda d: d["writer_instances"][0].__setitem__("owner_exit", "interval_end")),
        ("successor PC drift", "immutable PC/edge/routine binding",
         lambda d: d["writer_instances"][0].__setitem__("watchpoint_reported_pc", "0xfffffe")),
        ("HIT bus-event count drift", "hit animation writer",
         lambda d: d["writer_instances"][d["correlations"]["hit"]["anim_writer_instance_index"]].__setitem__("bus_event_count", 1)),
        ("live register binding removed", "immutable PC/edge/routine binding",
         lambda d: d["writer_instances"][0].__setitem__("dynamic_register_binding", {})),
        ("owner outside writer_owner role", "writer owner selection",
         lambda d: d["writer_instances"][0].__setitem__("owner_entry_pc", d["closure"]["task_root"]["entry_pc"])),
        ("writer PC outside owner members", "writer owner membership",
         lambda d: d["writer_instances"][0].__setitem__("owner_entry_pc", next(
             routine["entry_pc"] for routine in d["closure"]["selected_routines"]
             if routine["closure_role"] == "writer_owner"
             and d["writer_instances"][0]["instruction_pc"] not in routine["member_pcs"]))),
        ("task root corruption", "task root binding", lambda d: d["closure"]["task_root"].__setitem__("kind", "asserted")),
        ("corrupted routine entry", "unique routine entries",
         lambda d: selected_routine(d, "0x01f6c6").__setitem__("entry_pc", d["closure"]["selected_routines"][0]["entry_pc"])),
        ("corrupted routine member count", "routine membership", lambda d: selected_routine(d, "0x01f6c6").__setitem__("member_pc_count", 1)),
        ("corrupted routine member hash", "routine membership", lambda d: selected_routine(d, "0x01f6c6").__setitem__("member_pc_sha256", "0" * 64)),
        ("missing observed caller", "immutable PC/edge/routine binding", lambda d: selected_routine(d, "0x01f6c6")["observed_callers"].pop()),
        ("missing routine field write", "routine actor-field attribution",
         lambda d: selected_routine(d, "0x016518")["actor_field_writes"].remove("anim_record")),
        ("changed edge kind", "edge kind", lambda d: d["closure"]["selected_edges"][0].__setitem__("kind", "not_an_edge")),
        ("edge absent from dynamic trace", "edge shape", lambda d: d["closure"]["selected_edges"][0].__setitem__("target", "0x000002")),
        # derived dependency controls
        ("changed target actor binding", "work-RAM dependency schema",
         lambda d: d["dependencies"]["work_ram"][0].__setitem__("address", "0xffa0c0")),
        ("dropped derived byte offset", "work-RAM dependency derivation",
         lambda d: d["dependencies"]["work_ram"][0]["written_byte_offsets"]["anim_timer"].pop()),
        ("out-of-set HIT ROM address", "program dependencies",
         lambda d: d["dependencies"]["rom_data"][1].__setitem__("address", "0x1ffffe")),
        ("ROM dependency purpose drift", "ROM dependency schema",
         lambda d: d["dependencies"]["rom_data"][1].__setitem__("purpose", "asserted_hit_record")),
        ("forged ROM pointer count", "program dependencies",
         lambda d: d["dependencies"]["rom_data"][0].__setitem__("pointer_count", 1)),
        ("changed typed event exit", "HIT typed event exit",
         lambda d: d["dependencies"]["typed_event_exits"][0].__setitem__("event", "enemy_walk_event")),
        ("field dependency PC drop", "field writer dependency closure",
         lambda d: d["dependencies"]["field_writer_dependencies"][3]["writer_pcs"].pop()),
        ("actor reference field drop", "actor-field dependency derivation",
         lambda d: d["dependencies"]["actor_field_references"].pop("state")),
        ("routine actor reference drift", "routine actor-field attribution",
         lambda d: d["closure"]["selected_routines"][0]["actor_field_references"].append("health")),
        ("outgoing control edge drop", "derived counts",
         lambda d: d["dependencies"]["outgoing_control_edges"].pop()),
        ("outgoing control edge retarget", "outgoing edge derivation",
         lambda d: d["dependencies"]["outgoing_control_edges"][0].__setitem__("target", d["closure"]["selected_pcs"][0])),
        ("trace collapse dependency drift", "exclusions",
         lambda d: d["dependencies"]["trace_collapse_dependency"].__setitem__("occurrence_sha256", "0" * 64)),
        ("trace collapse exclusion drift", "exclusions",
         lambda d: d["exclusions"][-1].__setitem__("occurrence_count", d["exclusions"][-1]["occurrence_count"] + 1)),
        ("external callee attribution flip", "external callee attribution",
         lambda d: d["dependencies"]["external_callees"][0].__setitem__("writer_free_outside_selection", False)),
        ("external callee outside members", "external callee attribution",
         lambda d: d["dependencies"]["external_callees"][0]["call_sites"][0].__setitem__("call_site_pc", "0x000002")),
        ("scheduler exit unbinding", "task scheduler exit binding",
         lambda d: d["dependencies"]["task_scheduler_exits"].__setitem__(0, {"callee_entry_pc": "0x000002", "call_sites": []})),
        ("in-window writer exclusion", "exclusions",
         lambda d: d["exclusions"].append({"kind": "in_window_target_writer", "pc": "0x016526", "interval_start_frame": 5190})),
        ("forged exclusion count", "exclusions",
         lambda d: d["exclusions"][3].__setitem__("count", 0)),
        ("missing semantic before/after", "hit semantic binding",
         lambda d: d["correlations"]["hit"]["semantic_changes"][0].__setitem__("after", d["correlations"]["hit"]["semantic_changes"][0]["after"] + 1)),
    ]
    for name, invariant, mutate in controls:
        require_rejection(
            module, report,
            lambda candidate, local=mutate: preserved(candidate, local),
            "production validator accepted mutation: " + name,
            invariant, failures)
    if failures:
        raise AssertionError("writer-set correction findings: " + "; ".join(failures))
    if any(report["window"].get(key) != value for key, value in EXACT_WINDOW.items()):
        raise AssertionError("committed writer-set anchors differ from accepted window")
    print("HIT/KO writer-set committed artifact and correction controls passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
