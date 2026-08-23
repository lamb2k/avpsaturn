#!/usr/bin/env python3
"""Prepare the ignored exact-release INTEGRATE-03 review package."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
TASK_ID = "INTEGRATE-03-PLAYABLE-SLICE"
EXPECTED_ISO_SHA256 = (
    "8699d5c642f7e3732de1d00c884ba4cd620e4e35bd036d8bacca8a74030ee8c4"
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
    state.pop("slice_player_action_frame", None)
    state.pop("slice_enemy_action_frame", None)
    return state


def main() -> int:
    run_1 = SOURCE / "run-1"
    run_2 = SOURCE / "run-2"
    build_1 = read_json(run_1 / "build.json")
    build_2 = read_json(run_2 / "build.json")
    readback_1 = read_json(run_1 / "readback.json")
    readback_2 = read_json(run_2 / "readback.json")
    trace_1 = read_json(run_1 / "scene-trace.json")
    trace_2 = read_json(run_2 / "scene-trace.json")

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
    assert trace_1["result"] == trace_2["result"] == "PASS"
    assert trace_1["samples"] == trace_2["samples"]
    assert trace_1["contacts"] == [600, 1200, 1800, 2400]

    DESTINATION.mkdir(parents=True, exist_ok=True)
    before_clip = DESTINATION / "review-correction-2-before.gif"
    before_sources = [
        DESTINATION / "run-1-hit.png",
        DESTINATION / "run-1-ko.png",
        DESTINATION / "run-2-hit.png",
        DESTINATION / "run-2-ko.png",
    ]
    if not before_clip.exists():
        assert all(path.is_file() for path in before_sources)
        images = [Image.open(path).convert(
            "P", palette=Image.Palette.ADAPTIVE, colors=256)
                  for path in before_sources]
        images[0].save(before_clip, save_all=True, append_images=images[1:],
                       duration=900, loop=0, optimize=False, disposal=2)

    copied = []
    for run_name in ("run-1", "run-2"):
        run_source = SOURCE / run_name
        for name in (
            "build.json",
            "iso-normalization.json",
            "readback.json",
            "scene-trace.json",
            "hit.png",
            "ko.png",
        ):
            source = run_source / name
            target = DESTINATION / f"{run_name}-{name}"
            shutil.copy2(source, target)
            copied.append(
                {"path": target.name, "bytes": target.stat().st_size, "sha256": sha256(target)}
            )
    after_clip = DESTINATION / "review-correction-2-after.gif"
    shutil.copy2(run_1 / "scene-after.gif", after_clip)
    copied.append({"path": after_clip.name, "bytes": after_clip.stat().st_size,
                   "sha256": sha256(after_clip)})
    copied.append({"path": before_clip.name, "bytes": before_clip.stat().st_size,
                   "sha256": sha256(before_clip)})
    for frame in (45, 46, 320, 588, 599, 600, 601, 620, 637,
                  1200, 1800, 2400, 2420, 2480):
        source = run_1 / f"scene-{frame:04d}.png"
        target = DESTINATION / source.name
        shutil.copy2(source, target)
        copied.append({"path": target.name, "bytes": target.stat().st_size,
                       "sha256": sha256(target)})
    visual_qa = run_1 / "visual-qa.json"
    assert visual_qa.is_file()
    target_visual_qa = DESTINATION / "visual-qa.json"
    shutil.copy2(visual_qa, target_visual_qa)
    copied.append({"path": target_visual_qa.name,
                   "bytes": target_visual_qa.stat().st_size,
                   "sha256": sha256(target_visual_qa)})

    summary = {
        "schema": 1,
        "task_id": TASK_ID,
        "candidate_commit": build_1["source_commit"],
        "compile_profile": build_1["compile_profile"],
        "manifest_profile": build_1["manifest_profile"],
        "normalized_iso_sha256": EXPECTED_ISO_SHA256,
        "paired_emulator_result": "PASS",
        "paired_synchronized_trace_result": "PASS / 271 exact samples",
        "ai_visual_qa": "PASS / correlated with synchronized trace",
        "review_focus": [
            "continuous camera pan, approach, attack, contact, HIT/recovery, later contacts, and KO",
            "no camera reset after the first contact",
            "continuous class 0x1F street-alien identity across walk, HIT, and KO",
            "player and class 0x1F enemy alignment at HIT and KO",
            "camera and two-plane stage presentation",
            "P1 and P2 HUD color and placement",
            "PCM cue and CDDA playback",
        ],
        "full_lane": {
            "status": "NOT_RERUN_BY_REVIEW_CORRECTION_2",
            "prior_status": "FAIL",
            "prior_scope": "out-of-card generated-artifact drift",
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
        "Review the preserved rejected-candidate checkpoint montage, continuous "
        "corrected after clip, "
        "paired exact trace, and the running exact release. Focus first on "
        "camera/actor coherence and visible combat engagement, then actor identity, "
        "camera/stage, both HUDs, and audio.\n\n"
        f"ISO SHA-256: `{EXPECTED_ISO_SHA256}`\n\n"
        "This is emulator/user evidence only. Physical Saturn is UNRUN. Full was "
        "not rerun for Review correction 2; its prior result separately reports "
        "three out-of-card generated-artifact drifts.\n\n"
        f"{QUESTION}\n",
        encoding="utf-8",
    )
    print(f"Prepared {DESTINATION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
