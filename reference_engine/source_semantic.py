"""Source semantic layer: what a CPS2 game *means*, before any Saturn choice.

Records here describe the original machine's own representation -- animation
script programs, sprite assemblies, ordered object parts, actor states and
their transitions, and abstract interaction events. Nothing in this module may
mention VDP1, VDP2, SCSP, or a Saturn address.

The concrete field layouts are the ones proven by this repository's own
decoders and recorded in tracked JSON:

* a 16-byte animation pose record (duration, flags, assembly pointer, tail)
  with a 4-byte jump record, from ``data/avsp_animation_scripts.json``;
* a selector-6 sprite assembly (selector, budget, count, offset-index,
  origin-x, origin-y, then ``count`` (code, attribute, layout-adjust) triples).

Two field readings are marked INFERRED and carry their falsification here
rather than in prose: the object-part tile span and the palette index, both
derived from the CPS2 attribute word.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

#: An animation pose record is 16 bytes; the updater advances by that much.
POSE_RECORD_BYTES = 16
#: Flags bit 15 marks the record that redirects control flow.
CONTROL_FLAG_BIT = 0x8000

#: CPS2 attribute word, candidate bit split. Both readings are INFERRED.
ATTRIBUTE_PALETTE_MASK = 0x001F
ATTRIBUTE_FLIP_X_BIT = 0x0020
ATTRIBUTE_FLIP_Y_BIT = 0x0040
ATTRIBUTE_TILES_X_SHIFT = 8
ATTRIBUTE_TILES_Y_SHIFT = 12
ATTRIBUTE_TILE_MASK = 0x000F

#: CPS2 character tiles are 16x16 pixels at 4bpp.
TILE_WIDTH = 16
TILE_HEIGHT = 16
TILE_BITS_PER_PIXEL = 4
TILE_BYTES = TILE_WIDTH * TILE_HEIGHT * TILE_BITS_PER_PIXEL // 8


class SourceModelError(ValueError):
    """Raised when source records are structurally inconsistent."""


# ---------------------------------------------------------------------------
# Animation scripts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PoseRecord:
    """One 16-byte animation pose record."""

    address: int
    duration: int
    flags: int
    assembly: int
    sequence_index: int
    param_byte: int
    #: Tail byte +8 and +9: proven interaction-table selectors.
    interaction_selector_a: int = 0
    interaction_selector_b: int = 0

    @property
    def is_control_record(self) -> bool:
        """Flags bit 15: the updater follows a pointer instead of advancing."""
        return bool(self.flags & CONTROL_FLAG_BIT)

    def to_json(self) -> dict[str, object]:
        return {
            "address": "0x%06X" % self.address,
            "duration": self.duration,
            "sequence_index": self.sequence_index,
            "param_byte": self.param_byte,
            "assembly": "0x%06X" % self.assembly,
            "interaction_selectors": [
                self.interaction_selector_a,
                self.interaction_selector_b,
            ],
        }


@dataclass(frozen=True)
class JumpRecord:
    """A 4-byte pointer record that closes or redirects a program."""

    address: int
    target: int

    def to_json(self) -> dict[str, object]:
        return {"address": "0x%06X" % self.address, "target": "0x%06X" % self.target}


@dataclass
class AnimationProgram:
    """An ordered animation program with explicit control flow.

    ``walk`` is the executable part: it holds each pose for its own duration
    and then follows the program's control flow, exactly as the updater does.
    Zero-duration poses consume their slot without producing a frame.
    """

    start: int
    poses: list[PoseRecord] = field(default_factory=list)
    jumps: list[JumpRecord] = field(default_factory=list)
    status: str = "unknown"

    def __post_init__(self) -> None:
        if not self.poses:
            raise SourceModelError("Animation program 0x%06X has no poses" % self.start)

    @property
    def cycle_frames(self) -> int:
        """Total frames of one full pass through the program."""
        return sum(pose.duration for pose in self.poses)

    @property
    def loops(self) -> bool:
        return any(jump.target == self.start for jump in self.jumps)

    def pose_at_address(self, address: int) -> PoseRecord | None:
        for pose in self.poses:
            if pose.address == address:
                return pose
        return None

    def next_address(self, pose: PoseRecord) -> int:
        """Where control goes after ``pose`` has been held for its duration."""
        following = pose.address + POSE_RECORD_BYTES
        for jump in self.jumps:
            if jump.address == following:
                return jump.target
        return following

    def walk(self, frames: int) -> list[PoseRecord]:
        """Return the pose shown on each of ``frames`` consecutive frames."""
        if frames < 0:
            raise SourceModelError("Frame count must not be negative")
        shown: list[PoseRecord] = []
        pose = self.poses[0]
        held = 0
        guard = 0
        while len(shown) < frames:
            if held >= pose.duration:
                nxt = self.next_address(pose)
                following = self.pose_at_address(nxt)
                if following is None:
                    break
                pose = following
                held = 0
                guard += 1
                if guard > frames + len(self.poses) + 1:
                    raise SourceModelError(
                        "Program 0x%06X spins without producing frames" % self.start
                    )
                continue
            shown.append(pose)
            held += 1
            guard = 0
        return shown

    def to_json(self) -> dict[str, object]:
        return {
            "start": "0x%06X" % self.start,
            "status": self.status,
            "pose_count": len(self.poses),
            "jump_count": len(self.jumps),
            "cycle_frames": self.cycle_frames,
            "loops": self.loops,
            "poses": [pose.to_json() for pose in self.poses],
            "jumps": [jump.to_json() for jump in self.jumps],
        }


# ---------------------------------------------------------------------------
# Sprite assemblies and ordered object parts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ObjectPart:
    """One ordered entry of a CPS2 sprite assembly.

    ``order`` is the entry's position in the assembly and is load-bearing: the
    source machine draws parts in this order, and the translation layer must
    preserve it because VDP1 has no per-command priority field.
    """

    order: int
    code: int
    attribute: int
    layout_adjust: int
    layout_x: int
    layout_y: int

    # -- INFERRED attribute readings ---------------------------------------
    @property
    def tiles_x(self) -> int:
        """Candidate horizontal tile span. INFERRED from attribute bits 8-11."""
        return ((self.attribute >> ATTRIBUTE_TILES_X_SHIFT) & ATTRIBUTE_TILE_MASK) + 1

    @property
    def tiles_y(self) -> int:
        """Candidate vertical tile span. INFERRED from attribute bits 12-15."""
        return ((self.attribute >> ATTRIBUTE_TILES_Y_SHIFT) & ATTRIBUTE_TILE_MASK) + 1

    @property
    def tile_count(self) -> int:
        return self.tiles_x * self.tiles_y

    @property
    def width(self) -> int:
        return self.tiles_x * TILE_WIDTH

    @property
    def height(self) -> int:
        return self.tiles_y * TILE_HEIGHT

    @property
    def palette_index(self) -> int:
        """Candidate 16-colour subpalette. INFERRED from attribute bits 0-4."""
        return self.attribute & ATTRIBUTE_PALETTE_MASK

    @property
    def source_flip_x(self) -> bool:
        """Candidate per-part horizontal flip. INFERRED from attribute bit 5."""
        return bool(self.attribute & ATTRIBUTE_FLIP_X_BIT)

    @property
    def source_flip_y(self) -> bool:
        """Candidate per-part vertical flip. INFERRED from attribute bit 6."""
        return bool(self.attribute & ATTRIBUTE_FLIP_Y_BIT)

    def to_json(self) -> dict[str, object]:
        return {
            "order": self.order,
            "code": "0x%04X" % self.code,
            "attribute": "0x%04X" % self.attribute,
            "layout": [self.layout_x, self.layout_y],
            "tile_span": [self.tiles_x, self.tiles_y],
            "tile_count": self.tile_count,
            "palette_index": self.palette_index,
            "source_flip": [self.source_flip_x, self.source_flip_y],
        }


@dataclass
class SpriteAssembly:
    """A selector-6 assembly: an origin plus an ordered list of object parts."""

    address: int
    selector: int
    budget: int
    origin_x: int
    origin_y: int
    parts: list[ObjectPart] = field(default_factory=list)

    @property
    def part_count(self) -> int:
        return len(self.parts)

    @property
    def tile_total(self) -> int:
        """Sum of the INFERRED per-part tile spans."""
        return sum(part.tile_count for part in self.parts)

    @property
    def budget_matches_tile_total(self) -> bool:
        """Whether ``budget`` equals the INFERRED tile total.

        This is the falsification test for the tile-span reading: if the two
        disagree for an assembly, the attribute bit split is wrong for it.
        """
        return self.budget == self.tile_total

    @property
    def palettes(self) -> list[int]:
        return sorted({part.palette_index for part in self.parts})

    def to_json(self) -> dict[str, object]:
        return {
            "address": "0x%06X" % self.address,
            "selector": self.selector,
            "budget": self.budget,
            "origin": [self.origin_x, self.origin_y],
            "part_count": self.part_count,
            "tile_total": self.tile_total,
            "budget_matches_tile_total": self.budget_matches_tile_total,
            "palettes": self.palettes,
            "parts": [part.to_json() for part in self.parts],
        }


# ---------------------------------------------------------------------------
# Actor state
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActorState:
    """One named actor state and the animation program it plays."""

    name: str
    program_start: int
    #: Whether the state ends on its own (``timed``) or waits (``held``).
    completion: str = "timed"

    def to_json(self) -> dict[str, object]:
        return {
            "name": self.name,
            "program": "0x%06X" % self.program_start,
            "completion": self.completion,
        }


@dataclass(frozen=True)
class StateTransition:
    """A directed transition and the semantic trigger that fires it."""

    source: str
    target: str
    trigger: str

    def to_json(self) -> dict[str, object]:
        return {"from": self.source, "to": self.target, "trigger": self.trigger}


@dataclass
class ActorStateMachine:
    """The state set, transitions, and the state an actor starts in."""

    initial: str
    states: dict[str, ActorState] = field(default_factory=dict)
    transitions: list[StateTransition] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.initial not in self.states:
            raise SourceModelError("Initial state %r is not defined" % self.initial)
        for transition in self.transitions:
            for name in (transition.source, transition.target):
                if name not in self.states:
                    raise SourceModelError(
                        "Transition names undefined state %r" % name
                    )

    def target_for(self, state: str, trigger: str) -> str | None:
        for transition in self.transitions:
            if transition.source == state and transition.trigger == trigger:
                return transition.target
        return None

    def to_json(self) -> dict[str, object]:
        return {
            "initial": self.initial,
            "states": [self.states[name].to_json() for name in sorted(self.states)],
            "transitions": [t.to_json() for t in self.transitions],
        }


# ---------------------------------------------------------------------------
# Abstract interaction events
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CollisionEvent:
    """An abstract contact between an attacker box and a defender box.

    Box extents and damage magnitude are deliberately *not* numbers here. No
    current evidence gives either for the modelled actor, and inventing them
    would be the exact error this engine exists to prevent.
    """

    frame: int
    attacker: str
    defender: str
    #: The pose whose interaction selector was active when contact resolved.
    attacker_pose: int
    #: Opaque token standing in for an unresolved damage magnitude.
    damage_token: str = "UNRESOLVED_DAMAGE_MAGNITUDE"
    outcome: str = "confirmed_hit"

    def to_json(self) -> dict[str, object]:
        return {
            "frame": self.frame,
            "attacker": self.attacker,
            "defender": self.defender,
            "attacker_pose": "0x%06X" % self.attacker_pose,
            "damage": self.damage_token,
            "outcome": self.outcome,
        }


@dataclass(frozen=True)
class AudioEvent:
    """An abstract audio cue raised by gameplay, before any transport choice."""

    frame: int
    cue: str
    category: str

    def to_json(self) -> dict[str, object]:
        return {"frame": self.frame, "cue": self.cue, "category": self.category}


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _as_int(value: object) -> int:
    if isinstance(value, bool):
        raise SourceModelError("Boolean is not a valid numeric field")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 16) if value.lower().startswith("0x") else int(value)
    raise SourceModelError("Cannot read %r as an integer" % (value,))


def load_programs(document: dict) -> dict[int, AnimationProgram]:
    """Build ``AnimationProgram`` objects from a decoded-script JSON document."""
    programs: dict[int, AnimationProgram] = {}
    for entry in document.get("programs", []):
        poses: list[PoseRecord] = []
        jumps: list[JumpRecord] = []
        for record in entry.get("records", []):
            address = _as_int(record["address"])
            if record.get("kind") == "jump":
                jumps.append(JumpRecord(address=address, target=_as_int(record["target"])))
                continue
            poses.append(
                PoseRecord(
                    address=address,
                    duration=_as_int(record["duration"]),
                    flags=_as_int(record.get("word_plus2_raw", 0)),
                    assembly=_as_int(record["assembly"]),
                    sequence_index=_as_int(record.get("sequence_index", 0)),
                    param_byte=_as_int(record.get("param_byte", 0)),
                    interaction_selector_a=_as_int(record.get("tail_byte_8_selector", 0)),
                    interaction_selector_b=_as_int(record.get("tail_byte_9_selector", 0)),
                )
            )
        start = _as_int(entry["start"])
        programs[start] = AnimationProgram(
            start=start, poses=poses, jumps=jumps, status=str(entry.get("status", "unknown"))
        )
    return programs


def load_assemblies(document: dict) -> dict[int, SpriteAssembly]:
    """Build ``SpriteAssembly`` objects from a decoded-script JSON document."""
    assemblies: dict[int, SpriteAssembly] = {}
    for entry in document.get("assemblies", []):
        parts = [
            ObjectPart(
                order=_as_int(item.get("index", index)),
                code=_as_int(item["code"]),
                attribute=_as_int(item["source_attribute"]),
                layout_adjust=_as_int(item.get("layout_adjust", 0)),
                layout_x=_as_int(item.get("layout_x_signed", 0)),
                layout_y=_as_int(item.get("layout_y_signed", 0)),
            )
            for index, item in enumerate(entry.get("entries", []))
        ]
        address = _as_int(entry["address"])
        assemblies[address] = SpriteAssembly(
            address=address,
            selector=_as_int(entry.get("selector", 0)),
            budget=_as_int(entry.get("budget", 0)),
            origin_x=_as_int(entry.get("origin_x", 0)),
            origin_y=_as_int(entry.get("origin_y", 0)),
            parts=parts,
        )
    return assemblies


def tile_span_agreement(assemblies: Iterable[SpriteAssembly]) -> dict[str, object]:
    """Measure how well ``budget`` agrees with the INFERRED tile totals.

    Reported rather than asserted: the agreement rate *is* the confidence in
    the attribute bit split, and disagreements are named individually.
    """
    items: Sequence[SpriteAssembly] = list(assemblies)
    disagreements = [
        {
            "assembly": "0x%06X" % item.address,
            "budget": item.budget,
            "inferred_tile_total": item.tile_total,
            "difference": item.tile_total - item.budget,
        }
        for item in items
        if not item.budget_matches_tile_total
    ]
    return {
        "assemblies": len(items),
        "agreeing": len(items) - len(disagreements),
        "disagreeing": len(disagreements),
        "disagreements": sorted(disagreements, key=lambda d: d["assembly"]),
    }
