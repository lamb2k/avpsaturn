#!/usr/bin/env python3
"""Task-card dependency and project-state consistency checks."""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_KINDS = {"SALVAGE", "REPAIR", "PROMOTE", "INTEGRATE"}
ALLOWED_KINDS = IMPLEMENTATION_KINDS | {"USER_REVIEW"}
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
    require(len(cards) == 19, "task-card set is incomplete")
    queue = yaml_block_list(state, "task_queue")
    require(len(queue) == 18 and len(set(queue)) == 18,
            "task queue must contain 18 unique ordered cards")
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
    ready_implementation = []
    accepted = set(inline_list(state, "accepted_tasks"))

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
        if task != "INTEGRATE-03-PLAYABLE-SLICE":
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
        if kind in IMPLEMENTATION_KINDS and status == "READY":
            ready_implementation.append(task)
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
    active = cards[active_id]
    require(ready_implementation == [active_id],
            "exactly one implementation card must be READY")
    require(active_id == "SALVAGE-00-OLD-BUILD-BASELINE",
            "first salvage card is not active")
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
    require(set(inline_list(active, "DEPENDENCIES")) <= accepted,
            "active card has unaccepted dependencies")
    require(scalar(state, "awaiting_user_feedback") == "[]",
            "initial activation unexpectedly awaits feedback")
    require(scalar(state, "open_blockers") == "[]",
            "active salvage card retains blockers")

    require(scalar(state, "review_candidate_status") ==
            "CORRECTIONS_REQUIRED", "V2-2B disposition was lost")
    for token in (
        "id: V2-2B",
        "dirty: true",
        "playable-skeleton-prototype",
        "preserve: true",
        "Exact writer ownership",
        "Control flow is not a call-rooted closure",
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

    for key in ("accepted_head", "review_candidate_head"):
        value = scalar(state, key)
        require(re.fullmatch(r"[0-9a-f]{40}", value) is not None,
                f"{key} is not pinned")
        git("cat-file", "-e", f"{value}^{{commit}}")
    git("merge-base", "--is-ancestor", scalar(state, "accepted_head"),
        scalar(state, "review_candidate_head"))

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

    print("task-card/state consistency: PASS")


if __name__ == "__main__":
    main()
