"""Saturn backend command generation, separate resource budgets, event ordering."""

from __future__ import annotations

import unittest

from reference_engine import saturn_backend as backend
from reference_engine import translation, vdp1
from reference_engine.evidence import (
    EVIDENCE_LABELS,
    Claim,
    ClaimSet,
    EvidenceError,
    adapted,
    inferred,
    measured,
    unresolved,
)
from reference_engine.source_semantic import ObjectPart, SpriteAssembly
from reference_engine.trace import EventTrace, TraceError


def assembly(*attributes: int) -> SpriteAssembly:
    parts = [
        ObjectPart(order=i, code=0x1000 + i, attribute=attr, layout_adjust=0, layout_x=i * 16, layout_y=0)
        for i, attr in enumerate(attributes)
    ]
    return SpriteAssembly(
        address=0xE000,
        selector=6,
        budget=sum(part.tile_count for part in parts),
        origin_x=0,
        origin_y=0,
        parts=parts,
    )


class EvidenceLabelTest(unittest.TestCase):
    def test_every_label_is_one_of_the_five(self):
        self.assertEqual(
            EVIDENCE_LABELS, ("MEASURED", "DECODED", "INFERRED", "ADAPTED", "UNRESOLVED")
        )

    def test_inferred_without_a_falsification_is_rejected(self):
        with self.assertRaises(EvidenceError):
            inferred("x", falsification="")

    def test_unresolved_without_a_probe_is_rejected(self):
        with self.assertRaises(EvidenceError):
            unresolved(probe="")

    def test_unresolved_is_the_only_label_allowed_a_missing_value(self):
        self.assertIsNone(unresolved(probe="trace it").value)
        with self.assertRaises(EvidenceError):
            Claim("MEASURED", None, source="s")

    def test_measured_requires_a_source(self):
        with self.assertRaises(EvidenceError):
            measured("x", source="")

    def test_claim_set_counts_and_lists_unresolved_names(self):
        claims = ClaimSet()
        claims.add("a", measured(1, "src"))
        claims.add("b", unresolved(probe="p"))
        claims.add("c", adapted(2, note="choice"))
        self.assertEqual(claims.label_counts()["MEASURED"], 1)
        self.assertEqual(claims.unresolved_names(), ["b"])
        with self.assertRaises(EvidenceError):
            claims.add("a", measured(2, "src"))


class CommandGenerationTest(unittest.TestCase):
    def test_per_tile_emits_one_command_per_tile_plus_prologue_and_end(self):
        posed = translation.normalise_assembly(assembly(0x011B, 0x121B))  # 2 + 6 tiles
        commands = backend.emit_pose_commands(posed, strategy=backend.STRATEGY_PER_TILE)
        self.assertEqual(len(commands), 2 + 8 + 1)
        self.assertEqual(commands[0].command_name, "SYSTEM_CLIP")
        self.assertEqual(commands[1].command_name, "LOCAL_COORDINATE")
        self.assertTrue(commands[-1].is_end)

    def test_per_part_emits_one_command_per_source_part(self):
        posed = translation.normalise_assembly(assembly(0x011B, 0x121B))
        commands = backend.emit_pose_commands(posed, strategy=backend.STRATEGY_PER_PART)
        self.assertEqual(len(commands), 2 + 2 + 1)

    def test_generated_list_is_readable_by_the_traversal(self):
        posed = translation.normalise_assembly(assembly(0x011B))
        commands = backend.emit_pose_commands(posed)
        walk = vdp1.traverse(vdp1.serialise(commands, size=0x1000))
        self.assertTrue(walk.terminated)
        self.assertEqual(walk.reachable_slot_count, len(commands))
        self.assertEqual(walk.jump_mode_histogram(), {"JUMP_NEXT": len(commands)})

    def test_source_order_becomes_list_order(self):
        posed = translation.normalise_assembly(assembly(0x001B, 0x001B, 0x001B))
        commands = backend.emit_pose_commands(posed, include_prologue=False, include_terminator=False)
        self.assertEqual([c.vertices[0] for c in commands], [0, 16, 32])

    def test_mirrored_multi_tile_part_reverses_its_tile_grid(self):
        source = assembly(0x021B)  # 3x1 tiles
        allocator = backend.TextureAllocator()
        # Emit facing right first so tile textures get ascending addresses.
        right = backend.emit_pose_commands(
            translation.normalise_assembly(source),
            allocator=allocator,
            include_prologue=False,
            include_terminator=False,
        )
        left = backend.emit_pose_commands(
            translation.normalise_assembly(source, facing=translation.FACING_LEFT),
            allocator=allocator,
            include_prologue=False,
            include_terminator=False,
        )

        right_addresses = [c.source_address for c in right]
        left_addresses = [c.source_address for c in left]
        self.assertEqual(right_addresses, sorted(right_addresses))
        # Screen order still runs left to right, but texture order is reversed,
        # so a mirrored block reassembles the right way round.
        self.assertEqual([c.vertices[0] for c in left], sorted(c.vertices[0] for c in left))
        self.assertEqual(left_addresses, sorted(left_addresses, reverse=True))
        self.assertTrue(all(c.flip_x for c in left))
        # Mirroring reuses the same textures rather than storing a second copy.
        self.assertEqual(sorted(left_addresses), right_addresses)
        self.assertEqual(allocator.entries, 3)

    def test_colour_bank_follows_the_measured_stride(self):
        calibration = backend.Vdp1Calibration()
        self.assertEqual(
            calibration.color_bank_for(1) - calibration.color_bank_for(0),
            vdp1.COLOR_BANK_STRIDE,
        )

    def test_unknown_strategy_is_rejected(self):
        posed = translation.normalise_assembly(assembly(0x001B))
        with self.assertRaises(backend.BackendError):
            backend.emit_pose_commands(posed, strategy="precomposed")

    def test_texture_allocator_is_deterministic_and_deduplicates(self):
        allocator = backend.TextureAllocator()
        first = allocator.address_for("tile-a", 128)
        second = allocator.address_for("tile-b", 128)
        self.assertEqual(allocator.address_for("tile-a", 128), first)
        self.assertEqual(second - first, 128)
        self.assertEqual(allocator.entries, 2)

        repeat = backend.TextureAllocator()
        self.assertEqual(repeat.address_for("tile-a", 128), first)

    def test_pressure_reports_more_slots_but_equal_texture_bytes(self):
        posed = translation.normalise_assembly(assembly(0x121B))
        per_part = backend.measure_pressure(posed, strategy=backend.STRATEGY_PER_PART)
        per_tile = backend.measure_pressure(posed, strategy=backend.STRATEGY_PER_TILE)
        self.assertGreater(per_tile.command_slots, per_part.command_slots)
        self.assertEqual(per_tile.texture_bytes, per_part.texture_bytes)
        self.assertEqual(per_tile.command_table_bytes, per_tile.command_slots * 32)


class ResourceLedgerTest(unittest.TestCase):
    def test_default_ledger_keeps_every_region_separate(self):
        ledger = backend.default_ledger()
        self.assertEqual(
            sorted(ledger.regions),
            [
                "cartridge_dram",
                "sound_ram",
                "vdp1_command_table",
                "vdp1_texture",
                "vdp2_color_ram",
                "vdp2_vram",
                "work_ram_high",
                "work_ram_low",
            ],
        )

    def test_the_ledger_never_offers_a_combined_total(self):
        document = backend.default_ledger().to_json()
        self.assertNotIn("total_bytes", document)
        self.assertIn("never summed", document["note"])

    def test_charging_one_region_does_not_touch_another(self):
        ledger = backend.default_ledger()
        ledger.charge_resident("vdp1_texture", 4096)
        self.assertEqual(ledger.regions["vdp1_texture"].resident_bytes, 4096)
        self.assertEqual(ledger.regions["cartridge_dram"].resident_bytes, 0)
        self.assertEqual(ledger.regions["work_ram_high"].resident_bytes, 0)

    def test_per_frame_and_resident_bytes_are_tracked_apart(self):
        ledger = backend.default_ledger()
        ledger.charge_per_frame("vdp1_command_table", 2048)
        region = ledger.regions["vdp1_command_table"]
        self.assertEqual(region.per_frame_bytes, 2048)
        self.assertEqual(region.resident_bytes, 0)

    def test_overcommitment_is_detected_per_region(self):
        ledger = backend.default_ledger()
        ledger.charge_resident("vdp2_color_ram", 8192)
        self.assertEqual(ledger.overcommitted(), ["vdp2_color_ram"])

    def test_unknown_region_is_rejected(self):
        ledger = backend.default_ledger()
        with self.assertRaises(backend.BackendError):
            ledger.charge_resident("main_memory", 1)

    def test_duplicate_region_is_rejected(self):
        ledger = backend.default_ledger()
        with self.assertRaises(backend.BackendError):
            ledger.add(ledger.regions["sound_ram"])

    def test_every_region_carries_a_labelled_responsibility(self):
        for region in backend.default_ledger().regions.values():
            self.assertIn(region.responsibility.label, EVIDENCE_LABELS)

    def test_backend_claims_are_all_labelled_and_name_their_gaps(self):
        claims = backend.backend_claims()
        self.assertTrue(claims.unresolved_names())
        for name in claims.unresolved_names():
            self.assertTrue(claims.claims[name].probe, "%s has no probe" % name)


class AudioRoutingTest(unittest.TestCase):
    def test_known_categories_route_and_unknown_ones_stay_unresolved(self):
        router = backend.default_audio_router()
        self.assertEqual(router.route("music"), backend.TRANSPORT_CDDA)
        self.assertEqual(router.route("voice_clip"), backend.TRANSPORT_UNRESOLVED)

    def test_gameplay_cues_route_to_the_measured_stream_not_a_per_event_slot(self):
        """Only three SCSP slots exist and none of their registers change, so a
        slot-per-event route would contradict the measurement."""
        router = backend.default_audio_router()
        for category in ("attack_swing", "impact"):
            self.assertEqual(router.route(category), backend.TRANSPORT_SCSP_STREAM)
            self.assertNotEqual(router.route(category), backend.TRANSPORT_SCSP_PCM)


class PhaseResidencyTest(unittest.TestCase):
    def test_phase_records_loads_retains_and_retires_separately(self):
        phase = backend.PhaseResidency(
            phase="round_one", loads=["a"], retains=["b"], retires=["c"]
        )
        document = phase.to_json()
        self.assertEqual(document["loads"], ["a"])
        self.assertEqual(document["retains"], ["b"])
        self.assertEqual(document["retires"], ["c"])


class TraceOrderingTest(unittest.TestCase):
    def test_events_sort_by_frame_then_semantic_priority(self):
        trace = EventTrace()
        trace.add(5, "render", "actor")
        trace.add(5, "collision", "target")
        trace.add(5, "state_enter", "actor")
        trace.add(4, "audio", "actor")
        self.assertEqual(
            [(e.frame, e.kind) for e in trace.ordered()],
            [(4, "audio"), (5, "state_enter"), (5, "collision"), (5, "render")],
        )

    def test_collision_precedes_the_damage_it_causes(self):
        trace = EventTrace()
        trace.add(9, "damage", "target", magnitude="UNRESOLVED")
        trace.add(9, "collision", "target")
        self.assertEqual([e.kind for e in trace.ordered()], ["collision", "damage"])

    def test_insertion_order_does_not_change_the_result(self):
        forward = EventTrace()
        backward = EventTrace()
        events = [(1, "input"), (1, "pose"), (2, "audio"), (2, "render")]
        for frame, kind in events:
            forward.add(frame, kind, "actor")
        for frame, kind in reversed(events):
            backward.add(frame, kind, "actor")
        self.assertEqual(
            [e.sort_key for e in forward.ordered()], [e.sort_key for e in backward.ordered()]
        )

    def test_detail_participates_in_the_total_order(self):
        trace = EventTrace()
        trace.add(1, "pose", "actor", assembly="0xB")
        trace.add(1, "pose", "actor", assembly="0xA")
        self.assertTrue(trace.is_totally_ordered())
        self.assertEqual(
            [e.detail["assembly"] for e in trace.ordered()], ["0xA", "0xB"]
        )

    def test_identical_events_break_the_total_order_and_are_reported(self):
        trace = EventTrace()
        trace.add(1, "pose", "actor", assembly="0xA")
        trace.add(1, "pose", "actor", assembly="0xA")
        self.assertFalse(trace.is_totally_ordered())

    def test_unknown_kind_and_negative_frame_are_rejected(self):
        trace = EventTrace()
        with self.assertRaises(TraceError):
            trace.add(1, "explosion", "actor")
        with self.assertRaises(TraceError):
            trace.add(-1, "pose", "actor")


if __name__ == "__main__":
    unittest.main()
