#!/usr/bin/env python3
"""Failing-first controls for the strengthened RP4 command instrument.

The committed RED is that the sorted reverse/forward pair is inert: the
same commands appear at the same final indices in both builds. An
instrument that only reproduces that result is not yet trustworthy,
because an instrument which could not see *any* difference would report
exactly the same thing. Each control below introduces one specific,
known difference and requires the instrument to notice it.

`srca` is deliberately excluded from identity. Texture addresses move
when the tile pool's upload order changes, which is a consequence of
emission order rather than an independent variable; the texture's
*content* hash is the stable key.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rp4_command_identity import (  # noqa: E402
    IDENTITY_FIELDS,
    CaptureRejected,
    command_identity,
    compare_captures,
    join_source_groups,
    require_distinct_builds,
    require_matching_provenance,
    texture_byte_count,
    witness_direction,
)

EVIDENCE = ROOT / "private-evidence" / "rp4-saturn-controls"


def sprite(index: int, xa: int, ya: int, colr: int = 0x2010,
           texture: str = "t0", flip_x: bool = False,
           flip_y: bool = False) -> dict:
    return {
        "index": index,
        "kind": "NORMAL_SPRITE",
        "pmod": 0x00C0,
        "colr": colr,
        "size": 0x0210,
        "xa": xa,
        "ya": ya,
        "flip_x": flip_x,
        "flip_y": flip_y,
        # srca varies freely and must not participate in identity.
        "srca": 0x1000 + index * 0x80,
        "texture_sha256": texture,
    }


def series(count: int = 8) -> list:
    return [sprite(i, 10 + i, 20 + i, texture="t%d" % i) for i in range(count)]


def renumber(commands: list) -> list:
    return [dict(c, index=i) for i, c in enumerate(commands)]


def check_identity_excludes_srca() -> None:
    a = sprite(0, 10, 20)
    b = dict(a, index=5, srca=0xDEAD)
    assert command_identity(a) == command_identity(b), (a, b)
    assert "srca" not in IDENTITY_FIELDS, IDENTITY_FIELDS
    for field in ("pmod", "colr", "size", "xa", "ya", "flip_x", "flip_y",
                  "texture_sha256", "kind"):
        assert field in IDENTITY_FIELDS, field
    # A sprite command with no texture hash is not identifiable and must be
    # refused rather than silently compared on geometry alone.
    incomplete = dict(a)
    del incomplete["texture_sha256"]
    try:
        command_identity(incomplete)
    except CaptureRejected:
        pass
    else:
        raise AssertionError("a sprite without a texture hash was accepted")


def check_texture_byte_count() -> None:
    # 16x16 at 4bpp colour-bank mode is 128 bytes.
    assert texture_byte_count(16, 16, 0) == 128
    assert texture_byte_count(16, 16, 1) == 128
    assert texture_byte_count(16, 16, 5) == 512
    for bad_mode in (6, 7):
        try:
            texture_byte_count(16, 16, bad_mode)
        except CaptureRejected:
            pass
        else:
            raise AssertionError("unsupported colour mode %d accepted" % bad_mode)


def check_inert_pair_is_reported_inert() -> None:
    """The committed RED must survive the stronger instrument."""
    baseline = json.loads((EVIDENCE / "cap_baseline.json").read_text())
    forward = json.loads((EVIDENCE / "cap_forward.json").read_text())
    result = compare_captures(baseline["commands"], forward["commands"],
                              require_texture_hash=False)
    assert result["same_command_count"], result
    assert result["same_draw_order"], result
    assert not result["exactly_reversed"], result
    assert result["order_preserved_fraction"] == 1.0, result


def check_mutated_texture_is_detected() -> None:
    base = series()
    variant = renumber(copy.deepcopy(base))
    variant[3]["texture_sha256"] = "MUTATED"
    result = compare_captures(base, variant)
    assert not result["same_identity_multiset"], result
    assert not result["same_draw_order"], result


def check_changed_coordinate_is_detected() -> None:
    base = series()
    variant = renumber(copy.deepcopy(base))
    variant[2]["ya"] += 1
    result = compare_captures(base, variant)
    assert not result["same_identity_multiset"], result


def check_changed_palette_selector_is_detected() -> None:
    base = series()
    variant = renumber(copy.deepcopy(base))
    variant[4]["colr"] = 0x4010          # a different sprite-class selector
    result = compare_captures(base, variant)
    assert not result["same_identity_multiset"], result


def check_dropped_and_duplicated_commands_are_detected() -> None:
    base = series()
    dropped = renumber([c for i, c in enumerate(copy.deepcopy(base)) if i != 5])
    result = compare_captures(base, dropped)
    assert not result["same_command_count"], result
    assert result["variant_command_count"] == len(base) - 1, result

    duplicated = renumber(copy.deepcopy(base) + [copy.deepcopy(base[0])])
    result = compare_captures(base, duplicated)
    assert not result["same_command_count"], result
    assert not result["same_identity_multiset"], result


def check_swapped_group_changes_order() -> None:
    """A reversed emission must read as reversed, not merely different."""
    base = series()
    reversed_variant = renumber(list(reversed(copy.deepcopy(base))))
    result = compare_captures(base, reversed_variant)
    assert result["same_identity_multiset"], result
    assert result["same_command_count"], result
    assert not result["same_draw_order"], result
    assert result["exactly_reversed"], result
    assert result["order_preserved_fraction"] == 0.0, result


def check_source_join_and_ambiguity() -> None:
    commands = series(6)
    groups = [
        {"slot": 0, "identities": [command_identity(commands[4])]},
        {"slot": 1, "identities": [command_identity(commands[1])]},
    ]
    joined = join_source_groups(groups, commands)
    assert joined["ambiguous_groups"] == 0, joined
    assert joined["unique_groups"] == 2, joined
    assert joined["by_slot"][0]["final_indices"] == [4], joined
    assert joined["by_slot"][1]["final_indices"] == [1], joined

    # Source order is slot 0 then slot 1; slot 0 landing LATER in the final
    # list is the direction CPS2 requires (earlier entry drawn on top).
    assert witness_direction(joined, earlier_slot=0, later_slot=1) == \
        "earlier_cps_entry_later_in_vdp1"
    assert witness_direction(joined, earlier_slot=1, later_slot=0) == \
        "earlier_cps_entry_earlier_in_vdp1"

    # Two source groups with the same identity cannot be told apart, so the
    # witness must be excluded rather than guessed.
    duplicated = series(6)
    duplicated[2] = dict(duplicated[2], xa=duplicated[5]["xa"],
                         ya=duplicated[5]["ya"],
                         texture_sha256=duplicated[5]["texture_sha256"])
    ambiguous = [{"slot": 0, "identities": [command_identity(duplicated[5])]}]
    result = join_source_groups(ambiguous, duplicated)
    assert result["ambiguous_groups"] == 1, result
    assert result["unique_groups"] == 0, result
    assert witness_direction(result, earlier_slot=0, later_slot=0) == \
        "not_uniquely_joinable"


def check_stale_provenance_is_rejected() -> None:
    good = {"fixture_sha256": "f", "elf_sha256": "e", "iso_sha256": "i"}
    require_matching_provenance(good, dict(good))
    for field in ("fixture_sha256", "elf_sha256", "iso_sha256"):
        stale = dict(good)
        stale[field] = "stale"
        try:
            require_matching_provenance(good, stale)
        except CaptureRejected:
            pass
        else:
            raise AssertionError("stale %s accepted" % field)


def check_self_comparison_is_rejected() -> None:
    """A build compared against itself proves nothing and must not pass."""
    require_distinct_builds("aa" * 32, "bb" * 32)
    try:
        require_distinct_builds("aa" * 32, "aa" * 32)
    except CaptureRejected:
        pass
    else:
        raise AssertionError("a build compared against itself was accepted")


def check_composite_controls_cannot_be_promoted() -> None:
    """Command-order evidence may never promote the two blocked controls."""
    from saturn_control_status import build_saturn_status

    passing_order = {
        "baseline_build_sha256": "aa" * 32,
        "variant_build_sha256": "bb" * 32,
        "fixture_sha256": "cc" * 32,
        "witness_sha256": "dd" * 32,
        "source_frame": 3474,
        "streettest_rel": 0,
        "expected_winner": "later object-RAM entry",
        "observed_winner": "later object-RAM entry",
        # The pixel is unreadable in this instrument, so a command-sequence
        # pass must never come from a pixel claim.
        "witness_pixels_changed": 0,
        "negative_control_pixels_changed": 0,
        "status": "passed",
        "evidence_kind": "final_vdp1_command_sequence",
        "baseline_command_table_sha256": "11" * 32,
        "variant_command_table_sha256": "22" * 32,
        "command_sequence": {
            "same_command_count": True,
            "same_identity_multiset": True,
            "unique_witnesses": 3,
            "witnesses_in_required_direction": 3,
            "sorted_pair_inert": True,
        },
    }
    # The composite controls need a witness PIXEL. Claiming them from
    # command-table evidence is the exact promotion this control forbids.
    forged = {
        "command_order": dict(passing_order),
        "cmdcolr_priority_selector": dict(passing_order),
        "sprite_priority_register_effect": dict(passing_order),
    }
    status = build_saturn_status(forged)
    # The command-order control may pass on this evidence kind...
    assert status["per_control"]["command_order"]["detected"] is True, status
    for blocked in ("cmdcolr_priority_selector",
                    "sprite_priority_register_effect"):
        assert not status["per_control"][blocked]["detected"], status
    assert status["saturn_output_order_status"] != "MEASURED", status


def main() -> None:
    check_identity_excludes_srca()
    check_texture_byte_count()
    check_inert_pair_is_reported_inert()
    check_mutated_texture_is_detected()
    check_changed_coordinate_is_detected()
    check_changed_palette_selector_is_detected()
    check_dropped_and_duplicated_commands_are_detected()
    check_swapped_group_changes_order()
    check_source_join_and_ambiguity()
    check_stale_provenance_is_rejected()
    check_self_comparison_is_rejected()
    check_composite_controls_cannot_be_promoted()
    print("rp4 command identity: every mutation and provenance control holds")


if __name__ == "__main__":
    main()
