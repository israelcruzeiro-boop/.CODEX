#!/usr/bin/env python3
"""Validate granular SDD change specs using only the Python standard library.

The validator checks the canonical ``.codex/specs`` layout, stable and qualified
IDs, repo-wide architecture identity, required semantic sections, actors,
rules, NFRs, rollout, task isolation, DoR/DoD, bidirectional traceability, and
EXECUTAR-TODAS. Fences, HTML comments, and indented Markdown code are
line-preservingly masked before structural parsing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path


LOCAL_ID_PREFIXES = ("REQ", "AC", "NFR", "TASK", "TEST", "EVD")
REPO_ID_PREFIXES = ("MOD", "CON", "EVT", "INV", "PAT", "ADR", "FIT")
ID_PREFIXES = LOCAL_ID_PREFIXES + REPO_ID_PREFIXES
STRICT_DEFINITION_PREFIXES = set(LOCAL_ID_PREFIXES) | {"MOD", "CON"}
ID_RE = re.compile(rf"\b({'|'.join(ID_PREFIXES)})-(\d+)\b")
CANONICAL_ID_RE = re.compile(rf"\b({'|'.join(ID_PREFIXES)})-\d{{3}}\b")
REFERENCE_RE = re.compile(
    rf"\b(?:(SPEC-\d{{3}}):)?(({'|'.join(ID_PREFIXES)})-\d{{3}})\b"
)
QUALIFIED_ANY_RE = re.compile(
    rf"\bSPEC-(\d+):(({'|'.join(ID_PREFIXES)})-(\d+))\b"
)
SPEC_ID_RE = re.compile(r"SPEC-\d{3}")
CHANGE_RE = re.compile(r"^(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*$")
VERDICTS = {"APROVADO", "APROVADO_COM_RESSALVAS", "QUESTIONAR", "REPROVADO"}


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    message: str
    line: int | None = None


@dataclass
class ValidationResult:
    root: str
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    changes: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, code: str, path: Path, message: str, line: int | None = None) -> None:
        self.errors.append(Issue(code, str(path), message, line))

    def warning(
        self, code: str, path: Path, message: str, line: int | None = None
    ) -> None:
        self.warnings.append(Issue(code, str(path), message, line))

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "kind": "specs",
            "root": self.root,
            "summary": {
                "changes": self.changes,
                "errors": len(self.errors),
                "warnings": len(self.warnings),
            },
            "errors": [asdict(item) for item in self.errors],
            "warnings": [asdict(item) for item in self.warnings],
        }


@dataclass(frozen=True)
class Table:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    line: int


@dataclass(frozen=True)
class Definition:
    path: Path
    line: int
    row: tuple[str, ...]


@dataclass(frozen=True)
class TaskFileSet:
    identifier: str
    reads: frozenset[str]
    writes: frozenset[str]
    dependencies: frozenset[str]
    isolation: str
    path: Path
    line: int


def _plain(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[`*_#]", "", value).lower()
    return re.sub(r"\s+", " ", value).strip()


def _mask_fenced(text: str) -> str:
    """Blank non-semantic Markdown while preserving the exact line count."""
    masked: list[str] = []
    fence_char = ""
    fence_size = 0
    in_comment = False
    raw_html_tag = ""
    raw_html_depth = 0
    raw_html_terminator = ""
    void_html_tags = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
    for raw_line in text.splitlines():
        line = raw_line
        visible: list[str] = []
        cursor = 0
        while cursor < len(line):
            if in_comment:
                end = line.find("-->", cursor)
                if end < 0:
                    cursor = len(line)
                    break
                in_comment = False
                cursor = end + 3
                continue
            start = line.find("<!--", cursor)
            if start < 0:
                visible.append(line[cursor:])
                break
            visible.append(line[cursor:start])
            in_comment = True
            cursor = start + 4
        line = "".join(visible)
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence_char:
            if match and match.group(1)[0] == fence_char and len(match.group(1)) >= fence_size:
                fence_char, fence_size = "", 0
            masked.append("")
            continue
        if match:
            token = match.group(1)
            fence_char, fence_size = token[0], len(token)
            masked.append("")
            continue
        if raw_html_terminator:
            if raw_html_terminator in line:
                raw_html_terminator = ""
            masked.append("")
            continue
        if raw_html_tag:
            opening = len(
                re.findall(
                    rf"<{re.escape(raw_html_tag)}(?=[\s>/]|$)",
                    line,
                    flags=re.IGNORECASE,
                )
            )
            closing = len(
                re.findall(
                    rf"</{re.escape(raw_html_tag)}\s*>",
                    line,
                    flags=re.IGNORECASE,
                )
            )
            raw_html_depth += opening - closing
            if raw_html_depth <= 0:
                raw_html_tag, raw_html_depth = "", 0
            masked.append("")
            continue
        construct = re.match(r"^ {0,3}(<\?|<!\[CDATA\[|<![A-Za-z])", line)
        if construct:
            token = construct.group(1).lower()
            if token == "<?":
                terminator = "?>"
            elif token == "<![cdata[":
                terminator = "]]>"
            else:
                terminator = ">"
            if terminator not in line[construct.end() :]:
                raw_html_terminator = terminator
            masked.append("")
            continue
        html = re.match(
            r"^ {0,3}<([A-Za-z][A-Za-z0-9:-]*)(?=[\s>/]|$)",
            line,
        )
        if html:
            tag = html.group(1).lower()
            if tag.endswith(":") and line[html.end() :].startswith("//"):
                masked.append(line)
                continue
            opening = len(
                re.findall(rf"<{re.escape(tag)}(?=[\s>/]|$)", line, flags=re.IGNORECASE)
            )
            closing = len(
                re.findall(rf"</{re.escape(tag)}\s*>", line, flags=re.IGNORECASE)
            )
            depth = opening - closing
            if tag not in void_html_tags and depth > 0:
                raw_html_tag, raw_html_depth = tag, depth
            masked.append("")
            continue
        if re.match(r"^ {0,3}</[A-Za-z][A-Za-z0-9:-]*\s*>", line):
            masked.append("")
            continue
        masked.append("" if re.match(r"^(?: {4}|\t)", line) else line)
    return "\n".join(masked)


def _cells(line: str) -> tuple[str, ...]:
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def _is_separator(cells: tuple[str, ...]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def _tables(text: str) -> list[Table]:
    lines = text.splitlines()
    result: list[Table] = []
    index = 0
    while index + 1 < len(lines):
        if not lines[index].lstrip().startswith("|"):
            index += 1
            continue
        headers = _cells(lines[index])
        separators = _cells(lines[index + 1])
        if len(headers) != len(separators) or not _is_separator(separators):
            index += 1
            continue
        rows: list[tuple[str, ...]] = []
        cursor = index + 2
        while cursor < len(lines) and lines[cursor].lstrip().startswith("|"):
            row = _cells(lines[cursor])
            if len(row) == len(headers):
                rows.append(row)
            cursor += 1
        result.append(Table(headers, tuple(rows), index + 1))
        index = cursor
    return result


def _find_tables(text: str, *tokens: str) -> list[Table]:
    wanted = tuple(_plain(token) for token in tokens)
    return [
        table
        for table in _tables(text)
        if all(any(token in _plain(header) for header in table.headers) for token in wanted)
    ]


def _headings(text: str) -> list[tuple[int, str, int]]:
    result: list[tuple[int, str, int]] = []
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            result.append((len(match.group(1)), _plain(match.group(2)), number))
    return result


def _section(text: str, needle: str) -> str:
    lines = text.splitlines()
    normalized = _plain(needle)
    start: int | None = None
    level = 0
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if not match:
            continue
        heading = _plain(match.group(2))
        if start is None and normalized in heading:
            start = index + 1
            level = len(match.group(1))
            continue
        if start is not None and len(match.group(1)) <= level:
            return "\n".join(lines[start:index])
    return "\n".join(lines[start:]) if start is not None else ""


def _has_heading(headings: list[tuple[int, str, int]], needle: str) -> bool:
    wanted = _plain(needle)
    return any(wanted in title for _, title, _ in headings)


def _metadata(text: str, label: str) -> str:
    wanted = _plain(label)
    for line in text.splitlines():
        stripped = re.sub(r"^\s*[-*]\s*", "", line).replace("**", "")
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        if _plain(key) == wanted:
            return value.strip()
    return ""


def _is_placeholder(value: str) -> bool:
    clean = _plain(value)
    return not clean or clean in {"...", "-", "todo", "tbd", "pendente", "n/a", "na"} or bool(
        re.search(r"\[(?:nome|descricao|pendente|preencher)[^\]]*\]", clean)
    )


def _is_justified_na(value: str) -> bool:
    clean = _plain(value)
    return bool(re.match(r"^(?:n/a|na)\s*[-:]\s*\S+", clean))


def _is_concrete(value: str, *, allow_justified_na: bool = False) -> bool:
    if allow_justified_na and _is_justified_na(value):
        return True
    return not _is_placeholder(value)


def _valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _concrete_reservation_field(value: str) -> bool:
    clean = _plain(value)
    return (
        _is_concrete(value)
        and not _is_justified_na(value)
        and "|" not in value
        and "[" not in value
        and clean not in {"x", "sim", "ok"}
    )


def _has_metadata_label(text: str, label: str) -> bool:
    wanted = _plain(label)
    for line in text.splitlines():
        stripped = re.sub(r"^\s*[-*]\s*", "", line).replace("**", "")
        if ":" in stripped and _plain(stripped.split(":", 1)[0]) == wanted:
            return True
    return False


def _definition_rows(texts: dict[Path, str]) -> dict[str, list[Definition]]:
    definitions: dict[str, list[Definition]] = {}
    for path, text in texts.items():
        for table in _tables(text):
            if not table.headers or _plain(table.headers[0]) != "id":
                continue
            for offset, row in enumerate(table.rows, 2):
                first = row[0].strip().strip("`")
                if CANONICAL_ID_RE.fullmatch(first):
                    definitions.setdefault(first, []).append(
                        Definition(path, table.line + offset, row)
                    )
    return definitions


def _traceability_tables(text: str) -> list[Table]:
    return _find_tables(text, "requisito", "modulo", "task", "teste", "evidencia")


def _column(table: Table, token: str) -> int:
    normalized = _plain(token)
    return next(
        index for index, header in enumerate(table.headers) if normalized in _plain(header)
    )


def _ids(value: str, prefixes: set[str] | None = None) -> set[str]:
    found = {match.group(2) for match in REFERENCE_RE.finditer(value)}
    if prefixes is not None:
        return {item for item in found if item.split("-", 1)[0] in prefixes}
    return found


def _local_ids(value: str, spec_id: str, prefixes: set[str]) -> set[str]:
    return {
        match.group(2)
        for match in REFERENCE_RE.finditer(value)
        if match.group(3) in prefixes and match.group(1) in {None, spec_id}
    }


def _unqualified_ids(value: str) -> set[str]:
    return {
        match.group(2)
        for match in REFERENCE_RE.finditer(value)
        if match.group(1) is None
    }


def _optional_column(table: Table, *tokens: str) -> int | None:
    wanted = tuple(_plain(token) for token in tokens)
    for index, header in enumerate(table.headers):
        normalized = _plain(header)
        if any(token in normalized for token in wanted):
            return index
    return None


def _literal_file_set(value: str) -> frozenset[str]:
    normalized = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    items: set[str] = set()
    for token in re.split(r"[,;\n]", normalized):
        clean = token.strip().strip("`").replace("\\", "/")
        if clean.startswith("./"):
            clean = clean[2:]
        if not clean or _plain(clean) in {"none", "nenhum", "nenhuma"}:
            continue
        if _is_justified_na(clean):
            continue
        items.add(clean)
    return frozenset(items)


def _validate_verdict(
    result: ValidationResult, path: Path, text: str, label: str
) -> str | None:
    section = _section(text, label)
    if not section:
        result.error("missing-checklist", path, f"Missing {label} section.")
        return None
    checkboxes = re.findall(r"(?m)^\s*-\s*\[([ xX])\]", section)
    if not checkboxes:
        result.error("missing-checklist", path, f"{label} must contain a checklist.")
    matches = re.findall(
        rf"(?im)^\s*\*\*Veredito\s+{re.escape(label)}:\*\*\s*`?([A-Z_]+)`?\s*$",
        section,
    )
    if len(matches) != 1:
        code = "invalid-verdict" if not matches else "duplicate-verdict"
        result.error(
            code,
            path,
            f"{label} must declare exactly one canonical verdict; found {len(matches)}.",
        )
        return None
    if matches[0] not in VERDICTS:
        result.error("invalid-verdict", path, f"{label} must declare one canonical verdict.")
        return None
    verdict = matches[0]
    if verdict == "APROVADO" and any(mark.lower() != "x" for mark in checkboxes):
        result.error(
            "inconsistent-approved-checklist",
            path,
            f"{label} cannot be APROVADO while checklist items remain unchecked.",
        )
    if verdict == "APROVADO_COM_RESSALVAS":
        gap = _metadata(section, "Lacuna nao bloqueante")
        action = _metadata(section, "Acao")
        owner = _metadata(section, "Dono")
        closure = _metadata(section, "Prazo ISO/criterio verificavel")
        deadline = re.search(r"\b\d{4}-\d{2}-\d{2}\b", closure)
        valid_deadline = bool(deadline and _valid_iso_date(deadline.group(0)))
        closure_evidence = _ids(closure, {"TEST", "FIT", "EVD"})
        verifiable_criterion = bool(
            deadline is None
            and _concrete_reservation_field(closure)
            and closure_evidence
            and re.search(
                r"\b(?:passa|pass|aprovado|registrado|produzido|exit code 0|sem falha)\b",
                _plain(closure),
            )
        )
        if not (
            _concrete_reservation_field(gap)
            and _concrete_reservation_field(action)
            and _concrete_reservation_field(owner)
            and (valid_deadline or verifiable_criterion)
        ):
            result.error(
                "incomplete-reservations",
                path,
                f"{label} APROVADO_COM_RESSALVAS requires a concrete nonblocking "
                "gap, action, owner, and valid ISO deadline or verifiable criterion.",
            )
    if verdict in {"QUESTIONAR", "REPROVADO"}:
        result.error(
            "blocking-verdict", path, f"{label} verdict is {verdict}; handoff is blocked."
        )
    return verdict


def _validate_state_and_rules(
    result: ValidationResult, spec: Path, text: str, definitions: dict[str, list[Definition]]
) -> None:
    state = _section(text, "1. State")
    for label in ("Atores e papeis", "Precondicoes"):
        if _is_placeholder(_metadata(state, label)):
            result.error(
                "missing-behavior-context", spec, f"State must define concrete {label}."
            )
    functional = _section(text, "3. Requisitos Funcionais")
    rule_tables = _find_tables(functional, "ID/relacao", "Regra", "Erros/estados", "Permissoes")
    if not rule_tables or not rule_tables[0].rows:
        result.error(
            "missing-rule-matrix",
            spec,
            "Functional requirements need a rule/errors/permissions matrix.",
        )
        return
    known = set(definitions)
    for row_number, row in enumerate(rule_tables[0].rows, rule_tables[0].line + 2):
        refs = _ids(row[0], {"REQ", "AC"})
        if not refs or refs - known:
            result.error(
                "invalid-rule-reference",
                spec,
                "Rule matrix row must reference defined REQ/AC IDs.",
                row_number,
            )
        if any(_is_placeholder(cell) for cell in row[1:]):
            result.error(
                "incomplete-rule-matrix",
                spec,
                "Rule, errors/states, and permissions must be concrete.",
                row_number,
            )


def _validate_nfrs(result: ValidationResult, spec: Path, text: str) -> None:
    section = _section(text, "4. Requisitos Nao Funcionais")
    tables = _find_tables(section, "ID", "Eixo", "Gate")
    if not tables:
        result.error(
            "missing-nfr-matrix",
            spec,
            "NFRs need an ID/eixo/limite/gate matrix.",
        )
        return
    found = False
    for table in tables:
        axis_col = _column(table, "Eixo")
        gate_col = _column(table, "Gate")
        limit_col = _optional_column(table, "Requisito/limite", "Limite", "Requisito")
        condition_col = _optional_column(table, "Condicao/carga", "Condicao", "Carga")
        if limit_col is None:
            result.error(
                "invalid-nfr-schema",
                spec,
                "NFR matrix needs a requirement/limit column.",
                table.line,
            )
            continue
        for row_number, row in enumerate(table.rows, table.line + 2):
            if not re.fullmatch(r"NFR-\d{3}", row[0].strip()):
                continue
            found = True
            required = [row[axis_col], row[limit_col], row[gate_col]]
            if condition_col is not None:
                required.append(row[condition_col])
            if any(not _is_concrete(value, allow_justified_na=True) for value in required):
                result.error(
                    "incomplete-nfr",
                    spec,
                    "NFR needs a concrete axis, limit, condition when declared, and gate.",
                    row_number,
                )
                continue
            gate = row[gate_col]
            if not _is_justified_na(gate) and not _ids(gate, {"TEST", "FIT"}):
                result.error(
                    "invalid-nfr-gate",
                    spec,
                    "NFR gate must reference TEST-/FIT- or use justified N/A.",
                    row_number,
                )
    if not found:
        result.error("missing-nfr-row", spec, "NFR matrix has no NFR-NNN row.")


def _validate_rollout(result: ValidationResult, spec: Path, text: str) -> None:
    section = _section(text, "10. Rollout E Rollback")
    if not _is_concrete(section):
        result.error(
            "missing-rollout-plan",
            spec,
            "Rollout/Rollback must contain a concrete plan.",
        )
        return
    labels = (
        "Ambientes e ordem",
        "Smoke e observabilidade",
        "Criterio de abortar",
        "Rollback de aplicacao",
        "Rollback de dados",
        "Forward-fix/restauracao quando rollback for inseguro",
    )
    labeled = any(_has_metadata_label(section, label) for label in labels)
    if not labeled:
        normalized = _plain(section)
        has_rollout = bool(re.search(r"\b(?:rollout|deploy|canary|ambiente|smoke)\b", normalized))
        has_rollback = bool(re.search(r"\b(?:rollback|forward-fix|restauracao)\b", normalized))
        if not has_rollout or not has_rollback:
            result.error(
                "incomplete-rollout-plan",
                spec,
                "Free-form rollout plan must state rollout/smoke and rollback/forward-fix.",
            )
        return
    for label in labels[:4]:
        value = _metadata(section, label)
        if not _is_concrete(value, allow_justified_na=False):
            result.error(
                "incomplete-rollout-plan",
                spec,
                f"Rollout/Rollback needs concrete {label}.",
            )
    data_rollback = _metadata(section, labels[4])
    forward_fix = _metadata(section, labels[5])
    if not any(
        _is_concrete(value, allow_justified_na=True)
        for value in (data_rollback, forward_fix)
    ):
        result.error(
            "incomplete-rollout-plan",
            spec,
            "Declare data rollback or a justified forward-fix/restoration strategy.",
        )


def _validate_qualified_references(
    result: ValidationResult,
    spec: Path,
    combined: str,
    catalog: dict[str, set[str]],
) -> None:
    for match in QUALIFIED_ANY_RE.finditer(combined):
        spec_digits, identifier, prefix, id_digits = match.groups()
        if len(spec_digits) != 3 or len(id_digits) != 3:
            result.error(
                "malformed-qualified-id",
                spec,
                f"Qualified reference {match.group(0)} must use three-digit IDs.",
            )
            continue
        target_spec = f"SPEC-{spec_digits}"
        if prefix not in LOCAL_ID_PREFIXES:
            result.error(
                "invalid-cross-spec-prefix",
                spec,
                f"Repo-scoped {identifier} must not be qualified with {target_spec}.",
            )
            continue
        if target_spec not in catalog:
            result.error(
                "unknown-cross-spec",
                spec,
                f"Qualified reference targets absent {target_spec}.",
            )
        elif identifier not in catalog[target_spec]:
            result.error(
                "unknown-cross-spec-id",
                spec,
                f"{target_spec} does not define {identifier}.",
            )


def _validate_backlog(
    result: ValidationResult, spec: Path, texts: dict[Path, str], definitions: dict[str, list[Definition]]
) -> None:
    tables: list[tuple[Path, Table]] = []
    for path, text in texts.items():
        tables.extend(
            (path, table)
            for table in _find_tables(
                text, "ID", "Entrega", "Read-set", "Write-set", "Dependencias"
            )
        )
    if not tables:
        result.error(
            "missing-backlog-contract",
            spec,
            "Backlog must declare Read-set and Write-set columns.",
        )
        return
    task_rows: set[str] = set()
    records: dict[str, TaskFileSet] = {}
    for path, table in tables:
        read_col = _column(table, "Read-set")
        write_col = _column(table, "Write-set")
        dependency_col = _column(table, "Dependencias")
        isolation_col = _optional_column(
            table, "Execucao/isolamento", "Isolamento", "Serializacao"
        )
        for row_number, row in enumerate(table.rows, table.line + 2):
            task = row[0].strip()
            if not re.fullmatch(r"TASK-\d{3}", task):
                continue
            task_rows.add(task)
            file_values = (row[read_col], row[write_col])
            if any(
                not _is_concrete(value, allow_justified_na=True)
                or _plain(value) in {"none", "nenhum", "nenhuma"}
                for value in file_values
            ):
                result.error(
                    "missing-task-file-set",
                    spec,
                    f"{task} needs non-placeholder Read-set and Write-set.",
                    row_number,
                )
            records[task] = TaskFileSet(
                task,
                _literal_file_set(row[read_col]),
                _literal_file_set(row[write_col]),
                frozenset(_ids(row[dependency_col], {"TASK"})),
                row[isolation_col] if isolation_col is not None else "",
                path,
                row_number,
            )
    defined_tasks = {identifier for identifier in definitions if identifier.startswith("TASK-")}
    missing = sorted(defined_tasks - task_rows)
    if missing:
        result.error(
            "task-outside-backlog",
            spec,
            f"TASK definitions absent from executable backlog: {missing}.",
        )

    visit_state: dict[str, int] = {}
    visit_stack: list[str] = []
    cyclic_nodes: set[str] = set()
    reported_cycles: set[tuple[str, ...]] = set()

    def detect_cycles(task_id: str) -> None:
        visit_state[task_id] = 1
        visit_stack.append(task_id)
        for dependency in sorted(records[task_id].dependencies):
            if dependency not in records:
                continue
            state = visit_state.get(dependency, 0)
            if state == 0:
                detect_cycles(dependency)
                continue
            if state == 1:
                start = visit_stack.index(dependency)
                cycle = visit_stack[start:] + [dependency]
                cyclic_nodes.update(cycle)
                signature = tuple(sorted(set(cycle[:-1])))
                if signature not in reported_cycles:
                    reported_cycles.add(signature)
                    result.error(
                        "task-dependency-cycle",
                        records[task_id].path,
                        f"Task dependency cycle detected: {' -> '.join(cycle)}.",
                        records[task_id].line,
                    )
        visit_stack.pop()
        visit_state[task_id] = 2

    for task_id in sorted(records):
        if visit_state.get(task_id, 0) == 0:
            detect_cycles(task_id)

    def depends_on(source: str, target: str, seen: set[str] | None = None) -> bool:
        if source not in records:
            return False
        if source in cyclic_nodes or target in cyclic_nodes:
            return False
        seen = set() if seen is None else seen
        if source in seen:
            return False
        seen.add(source)
        dependencies = records[source].dependencies
        return target in dependencies or any(
            depends_on(dependency, target, seen) for dependency in dependencies
        )

    def isolation_id(record: TaskFileSet, kind: str) -> str | None:
        declaration = _plain(record.isolation)
        match = re.search(rf"\b{kind}\s*[:=]\s*([^\s,;]+)", declaration)
        return match.group(1) if match else None

    task_ids = sorted(records)
    for index, left_id in enumerate(task_ids):
        left = records[left_id]
        for right_id in task_ids[index + 1 :]:
            right = records[right_id]
            if depends_on(left_id, right_id) or depends_on(right_id, left_id):
                continue
            left_declaration = _plain(left.isolation)
            right_declaration = _plain(right.isolation)
            if "serial" in left_declaration or "serial" in right_declaration:
                continue
            left_worktree = isolation_id(left, "worktree")
            right_worktree = isolation_id(right, "worktree")
            if left_worktree and right_worktree and left_worktree != right_worktree:
                continue
            left_snapshot = isolation_id(left, "snapshot")
            right_snapshot = isolation_id(right, "snapshot")
            unsafe = left.writes & right.writes
            if not right_snapshot:
                unsafe |= left.writes & right.reads
            if not left_snapshot:
                unsafe |= right.writes & left.reads
            if unsafe:
                result.error(
                    "concurrent-file-set-conflict",
                    left.path,
                    f"{left_id} and {right_id} have unsafely overlapping literal file sets: "
                    f"{sorted(unsafe)}. Add dependency, SERIAL, SNAPSHOT:<fingerprint> "
                    "for a reader, or distinct WORKTREE:<id> isolation.",
                    left.line,
                )


def _validate_change(
    result: ValidationResult, change: Path, catalog: dict[str, set[str]]
) -> dict[str, tuple[str, Path]]:
    spec = change / "spec.md"
    if not spec.is_file():
        result.error("missing-spec", change, "Every change folder must contain spec.md.")
        return {}
    files = [spec]
    tasks = change / "tasks.md"
    if tasks.is_file():
        files.append(tasks)
    raw_texts = {path: path.read_text(encoding="utf-8-sig") for path in files}
    texts = {path: _mask_fenced(text) for path, text in raw_texts.items()}
    for path, raw in raw_texts.items():
        if raw.strip() and not texts[path].strip():
            result.error(
                "fenced-artifact", path, "Artifact content cannot be entirely fenced code."
            )
    combined = "\n".join(texts.values())
    headings = _headings(texts[spec])
    expected_spec_id = f"SPEC-{change.name[:3]}"
    declared_spec_id = _metadata(texts[spec], "Spec").strip().strip("`")
    if not SPEC_ID_RE.fullmatch(declared_spec_id):
        result.error(
            "invalid-spec-id",
            spec,
            "Spec metadata must declare canonical SPEC-NNN.",
        )
    elif declared_spec_id != expected_spec_id:
        result.error(
            "spec-id-mismatch",
            spec,
            f"Folder {change.name} must declare {expected_spec_id}, not {declared_spec_id}.",
        )
    required_sections = (
        "0. Identificacao",
        "1. State",
        "2. Escopo",
        "3. Requisitos Funcionais",
        "4. Requisitos Nao Funcionais",
        "5. Definition Of Ready",
        "6. Design E Contratos",
        "7. Doubt",
        "8. Backlog Executavel",
        "9. Rastreabilidade Obrigatoria",
        "10. Rollout E Rollback",
        "11. Demonstrate - Testes, Harness E Evidencias",
        "12. Definition Of Done",
        "13. Document",
    )
    for heading in required_sections:
        if not _has_heading(headings, heading):
            result.error("missing-section", spec, f"Missing required section: {heading}.")

    _validate_verdict(result, spec, texts[spec], "DoR")
    _validate_verdict(result, spec, texts[spec], "DoD")
    _validate_nfrs(result, spec, texts[spec])
    _validate_rollout(result, spec, texts[spec])
    _validate_qualified_references(result, spec, combined, catalog)
    for match in ID_RE.finditer(combined):
        if len(match.group(2)) != 3:
            result.error(
                "malformed-id", spec, f"ID {match.group(0)} must use exactly three digits."
            )

    definitions = _definition_rows(texts)
    by_prefix = {prefix: set() for prefix in ID_PREFIXES}
    for identifier, records in definitions.items():
        by_prefix[identifier.split("-", 1)[0]].add(identifier)
        if len(records) > 1:
            where = ", ".join(f"{item.path.name}:{item.line}" for item in records)
            result.error(
                "duplicate-definition",
                change,
                f"ID {identifier} has multiple definition rows: {where}.",
            )
    for prefix in ("REQ", "AC", "NFR", "TASK", "EVD"):
        identifiers = by_prefix[prefix]
        if not identifiers:
            result.error(
                "missing-id-family",
                change,
                f"Change must define at least one {prefix}-NNN row in an ID table.",
            )

    referenced = _unqualified_ids(combined)
    available = set(definitions) | _ids(combined)
    for family, prefixes in (
        ("architecture", {"MOD", "CON", "EVT"}),
        ("proof", {"TEST", "FIT"}),
    ):
        if not any(identifier.split("-", 1)[0] in prefixes for identifier in available):
            result.error(
                "missing-id-family",
                change,
                f"Change must reference at least one canonical {family} ID: {sorted(prefixes)}.",
            )
    for identifier in sorted(referenced - set(definitions)):
        if identifier.split("-", 1)[0] not in STRICT_DEFINITION_PREFIXES:
            continue
        result.error(
            "undefined-id",
            change,
            f"Referenced ID {identifier} has no canonical definition row in this change.",
        )
    _validate_state_and_rules(result, spec, texts[spec], definitions)
    _validate_backlog(result, spec, texts, definitions)

    matrices = _traceability_tables(texts[spec])
    if not matrices:
        result.error(
            "missing-traceability-matrix",
            spec,
            "Traceability must map requirement -> module/contract -> task -> test -> evidence.",
        )
    else:
        covered: dict[str, set[str]] = {
            "requirement": set(),
            "task": set(),
            "test": set(),
            "evidence": set(),
        }
        for table in matrices:
            columns = {
                token: _column(table, token)
                for token in ("requisito", "modulo", "task", "teste", "evidencia")
            }
            for row_number, row in enumerate(table.rows, table.line + 2):
                chains = {
                    "requirement": _ids(row[columns["requisito"]], {"REQ", "AC", "NFR"}),
                    "module/contract/event": _ids(
                        row[columns["modulo"]], {"MOD", "CON", "EVT"}
                    ),
                    "task": _ids(row[columns["task"]], {"TASK"}),
                    "test/fitness": _ids(row[columns["teste"]], {"TEST", "FIT"}),
                    "evidence": _ids(row[columns["evidencia"]], {"EVD"}),
                }
                missing = [label for label, values in chains.items() if not values]
                if missing:
                    result.error(
                        "broken-traceability-row",
                        spec,
                        f"Traceability row is missing: {', '.join(missing)}.",
                        row_number,
                    )
                covered["requirement"].update(
                    _local_ids(
                        row[columns["requisito"]],
                        expected_spec_id,
                        {"REQ", "AC", "NFR"},
                    )
                )
                covered["task"].update(
                    _local_ids(row[columns["task"]], expected_spec_id, {"TASK"})
                )
                covered["test"].update(
                    _local_ids(row[columns["teste"]], expected_spec_id, {"TEST", "FIT"})
                )
                covered["evidence"].update(
                    _local_ids(row[columns["evidencia"]], expected_spec_id, {"EVD"})
                )
        expected_coverage = {
            "requirement": by_prefix["REQ"] | by_prefix["AC"] | by_prefix["NFR"],
            "task": by_prefix["TASK"],
            "test": by_prefix["TEST"] | by_prefix["FIT"],
            "evidence": by_prefix["EVD"],
        }
        for kind, expected_ids in expected_coverage.items():
            uncovered = sorted(expected_ids - covered[kind])
            if uncovered:
                result.error(
                    f"uncovered-{kind}",
                    spec,
                    f"{kind.title()} IDs absent from traceability matrix: {uncovered}.",
                )

    repo_definitions: dict[str, tuple[str, Path]] = {}
    for identifier, records in definitions.items():
        if identifier.split("-", 1)[0] in REPO_ID_PREFIXES and records:
            signature = _plain(" | ".join(records[0].row[1:]))
            repo_definitions[identifier] = (signature, change)
    return repo_definitions


def _resolve_specs_root(path: Path) -> Path:
    path = path.resolve()
    for candidate in (path, path / ".codex" / "specs", path / "specs"):
        if (candidate / "changes").is_dir() or (candidate / "EXECUTAR-TODAS.md").exists():
            return candidate
    return path


def validate_specs(path: str | Path) -> ValidationResult:
    root = _resolve_specs_root(Path(path))
    result = ValidationResult(str(root))
    changes_dir = root / "changes"
    index = root / "EXECUTAR-TODAS.md"
    if not changes_dir.is_dir():
        result.error("missing-changes", changes_dir, "Missing changes/ directory.")
        return result
    if not index.is_file():
        result.error("missing-index", index, "Missing EXECUTAR-TODAS.md.")

    changes = sorted(item for item in changes_dir.iterdir() if item.is_dir())
    result.changes = len(changes)
    if not changes:
        result.error("no-changes", changes_dir, "No granular change folders found.")
        return result
    numbers: dict[str, str] = {}
    valid_names: set[str] = set()
    valid_changes: list[Path] = []
    repo_ids: dict[str, tuple[str, Path]] = {}
    for change in changes:
        match = CHANGE_RE.fullmatch(change.name)
        if not match:
            result.error(
                "invalid-change-name", change, "Change folder must be NNN-descriptive-kebab-case."
            )
            continue
        number = match.group(1)
        if number in numbers:
            result.error(
                "duplicate-change-number",
                change,
                f"Change number {number} is already used by {numbers[number]}.",
            )
        numbers[number] = change.name
        valid_names.add(change.name)
        valid_changes.append(change)

    catalog: dict[str, set[str]] = {}
    for change in valid_changes:
        files = [change / "spec.md", change / "tasks.md"]
        texts = {
            file: _mask_fenced(file.read_text(encoding="utf-8-sig"))
            for file in files
            if file.is_file()
        }
        catalog[f"SPEC-{change.name[:3]}"] = set(_definition_rows(texts))

    for change in valid_changes:
        for identifier, (signature, owner) in _validate_change(
            result, change, catalog
        ).items():
            previous = repo_ids.get(identifier)
            if previous and previous[0] != signature:
                result.error(
                    "repo-id-conflict",
                    change,
                    f"{identifier} conflicts with its repo-wide definition in {previous[1].name}.",
                )
            else:
                repo_ids.setdefault(identifier, (signature, owner))

    if index.is_file():
        text = _mask_fenced(index.read_text(encoding="utf-8-sig"))
        indexed = set(re.findall(r"\b\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*\b", text))
        missing = sorted(valid_names - indexed)
        stale = sorted(indexed - valid_names)
        if missing:
            result.error("index-missing-change", index, f"Index omits changes: {missing}.")
        if stale:
            result.error("index-stale-change", index, f"Index references absent changes: {stale}.")
    return result


def _print_human(result: ValidationResult) -> None:
    print(f"Spec governance validation: {'OK' if result.ok else 'FAILED'}")
    print(f"Root: {result.root}")
    print(f"Changes: {result.changes}")
    for issue in result.errors:
        suffix = f":{issue.line}" if issue.line else ""
        print(f"ERROR [{issue.code}] {issue.path}{suffix}: {issue.message}")
    for issue in result.warnings:
        suffix = f":{issue.line}" if issue.line else ""
        print(f"WARNING [{issue.code}] {issue.path}{suffix}: {issue.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".", help="project or specs root")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    result = validate_specs(args.path)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_human(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
