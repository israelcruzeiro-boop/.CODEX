from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_quality_gate as gate


class QualityGateRunnerTests(unittest.TestCase):
    def test_gate_contains_every_required_continuous_check(self) -> None:
        names = [command.name for command in gate.build_commands("python")]
        self.assertEqual(
            names,
            [
                "compileall",
                "claude-wrapper-parity",
                "arsenal-contract",
                "project-coverage",
                "skill-contracts",
                "unit-and-adversarial-tests",
                "diff-check",
                "generated-drift-check",
            ],
        )

    def test_gate_reports_failed_command_but_runs_all_checks(self) -> None:
        calls: list[tuple[str, ...]] = []

        def runner(argv, cwd):
            calls.append(tuple(argv))
            code = 1 if "validate_arsenal.py" in " ".join(argv) else 0
            return subprocess.CompletedProcess(argv, code, stdout="arsenal failed" if code else "")

        evidence = gate.run_gate(Path.cwd(), runner=runner, python="python")
        self.assertEqual(len(calls), len(gate.build_commands("python")))
        self.assertFalse(all(item.passed for item in evidence))
        self.assertEqual([item.name for item in evidence if not item.passed], ["arsenal-contract"])

    def test_dirty_worktree_output_fails_even_with_zero_exit(self) -> None:
        def runner(argv, cwd):
            output = "?? generated.txt\n" if argv[:2] == ("git", "status") else ""
            return subprocess.CompletedProcess(argv, 0, stdout=output)

        evidence = gate.run_gate(Path.cwd(), runner=runner, python="python")
        final = evidence[-1]
        self.assertEqual(final.name, "generated-drift-check")
        self.assertFalse(final.passed)

    def test_os_error_is_recorded_as_exit_127(self) -> None:
        def runner(argv, cwd):
            raise OSError("missing executable")

        evidence = gate.run_gate(Path.cwd(), runner=runner, python="python")
        self.assertTrue(all(item.exit_code == 127 and not item.passed for item in evidence))

    def test_console_output_is_safe_for_legacy_code_pages(self) -> None:
        original = gate.sys.stdout

        class LegacyConsole:
            encoding = "cp1252"

        try:
            gate.sys.stdout = LegacyConsole()  # type: ignore[assignment]
            rendered = gate._console_safe("broken: \ufffd")
        finally:
            gate.sys.stdout = original
        self.assertEqual(rendered, "broken: \\ufffd")

    def test_long_output_preserves_beginning_and_end_with_marker(self) -> None:
        output = "BEGIN\n" + ("x" * 15000) + "\nEND"
        bounded = gate._bounded_output(output)
        self.assertLessEqual(len(bounded), gate.OUTPUT_LIMIT)
        self.assertTrue(bounded.startswith("BEGIN\n"))
        self.assertTrue(bounded.endswith("\nEND"))
        self.assertIn("TRUNCATED", bounded)
        self.assertIn("BEGINNING AND END PRESERVED", bounded)


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[2]
        cls.workflow = (cls.root / ".github" / "workflows" / "arsenal-ci.yml").read_text(encoding="utf-8")
        cls.dependabot = (cls.root / ".github" / "dependabot.yml").read_text(encoding="utf-8")

    def test_workflow_has_minimum_permissions_concurrency_and_timeout(self) -> None:
        self.assertIn("permissions:\n  contents: read", self.workflow)
        self.assertIn("concurrency:", self.workflow)
        self.assertIn("cancel-in-progress: true", self.workflow)
        timeout = re.search(r"timeout-minutes:\s*(\d+)", self.workflow)
        self.assertIsNotNone(timeout)
        self.assertGreater(int(timeout.group(1)), 0)  # type: ignore[union-attr]
        self.assertLessEqual(int(timeout.group(1)), 20)  # type: ignore[union-attr]

    def test_workflow_tests_windows_linux_and_python_floor(self) -> None:
        self.assertIn("ubuntu-latest", self.workflow)
        self.assertIn("windows-latest", self.workflow)
        self.assertRegex(self.workflow, r"['\"]3\.11['\"]")
        self.assertRegex(self.workflow, r"['\"]3\.14['\"]")
        self.assertIn("run_quality_gate.py", self.workflow)

    def test_every_action_is_pinned_to_full_sha(self) -> None:
        uses = [line.split("uses:", 1)[1].strip() for line in self.workflow.splitlines() if "uses:" in line]
        self.assertTrue(uses)
        for reference in uses:
            self.assertRegex(reference, r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}(?:\s+#.*)?$")

    def test_checkout_does_not_persist_credentials(self) -> None:
        self.assertIn("persist-credentials: false", self.workflow)

    def test_dependabot_is_scoped_to_github_actions(self) -> None:
        self.assertIn('package-ecosystem: "github-actions"', self.dependabot)
        self.assertIn('directory: "/"', self.dependabot)
        self.assertIn("interval: \"weekly\"", self.dependabot)


if __name__ == "__main__":
    unittest.main()
