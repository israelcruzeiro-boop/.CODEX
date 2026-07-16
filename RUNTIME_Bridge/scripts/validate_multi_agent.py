#!/usr/bin/env python3
"""Validate a multi-agent delivery plan, task envelopes, and result envelopes."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath

from validate_arsenal import _mask_nonsemantic_markdown


TASK_ID_RE = re.compile(r"^AGT-\d{3}(?:-R\d+)?$")
CLAIM_ID_RE = re.compile(r"^CLM-(AGT-\d{3}(?:-R\d+)?)-\d{3}$")
CANONICAL_VERDICTS = {
    "APROVADO",
    "APROVADO_COM_RESSALVAS",
    "QUESTIONAR",
    "REPROVADO",
}
TASK_STATUSES = {
    "PENDING",
    "RUNNING",
    "COMPLETE",
    "PARTIAL",
    "BLOCKED",
    "TIMEOUT",
    "INTERRUPTED",
    "FAILED",
    "CONFLICT",
}
RESULT_STATUSES = TASK_STATUSES - {"PENDING", "RUNNING"}
OPERATIONAL_STATUSES = {"COMPLETE", "COMPLETE_COM_RESSALVAS", "INCOMPLETE"}
CLAIM_STATUSES = {"NAO_AVALIADO", "CONFIRMADO", "PARCIAL", "REFUTADO"}
PLACEHOLDERS = {
    "",
    "-",
    "...",
    "todo",
    "tbd",
    "pendente",
    "[task_id]",
    "[entrega]",
    "read/write",
    "sim/nao",
}


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }
        if self.line is not None:
            data["line"] = self.line
        return data


@dataclass
class ValidationResult:
    plan: Path
    phase: str
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    tasks: int = 0
    results: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, code: str, path: Path, message: str, line: int | None = None) -> None:
        self.errors.append(Issue(code, str(path), message, line))

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "phase": self.phase,
            "plan": str(self.plan),
            "tasks": self.tasks,
            "results": self.results,
            "errors": [issue.to_dict() for issue in self.errors],
            "warnings": [issue.to_dict() for issue in self.warnings],
        }


@dataclass(frozen=True)
class Table:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    line: int


@dataclass
class PlanTask:
    task_id: str
    objective: str
    dependencies: frozenset[str]
    group: str
    agent: str
    mode: str
    reads: frozenset[str]
    writes: frozenset[str]
    isolation: str
    timeout: str
    retry_of: str
    evidence: str
    join: str
    status: str
    line: int


@dataclass
class Envelope:
    task_id: str
    path: Path
    metadata: dict[str, str]
    claims: dict[str, tuple[str, str, int]] = field(default_factory=dict)


@dataclass(frozen=True)
class LedgerClaim:
    claim: str
    source: str
    agent: str
    status: str
    decision: str
    line: int


def _plain(value: str) -> str:
    return re.sub(r"[`*]", "", value).strip()


def _concrete(value: str, *, allow_na: bool = False) -> bool:
    clean = _plain(value)
    folded = clean.casefold()
    if folded in PLACEHOLDERS or clean.startswith("[") and clean.endswith("]"):
        return False
    if "|" in clean and all(not part.strip() for part in clean.split("|")):
        return False
    if re.match(r"^(?:n/a|na|none|nenhum|nenhuma)(?:$|\s|[-:])", folded):
        return allow_na and bool(re.search(r"(?:porque|pois|:|-).+", clean, re.I))
    return True


def _metadata(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for match in re.finditer(r"(?m)^\s{0,3}\*\*([^*\r\n]+):\*\*\s*(.*?)\s*$", text):
        result[_plain(match.group(1)).casefold()] = match.group(2).strip()
    return result


def _duplicate_metadata_labels(text: str) -> set[str]:
    labels = [
        _plain(match.group(1)).casefold()
        for match in re.finditer(r"(?m)^\s{0,3}\*\*([^*\r\n]+):\*\*\s*(.*?)\s*$", text)
    ]
    return {label for label in labels if labels.count(label) > 1}


def _cells(line: str) -> tuple[str, ...]:
    content = line.strip()
    if content.startswith("|"):
        content = content[1:]
    if content.endswith("|") and not content.endswith(r"\|"):
        content = content[:-1]

    cells: list[str] = []
    current: list[str] = []
    index = 0
    while index < len(content):
        char = content[index]
        if char == "\\" and index + 1 < len(content) and content[index + 1] == "|":
            current.append("|")
            index += 2
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        index += 1
    cells.append("".join(current).strip())
    return tuple(cells)


def _tables(text: str) -> list[Table]:
    lines = text.splitlines()
    found: list[Table] = []
    index = 0
    while index + 1 < len(lines):
        if "|" not in lines[index] or "|" not in lines[index + 1]:
            index += 1
            continue
        headers = _cells(lines[index])
        separator = _cells(lines[index + 1])
        if len(headers) < 2 or len(headers) != len(separator) or not all(
            re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in separator
        ):
            index += 1
            continue
        rows: list[tuple[str, ...]] = []
        cursor = index + 2
        while cursor < len(lines) and "|" in lines[cursor]:
            row = _cells(lines[cursor])
            if len(row) != len(headers):
                break
            rows.append(row)
            cursor += 1
        found.append(Table(headers, tuple(rows), index + 1))
        index = cursor
    return found


def _column(table: Table, *tokens: str) -> int | None:
    normalized = [_plain(value).casefold() for value in table.headers]
    for token in tokens:
        folded = token.casefold()
        for index, header in enumerate(normalized):
            if folded == header:
                return index
    for token in tokens:
        folded = token.casefold()
        for index, header in enumerate(normalized):
            if folded in header:
                return index
    return None


def _find_table(text: str, *tokens: str) -> Table | None:
    folded = tuple(token.casefold() for token in tokens)
    for table in _tables(text):
        headers = " ".join(_plain(value).casefold() for value in table.headers)
        if all(token in headers for token in folded):
            return table
    return None


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"(?ims)^\s{{0,3}}#{{2,6}}\s+{re.escape(heading)}\s*$\n(.*?)(?=^\s{{0,3}}#{{1,6}}\s|\Z)",
        text,
    )
    return match.group(1).strip() if match else ""


def _heading_task_id(text: str, kind: str) -> str:
    match = re.search(rf"(?im)^\s{{0,3}}#\s+{kind}\s+-\s+({TASK_ID_RE.pattern[1:-1]})\s*$", text)
    return match.group(1) if match else ""


def _split_values(value: str) -> list[str]:
    value = re.sub(r"<br\s*/?>", ",", value, flags=re.I)
    return [item.strip() for item in re.split(r"[,;\n]+", value) if item.strip()]


def _path_set(value: str) -> frozenset[str]:
    result: set[str] = set()
    for raw in _split_values(value):
        clean = raw.strip().strip("`").replace("\\", "/").strip().rstrip("/")
        if clean.casefold().startswith(("n/a", "none", "nenhum", "nenhuma")):
            continue
        result.add(clean.casefold())
    return frozenset(result)


def _valid_scoped_path(value: str) -> bool:
    if not value or "\x00" in value:
        return False
    if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
        return False
    parts = PurePosixPath(value).parts
    return not any(part in {"", ".", ".."} or ":" in part for part in parts)


def _static_prefix(pattern: str) -> str:
    match = re.search(r"[*?[{]", pattern)
    return pattern[: match.start()] if match else pattern


def _paths_overlap(left: str, right: str) -> bool:
    left = left.casefold().rstrip("/")
    right = right.casefold().rstrip("/")
    if left == right:
        return True
    if not any(char in left for char in "*?[{") and not any(char in right for char in "*?[{"):
        return left.startswith(right + "/") or right.startswith(left + "/")
    if fnmatch.fnmatchcase(left, right) or fnmatch.fnmatchcase(right, left):
        return True
    left_prefix = _static_prefix(left).rstrip("/")
    right_prefix = _static_prefix(right).rstrip("/")
    return not left_prefix or not right_prefix or left_prefix.startswith(right_prefix) or right_prefix.startswith(left_prefix)


def _sets_overlap(left: frozenset[str], right: frozenset[str]) -> set[tuple[str, str]]:
    return {(a, b) for a in left for b in right if _paths_overlap(a, b)}


def _dependencies(value: str) -> frozenset[str]:
    return frozenset(re.findall(r"AGT-\d{3}(?:-R\d+)?", value))


def _isolation_id(value: str, kind: str) -> str | None:
    match = re.search(rf"\b{kind}\s*[:=]\s*([a-zA-Z0-9_.-]+)", value, re.I)
    return match.group(1).casefold() if match else None


def _path_authorized(actual: str, planned: frozenset[str]) -> bool:
    if any(char in actual for char in "*?[{"):
        return actual in planned
    return any(
        actual == allowed
        or actual.startswith(allowed.rstrip("/") + "/")
        or fnmatch.fnmatchcase(actual, allowed)
        for allowed in planned
    )


def _read_semantic(path: Path, result: ValidationResult) -> str:
    try:
        if path.is_symlink() or not path.is_file():
            raise OSError("not a regular file")
        raw = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        result.error("unreadable-artifact", path, f"Cannot read artifact: {exc}.")
        return ""
    return _mask_nonsemantic_markdown(raw)


def _parse_plan(result: ValidationResult, text: str) -> tuple[dict[str, PlanTask], dict[str, str], dict[str, LedgerClaim]]:
    meta = _metadata(text)
    for label in sorted(_duplicate_metadata_labels(text)):
        result.error("duplicate-plan-control", result.plan, f"Plan metadata label {label!r} is duplicated.")
    required = (
        "objetivo",
        "agente raiz/integrador",
        "risco",
        "limite de threads observado",
        "profundidade permitida",
        "versao das fontes (branch + commit + hash do diff/working tree)",
        "politica de timeout/retry",
        "challenge pass",
        "status operacional da dag",
    )
    for field_name in required:
        if not _concrete(meta.get(field_name, ""), allow_na=field_name == "challenge pass"):
            result.error("missing-plan-control", result.plan, f"Plan control {field_name!r} is missing or placeholder.")
    if _plain(meta.get("risco", "")).upper() not in {"BAIXO", "MEDIO", "ALTO", "CRITICO"}:
        result.error("invalid-risk", result.plan, "Risk must be BAIXO, MEDIO, ALTO, or CRITICO.")
    if not re.fullmatch(r"\d+", _plain(meta.get("limite de threads observado", ""))) or _plain(meta.get("limite de threads observado", "")) == "0":
        result.error("invalid-thread-limit", result.plan, "Observed thread limit must be a positive integer.")
    if not re.fullmatch(r"\d+", _plain(meta.get("profundidade permitida", ""))):
        result.error("invalid-depth", result.plan, "Allowed depth must be a non-negative integer.")

    table = _find_table(text, "task id", "read-set", "write-set", "isolation", "timeout", "evid")
    tasks: dict[str, PlanTask] = {}
    if table is None:
        result.error("missing-dag", result.plan, "DAG table with isolation, timeout, and evidence columns is required.")
        return tasks, meta, {}
    columns = {
        "id": _column(table, "Task ID"),
        "objective": _column(table, "Objetivo"),
        "depends": _column(table, "Depende de"),
        "group": _column(table, "Grupo paralelo"),
        "agent": _column(table, "Agente"),
        "mode": _column(table, "Modo"),
        "reads": _column(table, "Read-set"),
        "writes": _column(table, "Write-set"),
        "isolation": _column(table, "Isolation", "Isolamento"),
        "timeout": _column(table, "Timeout"),
        "retry": _column(table, "Retry de"),
        "evidence": _column(table, "Evidencia/saida", "Evidência/saída"),
        "join": _column(table, "Join/aceite"),
        "status": _column(table, "Status"),
    }
    if any(value is None for value in columns.values()):
        result.error("invalid-dag-columns", result.plan, "DAG table is missing a required P1 column.", table.line)
        return tasks, meta, {}
    for offset, row in enumerate(table.rows, table.line + 2):
        task_id = _plain(row[columns["id"]])  # type: ignore[index]
        if not TASK_ID_RE.fullmatch(task_id):
            result.error("invalid-task-id", result.plan, f"Invalid task ID {task_id!r}.", offset)
            continue
        if task_id in tasks:
            result.error("duplicate-task-id", result.plan, f"Duplicate task ID {task_id}.", offset)
            continue
        values = {key: row[index] for key, index in columns.items() if index is not None}
        mode = _plain(values["mode"]).upper()
        status = _plain(values["status"]).upper()
        reads = _path_set(values["reads"])
        writes = _path_set(values["writes"])
        if mode not in {"READ", "WRITE"}:
            result.error("invalid-task-mode", result.plan, f"{task_id} has invalid mode {mode!r}.", offset)
        for field_name in ("objective", "group", "agent", "timeout", "evidence", "join"):
            if not _concrete(values[field_name]):
                result.error("missing-task-contract", result.plan, f"{task_id} has placeholder {field_name}.", offset)
        if not re.search(r"\d", values["timeout"]):
            result.error("invalid-timeout", result.plan, f"{task_id} timeout must be explicit.", offset)
        if not reads:
            result.error("empty-read-set", result.plan, f"{task_id} must declare a concrete read-set.", offset)
        if mode == "WRITE" and not writes:
            result.error("empty-write-set", result.plan, f"WRITE task {task_id} must declare a write-set.", offset)
        if mode == "READ" and writes:
            result.error("read-task-writes", result.plan, f"READ task {task_id} cannot declare writes.", offset)
        for scoped_path in reads | writes:
            if not _valid_scoped_path(scoped_path):
                result.error("unsafe-file-set", result.plan, f"{task_id} has unsafe project-relative path/pattern {scoped_path!r}.", offset)
        if status not in TASK_STATUSES:
            result.error("invalid-task-status", result.plan, f"{task_id} has invalid status {status!r}.", offset)
        tasks[task_id] = PlanTask(
            task_id,
            values["objective"],
            _dependencies(values["depends"]),
            values["group"],
            values["agent"],
            mode,
            reads,
            writes,
            values["isolation"],
            values["timeout"],
            _plain(values["retry"]),
            values["evidence"],
            values["join"],
            status,
            offset,
        )

    max_retries_match = re.search(r"(?:maximo|máximo|max)\D*(\d+)", meta.get("politica de timeout/retry", ""), re.I)
    max_retries = int(max_retries_match.group(1)) if max_retries_match else None
    for task in tasks.values():
        unknown = sorted(task.dependencies - tasks.keys())
        if unknown:
            result.error("unknown-dependency", result.plan, f"{task.task_id} depends on unknown tasks {unknown}.", task.line)
        retry_match = re.fullmatch(r"AGT-(\d{3})-R(\d+)", task.task_id)
        if retry_match:
            expected_base = f"AGT-{retry_match.group(1)}"
            if task.retry_of != expected_base or expected_base not in tasks:
                result.error("invalid-retry", result.plan, f"{task.task_id} must retry existing {expected_base}.", task.line)
            if expected_base not in task.dependencies:
                result.error("retry-without-dependency", result.plan, f"{task.task_id} must depend on {expected_base}.", task.line)
            if max_retries is not None and int(retry_match.group(2)) > max_retries:
                result.error("retry-limit", result.plan, f"{task.task_id} exceeds retry limit {max_retries}.", task.line)
        elif task.retry_of and not task.retry_of.casefold().startswith("n/a"):
            result.error("unexpected-retry", result.plan, f"Base task {task.task_id} cannot declare Retry de {task.retry_of!r}.", task.line)

    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(task_id: str) -> None:
        state[task_id] = 1
        stack.append(task_id)
        for dependency in tasks[task_id].dependencies:
            if dependency not in tasks:
                continue
            if state.get(dependency, 0) == 0:
                visit(dependency)
            elif state.get(dependency) == 1:
                cycle = stack[stack.index(dependency):] + [dependency]
                result.error("dag-cycle", result.plan, f"Dependency cycle: {' -> '.join(cycle)}.", tasks[task_id].line)
        stack.pop()
        state[task_id] = 2

    for task_id in tasks:
        if state.get(task_id, 0) == 0:
            visit(task_id)

    def depends_on(source: str, target: str, seen: set[str] | None = None) -> bool:
        seen = set() if seen is None else seen
        if source in seen or source not in tasks:
            return False
        seen.add(source)
        return target in tasks[source].dependencies or any(depends_on(dep, target, seen) for dep in tasks[source].dependencies)

    task_ids = sorted(tasks)
    for index, left_id in enumerate(task_ids):
        left = tasks[left_id]
        for right_id in task_ids[index + 1:]:
            right = tasks[right_id]
            if depends_on(left_id, right_id) or depends_on(right_id, left_id):
                continue
            write_write = _sets_overlap(left.writes, right.writes)
            left_write_right_read = _sets_overlap(left.writes, right.reads)
            right_write_left_read = _sets_overlap(right.writes, left.reads)
            if not (write_write or left_write_right_read or right_write_left_read):
                continue
            left_worktree = _isolation_id(left.isolation, "worktree")
            right_worktree = _isolation_id(right.isolation, "worktree")
            if left_worktree and right_worktree and left_worktree != right_worktree:
                continue
            right_snapshot = _isolation_id(right.isolation, "snapshot")
            left_snapshot = _isolation_id(left.isolation, "snapshot")
            unsafe = set(write_write)
            if not right_snapshot:
                unsafe |= left_write_right_read
            if not left_snapshot:
                unsafe |= right_write_left_read
            if unsafe:
                result.error("concurrent-file-set-conflict", result.plan, f"{left_id} and {right_id} overlap without structural isolation: {sorted(unsafe)}.")

    ledger: dict[str, LedgerClaim] = {}
    ledger_table = _find_table(text, "claim id", "fonte primaria", "decisao do integrador")
    if ledger_table:
        claim_col = _column(ledger_table, "Claim ID")
        claim_text_col = _column(ledger_table, "Claim")
        agent_col = _column(ledger_table, "Agente")
        status_col = _column(ledger_table, "Status")
        decision_col = _column(ledger_table, "Decisao do integrador")
        conflict_col = _column(ledger_table, "Conflito")
        source_col = _column(ledger_table, "Fonte primaria")
        if None not in {claim_col, claim_text_col, agent_col, status_col, decision_col, conflict_col, source_col}:
            for line, row in enumerate(ledger_table.rows, ledger_table.line + 2):
                claim = _plain(row[claim_col])  # type: ignore[index]
                if not CLAIM_ID_RE.fullmatch(claim):
                    result.error("invalid-ledger-claim", result.plan, f"Invalid ledger claim {claim!r}.", line)
                    continue
                if claim in ledger:
                    result.error("duplicate-claim", result.plan, f"Duplicate ledger claim {claim}.", line)
                    continue
                status = _plain(row[status_col]).upper()  # type: ignore[index]
                if status not in CLAIM_STATUSES:
                    result.error("invalid-claim-status", result.plan, f"Claim {claim} has invalid status {status!r}.", line)
                ledger[claim] = LedgerClaim(
                    row[claim_text_col],  # type: ignore[index]
                    row[source_col],  # type: ignore[index]
                    row[agent_col],  # type: ignore[index]
                    status,
                    row[decision_col],  # type: ignore[index]
                    line,
                )
                namespace = CLAIM_ID_RE.fullmatch(claim)
                if namespace and _plain(row[agent_col]) != namespace.group(1):  # type: ignore[index]
                    result.error("ledger-agent-mismatch", result.plan, f"Claim {claim} must be attributed to {namespace.group(1)}.", line)
                conflict = row[conflict_col]  # type: ignore[index]
                if _concrete(conflict, allow_na=False) and not _concrete(meta.get("challenge pass", ""), allow_na=False):
                    result.error("missing-challenge-pass", result.plan, f"Ledger conflict for {claim} requires a concrete challenge pass.", line)
                if result.phase in {"fan-in", "complete"} and (
                    status == "NAO_AVALIADO"
                    or not _concrete(row[claim_text_col])  # type: ignore[index]
                    or not _concrete(row[source_col])  # type: ignore[index]
                    or not _concrete(row[decision_col])  # type: ignore[index]
                ):
                    result.error("unresolved-ledger-claim", result.plan, f"Claim {claim} is unresolved in {result.phase} phase.", line)
    elif result.phase in {"fan-in", "complete"}:
        result.error("missing-evidence-ledger", result.plan, "Evidence ledger is required for fan-in and complete phases.")
    return tasks, meta, ledger


def _envelopes(directory: Path | None, kind: str, result: ValidationResult) -> dict[str, Envelope]:
    envelopes: dict[str, Envelope] = {}
    if directory is None:
        return envelopes
    try:
        if directory.is_symlink() or not directory.is_dir():
            raise OSError("not a regular directory")
        paths = sorted(directory.glob("*.md"))
    except OSError as exc:
        result.error("unreadable-envelope-directory", directory, f"Cannot read {kind} directory: {exc}.")
        return envelopes
    for path in paths:
        text = _read_semantic(path, result)
        task_id = _heading_task_id(text, "AGENT TASK" if kind == "task" else "AGENT RESULT")
        if not task_id:
            result.error("missing-envelope-id", path, f"{kind.title()} heading must contain a valid task ID.")
            continue
        if task_id in envelopes:
            result.error("duplicate-envelope", path, f"Duplicate {kind} envelope for {task_id}.")
            continue
        for label in sorted(_duplicate_metadata_labels(text)):
            result.error("duplicate-envelope-field", path, f"{kind.title()} metadata label {label!r} is duplicated.")
        envelope = Envelope(task_id, path, _metadata(text))
        if kind == "result":
            table = _find_table(text, "claim id", "fato", "evidencia primaria")
            if table:
                claim_col = _column(table, "Claim ID")
                fact_col = _column(table, "Fato")
                evidence_col = _column(table, "Evidencia primaria")
                if None not in {claim_col, fact_col, evidence_col}:
                    for line, row in enumerate(table.rows, table.line + 2):
                        claim = _plain(row[claim_col])  # type: ignore[index]
                        if claim in envelope.claims:
                            result.error("duplicate-result-claim", path, f"Duplicate result claim {claim}.", line)
                        envelope.claims[claim] = (row[fact_col], row[evidence_col], line)  # type: ignore[index]
        envelopes[task_id] = envelope
    return envelopes


def _validate_task_envelopes(result: ValidationResult, plan_meta: dict[str, str], tasks: dict[str, PlanTask], envelopes: dict[str, Envelope], *, required: bool) -> None:
    if required:
        for extra in sorted(envelopes.keys() - tasks.keys()):
            result.error("unknown-task-envelope", envelopes[extra].path, f"Task envelope {extra} is absent from the plan.")
        for missing in sorted(tasks.keys() - envelopes.keys()):
            result.error("missing-task-envelope", result.plan, f"Plan task {missing} has no task envelope.")
    for task_id, envelope in envelopes.items():
        if task_id not in tasks:
            continue
        task = tasks[task_id]
        meta = envelope.metadata
        comparisons = {
            "grupo paralelo": task.group,
            "agente/papel": task.agent,
            "modo": task.mode,
            "read-set": ",".join(sorted(task.reads)),
            "write-set exclusivo": ",".join(sorted(task.writes)),
            "isolation": task.isolation,
            "timeout": task.timeout,
            "retry de": task.retry_of,
            "versao das fontes (branch + commit + hash do diff/working tree)": plan_meta.get("versao das fontes (branch + commit + hash do diff/working tree)", ""),
        }
        for label, expected in comparisons.items():
            actual = meta.get(label, "")
            if label in {"read-set", "write-set exclusivo"}:
                if _path_set(actual) != _path_set(expected):
                    result.error("task-plan-drift", envelope.path, f"{task_id} {label} differs from plan.")
            elif _plain(actual).casefold() != _plain(expected).casefold():
                result.error("task-plan-drift", envelope.path, f"{task_id} {label} differs from plan.")
        if _dependencies(meta.get("depende de", "")) != task.dependencies:
            result.error("task-plan-drift", envelope.path, f"{task_id} dependencies differ from plan.")
        for label in ("objetivo", "fora de escopo", "criterio de conclusao", "evidencia esperada/formato", "destino do handoff"):
            if not _concrete(meta.get(label, "")):
                result.error("incomplete-task-envelope", envelope.path, f"{task_id} has missing {label}.")


def _normalized_claim_value(value: str) -> str:
    return " ".join(_plain(value).split()).casefold()


def _validate_result_envelopes(result: ValidationResult, plan_meta: dict[str, str], tasks: dict[str, PlanTask], envelopes: dict[str, Envelope], ledger: dict[str, LedgerClaim]) -> None:
    for extra in sorted(envelopes.keys() - tasks.keys()):
        result.error("unknown-result-envelope", envelopes[extra].path, f"Result {extra} is absent from the plan.")
    if result.phase in {"fan-in", "complete"}:
        for missing in sorted(tasks.keys() - envelopes.keys()):
            result.error("missing-result-envelope", result.plan, f"{result.phase} phase requires result for {missing}.")
    all_claims: dict[str, tuple[str, str, str]] = {}
    source_fingerprint = plan_meta.get("versao das fontes (branch + commit + hash do diff/working tree)", "")
    challenge_needed = False
    for task_id, envelope in envelopes.items():
        if task_id not in tasks:
            continue
        task = tasks[task_id]
        meta = envelope.metadata
        status = _plain(meta.get("status", "")).upper()
        if status not in RESULT_STATUSES:
            result.error("invalid-result-status", envelope.path, f"{task_id} result has invalid status {status!r}.")
        if task.status != status:
            result.error("result-status-drift", envelope.path, f"{task_id} plan status {task.status} differs from result {status}.")
        if _plain(meta.get("agente/papel", "")).casefold() != _plain(task.agent).casefold():
            result.error("result-agent-drift", envelope.path, f"{task_id} result agent differs from plan.")
        if _plain(meta.get("modo executado", "")).upper() != task.mode:
            result.error("result-mode-drift", envelope.path, f"{task_id} result mode differs from plan.")
        if _plain(meta.get("retry de", "")).casefold() != _plain(task.retry_of).casefold():
            result.error("result-retry-drift", envelope.path, f"{task_id} result retry origin differs from plan.")
        actual_reads = _path_set(meta.get("read-set efetivamente usado", ""))
        actual_writes = _path_set(meta.get("write-set alterado", ""))
        if not _concrete(meta.get("read-set efetivamente usado", ""), allow_na=True):
            result.error("missing-actual-read-set", envelope.path, f"{task_id} must report the effective read-set or justified N/A.")
        if task.mode == "WRITE" and status == "COMPLETE" and not actual_writes:
            result.error("missing-actual-write-set", envelope.path, f"COMPLETE WRITE task {task_id} must report at least one changed path.")
        unauthorized_reads = sorted(path for path in actual_reads if not _path_authorized(path, task.reads))
        unauthorized_writes = sorted(path for path in actual_writes if not _path_authorized(path, task.writes))
        if unauthorized_reads:
            result.error("unauthorized-read-set", envelope.path, f"{task_id} read outside authorized plan: {unauthorized_reads}.")
        if unauthorized_writes:
            result.error("unauthorized-write-set", envelope.path, f"{task_id} wrote outside authorized plan: {unauthorized_writes}.")
        if task.mode == "READ" and actual_writes:
            result.error("read-result-writes", envelope.path, f"READ task {task_id} reported writes.")
        if _plain(meta.get("isolation usada", "")).casefold() != _plain(task.isolation).casefold():
            result.error("result-isolation-drift", envelope.path, f"{task_id} result isolation differs from plan.")
        start = meta.get("fingerprint lido no inicio", "")
        end = meta.get("fingerprint confirmado no fim", "")
        if _plain(start).casefold() != _plain(source_fingerprint).casefold():
            result.error("stale-start-fingerprint", envelope.path, f"{task_id} did not start from the plan fingerprint.")
        if not _concrete(end):
            result.error("missing-end-fingerprint", envelope.path, f"{task_id} has no final fingerprint.")
        if task.mode == "READ" and not _isolation_id(task.isolation, "snapshot") and not _isolation_id(task.isolation, "worktree") and _plain(end).casefold() != _plain(start).casefold():
            result.error("mutable-read-fingerprint", envelope.path, f"READ task {task_id} observed changing sources without isolation.")
        join = _plain(meta.get("join condition atendida", "")).upper()
        if join not in {"SIM", "NAO"}:
            result.error("invalid-result-join", envelope.path, f"{task_id} must declare whether join was met.")
        if status in {"FAILED", "BLOCKED", "TIMEOUT", "INTERRUPTED", "CONFLICT"} and join == "SIM":
            result.error("failed-result-joined", envelope.path, f"{task_id} cannot satisfy join with status {status}.")
        if result.phase == "complete" and join != "SIM":
            result.error("unsatisfied-result-join", envelope.path, f"Complete phase requires satisfied join for {task_id}.")
        if _plain(meta.get("precisa de challenge pass", "")).upper() == "SIM" or status == "CONFLICT":
            challenge_needed = True
        if not envelope.claims:
            result.error("missing-result-claims", envelope.path, f"{task_id} result has no factual claim.")
        for claim, (fact, evidence, line) in envelope.claims.items():
            match = CLAIM_ID_RE.fullmatch(claim)
            if not match or match.group(1) != task_id:
                result.error("invalid-claim-namespace", envelope.path, f"Claim {claim!r} does not belong to {task_id}.", line)
            if claim in all_claims:
                result.error("duplicate-global-claim", envelope.path, f"Claim {claim} also appears in {all_claims[claim][2]}.", line)
                continue
            all_claims[claim] = (fact, evidence, str(envelope.path))
            if not _concrete(fact) or not _concrete(evidence):
                result.error("claim-without-evidence", envelope.path, f"Claim {claim} lacks fact or primary evidence.", line)
    if result.phase in {"fan-in", "complete"}:
        for claim in sorted(set(all_claims) - set(ledger)):
            result.error("claim-missing-from-ledger", result.plan, f"Result claim {claim} is absent from evidence ledger.")
        for claim in sorted(set(ledger) - set(all_claims)):
            result.error("ledger-claim-without-result", result.plan, f"Ledger claim {claim} has no result source.")
        for claim in sorted(set(all_claims) & set(ledger)):
            fact, evidence, source_path = all_claims[claim]
            recorded = ledger[claim]
            if _normalized_claim_value(fact) != _normalized_claim_value(recorded.claim):
                result.error(
                    "ledger-claim-content-mismatch",
                    result.plan,
                    f"Ledger claim {claim} differs from result {source_path}.",
                    recorded.line,
                )
            if _normalized_claim_value(evidence) != _normalized_claim_value(recorded.source):
                result.error(
                    "ledger-claim-source-mismatch",
                    result.plan,
                    f"Ledger source for {claim} differs from result {source_path}.",
                    recorded.line,
                )
    if challenge_needed and not _concrete(plan_meta.get("challenge pass", ""), allow_na=False):
        result.error("missing-challenge-pass", result.plan, "A conflict/result requires a concrete challenge pass owner, timeout, and tie-break rule.")


def validate_multi_agent(plan: str | Path, *, tasks_dir: str | Path | None = None, results_dir: str | Path | None = None, phase: str = "plan") -> ValidationResult:
    plan_path = Path(plan).expanduser().absolute()
    result = ValidationResult(plan_path, phase)
    if phase not in {"plan", "fan-in", "complete"}:
        result.error("invalid-phase", plan_path, f"Unsupported phase {phase!r}.")
        return result
    text = _read_semantic(plan_path, result)
    tasks, meta, ledger = _parse_plan(result, text)
    result.tasks = len(tasks)
    if tasks_dir is None:
        result.error("missing-tasks-dir", plan_path, "Task envelopes directory is required in every phase.")
    if phase in {"fan-in", "complete"} and results_dir is None:
        result.error("missing-results-dir", plan_path, f"Results directory is required in {phase} phase.")
    task_envelopes = _envelopes(Path(tasks_dir).expanduser().absolute() if tasks_dir else None, "task", result)
    result_envelopes = _envelopes(Path(results_dir).expanduser().absolute() if results_dir else None, "result", result)
    result.results = len(result_envelopes)
    _validate_task_envelopes(result, meta, tasks, task_envelopes, required=tasks_dir is not None)
    _validate_result_envelopes(result, meta, tasks, result_envelopes, ledger)

    operational = _plain(meta.get("status operacional da dag", "")).upper()
    verdict = _plain(meta.get("veredito global", "")).upper()
    if operational and operational not in OPERATIONAL_STATUSES:
        result.error("invalid-operational-status", plan_path, f"Invalid operational DAG status {operational!r}.")
    if phase == "complete":
        if operational not in {"COMPLETE", "COMPLETE_COM_RESSALVAS"}:
            result.error("incomplete-dag", plan_path, "Complete phase requires a complete operational DAG status.")
        if verdict not in CANONICAL_VERDICTS:
            result.error("invalid-global-verdict", plan_path, "Complete phase requires one canonical global verdict.")
        if not _concrete(meta.get("prova pos-fan-in", "")):
            result.error("missing-post-fan-in-proof", plan_path, "Complete phase requires post-fan-in integration evidence.")
        reservations = meta.get("ressalvas finais", "")
        if verdict == "APROVADO_COM_RESSALVAS" and not _concrete(reservations):
            result.error("missing-final-reservation", plan_path, "Approval with reservations requires a concrete final reservation.")
        if verdict == "APROVADO" and any(task.status != "COMPLETE" for task in tasks.values()):
            result.error("approval-masks-task-gap", plan_path, "APROVADO cannot mask non-COMPLETE tasks.")
        if verdict == "APROVADO" and any(item.status != "CONFIRMADO" for item in ledger.values()):
            result.error("approval-masks-claim-gap", plan_path, "APROVADO requires every ledger claim to be CONFIRMADO.")
        if verdict in {"APROVADO", "APROVADO_COM_RESSALVAS"} and any(task.status in {"FAILED", "BLOCKED", "TIMEOUT", "INTERRUPTED", "CONFLICT"} for task in tasks.values()):
            result.error("approval-masks-task-failure", plan_path, f"{verdict} cannot mask blocking task status.")
    return result


def _print_human(result: ValidationResult) -> None:
    print(f"Multi-agent governance validation: {'OK' if result.ok else 'FAILED'}")
    print(f"Plan: {result.plan}")
    print(f"Phase: {result.phase}; tasks: {result.tasks}; results: {result.results}")
    for issue in result.errors:
        suffix = f":{issue.line}" if issue.line else ""
        print(f"ERROR [{issue.code}] {issue.path}{suffix}: {issue.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", help="multi-agent plan Markdown file")
    parser.add_argument("--tasks-dir", help="directory containing AGENT TASK envelopes")
    parser.add_argument("--results-dir", help="directory containing AGENT RESULT envelopes")
    parser.add_argument("--phase", choices=("plan", "fan-in", "complete"), default="plan")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    result = validate_multi_agent(args.plan, tasks_dir=args.tasks_dir, results_dir=args.results_dir, phase=args.phase)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_human(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
