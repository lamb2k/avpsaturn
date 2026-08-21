#!/usr/bin/env python3
"""Fixture tests for the executable workflow controller."""

from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("powershell.exe") or shutil.which("pwsh")


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


class WorkflowFixture:
    def __init__(self, parent: Path) -> None:
        self.root = parent / "control"
        self.candidate = parent / "candidate"
        (self.root / "tools").mkdir(parents=True)
        (self.root / "docs" / "task_cards").mkdir(parents=True)
        (self.root / ".codex").mkdir(parents=True)
        for name in (
            "start-agent-task.ps1",
            "Apply-ReviewDisposition.ps1",
            "Invoke-TaskExecutor.ps1",
        ):
            shutil.copy2(SOURCE_ROOT / "tools" / name, self.root / "tools" / name)
        run(["git", "init", "-b", "control"], self.root)
        run(["git", "config", "user.email", "workflow-test@example.invalid"], self.root)
        run(["git", "config", "user.name", "Workflow Test"], self.root)
        (self.root / "AGENTS.md").write_text("# Fixture policy\n", encoding="utf-8")
        (self.root / "docs" / "PARITY_PLAN.md").write_text(
            "# Fixture roadmap\n", encoding="utf-8"
        )
        (self.root / "capture.ps1").write_text("# retained\n", encoding="utf-8")
        (self.root / "seed.txt").write_text("base\n", encoding="utf-8")
        run(
            [
                "git",
                "add",
                "AGENTS.md",
                "docs/PARITY_PLAN.md",
                "capture.ps1",
                "seed.txt",
            ],
            self.root,
        )
        run(["git", "commit", "-m", "base"], self.root)
        self.accepted = run(["git", "rev-parse", "HEAD"], self.root).stdout.strip()
        run(
            ["git", "worktree", "add", "-b", "candidate", str(self.candidate), self.accepted],
            self.root,
        )
        (self.candidate / "seed.txt").write_text("candidate\n", encoding="utf-8")
        run(["git", "add", "seed.txt"], self.candidate)
        run(["git", "commit", "-m", "candidate"], self.candidate)
        self.reviewed = run(["git", "rev-parse", "HEAD"], self.candidate).stdout.strip()
        (self.candidate / "capture.ps1").unlink()

        state = f"""schema: 1
architecture: fixture
accepted_head: {self.accepted}
review_candidate_head: {self.reviewed}
review_candidate_status: CORRECTIONS_REQUIRED
current_checkpoint: FIX-1-correction
active_task_card: docs/task_cards/FIX-1.md
task_status: CORRECTIONS
accepted_tasks: []
open_blockers:
  - Preserve and commit the expected deletion.
"""
        card = f"""# Fixture

TASK: fixture correction
STATUS: CORRECTIONS
CHECKPOINT: FIX-1-correction
BASE: {self.accepted}
BRANCH: candidate
TIER: 1
EXECUTOR_POLICY: EITHER
NEXT_TASK: AUTO
DEPENDENCIES: []
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CORRECTION_PATHS: [capture.ps1, seed.txt]
"""
        (self.root / "project_state.yaml").write_text(state, encoding="utf-8")
        (self.root / "docs" / "task_cards" / "FIX-1.md").write_text(card, encoding="utf-8")
        run(["git", "add", "project_state.yaml", "docs/task_cards/FIX-1.md"], self.root)
        run(["git", "commit", "-m", "activate correction"], self.root)


@unittest.skipUnless(POWERSHELL, "PowerShell is required")
class WorkflowControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="avp-workflow-test-")
        self.fixture = WorkflowFixture(Path(self.temp.name))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def invoke(self, script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
        return run(
            [
                POWERSHELL,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(self.fixture.root / "tools" / script),
                *arguments,
            ],
            self.fixture.root,
        )

    def executor_plan(self, *arguments: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = self.invoke(
            "Invoke-TaskExecutor.ps1",
            "-Task",
            "FIX-1",
            "-PlanOnly",
            "-ProjectRoot",
            str(self.fixture.root),
            *arguments,
        )
        if result.returncode != 0:
            return result, {}
        plan_line = next(
            line for line in result.stdout.splitlines() if line.startswith("PLAN: ")
        )
        plan = json.loads(Path(plan_line[6:].strip()).read_text(encoding="utf-8-sig"))
        return result, plan

    def activate_ready(self, dependencies: str = "[]") -> None:
        state_path = self.fixture.root / "project_state.yaml"
        state_path.write_text(
            f"""schema: 1
architecture: fixture
accepted_head: {self.fixture.accepted}
review_candidate_head: {self.fixture.accepted}
review_candidate_status: ACCEPTED
current_checkpoint: FIX-1-ready
active_task_card: docs/task_cards/FIX-1.md
task_status: READY
accepted_tasks: []
open_blockers: []
""",
            encoding="utf-8",
        )
        card_path = self.fixture.root / "docs" / "task_cards" / "FIX-1.md"
        card_path.write_text(
            f"""# Fixture

TASK: fixture implementation
STATUS: READY
CHECKPOINT: FIX-1-ready
BASE: repository.HEAD
BRANCH: ready-implementation
TIER: 1
EXECUTOR_POLICY: EITHER
PREFERRED_EXECUTOR: CLAUDE
CLAUDE_MODEL: fable
CLAUDE_EFFORT: medium
NEXT_TASK: AUTO
DEPENDENCIES: {dependencies}
REQUIRED_LANES: [Fast]
OPTIONAL_LANES: []
CORRECTION_PATHS: []
""",
            encoding="utf-8",
        )
        run(
            ["git", "add", "project_state.yaml", "docs/task_cards/FIX-1.md"],
            self.fixture.root,
        )
        committed = run(
            ["git", "commit", "-m", "activate ready fixture"], self.fixture.root
        )
        self.assertEqual(committed.returncode, 0, committed.stdout)

    def test_executor_defaults_are_codex_fable_medium(self) -> None:
        result, plan = self.executor_plan()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(plan["executor_policy"], "EITHER")
        self.assertEqual(plan["preferred_executor"], "CODEX")
        self.assertEqual(plan["executor"], "Codex")
        self.assertEqual(plan["claude_model"], "fable")
        self.assertEqual(plan["claude_effort"], "medium")

    def test_claude_plan_selects_fable_and_supports_low_override(self) -> None:
        result, plan = self.executor_plan("-Executor", "Claude")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(plan["executor"], "Claude")
        self.assertEqual(plan["claude_model"], "fable")
        self.assertEqual(plan["claude_effort"], "medium")
        self.assertEqual(plan["model"], "fable")
        self.assertEqual(plan["effort"], "medium")
        self.assertEqual(plan["base"], self.fixture.accepted)
        result, plan = self.executor_plan(
            "-Executor", "Claude", "-Effort", "low"
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(plan["claude_effort"], "low")

    def test_claude_effort_can_come_from_task_card(self) -> None:
        card = self.fixture.root / "docs" / "task_cards" / "FIX-1.md"
        text = card.read_text(encoding="utf-8")
        text += "PREFERRED_EXECUTOR: CLAUDE\nCLAUDE_MODEL: fable\nCLAUDE_EFFORT: low\n"
        card.write_text(text, encoding="utf-8")
        result, plan = self.executor_plan("-Executor", "Claude")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(plan["executor"], "Claude")
        self.assertEqual(plan["claude_model"], "fable")
        self.assertEqual(plan["claude_effort"], "low")

    def test_executor_plan_reuses_correction_worktree_without_state_change(self) -> None:
        before_state = (self.fixture.root / "project_state.yaml").read_bytes()
        before_roadmap = (self.fixture.root / "docs" / "PARITY_PLAN.md").read_bytes()
        result, plan = self.executor_plan("-Executor", "Claude")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(plan["task_kind"], "Correction")
        self.assertEqual(Path(plan["worktree"]), self.fixture.candidate)
        self.assertEqual(
            plan["preexisting_changes"], [{"status": "D", "path": "capture.ps1"}]
        )
        self.assertEqual(
            (self.fixture.root / "project_state.yaml").read_bytes(), before_state
        )
        self.assertEqual(
            (self.fixture.root / "docs" / "PARITY_PLAN.md").read_bytes(),
            before_roadmap,
        )

    def test_ready_task_resolves_declared_branch_and_new_worktree(self) -> None:
        self.activate_ready()
        result, plan = self.executor_plan()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(plan["task_kind"], "Implementation")
        self.assertEqual(plan["executor"], "Claude")
        self.assertEqual(plan["branch"], "ready-implementation")
        worktree = Path(plan["worktree"])
        self.assertTrue(worktree.is_dir())
        branch = run(["git", "branch", "--show-current"], worktree)
        self.assertEqual(branch.stdout.strip(), "ready-implementation")

    def test_claude_cannot_bypass_unaccepted_dependency(self) -> None:
        self.activate_ready("[NEEDED]")
        result, _ = self.executor_plan("-Executor", "Claude")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("depends on unaccepted task NEEDED", result.stdout)

    def test_executor_cannot_select_an_inactive_task(self) -> None:
        inactive = self.fixture.root / "docs" / "task_cards" / "OTHER.md"
        inactive.write_text(
            (self.fixture.root / "docs" / "task_cards" / "FIX-1.md")
            .read_text(encoding="utf-8")
            .replace("TASK: fixture correction", "TASK: inactive"),
            encoding="utf-8",
        )
        result = self.invoke(
            "Invoke-TaskExecutor.ps1",
            "-Task",
            "OTHER",
            "-Executor",
            "Claude",
            "-PlanOnly",
            "-ProjectRoot",
            str(self.fixture.root),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("is not active", result.stdout)

    def test_correction_launch_reuses_worktree_and_fingerprints_dirt(self) -> None:
        result = self.invoke(
            "start-agent-task.ps1", "-Task", "FIX-1", "-TaskKind", "Correction"
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        metadata_line = next(
            line for line in result.stdout.splitlines() if line.startswith("Metadata: ")
        )
        metadata = json.loads(Path(metadata_line[10:].strip()).read_text(encoding="utf-8-sig"))
        self.assertEqual(metadata["task_kind"], "Correction")
        self.assertEqual(Path(metadata["worktree"]), self.fixture.candidate)
        self.assertEqual(
            metadata["preexisting_changes"], [{"status": "D", "path": "capture.ps1"}]
        )

    def test_correction_launch_cannot_prepare_a_new_worktree(self) -> None:
        result = self.invoke(
            "start-agent-task.ps1",
            "-Task",
            "FIX-1",
            "-TaskKind",
            "Correction",
            "-Prepare",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reuse the existing branch/worktree", result.stdout)

    def test_external_correction_disposition_is_applied_mechanically(self) -> None:
        run(["git", "add", "capture.ps1"], self.fixture.candidate)
        run(["git", "commit", "-m", "bounded correction"], self.fixture.candidate)
        candidate_head = run(
            ["git", "rev-parse", "HEAD"], self.fixture.candidate
        ).stdout.strip()
        review_root = self.fixture.root / "build" / "reviews"
        review_root.mkdir(parents=True)
        bundle = review_root / "bundle.md"
        bundle.write_text(
            f"Task: FIX-1\nHead: `{candidate_head}`\n", encoding="utf-8"
        )
        reviews = []
        for role in ("semantic", "provenance", "saturn"):
            output = review_root / f"{role}.txt"
            output.write_text(
                "VERDICT: CORRECTIONS REQUIRED\nBLOCKING:\n- fixture blocker\n"
                "NONBLOCKING:\nEVIDENCE:\nNEXT ACTION:\n",
                encoding="utf-8",
            )
            reviews.append(
                {
                    "role": role,
                    "verdict": "CORRECTIONS REQUIRED",
                    "output_path": str(output),
                    "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                }
            )
        disposition = review_root / "disposition.json"
        disposition.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "task": "FIX-1",
                    "candidate_head": candidate_head,
                    "verdict": "CORRECTIONS REQUIRED",
                    "blocking": ["fixture blocker"],
                    "review_bundle_path": str(bundle),
                    "review_bundle_sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
                    "reviews": reviews,
                }
            ),
            encoding="utf-8",
        )
        result = self.invoke(
            "Apply-ReviewDisposition.ps1", "-DispositionPath", str(disposition)
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        state = (self.fixture.root / "project_state.yaml").read_text(encoding="utf-8-sig")
        self.assertIn(f"review_candidate_head: {candidate_head}", state)
        self.assertIn("review_candidate_status: CORRECTIONS_REQUIRED", state)
        self.assertIn("task_status: CORRECTIONS", state)
        self.assertIn("  - fixture blocker", state)


if __name__ == "__main__":
    unittest.main()
