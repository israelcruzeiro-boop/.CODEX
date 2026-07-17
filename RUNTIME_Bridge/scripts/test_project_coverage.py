from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_project_coverage as coverage  # noqa: E402


KIT = Path(__file__).resolve().parents[2]
MAP = KIT / "RUNTIME_Bridge" / "PROJECT_COVERAGE_MAP.toml"


class ProjectCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = coverage.load_document(MAP)

    def errors_for(self, data: dict) -> list[str]:
        return coverage.validate_data(KIT, data)

    def profile(self, data: dict, profile_id: str) -> dict:
        return next(item for item in data["profiles"] if item["id"] == profile_id)

    def test_canonical_map_is_valid(self) -> None:
        self.assertEqual([], self.errors_for(self.data))

    def test_partial_profile_requires_forge_fallback(self) -> None:
        data = copy.deepcopy(self.data)
        self.profile(data, "DESKTOP")["fallback"] = []
        self.assertTrue(any("requires fallback @F" in item for item in self.errors_for(data)))

    def test_absent_profile_cannot_claim_owner(self) -> None:
        data = copy.deepcopy(self.data)
        self.profile(data, "EMBEDDED")["owners"] = ["@A"]
        self.assertTrue(any("AUSENTE cannot declare" in item for item in self.errors_for(data)))

    def test_cli_never_inherits_playwright_gate(self) -> None:
        data = copy.deepcopy(self.data)
        self.profile(data, "CLI_SDK_PACKAGE")["tests"].append("Playwright")
        self.assertTrue(any("CLI_NOT_PLAYWRIGHT failed" in item for item in self.errors_for(data)))

    def test_classical_ml_is_not_owned_by_ai(self) -> None:
        data = copy.deepcopy(self.data)
        self.profile(data, "ML_ENGINEERING")["owners"] = ["@AI"]
        self.assertTrue(any("ML_NOT_AI failed" in item for item in self.errors_for(data)))

    def test_etl_is_not_owned_by_database_migrations(self) -> None:
        data = copy.deepcopy(self.data)
        self.profile(data, "DATA_ENGINEERING")["owners"] = ["@DATA"]
        self.assertTrue(any("ETL_NOT_DATA failed" in item for item in self.errors_for(data)))

    def test_ci_provider_must_be_detected(self) -> None:
        data = copy.deepcopy(self.data)
        data["coverage"]["ci_provider_policy"] = "GITHUB_ACTIONS"
        self.assertTrue(any("must be DETECT" in item for item in self.errors_for(data)))

    def test_missing_canonical_profile_fails(self) -> None:
        data = copy.deepcopy(self.data)
        data["profiles"] = [item for item in data["profiles"] if item["id"] != "GAME"]
        self.assertTrue(any("Missing canonical profiles" in item for item in self.errors_for(data)))

    def test_evidence_cannot_escape_kit(self) -> None:
        data = copy.deepcopy(self.data)
        self.profile(data, "WEB_FRONTEND")["evidence"] = ["../outside.md"]
        self.assertTrue(any("unsafe relative path" in item for item in self.errors_for(data)))

    def test_observed_owner_requires_canonical_source_and_runtime_wrapper(self) -> None:
        data = copy.deepcopy(self.data)
        self.profile(data, "WEB_FRONTEND")["evidence"] = ["AGENTS.md"]
        errors = self.errors_for(data)
        self.assertTrue(any("canonical source" in item for item in errors))

    def test_profile_scenario_status_and_owner_must_match_profile(self) -> None:
        data = copy.deepcopy(self.data)
        data["profile_scenarios"][0]["expected_status"] = "AUSENTE"
        data["profile_scenarios"][0]["expected_owners"] = ["@B"]
        errors = self.errors_for(data)
        self.assertTrue(any("expected_status must match" in item for item in errors))
        self.assertTrue(any("expected_owners must exactly match" in item for item in errors))

    def test_specialist_source_and_alias_are_canonical(self) -> None:
        data = copy.deepcopy(self.data)
        data["specialists"][0]["alias"] = "@WRONG"
        errors = self.errors_for(data)
        self.assertTrue(any("Specialist aliases must exactly" in item for item in errors))

    def test_specialist_ids_sources_and_wrappers_are_unique(self) -> None:
        data = copy.deepcopy(self.data)
        data["specialists"][1]["id"] = data["specialists"][0]["id"]
        data["specialists"][1]["source"] = data["specialists"][0]["source"]
        data["specialists"][1]["wrapper"] = data["specialists"][0]["wrapper"]
        errors = self.errors_for(data)
        self.assertTrue(any("duplicate id" in item for item in errors))
        self.assertTrue(any("duplicate source" in item for item in errors))
        self.assertTrue(any("duplicate wrapper" in item for item in errors))

    def test_json_cli_is_machine_readable(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("validate_project_coverage.py")), "--json"],
            cwd=KIT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(13, payload["profiles"])
        self.assertEqual(4, payload["specialists"])
        self.assertEqual(13, payload["profile_scenarios"])


if __name__ == "__main__":
    unittest.main()
