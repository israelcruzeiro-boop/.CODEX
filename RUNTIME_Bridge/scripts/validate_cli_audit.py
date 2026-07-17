#!/usr/bin/env python3
"""Validate a CLI Audit Harness Markdown artifact and its evidence semantics."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from validate_arsenal import _mask_nonsemantic_markdown
from validate_multi_agent import (
    Issue,
    Table,
    _column,
    _concrete,
    _duplicate_metadata_labels,
    _find_table,
    _metadata,
    _plain,
    _section,
)


RESULTS = {"PASS", "FAIL", "LACUNA", "SKIP_JUSTIFICADO"}
VERDICTS = {"APROVADO", "APROVADO_COM_RESSALVAS", "QUESTIONAR", "REPROVADO"}


@dataclass
class ValidationResult:
    path: Path
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    commands: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, code: str, message: str, line: int | None = None) -> None:
        self.errors.append(Issue(code, str(self.path), message, line))

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "path": str(self.path),
            "commands": self.commands,
            "errors": [issue.to_dict() for issue in self.errors],
            "warnings": [issue.to_dict() for issue in self.warnings],
        }


@dataclass(frozen=True)
class CommandEvidence:
    evidence: str
    command: str
    cwd: str
    objective: str
    exit_code: str
    status: str
    observation: str
    line: int


@dataclass(frozen=True)
class StructuredGap:
    gap_id: str
    description: str
    blocking: bool
    action: str
    owner: str
    deadline: str
    line: int


def _semantic_file(path: Path, result: ValidationResult) -> str:
    try:
        if path.is_symlink() or not path.is_file():
            raise OSError("not a regular file")
        return _mask_nonsemantic_markdown(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        result.error("unreadable-audit", f"Cannot read CLI audit: {exc}.")
        return ""


def _actual_bullets(section: str) -> list[str]:
    items = []
    for match in re.finditer(r"(?m)^\s{0,3}-\s+(.+?)\s*$", section):
        value = _plain(match.group(1))
        if value.casefold().startswith(("n/a", "nenhuma", "nenhum", "none")):
            continue
        if _concrete(value):
            items.append(value)
    return items


def _parse_commands(text: str, result: ValidationResult) -> dict[str, CommandEvidence]:
    table = _find_table(text, "evidencia", "comando", "cwd", "objetivo", "exit code", "resultado", "observacao")
    commands: dict[str, CommandEvidence] = {}
    if table is None:
        result.error("missing-command-table", "Commands table with P1 evidence columns is required.")
        return commands
    columns = {
        "evidence": _column(table, "Evidencia"),
        "command": _column(table, "Comando"),
        "cwd": _column(table, "CWD"),
        "objective": _column(table, "Objetivo"),
        "exit": _column(table, "Exit code"),
        "status": _column(table, "Resultado"),
        "observation": _column(table, "Observacao", "prova substituta"),
    }
    if any(index is None for index in columns.values()):
        result.error("invalid-command-columns", "Commands table lacks a required P1 column.", table.line)
        return commands
    for line, row in enumerate(table.rows, table.line + 2):
        values = {key: row[index] for key, index in columns.items() if index is not None}
        evidence = _plain(values["evidence"])
        if not re.fullmatch(r"EVD-\d{3}", evidence):
            result.error("invalid-evidence-id", f"Invalid command evidence ID {evidence!r}.", line)
            continue
        if evidence in commands:
            result.error("duplicate-evidence-id", f"Duplicate evidence ID {evidence}.", line)
            continue
        status = _plain(values["status"]).upper()
        if status not in RESULTS:
            result.error("invalid-command-status", f"{evidence} has invalid result {status!r}.", line)
        for field_name in ("command", "cwd", "objective"):
            if not _concrete(values[field_name]):
                result.error("incomplete-command-evidence", f"{evidence} has missing {field_name}.", line)
        exit_value = _plain(values["exit"])
        numeric_exit = int(exit_value) if re.fullmatch(r"-?\d+", exit_value) else None
        if status == "PASS" and numeric_exit != 0:
            result.error("pass-with-nonzero-exit", f"{evidence} is PASS but exit code is not 0.", line)
        if status == "FAIL" and (numeric_exit is None or numeric_exit == 0):
            result.error("fail-without-nonzero-exit", f"{evidence} is FAIL but lacks a nonzero exit code.", line)
        if status in {"LACUNA", "SKIP_JUSTIFICADO"}:
            if numeric_exit is not None or not _concrete(values["observation"]):
                result.error("unjustified-nonexecution", f"{evidence} {status} requires nonnumeric N/A exit and concrete justification/proof substitute.", line)
        elif not _concrete(values["observation"], allow_na=True):
            result.error("missing-command-observation", f"{evidence} requires a result summary.", line)
        commands[evidence] = CommandEvidence(
            evidence,
            values["command"],
            values["cwd"],
            values["objective"],
            exit_value,
            status,
            values["observation"],
            line,
        )
    result.commands = len(commands)
    if not commands:
        result.error("empty-command-table", "At least one concrete command evidence row is required.")
    return commands


def _validate_traceability(
    text: str,
    commands: dict[str, CommandEvidence],
    declared_requirements: set[str],
    result: ValidationResult,
) -> None:
    table = _find_table(text, "requisito", "modulo/contrato", "task", "teste/gate", "evidencia", "resultado")
    if table is None:
        result.error("missing-traceability", "Traceability table is required.")
        return
    evidence_col = _column(table, "Evidencia")
    outcome_col = _column(table, "Resultado")
    requirement_col = _column(table, "Requisito")
    module_col = _column(table, "Modulo/contrato")
    task_col = _column(table, "Task")
    test_col = _column(table, "Teste/gate")
    seen: set[str] = set()
    seen_requirements: set[str] = set()
    if None in {evidence_col, outcome_col, requirement_col, module_col, task_col, test_col}:
        result.error("invalid-traceability-columns", "Traceability table is incomplete.", table.line)
        return
    for line, row in enumerate(table.rows, table.line + 2):
        requirement = _plain(row[requirement_col])  # type: ignore[index]
        requirement_ids = set(re.findall(r"\b(?:REQ|AC|NFR)-\d{3}\b", requirement))
        seen_requirements.update(requirement_ids & declared_requirements)
        evidence_ids = set(re.findall(r"EVD-\d{3}", row[evidence_col]))  # type: ignore[index]
        outcome = _plain(row[outcome_col]).upper()  # type: ignore[index]
        if not requirement_ids:
            result.error("invalid-traceability-requirement", f"Traceability row lacks a requirement ID: {requirement!r}.", line)
        if not re.search(r"\b(?:MOD|CON|EVT)-\d{3}\b", row[module_col]):  # type: ignore[index]
            result.error("invalid-traceability-module", "Traceability row lacks MOD/CON/EVT linkage.", line)
        if not re.search(r"\bTASK-\d{3}\b", row[task_col]):  # type: ignore[index]
            result.error("invalid-traceability-task", "Traceability row lacks TASK linkage.", line)
        if not re.search(r"\b(?:TEST|FIT)-\d{3}\b", row[test_col]):  # type: ignore[index]
            result.error("invalid-traceability-test", "Traceability row lacks TEST/FIT linkage.", line)
        if not evidence_ids:
            result.error("traceability-without-evidence", "Traceability row has no EVD ID.", line)
        for evidence in evidence_ids:
            seen.add(evidence)
            if evidence not in commands:
                result.error("unknown-traceability-evidence", f"Traceability references unknown {evidence}.", line)
                continue
            status = commands[evidence].status
            compatible = {
                "PROVADO": {"PASS"},
                "FALHOU": {"FAIL"},
                "LACUNA": {"LACUNA"},
            }
            if outcome in compatible and status not in compatible[outcome]:
                result.error("traceability-result-mismatch", f"{evidence} status {status} cannot support {outcome}.", line)
            elif outcome.startswith("N/A"):
                if not re.search(r"(?:porque|pois|:|-).+", outcome, re.I):
                    result.error("unjustified-traceability-na", "Traceability N/A requires a reason.", line)
            elif outcome not in compatible:
                result.error("invalid-traceability-result", f"Invalid traceability result {outcome!r}.", line)
    for evidence, command in commands.items():
        if command.status in {"PASS", "FAIL", "LACUNA"} and evidence not in seen:
            result.error("unmapped-command-evidence", f"{evidence} is not mapped in traceability.", command.line)
    for missing in sorted(declared_requirements - seen_requirements):
        result.error("unmapped-declared-requirement", f"Declared context requirement {missing} is absent from traceability.")


def _parse_structured_gaps(text: str, result: ValidationResult) -> list[StructuredGap]:
    table = _find_table(text, "id", "lacuna", "bloqueante", "acao", "responsavel", "prazo/criterio")
    if table is None:
        return []
    columns = {
        "id": _column(table, "ID"),
        "description": _column(table, "Lacuna"),
        "blocking": _column(table, "Bloqueante?", "Bloqueante"),
        "action": _column(table, "Acao"),
        "owner": _column(table, "Responsavel"),
        "deadline": _column(table, "Prazo/criterio"),
    }
    if any(index is None for index in columns.values()):
        result.error("invalid-gap-columns", "Structured gaps table is incomplete.", table.line)
        return []
    gaps: list[StructuredGap] = []
    seen: set[str] = set()
    for line, row in enumerate(table.rows, table.line + 2):
        values = {key: row[index] for key, index in columns.items() if index is not None}
        gap_id = _plain(values["id"])
        if not re.fullmatch(r"GAP-\d{3}", gap_id):
            result.error("invalid-gap-id", f"Structured gap ID {gap_id!r} must use GAP-NNN.", line)
            continue
        if gap_id in seen:
            result.error("duplicate-gap-id", f"Structured gap {gap_id} is duplicated.", line)
            continue
        seen.add(gap_id)
        blocking_value = _plain(values["blocking"]).upper()
        if blocking_value not in {"SIM", "NAO"}:
            result.error("invalid-gap-blocking", f"{gap_id} Bloqueante? must be SIM or NAO.", line)
        for field_name in ("description", "action", "owner", "deadline"):
            if not _concrete(values[field_name]):
                result.error("incomplete-structured-gap", f"{gap_id} has missing {field_name}.", line)
        gaps.append(
            StructuredGap(
                gap_id,
                values["description"],
                blocking_value == "SIM",
                values["action"],
                values["owner"],
                values["deadline"],
                line,
            )
        )
    return gaps


def _justified_na(value: str) -> bool:
    return bool(re.match(r"^(?:n/a|na)(?:\s*[-:]\s*).+", _plain(value), re.I))


def _validate_cycle_close(meta: dict[str, str], result: ValidationResult) -> list[str]:
    general_key = "status geral atualizado em status.md"
    environments_key = "status por ambiente atualizado em status.md"
    detail_keys = (
        "ambientes sem validacao e motivo",
        "migrations do ciclo",
        "diretorio canonico de migrations confirmado",
        "lacunas de replicacao do banco",
    )
    for key in (general_key, environments_key):
        value = _plain(meta.get(key, ""))
        if value.upper() == "SIM" or _justified_na(value):
            continue
        result.error(
            "incomplete-cycle-close",
            f"Cycle close field {key!r} must be SIM or justified N/A.",
        )
    for key in detail_keys:
        value = meta.get(key, "")
        if not (_concrete(value) or _justified_na(value)):
            result.error("incomplete-cycle-close", f"Cycle close field {key!r} is missing or placeholder.")

    migrations = meta.get("migrations do ciclo", "")
    migration_directory = meta.get("diretorio canonico de migrations confirmado", "")
    if _concrete(migrations) and not _justified_na(migrations) and _justified_na(migration_directory):
        result.error("missing-canonical-migration-directory", "A cycle with migrations requires a concrete canonical migration directory.")

    cycle_gaps: list[str] = []
    unvalidated = meta.get("ambientes sem validacao e motivo", "")
    replication = meta.get("lacunas de replicacao do banco", "")
    if _concrete(unvalidated) and not _justified_na(unvalidated):
        cycle_gaps.append(unvalidated)
    if _concrete(replication) and not _justified_na(replication):
        cycle_gaps.append(replication)
    return cycle_gaps


def validate_cli_audit(path: str | Path) -> ValidationResult:
    audit_path = Path(path).expanduser().absolute()
    result = ValidationResult(audit_path)
    text = _semantic_file(audit_path, result)
    meta = _metadata(text)
    for label in sorted(_duplicate_metadata_labels(text)):
        result.error("duplicate-audit-field", f"Audit metadata label {label!r} is duplicated.")
    required_context = (
        "tarefa",
        "spec/tasks",
        "requisitos/nfrs",
        "modulos/contratos",
        "branch/commit",
        "diretorio raiz",
        "ambientes afetados",
        "arquivos alterados",
        "data",
    )
    for field_name in required_context:
        if not _concrete(meta.get(field_name, ""), allow_na=field_name in {"arquivos alterados", "ambientes afetados"}):
            result.error("missing-audit-context", f"Audit context {field_name!r} is missing or placeholder.")
    date_value = _plain(meta.get("data", ""))
    try:
        date.fromisoformat(date_value)
    except ValueError:
        result.error("invalid-audit-date", "Audit date must use ISO YYYY-MM-DD.")

    commands = _parse_commands(text, result)
    declared_requirements = set(re.findall(r"\b(?:REQ|NFR)-\d{3}\b", _plain(meta.get("requisitos/nfrs", ""))))
    _validate_traceability(text, commands, declared_requirements, result)
    structured_gaps = _parse_structured_gaps(text, result)
    cycle_gaps = _validate_cycle_close(meta, result)
    gaps = _actual_bullets(_section(text, "Lacunas")) + [gap.description for gap in structured_gaps] + cycle_gaps
    blocking_gaps = [gap for gap in structured_gaps if gap.blocking]
    failures = _actual_bullets(_section(text, "Falhas"))
    verdict_lines = re.findall(r"(?im)^\s{0,3}\*\*Veredito:\*\*\s*\S.*$", text)
    if len(verdict_lines) != 1:
        result.error("verdict-cardinality", "Audit must declare exactly one semantic verdict line.")
    verdict = _plain(meta.get("veredito", "")).upper()
    if verdict not in VERDICTS:
        result.error("invalid-audit-verdict", "Audit must declare exactly one canonical verdict.")
        return result
    if not _concrete(meta.get("justificativa", "")):
        result.error("missing-verdict-justification", "Verdict requires concrete justification.")
    statuses = {command.status for command in commands.values()}
    if "FAIL" in statuses or failures:
        if verdict != "REPROVADO":
            result.error("failure-masked-by-verdict", f"FAIL/explicit failure requires REPROVADO, not {verdict}.")
    if verdict == "APROVADO":
        if statuses & {"FAIL", "LACUNA"} or gaps or failures:
            result.error("approval-masks-gap", "APROVADO cannot contain FAIL, LACUNA, explicit gaps, or failures.")
    elif verdict == "APROVADO_COM_RESSALVAS":
        if "FAIL" in statuses or failures:
            result.error("reservation-masks-failure", "APROVADO_COM_RESSALVAS cannot mask a failure.")
        if blocking_gaps:
            result.error("reservation-masks-blocking-gap", "APROVADO_COM_RESSALVAS cannot mask a blocking structured gap.")
        if not (statuses & {"LACUNA", "SKIP_JUSTIFICADO"} or gaps):
            result.error("reservation-without-gap", "Approval with reservations requires a concrete nonblocking gap.")
        for field_name in ("ressalva", "acao da ressalva", "responsavel pela ressalva", "prazo/criterio da ressalva"):
            if not _concrete(meta.get(field_name, "")):
                result.error("incomplete-reservation", f"Reservation field {field_name!r} is required.")
    elif verdict == "QUESTIONAR":
        if "FAIL" in statuses or failures:
            result.error("questionar-masks-failure", "A proven failure requires REPROVADO.")
        if not ("LACUNA" in statuses or gaps):
            result.error("questionar-without-gap", "QUESTIONAR requires missing evidence/context.")
    elif verdict == "REPROVADO" and not ("FAIL" in statuses or failures or blocking_gaps):
        result.error("reprovado-without-failure", "REPROVADO requires FAIL, an explicit failure, or a structured blocking gap.")

    if verdict != "APROVADO" and not _concrete(meta.get("proximo passo", "")):
        result.error("missing-next-step", f"{verdict} requires a concrete next step.")
    return result


def _print_human(result: ValidationResult) -> None:
    print(f"CLI Audit Harness validation: {'OK' if result.ok else 'FAILED'}")
    print(f"Artifact: {result.path}; commands: {result.commands}")
    for issue in result.errors:
        suffix = f":{issue.line}" if issue.line else ""
        print(f"ERROR [{issue.code}] {issue.path}{suffix}: {issue.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="CLI Audit Harness Markdown file")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    result = validate_cli_audit(args.path)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_human(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
