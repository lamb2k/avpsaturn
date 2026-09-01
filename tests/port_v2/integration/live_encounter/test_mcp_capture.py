#!/usr/bin/env python3
"""Validate the pinned emulator MCP capture checkpoint and mutations."""
from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
REPORT = json.loads((ROOT / "data/reimplement13_emulator_mcp_capture.json")
                    .read_text(encoding="ascii"))
SETUP = (ROOT / "setup_emulator.ps1").read_text(encoding="utf-8")
PREPARE = (ROOT / "tests/port_v2/integration/live_encounter/"
           "prepare_mcp_visual_qa.py").read_text(encoding="utf-8")


def validate(report: dict[str, object]) -> None:
    package = report["package"]
    semantic = report["semantic_negative_control"]
    framebuffer = report["framebuffer_negative_control"]
    savestate = report["savestate_negative_control"]
    visual = report["visual_qa"]
    limits = report["platform_limits"]
    assert report["result"] == "PASS"
    assert package["archive_sha256"] == \
        "0d6b44afae0f99a76f5ba3090a3ce307137c9fc305ffa67d0c0a04bf040dd34b"
    assert package["exe_sha256"] == \
        "da2ffb341532f10808d8f9659c875a96cbc29ebc10a454426415059c7cef8746"
    assert package["fork_source_modified"] is False
    assert semantic["cold_runs_per_executable"] == 2
    assert semantic["samples_per_run"] == 575
    assert semantic["canonical_semantic_sha256"] == \
        "179120458393d519a5c3896de6c43ac9a99024f63d579c107c60ad64d5c68798"
    assert semantic["byte_identical"] is True
    assert framebuffer["cold_runs"] == [
        "da2ffb34-aligned1", "da2ffb34-aligned2"]
    assert framebuffer["frame_range"] == [2051, 2081]
    assert framebuffer["frame_count"] == 31
    assert framebuffer["canonical_frame_hash_sequence_sha256"] == \
        "6d64c5aea1e3666d5dae9515bef9a08ec49169702474697d4ca55d12661e75e0"
    assert framebuffer["same_frame_hashes_identical"] is True
    assert framebuffer["unique_frame_hashes"] > 1
    assert framebuffer["animated_window_discriminates"] is True
    assert savestate["pre_roll_core"] == 3
    assert savestate["capture_core"] == 0
    assert savestate["fresh_interpreter_legs"] == 2
    assert savestate["frame_range_load_relative"] == [1, 12]
    assert savestate["manifest_sha256"] == \
        "ec0aebb185f673ee4be3fb4505ac207472e715266fb4f5440ab0f38cbc3e5979"
    assert savestate["row_one_identity"] is True
    assert savestate["reload_inside_ran_session"] is False
    assert visual["capture_mode"] == "MCP_FRAMEBUFFER_BURST"
    assert visual["direct_inspection"] == "PASS"
    assert report["evidence_tier"] == "ONE_EMULATOR"
    assert limits["scu_dma_a_bus_rule"] == "PHYSICAL_TIER_ONLY"
    assert report["physical_saturn"] == "UNRUN"


def reject(label: str, path: tuple[str, ...], value: object) -> None:
    mutant = copy.deepcopy(REPORT)
    current = mutant
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = value
    try:
        validate(mutant)
    except AssertionError:
        return
    raise AssertionError(f"MCP capture mutation was accepted: {label}")


validate(REPORT)
for token in (
        "DebugRigMcp", REPORT["package"]["archive_sha256"].upper(),
        REPORT["package"]["exe_sha256"].upper(), "Confirm-EmulatorExe"):
    assert token in SETUP, f"emulator setup pin missing: {token}"
for token in (
        "frame\\tfile\\tsha256", "image identity drift", "cadence-1",
        "MCP_FRAMEBUFFER_BURST", "ONE_EMULATOR"):
    assert token in PREPARE, f"visual-QA MCP control missing: {token}"

reject("archive identity", ("package", "archive_sha256"), "0" * 64)
reject("executable identity", ("package", "exe_sha256"), "0" * 64)
reject("semantic equality", ("semantic_negative_control", "byte_identical"),
       False)
reject("semantic identity", ("semantic_negative_control",
                             "canonical_semantic_sha256"), "0" * 64)
reject("image determinism",
       ("framebuffer_negative_control", "same_frame_hashes_identical"), False)
reject("burst sequence identity", ("framebuffer_negative_control",
                                    "canonical_frame_hash_sequence_sha256"),
       "0" * 64)
reject("animated window", ("framebuffer_negative_control",
                            "unique_frame_hashes"), 1)
reject("savestate row-one identity", ("savestate_negative_control",
                                       "row_one_identity"), False)
reject("savestate fresh-leg rule", ("savestate_negative_control",
                                     "reload_inside_ran_session"), True)
reject("evidence tier", ("evidence_tier",), "PAIRED_EMULATOR")
reject("physical status", ("physical_saturn",), "PASS")

print("REIMPLEMENT-13 emulator MCP capture: PASS (11 mutations rejected)")
