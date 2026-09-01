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
    visual = report["visual_qa"]
    limits = report["platform_limits"]
    assert report["result"] == "PASS"
    assert package["archive_sha256"] == \
        "6f157f15da4d01cca9ef044d32352b8e6d3cf6b71a44ad3303aaeb9939015864"
    assert package["exe_sha256"] == \
        "d77675912421a7435d02d844625a6ef68ba0e55ef17c9845f08651eb98f54b45"
    assert package["fork_source_modified"] is False
    assert semantic["cold_runs_per_executable"] == 2
    assert semantic["samples_per_run"] == 575
    assert semantic["canonical_semantic_sha256"] == \
        "7fae4a7cffe2c35a0df8a3c181a5ffa8f141f5b113500d67de1fd60f071a56fc"
    assert semantic["byte_identical"] is True
    assert framebuffer["cold_runs"] == [
        "coffee-shop-control-b", "coffee-shop-control-c"]
    assert framebuffer["frame_range"] == [2095, 2125]
    assert framebuffer["frame_count"] == 31
    assert framebuffer["manifest_sha256"] == \
        "13afd26ef889b6f792ade52989749eeec1dc23203b5eb1def55ac85ccca31c1f"
    assert framebuffer["same_frame_hashes_identical"] is True
    assert framebuffer["unique_frame_hashes"] > 1
    assert framebuffer["animated_window_discriminates"] is True
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
reject("burst manifest identity", ("framebuffer_negative_control",
                                   "manifest_sha256"), "0" * 64)
reject("animated window", ("framebuffer_negative_control",
                            "unique_frame_hashes"), 1)
reject("evidence tier", ("evidence_tier",), "PAIRED_EMULATOR")
reject("physical status", ("physical_saturn",), "PASS")

print("REIMPLEMENT-13 emulator MCP capture: PASS (9 mutations rejected)")
