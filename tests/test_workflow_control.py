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
        for name in ("start-agent-task.ps1", "Apply-ReviewDisposition.ps1"):
            shutil.copy2(SOURCE_ROOT / "tools" / name, self.root / "tools" / name)
        run(["git", "init", "-b", "control"], self.root)
        run(["git", "config", "user.email", "workflow-test@example.invalid"], self.root)
        run(["git", "config", "user.name", "Workflow Test"], self.root)
        (self.root / "AGENTS.md").write_text("# Fixture policy\n", encoding="utf-8")
        (self.root / "capture.ps1").write_text("# retained\n", encoding="utf-8")
        (self.root / "seed.txt").write_text("base\n", encoding="utf-8")
        run(["git", "add", "AGENTS.md", "capture.ps1", "seed.txt"], self.root)
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
