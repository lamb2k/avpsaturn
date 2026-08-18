"""End-to-end scenario run, report determinism, and evidence-labelling gates."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from reference_engine import report as report_module
from reference_engine.evidence import EVIDENCE_LABELS, UNRESOLVED
from reference_engine.scenario import NormalHitModel, ScenarioError

ROOT = Path(__file__).resolve().parents[2]
SCENARIO = ROOT / "reference_engine" / "scenarios" / "normal_hit.json"
TRACKED_REPORT = ROOT / "data" / "reference_engine_normal_hit_report.json"


class _ScenarioCase(unittest.TestCase):
    """Shared fixture. Holds no assertions so subclasses do not re-run them."""

    @classmethod
    def setUpClass(cls):
        cls.model = NormalHitModel.load(ROOT, SCENARIO)
        cls.result = cls.model.run()


class ScenarioRunTest(_ScenarioCase):
    def test_all_four_anchors_land_in_their_own_state(self):
        self.assertEqual(
            self.result.anchor_states,
            {
                "idle": "idle",
                "normal_active": "attack_active",
                "impact": "attack_impact",
                "recovery": "attack_recovery",
            },
        )

    def test_the_state_machine_returns_to_idle(self):
        self.assertEqual(self.result.frames[-1].state, "idle")

    def test_exactly_one_collision_and_one_damage_event_are_raised(self):
        self.assertEqual(len(self.result.trace.of_kind("collision")), 1)
        self.assertEqual(len(self.result.trace.of_kind("damage")), 1)

    def test_damage_magnitude_is_never_a_number(self):
        for event in self.result.trace.of_kind("damage"):
            self.assertIsInstance(event.detail["magnitude"], str)
            self.assertIn("UNRESOLVED", event.detail["magnitude"])

    def test_collision_precedes_damage_which_precedes_audio(self):
        frame = self.result.trace.of_kind("collision")[0].frame
        kinds = [
            event.kind
            for event in self.result.trace.ordered()
            if event.frame == frame and event.kind in {"collision", "damage", "audio"}
        ]
        self.assertEqual(kinds, ["collision", "damage", "audio"])

    def test_contact_is_attributed_to_the_attacking_pose_not_the_reaction_pose(self):
        collision = self.result.trace.of_kind("collision")[0]
        active_state = self.result.state_machine.states["attack_active"]
        active_program = self.model.programs[active_state.program_start]
        self.assertEqual(
            collision.detail["attacker_pose"],
            "0x%06X" % active_program.poses[0].address,
        )

    def test_the_event_trace_is_totally_ordered(self):
        self.assertTrue(self.result.trace.is_totally_ordered())

    def test_every_frame_produces_a_render_event(self):
        self.assertEqual(
            len(self.result.trace.of_kind("render")), len(self.result.frames)
        )

    def test_idle_state_walks_more_than_one_pose(self):
        idle_poses = {
            event.detail["assembly"]
            for event in self.result.trace.of_kind("pose")
            if event.frame < 24
        }
        self.assertGreater(len(idle_poses), 1)

    def test_per_tile_pressure_exceeds_per_part_on_every_frame(self):
        for frame in self.result.frames:
            self.assertGreaterEqual(
                frame.per_tile.command_slots, frame.per_part.command_slots
            )

    def test_no_resource_region_is_overcommitted(self):
        self.assertEqual(self.result.ledger.overcommitted(), [])

    def test_tile_span_agreement_is_reported_with_its_one_disagreement(self):
        agreement = self.result.tile_agreement
        self.assertEqual(agreement["assemblies"], agreement["agreeing"] + agreement["disagreeing"])
        self.assertEqual(len(agreement["disagreements"]), agreement["disagreeing"])


class ClaimLabellingTest(_ScenarioCase):
    def test_every_claim_carries_one_of_the_five_labels(self):
        for name, claim in self.result.claims.claims.items():
            self.assertIn(claim.label, EVIDENCE_LABELS, name)

    def test_all_five_label_classes_are_represented(self):
        counts = self.result.claims.label_counts()
        for label in EVIDENCE_LABELS:
            self.assertGreater(counts[label], 0, "no %s claim" % label)

    def test_every_unresolved_claim_names_a_probe(self):
        for name in self.result.claims.unresolved_names():
            self.assertTrue(self.result.claims.claims[name].probe, name)

    def test_every_inferred_claim_names_a_falsification(self):
        for name, claim in self.result.claims.claims.items():
            if claim.label == "INFERRED":
                self.assertTrue(claim.falsification, name)


class ReportTest(_ScenarioCase):
    def test_report_serialisation_is_byte_stable_across_runs(self):
        first = report_module.serialise(report_module.build_report(self.result, self.model))
        second_model = NormalHitModel.load(ROOT, SCENARIO)
        second = report_module.serialise(
            report_module.build_report(second_model.run(), second_model)
        )
        self.assertEqual(first, second)

    def test_report_digest_is_reproducible(self):
        document = report_module.build_report(self.result, self.model)
        self.assertEqual(report_module.digest(document), report_module.digest(document))

    def test_tracked_report_matches_a_fresh_run(self):
        self.assertTrue(TRACKED_REPORT.is_file(), "generate the report first")
        fresh = report_module.serialise(report_module.build_report(self.result, self.model))
        self.assertEqual(TRACKED_REPORT.read_bytes(), fresh.encode("ascii"))

    def test_report_states_its_inputs_with_hashes(self):
        document = report_module.build_report(self.result, self.model)
        self.assertTrue(document["inputs"])
        for item in document["inputs"]:
            self.assertEqual(len(item["sha256"]), 64)
            self.assertIn(item["evidence"], EVIDENCE_LABELS)

    def test_report_separates_reachable_from_stored_command_counts(self):
        document = report_module.build_report(self.result, self.model)
        envelope = document["layers"]["saturn_backend"]["reference_envelope"]
        self.assertTrue(envelope["available"])
        for anchor in envelope["anchors"]:
            self.assertIn("reachable_slots", anchor)
            self.assertIn("sequentially_stored_slots", anchor)
            self.assertIn("stored_nonzero_slots", anchor)
            self.assertGreater(anchor["stored_nonzero_slots"], anchor["reachable_slots"])

    def test_report_keeps_resource_regions_separate_with_no_total(self):
        document = report_module.build_report(self.result, self.model)
        resources = document["layers"]["saturn_backend"]["resources"]
        names = [region["name"] for region in resources["regions"]]
        self.assertIn("cartridge_dram", names)
        self.assertIn("work_ram_high", names)
        self.assertIn("vdp1_command_table", names)
        self.assertNotIn("total_bytes", resources)

    def test_report_lists_unresolved_fields_and_prohibited_inferences(self):
        document = report_module.build_report(self.result, self.model)
        self.assertTrue(document["unresolved_fields"])
        for item in document["unresolved_fields"]:
            self.assertTrue(item["probe"])
        self.assertTrue(document["prohibited_inferences"])

    def test_report_answers_both_decision_sentences(self):
        document = report_module.build_report(self.result, self.model)
        statement = document["decision_statement"]
        self.assertTrue(statement["will_decide"].strip())
        self.assertTrue(statement["must_verify"].strip())
        self.assertTrue(document["required_avp_probe"].strip())

    def test_report_declares_what_it_is_not(self):
        document = report_module.build_report(self.result, self.model)
        joined = " ".join(document["boundary"]).lower()
        self.assertIn("not a saturn runtime", joined)
        self.assertIn("not a cps2 emulator", joined)

    def test_report_contains_no_absolute_path(self):
        text = report_module.serialise(report_module.build_report(self.result, self.model))
        self.assertNotIn("C:\\\\", text)
        self.assertNotIn(".deps", text)


class ScenarioValidationTest(unittest.TestCase):
    def test_a_scenario_naming_an_undecoded_program_is_rejected(self):
        document = json.loads(SCENARIO.read_text(encoding="utf-8"))
        document["states"][0]["program"] = "0xDEAD00"
        broken = ROOT / "reference_engine" / "scenarios" / "_broken_program.json"
        broken.write_text(json.dumps(document), encoding="utf-8")
        try:
            model = NormalHitModel.load(ROOT, broken)
            with self.assertRaises(ScenarioError):
                model.build_state_machine()
        finally:
            broken.unlink()

    def test_a_scenario_missing_a_required_section_is_rejected(self):
        document = json.loads(SCENARIO.read_text(encoding="utf-8"))
        del document["prohibited_inferences"]
        broken = ROOT / "reference_engine" / "scenarios" / "_broken_section.json"
        broken.write_text(json.dumps(document), encoding="utf-8")
        try:
            with self.assertRaises(ScenarioError):
                NormalHitModel.load(ROOT, broken)
        finally:
            broken.unlink()


class ControlFlowArtifactTest(unittest.TestCase):
    """Gates on the tracked VDP1 control-flow report itself."""

    @classmethod
    def setUpClass(cls):
        path = ROOT / "data" / "mshvsf_saturn_vdp1_control_flow.json"
        if not path.is_file():
            raise unittest.SkipTest("VDP1 control-flow report has not been generated")
        cls.document = json.loads(path.read_text(encoding="utf-8"))

    def test_every_anchor_reports_reachable_and_stored_counts_apart(self):
        for anchor in self.document["anchors"]:
            self.assertIn("reachable_slot_count", anchor)
            self.assertIn("sequential_slot_count", anchor)
            self.assertIn("stored_nonzero_slots", anchor)
            self.assertGreater(
                anchor["stored_nonzero_slots"], anchor["reachable_slot_count"]
            )
            self.assertEqual(
                anchor["residual_slots_after_terminator"],
                anchor["stored_nonzero_slots"] - anchor["reachable_slot_count"],
            )

    def test_every_anchor_terminates_on_a_draw_end_without_anomalies(self):
        for anchor in self.document["anchors"]:
            self.assertTrue(anchor["terminated_by_draw_end"], anchor["label"])
            self.assertEqual(anchor["control_flow_anomalies"], [])

    def test_every_finding_is_labelled_and_names_a_falsification(self):
        for finding in self.document["findings"]:
            self.assertIn(finding["evidence"], EVIDENCE_LABELS)
            self.assertTrue(finding["falsification"])
            self.assertIsInstance(finding["holds"], bool)

    def test_the_report_keeps_its_promotion_boundary(self):
        self.assertEqual(
            self.document["evidence_class"],
            "MEASURED_ON_MARVEL_NOT_YET_VALIDATED_ON_AVP",
        )


if __name__ == "__main__":
    unittest.main()
