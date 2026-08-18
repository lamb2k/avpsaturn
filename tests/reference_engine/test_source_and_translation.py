"""Animation control flow, object ordering, and coordinate/flip normalisation."""

from __future__ import annotations

import unittest

from reference_engine import translation
from reference_engine.source_semantic import (
    AnimationProgram,
    JumpRecord,
    ObjectPart,
    PoseRecord,
    SourceModelError,
    SpriteAssembly,
    tile_span_agreement,
)


def pose(address: int, duration: int, assembly: int, **kwargs) -> PoseRecord:
    return PoseRecord(
        address=address,
        duration=duration,
        flags=kwargs.get("flags", 0),
        assembly=assembly,
        sequence_index=kwargs.get("sequence_index", 0),
        param_byte=kwargs.get("param_byte", 0),
        interaction_selector_a=kwargs.get("selector_a", 0),
        interaction_selector_b=kwargs.get("selector_b", 0),
    )


def three_pose_loop() -> AnimationProgram:
    """Three poses of 2, 3 and 1 frames, looping back to the first."""
    poses = [
        pose(0x100, 2, 0xA00),
        pose(0x110, 3, 0xA01),
        pose(0x120, 1, 0xA02),
    ]
    return AnimationProgram(
        start=0x100, poses=poses, jumps=[JumpRecord(address=0x130, target=0x100)]
    )


class AnimationControlFlowTest(unittest.TestCase):
    def test_each_pose_is_held_for_exactly_its_duration(self):
        shown = three_pose_loop().walk(6)
        self.assertEqual(
            [record.assembly for record in shown], [0xA00, 0xA00, 0xA01, 0xA01, 0xA01, 0xA02]
        )

    def test_cycle_frames_is_the_sum_of_durations(self):
        self.assertEqual(three_pose_loop().cycle_frames, 6)

    def test_the_program_loops_back_to_its_start(self):
        program = three_pose_loop()
        self.assertTrue(program.loops)
        shown = program.walk(13)
        self.assertEqual(shown[6].assembly, 0xA00)
        self.assertEqual([r.assembly for r in shown[:6]], [r.assembly for r in shown[6:12]])

    def test_next_address_follows_a_jump_record(self):
        program = three_pose_loop()
        self.assertEqual(program.next_address(program.poses[2]), 0x100)
        self.assertEqual(program.next_address(program.poses[0]), 0x110)

    def test_zero_duration_pose_consumes_its_slot_without_a_frame(self):
        program = AnimationProgram(
            start=0x200,
            poses=[pose(0x200, 0, 0xB00), pose(0x210, 2, 0xB01)],
            jumps=[JumpRecord(address=0x220, target=0x200)],
        )
        shown = program.walk(3)
        self.assertEqual([r.assembly for r in shown], [0xB01, 0xB01, 0xB01])

    def test_a_program_that_never_yields_a_frame_is_rejected(self):
        program = AnimationProgram(
            start=0x300,
            poses=[pose(0x300, 0, 0xC00)],
            jumps=[JumpRecord(address=0x310, target=0x300)],
        )
        with self.assertRaises(SourceModelError):
            program.walk(4)

    def test_a_program_without_poses_is_rejected(self):
        with self.assertRaises(SourceModelError):
            AnimationProgram(start=0x400, poses=[], jumps=[])

    def test_walking_a_non_looping_program_stops_at_the_end(self):
        program = AnimationProgram(start=0x500, poses=[pose(0x500, 2, 0xD00)], jumps=[])
        self.assertEqual(len(program.walk(10)), 2)


def part(order: int, attribute: int, x: int, y: int, code: int = 0x1000) -> ObjectPart:
    return ObjectPart(
        order=order, code=code, attribute=attribute, layout_adjust=0, layout_x=x, layout_y=y
    )


def three_part_assembly() -> SpriteAssembly:
    # attribute 0x011B -> 2x1 tiles, palette 27; 0x121B -> 3x2; 0x001B -> 1x1
    return SpriteAssembly(
        address=0xE000,
        selector=6,
        budget=2 + 6 + 1,
        origin_x=-8,
        origin_y=-4,
        parts=[
            part(0, 0x011B, 0, 0),
            part(1, 0x121B, 16, 32),
            part(2, 0x001B, -16, -32),
        ],
    )


class ObjectPartTest(unittest.TestCase):
    def test_attribute_tile_span_and_pixel_size(self):
        item = part(0, 0x121B, 0, 0)
        self.assertEqual((item.tiles_x, item.tiles_y), (3, 2))
        self.assertEqual((item.width, item.height), (48, 32))
        self.assertEqual(item.tile_count, 6)

    def test_attribute_palette_and_flip_bits(self):
        self.assertEqual(part(0, 0x011B, 0, 0).palette_index, 27)
        self.assertTrue(part(0, 0x013B, 0, 0).source_flip_x)
        self.assertTrue(part(0, 0x015B, 0, 0).source_flip_y)

    def test_budget_agreement_is_reported_not_assumed(self):
        good = three_part_assembly()
        self.assertTrue(good.budget_matches_tile_total)

        bad = SpriteAssembly(
            address=0xE100, selector=6, budget=99, origin_x=0, origin_y=0, parts=[part(0, 0x001B, 0, 0)]
        )
        self.assertFalse(bad.budget_matches_tile_total)

        summary = tile_span_agreement([good, bad])
        self.assertEqual(summary["assemblies"], 2)
        self.assertEqual(summary["agreeing"], 1)
        self.assertEqual(summary["disagreements"][0]["assembly"], "0x00E100")


class CoordinateTest(unittest.TestCase):
    def test_sign_extension_of_a_ten_bit_field(self):
        self.assertEqual(translation.unwrap_signed(0x3FF, 10), -1)
        self.assertEqual(translation.unwrap_signed(0x200, 10), -512)
        self.assertEqual(translation.unwrap_signed(0x1FF, 10), 511)
        self.assertEqual(translation.unwrap_signed(0x000, 10), 0)

    def test_sign_extension_is_idempotent_for_in_range_values(self):
        for value in (-3, 0, 7):
            self.assertEqual(translation.unwrap_signed(value, 10), value)

    def test_invalid_field_width_is_rejected(self):
        with self.assertRaises(translation.TranslationError):
            translation.unwrap_signed(0, 1)


class NormalisationTest(unittest.TestCase):
    def test_right_facing_position_is_origin_plus_layout(self):
        assembly = three_part_assembly()
        posed = translation.normalise_assembly(assembly, actor_x=100, actor_y=50)
        first = posed.parts[0]
        self.assertEqual((first.x, first.y), (100 - 8 + 0, 50 - 4 + 0))

    def test_left_facing_mirrors_about_the_actor_origin(self):
        assembly = three_part_assembly()
        right = translation.normalise_assembly(assembly, actor_x=100, actor_y=50)
        left = translation.normalise_assembly(
            assembly, actor_x=100, actor_y=50, facing=translation.FACING_LEFT
        )
        for a, b in zip(right.parts, left.parts):
            # Mirrored right edge becomes the left edge, and y never moves.
            self.assertEqual(b.x, 200 - (a.x + a.width))
            self.assertEqual(a.y, b.y)

    def test_facing_and_source_flip_combine_by_exclusive_or(self):
        assembly = SpriteAssembly(
            address=0xE200,
            selector=6,
            budget=2,
            origin_x=0,
            origin_y=0,
            parts=[part(0, 0x001B, 0, 0), part(1, 0x003B, 0, 0)],
        )
        right = translation.normalise_assembly(assembly)
        left = translation.normalise_assembly(assembly, facing=translation.FACING_LEFT)
        self.assertEqual([p.flip_x for p in right.parts], [False, True])
        self.assertEqual([p.flip_x for p in left.parts], [True, False])

    def test_mirroring_twice_restores_the_original_geometry(self):
        assembly = three_part_assembly()
        once = translation.normalise_assembly(
            assembly, actor_x=0, actor_y=0, facing=translation.FACING_LEFT
        )
        twice = translation.normalise_assembly(
            assembly, actor_x=0, actor_y=0, facing=translation.FACING_RIGHT
        )
        for a, b in zip(once.parts, twice.parts):
            self.assertEqual(a.x, -(b.x + b.width))
            self.assertNotEqual(a.flip_x, b.flip_x)

    def test_draw_order_is_preserved_exactly(self):
        assembly = three_part_assembly()
        posed = translation.normalise_assembly(assembly)
        self.assertTrue(translation.order_is_preserved(assembly, posed))
        self.assertEqual([p.order for p in posed.parts], [0, 1, 2])

    def test_shuffled_source_parts_still_normalise_in_order(self):
        assembly = three_part_assembly()
        assembly.parts = [assembly.parts[2], assembly.parts[0], assembly.parts[1]]
        posed = translation.normalise_assembly(assembly)
        self.assertEqual([p.order for p in posed.parts], [0, 1, 2])
        self.assertTrue(translation.order_is_preserved(assembly, posed))

    def test_palette_identity_crosses_as_an_index_not_an_address(self):
        posed = translation.normalise_assembly(three_part_assembly())
        self.assertEqual(posed.palettes, [27])
        self.assertEqual(posed.parts[0].palette.entries, 16)

    def test_bounding_box_covers_every_part(self):
        posed = translation.normalise_assembly(three_part_assembly(), actor_x=0, actor_y=0)
        left, top, right, bottom = posed.bounding_box()
        self.assertEqual(left, -8 + -16)
        self.assertEqual(top, -4 + -32)
        self.assertEqual(right, -8 + 16 + 48)
        self.assertEqual(bottom, -4 + 32 + 32)

    def test_invalid_facing_is_rejected(self):
        with self.assertRaises(translation.TranslationError):
            translation.normalise_assembly(three_part_assembly(), facing=0)

    def test_tile_total_matches_the_sum_of_part_tile_counts(self):
        posed = translation.normalise_assembly(three_part_assembly())
        self.assertEqual(posed.tile_total, 9)


if __name__ == "__main__":
    unittest.main()
