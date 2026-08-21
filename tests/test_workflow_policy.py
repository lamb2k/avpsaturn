#!/usr/bin/env python3
"""Fast policy invariants for the interactive AvP salvage workflow."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def scalar(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}:\s*(.+?)\s*$", text)
    require(match is not None, f"missing {name}")
    return match.group(1).strip()


def main() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    require(len(agents.splitlines()) < 150, "AGENTS.md is not concise")
    for token in (
        "Codex Goal Mode owns interactive implementation",
        "`docs/PARITY_PLAN.md` is the only roadmap",
        "Exactly one implementation task owns writes at a time",
        "implementation is the default for ordinary work",
        "nested Codex executors are",
        "not used for ordinary implementation",
        "Claude is an optional bounded provider",
        "automatically correct ordinary compile",
        "A passing emulator check is not human",
        "A user-approved component is locked",
        "build/feedback/<task-id>/",
    ):
        require(token in agents, f"AGENTS.md missing policy: {token}")
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
        "not as final gameplay authority",
        "does not itself advance parity",
        "complete port",
    ):
        require(token in goal, f"goal missing {token}")

    architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    require("interactive salvage-and-promotion loop" in architecture and
            "do not advance production parity" in architecture,
            "active architecture conflicts with salvage governance")

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
    for milestone in range(14):
        require(f"### R{milestone} " in roadmap,
                f"roadmap missing R{milestone}")
    for token in (
        "only roadmap",
        "Isolated salvage benches",
        "Define production interfaces",
        "V2-2B remains unresolved",
        "not for loading, controller",
        "909-tile",
        "15%",
        "physical capability slice",
    ):
        require(token in roadmap, f"roadmap missing {token}")
    require(scalar(roadmap, "CURRENT_TASK") ==
            "SALVAGE-00-OLD-BUILD-BASELINE",
            "roadmap does not route to first salvage card")
    require(not re.search(r"\b[0-9a-f]{40}\b", roadmap),
            "roadmap repeats volatile commit SHAs")

    handoff = (ROOT / "docs/AGENT_HANDOFF.md").read_text(encoding="utf-8")
    require(len(handoff.splitlines()) < 50,
            "handoff became a historical narrative")
    for token in (
        "Workflow pivot",
        "Preserved paused work",
        "SALVAGE-00-OLD-BUILD-BASELINE",
        "USER-01-PLAYER-BASELINE-REVIEW",
    ):
        require(token in handoff, f"handoff missing {token}")

    require((ROOT / "data/port_v2_migration_map.yaml").is_file(),
            "migration ledger is missing")
    require((ROOT / "tools/New-ReviewBundle.ps1").is_file(),
            "evidence review bundle helper was removed")

    print("workflow policy: PASS")


if __name__ == "__main__":
    main()
