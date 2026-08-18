"""VDP1 command decoding, control-flow traversal, and generation."""

from __future__ import annotations

import unittest

from reference_engine import vdp1


def _sprite(offset: int, **kwargs) -> vdp1.Vdp1Command:
    defaults = dict(
        x=0, y=0, width=16, height=16, source_address=0x010000, color_bank=0x6000
    )
    defaults.update(kwargs)
    return vdp1.normal_sprite_command(offset, **defaults)


def _with_control(command: vdp1.Vdp1Command, control: int) -> vdp1.Vdp1Command:
    words = list(command.words)
    words[0] = control
    return vdp1.Vdp1Command(offset=command.offset, words=tuple(words))


def _with_link(command: vdp1.Vdp1Command, target: int) -> vdp1.Vdp1Command:
    words = list(command.words)
    words[1] = target >> vdp1.SRCA_SHIFT
    return vdp1.Vdp1Command(offset=command.offset, words=tuple(words))


class DecodeTest(unittest.TestCase):
    def test_control_word_fields_split_correctly(self):
        command = _with_control(_sprite(0), 0x2035)
        self.assertEqual(command.jump_mode, vdp1.JUMP_CALL)
        self.assertEqual(command.command_type, 0x5)
        self.assertTrue(command.flip_x)
        self.assertTrue(command.flip_y)
        self.assertFalse(command.is_end)

    def test_end_bit_is_independent_of_jump_mode(self):
        command = _with_control(_sprite(0), vdp1.END_BIT | 0x1000)
        self.assertTrue(command.is_end)
        self.assertEqual(command.jump_mode, vdp1.JUMP_ASSIGN)

    def test_link_and_source_are_scaled_by_eight(self):
        command = _with_link(_sprite(0, source_address=0x012340), 0x004060)
        self.assertEqual(command.link, 0x004060)
        self.assertEqual(command.source_address, 0x012340)

    def test_size_and_texture_bytes_for_16_colour_mode(self):
        command = _sprite(0, width=32, height=48)
        self.assertEqual((command.width, command.height), (32, 48))
        self.assertEqual(command.color_mode, vdp1.COLOR_MODE_16_BANK)
        self.assertEqual(command.texture_bytes, 32 * 48 // 2)

    def test_coordinates_are_thirteen_bit_signed(self):
        command = _sprite(0, x=-16, y=-8)
        self.assertEqual(command.vertices[0], -16)
        self.assertEqual(command.vertices[1], -8)

    def test_odd_width_is_rejected(self):
        with self.assertRaises(ValueError):
            _sprite(0, width=12)


class TraversalTest(unittest.TestCase):
    def test_flat_jump_next_list_reaches_every_stored_command(self):
        commands = vdp1.build_list([_sprite(0) for _ in range(4)] + [vdp1.draw_end_command(0)])
        vram = vdp1.serialise(commands, size=0x1000)
        walk = vdp1.traverse(vram)
        self.assertTrue(walk.terminated)
        self.assertEqual(walk.stop_reason, "draw_end")
        self.assertEqual(walk.reachable_slot_count, 5)
        self.assertEqual(walk.drawn_command_count, 4)
        self.assertEqual(walk.jump_mode_histogram(), {"JUMP_NEXT": 5})
        self.assertEqual(len(walk.links_followed), 0)

    def test_jump_assign_skips_stored_commands_so_counts_diverge(self):
        """The gate case: stored order and reachable order must not be conflated."""
        slots = [_sprite(i * vdp1.SLOT_BYTES) for i in range(6)]
        # Slot 0 jumps straight to slot 4, so slots 1-3 are stored but unreachable.
        slots[0] = _with_link(
            _with_control(slots[0], (vdp1.JUMP_ASSIGN << 12)), 4 * vdp1.SLOT_BYTES
        )
        slots[5] = vdp1.draw_end_command(5 * vdp1.SLOT_BYTES)
        vram = vdp1.serialise(slots, size=0x1000)

        walk = vdp1.traverse(vram)
        stored = vdp1.sequential_scan(vram)

        self.assertEqual(walk.reachable_slot_count, 3)  # slots 0, 4, 5
        self.assertEqual(len(stored), 6)
        self.assertNotEqual(walk.reachable_slot_count, len(stored))
        self.assertEqual(
            [command.offset for command in walk.visited],
            [0, 4 * vdp1.SLOT_BYTES, 5 * vdp1.SLOT_BYTES],
        )
        self.assertEqual(len(walk.links_followed), 1)
        self.assertEqual(walk.links_followed[0][2], "JUMP_ASSIGN")

    def test_call_and_return_resume_after_the_call_site(self):
        slots = [_sprite(i * vdp1.SLOT_BYTES) for i in range(6)]
        slots[0] = _with_link(
            _with_control(slots[0], (vdp1.JUMP_CALL << 12)), 3 * vdp1.SLOT_BYTES
        )
        slots[3] = _with_control(slots[3], (vdp1.JUMP_RETURN << 12))
        slots[2] = vdp1.draw_end_command(2 * vdp1.SLOT_BYTES)
        vram = vdp1.serialise(slots, size=0x1000)

        walk = vdp1.traverse(vram)
        self.assertEqual(
            [command.offset // vdp1.SLOT_BYTES for command in walk.visited], [0, 3, 1, 2]
        )
        self.assertTrue(walk.terminated)
        self.assertEqual(walk.anomalies, [])

    def test_unmatched_return_is_reported_not_silently_ignored(self):
        slots = [_sprite(0), _sprite(vdp1.SLOT_BYTES)]
        slots[0] = _with_control(slots[0], (vdp1.JUMP_RETURN << 12))
        vram = vdp1.serialise(slots, size=0x1000)
        walk = vdp1.traverse(vram)
        self.assertEqual(walk.stop_reason, "unmatched_return")
        self.assertFalse(walk.terminated)
        self.assertTrue(any("no saved return" in note for note in walk.anomalies))

    def test_skip_modes_route_control_flow_but_are_not_drawn(self):
        slots = [_sprite(i * vdp1.SLOT_BYTES) for i in range(3)]
        slots[0] = _with_control(slots[0], (vdp1.SKIP_NEXT << 12))
        slots[2] = vdp1.draw_end_command(2 * vdp1.SLOT_BYTES)
        vram = vdp1.serialise(slots, size=0x1000)
        walk = vdp1.traverse(vram)
        self.assertEqual(walk.reachable_slot_count, 3)
        self.assertEqual(walk.skipped_command_count, 1)
        self.assertEqual(walk.drawn_command_count, 1)

    def test_self_referencing_link_is_reported_as_a_loop(self):
        slots = [_sprite(0)]
        slots[0] = _with_link(_with_control(slots[0], (vdp1.JUMP_ASSIGN << 12)), 0)
        vram = vdp1.serialise(slots, size=0x1000)
        walk = vdp1.traverse(vram)
        self.assertEqual(walk.stop_reason, "loop_detected")
        self.assertFalse(walk.terminated)

    def test_link_outside_the_image_stops_the_walk(self):
        slots = [_sprite(0)]
        slots[0] = _with_link(_with_control(slots[0], (vdp1.JUMP_ASSIGN << 12)), 0x7FFE0)
        vram = vdp1.serialise(slots, size=0x1000)
        walk = vdp1.traverse(vram)
        self.assertEqual(walk.stop_reason, "out_of_range")

    def test_non_slot_aligned_link_is_flagged(self):
        slots = [_sprite(0), _sprite(vdp1.SLOT_BYTES)]
        slots[0] = _with_link(_with_control(slots[0], (vdp1.JUMP_ASSIGN << 12)), 0x28)
        vram = vdp1.serialise(slots, size=0x1000)
        walk = vdp1.traverse(vram)
        self.assertTrue(any("non-slot address" in note for note in walk.anomalies))


class StoredExtentTest(unittest.TestCase):
    def test_residue_past_the_terminator_is_counted_separately(self):
        live = vdp1.build_list([_sprite(0), vdp1.draw_end_command(0)])
        residue = [_sprite(offset) for offset in (2 * vdp1.SLOT_BYTES, 3 * vdp1.SLOT_BYTES)]
        vram = vdp1.serialise(live + residue, size=0x1000)

        walk = vdp1.traverse(vram)
        self.assertEqual(walk.reachable_slot_count, 2)
        self.assertEqual(vdp1.stored_nonzero_slots(vram), 4)

    def test_stored_extent_stops_at_the_first_zero_slot(self):
        commands = [_sprite(0), _sprite(2 * vdp1.SLOT_BYTES)]
        vram = vdp1.serialise(commands, size=0x1000)
        self.assertEqual(vdp1.stored_nonzero_slots(vram), 1)


class TextureAndPaletteTest(unittest.TestCase):
    def test_texture_spans_merge_adjacent_references(self):
        commands = vdp1.build_list(
            [
                _sprite(0, source_address=0x010000),
                _sprite(0, source_address=0x010080),
                _sprite(0, source_address=0x020000),
                vdp1.draw_end_command(0),
            ]
        )
        walk = vdp1.traverse(vdp1.serialise(commands, size=0x1000))
        self.assertEqual(
            walk.texture_spans(), [(0x010000, 0x010100), (0x020000, 0x020080)]
        )
        self.assertEqual(walk.texture_bytes_referenced(), 0x180)

    def test_distinct_colour_banks_are_collected(self):
        commands = vdp1.build_list(
            [
                _sprite(0, color_bank=0x6000),
                _sprite(0, color_bank=0x6010),
                _sprite(0, color_bank=0x6000),
                vdp1.draw_end_command(0),
            ]
        )
        walk = vdp1.traverse(vdp1.serialise(commands, size=0x1000))
        self.assertEqual(walk.color_banks(), [0x6000, 0x6010])

    def test_flip_survives_a_generate_serialise_traverse_round_trip(self):
        commands = vdp1.build_list(
            [
                _sprite(0, flip_x=True),
                _sprite(0, flip_y=True),
                _sprite(0, flip_x=True, flip_y=True),
                _sprite(0),
                vdp1.draw_end_command(0),
            ]
        )
        walk = vdp1.traverse(vdp1.serialise(commands, size=0x1000))
        self.assertEqual(
            walk.flip_histogram(), {"NONE": 1, "FLIP_X": 1, "FLIP_Y": 1, "FLIP_XY": 1}
        )

    def test_size_histogram_reports_one_key_per_distinct_size(self):
        commands = vdp1.build_list(
            [_sprite(0), _sprite(0), _sprite(0, width=32), vdp1.draw_end_command(0)]
        )
        walk = vdp1.traverse(vdp1.serialise(commands, size=0x1000))
        self.assertEqual(walk.size_histogram(), {"16x16": 2, "32x16": 1})


if __name__ == "__main__":
    unittest.main()
