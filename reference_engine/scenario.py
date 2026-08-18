"""The executable scenario: one actor, one normal attack, four anchors.

This is the smallest model that exercises every layer end to end:

    decoded animation script  -> pose control flow
    selector-6 assembly       -> ordered object parts
    translation               -> neutral parts, signed coordinates, flip, order
    Saturn backend            -> VDP1 commands, separate resource regions
    trace                     -> deterministic semantic events

It is a host-side specification. It does not run on a Saturn, does not emulate
CPS2, and does not assert any timing value as the original game's timing. State
role bindings and trigger frames are scenario inputs, labelled ADAPTED, and the
report says so.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import saturn_backend as backend
from . import translation, vdp1
from .evidence import Claim, ClaimSet, adapted, decoded, inferred, measured, unresolved
from .source_semantic import (
    ActorState,
    ActorStateMachine,
    AnimationProgram,
    AudioEvent,
    CollisionEvent,
    SourceModelError,
    SpriteAssembly,
    StateTransition,
    load_assemblies,
    load_programs,
    tile_span_agreement,
)
from .trace import EventTrace


class ScenarioError(ValueError):
    """Raised when a scenario is internally inconsistent."""


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class EvidenceInput:
    """One tracked, copyright-safe input file and how it is being used."""

    role: str
    path: str
    sha256: str
    evidence_label: str
    note: str = ""

    def to_json(self) -> dict[str, object]:
        record = {
            "role": self.role,
            "path": self.path,
            "sha256": self.sha256,
            "evidence": self.evidence_label,
        }
        if self.note:
            record["note"] = self.note
        return record


@dataclass
class ScenarioDefinition:
    """A parsed scenario document."""

    identifier: str
    title: str
    actor: str
    defender: str
    inputs: dict[str, str]
    states: list[dict[str, Any]]
    transitions: list[dict[str, str]]
    schedule: list[dict[str, Any]]
    anchors: list[dict[str, Any]]
    audio_cues: list[dict[str, Any]]
    prohibited_inferences: list[str]
    avp_probe: str
    decision_statement: dict[str, str]

    @classmethod
    def load(cls, path: Path) -> "ScenarioDefinition":
        document = json.loads(path.read_text(encoding="utf-8"))
        try:
            return cls(
                identifier=document["id"],
                title=document["title"],
                actor=document["actor"],
                defender=document["defender"],
                inputs=document["inputs"],
                states=document["states"],
                transitions=document["transitions"],
                schedule=document["schedule"],
                anchors=document["anchors"],
                audio_cues=document.get("audio_cues", []),
                prohibited_inferences=document["prohibited_inferences"],
                avp_probe=document["avp_probe"],
                decision_statement=document["decision_statement"],
            )
        except KeyError as error:
            raise ScenarioError("Scenario %s is missing %s" % (path, error)) from error


@dataclass
class FrameReport:
    """Everything the model knows about one frame."""

    frame: int
    state: str
    assembly: int
    pose_address: int
    part_count: int
    tile_total: int
    per_part: backend.Vdp1Pressure
    per_tile: backend.Vdp1Pressure

    def to_json(self) -> dict[str, object]:
        return {
            "frame": self.frame,
            "state": self.state,
            "pose": "0x%06X" % self.pose_address,
            "assembly": "0x%06X" % self.assembly,
            "part_count": self.part_count,
            "tile_total": self.tile_total,
            "vdp1_per_part": self.per_part.to_json(),
            "vdp1_per_tile": self.per_tile.to_json(),
        }


@dataclass
class RunResult:
    """The deterministic output of one scenario run."""

    definition: ScenarioDefinition
    inputs: list[EvidenceInput]
    state_machine: ActorStateMachine
    trace: EventTrace
    frames: list[FrameReport]
    ledger: backend.ResourceLedger
    phases: list[backend.PhaseResidency]
    router: backend.AudioRouter
    claims: ClaimSet
    tile_agreement: dict[str, object]
    anchor_states: dict[str, str] = field(default_factory=dict)


@dataclass
class NormalHitModel:
    """Builds and runs the normal-hit scenario."""

    root: Path
    definition: ScenarioDefinition
    programs: dict[int, AnimationProgram]
    assemblies: dict[int, SpriteAssembly]
    inputs: list[EvidenceInput]
    calibration: backend.Vdp1Calibration
    control_flow: dict[str, Any]

    @classmethod
    def load(cls, root: Path, scenario_path: Path) -> "NormalHitModel":
        definition = ScenarioDefinition.load(scenario_path)
        inputs: list[EvidenceInput] = []

        scripts_rel = definition.inputs["animation_scripts"]
        scripts_path = root / scripts_rel
        if not scripts_path.is_file():
            raise ScenarioError("Missing animation-script input: %s" % scripts_rel)
        scripts = json.loads(scripts_path.read_text(encoding="utf-8"))
        inputs.append(
            EvidenceInput(
                role="animation_scripts",
                path=scripts_rel,
                sha256=sha256_of(scripts_path),
                evidence_label="DECODED",
                note=(
                    "Source-form animation script and selector-6 assembly records, "
                    "decoded by this repository's own decoder from private ROM data"
                ),
            )
        )

        control_flow: dict[str, Any] = {}
        calibration = backend.Vdp1Calibration()
        flow_rel = definition.inputs.get("vdp1_control_flow")
        if flow_rel:
            flow_path = root / flow_rel
            if not flow_path.is_file():
                raise ScenarioError("Missing VDP1 control-flow input: %s" % flow_rel)
            control_flow = json.loads(flow_path.read_text(encoding="utf-8"))
            calibration = backend.Vdp1Calibration.from_control_flow_report(control_flow)
            inputs.append(
                EvidenceInput(
                    role="vdp1_control_flow",
                    path=flow_rel,
                    sha256=sha256_of(flow_path),
                    evidence_label="MEASURED",
                    note=(
                        "Saturn VDP1 drawing mode and control-flow shape measured on the "
                        "reference title; calibration only, never a budget"
                    ),
                )
            )

        video_audio_rel = definition.inputs.get("vdp2_scsp")
        if video_audio_rel:
            video_audio_path = root / video_audio_rel
            if not video_audio_path.is_file():
                raise ScenarioError("Missing VDP2/SCSP input: %s" % video_audio_rel)
            inputs.append(
                EvidenceInput(
                    role="vdp2_scsp",
                    path=video_audio_rel,
                    sha256=sha256_of(video_audio_path),
                    evidence_label="MEASURED",
                    note=(
                        "Colour ownership and SCSP slot activity for the same four "
                        "anchors; responsibility mapping only"
                    ),
                )
            )

        memory_rel = definition.inputs.get("runtime_memory")
        if memory_rel:
            memory_path = root / memory_rel
            if not memory_path.is_file():
                raise ScenarioError("Missing runtime-memory input: %s" % memory_rel)
            inputs.append(
                EvidenceInput(
                    role="runtime_memory",
                    path=memory_rel,
                    sha256=sha256_of(memory_path),
                    evidence_label="MEASURED",
                    note="Per-region residency and change evidence for the four anchors",
                )
            )

        return cls(
            root=root,
            definition=definition,
            programs=load_programs(scripts),
            assemblies=load_assemblies(scripts),
            inputs=inputs,
            calibration=calibration,
            control_flow=control_flow,
        )

    # -- construction -------------------------------------------------------

    def build_state_machine(self) -> ActorStateMachine:
        states: dict[str, ActorState] = {}
        for entry in self.definition.states:
            program = int(entry["program"], 16)
            if program not in self.programs:
                raise ScenarioError(
                    "State %r names program 0x%06X, which is not decoded"
                    % (entry["name"], program)
                )
            states[entry["name"]] = ActorState(
                name=entry["name"],
                program_start=program,
                completion=entry.get("completion", "timed"),
            )
        transitions = [
            StateTransition(source=t["from"], target=t["to"], trigger=t["trigger"])
            for t in self.definition.transitions
        ]
        initial = self.definition.states[0]["name"]
        return ActorStateMachine(initial=initial, states=states, transitions=transitions)

    def _assembly_for(self, address: int) -> SpriteAssembly:
        if address not in self.assemblies:
            raise ScenarioError("Pose references undecoded assembly 0x%06X" % address)
        return self.assemblies[address]

    # -- execution ----------------------------------------------------------

    def run(self) -> RunResult:
        definition = self.definition
        machine = self.build_state_machine()
        trace = EventTrace()
        frames: list[FrameReport] = []
        ledger = backend.default_ledger()
        allocator = backend.TextureAllocator()
        router = backend.default_audio_router()

        schedule = {int(item["frame"]): item for item in definition.schedule}
        total_frames = max(schedule) + int(definition.schedule[-1].get("hold", 1))
        anchors = {int(item["frame"]): item["label"] for item in definition.anchors}
        audio_cues = {int(item["frame"]): item for item in definition.audio_cues}

        state = machine.initial
        state_entry_frame = 0
        previous_assembly: int | None = None
        #: Pose shown on the previous frame; contact is tested against it.
        contact_pose: int | None = None
        anchor_states: dict[str, str] = {}

        trace.add(0, "state_enter", definition.actor, state=state)

        for frame in range(total_frames):
            event = schedule.get(frame)
            if event and frame > 0:
                trigger = event["trigger"]
                target = machine.target_for(state, trigger)
                if target is None:
                    raise ScenarioError(
                        "Trigger %r is not defined for state %r at frame %d"
                        % (trigger, state, frame)
                    )
                trace.add(frame, "input", definition.actor, trigger=trigger)
                trace.add(frame, "state_exit", definition.actor, state=state)
                state = target
                state_entry_frame = frame
                previous_assembly = None
                trace.add(frame, "state_enter", definition.actor, state=state)

            program = self.programs[machine.states[state].program_start]
            shown = program.walk(frame - state_entry_frame + 1)
            if not shown:
                raise ScenarioError(
                    "Program 0x%06X produced no frame at %d" % (program.start, frame)
                )
            pose = shown[-1]
            assembly = self._assembly_for(pose.assembly)

            if assembly.address != previous_assembly:
                trace.add(
                    frame,
                    "pose",
                    definition.actor,
                    assembly="0x%06X" % assembly.address,
                    pose="0x%06X" % pose.address,
                    sequence_index=pose.sequence_index,
                    interaction_selector=pose.interaction_selector_a,
                )
                previous_assembly = assembly.address

            neutral = translation.normalise_assembly(
                assembly, actor_x=0, actor_y=0, facing=translation.FACING_RIGHT
            )
            if not translation.order_is_preserved(assembly, neutral):
                raise ScenarioError(
                    "Normalisation reordered assembly 0x%06X" % assembly.address
                )

            per_part = backend.measure_pressure(
                neutral, strategy=backend.STRATEGY_PER_PART, calibration=self.calibration
            )
            per_tile = backend.measure_pressure(
                neutral, strategy=backend.STRATEGY_PER_TILE, calibration=self.calibration
            )
            backend.emit_pose_commands(
                neutral,
                strategy=backend.STRATEGY_PER_TILE,
                calibration=self.calibration,
                allocator=allocator,
            )

            trace.add(
                frame,
                "render",
                definition.actor,
                command_slots=per_tile.command_slots,
                strategy=backend.STRATEGY_PER_TILE,
            )

            if event and "collision" in event:
                # Contact is resolved from the pose that was on screen when the
                # test ran, not from the reaction pose this frame switches to.
                collision = CollisionEvent(
                    frame=frame,
                    attacker=definition.actor,
                    defender=definition.defender,
                    attacker_pose=contact_pose if contact_pose is not None else pose.address,
                )
                detail = {
                    key: value
                    for key, value in collision.to_json().items()
                    if key != "frame"
                }
                trace.add(frame, "collision", definition.defender, **detail)
                trace.add(
                    frame,
                    "damage",
                    definition.defender,
                    magnitude=collision.damage_token,
                    source=definition.actor,
                )

            cue = audio_cues.get(frame)
            if cue:
                audio = AudioEvent(frame=frame, cue=cue["cue"], category=cue["category"])
                trace.add(
                    frame,
                    "audio",
                    definition.actor,
                    transport=router.route(audio.category),
                    cue=audio.cue,
                    category=audio.category,
                )

            if frame in anchors:
                anchor_states[anchors[frame]] = state

            contact_pose = pose.address
            frames.append(
                FrameReport(
                    frame=frame,
                    state=state,
                    assembly=assembly.address,
                    pose_address=pose.address,
                    part_count=neutral.part_count,
                    tile_total=neutral.tile_total,
                    per_part=per_part,
                    per_tile=per_tile,
                )
            )

        ledger.charge_resident("vdp1_texture", allocator.bytes_allocated)
        peak_slots = max(report.per_tile.command_slots for report in frames)
        ledger.charge_per_frame("vdp1_command_table", peak_slots * vdp1.SLOT_BYTES)
        ledger.charge_resident(
            "vdp2_color_ram",
            len({index for report in frames for index in self._palettes(report)})
            * self.calibration.color_bank_stride
            * 2,
        )

        phases = [
            backend.PhaseResidency(
                phase="normal_hit_window",
                loads=["actor_pose_textures"],
                retains=["actor_pose_textures", "stage_background"],
                retires=[],
            )
        ]

        return RunResult(
            definition=definition,
            inputs=self.inputs,
            state_machine=machine,
            trace=trace,
            frames=frames,
            ledger=ledger,
            phases=phases,
            router=router,
            claims=self._claims(),
            tile_agreement=tile_span_agreement(self.assemblies.values()),
            anchor_states=anchor_states,
        )

    def _palettes(self, report: FrameReport) -> list[int]:
        return self.assemblies[report.assembly].palettes

    def _claims(self) -> ClaimSet:
        claims = backend.backend_claims()
        claims.add(
            "animation_record_format",
            decoded(
                "16-byte pose record: duration, flags, assembly pointer, 8-byte tail",
                source=self.definition.inputs["animation_scripts"],
                note="Flags bit 15 redirects control flow; a 4-byte record closes the loop",
            ),
        )
        claims.add(
            "object_part_order",
            decoded(
                "Selector-6 assemblies list object parts in an explicit draw order",
                source=self.definition.inputs["animation_scripts"],
            ),
        )
        claims.add(
            "attribute_tile_span",
            inferred(
                "Attribute bits 8-11 and 12-15 hold horizontal and vertical tile span",
                falsification=(
                    "An assembly whose declared budget does not equal the summed tile "
                    "span under this bit split; one of 28 already disagrees by two tiles"
                ),
                source=self.definition.inputs["animation_scripts"],
            ),
        )
        claims.add(
            "attribute_palette_index",
            inferred(
                "Attribute bits 0-4 hold the 16-colour subpalette index",
                falsification=(
                    "A pose whose observed colour bank does not follow the low five "
                    "attribute bits"
                ),
                source=self.definition.inputs["animation_scripts"],
            ),
        )
        claims.add(
            "state_role_binding",
            adapted(
                "Scenario names which decoded program plays in which state",
                note=(
                    "Program-to-state roles are not proven; the binding exists so the "
                    "model can run and is not a claim about the source game"
                ),
            ),
        )
        claims.add(
            "trigger_timing",
            adapted(
                "Trigger and contact frames are scenario inputs",
                note="Real attack startup, active and recovery timing is unresolved",
            ),
        )
        claims.add(
            "collision_geometry",
            unresolved(
                probe=(
                    "Decode actor-local hitbox and attack-box records and validate them "
                    "against the game's own debug overlays"
                ),
                note="The model raises an abstract contact event with no box extents",
            ),
        )
        claims.add(
            "damage_magnitude",
            unresolved(
                probe=(
                    "Locate the health field and its writer, then confirm with an "
                    "out-of-range whiff control that the field only moves on contact"
                ),
                note="Damage is carried as an opaque token, never as a number",
            ),
        )
        return claims
