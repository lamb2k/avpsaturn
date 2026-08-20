#!/usr/bin/env python3
"""Unit tests for the CPS2 object/layer priority register decode.

These pin the decode itself, independently of any capture: the layer
draw order comes from CPS-B layer control bits 6..13, each layer's
4-bit priority is indexed by LAYER NUMBER in OBJ_PRI, and object
priority code i is hidden under layer L exactly when i <= pri(L)
(MAME 0.289 src/mame/capcom/cps2.cpp render_layers).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from pin_source_priority_semantics import (  # noqa: E402
    decode_layer_priorities)
from pin_object_layer_priority import (  # noqa: E402
    decode, perturbed_order)


class DecodeTest(unittest.TestCase):
    def test_draw_order_reads_layer_control_bits(self):
        # 0x12c3: bits 6..13 encode the order 3,2,0,1 back to front.
        out = decode_layer_priorities(0x12C3, 0x2377)
        self.assertEqual(out["draw_order_back_to_front"], [3, 2, 0, 1])

    def test_priority_nibbles_indexed_by_layer_number(self):
        out = decode_layer_priorities(0x12C3, 0x2377)
        self.assertEqual(out["layer_priority_nibbles"],
                         {"1": 7, "2": 3, "3": 2})

    def test_code_is_hidden_when_not_greater_than_layer_priority(self):
        out = decode_layer_priorities(0x12C3, 0x2377)
        rel = out["object_code_relationships"]
        # street registers: code 4 beats layers 2 and 3, loses to 1.
        self.assertEqual(rel["4"]["draws_above_layers"], [2, 3])
        self.assertEqual(rel["4"]["hidden_under_layers"], [1])
        # code 1 is hidden under every layer: the behind-everything band.
        self.assertEqual(rel["1"]["draws_above_layers"], [])
        self.assertEqual(rel["1"]["hidden_under_layers"], [1, 2, 3])

    def test_equal_priority_hides_the_object(self):
        # pri(2) == 4 (nibble at bits 8..11) must hide code 4.
        out = decode_layer_priorities(0x12C3, 0x0400)
        self.assertIn(2, out["object_code_relationships"]["4"]
                      ["hidden_under_layers"])

    def test_select_scene_registers_let_code_seven_beat_the_text_layer(self):
        out = decode_layer_priorities(0x12C3, 0x3266)
        rel = out["object_code_relationships"]
        self.assertIn(1, rel["7"]["draws_above_layers"])
        self.assertIn(1, rel["6"]["hidden_under_layers"])

    def test_witness_decode_agrees_with_the_sweep_decode(self):
        sweep = decode_layer_priorities(0x12C3, 0x2377)
        witness = decode({"layer_control": 0x12C3, "obj_pri": 0x2377})
        self.assertEqual(witness["draw_order_back_to_front"],
                         sweep["draw_order_back_to_front"])
        self.assertEqual(witness["object_code_draws_above"],
                         sweep["object_code_relationships"]["4"]
                         ["draws_above_layers"])
        self.assertEqual(witness["object_code_hidden_under"],
                         sweep["object_code_relationships"]["4"]
                         ["hidden_under_layers"])

    def test_perturbed_order_moves_the_named_layer_to_the_front(self):
        moved = perturbed_order(0x12C3, 2)
        order = [(moved >> s) & 3 for s in (6, 8, 10, 12)]
        self.assertEqual(order[-1], 2)
        self.assertNotEqual(order, [3, 2, 0, 1])
        self.assertCountEqual(order, [3, 2, 0, 1])

    def test_perturbed_order_is_inert_for_an_absent_layer(self):
        # An order that never names layer 1 must ignore layer 1.
        control = 0x0000
        order = [(control >> s) & 3 for s in (6, 8, 10, 12)]
        self.assertNotIn(1, order)
        self.assertEqual(perturbed_order(control, 1), control)


if __name__ == "__main__":
    unittest.main()
