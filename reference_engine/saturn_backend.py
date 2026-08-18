"""Saturn backend layer: which piece of Saturn hardware carries each concept.

The backend takes platform-neutral poses and events and states, in Saturn
terms, what carries them: VDP1 command table and texture memory, VDP2 layers,
SH-2 gameplay work, cartridge and work-RAM lifetimes, and SCSP/CDDA routing.

Calibration values default to what the Marvel capture actually measures at the
four normal-hit anchors. Those defaults are MEASURED *on Marvel*; they are not
budgets for any other title, and ``ResourceLedger`` keeps every region separate
precisely so no single number can be mistaken for a whole-machine figure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from . import vdp1
from .evidence import Claim, ClaimSet, adapted, inferred, measured, unresolved
from .source_semantic import TILE_BYTES, TILE_HEIGHT, TILE_WIDTH
from .translation import NeutralPart, NeutralPose

#: One VDP1 command per source object part, drawn at the part's full size.
STRATEGY_PER_PART = "per_part"
#: One VDP1 command per 16x16 tile. This is what the Marvel capture measures.
STRATEGY_PER_TILE = "per_tile"
STRATEGIES = (STRATEGY_PER_PART, STRATEGY_PER_TILE)


class BackendError(ValueError):
    """Raised when a backend decision would need an unmeasured value."""


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Vdp1Calibration:
    """Drawing-mode constants observed in the reference capture."""

    pmod: int = 0x0880
    color_bank_base: int = 0x6000
    color_bank_stride: int = vdp1.COLOR_BANK_STRIDE
    tile_width: int = TILE_WIDTH
    tile_height: int = TILE_HEIGHT
    tile_bytes: int = TILE_BYTES
    system_clip_right: int = 351
    system_clip_bottom: int = 223
    source: str = "reference_engine defaults"

    @classmethod
    def from_control_flow_report(cls, document: dict) -> "Vdp1Calibration":
        """Build calibration from a tracked VDP1 control-flow analysis."""
        observed = document.get("observed_drawing_mode", {})
        pmod_text = observed.get("command_pmod")
        banks = observed.get("color_bank_stride")
        size = observed.get("sprite_size") or [TILE_WIDTH, TILE_HEIGHT]
        return cls(
            pmod=int(pmod_text, 16) if isinstance(pmod_text, str) else cls.pmod,
            color_bank_stride=int(banks) if banks else vdp1.COLOR_BANK_STRIDE,
            tile_width=int(size[0]),
            tile_height=int(size[1]),
            tile_bytes=int(size[0]) * int(size[1]) // 2,
            source=str(document.get("title", "VDP1 control-flow report")),
        )

    def color_bank_for(self, palette_index: int) -> int:
        return self.color_bank_base + palette_index * self.color_bank_stride


# ---------------------------------------------------------------------------
# Texture placement
# ---------------------------------------------------------------------------


@dataclass
class TextureAllocator:
    """Deterministic VDP1 texture placement for modelled parts.

    The layout is ADAPTED: it exists so the model can report real byte
    accounting for a pose, not because any original port places textures here.
    Allocation is first-come by token, so repeated runs place identically.
    """

    base: int = 0x010000
    alignment: int = 0x20
    _offsets: dict[str, int] = field(default_factory=dict)
    _next: int = 0

    def __post_init__(self) -> None:
        self._next = self.base

    def address_for(self, token: str, size_bytes: int) -> int:
        if token in self._offsets:
            return self._offsets[token]
        address = self._next
        self._offsets[token] = address
        stride = (size_bytes + self.alignment - 1) // self.alignment * self.alignment
        self._next = address + stride
        return address

    @property
    def bytes_allocated(self) -> int:
        return self._next - self.base

    @property
    def entries(self) -> int:
        return len(self._offsets)


# ---------------------------------------------------------------------------
# VDP1 command generation
# ---------------------------------------------------------------------------


def _tiles_of(part: NeutralPart, calibration: Vdp1Calibration) -> list[tuple[int, int, int, int]]:
    """Split a part into (tile_index, x, y, sub_token_index) at tile size.

    Flip is applied to the *tile grid* as well as the tile pixels: mirroring a
    multi-tile block requires reversing the tile order, otherwise the block
    reassembles inside out.
    """
    across = max(1, part.width // calibration.tile_width)
    down = max(1, part.height // calibration.tile_height)
    tiles: list[tuple[int, int, int, int]] = []
    index = 0
    for row in range(down):
        for column in range(across):
            source_column = across - 1 - column if part.flip_x else column
            source_row = down - 1 - row if part.flip_y else row
            tiles.append(
                (
                    index,
                    part.x + column * calibration.tile_width,
                    part.y + row * calibration.tile_height,
                    source_row * across + source_column,
                )
            )
            index += 1
    return tiles


def emit_pose_commands(
    pose: NeutralPose,
    *,
    strategy: str = STRATEGY_PER_TILE,
    calibration: Vdp1Calibration | None = None,
    allocator: TextureAllocator | None = None,
    include_prologue: bool = True,
    include_terminator: bool = True,
) -> list[vdp1.Vdp1Command]:
    """Generate a neutral VDP1 command list for one normalised pose.

    Source draw order is preserved exactly: parts are emitted in ``order``, and
    within a part, tiles are emitted row-major. VDP1 has no priority field, so
    list position carries the ordering the source machine expressed.
    """
    if strategy not in STRATEGIES:
        raise BackendError("Unknown VDP1 strategy %r" % (strategy,))
    calibration = calibration or Vdp1Calibration()
    allocator = allocator if allocator is not None else TextureAllocator()

    commands: list[vdp1.Vdp1Command] = []
    if include_prologue:
        commands.append(
            vdp1.system_clip_command(
                0, calibration.system_clip_right, calibration.system_clip_bottom
            )
        )
        commands.append(vdp1.local_coordinate_command(0, 0, 0))

    for part in pose.parts:
        bank = calibration.color_bank_for(part.palette.index)
        if strategy == STRATEGY_PER_PART:
            token = "%s/full" % part.source_token
            size_bytes = part.width * part.height // 2
            commands.append(
                vdp1.normal_sprite_command(
                    0,
                    x=part.x,
                    y=part.y,
                    width=part.width,
                    height=part.height,
                    source_address=allocator.address_for(token, size_bytes),
                    color_bank=bank,
                    flip_x=part.flip_x,
                    flip_y=part.flip_y,
                )
            )
            continue
        for _, x, y, source_index in _tiles_of(part, calibration):
            token = "%s/tile%03d" % (part.source_token, source_index)
            commands.append(
                vdp1.normal_sprite_command(
                    0,
                    x=x,
                    y=y,
                    width=calibration.tile_width,
                    height=calibration.tile_height,
                    source_address=allocator.address_for(token, calibration.tile_bytes),
                    color_bank=bank,
                    flip_x=part.flip_x,
                    flip_y=part.flip_y,
                )
            )

    if include_terminator:
        commands.append(vdp1.draw_end_command(0))
    return vdp1.build_list(commands)


@dataclass(frozen=True)
class Vdp1Pressure:
    """VDP1 cost of one frame, reported as a bounded range."""

    strategy: str
    command_slots: int
    command_table_bytes: int
    texture_bytes: int
    distinct_color_banks: int

    def to_json(self) -> dict[str, object]:
        return {
            "strategy": self.strategy,
            "command_slots": self.command_slots,
            "command_table_bytes": self.command_table_bytes,
            "texture_bytes": self.texture_bytes,
            "distinct_color_banks": self.distinct_color_banks,
        }


def measure_pressure(
    pose: NeutralPose,
    *,
    strategy: str = STRATEGY_PER_TILE,
    calibration: Vdp1Calibration | None = None,
) -> Vdp1Pressure:
    """Cost one pose under a strategy, using a private allocator each time."""
    calibration = calibration or Vdp1Calibration()
    allocator = TextureAllocator()
    commands = emit_pose_commands(
        pose, strategy=strategy, calibration=calibration, allocator=allocator
    )
    banks = {
        command.color_control
        for command in commands
        if command.command_type in vdp1.DRAW_COMMANDS and not command.is_end
    }
    return Vdp1Pressure(
        strategy=strategy,
        command_slots=len(commands),
        command_table_bytes=len(commands) * vdp1.SLOT_BYTES,
        texture_bytes=allocator.bytes_allocated,
        distinct_color_banks=len(banks),
    )


# ---------------------------------------------------------------------------
# Resource ledger
# ---------------------------------------------------------------------------


@dataclass
class ResourceRegion:
    """One separately-budgeted Saturn memory or processing region."""

    name: str
    capacity_bytes: int | None
    owner: str
    responsibility: Claim
    #: Bytes that must stay resident for the modelled phase.
    resident_bytes: int = 0
    #: Bytes rewritten every frame.
    per_frame_bytes: int = 0

    def to_json(self) -> dict[str, object]:
        record: dict[str, object] = {
            "name": self.name,
            "owner": self.owner,
            "resident_bytes": self.resident_bytes,
            "per_frame_bytes": self.per_frame_bytes,
            "responsibility": self.responsibility.to_json(),
        }
        if self.capacity_bytes is not None:
            record["capacity_bytes"] = self.capacity_bytes
            record["resident_fraction"] = round(
                self.resident_bytes / self.capacity_bytes, 6
            )
        return record


@dataclass
class ResourceLedger:
    """Every Saturn resource, kept strictly separate.

    A combined total is deliberately not offered. Work RAM, cartridge DRAM,
    VDP1 VRAM, VDP2 VRAM, colour RAM and sound RAM are physically distinct;
    summing them produces a number that describes no real constraint.
    """

    regions: dict[str, ResourceRegion] = field(default_factory=dict)

    def add(self, region: ResourceRegion) -> "ResourceLedger":
        if region.name in self.regions:
            raise BackendError("Duplicate resource region %r" % region.name)
        self.regions[region.name] = region
        return self

    def charge_resident(self, name: str, byte_count: int) -> None:
        self._region(name).resident_bytes += byte_count

    def charge_per_frame(self, name: str, byte_count: int) -> None:
        self._region(name).per_frame_bytes += byte_count

    def _region(self, name: str) -> ResourceRegion:
        if name not in self.regions:
            raise BackendError("Unknown resource region %r" % name)
        return self.regions[name]

    def overcommitted(self) -> list[str]:
        return sorted(
            name
            for name, region in self.regions.items()
            if region.capacity_bytes is not None
            and region.resident_bytes > region.capacity_bytes
        )

    def to_json(self) -> dict[str, object]:
        return {
            "note": (
                "Regions are physically distinct and are never summed into a "
                "single machine total."
            ),
            "regions": [self.regions[name].to_json() for name in sorted(self.regions)],
            "overcommitted": self.overcommitted(),
        }


def default_ledger() -> ResourceLedger:
    """The Saturn regions this model tracks, with their responsibility claims."""
    ledger = ResourceLedger()
    ledger.add(
        ResourceRegion(
            "vdp1_command_table",
            capacity_bytes=None,
            owner="VDP1",
            responsibility=measured(
                "One 32-byte command slot per drawn part; the list is rebuilt per frame",
                source="data/mshvsf_saturn_vdp1_control_flow.json",
                note="Marvel reaches 296-334 slots at the four normal-hit anchors",
            ),
        )
    )
    ledger.add(
        ResourceRegion(
            "vdp1_texture",
            capacity_bytes=512 * 1024,
            owner="VDP1",
            responsibility=measured(
                "Character pixels referenced by CMDSRCA, shared across frames",
                source="data/mshvsf_saturn_vdp1_control_flow.json",
                note="Command table and textures share the same 512 KiB VDP1 VRAM",
            ),
        )
    )
    ledger.add(
        ResourceRegion(
            "vdp2_vram",
            capacity_bytes=512 * 1024,
            owner="VDP2",
            responsibility=measured(
                "Scrolling background layers; byte-identical across the combat window",
                source="data/mshvsf_saturn_runtime_memory.json",
                note="Stage residency is stable during combat; load-time ownership is separate",
            ),
        )
    )
    ledger.add(
        ResourceRegion(
            "vdp2_color_ram",
            capacity_bytes=4 * 1024,
            owner="VDP2",
            responsibility=measured(
                "16-colour banks addressed by CMDCOLR; every referenced bank is populated",
                source="data/mshvsf_saturn_vdp2_scsp.json",
                note="This is where colour-bank sprites actually spend memory",
            ),
        )
    )
    ledger.add(
        ResourceRegion(
            "work_ram_low",
            capacity_bytes=1024 * 1024,
            owner="SH-2",
            responsibility=measured(
                "Small per-frame gameplay mutation; 2-8 changed pages per transition",
                source="data/mshvsf_saturn_runtime_memory.json",
                note="Which structures live here is unresolved",
            ),
        )
    )
    ledger.add(
        ResourceRegion(
            "work_ram_high",
            capacity_bytes=1024 * 1024,
            owner="SH-2",
            responsibility=measured(
                "Principal gameplay state; 39-42 changed pages per transition",
                source="data/mshvsf_saturn_runtime_memory.json",
                note="Actor, health and collision fields are not yet located inside it",
            ),
        )
    )
    ledger.add(
        ResourceRegion(
            "cartridge_dram",
            capacity_bytes=4 * 1024 * 1024,
            owner="expansion cartridge",
            responsibility=measured(
                "Byte-identical through the whole combat window",
                source="data/mshvsf_saturn_runtime_memory.json",
                note="Stable residency only; allocation and lifetime remain unresolved",
            ),
        )
    )
    ledger.add(
        ResourceRegion(
            "sound_ram",
            capacity_bytes=512 * 1024,
            owner="SCSP",
            responsibility=measured(
                "A refilled mixed-audio buffer: five changed pages on every transition "
                "while the SCSP slot registers stay identical",
                source="data/mshvsf_saturn_vdp2_scsp.json",
                note="Which refill region carries which cue is unresolved",
            ),
        )
    )
    return ledger


# ---------------------------------------------------------------------------
# Phase residency
# ---------------------------------------------------------------------------


@dataclass
class PhaseResidency:
    """What a phase loads, what it keeps, and what it retires.

    Modelled so the eventual native runtime has somewhere to state lifetimes
    instead of implying that everything is permanently resident.
    """

    phase: str
    loads: list[str] = field(default_factory=list)
    retains: list[str] = field(default_factory=list)
    retires: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "loads": sorted(self.loads),
            "retains": sorted(self.retains),
            "retires": sorted(self.retires),
        }


# ---------------------------------------------------------------------------
# Audio routing
# ---------------------------------------------------------------------------

#: A slot keyed per game event. Not what the reference capture shows.
TRANSPORT_SCSP_PCM = "SCSP_PCM_SLOT_PER_EVENT"
#: A small static slot set playing a buffer a sound program refills. This is
#: what the reference capture is consistent with.
TRANSPORT_SCSP_STREAM = "SCSP_MIXED_STREAM"
TRANSPORT_CDDA = "CDDA"
TRANSPORT_UNRESOLVED = "UNRESOLVED"


@dataclass
class AudioRouter:
    """Maps abstract audio cue categories onto a Saturn transport."""

    routes: dict[str, str] = field(default_factory=dict)

    def route(self, category: str) -> str:
        return self.routes.get(category, TRANSPORT_UNRESOLVED)

    def to_json(self) -> dict[str, object]:
        return {
            "routes": {key: self.routes[key] for key in sorted(self.routes)},
            "default": TRANSPORT_UNRESOLVED,
        }


def default_audio_router() -> AudioRouter:
    """Route cues the way the reference measurement supports.

    Gameplay cues go to the mixed-stream transport rather than to a per-event
    slot, because across all four anchors only three SCSP slots hold any
    register content and none of their registers change, while sound RAM moves
    by roughly 16 KiB per transition.
    """
    return AudioRouter(
        routes={
            "attack_swing": TRANSPORT_SCSP_STREAM,
            "impact": TRANSPORT_SCSP_STREAM,
            "music": TRANSPORT_CDDA,
        }
    )


def backend_claims() -> ClaimSet:
    """The backend's own architectural claims, each with an evidence label."""
    claims = ClaimSet()
    claims.add(
        "vdp1_draw_granularity",
        measured(
            "Every drawn command is a 16x16 normal sprite",
            source="data/mshvsf_saturn_vdp1_control_flow.json",
            note="1,233 drawn commands across four anchors, no other size present",
        ),
    )
    claims.add(
        "vdp1_control_flow_shape",
        measured(
            "Every reachable command uses JUMP_NEXT; the list is a flat run to a draw-end",
            source="data/mshvsf_saturn_vdp1_control_flow.json",
            note="No jump, call, return or skip mode occurs at any of the four anchors",
        ),
    )
    claims.add(
        "vdp1_color_mode",
        measured(
            "CMDPMOD 0x0880 for every drawn command: colour-bank mode, 16 colours",
            source="data/mshvsf_saturn_vdp1_control_flow.json",
        ),
    )
    claims.add(
        "draw_order_is_priority",
        adapted(
            "Source assembly order becomes VDP1 list position",
            note="VDP1 has no per-command priority field, so list order is the only ordering",
        ),
    )
    claims.add(
        "texture_layout",
        adapted(
            "Textures are placed by a deterministic first-come allocator",
            note="Chosen so byte accounting is reproducible; not an observed layout",
        ),
    )
    claims.add(
        "vdp2_owns_sprite_colour",
        measured(
            "Every VDP1 sprite colour bank resolves into a populated VDP2 colour-RAM bank",
            source="data/mshvsf_saturn_vdp2_scsp.json",
            note=(
                "Colour-bank mode sprites spend a VDP2 colour-RAM budget, not a VDP1 "
                "texture budget; 12 to 14 banks are live per anchor"
            ),
        ),
    )
    claims.add(
        "vdp2_colour_effects_during_combat",
        measured(
            "Colour RAM changes inside the combat window while VDP2 VRAM does not",
            source="data/mshvsf_saturn_vdp2_scsp.json",
            note="16 bytes in one bank at attack start, 35 bytes across three banks at recovery",
        ),
    )
    claims.add(
        "vdp2_layer_assignment",
        unresolved(
            probe=(
                "Use an instrument that can observe VDP2 register writes, such as a "
                "write watchpoint or breakpoint, because the register block itself "
                "reads back as all zeros"
            ),
            note=(
                "MEASURED: the VDP2 register block is entirely zero at all four "
                "anchors, so layer enables, plane maps, priorities and scroll values "
                "cannot be decoded from this capture. The gap is an instrument limit, "
                "not a missing parser"
            ),
        ),
    )
    claims.add(
        "sh2_work_division",
        unresolved(
            probe="Trace master and slave SH-2 program counters across one frame boundary",
            note="No evidence yet separates gameplay, list building and audio driver work",
        ),
    )
    claims.add(
        "cartridge_lifetime",
        unresolved(
            probe="Capture team and stage loading and compare cartridge contents before and after",
            note="A byte-stable combat window cannot show when the cartridge is written",
        ),
    )
    claims.add(
        "scsp_slot_set_is_static",
        measured(
            "Only three of thirty-two SCSP slots hold register content, unchanged across the window",
            source="data/mshvsf_saturn_vdp2_scsp.json",
            note=(
                "The one changing SCSP register byte is the same byte at every "
                "transition while sound RAM moves by roughly 16 KiB"
            ),
        ),
    )
    claims.add(
        "audio_delivery_model",
        inferred(
            "Gameplay audio reaches the DAC as a mixed stream, not one keyed slot per event",
            falsification=(
                "A slot key-on write between the sampled anchors, or an anchor whose "
                "sound RAM is unchanged while audio is audibly playing"
            ),
            source="data/mshvsf_saturn_vdp2_scsp.json",
            note=(
                "Three static slots plus a per-transition sound-RAM refill fits a "
                "continuously-playing buffer; four sampled frames cannot see a write "
                "that happens between them"
            ),
        ),
    )
    claims.add(
        "scsp_cue_attribution",
        unresolved(
            probe=(
                "Trace sound-RAM writes with a write watchpoint across an attack and "
                "an impact in isolation, with a whiff control, and attribute each "
                "refill region to a cue"
            ),
            note=(
                "Slot registers cannot attribute a cue because they do not change; "
                "the evidence lives in the buffer refills, not in the slot set"
            ),
        ),
    )
    return claims
