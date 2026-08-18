#!/usr/bin/env python3
"""Build paired semantic models from tracked deterministic evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def cps2_model(report: dict[str, object]) -> dict[str, object]:
    anchors = report["semantic_anchors"]
    return {
        "title": "MSHvSF CPS-2 semantic model",
        "model_kind": "Evidence-backed behavioral model; not a decompilation",
        "source": "data/mshvsf_cps2_vertical_slice.json",
        "runtime": report["source"],
        "route": {
            "actors": "Ryu/Ken versus Spider-Man/Captain America",
            "control": "P1 scripted; P2 human port held neutral",
            "capture_frames": [
                report["capture"]["first_frame"],
                report["capture"]["last_frame"],
            ],
        },
        "subsystems": [
            {
                "semantic_system": "game_state",
                "proven": "The deterministic frontend reaches the same two-player match on cold replay.",
                "structural_status": "UNRESOLVED",
                "missing": "Mode, round, team, and active-character addresses and writer functions.",
            },
            {
                "semantic_system": "input",
                "proven": "Exact coin, start, direction, and light-punch edges are recorded with frame and 68000 PC samples.",
                "structural_status": "PARTIAL",
                "missing": "Input-buffer address, command parser, and state-transition call path.",
            },
            {
                "semantic_system": "player_structure",
                "proven": "Per-frame work RAM and object-list evidence exists for the complete slice.",
                "structural_status": "UNRESOLVED",
                "missing": "Ryu and Spider-Man actor bases, struct stride, coordinate, velocity, state, animation, collision, and health fields.",
            },
            {
                "semantic_system": "movement_and_animation",
                "proven": "Idle, walk, and jump visual anchors reproduce with contiguous work RAM, object RAM, palette, and CPS register streams.",
                "structural_status": "PARTIAL",
                "missing": "Movement writers, animation-script pointer, duration fields, assembly decoder, and normalized trajectory.",
            },
            {
                "semantic_system": "attack_collision_damage",
                "proven": "Standing light punch and Hadouken visual sequences, projectile collision, and hit reaction are captured.",
                "structural_status": "UNRESOLVED",
                "missing": "Attack-state writers, hitbox records, health address, damage value, hitstop, and reaction-state fields.",
            },
            {
                "semantic_system": "rendering",
                "proven": "Final framebuffer, CPS object list, palette, and CPS-A/CPS-B register streams are synchronized at every frame.",
                "structural_status": "PARTIAL",
                "missing": "ROM animation/assembly tables and the exact object-command generation path.",
            },
            {
                "semantic_system": "audio",
                "proven": "QSound bus writes and register commits are synchronized to normal and Hadouken windows.",
                "structural_status": "PARTIAL",
                "missing": "Event identifiers, sample ownership, voice allocation, and audible-onset mapping.",
            },
        ],
        "timeline": [
            {
                "event": name,
                "frame": anchor["frame"],
                "framebuffer_sha256": anchor["png_sha256"],
                "evidence_scope": "framebuffer plus synchronized work RAM, object RAM, palette, video registers, and QSound log",
            }
            for name, anchor in anchors.items()
        ],
        "confidence": {
            "behavioral_order": "HIGH",
            "internal_state_mapping": "LOW",
            "warning": "Captured RAM and registers are evidence streams, not labeled fields until ownership and writer paths are proven.",
        },
    }


def saturn_model(
    report: dict[str, object], topology: dict[str, object]
) -> dict[str, object]:
    anchors = report["semantic_anchors"]
    return {
        "title": "MSHvSF Saturn semantic model",
        "model_kind": "Evidence-backed external behavioral model; internal SH-2 state is not yet traced",
        "source": "data/mshvsf_saturn_first_pass.json",
        "runtime": report["source"],
        "route": {
            "actors": "Ryu/Ken versus Spider-Man/Captain America",
            "control": "Native replay applies exact Port 1 and Port 2 bytes; P2 is neutral after setup",
            "record_sha256": report["replay"]["record_sha256"],
            "cold_replays": report["replay"]["cold_replay_count"],
            "identical_screenshot_anchors": report["replay"][
                "screenshot_anchor_count"
            ],
        },
        "subsystems": [
            {
                "semantic_system": "game_state",
                "proven": "The fixed backup plus replay deterministically traverses title, Versus selection, teams, mode, speed, stage, and gameplay.",
                "structural_status": "UNRESOLVED",
                "missing": "SH-2 state addresses, mode/round structures, and writer functions.",
            },
            {
                "semantic_system": "input",
                "proven": "Standard-pad active-low bytes and exact frame edges are reproduced for both controller ports.",
                "structural_status": "PARTIAL",
                "missing": "SMPC read routine, game input buffer, command parser, and latency to actor state.",
            },
            {
                "semantic_system": "player_structure",
                "proven": "Ryu responds to walk, jump, and normal inputs and Spider-Man remains neutral until the hit reaction.",
                "structural_status": "UNRESOLVED",
                "missing": "Actor bases, struct stride, coordinates, velocity, state, animation, collision, and health fields.",
            },
            {
                "semantic_system": "movement_and_animation",
                "proven": "Idle, walk, jump, normal, hit reaction, and recovery anchors reproduce byte-identically across two cold runs.",
                "structural_status": "EXTERNAL_ONLY",
                "missing": "Animation tables, rendered-frame durations, normalized trajectories, and SH-2 state transitions.",
            },
            {
                "semantic_system": "attack_collision_damage",
                "proven": "The normal visibly contacts Spider-Man, triggers FIRST ATTACK, changes the health HUD, and produces a hit reaction while P2 is neutral.",
                "structural_status": "EXTERNAL_ONLY",
                "missing": "Hitbox records, collision routine, health field, exact damage, hitstop, and reaction-state data. Hadouken is deferred.",
            },
            {
                "semantic_system": "rendering",
                "proven": "The route produces stable foreground, background, effects, and HUD output.",
                "structural_status": "UNRESOLVED",
                "missing": "VDP1 command tables, VDP2 registers/layers, VRAM addresses, palette ownership, and transfer path.",
            },
            {
                "semantic_system": "audio",
                "proven": "The disc contains ADP members and eleven CD audio tracks; the runtime emits audio.",
                "structural_status": "UNRESOLVED",
                "missing": "Normal-hit event routing, SCSP slots/RAM, ADP decoder, CDDA selection, and onset timing.",
            },
            {
                "semantic_system": "asset_loading",
                "proven": f"The flat ISO contains {topology['disc_file_count']} files in eight measured naming families.",
                "structural_status": "UNRESOLVED",
                "missing": "Package format, decompressed size, load destination, lifetime, eviction, DMA, and CD seek schedule.",
            },
        ],
        "timeline": [
            {
                "event": name,
                "frame": anchor["frame"],
                "framebuffer_sha256": anchor["png_sha256"],
                "evidence_scope": "external framebuffer and exact replay input state",
            }
            for name, anchor in anchors.items()
        ],
        "input_edges": report["input_edges"],
        "confidence": {
            "behavioral_order": "HIGH",
            "internal_state_mapping": "LOW",
            "warning": "Byte-identical screenshots prove repeatable external behavior, not SH-2, VDP, SCSP, RAM, CD, or DMA responsibility.",
        },
    }


def paired_reconstruction(
    cps2: dict[str, object], saturn: dict[str, object]
) -> dict[str, object]:
    cps_by_name = {item["event"]: item for item in cps2["timeline"]}
    sat_by_name = {item["event"]: item for item in saturn["timeline"]}

    def paired(
        concept: str,
        cps_event: str,
        sat_event: str,
        observation: str,
    ) -> dict[str, object]:
        return {
            "semantic_concept": concept,
            "cps2": cps_by_name[cps_event],
            "saturn": sat_by_name[sat_event],
            "relationship": "UNRESOLVED",
            "observation": observation,
            "missing_for_classification": "Paired internal state and normalized timing/geometry measurements",
        }

    return {
        "title": "MSHvSF paired reconstructed vertical slice",
        "reconstruction_kind": "Semantic event reconstruction; not a Saturn executable or code port",
        "status": "FIRST_PASS_COMPLETE_PROJECTILE_DEFERRED",
        "route_setup": {
            "relationship": "EQUIVALENT",
            "confidence": "HIGH",
            "evidence": "Both cold-boot routes reach Ryu/Ken versus Spider-Man/Captain America with P2 neutral.",
        },
        "events": [
            paired("idle", "idle", "idle", "Stable neutral state observed on both systems."),
            paired("forward walk", "walk", "walk", "Forward movement follows a recorded right input on both systems."),
            paired("jump", "jump", "jump", "Airborne Ryu follows a recorded up input on both systems."),
            paired(
                "standing normal attack",
                "normal_attack_active",
                "normal_attack_active",
                "A visually active standing punch follows the recorded attack input on both systems.",
            ),
            {
                "semantic_concept": "collision, damage response, and hit reaction",
                "cps2": cps_by_name["projectile_collision_hit_reaction"],
                "saturn": sat_by_name["collision_damage_hit_reaction"],
                "relationship": "UNRESOLVED",
                "observation": "Both captures include a target reaction and visible damage response, but the CPS-2 anchor is projectile-driven while the Saturn first pass is normal-driven.",
                "missing_for_classification": "Same-attack paired collision, health, damage, hitstop, and reaction-state measurements",
            },
            paired("recovery", "recovery", "recovery", "Ryu returns to a stable post-action state on both systems."),
            {
                "semantic_concept": "Hadouken projectile lifecycle",
                "cps2": {
                    "input": cps_by_name["hadouken_input_complete"],
                    "visible": cps_by_name["hadouken_visible"],
                    "collision": cps_by_name["projectile_collision_hit_reaction"],
                },
                "saturn": None,
                "relationship": "UNRESOLVED",
                "observation": "CPS-2 is captured; Saturn command acceptance and projectile lifecycle are deferred.",
                "missing_for_classification": "Deterministic Saturn Hadouken, projectile spawn/travel/collision, damage, and recovery evidence",
            },
        ],
        "completion_boundary": {
            "proven": "Deterministic paired route and external normal-hit first pass",
            "not_proven": "Function/data correspondence, exact mechanics, audio parity, hardware responsibilities, and full preferred projectile slice",
        },
        "acceptance_rule": "Do not promote an event above UNRESOLVED until the same attack is paired with normalized timing and internal state evidence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cps2-report",
        type=Path,
        default=Path("data/mshvsf_cps2_vertical_slice.json"),
    )
    parser.add_argument(
        "--saturn-report",
        type=Path,
        default=Path("data/mshvsf_saturn_first_pass.json"),
    )
    parser.add_argument(
        "--asset-topology",
        type=Path,
        default=Path("data/mshvsf_saturn_asset_topology.json"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()

    cps2 = cps2_model(load(args.cps2_report))
    saturn = saturn_model(load(args.saturn_report), load(args.asset_topology))
    paired = paired_reconstruction(cps2, saturn)
    write(args.output_dir / "mshvsf_cps2_semantic_model.json", cps2)
    write(args.output_dir / "mshvsf_saturn_semantic_model.json", saturn)
    write(args.output_dir / "mshvsf_reconstructed_vertical_slice.json", paired)
    print("Built CPS-2, Saturn, and paired semantic models.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
