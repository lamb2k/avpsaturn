#!/usr/bin/env python3
"""Prepare the ignored exact-release INTEGRATE-03 review package."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
TASK_ID = "INTEGRATE-03-PLAYABLE-SLICE"
SOURCE = ROOT / "build" / "port_v2" / "integration" / "slice"
REFERENCE = (
    ROOT / "build" / "feedback" /
    "REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION"
)
DESTINATION = ROOT / "build" / "feedback" / TASK_ID
QUESTION = (
    "What should remain unchanged, what looks or feels wrong, and which issue "
    "should be fixed first?"
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_state(report: dict, name: str) -> dict:
    state = dict(report[name])
    for key in (
        "slice_frame_stage", "slice_frame", "slice_stability_frames",
        "slice_stage_submissions", "slice_player_action_frame",
        "slice_enemy_action_frame", "slice_source_sample",
    ):
        state.pop(key, None)
    return state


def source_validator():
    path = HERE / "render_identity.py"
    spec = importlib.util.spec_from_file_location("slice_render_identity", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def actor_comparator():
    path = HERE / "actor_image_compare.py"
    spec = importlib.util.spec_from_file_location("slice_actor_compare", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_record(source: Path, target: Path, records: list[dict]) -> None:
    assert source.is_file(), source
    shutil.copy2(source, target)
    records.append({
        "path": target.name,
        "bytes": target.stat().st_size,
        "sha256": sha256(target),
    })


def save_combat_clip(
        gif_path: Path, sample_frames: list[int], target: Path,
        duration_ms: int) -> None:
    selected = []
    sample_index = 0
    with Image.open(gif_path) as image:
        for gif_index in range(image.n_frames):
            image.seek(gif_index)
            # GIF stores durations in 10 ms units and coalesces identical
            # adjacent samples.  Expand each duration back to the 167 ms
            # collector ledger before selecting the cadence-1 combat window.
            repeats = round(image.info.get("duration", 167) / 167)
            rendered = image.convert("RGB").copy()
            for _ in range(repeats):
                assert sample_index < len(sample_frames)
                frame_number = sample_frames[sample_index]
                if 583 <= frame_number <= 879:
                    selected.append(rendered)
                sample_index += 1
    assert sample_index == len(sample_frames)
    assert len(selected) == 297
    selected[0].save(
        target, format="WEBP", save_all=True, append_images=selected[1:],
        duration=duration_ms, loop=0, lossless=True, method=4)


def main() -> int:
    run_1 = SOURCE / "run-1"
    run_2 = SOURCE / "run-2"
    builds = [read_json(run / "build.json") for run in (run_1, run_2)]
    reads = [read_json(run / "readback.json") for run in (run_1, run_2)]
    traces = [read_json(run / "scene-trace.json") for run in (run_1, run_2)]
    normals = [
        read_json(run / "iso-normalization.json") for run in (run_1, run_2)
    ]
    iso_sha = builds[0]["artifacts"]["game_iso"]["sha256"]

    assert builds[1]["artifacts"]["game_iso"]["sha256"] == iso_sha
    assert (normals[0]["normalized_iso_sha256"] ==
            normals[1]["normalized_iso_sha256"] == iso_sha)
    for build in builds:
        assert build["task_id"] == TASK_ID
        assert build["exact_normal_release"] is True
        assert build["compile_profile"] == "release-normal-release"
        assert build["manifest_profile"] == "normal-release"
        assert build["physical_saturn"] == "UNRUN"
    for state_name in ("hit_state", "ko_state", "final_state"):
        for report in reads:
            state = report[state_name]
            assert (state["slice_stage_submissions"] ==
                    state["slice_stability_frames"] * 3)
        assert (stable_state(reads[0], state_name) ==
                stable_state(reads[1], state_name))

    source_contract = read_json(
        ROOT / "data" / "avsp_source_combat_presentation_contract.json")
    validator = source_validator()
    for trace in traces:
        assert trace["result"] == "PASS"
        assert trace["fidelity"] == "SOURCE_BOUND_WITH_ADAPTED_INPUT"
        assert (trace["clip"] is None or
                trace["clip"]["combat_cadence"] == 1)
        assert trace["contacts"] == [600, 646, 693, 739]
        assert trace["post_ko_framing"] == {
            "intentional_exit": False,
            "player_world_x": 440,
            "camera_world_x": 161,
            "player_screen_x": 103,
            "aperture": [-176, 175],
            "result": "VISIBLE_HOLD",
        }
        assert (validator.validate_trace(trace, source_contract)["result"] ==
                "PASS")
    assert traces[0]["samples"] == traces[1]["samples"]

    full = read_json(ROOT / "build" / "verification" / "full.json")
    assert full["status"] == "PASS"
    DESTINATION.mkdir(parents=True, exist_ok=True)
    copied: list[dict] = []

    for run_name, run_source in (("run-1", run_1), ("run-2", run_2)):
        names = [
            "build.json", "iso-normalization.json", "readback.json",
            "scene-trace.json", "hit.png", "ko.png",
        ]
        if run_name == "run-1":
            names.append("visual-qa.json")
        for name in names:
            copy_record(
                run_source / name, DESTINATION / f"{run_name}-{name}", copied)

    final_iso = DESTINATION / "integrate-03-source-bound-review.iso"
    copy_record(ROOT / "game.iso", final_iso, copied)
    assert sha256(final_iso) == iso_sha

    saturn_full = DESTINATION / "saturn-source-bound-full-speed.webp"
    saturn_slow = DESTINATION / "saturn-source-bound-slow-motion.webp"
    save_combat_clip(
        run_1 / "scene-after.gif", traces[0]["sample_frames"],
        saturn_full, 17)
    save_combat_clip(
        run_1 / "scene-after.gif", traces[0]["sample_frames"],
        saturn_slow, 100)
    copied.extend([
        {"path": saturn_full.name, "bytes": saturn_full.stat().st_size,
         "sha256": sha256(saturn_full)},
        {"path": saturn_slow.name, "bytes": saturn_slow.stat().st_size,
         "sha256": sha256(saturn_slow)},
    ])

    key_frames = sorted(int(frame) for frame in traces[0]["key_images"])
    for frame in key_frames:
        source = run_1 / f"scene-{frame:04d}.png"
        copy_record(source, DESTINATION / source.name, copied)

    references = (
        "source-full-speed.webp",
        "mame-source-event-contact-sheet.png",
        "collision-overlay-1.png",
        "collision-overlay-2.png",
        "collision-overlay-3.png",
        "collision-overlay-4.png",
        "alien-visual-family-comparison.png",
        "source-vs-saturn-temporal-strips.png",
        "attack-timing-comparison.json",
        "player-grounding-trace.json",
        "frame-indexed-findings.json",
        "visual-findings.json",
    )
    for name in references:
        copy_record(REFERENCE / name, DESTINATION / f"source-reference-{name}",
                    copied)
    copy_record(
        ROOT / "data" / "avsp_source_combat_presentation_contract.json",
        DESTINATION / "mame-source-combat-contract.json", copied)
    comparison = actor_comparator().generate()
    assert comparison["result"] == "PASS"
    assert comparison["frames_checked"] == 297
    assert all(item["result"] == "REJECTED"
               for item in comparison["negative_controls"])
    shutil.copy2(
        DESTINATION / "actor-image-direct-inspection.json",
        DESTINATION / "integrated-frame-indexed-findings.json")
    for name in (
            "actor-image-metrics.json", "visual-findings.json",
            "actor-image-direct-inspection.json",
            "integrated-frame-indexed-findings.json",
            "actor-silhouette-comparison.png", "actor-flagged-pairs.png"):
        path = DESTINATION / name
        copied.append({"path": name, "bytes": path.stat().st_size,
                       "sha256": sha256(path)})

    summary = {
        "schema": 2,
        "task_id": TASK_ID,
        "candidate_commit": builds[0]["source_commit"],
        "compile_profile": builds[0]["compile_profile"],
        "manifest_profile": builds[0]["manifest_profile"],
        "normalized_iso_sha256": iso_sha,
        "paired_emulator_result": "PASS",
        "paired_synchronized_trace":
            f"PASS / {len(traces[0]['samples'])} samples including 297 cadence-1 combat frames",
        "fidelity": "SOURCE_BOUND_WITH_ADAPTED_INPUT",
        "adapted_scope": traces[0]["adapted_scope"],
        "source_contract": {
            "path": "mame-source-combat-contract.json",
            "origin": "MAME_SOURCE_ONLY",
            "byte_identical_source_reruns": True,
        },
        "candidate_derived_render_hash_contract": "SUPERSEDED / NOT EVIDENCE",
        "actor_image_negative_controls": (
            "PASS / valid wrong alien crop, one-frame Y offset, stale pose, "
            "skipped reaction, and pivot jump rejected"),
        "post_ko_framing": traces[0]["post_ko_framing"],
        "ai_visual_qa": (
            "PASS / calculated cadence-1 actor metrics plus direct inspection "
            "of every automatically flagged pair"),
        "full_lane": "PASS",
        "physical_saturn": "UNRUN",
        "remaining_unknown": [
            "production player control",
            "production enemy AI",
            "physical Saturn capability procedure",
        ],
        "review_question": QUESTION,
        "files": copied,
    }
    (DESTINATION / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (DESTINATION / "README.md").write_text(
        "# INTEGRATE-03 source-bound exact-release review\n\n"
        "Review the source clip and collision overlays first, then the exact "
        "release Saturn full-speed and slow-motion clips. The same measured "
        "source event now supplies each selector, rendered player pose, "
        "collision box, damage, and alien reaction. `visual-findings.json` "
        "is calculated from all 297 cadence frames; its seven same-assembly "
        "record flags are dispositioned in "
        "`actor-image-direct-inspection.json`.\n\n"
        f"ISO SHA-256: `{iso_sha}`\n\n"
        "Only the deterministic input choreography is ADAPTED. Production "
        "player control and enemy AI remain UNKNOWN. Full passes separately; "
        "physical Saturn is UNRUN and remains required.\n\n"
        f"{QUESTION}\n",
        encoding="utf-8")
    print(f"Prepared {DESTINATION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
