#!/usr/bin/env python3
"""Prepare the ignored exact-release INTEGRATE-03 review package."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
TASK_ID = "INTEGRATE-03-PLAYABLE-SLICE"
EXPECTED_ISO_SHA256 = (
    "f1be594e8ceab37473333c46ff80b11a9a110c6969b7fc6c863638d042b2ba2b"
)
SOURCE = ROOT / "build" / "port_v2" / "integration" / "slice"
DESTINATION = ROOT / "build" / "feedback" / TASK_ID
QUESTION = (
    "What should remain unchanged, what looks or feels wrong, and which issue "
    "should be fixed first?"
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_state(report: dict, name: str) -> dict:
    state = dict(report[name])
    state.pop("slice_frame_stage", None)
    state.pop("slice_frame", None)
    state.pop("slice_stability_frames", None)
    state.pop("slice_stage_submissions", None)
    return state


def main() -> int:
    run_1 = SOURCE / "run-1"
    run_2 = SOURCE / "run-2"
    build_1 = read_json(run_1 / "build.json")
    build_2 = read_json(run_2 / "build.json")
    readback_1 = read_json(run_1 / "readback.json")
    readback_2 = read_json(run_2 / "readback.json")

    for build in (build_1, build_2):
        assert build["task_id"] == TASK_ID
        assert build["exact_normal_release"] is True
        assert build["compile_profile"] == "release-normal-release"
        assert build["manifest_profile"] == "normal-release"
        assert build["artifacts"]["game_iso"]["sha256"] == EXPECTED_ISO_SHA256
        assert build["physical_saturn"] == "UNRUN"

    for state_name in ("hit_state", "ko_state", "final_state"):
        for report in (readback_1, readback_2):
            state = report[state_name]
            assert state["slice_stage_submissions"] == \
                state["slice_stability_frames"] * 3
        assert stable_state(readback_1, state_name) == stable_state(
            readback_2, state_name
        )

    DESTINATION.mkdir(parents=True, exist_ok=True)
    copied = []
    for run_name in ("run-1", "run-2"):
        run_source = SOURCE / run_name
        for name in (
            "build.json",
            "iso-normalization.json",
            "readback.json",
            "hit.png",
            "ko.png",
        ):
            source = run_source / name
            target = DESTINATION / f"{run_name}-{name}"
            shutil.copy2(source, target)
            copied.append(
                {"path": target.name, "bytes": target.stat().st_size, "sha256": sha256(target)}
            )

    summary = {
        "schema": 1,
        "task_id": TASK_ID,
        "candidate_commit": build_1["source_commit"],
        "compile_profile": build_1["compile_profile"],
        "manifest_profile": build_1["manifest_profile"],
        "normalized_iso_sha256": EXPECTED_ISO_SHA256,
        "paired_emulator_result": "PASS",
        "review_focus": [
            "visible player attack, alien contact reaction, and final KO",
            "player and class 0x1F enemy alignment at HIT and KO",
            "camera and two-plane stage presentation",
            "P1 and P2 HUD color and placement",
            "PCM cue and CDDA playback",
        ],
        "full_lane": {
            "status": "FAIL",
            "scope": "out-of-card generated-artifact drift",
            "artifacts": [
                "data/avsp_palette_coverage.json",
                "data/avsp_translation_boundary.json",
                "data/avsp_vertical_slice_oracle_manifest.json",
            ],
        },
        "physical_saturn": "UNRUN",
        "review_question": QUESTION,
        "files": copied,
    }
    (DESTINATION / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    (DESTINATION / "README.md").write_text(
        "# INTEGRATE-03 exact-release review\n\n"
        "Review the paired HIT and KO screenshots and the running exact release. "
        "Focus first on visible combat engagement, then actor alignment, "
        "camera/stage, both HUDs, and audio.\n\n"
        f"ISO SHA-256: `{EXPECTED_ISO_SHA256}`\n\n"
        "This is emulator/user evidence only. Physical Saturn is UNRUN. The Full "
        "lane separately reports three out-of-card generated-artifact drifts.\n\n"
        f"{QUESTION}\n",
        encoding="utf-8",
    )
    print(f"Prepared {DESTINATION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
