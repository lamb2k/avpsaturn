#!/usr/bin/env python3
"""Unit tests for the VDP2 priority register decode.

These pin the decode against register blocks built here, so they hold
whether or not any capture can read the real block. The all-zero block
is covered explicitly, because the tracked MSHvSF capture returns one
and a decode that quietly produces "priority 0 everywhere" from it would
manufacture a measurement out of an instrument limit.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from probe_mshvsf_vdp2_priority import (  # noqa: E402
    REGISTER_LENGTH, decode_priority_registers)


def block(**registers: int) -> bytes:
    data = bytearray(REGISTER_LENGTH)
    for offset, value in registers.items():
        at = int(offset[1:], 16)
        data[at:at + 2] = value.to_bytes(2, "big")
    return bytes(data)


class Vdp2PriorityDecodeTest(unittest.TestCase):
    def test_nbg_priorities_come_from_prina_and_prinb(self):
        out = decode_priority_registers(
            block(o0F8=0x0603, o0FA=0x0102))
        self.assertEqual(out["nbg_priority"],
                         {"NBG0": 3, "NBG1": 6, "NBG2": 2, "NBG3": 1})

    def test_sprite_priorities_interleave_across_prisa_to_prisd(self):
        out = decode_priority_registers(
            block(o0F0=0x0201, o0F2=0x0403, o0F4=0x0605, o0F6=0x0007))
        self.assertEqual(
            out["sprite_priority_by_number"],
            {"0": 1, "1": 2, "2": 3, "3": 4,
             "4": 5, "5": 6, "6": 7, "7": 0})

    def test_priority_fields_are_three_bits_wide(self):
        out = decode_priority_registers(block(o0F8=0xFFFF, o0F0=0xFFFF))
        self.assertEqual(out["nbg_priority"]["NBG0"], 7)
        self.assertEqual(out["nbg_priority"]["NBG1"], 7)
        self.assertEqual(out["sprite_priority_by_number"]["0"], 7)

    def test_spctl_sprite_type_selects_the_sprite_data_bit_split(self):
        out = decode_priority_registers(block(o0E0=0x0000))
        self.assertEqual(out["sprite_type"], 0)
        self.assertEqual(out["sprite_data_split"]["priority_bits"],
                         "bits 14-15")
        other = decode_priority_registers(block(o0E0=0x0A00))
        self.assertEqual(other["sprite_type"], 0xA)
        self.assertEqual(other["sprite_data_split"]["priority_bits"],
                         "bits 6-7")
        self.assertEqual(other["sprite_data_split"]["colour_bits"],
                         "none")

    def test_every_sprite_type_has_a_declared_bit_split(self):
        for sprite_type in range(16):
            out = decode_priority_registers(
                block(o0E0=sprite_type << 8))
            self.assertEqual(out["sprite_type"], sprite_type)
            self.assertIn("priority_bits", out["sprite_data_split"])

    def test_sprite_window_flag_reads_spctl_bit_four(self):
        self.assertTrue(
            decode_priority_registers(block(o0E0=0x0010))
            ["sprite_window_enabled"])
        self.assertFalse(
            decode_priority_registers(block(o0E0=0x0000))
            ["sprite_window_enabled"])

    def test_all_zero_block_decodes_to_all_zero_priorities(self):
        # The decode itself must not invent anything; the probe, not the
        # decode, is what refuses to treat this block as a measurement.
        out = decode_priority_registers(bytes(REGISTER_LENGTH))
        self.assertEqual(set(out["nbg_priority"].values()), {0})
        self.assertEqual(set(out["sprite_priority_by_number"].values()),
                         {0})

    def test_short_block_is_rejected(self):
        with self.assertRaises(ValueError):
            decode_priority_registers(bytes(0x40))


if __name__ == "__main__":
    unittest.main()
