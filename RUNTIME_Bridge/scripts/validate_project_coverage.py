#!/usr/bin/env python3
"""Validate the project-profile coverage contract using only stdlib."""

from __future__ import annotations

import argparse
import json
import re
import stat
import sys
import tomllib
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


STATUSES = {"OBSERVADO", "PARCIAL", "AUSENTE"}
REQUIRED_PROFILES = {
    "WEB_FRONTEND",
    "MARKETING_LANDING",
    "API_BACKEND",
    "WORKER_AUTOMATION",
    "MOBILE",
    "DESKTOP",
    "MONOREPO",
    "CLI_SDK_PACKAGE",
    "DATA_ENGINEERING",
    "ML_ENGINEERING",
    "INFRASTRUCTURE_AS_CODE",
    "AI_LLM",
    "EMBEDDED",
    "GAME",
}
REQUIRED_SPECIALISTS = {
    "@PKG": "PKG_PackageSDK/PKG_Agent_PackageCLISDK.md",
    "@DE": "DE_DataEngineering/DE_Agent_DataPipeline.md",
    "@ML": "ML_MLEngineering/ML_Agent_MLEngineering.md",
    "@MKT": "MKT_Marketing/MKT_Agent_SEOGrowthStrategist.md",
    "@IAC": "IAC_PlatformEngineering/IAC_Agent_InfrastructureAsCode.md",
}
REQUIRED_NEGATIVE_SCENARIOS = {
    "CLI_NOT_PLAYWRIGHT": "CLI_SDK_PACKAGE",
    "GITLAB_NOT_GITHUB_ACTIONS": "INFRASTRUCTURE_AS_CODE",
    "ML_NOT_AI": "ML_ENGINEERING",
    "ETL_NOT_DATA": "DATA_ENGINEERING",
}
FULL_SOURCE_INSTRUCTION = (
    "Before acting, read the selected source file completely; "
    "do not rely on this wrapper as a substitute."
)
ID_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
ALIAS_RE = re.compile(r"^@[A-Z][A-Z0-9]*(?::[A-Za-z0-9_-]+)?$")


def _kit_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return path.is_symlink()
    return path.is_symlink() or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _safe_file(kit: Path, raw: str, label: str, errors: list[str]) -> Path | None:
    value = raw.strip().replace("\\", "/")
    win = PureWindowsPath(value)
    if (
        not value
        or "\x00" in value
        or PurePosixPath(value).is_absolute()
        or win.is_absolute()
        or bool(win.drive)
        or any(part in {"..", ""} for part in PurePosixPath(value).parts)
    ):
        errors.append(f"{label}: unsafe relative path {raw!r}.")
        return None
    candidate = kit.joinpath(*PurePosixPath(value).parts)
    root = kit.resolve(strict=True)
    try:
        candidate.resolve(strict=False).relative_to(root)
    except ValueError:
        errors.append(f"{label}: path escapes kit root: {raw!r}.")
        return None
    current = kit
    for part in PurePosixPath(value).parts:
        current /= part
        if _is_reparse(current):
            errors.append(f"{label}: symlink/reparse paths are forbidden: {raw!r}.")
            return None
    if not candidate.is_file():
        errors.append(f"{label}: file does not exist: {raw!r}.")
        return None
    return candidate


def load_document(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8-sig"))


def _string_list(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{label}: expected a list of non-empty strings.")
        return []
    return [item.strip() for item in value]


def _runtime_agents(kit: Path, errors: list[str]) -> dict[str, dict[str, str]]:
    path = kit / "RUNTIME_Bridge" / "AGENT_RUNTIME_MAP.toml"
    try:
        data = load_document(path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Runtime map cannot be read: {exc}")
        return {}
    catalog: dict[str, dict[str, str]] = {}
    for entry in data.get("agents", []):
        if not isinstance(entry, dict):
            continue
        alias = str(entry.get("alias", "")).strip()
        name = str(entry.get("name", "")).strip()
        source = str(entry.get("source", "")).strip().replace("\\", "/")
        if not alias or not name or not source:
            continue
        record = {
            "name": name,
            "source": source,
            "wrapper": f".codex/agents/{name}.toml",
        }
        catalog[alias] = record
        if ":" in alias:
            catalog.setdefault(alias.split(":", 1)[0], record)
    return catalog


def validate_data(kit: Path, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    coverage = data.get("coverage")
    if not isinstance(coverage, dict):
        return ["Missing [coverage] table."]
    if coverage.get("schema_version") != 1:
        errors.append("coverage.schema_version must be 1.")
    if set(_string_list(coverage.get("status_values"), "coverage.status_values", errors)) != STATUSES:
        errors.append("coverage.status_values must exactly declare OBSERVADO/PARCIAL/AUSENTE.")
    if coverage.get("fallback_alias") != "@F":
        errors.append("coverage.fallback_alias must be @F.")
    if coverage.get("ci_provider_policy") != "DETECT":
        errors.append("coverage.ci_provider_policy must be DETECT; no CI vendor is universal.")
    if coverage.get("never_claim_total_coverage") is not True:
        errors.append("coverage.never_claim_total_coverage must be true.")

    runtime_agents = _runtime_agents(kit, errors)
    runtime_aliases = set(runtime_agents)
    specialists = data.get("specialists")
    if not isinstance(specialists, list):
        specialists = []
        errors.append("[[specialists]] entries are required.")
    specialist_ids: set[str] = set()
    specialist_aliases: set[str] = set()
    specialist_sources: set[str] = set()
    specialist_wrappers: set[str] = set()
    for index, entry in enumerate(specialists, 1):
        label = f"specialists[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label}: expected table.")
            continue
        sid = str(entry.get("id", "")).strip()
        alias = str(entry.get("alias", "")).strip()
        source_raw = str(entry.get("source", "")).strip()
        wrapper_raw = str(entry.get("wrapper", "")).strip()
        if not ID_RE.fullmatch(sid):
            errors.append(f"{label}: invalid id {sid!r}.")
        if sid in specialist_ids:
            errors.append(f"{label}: duplicate id {sid}.")
        specialist_ids.add(sid)
        if not ALIAS_RE.fullmatch(alias):
            errors.append(f"{label}: invalid alias {alias!r}.")
        if alias in specialist_aliases:
            errors.append(f"{label}: duplicate alias {alias}.")
        specialist_aliases.add(alias)
        if source_raw in specialist_sources:
            errors.append(f"{label}: duplicate source {source_raw!r}.")
        specialist_sources.add(source_raw)
        if wrapper_raw in specialist_wrappers:
            errors.append(f"{label}: duplicate wrapper {wrapper_raw!r}.")
        specialist_wrappers.add(wrapper_raw)
        source = _safe_file(kit, source_raw, f"{label}.source", errors)
        wrapper = _safe_file(kit, wrapper_raw, f"{label}.wrapper", errors)
        _string_list(entry.get("excludes"), f"{label}.excludes", errors)
        if not str(entry.get("scope", "")).strip():
            errors.append(f"{label}.scope is required.")
        if source is not None:
            text = source.read_text(encoding="utf-8-sig")
            if alias not in text:
                errors.append(f"{label}.source does not declare alias {alias}.")
        if wrapper is not None:
            try:
                wrapper_data = tomllib.loads(wrapper.read_text(encoding="utf-8-sig"))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{label}.wrapper invalid TOML: {exc}")
                wrapper_data = {}
            instructions = str(wrapper_data.get("developer_instructions", ""))
            if wrapper_data.get("name") != wrapper.stem:
                errors.append(f"{label}.wrapper name must match filename {wrapper.stem!r}.")
            if FULL_SOURCE_INSTRUCTION not in instructions:
                errors.append(f"{label}.wrapper does not require complete source reading.")
            if source_raw not in instructions or f".codex/{source_raw}" not in instructions:
                errors.append(f"{label}.wrapper does not reference both source topologies.")
            if alias not in instructions:
                errors.append(f"{label}.wrapper does not declare alias {alias}.")

    if specialist_aliases != set(REQUIRED_SPECIALISTS):
        errors.append(
            "Specialist aliases must exactly match the canonical specialist set; "
            f"found {sorted(specialist_aliases)}."
        )
    for alias, source in REQUIRED_SPECIALISTS.items():
        matching = [entry for entry in specialists if isinstance(entry, dict) and entry.get("alias") == alias]
        if matching and matching[0].get("source") != source:
            errors.append(f"{alias} must use canonical source {source}.")

    known_aliases = runtime_aliases | specialist_aliases | {"@F"}
    profiles = data.get("profiles")
    if not isinstance(profiles, list):
        profiles = []
        errors.append("[[profiles]] entries are required.")
    by_id: dict[str, dict[str, Any]] = {}
    profile_scenario_ids: dict[str, str] = {}
    validated_owner_runtime: set[str] = set()
    for index, entry in enumerate(profiles, 1):
        label = f"profiles[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label}: expected table.")
            continue
        pid = str(entry.get("id", "")).strip()
        status = str(entry.get("status", "")).strip()
        if not ID_RE.fullmatch(pid):
            errors.append(f"{label}: invalid id {pid!r}.")
        if pid in by_id:
            errors.append(f"{label}: duplicate id {pid}.")
        by_id[pid] = entry
        if status not in STATUSES:
            errors.append(f"{label}: invalid status {status!r}.")
        owners = _string_list(entry.get("owners"), f"{label}.owners", errors)
        gates = _string_list(entry.get("gates"), f"{label}.gates", errors)
        tests = _string_list(entry.get("tests"), f"{label}.tests", errors)
        release = _string_list(entry.get("release"), f"{label}.release", errors)
        limitations = _string_list(entry.get("limitations"), f"{label}.limitations", errors)
        fallback = _string_list(entry.get("fallback"), f"{label}.fallback", errors)
        evidence = _string_list(entry.get("evidence"), f"{label}.evidence", errors)
        scenario = str(entry.get("scenario", "")).strip()
        if not str(entry.get("label", "")).strip():
            errors.append(f"{label}.label is required.")
        if status == "OBSERVADO" and not owners:
            errors.append(f"{label}: OBSERVADO requires at least one owner.")
        if status == "AUSENTE" and owners:
            errors.append(f"{label}: AUSENTE cannot declare a direct owner.")
        if status in {"PARCIAL", "AUSENTE"} and "@F" not in fallback:
            errors.append(f"{label}: {status} requires fallback @F.")
        if status == "OBSERVADO" and fallback:
            errors.append(f"{label}: OBSERVADO must not pretend a mandatory fallback.")
        if not gates or not tests or not release or not limitations or not evidence:
            errors.append(f"{label}: gates/tests/release/limitations/evidence must be non-empty.")
        if not scenario:
            errors.append(f"{label}.scenario is required.")
        elif scenario in profile_scenario_ids:
            errors.append(
                f"{label}: scenario {scenario!r} is already assigned to "
                f"{profile_scenario_ids[scenario]}."
            )
        else:
            profile_scenario_ids[scenario] = pid
        for alias in owners + gates + fallback:
            if not ALIAS_RE.fullmatch(alias) or alias not in known_aliases:
                errors.append(f"{label}: unknown alias {alias!r}.")
        for ev_index, raw in enumerate(evidence, 1):
            _safe_file(kit, raw, f"{label}.evidence[{ev_index}]", errors)
        evidence_set = {item.replace("\\", "/") for item in evidence}
        for owner in owners:
            runtime_owner = runtime_agents.get(owner)
            if runtime_owner is None:
                continue
            if runtime_owner["source"] not in evidence_set:
                errors.append(
                    f"{label}: evidence must include canonical source "
                    f"{runtime_owner['source']!r} for owner {owner}."
                )
            if owner not in validated_owner_runtime:
                source_path = _safe_file(
                    kit,
                    runtime_owner["source"],
                    f"{label}.owner-source[{owner}]",
                    errors,
                )
                wrapper_path = _safe_file(
                    kit,
                    runtime_owner["wrapper"],
                    f"{label}.owner-wrapper[{owner}]",
                    errors,
                )
                if source_path is not None and wrapper_path is not None:
                    try:
                        wrapper_data = tomllib.loads(wrapper_path.read_text(encoding="utf-8-sig"))
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"{label}: owner wrapper {owner} is invalid TOML: {exc}")
                    else:
                        instructions = str(wrapper_data.get("developer_instructions", ""))
                        source = runtime_owner["source"]
                        if (
                            wrapper_data.get("name") != runtime_owner["name"]
                            or owner not in instructions
                            or source not in instructions
                            or f".codex/{source}" not in instructions
                            or FULL_SOURCE_INSTRUCTION not in instructions
                        ):
                            errors.append(
                                f"{label}: owner wrapper {owner} is not a complete canonical route to {source}."
                            )
                validated_owner_runtime.add(owner)

    found_profiles = set(by_id)
    if found_profiles != REQUIRED_PROFILES:
        missing = sorted(REQUIRED_PROFILES - found_profiles)
        extra = sorted(found_profiles - REQUIRED_PROFILES)
        if missing:
            errors.append(f"Missing canonical profiles: {missing}.")
        if extra:
            errors.append(f"Unsupported profiles: {extra}.")

    profile_scenarios = data.get("profile_scenarios")
    if not isinstance(profile_scenarios, list):
        profile_scenarios = []
        errors.append("[[profile_scenarios]] entries are required.")
    scenarios_by_id: dict[str, dict[str, Any]] = {}
    scenario_profiles: set[str] = set()
    for index, entry in enumerate(profile_scenarios, 1):
        label = f"profile_scenarios[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label}: expected table.")
            continue
        scenario_id = str(entry.get("id", "")).strip()
        profile_id = str(entry.get("profile", "")).strip()
        if not ID_RE.fullmatch(scenario_id):
            errors.append(f"{label}: invalid id {scenario_id!r}.")
        if scenario_id in scenarios_by_id:
            errors.append(f"{label}: duplicate id {scenario_id!r}.")
        scenarios_by_id[scenario_id] = entry
        scenario_profiles.add(profile_id)
        profile = by_id.get(profile_id)
        if profile is None:
            errors.append(f"{label}: unknown profile {profile_id!r}.")
            continue
        if profile.get("scenario") != scenario_id:
            errors.append(f"{label}: profile {profile_id} must reference scenario {scenario_id}.")
        if entry.get("expected_status") != profile.get("status"):
            errors.append(f"{label}: expected_status must match {profile_id} status.")
        expected_owners = _string_list(entry.get("expected_owners"), f"{label}.expected_owners", errors)
        if expected_owners != profile.get("owners"):
            errors.append(f"{label}: expected_owners must exactly match {profile_id} owners.")
        for field_name in ("fixture", "expected_route", "expected_limit"):
            if len(str(entry.get(field_name, "")).strip()) < 16:
                errors.append(f"{label}.{field_name} must be concrete.")
    if scenario_profiles != REQUIRED_PROFILES:
        errors.append("Profile scenarios must cover every canonical profile exactly once.")
    if set(profile_scenario_ids) != set(scenarios_by_id):
        errors.append("Every profile scenario reference must resolve exactly once.")

    scenarios = data.get("negative_scenarios")
    if not isinstance(scenarios, list):
        scenarios = []
        errors.append("[[negative_scenarios]] entries are required.")
    scenario_map: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(scenarios, 1):
        if not isinstance(entry, dict):
            errors.append(f"negative_scenarios[{index}]: expected table.")
            continue
        sid = str(entry.get("id", "")).strip()
        if sid in scenario_map:
            errors.append(f"negative_scenarios[{index}]: duplicate id {sid}.")
        scenario_map[sid] = entry
        if not str(entry.get("rule", "")).strip():
            errors.append(f"negative_scenarios[{index}].rule is required.")
    if set(scenario_map) != set(REQUIRED_NEGATIVE_SCENARIOS):
        errors.append("Negative scenarios must exactly cover CLI, CI vendor, ML and ETL separation.")
    for sid, profile in REQUIRED_NEGATIVE_SCENARIOS.items():
        if sid in scenario_map and scenario_map[sid].get("profile") != profile:
            errors.append(f"Negative scenario {sid} must target {profile}.")

    cli = by_id.get("CLI_SDK_PACKAGE", {})
    if "@PKG" not in cli.get("owners", []) or any(
        "playwright" in str(item).lower() for item in cli.get("tests", [])
    ):
        errors.append("CLI_NOT_PLAYWRIGHT failed: CLI must use @PKG and no Playwright gate.")
    ml = by_id.get("ML_ENGINEERING", {})
    if "@ML" not in ml.get("owners", []) or "@AI" in ml.get("owners", []):
        errors.append("ML_NOT_AI failed: classical ML must be owned by @ML, not @AI.")
    data_profile = by_id.get("DATA_ENGINEERING", {})
    if "@DE" not in data_profile.get("owners", []) or "@DATA" in data_profile.get("owners", []):
        errors.append("ETL_NOT_DATA failed: ETL must be owned by @DE, not @DATA.")

    operations = kit / "O_Observability" / "O_Agent_DeployObservability.md"
    if operations.is_file():
        operations_text = operations.read_text(encoding="utf-8-sig")
        if "GitLab CI" not in operations_text or "detect" not in operations_text.lower():
            errors.append("GITLAB_NOT_GITHUB_ACTIONS failed: @O must detect CI and name GitLab CI.")
        for forbidden in (
            "Voce constroi a pipeline no GitHub Actions",
            "## Pipeline GitHub Actions",
            "Nenhuma release passa o gate sem GitHub Actions verde",
        ):
            if forbidden in operations_text:
                errors.append(f"GITLAB_NOT_GITHUB_ACTIONS failed: unconditional vendor rule remains: {forbidden!r}.")
    else:
        errors.append("GITLAB_NOT_GITHUB_ACTIONS failed: @O source is missing.")
    return errors


def validate(kit: Path, coverage_path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        data = load_document(coverage_path)
    except Exception as exc:  # noqa: BLE001
        return {}, [f"Invalid coverage TOML: {exc}"]
    return data, validate_data(kit, data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit-root", type=Path, default=_kit_root())
    parser.add_argument("--map", dest="map_path", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    kit = args.kit_root.resolve()
    coverage_path = args.map_path or kit / "RUNTIME_Bridge" / "PROJECT_COVERAGE_MAP.toml"
    data, errors = validate(kit, coverage_path)
    result = {
        "ok": not errors,
        "kit_root": str(kit),
        "coverage_map": str(coverage_path),
        "profiles": len(data.get("profiles", [])) if isinstance(data, dict) else 0,
        "specialists": len(data.get("specialists", [])) if isinstance(data, dict) else 0,
        "profile_scenarios": len(data.get("profile_scenarios", [])) if isinstance(data, dict) else 0,
        "errors": errors,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Project profile coverage validation")
        print(f"Kit root: {kit}")
        print(f"Profiles: {result['profiles']}")
        print(f"Specialists: {result['specialists']}")
        print(f"Profile scenarios: {result['profile_scenarios']}")
        if errors:
            print("\nFAILED")
            for error in errors:
                print(f"- {error}")
        else:
            print("\nOK: profile schema, specialists, evidence, fallbacks and negative scenarios are coherent.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
