#!/usr/bin/env python3
"""HUD/PCM salvage contract and non-vacuous perturbation controls."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(contract: dict[str, object]) -> None:
    require(contract["task_id"] == "REPAIR-05-HUD-COLORS",
            "task identity drifted")
    palette = contract["hud_palette"]
    require((palette["source_offset"], palette["binding_ok"]) == (1, 1),
            "HUD palette binding drifted")
    require(palette["semantic_colors"] == {
        "yellow": {"source_index": 1, "rgb888": [255, 255, 0],
                   "saturn_cram": 33791},
        "red": {"source_index": 2, "rgb888": [255, 0, 0],
                "saturn_cram": 32799},
        "energy": {"source_index": 3, "rgb888": [187, 255, 119],
                   "saturn_cram": 48119},
        "empty": {"source_index": 4, "rgb888": [136, 136, 136],
                  "saturn_cram": 50737},
    }, "HUD semantic CRAM colors drifted")
    evidence = json.loads((ROOT / contract["palette_evidence"]).read_text(
        encoding="utf-8"))
    require(evidence["task_id"] == contract["task_id"] and
            evidence["binding"] == {
                "source_offset": 1,
                "jo_palette_entry": 0,
                "first_visible_source_index": 1,
                "first_visible_sprite_pen": 1,
            } and
            evidence["semantic_colors"] == palette["semantic_colors"] and
            evidence["physical_saturn"] == "UNRUN",
            "HUD palette repair evidence drifted")
    states = contract["hud_states"]
    require(set(states) == {"zero", "mid", "full", "pcm_only"},
            "zero/mid/full/PCM-only coverage drifted")
    expected = {
        "zero": (20, 0, 0, 0, 0, 0, 3),
        "mid": (140, 1, 50, 32, 57, 30, 3),
        "full": (260, 2, 101, 64, 116, 59, 3),
        "pcm_only": (420, -1, 50, 32, 57, 30, 0),
    }
    for name, values in expected.items():
        state = states[name]
        actual = tuple(state[key] for key in (
            "frame", "state", "health", "energy", "health_fill",
            "energy_fill", "render_count"))
        require(actual == values, f"{name} HUD state drifted")
    pcm = contract["pcm"]
    require(pcm["semantic_event_frames"] == [147, 387] and
            pcm["start_frames"] == [150, 390] and
            pcm["end_frames"] == [200, 440],
            "deterministic PCM schedule drifted")
    require(pcm["source_start_delay_frames"] == 3 and
            pcm["duration_frames"] == 50 and
            (pcm["sample_rate"], pcm["channels"], pcm["sample_bits"]) ==
            (44100, 2, 16), "PCM source timing/format drifted")
    require(set(contract["negative_controls"]) == {
        "missing HUD asset", "invalid PCM metadata", "missing PCM asset",
        "rejected zero-based HUD palette binding"},
        "required negative controls drifted")
    require(contract["disabled_systems"] ==
            ["CDDA", "combat", "camera movement", "stage expansion"],
            "disabled-system boundary drifted")
    require(contract["physical_saturn"] == "UNRUN",
            "physical Saturn evidence was overstated")


def static_wiring(contract: dict[str, object]) -> None:
    for relative, expected in contract["source_evidence_sha256"].items():
        require(sha256(ROOT / relative) == expected,
                f"source evidence changed: {relative}")
    require(sha256(ROOT / "tests/port_v2/stage_bench/stage_contract.json") ==
            contract["approved_stage_contract_sha256"],
            "approved stage contract changed")
    files = {
        "build": (ROOT / "build.ps1").read_text(encoding="utf-8"),
        "verify": (ROOT / "verify.ps1").read_text(encoding="utf-8"),
        "make": (ROOT / "makefile").read_text(encoding="utf-8"),
        "source": (ROOT / "main.c").read_text(encoding="utf-8"),
    }
    for token, name in (
        ("HudPcmSalvageBench", "build"),
        ("hud-pcm-salvage-bench", "build"),
        ("HudPcmSalvageBench", "verify"),
        ("AVSP_HUD_PCM_SALVAGE_BENCH", "make"),
        ("avsp_diag_hud_pcm_negative_rejections", "source"),
        ("avsp_diag_hud_palette_binding_ok", "source"),
        ("avsp_hud_palette[index + 1]", "source"),
        ("hud_palette_binding_valid(rejected_zero_based, 1)", "source"),
        ("hud_pcm_bench_frame_callback", "source"),
    ):
        require(token in files[name], f"missing HUD/PCM wiring: {token}")
    callback = files["source"].split(
        "static void hud_pcm_bench_frame_callback", 1)[1].split(
            "static CapInput read_input", 1)[0]
    require("jo_audio_play_cd_track" not in callback,
            "HUD/PCM bench enabled CDDA")


def negative_controls(original: dict[str, object]) -> None:
    mutations = []
    wrong_fill = copy.deepcopy(original)
    wrong_fill["hud_states"]["full"]["health_fill"] = 132
    mutations.append(("wrong HUD fill", wrong_fill))
    wrong_palette_offset = copy.deepcopy(original)
    wrong_palette_offset["hud_palette"]["source_offset"] = 0
    mutations.append(("wrong HUD palette offset", wrong_palette_offset))
    wrong_palette_color = copy.deepcopy(original)
    wrong_palette_color["hud_palette"]["semantic_colors"]["yellow"][
        "saturn_cram"] = 0
    mutations.append(("wrong HUD palette color", wrong_palette_color))
    wrong_delay = copy.deepcopy(original)
    wrong_delay["pcm"]["start_frames"][0] = 149
    mutations.append(("wrong PCM delay", wrong_delay))
    wrong_duration = copy.deepcopy(original)
    wrong_duration["pcm"]["end_frames"][1] = 439
    mutations.append(("wrong PCM duration", wrong_duration))
    missing_control = copy.deepcopy(original)
    missing_control["negative_controls"].pop()
    mutations.append(("missing palette control", missing_control))
    cdda = copy.deepcopy(original)
    cdda["disabled_systems"].remove("CDDA")
    mutations.append(("CDDA enabled", cdda))
    for name, mutation in mutations:
        try:
            validate(mutation)
        except AssertionError:
            continue
        raise AssertionError(f"{name} perturbation was not rejected")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    contract = json.loads((HERE / "hud_pcm_contract.json").read_text(
        encoding="utf-8"))
    validate(contract)
    static_wiring(contract)
    if args.negative_control:
        negative_controls(contract)
        print("HUD/PCM perturbation controls: PASS")
    else:
        print("HUD/PCM contract: PASS")


if __name__ == "__main__":
    main()
