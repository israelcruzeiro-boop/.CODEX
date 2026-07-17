from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_skill_contract_evals as evals  # noqa: E402


class SkillContractEvalTests(unittest.TestCase):
    def _temp_file(self, content: str, name: str = "fixture.toml") -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / name
        path.write_text(content, encoding="utf-8")
        return path

    def _manifest_data(self) -> dict[str, object]:
        with evals.DEFAULT_MANIFEST.open("rb") as stream:
            return tomllib.load(stream)

    def _results_text(self) -> str:
        data = self._manifest_data()
        lines = [
            'run_id = "forward-test-2026-07-16"',
            'executor = "fresh-agent-eval-harness"',
            'executed_at = "2026-07-16T18:00:00-03:00"',
        ]
        for case in data["cases"]:  # type: ignore[index]
            invocation = case["expected_invocation"]
            invoked = [case["skill"]] if invocation == "REQUIRED" else []
            decision = "INVOKED" if invoked else "SKIPPED"
            validators = [
                value for value in case["validators"] if not value.startswith("N/A - ")
            ]
            validator_results = ", ".join(
                f'{{ path = {json.dumps(value)}, exit_code = 0 }}' for value in validators
            )
            lines.extend(
                [
                    "",
                    "[[results]]",
                    f'case_id = {json.dumps(case["id"])}',
                    f"invoked_skills = {json.dumps(invoked)}",
                    f'decision = "{decision}"',
                    'reason = "Observed routing follows the isolated case evidence and declared trigger contract."',
                    'outcome = "PASS"',
                    f'output_contract = {json.dumps(case["expected_contract"])}',
                    f'evidence = {json.dumps(case["evidence_required"])}',
                    f"validator_results = [{validator_results}]",
                ]
            )
        return "\n".join(lines) + "\n"

    def test_canonical_manifest_has_required_coverage(self) -> None:
        report = evals.evaluate()
        self.assertTrue(report.ok, report.errors)
        self.assertFalse(report.execution_proven)
        self.assertEqual(24, len(report.cases))
        for counts in report.coverage.values():
            self.assertEqual(
                {"total": 4, "trigger": 2, "boundary": 1, "negative": 1},
                counts,
            )

    def test_json_cli_distinguishes_manifest_from_execution_proof(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = evals.main(["--json"])
        payload = json.loads(output.getvalue())
        self.assertEqual(0, exit_code)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["execution_proven"])
        self.assertEqual(24, payload["summary"]["cases"])

    def test_require_results_fails_without_observed_run(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = evals.main(["--require-results", "--json"])
        payload = json.loads(output.getvalue())
        self.assertEqual(1, exit_code)
        self.assertIn("execution-required", {item["code"] for item in payload["errors"]})

    def test_complete_observed_run_proves_execution(self) -> None:
        results = self._temp_file(self._results_text(), "results.toml")
        report = evals.evaluate(results=results)
        self.assertTrue(report.ok, report.errors)
        self.assertTrue(report.execution_proven)

    def test_required_skill_must_be_observed(self) -> None:
        text = self._results_text().replace(
            'invoked_skills = ["agent-forge"]',
            "invoked_skills = []",
            1,
        )
        report = evals.evaluate(results=self._temp_file(text, "results.toml"))
        self.assertIn("required-skill-not-invoked", {issue.code for issue in report.errors})
        self.assertFalse(report.execution_proven)

    def test_validator_exit_must_be_zero(self) -> None:
        text = self._results_text().replace("exit_code = 0", "exit_code = 9", 1)
        report = evals.evaluate(results=self._temp_file(text, "results.toml"))
        self.assertIn("validator-failed", {issue.code for issue in report.errors})

    def test_manifest_rejects_invalid_evidence_contract(self) -> None:
        text = evals.DEFAULT_MANIFEST.read_text(encoding="utf-8").replace(
            '"decision:creation-gate"',
            '"Decision With Spaces"',
            1,
        )
        report = evals.evaluate(manifest=self._temp_file(text))
        self.assertIn("invalid-evidence-contract", {issue.code for issue in report.errors})

    def test_manifest_rejects_unknown_validator(self) -> None:
        text = evals.DEFAULT_MANIFEST.read_text(encoding="utf-8").replace(
            "RUNTIME_Bridge/scripts/validate_arsenal.py",
            "RUNTIME_Bridge/scripts/does_not_exist.py",
            1,
        )
        report = evals.evaluate(manifest=self._temp_file(text))
        self.assertIn("missing-validator", {issue.code for issue in report.errors})

    def test_manifest_rejects_coverage_contract_drift(self) -> None:
        text = evals.DEFAULT_MANIFEST.read_text(encoding="utf-8").replace(
            "minimum_trigger_per_skill = 2",
            "minimum_trigger_per_skill = 3",
            1,
        )
        report = evals.evaluate(manifest=self._temp_file(text))
        self.assertIn("invalid-coverage-contract", {issue.code for issue in report.errors})


if __name__ == "__main__":
    unittest.main()
