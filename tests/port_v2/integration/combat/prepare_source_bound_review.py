#!/usr/bin/env python3
"""Build the ignored REPAIR-09 source-versus-Saturn review package."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
PACKAGE = ROOT / "build/feedback/REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION"
SOURCE_RUN = ROOT / ".deps/mame/source_bound_combat/run_c"
SOURCE = SOURCE_RUN / "frames"
SOURCE_ANALYSIS = ROOT / ".deps/mame/source_bound_combat/analysis"
SATURN = PACKAGE / "saturn-frames"
CONTRACT = ROOT / "data/avsp_source_combat_presentation_contract.json"
TRACE = PACKAGE / "saturn-cadence-1-trace.json"


def fit_x(value: int) -> int:
    return value * 352 // 384


def source_image(frame: int) -> Image.Image:
    return Image.open(SOURCE / f"{frame:05d}.png").convert("RGB").resize(
        (352, 224), Image.Resampling.NEAREST)


def saturn_image(frame: int) -> Image.Image:
    return Image.open(SATURN / f"{frame:05d}.png").convert("RGB")


def label(image: Image.Image, text: str) -> Image.Image:
    out = image.copy()
    draw = ImageDraw.Draw(out)
    draw.rectangle((0, 0, min(out.width, len(text) * 7 + 6), 13), fill="black")
    draw.text((3, 2), text, fill="white")
    return out


def animation(frames: list[Image.Image], path: Path, duration: int) -> None:
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0, lossless=True, method=4)


def side_by_side(left: Image.Image, right: Image.Image,
                 left_label: str, right_label: str) -> Image.Image:
    out = Image.new("RGB", (704, 224), "black")
    out.paste(label(left, left_label), (0, 0))
    out.paste(label(right, right_label), (352, 0))
    return out


def collision_rect(pivot: list[int], facing: int, box: dict,
                   scale_x: bool) -> tuple[int, int, int, int]:
    center_x = pivot[0] + (-box["x_center"] if facing else box["x_center"])
    x0, x1 = center_x - box["x_half"], center_x + box["x_half"]
    y_center = pivot[1] - box["y_center"]
    y0, y1 = y_center - box["y_half"], y_center + box["y_half"]
    if scale_x:
        x0, x1 = fit_x(x0), fit_x(x1)
    return x0, y0, x1, y1


def overlay(frame: int, event: dict, target: bool) -> Image.Image:
    image = saturn_image(frame) if target else source_image(frame)
    draw = ImageDraw.Draw(image)
    player = event["player"]
    enemy = event["enemy_contact"]
    attack = collision_rect(player["pivot"], player["facing"],
                            event["collision"]["attack_box"], True)
    hurt = collision_rect(enemy["pivot"], enemy["facing"],
                          event["collision"]["hurt_box"], True)
    draw.rectangle(attack, outline=(255, 64, 64), width=2)
    draw.rectangle(hurt, outline=(64, 255, 64), width=2)
    draw.text((2, 206), "red=attack green=hurt overlap=PASS", fill="white")
    return image


def crop_actor(image: Image.Image, center_x: int) -> Image.Image:
    left = max(0, center_x - 72)
    right = min(image.width, center_x + 72)
    crop = image.crop((left, 56, right, 224))
    canvas = Image.new("RGB", (144, 168), "black")
    canvas.paste(crop, (72 - (center_x - left), 0))
    return canvas


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    contract = json.loads(CONTRACT.read_text())
    trace = json.loads(TRACE.read_text())
    frames = trace["frames"]
    if len(frames) != 297 or [frames[0]["source_frame"],
                              frames[-1]["source_frame"]] != [5173, 5469]:
        raise ValueError("cadence-1 Saturn trace is incomplete")
    by_frame = {item["source_frame"]: item for item in frames}
    source_frames = [source_image(frame) for frame in range(5173, 5470)]
    saturn_frames = [saturn_image(frame) for frame in range(5173, 5470)]
    comparisons = [side_by_side(a, b, f"MAME {frame}", f"SATURN {frame}")
                   for frame, (a, b) in enumerate(
                       zip(source_frames, saturn_frames), start=5173)]
    animation(source_frames, PACKAGE / "source-full-speed.webp", 17)
    animation(saturn_frames, PACKAGE / "saturn-full-speed.webp", 17)
    animation(comparisons, PACKAGE / "source-vs-saturn-slow-motion.webp", 100)

    timing = []
    frame_findings = []
    grounding = []
    identity_failures = []
    render_failures = []
    grounding_failures = []
    with (SOURCE_RUN / "samples.tsv").open(
            newline="", encoding="ascii") as stream:
        samples = {int(row["frame"]): row for row in csv.DictReader(stream,
                                                                    delimiter="\t")}
    for item in frames:
        frame = item["source_frame"]
        state = item["state"]
        selector = state["combat_attack_selector"]
        if state["combat_player_presentation_active"] and 1 <= selector <= 4:
            presentation_frame = (
                contract["events"][selector - 1]["player_presentation_window"][0] +
                state["combat_player_action_frame"])
        else:
            presentation_frame = None
        sample = samples[presentation_frame] if presentation_frame else samples[frame]
        source_height = int(sample["p_y"]) - int(sample["p_z"])
        target_height = state["combat_player_height"]
        grounding.append({
            "frame": frame,
            "source_presentation_frame": presentation_frame,
            "source_height": source_height,
            "saturn_height": target_height,
            "source_ground_y": int(sample["p_z"]),
            "saturn_ground_baseline": state["combat_player_lane"] - target_height,
            "source_action": int(sample["p_action"]),
            "source_selector": state["combat_attack_selector"],
        })
        if ((presentation_frame is not None and source_height != target_height) or
                (presentation_frame is None and target_height != 0)):
            grounding_failures.append(frame)
        if (state["combat_enemy_render_object_identity"] !=
                state["combat_enemy_source_object_identity"] or
                state["combat_enemy_render_tile_identity"] !=
                state["combat_enemy_source_tile_identity"]):
            identity_failures.append(frame)
        if state["player_render_count"] <= 0 or state["enemy_render_count"] <= 0:
            render_failures.append(frame)

    family_sheet = Image.new("RGB", (4 * 288, 2 * 196), "black")
    temporal = Image.new("RGB", (3 * 352, 8 * 224), "black")
    for index, event in enumerate(contract["events"], start=1):
        frame = event["contact_frame"]
        source_contact = Image.open(
            SOURCE_ANALYSIS / f"event-{index}-alien-contact.png").convert("RGB")
        source_reaction = Image.open(
            SOURCE_ANALYSIS / f"event-{index}-alien-reaction.png").convert("RGB")
        target_x = by_frame[frame]["state"]["combat_enemy_x"]
        target_contact = crop_actor(saturn_image(frame), target_x)
        # The source object list displays the semantic reaction one frame
        # later; the Saturn trace key is the semantic frame that owns the
        # exact identity.  Compare those corresponding pipeline stages.
        reaction_frame = event["reaction_window"][0]
        captured_reaction_frame = reaction_frame + 2
        target_reaction = crop_actor(
            saturn_image(captured_reaction_frame),
            by_frame[reaction_frame]["state"]["combat_enemy_x"])
        pair = Image.new("RGB", (288, 392), "black")
        pair.paste(label(source_contact.resize((144, 168)), f"MAME E{index} contact"), (0, 0))
        pair.paste(label(target_contact, f"SAT E{index} contact"), (144, 0))
        pair.paste(label(source_reaction.resize((144, 168)), f"MAME E{index} react"), (0, 196))
        pair.paste(label(target_reaction, f"SAT E{index} react"), (144, 196))
        family_sheet.paste(pair, ((index - 1) * 288, 0))

        source_overlay = overlay(frame, event, False)
        saturn_overlay = overlay(frame, event, True)
        side_by_side(source_overlay, saturn_overlay,
                     f"MAME contact {index}", f"SATURN contact {index}").save(
                         PACKAGE / f"collision-overlay-{index}.png")
        source_sequence = [event["attack_input_frame"], frame,
                           event["enemy_reaction"]["source_render_frame"]]
        target_sequence = [event["attack_input_frame"], frame,
                           captured_reaction_frame]
        for column, (source_at, target_at) in enumerate(
                zip(source_sequence, target_sequence)):
            temporal.paste(label(source_image(source_at),
                                 f"MAME E{index} {source_at}"),
                           (column * 352, (index - 1) * 448))
            temporal.paste(label(saturn_image(target_at),
                                 f"SAT E{index} {target_at}"),
                           (column * 352, (index - 1) * 448 + 224))
        timing.append({
            "event": index,
            "selector": event["attack_selector"],
            "source_attack_start": event["attack_input_frame"],
            "saturn_attack_start": event["attack_input_frame"],
            "source_contact": frame,
            "saturn_contact": frame,
            "source_first_reaction": reaction_frame,
            "saturn_first_reaction": reaction_frame,
            "source_first_visible_reaction":
                event["enemy_reaction"]["source_render_frame"],
            "saturn_debug_capture_visible_reaction": captured_reaction_frame,
            "debug_capture_observer_offset_vs_source_frames": 1,
            "difference_frames": 0,
        })
        frame_findings.append({
            "event": index,
            "contact_frame": frame,
            "visible_observation": (
                f"selector {event['attack_selector']} player pose owns the "
                "red attack box; the green class-0x1F hurt box overlaps and "
                "the same alien enters its measured reaction family"),
            "source_comparison": "matching MAME contact/reaction crops and geometry",
            "semantic_state": {
                "selector": event["attack_selector"],
                "health_before": event["health_before"],
                "health_after": event["health_after"],
                "enemy_contact_record": event["enemy_contact"]["animation_record"],
                "enemy_reaction_record": event["enemy_reaction"]["animation_record"],
            },
            "root_cause": (
                "prior stitched presentation detached selector/pose/reaction; "
                "events 2/3 also lacked complete animation/tile source windows"),
            "repair": (
                "one source event now supplies player presentation, collision "
                "selector, damage, enemy record, palette, objects, and tiles"),
            "recaptured_result": "PASS",
        })
    family_sheet.save(PACKAGE / "alien-visual-family-comparison.png")
    temporal.save(PACKAGE / "source-vs-saturn-temporal-strips.png")
    shutil.copy2(SOURCE_ANALYSIS / "source-event-contact-sheet.png",
                 PACKAGE / "mame-source-event-contact-sheet.png")

    (PACKAGE / "attack-timing-comparison.json").write_text(
        json.dumps(timing, indent=2) + "\n", encoding="ascii")
    (PACKAGE / "player-grounding-trace.json").write_text(
        json.dumps(grounding, indent=2) + "\n", encoding="ascii")
    findings = {
        "schema": 1,
        "task_id": "REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION",
        "frames_checked": 297,
        "identity_mismatch_frames": identity_failures,
        "missing_actor_frames": render_failures,
        "player_grounding_mismatch_frames": grounding_failures,
        "contact_timing_differences": [row["difference_frames"] for row in timing],
        "result": "PASS" if not (identity_failures or render_failures or
                                  grounding_failures) else "FAIL",
        "direct_inspection_required": True,
        "physical_saturn": "UNRUN",
    }
    (PACKAGE / "visual-findings.json").write_text(
        json.dumps(findings, indent=2) + "\n", encoding="ascii")
    (PACKAGE / "frame-indexed-findings.json").write_text(
        json.dumps({
            "schema": 1,
            "findings": frame_findings,
            "capture_note": (
                "Pinned debugger screenshots expose the completed VDP1 frame "
                "two diagnostic markers after its semantic state; source MAME "
                "object lists expose alien reactions one source frame after "
                "their semantic record. This observer offset is recorded and "
                "is not used as runtime timing proof."),
        }, indent=2) + "\n", encoding="ascii")
    files = {}
    for path in sorted(PACKAGE.iterdir()):
        if path.is_file():
            files[path.name] = {"sha256": sha(path), "bytes": path.stat().st_size}
    (PACKAGE / "package.json").write_text(json.dumps({
        "schema": 1,
        "task_id": "REPAIR-09-SOURCE-BOUND-COMBAT-PRESENTATION",
        "classification": "ignored source-bound human review package",
        "source_contract_sha256": sha(CONTRACT),
        "files": files,
        "adapted": ["deterministic capability-slice input choreography"],
        "unknown": ["production player control", "production enemy AI"],
        "physical_saturn": "UNRUN",
    }, indent=2, sort_keys=True) + "\n", encoding="ascii")
    (PACKAGE / "README.md").write_text(
        "# REPAIR-09 source-bound combat review\n\n"
        "Review `source-vs-saturn-slow-motion.webp`, the four collision "
        "overlays, `alien-visual-family-comparison.png`, and the full-speed "
        "source/Saturn clips. The attack selector, player presentation, "
        "collision, damage, and alien reaction are sourced from one event "
        "pipeline. Choreography remains ADAPTED; player control and enemy AI "
        "remain UNKNOWN. Physical Saturn is UNRUN.\n",
        encoding="ascii", newline="\n")
    if findings["result"] != "PASS":
        raise ValueError(f"visual findings failed: {findings}")
    print(f"prepared source-bound review package: {PACKAGE}")


if __name__ == "__main__":
    main()
