#!/usr/bin/env python3
"""Fast executable invariants for the risk-tiered agent workflow."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def scalar(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}:\s*(.+?)\s*$", text)
    require(match is not None, f"missing {name}")
    return match.group(1).strip()


def blockers(text: str) -> list[str]:
    match = re.search(r"(?m)^open_blockers:[ \t]*([^\r\n]*)[ \t]*$", text)
    require(match is not None, "missing open_blockers")
    if match.group(1) in ("[]", ""):
        start = match.end()
        tail = text[start:]
        rows = []
        for line in tail.splitlines():
            if line and not line[0].isspace():
                break
            item = re.match(r"\s+-\s+(.+)", line)
            if item:
                rows.append(item.group(1))
        return rows
    return [match.group(1)]


def inline_list(text: str, name: str) -> list[str]:
    value = scalar(text, name)
    require(value.startswith("[") and value.endswith("]"),
            f"{name} must be an inline list")
    body = value[1:-1].strip()
    if not body:
        return []
    return [item.strip() for item in body.split(",")]


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], check=True,
        capture_output=True, text=True).stdout.strip()


def normalized_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def validate_relationship(state: str, card: str, accepted_tasks: set[str]) -> None:
    status = scalar(state, "task_status")
    require(status in {"BLOCKED", "REVIEW", "READY", "CORRECTIONS",
                       "EVIDENCE_REPAIR", "NOT_REVIEWABLE", "ACCEPTED"},
            f"unsupported task status: {status}")
    require(status == scalar(card, "STATUS"),
            "task-card status and project state disagree")
    require(scalar(state, "current_checkpoint") == scalar(card, "CHECKPOINT"),
            "task-card checkpoint and project state disagree")
    dependencies = set(inline_list(card, "DEPENDENCIES"))
    require(dependencies <= accepted_tasks,
            "active task has an unaccepted dependency")
    if status == "READY":
        require(not blockers(state), "READY state retains an open blocker")
        require(scalar(state, "accepted_head") ==
                scalar(state, "review_candidate_head"),
                "READY state has not pinned the reviewed candidate")
        require(scalar(state, "review_candidate_status") == "ACCEPTED",
                "READY state does not record an accepted disposition")


def main() -> None:
    require(blockers("open_blockers: []\n") == [],
            "inline empty blocker form is not recognized")
    require(blockers("open_blockers: [blocked]\n") == ["[blocked]"],
            "inline nonempty blocker form is not recognized")
    require(blockers("open_blockers:\n  - blocked\nnext: value\n") == ["blocked"],
            "multiline blocker form is not recognized")

    state_path = ROOT / "project_state.yaml"
    state = state_path.read_text(encoding="utf-8")
    require(scalar(state, "architecture") == "avp-hybrid-native-v2",
            "architecture drifted")
    candidate_status = scalar(state, "review_candidate_status")
    require(candidate_status in {"REVIEW", "ACCEPTED", "CORRECTIONS_REQUIRED",
                                 "NOT_REVIEWABLE"},
            "unsupported candidate disposition")

    conditions = re.findall(
        r"(?m)^\s+- id:\s*([a-z0-9_]+)\s*\r?\n\s+status:\s*([A-Z_]+)\s*$",
        state)
    require(len(conditions) == 12, "project state must record 12 conditions")
    require(len({name for name, _ in conditions}) == 12,
            "capability condition ids are not unique")
    require(all(status in {"OPEN", "CLOSED"} for _, status in conditions),
            "unsupported capability condition status")
    closed_count = sum(status == "CLOSED" for _, status in conditions)
    require(scalar(state, "capability_gate") == f"{closed_count}/12",
            "capability count disagrees with condition statuses")

    for key in ("accepted_head", "review_candidate_head"):
        value = scalar(state, key)
        require(bool(re.fullmatch(r"[0-9a-f]{40}", value)),
                f"{key} is not a pinned Git hash")
        git("cat-file", "-e", f"{value}^{{commit}}")
    git("merge-base", "--is-ancestor", scalar(state, "accepted_head"),
        scalar(state, "review_candidate_head"))
    if candidate_status == "ACCEPTED":
        require(scalar(state, "accepted_head") ==
                scalar(state, "review_candidate_head"),
                "accepted candidate is not the accepted head")

    artifact_bindings = {
        "contract_sha256": ROOT / "data/avsp_vertical_slice_contract.json",
        "oracle_manifest_sha256":
            ROOT / "data/avsp_vertical_slice_oracle_manifest.json",
        "translation_boundary_sha256":
            ROOT / "data/avsp_translation_boundary.json",
        "writer_set_manifest_sha256":
            ROOT / "data/avsp_hit_ko_writer_set.json",
    }
    for key, path in artifact_bindings.items():
        value = scalar(state, key)
        require(value == normalized_sha256(path),
                f"{key} does not hash {path.name}")

    active_relative = scalar(state, "active_task_card")
    require(bool(re.fullmatch(r"docs/task_cards/[A-Za-z0-9._-]+\.md",
                              active_relative)),
            "active task card escapes docs/task_cards")
    active_card = (ROOT / active_relative).read_text(encoding="utf-8")
    for field in ("TASK", "STATUS", "CHECKPOINT", "BASE", "BRANCH", "TIER",
                  "DEPENDENCIES", "REQUIRED_LANES", "OPTIONAL_LANES"):
        scalar(active_card, field)

    accepted_tasks = set(inline_list(state, "accepted_tasks"))
    card_ids = {path.stem for path in (ROOT / "docs/task_cards").glob("*.md")}
    require(accepted_tasks <= card_ids, "accepted_tasks names an unknown card")
    validate_relationship(state, active_card, accepted_tasks)

    for card_path in sorted((ROOT / "docs/task_cards").glob("*.md")):
        card = card_path.read_text(encoding="utf-8")
        for field in ("TASK", "STATUS", "CHECKPOINT", "BASE", "BRANCH", "TIER",
                      "DEPENDENCIES", "REQUIRED_LANES", "OPTIONAL_LANES"):
            scalar(card, field)
        dependencies = set(inline_list(card, "DEPENDENCIES"))
        require(dependencies <= card_ids,
                f"{card_path.name} names an unknown dependency")
        required_lanes = inline_list(card, "REQUIRED_LANES")
        optional_lanes = inline_list(card, "OPTIONAL_LANES")
        allowed_lanes = {"Fast", "Oracle", "Full", "Target", "Emulator",
                         "Physical"}
        require(bool(required_lanes), f"{card_path.name} has no required lane")
        require(set(required_lanes + optional_lanes) <= allowed_lanes,
                f"{card_path.name} names an unsupported lane")
        require(not (set(required_lanes) & set(optional_lanes)),
                f"{card_path.name} repeats a required lane as optional")
        if dependencies <= accepted_tasks:
            require(scalar(card, "STATUS") != "BLOCKED",
                    f"{card_path.name} remains blocked after all dependencies accepted")
        for section in ("## Objective", "## Owned paths", "## Done",
                        "## Exclude", "## Stop"):
            require(section in card, f"{card_path.name} missing {section}")

    require(inline_list((ROOT / "docs/task_cards/V2-2B.md").read_text(
                encoding="utf-8"), "REQUIRED_LANES") == ["Fast", "Oracle", "Full"],
            "writer-map trust boundary lacks Fast, Oracle, Full")
    require(inline_list((ROOT / "docs/task_cards/WF-1.md").read_text(
                encoding="utf-8"), "REQUIRED_LANES") == ["Fast"],
            "workflow-only task requires more than Fast")
    require(inline_list((ROOT / "docs/task_cards/V2-B1.md").read_text(
                encoding="utf-8"), "REQUIRED_LANES") == ["Fast", "Oracle"],
            "native host HIT/KO task lacks Fast and Oracle")

    next_card_path = ROOT / "docs/task_cards/V2-B1.md"
    next_card = next_card_path.read_text(encoding="utf-8")
    simulated_state = re.sub(
        r"(?m)^active_task_card:.*$", "active_task_card: docs/task_cards/V2-B1.md",
        state)
    simulated_state = re.sub(
        r"(?m)^task_status:.*$", "task_status: READY", simulated_state)
    simulated_state = re.sub(
        r"(?m)^current_checkpoint:.*$",
        "current_checkpoint: V2-B1-native-hit-ko", simulated_state)
    simulated_state = re.sub(
        r"(?m)^accepted_head:.*$",
        "accepted_head: " + scalar(state, "review_candidate_head"), simulated_state)
    simulated_state = re.sub(
        r"(?m)^review_candidate_status:.*$",
        "review_candidate_status: ACCEPTED", simulated_state)
    simulated_state = re.sub(
        r"(?m)^accepted_tasks:.*$", "accepted_tasks: [V2-2B]", simulated_state)
    simulated_state = re.sub(
        r"(?m)^open_blockers:[ \t]*\r?\n(?:^[ \t]+[^\r\n]*(?:\r?\n|$))*",
        "open_blockers: []\n", simulated_state)
    simulated_card = re.sub(r"(?m)^STATUS:.*$", "STATUS: READY", next_card)
    validate_relationship(simulated_state, simulated_card, {"V2-2B"})

    writer = json.loads(
        (ROOT / "data/avsp_hit_ko_writer_set.json").read_text(encoding="utf-8"))
    require(writer["inputs"]["contract_sha256"] ==
            scalar(state, "contract_sha256"), "writer/contract binding drifted")
    require(writer["inputs"]["oracle_sha256"] ==
            scalar(state, "oracle_manifest_sha256"), "writer/oracle binding drifted")
    require(writer["inputs"]["boundary_sha256"] ==
            scalar(state, "translation_boundary_sha256"),
            "writer/boundary binding drifted")

    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for obsolete in ("NEXT_AGENT_PROMPT", "IMPLEMENTOR_INVOCATION",
                     "CODEX_REVIEW_TEMPLATE"):
        require(obsolete not in agents, f"durable policy names obsolete {obsolete}")
    require(not re.search(r"\b[0-9a-f]{40}\b", agents),
            "durable policy contains a volatile commit SHA")
    require(len(agents.splitlines()) < 190,
            "durable policy grew beyond its limit")

    for relative in ("docs/NEXT_AGENT_PROMPT.md",
                     "docs/CODEX_REVIEW_TEMPLATE.md",
                     "docs/IMPLEMENTOR_INVOCATION.md"):
        require(not (ROOT / relative).exists(),
                f"obsolete control file exists: {relative}")

    implementer = (ROOT / ".codex/agents/avp-implementer.toml").read_text(
        encoding="utf-8")
    require('model_reasoning_effort = "low"' not in implementer,
            "implementer remains permanently pinned to low reasoning")

    supervisor = (ROOT / ".codex/agents/supervisor.toml").read_text(
        encoding="utf-8")
    for profile in ("semantic-reviewer", "provenance-reviewer",
                    "saturn-reviewer"):
        require(profile in supervisor,
                f"Tier 2 supervisor omits {profile}")

    verify = (ROOT / "verify.ps1").read_text(encoding="utf-8")
    for lane in ("Fast", "Oracle", "Target", "Full"):
        require(f"'{lane}'" in verify, f"verify.ps1 lacks {lane} lane")
    for token in ("[string[]]$Command", "INCOMPLETE", "[switch]$BuildOnly",
                  "[string[]]$EmulatorCheck", "release-normal-release",
                  "tests\\target\\verify_release_readback.py", "BUILD_ONLY",
                  "Emulator readback check is not committed",
                  "LastWriteTimeUtc",
                  "tracked_dirty_before_count", "git_tree",
                  "full-shadow-diff.json", "git worktree add --detach"):
        require(token in verify, f"verify.ps1 lacks {token}")
    require("test.ps1" in verify, "Full lane is not connected to test.ps1")

    launcher = (ROOT / "tools/start-agent-task.ps1").read_text(encoding="utf-8")
    for token in ("active_task_card", "task_status", "current_checkpoint",
                  "open_blockers", "acceptedHead -ne $candidateHead",
                  "Read-Blockers", "TaskKind", "Correction",
                  "existing branch/worktree", "preexisting_changes",
                  "--is-ancestor $acceptedHead $base",
                  "--untracked-files=no", "repository.HEAD", "gpt-5.6-sol",
                  "xhigh", "REQUIRED_LANES", "DEPENDENCIES"):
        require(token in launcher, f"launcher lacks invariant: {token}")

    executor = (ROOT / "tools/Invoke-TaskExecutor.ps1").read_text(
        encoding="utf-8")
    for token in ("EXECUTOR_POLICY", "PREFERRED_EXECUTOR", "CLAUDE_MODEL",
                  "CLAUDE_EFFORT", "ResumeSessionId", "FeedbackPath",
                  "READY_FOR_REVIEW", "VERIFICATION_FAILED",
                  "Invoke-VerificationLane", "New-ReviewBundle.ps1"):
        require(token in executor, f"task executor lacks {token}")
    require("for ($attempt" not in executor,
            "task executor contains an autonomous repair loop")
    require("if (-not $claudeModel) { $claudeModel = 'fable' }" in executor,
            "Claude executor does not default to fable")
    require("@('CODEX', 'CLAUDE', 'EITHER')" in executor,
            "Claude executor policy vocabulary drifted")
    require("@('low', 'medium')" in executor,
            "Claude executor effort exceeds the bounded contract")

    disposition = (ROOT / "tools/Apply-ReviewDisposition.ps1").read_text(
        encoding="utf-8")
    for token in ("review_bundle_sha256", "output_sha256", "semantic",
                  "provenance", "saturn", "conservatively resolve",
                  "automatic selection is forbidden",
                  "must be integrated into controller HEAD"):
        require(token in disposition,
                f"disposition helper lacks invariant: {token}")
    require(not (ROOT / "tools/Invoke-AvpControlLoop.ps1").exists(),
            "repository contains a second autonomous planning loop")
    require(not (ROOT / ".codex/hooks.json").exists(),
            "repository contains a self-advancing Stop hook")

    bundle = (ROOT / "tools/New-ReviewBundle.ps1").read_text(encoding="utf-8")
    for token in ("clean committed candidate", "HEAD^{tree}",
                  "Patch SHA-256", "## Exact patch", "summary.checks",
                  "STALE/EXCLUDED", "build\\review",
                  "TaskCard", "CandidateRoot",
                  "VERDICT: ACCEPTED | CORRECTIONS REQUIRED | NOT REVIEWABLE"):
        require(token in bundle, f"review bundle lacks {token}")

    release_readback = ROOT / "tests/target/verify_release_readback.py"
    require(release_readback.is_file(), "canonical release readback is missing")
    release_text = release_readback.read_text(encoding="utf-8")
    for token in ("release-normal-release", "game_iso_sha256",
                  "oracle_manifest_sha256", "semantic", "resource", "render",
                  "final_scanout", "ONE_EMULATOR"):
        require(token in release_text,
                f"canonical release readback lacks {token}")

    handoff_lines = (ROOT / "docs/AGENT_HANDOFF.md").read_text(
        encoding="utf-8").splitlines()
    require(len(handoff_lines) < 70,
            "active handoff became an append-only narrative")

    roadmap = (ROOT / "docs/PARITY_PLAN.md").read_text(encoding="utf-8")
    for heading in ("## 1. Goal", "## 2. AvP performance contract",
                    "## 3. Accepted baseline and current checkpoint",
                    "## 4. Active backlog", "## 5. Delivery roadmap",
                    "## 6. Capability slice conditions",
                    "## 7. Full-port completion conditions",
                    "## 8. Parked work", "## 9. Update rules"):
        require(heading in roadmap, f"roadmap missing {heading}")
    for milestone in range(14):
        require(f"### R{milestone} " in roadmap,
                f"roadmap missing R{milestone}")
    for token in ("909-tile", "15%", "quality calibration",
                  "MSHvSF measurement as a prerequisite"):
        require(token in roadmap, f"roadmap contract lacks {token}")
    backlog = roadmap.split("## 4. Active backlog", 1)[1].split(
        "## 5. Delivery roadmap", 1)[0]
    priorities = re.findall(r"(?m)^\|\s*([1-8])\s*\|", backlog)
    require(priorities == [str(value) for value in range(1, 9)],
            "active backlog is not exactly priorities 1 through 8")
    roadmap_task = scalar(roadmap, "CURRENT_TASK")
    require(roadmap_task == Path(active_relative).stem,
            "roadmap current task disagrees with project state")
    require(not re.search(r"\b[0-9a-f]{40}\b", roadmap),
            "roadmap repeats volatile full Git SHAs")

    print("workflow policy: PASS")


if __name__ == "__main__":
    main()
