#!/usr/bin/env python3
"""Validate repository skill scenarios and observed forward-test results.

Manifest validation proves case coverage and contract integrity. Execution is
only considered proven when a complete results TOML is supplied and every
record satisfies invocation, output, evidence, and validator expectations.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
KIT_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_MANIFEST = KIT_ROOT / "RUNTIME_Bridge" / "evals" / "skills" / "cases.toml"
RUNTIME_MAP = KIT_ROOT / "RUNTIME_Bridge" / "AGENT_RUNTIME_MAP.toml"

KINDS = {"trigger", "boundary", "negative"}
INVOCATION_BY_KIND = {
    "trigger": "REQUIRED",
    "boundary": "CONDITIONAL",
    "negative": "FORBIDDEN",
}
CONTRACTS = {
    "AGENT_CHANGE",
    "ARCHITECTURE_PACKAGE",
    "HARNESS_REPORT",
    "KIT_OPERATION",
    "MULTI_AGENT_PLAN",
    "ROUTE_DECISION",
    "SPEC_PACKAGE",
}
CASE_ID = re.compile(r"^[A-Z]+-(TRG|BND|NEG)-\d{3}$")
PLACEHOLDER = re.compile(r"(?:\bTODO\b|\bTBD\b|\[.+?\]|<.+?>)", re.IGNORECASE)
EVIDENCE_TOKEN = re.compile(r"^[a-z][a-z0-9-]*:[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    case_id: str | None = None


@dataclass
class EvalReport:
    manifest: str
    results: str | None = None
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    cases: dict[str, dict[str, Any]] = field(default_factory=dict)
    coverage: dict[str, dict[str, int]] = field(default_factory=dict)
    execution_proven: bool = False

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, code: str, message: str, case_id: str | None = None) -> None:
        self.errors.append(Issue(code, message, case_id))

    def warning(self, code: str, message: str, case_id: str | None = None) -> None:
        self.warnings.append(Issue(code, message, case_id))

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "kind": "skill-contract-evals",
            "manifest": self.manifest,
            "results": self.results,
            "execution_proven": self.execution_proven,
            "summary": {
                "cases": len(self.cases),
                "skills": len(self.coverage),
                "errors": len(self.errors),
                "warnings": len(self.warnings),
            },
            "coverage": self.coverage,
            "errors": [asdict(issue) for issue in self.errors],
            "warnings": [asdict(issue) for issue in self.warnings],
        }


def _load_toml(path: Path, report: EvalReport, label: str) -> dict[str, Any] | None:
    try:
        with path.open("rb") as stream:
            value = tomllib.load(stream)
    except OSError as exc:
        report.error(f"missing-{label}", f"Cannot read {label} {path}: {exc}")
        return None
    except tomllib.TOMLDecodeError as exc:
        report.error(f"invalid-{label}-toml", f"Cannot parse {label} {path}: {exc}")
        return None
    if not isinstance(value, dict):
        report.error(f"invalid-{label}", f"{label} must be a TOML table.")
        return None
    return value


def _strings(value: Any) -> list[str] | None:
    if not isinstance(value, list) or not value:
        return None
    if any(not isinstance(item, str) or not item.strip() for item in value):
        return None
    return [item.strip() for item in value]


def _concrete(value: Any, minimum: int = 12) -> bool:
    return isinstance(value, str) and len(value.strip()) >= minimum and not PLACEHOLDER.search(value)


def _safe_validator(path_text: str, report: EvalReport, case_id: str) -> None:
    if path_text.startswith("N/A - "):
        if len(path_text.removeprefix("N/A - ").strip()) < 16:
            report.error("unjustified-validator-na", "Validator N/A needs a concrete reason.", case_id)
        return
    relative = Path(path_text)
    if relative.is_absolute() or ".." in relative.parts:
        report.error("unsafe-validator-path", f"Validator path is unsafe: {path_text}", case_id)
        return
    target = KIT_ROOT.joinpath(relative)
    try:
        target.resolve().relative_to(KIT_ROOT.resolve())
    except (OSError, ValueError):
        report.error("unsafe-validator-path", f"Validator escapes KIT_ROOT: {path_text}", case_id)
        return
    if not target.is_file():
        report.error("missing-validator", f"Validator does not exist: {path_text}", case_id)


def _canonical_skills(report: EvalReport) -> set[str]:
    data = _load_toml(RUNTIME_MAP, report, "runtime-manifest")
    if data is None:
        return set()
    entries = data.get("skills")
    if not isinstance(entries, list) or not entries:
        report.error("missing-runtime-skills", "Runtime manifest needs [[skills]] entries.")
        return set()
    skills: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            report.error("invalid-runtime-skill", "Runtime skill entry must be a table.")
            continue
        name = str(entry.get("name", "")).strip()
        path = str(entry.get("path", "")).replace("\\", "/").strip()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            report.error("invalid-runtime-skill", f"Invalid runtime skill name: {name!r}.")
            continue
        if name in skills:
            report.error("duplicate-runtime-skill", f"Duplicate runtime skill: {name}.")
            continue
        expected = f"skills/{name}/SKILL.md"
        if path != expected:
            report.error(
                "invalid-runtime-skill-path",
                f"Runtime skill {name} must use {expected!r}.",
            )
            continue
        skills.add(name)
    return skills


def _validate_case(raw: Any, report: EvalReport, skills: set[str]) -> None:
    if not isinstance(raw, dict):
        report.error("invalid-case", "Every [[cases]] entry must be a table.")
        return
    case_id = str(raw.get("id", "")).strip()
    if not CASE_ID.fullmatch(case_id):
        report.error("invalid-case-id", f"Invalid case id: {case_id!r}", case_id or None)
        return
    if case_id in report.cases:
        report.error("duplicate-case-id", f"Duplicate case id: {case_id}", case_id)
        return

    skill = str(raw.get("skill", "")).strip()
    kind = str(raw.get("kind", "")).strip()
    invocation = str(raw.get("expected_invocation", "")).strip()
    contract = str(raw.get("expected_contract", "")).strip()
    if skill not in skills:
        report.error("unknown-skill", f"Unknown skill: {skill!r}", case_id)
    if kind not in KINDS:
        report.error("invalid-case-kind", f"Invalid case kind: {kind!r}", case_id)
    elif invocation != INVOCATION_BY_KIND[kind]:
        report.error(
            "invocation-kind-mismatch",
            f"{kind} requires {INVOCATION_BY_KIND[kind]}, got {invocation!r}.",
            case_id,
        )
    if contract not in CONTRACTS:
        report.error("invalid-output-contract", f"Unknown output contract: {contract!r}", case_id)
    for field_name in ("prompt", "fixture"):
        if not _concrete(raw.get(field_name), 24):
            report.error("incomplete-case", f"{field_name} must be concrete.", case_id)

    outputs = _strings(raw.get("expected_outputs"))
    evidence = _strings(raw.get("evidence_required"))
    validators = _strings(raw.get("validators"))
    if outputs is None:
        report.error("missing-expected-outputs", "expected_outputs must be non-empty.", case_id)
    if evidence is None:
        report.error("missing-evidence-contract", "evidence_required must be non-empty.", case_id)
    else:
        if len(evidence) != len(set(evidence)) or any(not EVIDENCE_TOKEN.fullmatch(item) for item in evidence):
            report.error(
                "invalid-evidence-contract",
                "Evidence tokens must be unique lowercase category:value pairs.",
                case_id,
            )
    if validators is None:
        report.error("missing-validator-contract", "validators must be non-empty.", case_id)
    else:
        for validator in validators:
            _safe_validator(validator, report, case_id)

    report.cases[case_id] = raw


def _validate_manifest(
    data: dict[str, Any], report: EvalReport, skills: set[str]
) -> None:
    if data.get("schema_version") != 1:
        report.error("unsupported-schema", "schema_version must be 1.")
    required = _strings(data.get("required_skills"))
    if required is None or set(required) != skills or len(required) != len(skills):
        report.error("invalid-required-skills", "required_skills must list each canonical skill exactly once.")
    for skill in sorted(skills):
        source = KIT_ROOT / "skills" / skill / "SKILL.md"
        ui = KIT_ROOT / "skills" / skill / "agents" / "openai.yaml"
        if not source.is_file():
            report.error("missing-skill-source", f"Missing canonical source for {skill}: {source}.")
        else:
            text = source.read_text(encoding="utf-8-sig")
            frontmatter = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
            if frontmatter is None or not re.search(
                rf"^name:\s*{re.escape(skill)}\s*$", frontmatter.group(1), re.MULTILINE
            ):
                report.error("skill-name-mismatch", f"Canonical SKILL.md name differs for {skill}.")
            if frontmatter is None or not re.search(r"^description:\s*\S.+$", frontmatter.group(1), re.MULTILINE):
                report.error("missing-skill-description", f"Canonical SKILL.md lacks description for {skill}.")
        if not ui.is_file():
            report.error("missing-skill-ui", f"Missing agents/openai.yaml for {skill}.")
        elif f"${skill}" not in ui.read_text(encoding="utf-8-sig"):
            report.error("skill-ui-prompt-mismatch", f"UI prompt does not mention ${skill}.")

    coverage_contract = data.get("coverage")
    expected_coverage = {
        "minimum_total_per_skill": 4,
        "minimum_trigger_per_skill": 2,
        "minimum_boundary_per_skill": 1,
        "minimum_negative_per_skill": 1,
    }
    if not isinstance(coverage_contract, dict):
        report.error("missing-coverage-contract", "[coverage] is required.")
    else:
        for key, minimum in expected_coverage.items():
            if coverage_contract.get(key) != minimum:
                report.error("invalid-coverage-contract", f"{key} must equal {minimum}.")

    cases = data.get("cases")
    if not isinstance(cases, list):
        report.error("missing-cases", "At least one [[cases]] entry is required.")
        return
    prompts: dict[str, str] = {}
    for raw in cases:
        _validate_case(raw, report, skills)
        if isinstance(raw, dict):
            case_id = str(raw.get("id", "")).strip()
            prompt = re.sub(r"\s+", " ", str(raw.get("prompt", "")).strip().casefold())
            if prompt and prompt in prompts:
                report.error("duplicate-prompt", f"Prompt duplicates {prompts[prompt]}.", case_id or None)
            elif prompt:
                prompts[prompt] = case_id

    report.coverage = {
        skill: {"total": 0, "trigger": 0, "boundary": 0, "negative": 0}
        for skill in sorted(skills)
    }
    for case in report.cases.values():
        skill = str(case.get("skill", ""))
        kind = str(case.get("kind", ""))
        if skill in report.coverage and kind in KINDS:
            report.coverage[skill]["total"] += 1
            report.coverage[skill][kind] += 1
    for skill, counts in report.coverage.items():
        if counts["total"] < 4 or counts["trigger"] < 2 or counts["boundary"] < 1 or counts["negative"] < 1:
            report.error("insufficient-skill-coverage", f"{skill} coverage is insufficient: {counts}.")


def _valid_timestamp(value: Any) -> bool:
    if isinstance(value, (dt.datetime, dt.date)):
        return True
    if not isinstance(value, str):
        return False
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _validator_paths(case: dict[str, Any]) -> set[str]:
    return {
        value
        for value in case.get("validators", [])
        if isinstance(value, str) and not value.startswith("N/A - ")
    }


def _validate_results(
    data: dict[str, Any], report: EvalReport, skills: set[str]
) -> None:
    if not _concrete(data.get("run_id")):
        report.error("invalid-run-metadata", "results run_id must be concrete.")
    if not _concrete(data.get("executor")):
        report.error("invalid-run-metadata", "results executor must be concrete.")
    if not _valid_timestamp(data.get("executed_at")):
        report.error("invalid-run-metadata", "results executed_at must be ISO-8601.")
    results = data.get("results")
    if not isinstance(results, list):
        report.error("missing-results", "Results TOML needs [[results]] entries.")
        return

    seen: set[str] = set()
    for raw in results:
        if not isinstance(raw, dict):
            report.error("invalid-result", "Every [[results]] entry must be a table.")
            continue
        case_id = str(raw.get("case_id", "")).strip()
        if case_id in seen:
            report.error("duplicate-result", f"Duplicate result for {case_id}.", case_id or None)
            continue
        seen.add(case_id)
        case = report.cases.get(case_id)
        if case is None:
            report.error("unknown-result-case", f"Unknown result case: {case_id!r}", case_id or None)
            continue
        invoked = _strings(raw.get("invoked_skills")) or []
        unknown = set(invoked) - skills
        if unknown or len(invoked) != len(set(invoked)):
            report.error("invalid-invoked-skills", f"Unknown or duplicate invoked skills: {sorted(unknown)}.", case_id)
        decision = str(raw.get("decision", "")).strip()
        if decision not in {"INVOKED", "SKIPPED"}:
            report.error("invalid-result-decision", "decision must be INVOKED or SKIPPED.", case_id)
        expected = str(case["expected_invocation"])
        target_skill = str(case["skill"])
        if expected == "REQUIRED" and (target_skill not in invoked or decision != "INVOKED"):
            report.error("required-skill-not-invoked", f"{target_skill} was required.", case_id)
        if expected == "FORBIDDEN" and (target_skill in invoked or decision != "SKIPPED"):
            report.error("forbidden-skill-invoked", f"{target_skill} was forbidden.", case_id)
        if expected == "CONDITIONAL":
            consistent = (decision == "INVOKED" and target_skill in invoked) or (
                decision == "SKIPPED" and target_skill not in invoked
            )
            if not consistent:
                report.error("conditional-decision-mismatch", "Conditional invocation and decision disagree.", case_id)
        if not _concrete(raw.get("reason")):
            report.error("missing-result-reason", "Observed invocation decision needs a concrete reason.", case_id)
        if raw.get("outcome") != "PASS":
            report.error("failed-forward-test", "Observed case outcome must be PASS.", case_id)
        if raw.get("output_contract") != case.get("expected_contract"):
            report.error("output-contract-mismatch", "Observed output contract differs from the case.", case_id)
        observed_evidence = _strings(raw.get("evidence")) or []
        missing_evidence = set(case.get("evidence_required", [])) - set(observed_evidence)
        if missing_evidence:
            report.error("missing-observed-evidence", f"Missing evidence: {sorted(missing_evidence)}.", case_id)

        validator_results = raw.get("validator_results", [])
        observed_validators: dict[str, int] = {}
        if not isinstance(validator_results, list):
            report.error("invalid-validator-results", "validator_results must be an array of tables.", case_id)
        else:
            for item in validator_results:
                if not isinstance(item, dict):
                    report.error("invalid-validator-results", "validator result must be a table.", case_id)
                    continue
                path = str(item.get("path", "")).strip()
                code = item.get("exit_code")
                if path in observed_validators:
                    report.error("duplicate-validator-result", f"Duplicate validator result: {path}.", case_id)
                elif not isinstance(code, int):
                    report.error("invalid-validator-exit", f"Validator {path!r} lacks integer exit_code.", case_id)
                else:
                    observed_validators[path] = code
        required_validators = _validator_paths(case)
        missing_validators = required_validators - set(observed_validators)
        if missing_validators:
            report.error("missing-validator-result", f"Missing validator results: {sorted(missing_validators)}.", case_id)
        for path in required_validators & set(observed_validators):
            if observed_validators[path] != 0:
                report.error("validator-failed", f"Validator {path} exited {observed_validators[path]}.", case_id)

    missing = set(report.cases) - seen
    if missing:
        report.error("incomplete-forward-test-run", f"Missing results for cases: {sorted(missing)}.")


def evaluate(manifest: Path = DEFAULT_MANIFEST, results: Path | None = None) -> EvalReport:
    report = EvalReport(str(manifest), str(results) if results else None)
    skills = _canonical_skills(report)
    data = _load_toml(manifest, report, "manifest")
    if data is not None:
        _validate_manifest(data, report, skills)
    if results is None:
        report.warning(
            "execution-not-proven",
            "Manifest contracts passed, but no forward-test results were supplied.",
        )
    elif data is not None:
        result_data = _load_toml(results, report, "results")
        if result_data is not None:
            _validate_results(result_data, report, skills)
            report.execution_proven = not report.errors
    return report


def _print_human(report: EvalReport) -> None:
    print(f"Skill contract manifest: {'OK' if report.ok else 'FAIL'}")
    print(f"Cases: {len(report.cases)} | skills: {len(report.coverage)}")
    print(f"Forward-test execution proven: {'yes' if report.execution_proven else 'no'}")
    for skill, counts in sorted(report.coverage.items()):
        print(
            f"- {skill}: total={counts['total']} trigger={counts['trigger']} "
            f"boundary={counts['boundary']} negative={counts['negative']}"
        )
    for issue in report.errors:
        marker = f" [{issue.case_id}]" if issue.case_id else ""
        print(f"ERROR {issue.code}{marker}: {issue.message}")
    for issue in report.warnings:
        marker = f" [{issue.case_id}]" if issue.case_id else ""
        print(f"WARN {issue.code}{marker}: {issue.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--results", type=Path, help="observed forward-test results TOML")
    parser.add_argument("--require-results", action="store_true", help="fail unless execution is proven")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    report = evaluate(args.manifest, args.results)
    if args.require_results and not report.execution_proven:
        report.error("execution-required", "A complete passing results file is required.")
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_human(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
