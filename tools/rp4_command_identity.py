#!/usr/bin/env python3
"""Identity, comparison and source joining for captured VDP1 commands (pure).

The RP4 question is whether the Saturn's *final* VDP1 command sequence
carries the CPS2 object order. Answering it needs an identity for a
command that is stable across two builds, and a way to say which source
object a final command came from.

Two decisions matter here.

**`srca` is not identity.** The tile sprite pool is an LRU, so a texture
lands at whatever VDP1 address is free when its tile is first drawn.
Change the emission order and every texture address moves even when the
drawing is identical - which is exactly what the earlier sorted
reverse/forward experiment saw. Identity is therefore the command kind,
CMDPMOD, CMDCOLR, CMDSIZE, the vertex, the flip bits, and a SHA-256 of
the *texture bytes themselves*.

**A witness is only usable when it joins uniquely.** Two source objects
can emit byte-identical commands - the street repeats tiles - and then no
evidence in the final list can say which one won. Those are reported as
ambiguous and excluded, never resolved by picking the nearer index.

Nothing in this module decides an RP4 status. It measures relationships;
`tools/verify_rp4_saturn_controls.py` scores them.
"""
from __future__ import annotations

from collections import Counter

#: The fields that make a command comparable between two builds.
IDENTITY_FIELDS = ("kind", "pmod", "colr", "size", "xa", "ya",
                   "flip_x", "flip_y", "texture_sha256")

#: CMDPMOD bits 5-3 select the colour mode; these are the bits-per-pixel
#: each supported mode costs. Modes 6 and 7 are not defined for the
#: normal-sprite command and are refused rather than guessed.
COLOR_MODE_BITS = {0: 4, 1: 4, 2: 8, 3: 8, 4: 8, 5: 16}

FLIP_X_BIT = 0x0010
FLIP_Y_BIT = 0x0020

COMMAND_NAMES = {
    0x0: "NORMAL_SPRITE", 0x1: "SCALED_SPRITE", 0x2: "DISTORTED_SPRITE",
    0x3: "DISTORTED_SPRITE_ALT", 0x4: "POLYGON", 0x5: "POLYLINE",
    0x6: "LINE", 0x7: "POLYLINE_ALT", 0x8: "USER_CLIP",
    0x9: "SYSTEM_CLIP", 0xA: "LOCAL_COORDINATE",
}

SPRITE_KINDS = ("NORMAL_SPRITE", "SCALED_SPRITE", "DISTORTED_SPRITE",
                "DISTORTED_SPRITE_ALT")


class CaptureRejected(ValueError):
    """A capture or comparison that cannot support a verdict."""


def texture_byte_count(width: int, height: int, color_mode: int) -> int:
    """Bytes the texture occupies, from CMDSIZE and the colour mode.

    Derived, never assumed: a wrong byte count would hash the wrong
    bytes and make two different textures look equal.
    """
    if color_mode not in COLOR_MODE_BITS:
        raise CaptureRejected(
            "unsupported VDP1 colour mode %r; refusing to guess a texture "
            "byte count" % (color_mode,))
    if width <= 0 or height <= 0:
        raise CaptureRejected("non-positive texture size %dx%d" % (width, height))
    return width * height * COLOR_MODE_BITS[color_mode] // 8


def _as_int(value) -> int:
    if isinstance(value, str):
        return int(value, 16) if value.startswith("0x") else int(value)
    return int(value)


def normalise_command(record: dict) -> dict:
    """Accept both the original v0 capture shape and the v1 shape.

    The committed RED captures predate texture hashing and store their
    words as hex strings without a decoded kind or flip bits. Those are
    derived here from CMDCTRL so the stronger instrument can still be
    run against the committed evidence.
    """
    out = dict(record)
    if "kind" not in out and "ctrl" in out:
        control = _as_int(out["ctrl"])
        out["kind"] = COMMAND_NAMES.get(control & 0xF,
                                        "UNDEFINED_%X" % (control & 0xF))
        out["flip_x"] = bool(control & FLIP_X_BIT)
        out["flip_y"] = bool(control & FLIP_Y_BIT)
    for field in ("pmod", "colr", "size", "srca", "xa", "ya"):
        if field in out:
            out[field] = _as_int(out[field])
    return out


def command_identity(record: dict, require_texture_hash: bool = True) -> tuple:
    """The comparable identity of one command, excluding its texture address.

    System-clip, user-clip and local-coordinate commands carry no
    geometry or texture of their own, so they are identified by kind and
    compared as a separate sequence by `state_signature`; only drawing
    commands must present the full identity.
    """
    command = normalise_command(record)
    is_draw = command.get("kind") in SPRITE_KINDS or "xa" in command
    missing = [f for f in IDENTITY_FIELDS
               if f not in command and f != "texture_sha256"]
    if missing and is_draw:
        raise CaptureRejected(
            "command %r lacks identity fields %s" % (command.get("index"),
                                                     sorted(missing)))
    for field in missing:
        command[field] = None
    if "texture_sha256" not in command:
        if require_texture_hash and command["kind"] in SPRITE_KINDS:
            raise CaptureRejected(
                "sprite command %r has no texture hash, so two different "
                "textures would compare equal" % (command.get("index"),))
        command["texture_sha256"] = None
    return tuple(command[field] for field in IDENTITY_FIELDS)


def state_signature(commands) -> list:
    """The clip / local-coordinate commands, in order.

    These set up the coordinate frame every sprite is drawn in. If they
    move or change, a sprite comparison is no longer like for like, so
    they are checked as their own sequence rather than folded into the
    sprite identity multiset.
    """
    return [(c.get("kind"), c.get("ctrl")) for c in commands
            if c.get("kind") in ("USER_CLIP", "SYSTEM_CLIP",
                                 "LOCAL_COORDINATE")]


def identity_list(commands, require_texture_hash: bool = True) -> list:
    return [command_identity(c, require_texture_hash) for c in commands]


def compare_captures(baseline, variant, require_texture_hash: bool = True) -> dict:
    """Relate two final command sequences.

    ``order_preserved_fraction`` is computed only over identities that
    occur exactly once on both sides, because a repeated identity has no
    well-defined counterpart.
    """
    b = identity_list(baseline, require_texture_hash)
    v = identity_list(variant, require_texture_hash)
    b_counts, v_counts = Counter(b), Counter(v)
    unique = [p for p in set(b) & set(v)
              if b_counts[p] == 1 and v_counts[p] == 1]
    pairs = sorted((b.index(p), v.index(p)) for p in unique)
    preserved = sum(1 for i in range(len(pairs))
                    for j in range(i + 1, len(pairs))
                    if pairs[i][1] < pairs[j][1])
    total = len(pairs) * (len(pairs) - 1) // 2
    return {
        "baseline_command_count": len(b),
        "variant_command_count": len(v),
        "same_state_commands": (state_signature(baseline) ==
                                state_signature(variant)),
        "same_command_count": len(b) == len(v),
        "same_identity_multiset": b_counts == v_counts,
        "same_draw_order": b == v,
        "exactly_reversed": len(b) > 1 and b == v[::-1],
        "comparable_commands": len(unique),
        "ambiguous_identities": sum(1 for c in b_counts.values() if c > 1),
        "order_preserving_pairs": preserved,
        "comparable_pairs": total,
        "order_preserved_fraction": round(preserved / total, 6) if total else None,
    }


def join_source_groups(groups, commands, require_texture_hash: bool = True) -> dict:
    """Join decoded source object groups to final command indices.

    A group joins only when every identity it predicts occurs exactly
    once in the final list. Anything else is ambiguous and excluded: the
    street repeats tiles, so guessing here would manufacture a witness.
    """
    final = identity_list(commands, require_texture_hash)
    counts = Counter(final)
    by_slot = {}
    unique = ambiguous = 0
    for group in groups:
        identities = list(group["identities"])
        if identities and all(counts[i] == 1 for i in identities):
            indices = sorted(final.index(i) for i in identities)
            by_slot[group["slot"]] = {"final_indices": indices,
                                      "unique": True}
            unique += 1
        else:
            by_slot[group["slot"]] = {
                "final_indices": [],
                "unique": False,
                "reason": "identity occurs %s times in the final list"
                          % sorted({counts[i] for i in identities}),
            }
            ambiguous += 1
    return {
        "by_slot": by_slot,
        "unique_groups": unique,
        "ambiguous_groups": ambiguous,
        "total_groups": len(groups),
    }


def witness_direction(joined: dict, earlier_slot, later_slot) -> str:
    """Where the earlier CPS2 object-RAM entry landed in final VDP1 order.

    CPS2 draws the earlier object-RAM entry on top; VDP1 draws later
    commands on top. Parity therefore requires the earlier CPS entry to
    appear LATER in the final command list.
    """
    earlier = joined["by_slot"].get(earlier_slot)
    later = joined["by_slot"].get(later_slot)
    if not earlier or not later or not earlier["unique"] or not later["unique"]:
        return "not_uniquely_joinable"
    if earlier_slot == later_slot:
        return "not_uniquely_joinable"
    if min(earlier["final_indices"]) > max(later["final_indices"]):
        return "earlier_cps_entry_later_in_vdp1"
    if max(earlier["final_indices"]) < min(later["final_indices"]):
        return "earlier_cps_entry_earlier_in_vdp1"
    return "interleaved"


def require_matching_provenance(expected: dict, actual: dict) -> None:
    """Refuse a capture taken against different inputs than the build."""
    for field in ("fixture_sha256", "elf_sha256", "iso_sha256"):
        if field in expected and expected[field] != actual.get(field):
            raise CaptureRejected(
                "stale %s: capture recorded %r but the build is %r"
                % (field, actual.get(field), expected[field]))


def require_distinct_builds(baseline_sha256: str, variant_sha256: str) -> None:
    """A build compared against itself cannot demonstrate anything."""
    if baseline_sha256 == variant_sha256:
        raise CaptureRejected(
            "baseline and variant are the same build (%s): a build compared "
            "against itself proves nothing" % baseline_sha256[:16])
