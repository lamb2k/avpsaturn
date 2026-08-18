"""Gates on the tracked VDP2 colour-ownership and SCSP slot-activity report."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from reference_engine.evidence import EVIDENCE_LABELS

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "data" / "mshvsf_saturn_vdp2_scsp.json"


class Vdp2ScspArtifactTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not REPORT.is_file():
            raise unittest.SkipTest("VDP2/SCSP report has not been generated")
        cls.document = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_the_report_keeps_its_promotion_boundary(self):
        self.assertEqual(
            self.document["evidence_class"],
            "MEASURED_ON_MARVEL_NOT_YET_VALIDATED_ON_AVP",
        )

    def test_all_four_anchors_are_present(self):
        self.assertEqual(
            sorted(item["label"] for item in self.document["anchors"]),
            ["idle", "impact", "normal_active", "recovery"],
        )

    def test_vdp2_register_block_is_recorded_as_unreadable(self):
        """The negative result must stay explicit, or the gap looks like an
        analysis omission rather than an instrument limit."""
        for anchor in self.document["anchors"]:
            self.assertFalse(anchor["vdp2"]["vdp2_registers_readable"], anchor["label"])
            self.assertEqual(anchor["vdp2"]["vdp2_registers_nonzero_bytes"], 0)

    def test_every_referenced_colour_bank_resolves_into_populated_colour_ram(self):
        for anchor in self.document["anchors"]:
            vdp2 = anchor["vdp2"]
            self.assertGreater(vdp2["vdp1_color_banks_referenced"], 0, anchor["label"])
            self.assertTrue(vdp2["all_referenced_banks_populated"], anchor["label"])
            for item in vdp2["vdp1_color_bank_resolution"]:
                self.assertTrue(item["cram_bank_is_populated"], item["cmdcolr"])

    def test_colour_bank_resolution_stays_inside_colour_ram(self):
        for anchor in self.document["anchors"]:
            vdp2 = anchor["vdp2"]
            for item in vdp2["vdp1_color_bank_resolution"]:
                self.assertLess(item["candidate_cram_bank"], vdp2["color_ram_banks_total"])

    def test_only_a_small_static_scsp_slot_set_is_active(self):
        counts = {anchor["scsp"]["active_slot_count"] for anchor in self.document["anchors"]}
        self.assertEqual(len(counts), 1, "active slot count varies across anchors")
        self.assertLess(counts.pop(), self.document["anchors"][0]["scsp"]["slots_total"])

    def test_slot_registers_are_identical_across_every_transition(self):
        for transition in self.document["transitions"]:
            self.assertTrue(
                transition["scsp_slot_registers_identical"],
                "%s -> %s" % (transition["from"], transition["to"]),
            )
            self.assertEqual(transition["scsp_slots_changed"], [])

    def test_sound_ram_moves_even_though_slot_registers_do_not(self):
        """This pairing is the whole basis of the streaming inference."""
        for transition in self.document["transitions"]:
            self.assertGreater(transition["sound_ram_changed_bytes"], 0)
            self.assertTrue(transition["scsp_slot_registers_identical"])

    def test_vdp2_vram_is_stable_while_colour_ram_is_not(self):
        for transition in self.document["transitions"]:
            self.assertTrue(transition["vdp2_vram_identical"])
        self.assertTrue(
            any(t["color_ram_changed_bytes"] > 0 for t in self.document["transitions"]),
            "no colour-RAM activity found, so the colour claim has no support",
        )

    def test_every_finding_is_labelled_and_names_a_falsification(self):
        for finding in self.document["findings"]:
            self.assertIn(finding["evidence"], EVIDENCE_LABELS, finding["id"])
            self.assertTrue(finding["falsification"], finding["id"])
            self.assertTrue(finding["consequence"], finding["id"])
            self.assertIsInstance(finding["holds"], bool)

    def test_the_streaming_conclusion_is_inferred_not_measured(self):
        streaming = next(f for f in self.document["findings"] if f["id"] == "SCSP-2")
        self.assertEqual(streaming["evidence"], "INFERRED")

    def test_the_report_states_its_sampling_limit(self):
        joined = " ".join(self.document["limits"]).lower()
        self.assertIn("between them", joined)
        self.assertIn("budget for any other title", joined)


if __name__ == "__main__":
    unittest.main()
