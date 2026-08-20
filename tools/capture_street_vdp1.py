#!/usr/bin/env python3
"""Capture StreetTest's final VDP1 command sequence with texture content.

This strengthens `tools/capture_street_command_order.py` in the one way
that matters for RP4: every drawing command records a SHA-256 of the
texture bytes it actually references, so two builds can be compared on
what they draw rather than on where the tile pool happened to put it.

The earlier sorted reverse/forward experiment found the two builds
differing "only in texture address". That is precisely the field this
capture excludes from identity and replaces with content, because the
tile sprite pool is an LRU: change the emission order and every address
moves even when the drawing is identical.

The command list is walked as the hardware command processor walks it,
through `tools/avsp_vdp1_model.py`, so a jump/skip/call list is read
correctly instead of assumed sequential, and stored-but-unreachable
slots left behind by a longer earlier list are not counted as drawn.

Output is raw private evidence and stays ignored. The tracked manifest
is written by `tools/verify_rp4_saturn_controls.py` and carries hashes,
counts and labels only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from avsp_vdp1_model import (  # noqa: E402
    DRAW_COMMANDS,
    SLOT_BYTES,
    traverse,
)
from capture_frontend_cram import Mcp  # noqa: E402
from capture_street_command_order import symbols as elf_symbols  # noqa: E402
from rp4_command_identity import CaptureRejected, texture_byte_count  # noqa: E402
from street_launch import (  # noqa: E402
    READY_LIVE,
    classify_readiness,
    poll_diagnostics,
    sha256_file,
    wait_for_live,
)

VDP1_VRAM = 0x25C00000
#: Enough slots to cover the measured ~530-command street list with room to
#: see an overflow rather than silently truncating at the expected size.
CAPTURED_SLOTS = 2048
#: MCP returns hex text, so reads are chunked to keep each response sane.
READ_CHUNK = 0x1000
ENDPOINT = "http://127.0.0.1:9640/mcp"


def read_block(mcp: Mcp, address: int, length: int) -> bytes:
    data = bytearray()
    while len(data) < length:
        step = min(READ_CHUNK, length - len(data))
        data += mcp.read(address + len(data), step)
    return bytes(data)


def wait_for_fixture_frame(mcp: Mcp, symbols: dict, target_rel: int,
                           timeout: float = 600.0) -> int:
    """Stop on one exact fixture frame, with the command list complete.

    Hunting the frame by pause/read/resume does not converge: each round
    trip advances the fixture by about one frame, so reaching a chosen
    frame of a 201-frame cycle is a race that routinely runs out of time
    (measured: 70 of 201 frames visited in 300 seconds). A memory
    breakpoint on the write of `avsp_diag_street_frame` with a value
    comparison stops on exactly the wanted frame instead.

    The capture happens AT the breakpoint stop. Releasing the run to the
    next frame boundary instead is not an option: `pause` takes about
    0.74 s to return, and the fixture advances roughly 44 frames in that
    time, so each capture lands on an arbitrary different frame. That was
    measured, not assumed - it made two sorted builds that must be
    identical share only 7 comparable commands out of 394.

    The breakpoint fires at the END of the street draw loop. What the
    command table holds there depends on the submission path, so the
    caller declares the difference with `frame_lag` rather than the
    capture guessing:

    * immediate (slPutSprite) writes commands into the table as they are
      submitted, so at this point the table IS fixture frame `rel`
      (lag 0);
    * sorted (slDispSprite) leaves the frame in SGL's sort list until
      slSynch, so the table still holds the list committed one frame
      earlier (lag 1, i.e. request rel+1 to read frame rel).
    """
    state, sample = wait_for_live(mcp, symbols, timeout=timeout)
    if state != READY_LIVE:
        raise SystemExit(
            "StreetTest never reached a live advancing fixture (state=%s, "
            "diagnostics=%s)" % (state, sample))
    frame_symbol = symbols["_avsp_diag_street_frame"]
    mcp.call("breakpoint_add", cpu="master", type="memory",
             address=hex(frame_symbol), write=True, value=hex(target_rel))
    try:
        mcp.call("resume")
        stopped = mcp.call("wait_for_stop", timeout_ms=int(timeout * 1000))
        if "stopped: true" not in stopped:
            raise SystemExit(
                "no stop while waiting for fixture frame %d: %s"
                % (target_rel, stopped.strip()[:200]))
        observed = mcp.u32(frame_symbol)
        if observed != target_rel:
            raise SystemExit(
                "stopped at fixture frame %d, not the requested %d"
                % (observed, target_rel))
    finally:
        mcp.call("breakpoint_remove", cpu="master", type="memory",
                 address=hex(frame_symbol))
    # Stay stopped exactly here. Any resume would drift the frame.
    return target_rel


def capture_commands(mcp: Mcp) -> dict:
    """Decode the reachable command list and hash every referenced texture."""
    vram = read_block(mcp, VDP1_VRAM, CAPTURED_SLOTS * SLOT_BYTES)
    result = traverse(vram)
    records = []
    textures: dict[int, str] = {}
    unsupported = []
    for command in result.visited:
        # The terminator is control flow, not drawing, and a skipped command
        # routes control without putting pixels anywhere.
        if command.is_end or command.is_skipped:
            continue
        record = {
            "index": len(records),
            "slot": command.offset // SLOT_BYTES,
            "kind": command.command_name,
            "jump_mode": command.jump_mode_name,
            "ctrl": "0x%04X" % command.control,
        }
        if command.command_type in DRAW_COMMANDS:
            try:
                length = texture_byte_count(command.width, command.height,
                                            command.color_mode)
            except CaptureRejected as error:
                unsupported.append({"index": record["index"],
                                    "reason": str(error)})
                continue
            srca = command.source_address
            if srca not in textures:
                # Texture bytes live in the same VDP1 VRAM; read past the
                # captured command window only when the texture does.
                if srca + length <= len(vram):
                    payload = vram[srca:srca + length]
                else:
                    payload = read_block(mcp, VDP1_VRAM + srca, length)
                textures[srca] = hashlib.sha256(payload).hexdigest()
            record.update({
                "pmod": "0x%04X" % command.pmod,
                "colr": "0x%04X" % command.color_control,
                "size": "0x%04X" % command.words[5],
                "xa": command.vertices[0],
                "ya": command.vertices[1],
                "flip_x": command.flip_x,
                "flip_y": command.flip_y,
                # Recorded for diagnosis only; excluded from identity.
                "srca": "0x%06X" % srca,
                "texture_bytes": length,
                "texture_sha256": textures[srca],
            })
        records.append(record)
    return {
        "commands": records,
        "command_count": len(records),
        "reachable_slots": result.reachable_slot_count,
        "drawn_commands": result.drawn_command_count,
        "state_commands": result.state_command_count,
        "skipped_commands": result.skipped_command_count,
        "terminated": result.terminated,
        "stop_reason": result.stop_reason,
        "anomalies": list(result.anomalies),
        "jump_modes": result.jump_mode_histogram(),
        "command_types": result.command_type_histogram(),
        "command_table_sha256": hashlib.sha256(
            vram[:max(1, result.reachable_slot_count) * SLOT_BYTES]).hexdigest(),
        "distinct_textures": len(textures),
        "unsupported_commands": unsupported,
    }


def capture_at(mcp: Mcp, symbols: dict, label: str, rel: int, elf: Path,
               iso: Path, output: Path, timeout: float = 600.0,
               frame_lag: int = 0) -> dict:
    """Capture one variant so the table holds fixture frame `rel`.

    `frame_lag` is how many fixture frames the committed command table
    trails the draw loop for this build's submission path: 0 for the
    immediate path, 1 for the sorted path. The breakpoint is therefore
    armed on `rel + frame_lag`, and `scene_rel` records the frame the
    captured table actually represents.
    """
    frame = wait_for_fixture_frame(mcp, symbols, rel + frame_lag, timeout)
    # Already stopped on the wanted frame boundary. Read the counters in
    # place: poll_diagnostics would pause/resume and let the fixture run on.
    diagnostics = {
        "runtime_ready": mcp.u32(symbols["_avsp_diag_runtime_ready"]),
        "street_objects": mcp.u32(symbols["_avsp_diag_street_objects"]),
        "street_frame": mcp.u32(symbols["_avsp_diag_street_frame"]),
    }
    if classify_readiness(dict(diagnostics, advanced=True)) != READY_LIVE:
        raise SystemExit(
            "renderer was not live at the capture point: %s" % diagnostics)
    try:
        report = {
            "schema": "rp4-street-command-order-capture-v1",
            "label": label,
            "requested_rel": rel,
            "observed_rel": frame,
            "frame_lag": frame_lag,
            "scene_rel": frame - frame_lag,
            "runtime_ready": diagnostics.get("runtime_ready"),
            "street_objects": diagnostics.get("street_objects"),
            "elf_sha256": sha256_file(elf),
            "iso_sha256": sha256_file(iso),
            "fixture_sha256": sha256_file(ROOT / "build/rp4_fixture/STRIPS.BIN"),
            "identity_note":
                "srca is recorded but excluded from identity; the tile pool "
                "is an LRU so texture addresses move with emission order. "
                "Identity is kind, pmod, colr, size, xa, ya, flips and "
                "texture content",
        }
        report.update(capture_commands(mcp))
    finally:
        mcp.call("resume")

    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(
            json.dumps(report, indent=1, sort_keys=True) + "\n",
            encoding="ascii", newline="\n")
    print("%s: rel %d, %d commands, %d textures, table %s, objects %s"
          % (label, frame, report["command_count"], report["distinct_textures"],
             report["command_table_sha256"][:16], report["street_objects"]))
    return {key: value for key, value in report.items() if key != "commands"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument("--rel", type=int, default=0)
    parser.add_argument("--elf", type=Path, default=ROOT / "game.elf")
    parser.add_argument("--iso", type=Path, default=ROOT / "game.iso")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args()

    symbols = elf_symbols(args.elf)
    mcp = Mcp(ENDPOINT)
    mcp.initialize()
    capture_at(mcp, symbols, args.label, args.rel, args.elf, args.iso,
               args.output, args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
