"""Deterministic report assembly for a reference-engine run.

Reports contain no timestamps, no absolute paths, no dictionary iteration
order, and no floating point beyond fixed rounding, so two runs of the same
inputs produce byte-identical JSON and therefore an identical hash.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from . import saturn_backend as backend
from .evidence import EVIDENCE_LABELS, UNRESOLVED
from .scenario import RunResult

#: Bumped whenever the report schema changes shape.
REPORT_SCHEMA = 1

BOUNDARY = [
    "This is a host-side executable specification, not a Saturn runtime.",
    "It is not a CPS2 emulator and contains no 68000 interpreter.",
    "It does not run on SH-2 and produces no Saturn executable.",
    "Reference-title measurements calibrate the backend and are never budgets.",
    "No measured value here authorises a constant in any implementation lane.",
]


def _pressure_summary(result: RunResult) -> dict[str, Any]:
    per_part = [frame.per_part.command_slots for frame in result.frames]
    per_tile = [frame.per_tile.command_slots for frame in result.frames]
    texture_part = [frame.per_part.texture_bytes for frame in result.frames]
    texture_tile = [frame.per_tile.texture_bytes for frame in result.frames]
    return {
        "note": (
            "Command pressure is reported as a bounded range because the object-part "
            "tile span is an inferred attribute reading. per_part is the floor (one "
            "command per source part); per_tile is the ceiling and is the granularity "
            "the reference capture measures."
        ),
        "per_part": {
            "min_command_slots": min(per_part),
            "max_command_slots": max(per_part),
            "max_command_table_bytes": max(per_part) * 32,
            "max_texture_bytes": max(texture_part),
        },
        "per_tile": {
            "min_command_slots": min(per_tile),
            "max_command_slots": max(per_tile),
            "max_command_table_bytes": max(per_tile) * 32,
            "max_texture_bytes": max(texture_tile),
        },
    }


def _reference_envelope(control_flow: dict[str, Any]) -> dict[str, Any]:
    anchors = control_flow.get("anchors", [])
    if not anchors:
        return {"available": False}
    return {
        "available": True,
        "evidence": "MEASURED",
        "scope": "reference title only; never an implementation budget",
        "anchors": [
            {
                "label": anchor["label"],
                "reachable_slots": anchor["reachable_slot_count"],
                "sequentially_stored_slots": anchor["sequential_slot_count"],
                "stored_nonzero_slots": anchor["stored_nonzero_slots"],
                "drawn_commands": anchor["drawn_command_count"],
            }
            for anchor in anchors
        ],
    }


def _state_flow(result: RunResult) -> list[dict[str, Any]]:
    flow: list[dict[str, Any]] = []
    current: str | None = None
    for frame in result.frames:
        if frame.state != current:
            flow.append({"state": frame.state, "entered_frame": frame.frame, "frames": 0})
            current = frame.state
        flow[-1]["frames"] += 1
    return flow


def _animation_control_flow(result: RunResult, model_programs: dict) -> list[dict[str, Any]]:
    records = []
    for name in sorted(result.state_machine.states):
        state = result.state_machine.states[name]
        program = model_programs[state.program_start]
        records.append(
            {
                "state": name,
                "program": "0x%06X" % program.start,
                "pose_count": len(program.poses),
                "jump_count": len(program.jumps),
                "cycle_frames": program.cycle_frames,
                "loops": program.loops,
                "pose_order": ["0x%06X" % pose.address for pose in program.poses],
                "assembly_order": ["0x%06X" % pose.assembly for pose in program.poses],
                "durations": [pose.duration for pose in program.poses],
            }
        )
    return records


def _object_ordering(result: RunResult, assemblies: dict) -> list[dict[str, Any]]:
    seen: list[int] = []
    for frame in result.frames:
        if frame.assembly not in seen:
            seen.append(frame.assembly)
    return [assemblies[address].to_json() for address in sorted(seen)]


def build_report(result: RunResult, model) -> dict[str, Any]:
    """Assemble the full deterministic report document."""
    claims = result.claims
    label_counts = claims.label_counts()

    document: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "title": result.definition.title,
        "scenario": result.definition.identifier,
        "purpose": (
            "Show how one CPS2 normal attack becomes native Saturn work, with every "
            "field labelled measured, decoded, inferred, adapted or unresolved."
        ),
        "boundary": BOUNDARY,
        "inputs": [item.to_json() for item in result.inputs],
        "layers": {
            "source_semantic": {
                "actor": result.definition.actor,
                "defender": result.definition.defender,
                "state_machine": result.state_machine.to_json(),
                "animation_control_flow": _animation_control_flow(result, model.programs),
                "object_assemblies": _object_ordering(result, model.assemblies),
                "tile_span_agreement": result.tile_agreement,
            },
            "translation": {
                "coordinate_handling": (
                    "Packed source coordinate fields are sign-extended before use; "
                    "part positions are plain signed screen offsets from the actor origin."
                ),
                "flip_handling": (
                    "Actor facing and the part's own source flip combine by exclusive or; "
                    "a mirrored multi-tile part also reverses its tile grid."
                ),
                "ordering_rule": (
                    "Source assembly order is preserved exactly and becomes target list "
                    "position, because the target has no per-command priority field."
                ),
                "palette_rule": (
                    "Palettes cross the boundary as identities, not as target addresses."
                ),
            },
            "saturn_backend": {
                "vdp1_pressure": _pressure_summary(result),
                "reference_envelope": _reference_envelope(model.control_flow),
                "resources": result.ledger.to_json(),
                "phases": [phase.to_json() for phase in result.phases],
                "audio_routing": result.router.to_json(),
                "calibration": {
                    "pmod": "0x%04X" % model.calibration.pmod,
                    "tile_size": [model.calibration.tile_width, model.calibration.tile_height],
                    "tile_bytes": model.calibration.tile_bytes,
                    "color_bank_stride": model.calibration.color_bank_stride,
                    "source": model.calibration.source,
                },
            },
        },
        "run": {
            "frame_count": len(result.frames),
            "state_flow": _state_flow(result),
            "anchor_states": {
                key: result.anchor_states[key] for key in sorted(result.anchor_states)
            },
            "event_histogram": result.trace.kind_histogram(),
            "event_order_is_total": result.trace.is_totally_ordered(),
            "frames": [frame.to_json() for frame in result.frames],
        },
        "semantic_events": result.trace.to_json(),
        "claims": claims.to_json(),
        "evidence_label_counts": {label: label_counts[label] for label in EVIDENCE_LABELS},
        "unresolved_fields": [
            {
                "field": name,
                "probe": claims.claims[name].probe,
                "note": claims.claims[name].note,
            }
            for name in claims.unresolved_names()
        ],
        "prohibited_inferences": sorted(result.definition.prohibited_inferences),
        "required_avp_probe": result.definition.avp_probe,
        "decision_statement": {
            key: result.definition.decision_statement[key]
            for key in sorted(result.definition.decision_statement)
        },
    }
    return document


def serialise(document: dict[str, Any]) -> str:
    """Canonical JSON text: sorted keys, fixed indent, trailing newline."""
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def digest(document: dict[str, Any]) -> str:
    return hashlib.sha256(serialise(document).encode("ascii")).hexdigest()
