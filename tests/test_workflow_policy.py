#!/usr/bin/env python3
"""Workflow invariants; R7C delivery policy plus preserved historical ledgers."""

from __future__ import annotations

import json
import re
import contextlib
import io
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def scalar(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}:\s*(.+?)\s*$", text)
    require(match is not None, f"missing {name}")
    return match.group(1).strip()


def main(*, run_negative_controls: bool = True) -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    require(len(agents.splitlines()) < 150, "AGENTS.md is not concise")
    policy = re.sub(r"\s+", " ", agents)
    for token in (
        "Codex Goal Mode owns interactive implementation",
        "`docs/PARITY_PLAN.md` is the only roadmap",
        "Exactly one implementation task owns writes at a time",
        "implementation is the default for ordinary work",
        "nested Codex executors are not used for ordinary implementation",
        "Claude is an optional bounded provider",
        "gpt-5.6-sol",
        "automatically correct ordinary compile",
        "A passing emulator check is not human approval or physical proof",
        "A user-approved component is locked",
        "build/feedback/<task-id>/",
        "push it to `private-origin`",
        "remote branch SHA equals local",
        "independent_read_only_cards",
        "Do not restart salvage benches",
        "normal interactive image must not use a captured frame ledger",
        "An exhausted named gate stays blocked",
        "CODEX_REVIEW_INVOCATION",
    ):
        require(token in policy, f"AGENTS.md missing policy: {token}")
    require(not re.search(r"\b[0-9a-f]{40}\b", agents),
            "AGENTS.md contains a volatile commit SHA")

    for obsolete in (
        "docs/NEXT_AGENT_PROMPT.md",
        "docs/CODEX_REVIEW_TEMPLATE.md",
        "docs/IMPLEMENTOR_INVOCATION.md",
        "tools/start-agent-task.ps1",
    ):
        require(not (ROOT / obsolete).exists(),
                f"obsolete execution control remains: {obsolete}")
    require(not list((ROOT / ".codex/agents").glob("*")),
            "nested Codex agent profiles remain active")
    require(not list((ROOT / ".claude/agents").glob("*")),
            "Claude supervisor profiles remain active")
    codex_config = (ROOT / ".codex/config.toml").read_text(encoding="utf-8")
    require("enabled = false" in codex_config,
            "project still enables nested agents")

    goal = (ROOT / "docs/GOAL.md").read_text(encoding="utf-8")
    for token in (
        "human-in-the-loop salvage-and-promotion process",
        "final gameplay authority",
        "cold boot",
        "Predator Warrior",
        "Major Schaefer",
        "Predator Hunter",
        "Linn Kurosawa",
        "up to three simultaneous",
        "title-specific deterministic Port V2",
        "FIRST LIVE GAMEPLAY ENCOUNTER",
        "current gameplay state",
    ):
        require(token in re.sub(r"\s+", " ", goal), f"goal missing {token}")

    architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    require("interactive salvage-and-promotion loop" in architecture and
            "do not advance production parity" in architecture,
            "active architecture conflicts with salvage governance")
    for token in (
        "avsp_game_step",
        "fixed-capacity arrays",
        "InputPort",
        "RenderPort",
        "AudioPort",
        "AssetPort",
        "TelemetryPort",
        "PersistenceCreditPort",
        "GameSession",
        "PortV2CharacterDef",
        "AvspSceneDef",
        "Phase-scoped residency",
        "Temporary legacy adapters",
        "Exact deletion condition",
        "Game rules must not remain there",
        "Staged mechanical enforcement",
        "foundation_head",
        "production_head",
        "candidate_head",
        "evidence_candidate_head",
        "First live gameplay boundary",
        "Predator Warrior action controller",
        "class-`0x1F` AI controller",
        "Round 1 encounter controller",
        "Fixed-frame contact injection",
    ):
        require(token in architecture,
                f"production architecture missing {token}")
    for forbidden in (
        "general CPS-2 engine",
        "generalized Capcom framework",
        "general ECS",
    ):
        require(forbidden in architecture,
                f"architecture does not prohibit {forbidden}")

    test_plan = (ROOT / "docs/TEST_PLAN.md").read_text(encoding="utf-8")
    for heading in (
        "## DEV inner loop",
        "## BENCH self-review",
        "## CHECKPOINT integration and review",
        "## Fast workflow lane",
        "## Oracle lane",
        "## Target and normal-release lanes",
        "## Full lane",
        "## Physical lane",
    ):
        require(heading in test_plan, f"test plan missing {heading}")
    for token in (
        "strict compile for touched code",
        "deterministic repeat",
        "non-vacuous negative control",
        "Do not run the complete writer boundary",
        "build/feedback/<task-id>/",
    ):
        require(token in test_plan, f"test plan missing {token}")

    roadmap = (ROOT / "docs/PARITY_PLAN.md").read_text(encoding="utf-8")
    for milestone in [*(f"R{index}" for index in range(7)),
                      "R7A", "R7B", "R7C",
                      *(f"R{index}" for index in range(8, 14))]:
        require(f"### {milestone} " in roadmap,
                f"roadmap missing {milestone}")
    for token in (
        "only roadmap", "REIMPLEMENT-13", "QA-13", "USER-10",
        "SOURCE-CLOSED ROUND 1 END-TO-END PLAYABLE SLICE",
        "1972..15193", "Coffee Shop is RED", "AT RISK",
        "interactive scheduler", "captured-schedule authority",
        "changed input", "909-tile", "15%", "SALVAGE-08",
    ):
        require(token in roadmap, f"roadmap missing {token}")
    require(len(roadmap.splitlines()) < 180,
            "roadmap became a repeated checkpoint history")
    state = (ROOT / "project_state.yaml").read_text(encoding="utf-8")
    for token in (
        "worktree_routing_policy:",
        "mode: existing-worktree-first",
        "approved_card_transition:",
        "- push-to-private-origin",
        "- verify-remote-sha-equals-local",
        "- inspect-repository-state",
        "- select-best-existing-worktree-and-branch",
        "- continue-from-approved-predecessor",
        "tranche_or_milestone_alone_requires_new_worktree: false",
        "preserve_other_transition_validation_approval_and_push_requirements: true",
        "foundation_head:",
        "production_head:",
        "candidate_head:",
        "evidence_candidate_head:",
        "production_branch: codex/avp-playable-loop-pivot",
        "maximum_simultaneous_local_players: 3",
        "controller_and_multitap_topology: UNRUN",
        "architecture_enforcement:",
        "accepted_legacy_paths_are_grandfathered: true",
        "status: STAGED",
        "status: ACTIVE_FOR_NEW_ADAPTERS",
        "status: ACTIVE",
        "independent_read_only_cards:",
        "active_independent_read_only_card:",
        "serial_oracle_writers: true",
        "production_runtime_writes: false",
        "physical_status_changes: false",
        "FIRST LIVE GAMEPLAY ENCOUNTER",
        "scripted_capability_slice_sufficient: false",
        "status: SOURCE_CLOSURE_REQUIRED",
        "NOT_SOURCE_CLOSED",
        "formal_legal_clean_room_claim: false",
    ):
        require(token in state, f"state missing continuity policy: {token}")
    require(scalar(roadmap, "CURRENT_TASK") == scalar(state, "active_task_id"),
            "roadmap and machine-readable active task disagree")
    require(not re.search(r"\b[0-9a-f]{40}\b", roadmap),
            "roadmap repeats volatile commit SHAs")

    handoff = (ROOT / "docs/AGENT_HANDOFF.md").read_text(encoding="utf-8")
    require(len(handoff.splitlines()) < 50,
            "handoff became a historical narrative")
    for token in (
        scalar(state, "active_task_id"),
        scalar(state, "candidate_head"),
        "Exact next experiment",
        "captured-schedule",
        "P4 Coffee Shop remains RED",
        "no retry was authorized",
    ):
        require(token in handoff, f"handoff missing {token}")
    card = (ROOT / scalar(state, "active_task_card")).read_text(encoding="utf-8")
    require(len(card.splitlines()) < 220, "active card became a running history")
    for token in (
        "changed input", "1972..5566", "hardcoded",
        "93", "279", "BLOCKED_MISSING_SPEC_FIELDS",
        "Target and transition Emulator/WGC budgets remain exhausted",
    ):
        require(token in card, f"active delivery card missing {token}")
    require("interactive_authority_status: BLOCKED_CAPTURE_SCHEDULE_IN_NORMAL_CALLBACK"
            in state,
            "known interactive-authority defect lost before corrective evidence")
    verify = (ROOT / "verify.ps1").read_text(encoding="utf-8")
    require("[switch]$WorkflowOnly" in verify and
            "if (-not $WorkflowOnly)" in verify and
            "fast-workflow-only.json" in verify and
            "complete-lane" in verify,
            "workflow-only result could masquerade as complete Fast")
    require(verify.index("tests\\test_task_card_state.py") <
            verify.index("if (-not $WorkflowOnly)"),
            "workflow-only scope skips state/dependency checks")
    for test in (
        "tests\\port_v2\\round1\\test_entry.py",
        "tests\\port_v2\\round1\\test_target_entry_wiring.py",
    ):
        require(verify.count(test) == 2,
                f"default Fast and Oracle lost existing runtime test {test}")

    require((ROOT / "data/port_v2_migration_map.yaml").is_file(),
            "migration ledger is missing")
    require((ROOT / "tools/New-ReviewBundle.ps1").is_file(),
            "evidence review bundle helper was removed")

    ledger_paths = {
        "full_game": ROOT / "data/full_game_content_coverage.yaml",
        "actions": ROOT / "data/four_character_action_matrix.yaml",
        "endings": ROOT / "data/ending_credits_matrix.yaml",
    }
    ledgers = {}
    for name, path in ledger_paths.items():
        require(path.is_file(), f"{name} ledger is missing")
        try:
            ledgers[name] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AssertionError(
                f"{name} ledger is not JSON-compatible YAML: {exc}") from exc
        require(ledgers[name].get("schema") == 1,
                f"{name} ledger has wrong schema")
        require(ledgers[name].get("source_set") == "avspu",
                f"{name} ledger has wrong source set")

    expected_characters = [
        "predator_warrior",
        "major_schaefer",
        "predator_hunter",
        "linn_kurosawa",
    ]
    actions = ledgers["actions"]
    require(actions["selection_contract"]["identity_order"] ==
            expected_characters, "four-character identity order drifted")
    require(actions["selection_contract"]["status"] == "MEASURED",
            "measured selection contract was downgraded")
    require(actions["promoted_player_subset"]["character_binding"] == "UNKNOWN",
            "promoted player subset was assigned to a character without proof")
    require([row["character_id"] for row in actions["characters"]] ==
            expected_characters, "action matrix roster drifted")
    unknown_action_fields = {
        "all_attacks", "weapons_and_projectiles", "jump_dash_special",
        "pickups_use_throw", "grab_throw", "hit", "ko", "continue",
        "character_specific_state_and_resources", "ending_route",
    }
    for row in actions["characters"]:
        require(row["select_identity"] == "MEASURED",
                f"{row['character_id']} select identity lost")
        require(all(row[field] == "UNKNOWN"
                    for field in unknown_action_fields),
                f"{row['character_id']} contains fabricated action facts")
    predator = actions["characters"][0]
    live_subset = predator["first_live_encounter_subset"]
    require(live_subset["status"] == "MEASURED",
            "Predator Warrior bounded live subset lost ORACLE-04 measurement")
    require(live_subset["classification"] == "MEASURED_MAME_SOURCE_SUBSET" and
            live_subset["evidence"] ==
            "data/oracle04_predator_warrior_control_actions.json",
            "Predator Warrior live subset lost its bounded evidence binding")
    require(set(live_subset["unknown_scope"]) == {
                "complete_move_set", "interruption_and_cancellation",
                "player_side_rng_consumption"},
            "Predator Warrior live subset overstated unresolved source facts")
    require(live_subset["saturn_emulator"] == "UNRUN" and
            live_subset["physical_saturn"] == "UNRUN",
            "source-only Predator Warrior evidence overstated Saturn proof")
    require(predator["first_live_encounter_subset"]["evidence_gate"] ==
            "ORACLE-04-PREDATOR-WARRIOR-CONTROL-ACTIONS",
            "Predator Warrior live subset lost its source gate")
    require(all("first_live_encounter_subset" not in row
                for row in actions["characters"][1:]),
            "other characters received invented live-encounter scope")

    endings = ledgers["endings"]
    require([row["character_id"] for row in endings["characters"]] ==
            expected_characters, "ending matrix roster drifted")
    require(all(value == "UNKNOWN"
                for value in endings["classification"].values()),
            "ending topology was fabricated")
    require(all(row["final_boss_to_ending"] == "UNRUN" and
                row["ending_route"] == "UNKNOWN" and
                row["credits_route"] == "UNKNOWN"
                for row in endings["characters"]),
            "ending matrix contains unmeasured completion")

    coverage = ledgers["full_game"]
    required_coverage_fields = {
        "captured", "labeled", "packaged", "host_parity", "emulator",
        "human_review", "physical_workload", "blockers", "next_experiment",
    }
    route_bodies = coverage["route_bodies"]
    require(len(route_bodies) == len({row["id"] for row in route_bodies}),
            "coverage ledger repeats a route body")
    for row in route_bodies:
        require(required_coverage_fields <= set(row),
                f"{row['id']} lacks coverage fields")
        require(row["blockers"] and row["next_experiment"],
                f"{row['id']} lacks blocker/next experiment")
        require(row["physical_workload"] == "UNRUN",
                f"{row['id']} fabricates physical workload evidence")
    round1 = next(row for row in route_bodies if row["id"] == "round1")
    require(round1["technical_capability_slice"] == "PARTIAL",
            "Round 1 lost the bounded capability-slice distinction")
    require("INTEGRATE-04A-LIVE-CONTROL-AND-AI-ENCOUNTER" in
            scalar(state, "accepted_tasks"),
            "bounded live encounter advanced without accepted INTEGRATE-04A")
    for field in (
        "live_player_control", "street_alien_ai", "encounter_controller",
    ):
        require(round1[field] == "PASS_BOUNDED_ONE_EMULATOR",
                f"Round 1 {field} lost its bounded INTEGRATE-04A evidence")
    require(round1["complete_round1"] == "UNRUN",
            "bounded live encounter was inflated into complete Round 1")

    scene_manifest = json.loads(
        (ROOT / "data/avsp_scene_manifest.json").read_text(encoding="utf-8"))
    scene_evidence = coverage["known_evidence"]["scene_manifest"]
    require(scene_evidence["scene_count"] == scene_manifest["scene_count"],
            "coverage scene count is not source-bound")
    require(scene_evidence["capture_last_frame"] ==
            scene_manifest["route"]["last_frame"],
            "coverage last frame is not source-bound")
    labeled = sum(scene.get("label") is not None
                  for scene in scene_manifest["scenes"])
    require(scene_evidence["labeled_scene_count"] == labeled,
            "coverage labeled scene count drifted")
    require(scene_evidence["unlabeled_scene_count"] ==
            scene_manifest["scene_count"] - labeled,
            "coverage unlabeled scene count drifted")

    frontend = json.loads(
        (ROOT / "data/frontend_interaction.json").read_text(encoding="utf-8"))
    require([row["character"] for row in frontend["cursor_positions"]] ==
            expected_characters, "matrix identities differ from frontend evidence")
    require(all(row["latency_frames"] ==
                actions["selection_contract"]["directional_response_frames"]
                for row in frontend["direction_transitions"]),
            "matrix response latency differs from measured evidence")

    adr_names = [
        "0001-port-v2-ports-and-adapters.md",
        "0002-legacy-displacement-by-abstraction.md",
        "0003-deterministic-fixed-tick-kernel.md",
        "0004-hierarchical-route-state-machine.md",
        "0005-semantic-frame-events.md",
        "0006-phase-scoped-residency-packages.md",
        "0007-common-player-runtime-four-character-definitions.md",
        "0008-presentation-scenes-do-not-own-gameplay.md",
        "0009-no-general-cps2-engine-or-ecs.md",
        "0010-production-head-vs-foundation-head.md",
    ]
    adr_sections = (
        "## Status", "## Context", "## Decision",
        "## Alternatives considered", "## Consequences",
        "## Migration impact", "## Evidence still required",
    )
    require(sorted(path.name for path in (ROOT / "docs/adr").glob("*.md")) ==
            adr_names, "ADR set is incomplete or speculative")
    for name in adr_names:
        text = (ROOT / "docs/adr" / name).read_text(encoding="utf-8")
        for section in adr_sections:
            require(section in text, f"{name} missing {section}")

    for template in (
        "STAGE-SEGMENT-TEMPLATE.md",
        "CHARACTER-EXPANSION-TEMPLATE.md",
        "MULTIPLAYER-TEMPLATE.md",
    ):
        require((ROOT / "docs/task_cards/templates" / template).is_file(),
                f"missing future task-card template {template}")

    enforcement = state.split("architecture_enforcement:", 1)[1].split(
        "current_checkpoint:", 1)[0]
    expected_rules = {
        "core-no-jo-sgl",
        "gameplay-no-direct-asset-load",
        "render-no-gameplay-outcomes",
        "audio-no-route-progression",
        "deterministic-state-input-content",
        "phase-manifest-required",
        "no-active-phase-dynamic-allocation",
        "legacy-adapter-deletion-condition",
        "behavioral-claim-label",
        "character-matrix-required",
        "coverage-ledger-required",
        "evidence-tier-separation",
    }
    actual_rules = set(re.findall(
        r"(?m)^    - id:\s*([a-z0-9-]+)\s*$", enforcement))
    require(actual_rules == expected_rules,
            "staged architecture-rule inventory drifted")

    core = ROOT / "src/port_v2/core"
    if core.exists():
        include_pattern = re.compile(
            r"(?im)^\s*#\s*include\s*[<\"](?:jo|sgl)[^>\"]*[>\"]")
        for path in core.rglob("*"):
            if path.suffix.lower() in {".c", ".h"}:
                require(include_pattern.search(
                    path.read_text(encoding="utf-8", errors="replace")) is None,
                    f"Port V2 core includes Jo/SGL: {path.relative_to(ROOT)}")

    if run_negative_controls:
        check_policy_negative_controls()
    print("workflow policy: PASS")


def check_policy_negative_controls() -> None:
    """Mutate policy text in memory; require each intended diagnostic."""
    original_read = Path.read_text
    cases = (
        ("docs/AGENT_HANDOFF.md", "no retry was authorized", "retry approved",
         "handoff missing no retry"),
        ("project_state.yaml",
         "interactive_authority_status: BLOCKED_CAPTURE_SCHEDULE_IN_NORMAL_CALLBACK",
         "interactive_authority_status: PASS",
         "known interactive-authority defect lost"),
        ("verify.ps1", "fast-workflow-only.json", "fast.json",
         "workflow-only result could masquerade"),
    )
    for relative, before, after, diagnostic in cases:
        target = ROOT / relative

        def altered_read(path, *args, **kwargs):
            text = original_read(path, *args, **kwargs)
            if path.resolve() == target:
                require(before in text, f"invalid policy mutation: {relative}")
                return text.replace(before, after)
            return text

        with patch.object(Path, "read_text", altered_read), \
                contextlib.redirect_stdout(io.StringIO()):
            try:
                main(run_negative_controls=False)
            except AssertionError as exc:
                require(diagnostic in str(exc),
                        f"unrelated policy rejection: {relative}: {exc}")
            else:
                raise AssertionError(f"policy mutation survived: {relative}")
    print("workflow policy negatives: PASS (3 intended diagnostics; no file edits)")


if __name__ == "__main__":
    main()
