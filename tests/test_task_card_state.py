#!/usr/bin/env python3
"""Task-card dependency and project-state consistency checks."""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_KINDS = {"SALVAGE", "REPAIR", "PROMOTE", "INTEGRATE"}
CONTROL_KINDS = {"ARCHITECTURE", "ORACLE", "QA"}
EXECUTABLE_KINDS = IMPLEMENTATION_KINDS | CONTROL_KINDS
ALLOWED_KINDS = EXECUTABLE_KINDS | {"USER_REVIEW"}
ALLOWED_STATUSES = {
    "ACCEPTED", "READY", "BLOCKED", "PAUSED", "AWAITING_USER_FEEDBACK",
    "CHANGES_REQUESTED",
}
ALLOWED_LANES = {"Fast", "Oracle", "Target", "Emulator", "Full", "Physical"}
REQUIRED_QUESTION = (
    "What should remain unchanged, what looks or feels wrong, and which issue "
    "should be fixed first?"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def scalar(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}:\s*(.+?)\s*$", text)
    require(match is not None, f"missing {name}")
    return match.group(1).strip()


def inline_list(text: str, name: str) -> list[str]:
    value = scalar(text, name)
    require(value.startswith("[") and value.endswith("]"),
            f"{name} must be an inline list")
    body = value[1:-1].strip()
    return [] if not body else [item.strip() for item in body.split(",")]


def yaml_block_list(text: str, name: str) -> list[str]:
    match = re.search(
        rf"(?m)^{re.escape(name)}:\s*\r?\n"
        r"(?P<body>(?:^[ ]{2}-\s+[^\r\n]+\r?\n?)+)",
        text,
    )
    require(match is not None, f"missing block list {name}")
    return [row.strip()[2:].strip()
            for row in match.group("body").splitlines()]


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def normalized_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def activation_is_legal(task: str, kind: str, dependencies: set[str],
                        accepted: set[str],
                        awaiting_feedback: set[str]) -> bool:
    """Return whether a card can become active without crossing a review gate."""
    if not dependencies <= accepted:
        return False
    if kind == "PROMOTE" and dependencies & awaiting_feedback:
        return False
    return True


def can_advance_physical(kind: str, required_lanes: set[str]) -> bool:
    """Only an executable physical card may advance physical evidence."""
    return kind in EXECUTABLE_KINDS and kind != "ORACLE" and \
        "Physical" in required_lanes


def validate_transition_fixtures() -> None:
    """Keep the initial, salvage, and review transitions independently covered."""
    accepted = {"WF-1", "SALVAGE-00-OLD-BUILD-BASELINE"}
    require(activation_is_legal(
        "SALVAGE-01-PLAYER-LOAD-RENDER-INPUT", "SALVAGE",
        {"SALVAGE-00-OLD-BUILD-BASELINE"}, accepted, set()),
        "SALVAGE-00 completion must allow SALVAGE-01")
    require(not activation_is_legal(
        "SALVAGE-01-PLAYER-LOAD-RENDER-INPUT", "SALVAGE",
        {"SALVAGE-00-OLD-BUILD-BASELINE"}, {"WF-1"}, set()),
        "SALVAGE-01 activated without its accepted dependency")

    accepted.add("SALVAGE-01-PLAYER-LOAD-RENDER-INPUT")
    require(activation_is_legal(
        "USER-01-PLAYER-BASELINE-REVIEW", "USER_REVIEW",
        {"SALVAGE-01-PLAYER-LOAD-RENDER-INPUT"}, accepted, set()),
        "SALVAGE-01 completion must allow USER-01")
    require(not activation_is_legal(
        "PROMOTE-01-PLAYER-PIPELINE", "PROMOTE",
        {"SALVAGE-01-PLAYER-LOAD-RENDER-INPUT",
         "USER-01-PLAYER-BASELINE-REVIEW"},
        accepted | {"USER-01-PLAYER-BASELINE-REVIEW"},
        {"USER-01-PLAYER-BASELINE-REVIEW"}),
        "pending user feedback must prevent dependent promotion")
    require(activation_is_legal(
        "SALVAGE-02-ENEMY-RENDER-ANIMATION", "SALVAGE",
        {"SALVAGE-00-OLD-BUILD-BASELINE"}, accepted,
        {"USER-01-PLAYER-BASELINE-REVIEW"}),
        "independent salvage must remain legal while feedback is pending")

    live_accepted = {
        "INTEGRATE-03-PLAYABLE-SLICE",
        "INTEGRATE-04A-LIVE-CONTROL-AND-AI-ENCOUNTER",
        "PROMOTE-08-FRONTEND",
    }
    require(not activation_is_legal(
        "SALVAGE-08-FRONTEND", "SALVAGE",
        {"USER-09-LIVE-ENCOUNTER-REVIEW"}, live_accepted, set()),
        "frontend salvage bypassed the accepted live-encounter review")
    require(not activation_is_legal(
        "INTEGRATE-04-COLD-BOOT-TO-ROUND1", "INTEGRATE",
        {"USER-09-LIVE-ENCOUNTER-REVIEW", "PROMOTE-08-FRONTEND"},
        live_accepted, set()),
        "cold boot accepted only the scripted capability slice")
    require(not can_advance_physical("ORACLE", {"Fast", "Oracle"}),
            "read-only Oracle work advanced physical status")
    require(not can_advance_physical("USER_REVIEW", {"Fast"}),
            "user approval became physical proof")


def main() -> None:
    state = (ROOT / "project_state.yaml").read_text(encoding="utf-8")
    require(scalar(state, "schema") == "2", "unexpected state schema")
    require(scalar(state, "workflow_model") ==
            "interactive-salvage-promotion-integration",
            "state workflow model drifted")
    require(scalar(state, "roadmap") == "docs/PARITY_PLAN.md",
            "state names a competing roadmap")
    require(scalar(state, "migration_map") ==
            "data/port_v2_migration_map.yaml",
            "state names wrong migration map")

    card_paths = sorted((ROOT / "docs/task_cards").glob("*.md"))
    cards = {path.stem: path.read_text(encoding="utf-8")
             for path in card_paths}
    queue = yaml_block_list(state, "task_queue")
    require(len(queue) == len(set(queue)),
            "task queue contains duplicate cards")
    require(set(queue) == set(cards) - {"WF-1"},
            "task queue and card files disagree")

    required_sections = (
        "## Objective",
        "## Owned paths",
        "## Existing systems to reuse",
        "## Systems deliberately disabled",
        "## Focused machine checks",
        "## Saturn build profile",
        "## Emulator readback",
        "## Human-review requirement",
        "## Exclusions",
        "## Hard stops",
        "## Next eligible cards",
    )
    queue_index = {task: index for index, task in enumerate(queue)}
    ready_executable = []
    accepted = set(inline_list(state, "accepted_tasks"))
    independent_read_only = yaml_block_list(
        state, "independent_read_only_cards")
    require(len(independent_read_only) == len(set(independent_read_only)),
            "independent read-only card list contains duplicates")
    require(set(independent_read_only) == {
        "ORACLE-04-PREDATOR-WARRIOR-CONTROL-ACTIONS",
        "ORACLE-05-STREET-ALIEN-AI",
        "ORACLE-06-ROUND1-ENCOUNTER-RULES",
    }, "independent read-only Oracle inventory drifted")

    for task, text in cards.items():
        require(scalar(text, "TASK") == task,
                f"{task} metadata/file mismatch")
        kind = scalar(text, "KIND")
        status = scalar(text, "STATUS")
        require(kind in ALLOWED_KINDS, f"{task} has unsupported kind")
        require(status in ALLOWED_STATUSES, f"{task} has unsupported status")
        require(scalar(text, "TIER") in {"0", "1", "2"},
                f"{task} has unsupported tier")
        required = inline_list(text, "REQUIRED_LANES")
        optional = inline_list(text, "OPTIONAL_LANES")
        require(required and set(required + optional) <= ALLOWED_LANES,
                f"{task} has invalid lanes")
        require(not set(required) & set(optional),
                f"{task} repeats lanes")
        require(scalar(text, "CLAUDE_ALLOWED") in {"true", "false"},
                f"{task} lacks provider boundary")
        next_eligible = inline_list(text, "NEXT_ELIGIBLE_CARDS")
        require(set(next_eligible) <= set(cards),
                f"{task} names an unknown next eligible card")
        terminal = re.search(r"(?m)^TERMINAL:\s*true\s*$", text) is not None
        if terminal:
            require(not next_eligible,
                    f"{task} is terminal but names a successor")
        else:
            require(next_eligible, f"{task} has no predeclared successor")
        for section in required_sections:
            require(section in text, f"{task} missing {section}")

        dependencies = inline_list(text, "DEPENDENCIES")
        require(set(dependencies) <= set(cards),
                f"{task} names unknown dependency")
        if task in queue:
            for dependency in dependencies:
                if dependency not in accepted:
                    require(dependency in queue_index and
                            queue_index[dependency] < queue_index[task],
                            f"{task} is not dependency ordered")
        if kind in EXECUTABLE_KINDS and status == "READY":
            ready_executable.append(task)
        if task in independent_read_only:
            require(kind == "ORACLE", f"{task} is not an Oracle")
            require(scalar(text, "READ_ONLY") == "true",
                    f"{task} lost its read-only boundary")
            require("Physical" not in required + optional,
                    f"{task} can create physical evidence")
            require("All production runtime" in text and
                    "No production-path write" in text,
                    f"{task} permits production runtime writes")
        if kind == "USER_REVIEW":
            require("Perform no implementation" in text,
                    f"{task} permits implementation")
            require(REQUIRED_QUESTION in text,
                    f"{task} lacks exact user question")
            require("AWAITING_USER_FEEDBACK" in text,
                    f"{task} lacks wait state")
            require("Silence is not approval" in text or
                    "inferred approval" in text,
                    f"{task} can infer approval")

    active_relative = scalar(state, "active_task_card")
    require(re.fullmatch(r"docs/task_cards/[A-Za-z0-9._-]+\.md",
                         active_relative) is not None,
            "active card path escapes queue")
    active_id = Path(active_relative).stem
    require(active_id in cards, "active card does not exist")
    require(active_id in queue, "active card is not in the task queue")
    active = cards[active_id]
    active_independent = scalar(
        state, "active_independent_read_only_card")
    independent_owner = scalar(state, "independent_oracle_write_owner")
    if active_independent == "null":
        active_independent = None
    if independent_owner == "null":
        independent_owner = None
    active_cards = [
        task for task, text in cards.items()
        if (scalar(text, "KIND") in EXECUTABLE_KINDS and
            scalar(text, "STATUS") == "READY") or
           (scalar(text, "KIND") == "USER_REVIEW" and
            scalar(text, "STATUS") in {"READY", "AWAITING_USER_FEEDBACK"})
    ]
    expected_active_cards = {active_id}
    if active_independent is not None:
        expected_active_cards.add(active_independent)
    require(set(active_cards) == expected_active_cards,
            "active cards exceed the primary plus one read-only Oracle")
    require(active_id in ready_executable or
            scalar(active, "KIND") == "USER_REVIEW",
            "primary executable readiness disagrees with active card")
    require(scalar(state, "active_task_id") == active_id,
            "active task id mismatch")
    require(scalar(state, "active_task_kind") == scalar(active, "KIND"),
            "active kind mismatch")
    require(scalar(state, "task_status") == scalar(active, "STATUS"),
            "active status mismatch")
    require(scalar(state, "current_checkpoint") ==
            scalar(active, "CHECKPOINT"), "active checkpoint mismatch")
    require(scalar(state, "active_write_owner") == active_id,
            "active write owner mismatch")
    awaiting_feedback = set(inline_list(state, "awaiting_user_feedback"))
    require(activation_is_legal(
        active_id, scalar(active, "KIND"),
        set(inline_list(active, "DEPENDENCIES")), accepted, awaiting_feedback),
        "active card has unaccepted dependencies or crosses feedback gate")
    if scalar(active, "KIND") == "USER_REVIEW" and \
            scalar(active, "STATUS") == "AWAITING_USER_FEEDBACK":
        require(awaiting_feedback == {active_id},
                "awaiting review state does not name its active review card")
    else:
        require(not awaiting_feedback,
                "non-review activation unexpectedly awaits feedback")
    require(scalar(state, "open_blockers") == "[]",
            "active task retains blockers")

    if active_independent is None:
        require(independent_owner is None,
                "inactive Oracle lane retains a write owner")
    else:
        require(active_independent in independent_read_only,
                "active independent card is not predeclared")
        require(independent_owner == active_independent,
                "independent Oracle writer ownership drifted")
        independent_card = cards[active_independent]
        require(scalar(independent_card, "STATUS") == "READY",
                "active independent Oracle is not ready")
        require(activation_is_legal(
            active_independent, "ORACLE",
            set(inline_list(independent_card, "DEPENDENCIES")),
            accepted, awaiting_feedback),
            "independent Oracle has unaccepted dependencies")
        require(scalar(active, "KIND") == "QA" and
                "Physical" in inline_list(active, "REQUIRED_LANES"),
                "independent Oracle ran without a physical hard stop")

    require(accepted <= set(cards), "accepted task is absent from task cards")
    for accepted_task in accepted:
        require(scalar(cards[accepted_task], "STATUS") == "ACCEPTED",
                f"accepted task {accepted_task} is not recorded as accepted")

    v2_status = scalar(cards["V2-2B"], "STATUS")
    review_status = scalar(state, "review_candidate_status")
    if v2_status == "ACCEPTED":
        require(review_status == "ACCEPTED",
                "accepted V2-2B retains a correction disposition")
        require("V2-2B" in accepted,
                "accepted V2-2B is absent from accepted_tasks")
        for token in (
            "evidence_work:",
            "id: V2-2B",
            "status: ACCEPTED",
            "dirty: false",
            "blockers: []",
        ):
            require(token in state,
                    f"accepted V2-2B evidence state missing {token}")
    else:
        require(review_status == "CORRECTIONS_REQUIRED",
                "unaccepted V2-2B lost its correction disposition")
        require("V2-2B" not in accepted,
                "unaccepted V2-2B appears in accepted_tasks")
    for token in (
        "playable-skeleton-prototype",
        "preserve: true",
    ):
        require(token in state, f"preserved state missing {token}")

    conditions = re.findall(
        r"(?m)^\s+- id:\s*([a-z0-9_]+)\s*\r?\n\s+status:\s*([A-Z_]+)\s*$",
        state,
    )
    require(len(conditions) == 12, "state must retain 12 capability conditions")
    closed = sum(status == "CLOSED" for _, status in conditions)
    require(scalar(state, "capability_gate") == f"{closed}/12",
            "capability gate count drifted")
    require(closed == 0, "salvage evidence cannot advance capability status")

    hardware = re.search(
        r"(?ms)^hardware_pretest:[ \t]*\r?\n(.*?)^pending_integration_review:",
        state,
    )
    require(hardware is not None, "hardware pretest state is missing")
    hardware_text = hardware.group(1)
    require(re.search(rf"(?m)^  task:\s*{re.escape(active_id)}\s*$",
                      hardware_text) is not None,
            "active physical card and hardware pretest task disagree")
    require(re.search(r"(?m)^  status:\s*READY_FOR_PHYSICAL\s*$",
                      hardware_text) is not None and
            re.search(r"(?m)^  physical_saturn:\s*UNRUN\s*$",
                      hardware_text) is not None,
            "physical hard-stop status advanced or drifted")

    for token in (
        "production_player_control: UNRUN",
        "street_alien_ai: UNRUN",
        "encounter_controller: UNRUN",
        "interactive_human_review: UNRUN",
        "scripted_capability_slice_sufficient: false",
    ):
        require(token in state, f"live-gameplay state missing {token}")
    require("production player control and enemy AI remain UNKNOWN" in state,
            "INTEGRATE-03 was relabeled as measured production gameplay")

    head_keys = (
        "foundation_head",
        "production_head",
        "candidate_head",
        "evidence_candidate_head",
        "accepted_head",
        "review_candidate_head",
    )
    for key in head_keys:
        value = scalar(state, key)
        require(re.fullmatch(r"[0-9a-f]{40}", value) is not None,
                f"{key} is not pinned")
        git("cat-file", "-e", f"{value}^{{commit}}")
    require(scalar(state, "accepted_head") == scalar(state, "foundation_head"),
            "deprecated accepted_head alias drifted from foundation_head")
    require(scalar(state, "review_candidate_head") ==
            scalar(state, "evidence_candidate_head"),
            "deprecated review candidate alias drifted")
    foundation = scalar(state, "foundation_head")
    production = scalar(state, "production_head")
    candidate = scalar(state, "candidate_head")
    evidence = scalar(state, "evidence_candidate_head")
    for descendant in (production, candidate, evidence):
        git("merge-base", "--is-ancestor", foundation, descendant)
    git("merge-base", "--is-ancestor", production, candidate)
    history = re.search(
        r"(?ms)^accepted_implementation_history:\s*(.*?)"
        r"^accepted_control_plane_history:",
        state,
    )
    require(history is not None, "accepted implementation history is missing")
    accepted_implementation_heads = re.findall(
        r"(?m)^  - id: .+\r?\n"
        r"    status: ACCEPTED\r?\n"
        r"    head: ([0-9a-f]{40})$",
        history.group(1),
    )
    require(accepted_implementation_heads,
            "accepted implementation history has no accepted heads")
    require(accepted_implementation_heads[-1] == production,
            "production_head is not the latest accepted production implementation")
    require(
        f"current_continuity_branch: {scalar(state, 'production_branch')}"
        in state,
        "production branch drifted from the preserved continuity line",
    )

    for task, text in cards.items():
        kind = scalar(text, "KIND")
        status = scalar(text, "STATUS")
        if status == "BLOCKED" and kind in (
                IMPLEMENTATION_KINDS | {"QA", "USER_REVIEW"}):
            require(scalar(text, "BASE") == "project_state.production_head",
                    f"{task} is a future production card on the wrong base")
            require(scalar(text, "BRANCH") ==
                    "project_state.production_branch",
                    f"{task} invents a per-card production branch")

    bindings = {
        "contract_sha256": "data/avsp_vertical_slice_contract.json",
        "oracle_manifest_sha256": "data/avsp_vertical_slice_oracle_manifest.json",
        "translation_boundary_sha256": "data/avsp_translation_boundary.json",
        "writer_set_manifest_sha256": "data/avsp_hit_ko_writer_set.json",
    }
    for key, relative in bindings.items():
        require(scalar(state, key) == normalized_sha256(ROOT / relative),
                f"{key} drifted")

    roadmap = (ROOT / "docs/PARITY_PLAN.md").read_text(encoding="utf-8")
    require(scalar(roadmap, "CURRENT_TASK") == active_id,
            "roadmap and state active cards disagree")

    require(inline_list(cards["SALVAGE-08-FRONTEND"], "DEPENDENCIES") ==
            ["USER-09-LIVE-ENCOUNTER-REVIEW"],
            "frontend salvage can bypass the live-encounter review")
    require(set(inline_list(
        cards["INTEGRATE-04-COLD-BOOT-TO-ROUND1"], "DEPENDENCIES")) == {
            "USER-09-LIVE-ENCOUNTER-REVIEW", "PROMOTE-08-FRONTEND",
        }, "cold-boot integration dependencies drifted")
    live_card = cards["INTEGRATE-04A-LIVE-CONTROL-AND-AI-ENCOUNTER"]
    for pattern, label in (
        (r"promoted Predator Warrior action\s+controller", "player action state"),
        (r"promoted class-`0x1F` AI", "enemy AI state"),
        (r"current game state", "current-state decisions"),
        (r"Fixed-frame contact", "fixed-frame prohibition"),
        (r"damage without current overlap", "overlap-owned damage"),
        (r"(?:encounter clear|clear the\s+encounter)", "encounter clear"),
        (r"continue moving", "continued movement"),
    ):
        require(re.search(pattern, live_card) is not None,
                f"live encounter card missing invariant: {label}")
    require("scripted INTEGRATE-03 capability demonstration cannot satisfy" in
            cards["INTEGRATE-04-COLD-BOOT-TO-ROUND1"],
            "scripted capability slice can satisfy playable Round 1")
    require(scalar(cards["USER-09-LIVE-ENCOUNTER-REVIEW"], "STATUS") ==
            "BLOCKED" and "physical proof" in
            cards["USER-09-LIVE-ENCOUNTER-REVIEW"],
            "USER-09 can become physical proof")
    for later in (
        "INTEGRATE-06-FOUR-CHARACTER-ROSTER",
        "INTEGRATE-07-THREE-PLAYER-MULTIPLAYER",
    ):
        require(scalar(cards[later], "STATUS") == "BLOCKED" and
                inline_list(cards[later], "DEPENDENCIES"),
                f"{later} lost its evidence gate")

    validate_transition_fixtures()

    print("task-card/state consistency: PASS")


if __name__ == "__main__":
    main()
