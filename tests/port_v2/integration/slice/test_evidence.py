#!/usr/bin/env python3
"""Validate paired exact-release INTEGRATE-03 emulator evidence."""

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
BUILD = ROOT / "build/port_v2/integration/slice"


def load(path):
    return json.loads(path.read_text(encoding="ascii"))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_state(report, name):
    state = dict(report[name])
    state.pop("slice_frame_stage", None)
    return state


def main():
    builds = [load(BUILD / f"run-{run}/build.json") for run in (1, 2)]
    normals = [load(BUILD / f"run-{run}/iso-normalization.json")
               for run in (1, 2)]
    reads = [load(BUILD / f"run-{run}/readback.json") for run in (1, 2)]
    require(builds[0] == builds[1], "exact release builds are not identical")
    require(builds[0]["compile_profile"] == "release-normal-release" and
            builds[0]["manifest_profile"] == "normal-release" and
            builds[0]["exact_normal_release"] is True,
            "paired build is not the exact normal release")
    require(normals[0]["normalized_iso_sha256"] ==
            normals[1]["normalized_iso_sha256"],
            "normalized release ISO is not deterministic")
    for report, build, normal in zip(reads, builds, normals):
        require(report["result"] == "PASS" and
                report["physical_saturn"] == "UNRUN" and
                report["emulator"]["evidence_tier"] == "ONE_EMULATOR",
                "evidence result or tier drifted")
        require(report["iso_sha256"] ==
                build["artifacts"]["game_iso"]["sha256"] ==
                normal["normalized_iso_sha256"] and
                normal["production_payload_changed"] is False,
                "build, normalization, and readback identities disagree")
        for name in ("hit_state", "ko_state", "final_state"):
            state = report[name]
            require(state["runtime_ready"] == 1 and
                    state["slice_ready"] == 1 and
                    state["slice_actor_count"] == 2 and
                    state["slice_asset_failures"] == 0 and
                    state["slice_late_reads"] == 0 and
                    state["slice_fallback_used"] == 0 and
                    state["slice_canaries_ok"] == 1 and
                    state["slice_physical_saturn"] == 0 and
                    state["slice_init_stage"] == 17 and
                    state["stage_port_lock_ok"] == 1 and
                    state["hud_port_lock_ok"] == 1 and
                    state["pcm_port_lock_ok"] == 1 and
                    state["cdda_port_lock_ok"] == 1 and
                    state["enemy_render_count"] > 0,
                    f"{name} lost a promoted subsystem or safety invariant")
        require(report["hit_state"]["slice_frame"] == 605 and
                report["hit_state"]["slice_combat_events"] == 1 and
                report["hit_state"]["slice_hit_count"] == 1 and
                report["hit_state"]["slice_review_phase"] == 3 and
                report["ko_state"]["slice_frame"] == 2480 and
                report["ko_state"]["slice_combat_events"] == 4 and
                report["ko_state"]["slice_ko_count"] == 1 and
                report["ko_state"]["slice_review_phase"] == 4 and
                report["final_state"]["slice_frame"] == 3000 and
                report["final_state"]["slice_cdda_active"] == 0 and
                report["final_state"]["slice_cdda_transitions"] == 2,
                "exact HIT, KO, or ownership checkpoint drifted")
        for shot in report["screenshots"].values():
            path = ROOT / shot["path"]
            require(path.is_file() and sha(path) == shot["sha256"],
                    "scanout screenshot identity drifted")
            with Image.open(path) as image:
                colours = image.convert("RGB").getcolors(
                    maxcolors=image.width * image.height)
                require(image.width > 300 and image.height > 200 and
                        colours is not None and len(colours) >= 16,
                        "scanout screenshot is empty")
    for name in ("hit_state", "ko_state", "final_state"):
        require(stable_state(reads[0], name) == stable_state(reads[1], name),
                f"paired semantic state drifted at {name}")
    print("INTEGRATE-03 paired exact-release emulator evidence: PASS")


if __name__ == "__main__":
    main()
