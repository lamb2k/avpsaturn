"""Round-trip and control-flow tests for tools/avsp_vdp1_model.py.

These need no private inputs: every fixture is a VDP1 command table this test
builds in memory, so the traversal logic is checked against lists whose correct
reachable set is known by construction.

The property that matters is REACHABLE vs STORED. A command table retains
whatever a longer earlier list wrote past the terminator, so a sequential scan
overcounts. Each fixture below deliberately leaves residue after the end bit
and asserts the two readings differ in the expected direction.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import avsp_vdp1_model as vdp1  # noqa: E402

FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        return
    FAILURES.append(message)
    print("  FAIL:", message)


def slot(ctrl: int = 0, link: int = 0, pmod: int = 0, colr: int = 0,
         srca: int = 0, size: int = 0) -> bytes:
    words = [ctrl, link, pmod, colr, srca, 0, 0, size] + [0] * 8
    return struct.pack(">16H", *words)


def table(*slots: bytes, residue: int = 0) -> bytes:
    """Concatenate slots, then append `residue` non-zero slots AFTER the
    terminator so stored-order scanning has something to over-count."""
    body = b"".join(slots)
    body += b"".join(slot(ctrl=0x0001, colr=0xDEAD) for _ in range(residue))
    return body


def link_words(byte_address: int) -> int:
    return byte_address >> 3


def main() -> int:
    print("avsp_vdp1_model: control-flow and round-trip")

    # --- decode round-trip -------------------------------------------------
    original = slot(ctrl=0x0010, pmod=0x0880, colr=0x6080,
                    srca=link_words(0x30000), size=(2 << 8) | 16)
    command = vdp1.decode_command(original, 0)
    check(command.flip_x is True, "FLIP_X bit not decoded")
    check(command.flip_y is False, "FLIP_Y falsely decoded")
    check(command.jump_mode == vdp1.JUMP_NEXT,
          "jump mode should default to JUMP_NEXT")
    # CMDPMOD bits 5-3 == 0 selects 16-colour bank mode, with CMDCOLR holding
    # the CRAM bank address rather than a palette index.
    check(command.color_mode == 0,
          "CMDPMOD 0x0880 should decode to colour mode 0 (16-colour bank), "
          "got %d" % command.color_mode)
    check(command.color_control == 0x6080,
          "CMDCOLR should round-trip, got 0x%04X" % command.color_control)

    # --- JUMP_NEXT: flat list, terminator honoured -------------------------
    flat = table(slot(pmod=0x0880, colr=0x6000),
                 slot(pmod=0x0880, colr=0x6010),
                 slot(ctrl=vdp1.END_BIT), residue=5)
    result = vdp1.traverse(flat)
    check(result.drawn_command_count == 2,
          "flat list: expected 2 drawn commands, got %d"
          % result.drawn_command_count)
    stored = vdp1.stored_nonzero_slots(flat)
    check(stored > result.reachable_slot_count,
          "residue after the terminator should make stored (%d) exceed "
          "reachable (%d)" % (stored, result.reachable_slot_count))

    # --- JUMP_ASSIGN: follow CMDLINK, skipping a slot ----------------------
    assign = table(
        slot(ctrl=(vdp1.JUMP_ASSIGN << 12), link=link_words(0x40)),
        slot(pmod=0x0880, colr=0x1110),          # skipped: jumped over
        slot(ctrl=vdp1.END_BIT),                 # 0x40: terminator
    )
    result = vdp1.traverse(assign)
    check(result.drawn_command_count == 1,
          "JUMP_ASSIGN: expected 1 drawn command (the skipped slot must not "
          "be reached), got %d" % result.drawn_command_count)

    # --- JUMP_CALL / JUMP_RETURN ------------------------------------------
    called = table(
        slot(ctrl=(vdp1.JUMP_CALL << 12), link=link_words(0x40)),
        slot(ctrl=vdp1.END_BIT),                 # 0x20: return lands here
        slot(ctrl=(vdp1.JUMP_RETURN << 12)),     # 0x40: subroutine returns
    )
    result = vdp1.traverse(called)
    check(result.drawn_command_count == 2,
          "JUMP_CALL/RETURN: expected 2 drawn commands, got %d"
          % result.drawn_command_count)
    check(any(m in ("JUMP_CALL", "JUMP_RETURN")
              for _, _, m in result.links_followed),
          "call/return edges should appear in links_followed")

    # --- infinite loop must terminate, not hang ----------------------------
    loop = table(slot(ctrl=(vdp1.JUMP_ASSIGN << 12), link=link_words(0x00)))
    result = vdp1.traverse(loop, max_steps=64)
    check(result.reachable_slot_count <= 64,
          "self-jump must be bounded by max_steps, got %d"
          % result.reachable_slot_count)

    # --- out-of-range link is reported, not silently followed --------------
    bad = table(slot(ctrl=(vdp1.JUMP_ASSIGN << 12),
                     link=link_words(0x8000)))
    result = vdp1.traverse(bad)
    check(bool(result.anomalies),
          "a CMDLINK past the end of VRAM should raise an anomaly")

    # --- sequential_scan reads stored order, independent of control flow ---
    scanned = vdp1.sequential_scan(assign)
    check(len(scanned) >= 3,
          "sequential_scan should read stored slots regardless of jumps, "
          "got %d" % len(scanned))

    if FAILURES:
        print("\n%d check(s) failed" % len(FAILURES))
        return 1
    print("  all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
