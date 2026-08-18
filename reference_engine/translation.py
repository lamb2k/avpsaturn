"""Translation layer: normalise source records into platform-neutral draw items.

This layer is the whole point of the reference engine. It must:

* turn packed, machine-specific coordinates into plain signed screen offsets;
* resolve actor facing into an explicit per-part flip and mirrored position;
* keep the source draw order, because the target has no priority field;
* keep palette identity as an *identity*, not a target colour address.

Nothing here decides a Saturn register value. The Saturn backend does that.
Every mirroring and ordering rule below is ADAPTED: it is this model's stated
convention, not a claim about what any original program does internally.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .source_semantic import ObjectPart, SpriteAssembly, TILE_HEIGHT, TILE_WIDTH

FACING_RIGHT = 1
FACING_LEFT = -1


class TranslationError(ValueError):
    """Raised when a record cannot be normalised without inventing a value."""


def unwrap_signed(value: int, bits: int) -> int:
    """Sign-extend a ``bits``-wide two's complement field.

    CPS2 packs object coordinates into narrow fields (10 bits in the AvP object
    descriptor); reading them as unsigned is a classic source of wrapped
    sprites at screen edges.
    """
    if bits < 2 or bits > 32:
        raise TranslationError("Signed field width %d is out of range" % bits)
    mask = (1 << bits) - 1
    value &= mask
    sign = 1 << (bits - 1)
    return value - (1 << bits) if value & sign else value


@dataclass(frozen=True)
class PaletteIdentity:
    """A palette referred to by identity, not by any target address.

    ``index`` is the source subpalette number. ``entries`` is how many colours
    it holds. Where that identity lands in target colour memory is a backend
    decision, made once, in one place.
    """

    index: int
    entries: int = 16

    def to_json(self) -> dict[str, object]:
        return {"index": self.index, "entries": self.entries}


@dataclass(frozen=True)
class NeutralPart:
    """One ordered, fully-resolved drawable part in screen space.

    ``order`` is preserved from the source assembly. ``x``/``y`` are the
    top-left corner in signed screen coordinates. ``flip_x``/``flip_y`` already
    combine the actor's facing with the part's own source flip.
    """

    order: int
    x: int
    y: int
    width: int
    height: int
    flip_x: bool
    flip_y: bool
    palette: PaletteIdentity
    #: Opaque source identity for the pixels; the backend maps it to storage.
    source_token: str
    tile_count: int

    @property
    def tiles_x(self) -> int:
        return self.width // TILE_WIDTH

    @property
    def tiles_y(self) -> int:
        return self.height // TILE_HEIGHT

    def to_json(self) -> dict[str, object]:
        return {
            "order": self.order,
            "position": [self.x, self.y],
            "size": [self.width, self.height],
            "flip": [self.flip_x, self.flip_y],
            "palette": self.palette.to_json(),
            "source_token": self.source_token,
            "tile_count": self.tile_count,
        }


@dataclass(frozen=True)
class NeutralPose:
    """A complete pose: an ordered part list anchored at an actor position."""

    assembly_address: int
    actor_x: int
    actor_y: int
    facing: int
    parts: tuple[NeutralPart, ...]

    @property
    def part_count(self) -> int:
        return len(self.parts)

    @property
    def tile_total(self) -> int:
        return sum(part.tile_count for part in self.parts)

    @property
    def palettes(self) -> list[int]:
        return sorted({part.palette.index for part in self.parts})

    def bounding_box(self) -> tuple[int, int, int, int]:
        """(left, top, right, bottom) covering every part, exclusive on max."""
        if not self.parts:
            raise TranslationError("An empty pose has no bounding box")
        left = min(part.x for part in self.parts)
        top = min(part.y for part in self.parts)
        right = max(part.x + part.width for part in self.parts)
        bottom = max(part.y + part.height for part in self.parts)
        return left, top, right, bottom

    def to_json(self) -> dict[str, object]:
        left, top, right, bottom = self.bounding_box()
        return {
            "assembly": "0x%06X" % self.assembly_address,
            "actor_position": [self.actor_x, self.actor_y],
            "facing": "right" if self.facing == FACING_RIGHT else "left",
            "part_count": self.part_count,
            "tile_total": self.tile_total,
            "palettes": self.palettes,
            "bounding_box": [left, top, right, bottom],
            "parts": [part.to_json() for part in self.parts],
        }


def normalise_part(
    part: ObjectPart,
    assembly: SpriteAssembly,
    *,
    actor_x: int,
    actor_y: int,
    facing: int,
) -> NeutralPart:
    """Resolve one source object part into screen space.

    Mirroring convention (ADAPTED): a left-facing actor mirrors the whole pose
    about the actor's own origin, so a part's right edge becomes its left edge.
    The part's own source flip is then combined with the facing flip by XOR,
    because flipping twice restores the original orientation.
    """
    if facing not in (FACING_RIGHT, FACING_LEFT):
        raise TranslationError("Facing must be +1 or -1, got %r" % (facing,))

    offset_x = assembly.origin_x + part.layout_x
    offset_y = assembly.origin_y + part.layout_y
    width = part.width
    height = part.height

    if facing == FACING_RIGHT:
        x = actor_x + offset_x
    else:
        x = actor_x - offset_x - width

    return NeutralPart(
        order=part.order,
        x=x,
        y=actor_y + offset_y,
        width=width,
        height=height,
        flip_x=part.source_flip_x != (facing == FACING_LEFT),
        flip_y=part.source_flip_y,
        palette=PaletteIdentity(index=part.palette_index),
        source_token="code:0x%04X" % part.code,
        tile_count=part.tile_count,
    )


def normalise_assembly(
    assembly: SpriteAssembly,
    *,
    actor_x: int = 0,
    actor_y: int = 0,
    facing: int = FACING_RIGHT,
) -> NeutralPose:
    """Normalise a whole assembly, preserving its source draw order."""
    parts = tuple(
        normalise_part(part, assembly, actor_x=actor_x, actor_y=actor_y, facing=facing)
        for part in sorted(assembly.parts, key=lambda p: p.order)
    )
    return NeutralPose(
        assembly_address=assembly.address,
        actor_x=actor_x,
        actor_y=actor_y,
        facing=facing,
        parts=parts,
    )


def draw_order(parts: Iterable[NeutralPart]) -> list[NeutralPart]:
    """Return parts in guaranteed source order.

    The target has no per-command priority field, so list position *is* the
    priority. Sorting is stable on ``order`` alone so that two parts sharing an
    order never swap between runs.
    """
    return sorted(parts, key=lambda part: part.order)


def order_is_preserved(source: SpriteAssembly, pose: NeutralPose) -> bool:
    """Check that normalisation did not reorder or drop any part."""
    expected = [part.order for part in sorted(source.parts, key=lambda p: p.order)]
    actual = [part.order for part in pose.parts]
    return expected == actual


def mirror_pose(pose: NeutralPose) -> NeutralPose:
    """Return the same pose with the opposite facing, recomputed not guessed."""
    raise TranslationError(
        "Re-normalise from the source assembly with the other facing; "
        "mirroring an already-normalised pose loses the actor origin"
    )


def palette_set(poses: Sequence[NeutralPose]) -> list[int]:
    """Every distinct palette identity a sequence of poses needs at once."""
    return sorted({index for pose in poses for index in pose.palettes})
