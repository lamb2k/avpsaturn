#!/usr/bin/env python3
"""Validate active-P2 HUD fields in paired pinned-emulator readback."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    contract = json.loads((HERE / "player2_hud_contract.json").read_text(
        encoding="utf-8"))
    reads = [json.loads((ROOT / f"build/port_v2/hud_pcm_bench/run-{run}/readback.json").read_text(encoding="ascii")) for run in (1, 2)]
    builds = [json.loads((ROOT / f"build/port_v2/hud_pcm_bench/run-{run}/build.json").read_text(encoding="ascii")) for run in (1, 2)]
    require(builds[0]["artifacts"]["game_iso"]["sha256"] ==
            builds[1]["artifacts"]["game_iso"]["sha256"],
            "P2 HUD target builds are not byte-identical")
    for build in builds:
        for name, digest in {**contract["player2_payload_sha256"],
                             **contract["regression_payload_sha256"]}.items():
            require(build["iso_members"][name]["sha256"] == digest,
                    f"P2 HUD or regression payload drifted: {name}")
    keys = ("state", "health", "energy", "health_fill", "energy_fill",
            "render_count")
    fields = ("p2_hud_state", "p2_health", "p2_energy", "p2_health_fill",
              "p2_energy_fill", "p2_hud_render_count")
    for report in reads:
        require(report["result"] == "PASS" and
                report["physical_saturn"] == "UNRUN",
                "P2 HUD emulator result failed or overstated evidence")
        for label, expected in contract["states"].items():
            state = report["samples"][label]
            require(state["relative_frame"] == expected["frame"] and
                    state["p2_hud_binding_ok"] == 1,
                    f"P2 HUD binding failed at {label}")
            require(tuple(state[field] for field in fields) ==
                    tuple(expected[key] for key in keys),
                    f"P2 HUD semantic state drifted at {label}")
        negative = report["samples"]["negative"]
        require(negative["negative_rejections"] ==
                contract["negative_control"]["required_runtime_rejections"],
                "PRESS START substitution was not rejected at runtime")
        together = report["samples"]["together"]
        require((together["pcm_event_frame"], together["pcm_start_frame"],
                 together["pcm_active"]) == (147, 150, 1),
                "approved PCM timing lock drifted")
    print("Player 2 HUD paired emulator evidence: PASS")


if __name__ == "__main__":
    main()
