#!/usr/bin/env python3
"""Validate AS-IS, TO-BE, and Pattern Map architecture artifacts.

The stdlib-only validator masks fenced examples, indented Markdown code, and
raw HTML blocks before parsing structure. AS-IS requires direct dated evidence;
TO-BE requires complete module/contract graphs, safe transition semantics, and
referential integrity; Pattern Map keeps code presence separate from normative
decision and validates the final verdict.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path


PRESENCES = {"OBSERVADO", "PARCIAL", "NAO_OBSERVADO"}
MATERIALITIES = {"SIM", "NAO"}
DECISIONS = {
    "SEM_DECISAO",
    "PROPOSTO",
    "APROVADO",
    "DESCARTADO",
    "DEPRECIADO",
    "PROIBIDO",
}
NORMATIVE_DECISIONS = {"APROVADO", "DESCARTADO", "DEPRECIADO", "PROIBIDO"}
VERDICTS = {"APROVADO", "APROVADO_COM_RESSALVAS", "QUESTIONAR", "REPROVADO"}
TARGET_STATES = {"RASCUNHO", "APROVADO", "EM_TRANSICAO", "ATINGIDO", "SUBSTITUIDO"}
TARGET_PATTERN_PRESENCES = {"PRESENTE", "AUSENTE"}
TARGET_PATTERN_DECISIONS = {
    "PROPOSTO",
    "APROVADO",
    "DESCARTADO",
    "DEPRECIADO",
    "PROIBIDO",
}
ID = {
    prefix: re.compile(rf"\b{prefix}-\d{{3}}\b")
    for prefix in (
        "REQ",
        "AC",
        "NFR",
        "MOD",
        "CON",
        "EVT",
        "INV",
        "TASK",
        "TEST",
        "EVD",
        "ADR",
        "FIT",
        "PAT",
        "DELTA",
    )
}


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
    validated: list[str] = field(default_factory=list)

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
            "kind": "architecture",
            "root": self.root,
            "summary": {
                "validated": self.validated,
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


def _plain(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[`*_#]", "", value).lower()
    return re.sub(r"\s+", " ", value).strip()


def _mask_fenced(text: str) -> str:
    masked: list[str] = []
    fence_char = ""
    fence_size = 0
    for line in text.splitlines():
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if not fence_char:
            if match:
                token = match.group(1)
                fence_char, fence_size = token[0], len(token)
                masked.append("")
            else:
                masked.append(line)
            continue
        if match and match.group(1)[0] == fence_char and len(match.group(1)) >= fence_size:
            fence_char, fence_size = "", 0
        masked.append("")
    return "\n".join(masked)


def _mask_html_comments(text: str) -> str:
    """Mask complete or unterminated HTML comments while preserving line numbers."""

    def replace(match: re.Match[str]) -> str:
        return "".join("\n" if char == "\n" else " " for char in match.group(0))

    return re.sub(r"<!--.*?(?:-->|\Z)", replace, text, flags=re.DOTALL)


HTML_TAG_START = re.compile(
    r"^ {0,3}<([A-Za-z][A-Za-z0-9:-]*)(?=[\s/>])",
    re.IGNORECASE,
)
HTML_TAG_CLOSE = re.compile(
    r"^ {0,3}</([A-Za-z][A-Za-z0-9:-]*)\s*>",
    re.IGNORECASE,
)
HTML_VOID_TAGS = {
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


def _mask_raw_html_blocks(text: str) -> str:
    """Mask raw HTML blocks, including arbitrary paired wrapper elements."""

    def masked(line: str) -> str:
        return "".join("\n" if char == "\n" else " " for char in line)

    def tag_delta(line: str, tag: str) -> int:
        escaped = re.escape(tag)
        openings = re.findall(
            rf"<{escaped}(?=[\s/>])[^>]*>", line, flags=re.IGNORECASE
        )
        closings = len(
            re.findall(rf"</{escaped}\s*>", line, flags=re.IGNORECASE)
        )
        return len(openings) - closings

    result: list[str] = []
    active_tag = ""
    depth = 0
    special_end = ""
    for line in text.splitlines(keepends=True):
        if special_end:
            result.append(masked(line))
            if special_end.lower() in line.lower():
                special_end = ""
            continue
        if active_tag:
            result.append(masked(line))
            depth += tag_delta(line, active_tag)
            if depth <= 0:
                active_tag, depth = "", 0
            continue

        stripped = line.lstrip(" ")
        leading = len(line) - len(stripped)
        if leading <= 3 and stripped.startswith("<?"):
            result.append(masked(line))
            if "?>" not in line:
                special_end = "?>"
            continue
        if leading <= 3 and stripped.upper().startswith("<![CDATA["):
            result.append(masked(line))
            if "]]>" not in line:
                special_end = "]]>"
            continue
        if leading <= 3 and re.match(r"<![A-Z]", stripped):
            result.append(masked(line))
            if ">" not in line:
                special_end = ">"
            continue

        start = HTML_TAG_START.match(line)
        if start:
            tag = start.group(1)
            result.append(masked(line))
            depth = tag_delta(line, tag)
            if tag.lower() not in HTML_VOID_TAGS and depth <= 0:
                has_opening_end = bool(
                    re.search(rf"<{re.escape(tag)}(?=[\s/>])[^>]*>", line, re.IGNORECASE)
                )
                has_closing = bool(
                    re.search(rf"</{re.escape(tag)}\s*>", line, re.IGNORECASE)
                )
                if not (has_opening_end and has_closing):
                    depth = 1
            if tag.lower() not in HTML_VOID_TAGS and depth > 0:
                active_tag = tag
            continue
        if HTML_TAG_CLOSE.match(line):
            result.append(masked(line))
            continue
        result.append(line)
    return "".join(result)


def _mask_indented_code(text: str) -> str:
    """Mask Markdown indented code blocks while preserving line numbers."""

    masked: list[str] = []
    for line in text.splitlines(keepends=True):
        if re.match(r"^(?: {4,}|\t)", line):
            masked.append("".join("\n" if char == "\n" else " " for char in line))
        else:
            masked.append(line)
    return "".join(masked)


def _cells(line: str) -> tuple[str, ...]:
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


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
        valid_separator = bool(separators) and all(
            re.fullmatch(r":?-{3,}:?", cell) for cell in separators
        )
        if len(headers) != len(separators) or not valid_separator:
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


def _headings(text: str) -> list[tuple[int, str, int]]:
    result: list[tuple[int, str, int]] = []
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            result.append((len(match.group(1)), _plain(match.group(2)), number))
    return result


def _has_heading(headings: list[tuple[int, str, int]], needle: str) -> bool:
    wanted = _plain(needle)
    return any(wanted in title for _, title, _ in headings)


def _find_tables(text: str, *header_tokens: str) -> list[Table]:
    wanted = tuple(_plain(token) for token in header_tokens)
    return [
        table
        for table in _tables(text)
        if all(any(token in _plain(header) for header in table.headers) for token in wanted)
    ]


def _column(table: Table, token: str) -> int:
    normalized = _plain(token)
    return next(
        index
        for index, header in enumerate(table.headers)
        if normalized in _plain(header)
    )


def _placeholder(value: str) -> bool:
    clean = _plain(value)
    if not clean or clean in {"...", "-", "todo", "tbd", "pendente", "n/a", "na"}:
        return True
    if re.fullmatch(r"(?:mod|con|evt|inv|req|ac|nfr|task|test|evd|adr|fit|pat)-", clean):
        return True
    return bool(re.search(r"\[(?:nome|descricao|preencher|time|caminho)[^\]]*\]", clean))


def _actual_rows(table: Table) -> list[tuple[str, ...]]:
    return [row for row in table.rows if not all(_placeholder(cell) for cell in row)]


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


def _valid_date(value: str) -> bool:
    try:
        dt.date.fromisoformat(value.strip())
    except ValueError:
        return False
    return True


def _justified_na(value: str) -> bool:
    return bool(re.search(r"(?i)(?:^|[/|])\s*N/A\s*[-:–—]\s*\S.{5,}$", value.strip()))


def _adr_or_na(value: str) -> bool:
    return bool(ID["ADR"].search(value) or _justified_na(value))


def _starts_with_na(value: str) -> bool:
    return bool(re.match(r"(?i)^\s*N/A\b", value))


def _section_bounds(text: str, needle: str) -> tuple[int, int] | None:
    lines = text.splitlines()
    wanted = _plain(needle)
    start: int | None = None
    level = 0
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if not match:
            continue
        if start is None and wanted in _plain(match.group(2)):
            start = index + 1
            level = len(match.group(1))
            continue
        if start is not None and len(match.group(1)) <= level:
            return start, index
    return (start, len(lines)) if start is not None else None


def _section(text: str, needle: str) -> str:
    bounds = _section_bounds(text, needle)
    if bounds is None:
        return ""
    return "\n".join(text.splitlines()[bounds[0] : bounds[1]])


def _section_raw(raw: str, masked: str, needle: str) -> str:
    bounds = _section_bounds(masked, needle)
    if bounds is None:
        return ""
    return "\n".join(raw.splitlines()[bounds[0] : bounds[1]])


def _validate_evidence(
    result: ValidationResult, document: Path, value: str, context: str
) -> bool:
    external = bool(
        re.search(r"\b(?:EXTERNO|EXTERNAL)\s*:\s*\S", value, re.IGNORECASE)
    )
    command = bool(
        re.search(r"\b(?:COMANDO(?:/RESULTADO)?|COMMAND)\s*:\s*\S", value, re.IGNORECASE)
    )
    path_matches = re.findall(
        r"(?<![\w:/])([A-Za-z0-9_.-]+(?:[/\\][A-Za-z0-9_.-]+)*\.[A-Za-z0-9]+):[A-Za-z_][\w.:-]*",
        value,
    )
    valid_path = False
    for raw_path in path_matches:
        candidate = Path(raw_path)
        resolved = candidate if candidate.is_absolute() else document.parent / candidate
        if not resolved.is_file():
            result.error(
                "missing-evidence-path",
                document,
                f"{context} cites missing internal file: {raw_path}.",
            )
        else:
            valid_path = True
    if external or command or valid_path:
        return True
    if not path_matches:
        result.error(
            "missing-direct-evidence",
            document,
            f"{context} needs existing file:symbol, command, or EXTERNO: evidence.",
        )
    return False


def _require_headings(
    result: ValidationResult, path: Path, text: str, required: tuple[str, ...]
) -> None:
    headings = _headings(text)
    for heading in required:
        if not _has_heading(headings, heading):
            result.error("missing-section", path, f"Missing required section: {heading}.")


def _read_artifact(result: ValidationResult, path: Path) -> tuple[str, str]:
    raw = path.read_text(encoding="utf-8-sig")
    comment_masked = _mask_html_comments(raw)
    html_masked = _mask_raw_html_blocks(comment_masked)
    nonsemantic_masked = _mask_indented_code(html_masked)
    masked = _mask_fenced(nonsemantic_masked)
    if raw.strip() and not masked.strip():
        result.error(
            "fenced-artifact",
            path,
            "Artifact content cannot exist only inside fenced, indented-code, or raw-HTML blocks.",
        )
    return nonsemantic_masked, masked


def _validate_asis(result: ValidationResult, path: Path) -> None:
    _, text = _read_artifact(result, path)
    result.validated.append(path.name)
    _require_headings(
        result,
        path,
        text,
        (
            "1. Stack Real",
            "2. Visao Geral E Fluxo De Referencia",
            "3. Modelo De Dominio",
            "4. Estrutura Real De Pastas",
            "5. Contratos De API",
            "6. Autenticacao E Autorizacao",
            "7. Regras De Camada",
            "8. Gerenciamento De Estado",
            "9. Requisitos Minimos De Plataforma",
            "10. Escalabilidade E Cache",
            "11. Gaps E Pontos De Atencao",
            "12. Catalogo Modular Observado",
            "13. Transacoes, Consistencia E Eventos Observados",
            "14. Patterns Observados",
        ),
    )
    if _plain(_metadata(text, "Fonte")) != "analise direta do codigo":
        result.error("invalid-source", path, "AS-IS must cite direct code analysis as source.")
    if not _valid_date(_metadata(text, "Data da analise")):
        result.error("invalid-date", path, "AS-IS must declare a real ISO analysis date.")
    if _plain(_metadata(text, "Horizonte")) != "as-is":
        result.error("invalid-horizon", path, "ARCHITECTURE.md horizon must be AS-IS.")

    module_tables = _find_tables(
        text,
        "ID",
        "Modulo real",
        "Responsabilidade",
        "API publica",
        "Dados/owner",
        "Invariantes",
        "Dono",
    )
    modules: set[str] = set()
    invariant_definitions: set[str] = set()
    if not module_tables:
        result.error("missing-module-catalog", path, "AS-IS module catalog is missing.")
    else:
        table = module_tables[0]
        invariant_col = _column(table, "Invariantes")
        for row_number, row in enumerate(_actual_rows(table), table.line + 2):
            identifier = row[0].strip()
            if not ID["MOD"].fullmatch(identifier):
                result.error(
                    "invalid-module-id",
                    path,
                    f"Invalid module ID {identifier!r}.",
                    row_number,
                )
                continue
            if identifier in modules:
                result.error(
                    "duplicate-module-definition",
                    path,
                    f"AS-IS module {identifier} is defined more than once.",
                    row_number,
                )
            else:
                modules.add(identifier)
            if any(_placeholder(cell) for cell in row[1:]):
                result.error("incomplete-module", path, f"Module {identifier} is incomplete.")
            if not ID["CON"].search(row[_column(table, "API publica")]):
                result.error("missing-public-contract", path, f"Module {identifier} lacks CON-NNN.")
            for invariant in ID["INV"].findall(row[invariant_col]):
                if invariant in invariant_definitions:
                    result.error(
                        "duplicate-invariant-definition",
                        path,
                        f"AS-IS invariant {invariant} is defined by more than one module row.",
                        row_number,
                    )
                else:
                    invariant_definitions.add(invariant)
    dependencies = _find_tables(text, "Origem", "Destino", "Tipo", "Evidencia", "Estado")
    if not dependencies or not _actual_rows(dependencies[0]):
        result.error("missing-dependencies", path, "AS-IS must enumerate dependencies.")
    else:
        table = dependencies[0]
        evidence_col = _column(table, "Evidencia")
        for row in _actual_rows(table):
            refs = set(ID["MOD"].findall(" ".join(row[:2])))
            if refs - modules:
                result.error(
                    "unknown-module", path, f"Dependency references unknown modules: {sorted(refs - modules)}."
                )
            _validate_evidence(
                result, path, row[evidence_col], f"Dependency {row[0]} -> {row[1]}"
            )
    gates = _find_tables(text, "Regra", "Gate")
    if not gates or not _actual_rows(gates[0]):
        result.error("missing-gates", path, "AS-IS layer rules need executable gates.")
    else:
        gate_col = _column(gates[0], "Gate")
        for row in _actual_rows(gates[0]):
            if _placeholder(row[gate_col]):
                result.error("placeholder-gate", path, "AS-IS contains a rule without a gate.")


def _party_valid(value: str, modules: set[str]) -> tuple[bool, set[str]]:
    refs = set(ID["MOD"].findall(value))
    unknown = refs - modules
    if unknown:
        return False, unknown
    if refs:
        return True, set()
    return bool(re.search(r"\b(?:EXTERNO|EXTERNAL)\s*:\s*\S", value, re.IGNORECASE)), set()


def _validate_dependency_table(
    result: ValidationResult,
    path: Path,
    table: Table,
    modules: set[str],
    policy: str,
) -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    gate_col = _column(table, "Gate")
    for row_number, row in enumerate(_actual_rows(table), table.line + 2):
        origin = set(ID["MOD"].findall(row[0]))
        destination = set(ID["MOD"].findall(row[1]))
        unknown = (origin | destination) - modules
        if not origin or not destination or unknown:
            result.error(
                "unknown-dependency-module",
                path,
                f"{policy} dependency must reference existing origin/destination modules; unknown={sorted(unknown)}.",
                row_number,
            )
        if _placeholder(row[gate_col]):
            result.error(
                "empty-dependency-gate",
                path,
                f"{policy} dependency requires a non-placeholder gate.",
                row_number,
            )
        if len(origin) == 1 and len(destination) == 1 and not unknown:
            edges.add((next(iter(origin)), next(iter(destination))))
    return edges


GRAPH_ARROW = re.compile(r"(?:-->|-\.->|==>|->)")


def _graph_edges(text: str) -> set[tuple[str, str]]:
    """Extract directed MOD edges from common Mermaid flowchart notation."""

    aliases: dict[str, str] = {}
    for line in text.splitlines():
        module_refs = ID["MOD"].findall(line)
        alias_match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*[\[({]", line)
        if alias_match and len(module_refs) == 1:
            aliases[alias_match.group(1)] = module_refs[0]

    def node(segment: str, prefer_last: bool) -> str | None:
        direct = ID["MOD"].findall(segment)
        if direct:
            return direct[-1] if prefer_last else direct[0]
        tokens = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", segment)
        candidates = [aliases[token] for token in tokens if token in aliases]
        if not candidates:
            return None
        return candidates[-1] if prefer_last else candidates[0]

    edges: set[tuple[str, str]] = set()
    for line in text.splitlines():
        if not GRAPH_ARROW.search(line):
            continue
        parts = GRAPH_ARROW.split(line)
        for left, right in zip(parts, parts[1:]):
            origin = node(left, prefer_last=True)
            destination = node(right, prefer_last=False)
            if origin and destination:
                edges.add((origin, destination))
    return edges


def _validate_target_traceability(
    result: ValidationResult,
    path: Path,
    text: str,
    modules: set[str],
    contracts: set[str],
    events: set[str],
) -> None:
    tables = _find_tables(
        text, "Requisito", "Modulo/contrato", "ADR", "Task", "Teste", "Evidencia"
    )
    if not tables or not _actual_rows(tables[0]):
        result.error("missing-traceability", path, "TO-BE traceability matrix is empty.")
        return
    known_architecture_ids = modules | contracts | events
    for row_number, row in enumerate(_actual_rows(tables[0]), tables[0].line + 2):
        architecture_refs = set(
            ID["MOD"].findall(row[1])
            + ID["CON"].findall(row[1])
            + ID["EVT"].findall(row[1])
        )
        checks = {
            "requirement": bool(ID["REQ"].search(row[0]) or ID["AC"].search(row[0]) or ID["NFR"].search(row[0])),
            "module/contract/event": bool(architecture_refs),
            "ADR/N/A": _adr_or_na(row[2]),
            "task": bool(ID["TASK"].search(row[3])),
            "test": bool(ID["TEST"].search(row[4])),
            "evidence": bool(ID["EVD"].search(row[5])),
        }
        missing = [label for label, present in checks.items() if not present]
        if missing:
            result.error(
                "broken-traceability",
                path,
                f"TO-BE traceability row misses: {', '.join(missing)}.",
                row_number,
            )
        unknown = architecture_refs - known_architecture_ids
        if unknown:
            result.error(
                "unknown-traceability-reference",
                path,
                f"TO-BE traceability references undefined architecture IDs: {sorted(unknown)}.",
                row_number,
            )


def _validate_target_patterns(
    result: ValidationResult,
    path: Path,
    text: str,
    modules: set[str],
    state: str,
) -> None:
    tables = _find_tables(
        text,
        "Pattern",
        "Presenca alvo",
        "Decisao atual",
        "Decisao alvo",
        "Modulos",
        "ADR",
        "Gate",
    )
    if not tables or not _actual_rows(tables[0]):
        result.error("missing-target-patterns", path, "TO-BE target pattern catalog is empty.")
        return

    table = tables[0]
    presence_col = _column(table, "Presenca alvo")
    current_col = _column(table, "Decisao atual")
    target_col = _column(table, "Decisao alvo")
    modules_col = _column(table, "Modulos")
    adr_col = _column(table, "ADR")
    gate_col = _column(table, "Gate")
    pattern_definitions: set[str] = set()
    for row_number, row in enumerate(_actual_rows(table), table.line + 2):
        identifier = row[0].strip()
        if not ID["PAT"].fullmatch(identifier):
            result.error(
                "invalid-target-pattern-id",
                path,
                f"Target pattern row needs PAT-NNN, got {identifier!r}.",
                row_number,
            )
        elif identifier in pattern_definitions:
            result.error(
                "duplicate-target-pattern-definition",
                path,
                f"TO-BE pattern {identifier} is defined more than once.",
                row_number,
            )
        else:
            pattern_definitions.add(identifier)
        presence = row[presence_col].strip()
        current = row[current_col].strip()
        target = row[target_col].strip()
        if presence not in TARGET_PATTERN_PRESENCES:
            result.error(
                "invalid-target-pattern-presence",
                path,
                f"{identifier} target presence {presence!r} is invalid.",
                row_number,
            )
        if current not in DECISIONS:
            result.error(
                "invalid-current-pattern-decision",
                path,
                f"{identifier} current decision {current!r} is invalid.",
                row_number,
            )
        if target not in TARGET_PATTERN_DECISIONS:
            result.error(
                "invalid-target-pattern-decision",
                path,
                f"{identifier} target decision {target!r} is invalid.",
                row_number,
            )
        if state == "RASCUNHO" and current != "PROPOSTO":
            result.error(
                "invalid-draft-pattern-decision",
                path,
                f"{identifier} must keep current decision PROPOSTO while TARGET is RASCUNHO.",
                row_number,
            )
        elif state in TARGET_STATES - {"RASCUNHO"} and current != target:
            result.error(
                "unaccepted-target-pattern-decision",
                path,
                f"{identifier} current and target decisions must match once TARGET is {state}.",
                row_number,
            )
        module_refs = set(ID["MOD"].findall(row[modules_col]))
        if not module_refs or module_refs - modules:
            result.error(
                "unknown-target-pattern-module",
                path,
                f"{identifier} must reference existing modules; unknown={sorted(module_refs - modules)}.",
                row_number,
            )
        if not _adr_or_na(row[adr_col]):
            result.error(
                "missing-target-pattern-adr",
                path,
                f"{identifier} needs ADR-NNN or justified N/A.",
                row_number,
            )
        if _placeholder(row[gate_col]):
            result.error(
                "missing-target-pattern-gate",
                path,
                f"{identifier} needs a non-placeholder gate.",
                row_number,
            )


def _validate_target(result: ValidationResult, path: Path) -> None:
    raw, text = _read_artifact(result, path)
    result.validated.append(path.name)
    _require_headings(
        result,
        path,
        text,
        (
            "1. Objetivo E Drivers",
            "2. Delta AS-IS -> TO-BE",
            "3. Catalogo Alvo De Modulos",
            "4. APIs Publicas, Contratos E Eventos",
            "5. Ownership De Dados E Invariantes",
            "6. Dependencias",
            "7. Grafo E Ciclos",
            "8. Transacoes, Consistencia E Eventos",
            "9. Patterns",
            "10. Evolucao, Rollout E Rollback",
            "11. Fitness Gates",
            "12. Rastreabilidade",
            "13. Lacunas E Decisoes Pendentes",
        ),
    )
    if _plain(_metadata(text, "Horizonte")) != "to-be":
        result.error("invalid-horizon", path, "TARGET_ARCHITECTURE.md horizon must be TO-BE.")
    if not _valid_date(_metadata(text, "Data")):
        result.error("invalid-date", path, "TO-BE must declare a real ISO date.")
    specs = _metadata(text, "Spec(s) de origem e estado") or _metadata(text, "Spec(s)")
    if not (ID["REQ"].search(specs) or ID["AC"].search(specs) or ID["NFR"].search(specs)):
        result.error("missing-requirement", path, "TO-BE must cite a concrete requirement.")
    adrs = _metadata(text, "ADR(s) aplicaveis") or _metadata(text, "ADR(s) obrigatorias")
    if not _adr_or_na(adrs):
        result.error("missing-adr", path, "TO-BE needs ADR-NNN or justified N/A.")
    asis_ref = _metadata(text, "AS-IS de referencia")
    if _plain(asis_ref).startswith("n/a"):
        if not _justified_na(asis_ref) or "greenfield" not in _plain(asis_ref):
            result.error(
                "invalid-greenfield-reference",
                path,
                "AS-IS N/A is allowed only with a concrete greenfield justification.",
            )
    elif not re.search(r"ARCHITECTURE\.md.*\d{4}-\d{2}-\d{2}", asis_ref, re.IGNORECASE):
        result.error("invalid-asis-reference", path, "TO-BE must cite dated ARCHITECTURE.md or greenfield N/A.")
    state = _metadata(text, "Estado").strip()
    if state not in TARGET_STATES:
        result.error(
            "invalid-target-state",
            path,
            f"TO-BE state must be one of {sorted(TARGET_STATES)}, got {state!r}.",
        )

    delta_tables = _find_tables(
        text, "ID", "AS-IS observado", "TO-BE", "Spec/ADR", "Task de transicao"
    )
    if not delta_tables or not _actual_rows(delta_tables[0]):
        result.error("missing-transition", path, "TO-BE must define transition deltas.")
    else:
        delta_definitions: set[str] = set()
        for row_number, row in enumerate(
            _actual_rows(delta_tables[0]), delta_tables[0].line + 2
        ):
            delta = row[0].strip()
            if not ID["DELTA"].fullmatch(delta):
                result.error("invalid-delta", path, "Transition rows need DELTA-NNN IDs.")
            elif delta in delta_definitions:
                result.error(
                    "duplicate-delta-definition",
                    path,
                    f"Transition {delta} is defined more than once.",
                    row_number,
                )
            else:
                delta_definitions.add(delta)
            if not (ID["REQ"].search(row[4]) or ID["AC"].search(row[4]) or ID["NFR"].search(row[4])):
                result.error("unauthorized-delta", path, f"{row[0]} must cite a requirement.")
            if not _adr_or_na(row[4]):
                result.error("unauthorized-delta", path, f"{row[0]} needs ADR-NNN or justified N/A.")
            if not ID["TASK"].search(row[5]):
                result.error("unplanned-delta", path, f"{row[0]} needs TASK-NNN.")

    module_tables = _find_tables(
        text, "ID", "Modulo", "Responsabilidade", "API publica", "Dados/owner", "Invariantes", "Dono"
    )
    modules: set[str] = set()
    module_contracts: set[str] = set()
    invariant_definitions: set[str] = set()
    if not module_tables or not _actual_rows(module_tables[0]):
        result.error("missing-target-modules", path, "Target module catalog is empty.")
    else:
        table = module_tables[0]
        invariant_col = _column(table, "Invariantes")
        for row_number, row in enumerate(_actual_rows(table), table.line + 2):
            identifier = row[0].strip()
            if not ID["MOD"].fullmatch(identifier):
                result.error(
                    "invalid-module-id",
                    path,
                    f"Invalid target module ID {identifier!r}.",
                    row_number,
                )
                continue
            if identifier in modules:
                result.error(
                    "duplicate-module-definition",
                    path,
                    f"Target module {identifier} is defined more than once.",
                    row_number,
                )
            else:
                modules.add(identifier)
            if any(_placeholder(cell) for cell in row[1:]):
                result.error("incomplete-target-module", path, f"Target module {identifier} is incomplete.")
            contracts = set(ID["CON"].findall(row[_column(table, "API publica")]))
            if not contracts:
                result.error("missing-target-public-contract", path, f"{identifier} lacks CON-NNN.")
            module_contracts.update(contracts)
            invariants = ID["INV"].findall(row[invariant_col])
            if not invariants:
                result.error("missing-target-invariant", path, f"{identifier} lacks INV-NNN.")
            for invariant in invariants:
                if invariant in invariant_definitions:
                    result.error(
                        "duplicate-invariant-definition",
                        path,
                        f"Target invariant {invariant} is defined by more than one module row.",
                        row_number,
                    )
                else:
                    invariant_definitions.add(invariant)

    contract_tables = _find_tables(
        text,
        "ID",
        "Tipo/protocolo",
        "Operacao/rota/topico",
        "Produtor/owner",
        "Consumidor",
        "Entrada/saida/schema",
        "Erros/semantica",
        "AuthN/AuthZ",
        "Versao/depreciacao",
        "Idempotencia/deduplicacao",
        "Compatibilidade",
        "Gate",
    )
    contracts: set[str] = set()
    events: set[str] = set()
    if not contract_tables or not _actual_rows(contract_tables[0]):
        result.error("missing-target-contracts", path, "TO-BE contract/event catalog is empty.")
    else:
        table = contract_tables[0]
        type_col = _column(table, "Tipo/protocolo")
        operation_col = _column(table, "Operacao/rota/topico")
        owner_col = _column(table, "Produtor/owner")
        consumer_col = _column(table, "Consumidor")
        auth_col = _column(table, "AuthN/AuthZ")
        for row_number, row in enumerate(_actual_rows(table), table.line + 2):
            identifier = row[0].strip()
            if ID["CON"].fullmatch(identifier):
                if identifier in contracts:
                    result.error(
                        "duplicate-contract-definition",
                        path,
                        f"Contract {identifier} is defined more than once.",
                        row_number,
                    )
                else:
                    contracts.add(identifier)
            elif ID["EVT"].fullmatch(identifier):
                if identifier in events:
                    result.error(
                        "duplicate-event-definition",
                        path,
                        f"Event {identifier} is defined more than once.",
                        row_number,
                    )
                else:
                    events.add(identifier)
            else:
                result.error("invalid-contract-id", path, f"Invalid CON/EVT ID {identifier!r}.", row_number)
            if any(_placeholder(cell) for cell in row[1:]):
                result.error("incomplete-contract", path, f"{identifier} has incomplete semantics.", row_number)
            if _placeholder(row[type_col]) or _placeholder(row[operation_col]):
                result.error(
                    "incomplete-contract-interface",
                    path,
                    f"{identifier} needs concrete protocol/type and operation/route/topic.",
                    row_number,
                )
            auth = row[auth_col]
            if ID["CON"].fullmatch(identifier) and _starts_with_na(auth):
                result.error(
                    "invalid-contract-auth",
                    path,
                    f"{identifier} must declare concrete AuthN/AuthZ; N/A is reserved for events.",
                    row_number,
                )
            elif ID["EVT"].fullmatch(identifier) and _starts_with_na(auth) and not _justified_na(auth):
                result.error(
                    "invalid-contract-auth",
                    path,
                    f"{identifier} may use AuthN/AuthZ N/A only with a concrete justification.",
                    row_number,
                )
            for label, value in (("owner/producer", row[owner_col]), ("consumer", row[consumer_col])):
                valid, unknown = _party_valid(value, modules)
                if not valid:
                    result.error(
                        "invalid-contract-party",
                        path,
                        f"{identifier} {label} must be an existing MOD or EXTERNO: label; unknown={sorted(unknown)}.",
                        row_number,
                    )
    undefined_public = module_contracts - contracts
    if undefined_public:
        result.error(
            "undefined-public-contract",
            path,
            f"Module catalog references undefined contracts: {sorted(undefined_public)}.",
        )

    ownership_tables = _find_tables(text, "Dado/entidade", "Modulo owner", "Invariantes", "Gate")
    if not ownership_tables or not _actual_rows(ownership_tables[0]):
        result.error("missing-data-ownership", path, "TO-BE data ownership table is empty.")
    else:
        table = ownership_tables[0]
        gate_col = _column(table, "Gate")
        for row in _actual_rows(table):
            refs = set(ID["MOD"].findall(" ".join(row)))
            if not refs or refs - modules:
                result.error("unknown-data-owner", path, "Data ownership references unknown module.")
            if not ID["INV"].search(" ".join(row)) or _placeholder(row[gate_col]):
                result.error("incomplete-data-ownership", path, "Data ownership needs invariant and gate.")

    dependency_section = _section(text, "6. Dependencias")
    permitted = _find_tables(_section(dependency_section, "Permitidas"), "Origem", "Destino", "Motivo", "Gate")
    prohibited = _find_tables(_section(dependency_section, "Proibidas"), "Origem", "Destino", "Motivo", "Gate")
    permitted_edges: set[tuple[str, str]] = set()
    if not permitted or not _actual_rows(permitted[0]):
        result.error("missing-permitted-dependency", path, "At least one permitted dependency is required.")
    else:
        permitted_edges = _validate_dependency_table(
            result, path, permitted[0], modules, "Permitted"
        )
    if not prohibited or not _actual_rows(prohibited[0]):
        result.error("missing-prohibited-dependency", path, "At least one prohibited dependency is required.")
    else:
        _validate_dependency_table(result, path, prohibited[0], modules, "Prohibited")

    graph_masked = _section(text, "7. Grafo E Ciclos")
    graph_raw = _section_raw(raw, text, "7. Grafo E Ciclos")
    graph_modules = set(ID["MOD"].findall(graph_raw))
    graph_edges = _graph_edges(graph_raw)
    if len(graph_modules) < 2 or not graph_edges:
        result.error("placeholder-graph", path, "TO-BE graph must contain a concrete module edge.")
    unknown_graph_modules = graph_modules - modules
    if unknown_graph_modules:
        result.error(
            "unknown-graph-module",
            path,
            f"TO-BE graph references modules absent from the catalog: {sorted(unknown_graph_modules)}.",
        )
    undeclared_edges = graph_edges - permitted_edges
    if undeclared_edges:
        result.error(
            "undeclared-graph-edge",
            path,
            f"TO-BE graph contains edges absent from dependency policy: {sorted(undeclared_edges)}.",
        )
    missing_edges = permitted_edges - graph_edges
    if missing_edges:
        result.error(
            "missing-graph-edge",
            path,
            f"Permitted dependencies absent from the TO-BE graph: {sorted(missing_edges)}.",
        )
    cycles = _metadata(graph_masked, "Ciclos permitidos")
    cycle_gate = _metadata(graph_masked, "Gate de deteccao")
    if _placeholder(cycles) or "|" in cycles:
        result.error("missing-cycle-policy", path, "TO-BE must explicitly declare cycle policy.")
    if _placeholder(cycle_gate):
        result.error("missing-cycle-gate", path, "TO-BE must define a cycle-detection gate.")

    transaction_tables = _find_tables(
        text,
        "Fluxo",
        "Limite transacional",
        "Consistencia",
        "Evento/efeito",
        "Ordenacao",
        "Idempotencia/retry",
        "DLQ/replay",
        "Compensacao/reconciliacao",
    )
    if not transaction_tables or not _actual_rows(transaction_tables[0]):
        result.error("missing-consistency-plan", path, "TO-BE consistency/event table is empty.")
    else:
        for row in _actual_rows(transaction_tables[0]):
            if any(_placeholder(cell) for cell in row):
                result.error("incomplete-consistency-plan", path, "Cross-module flow is incomplete.")
            for value in row:
                if _starts_with_na(value) and not _justified_na(value):
                    result.error(
                        "unjustified-consistency-na",
                        path,
                        "Consistency/event fields may use N/A only with a concrete justification.",
                    )
            if set(ID["MOD"].findall(" ".join(row))) - modules:
                result.error("unknown-transaction-module", path, "Transaction references unknown module.")
            event_refs = set(ID["EVT"].findall(" ".join(row)))
            if event_refs - events:
                result.error("unknown-event", path, f"Undefined events: {sorted(event_refs - events)}.")

    evolution = _find_tables(
        text, "Etapa", "Mudanca", "Compatibilidade", "Rollout/smoke", "Abort criterion", "Rollback/forward-fix"
    )
    if not evolution or not _actual_rows(evolution[0]):
        result.error("missing-safe-transition", path, "TO-BE rollout/rollback plan is empty.")
    else:
        rollback_col = _column(evolution[0], "Rollback/forward-fix")
        for row in _actual_rows(evolution[0]):
            if any(_placeholder(cell) for cell in row[1:]):
                result.error("incomplete-safe-transition", path, "Transition stage is incomplete.")
            if not re.search(r"rollback|forward-fix", row[rollback_col], re.IGNORECASE):
                result.error("missing-rollback", path, "Every transition needs rollback or forward-fix.")

    fitness = _find_tables(
        text, "Gate", "Comando/regra", "Frequencia", "Evidencia", "Resultado bloqueante", "Dono"
    )
    if not fitness or not _actual_rows(fitness[0]):
        result.error("missing-fitness-gates", path, "TO-BE fitness gates are empty.")
    else:
        fitness_definitions: set[str] = set()
        for row_number, row in enumerate(
            _actual_rows(fitness[0]), fitness[0].line + 2
        ):
            fitness_id = row[0].strip()
            if not ID["FIT"].fullmatch(fitness_id) or not ID["EVD"].search(row[3]):
                result.error("invalid-fitness-gate", path, "Fitness gate needs FIT-NNN and EVD-NNN.")
            elif fitness_id in fitness_definitions:
                result.error(
                    "duplicate-fitness-definition",
                    path,
                    f"Fitness gate {fitness_id} is defined more than once.",
                    row_number,
                )
            else:
                fitness_definitions.add(fitness_id)
            if any(_placeholder(cell) for cell in row[1:]):
                result.error("incomplete-fitness-gate", path, f"Fitness gate {row[0]} is incomplete.")
    _validate_target_patterns(result, path, text, modules, state)
    _validate_target_traceability(
        result, path, text, modules, contracts, events
    )


def _pattern_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^###\s+(PAT-\d{3})\b.*$", text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group(1), text[match.end() : end]))
    return blocks


def _validate_final_verdict(result: ValidationResult, path: Path, text: str) -> None:
    section = _section(text, "Veredito")
    candidates = [
        line.strip().strip("`")
        for line in section.splitlines()
        if re.fullmatch(r"[A-Z_]+", line.strip().strip("`"))
    ]
    if len(candidates) != 1 or candidates[0] not in VERDICTS:
        result.error("invalid-final-verdict", path, "Pattern Map must declare one canonical final verdict.")
        return
    verdict = candidates[0]
    if verdict == "APROVADO":
        audit = _section(text, "Auditoria De Consistencia")
        checklist = re.findall(
            r"(?m)^\s*[-*]\s*\[([ xX])\]\s+\S.+$",
            audit,
        )
        if not checklist or any(mark.lower() != "x" for mark in checklist):
            result.error(
                "incomplete-audit-checklist",
                path,
                "APROVADO requires every Pattern Map audit checklist item to be marked.",
            )
        justification = _metadata(section, "Justificativa")
        justification_words = re.findall(r"\b[\w-]{2,}\b", justification)
        concrete_justification = (
            not _placeholder(justification)
            and not _starts_with_na(justification)
            and "|" not in justification
            and "[" not in justification
            and len(justification.strip()) >= 15
            and len(justification_words) >= 3
        )
        if not concrete_justification:
            result.error(
                "missing-verdict-justification",
                path,
                "APROVADO requires a concrete justification with supporting rationale.",
            )
    elif verdict in {"QUESTIONAR", "REPROVADO"}:
        result.error(
            "blocking-final-verdict",
            path,
            f"Pattern Map final verdict {verdict} is blocking.",
        )
    elif verdict == "APROVADO_COM_RESSALVAS":
        gap = _metadata(section, "Lacuna nao bloqueante")
        action = _metadata(section, "Acao/dono/prazo")
        action_parts = [part.strip() for part in action.split("/")]
        deadline = re.search(r"\b\d{4}-\d{2}-\d{2}\b", action)
        concrete_gap = (
            not _placeholder(gap)
            and not _starts_with_na(gap)
            and "|" not in gap
            and "[" not in gap
        )
        concrete_action = (
            len(action_parts) >= 3
            and not _placeholder(action_parts[0])
            and not _placeholder(action_parts[1])
            and deadline is not None
            and _valid_date(deadline.group(0))
        )
        if not concrete_gap or not concrete_action:
            result.error(
                "incomplete-reservations",
                path,
                "APROVADO_COM_RESSALVAS needs a concrete nonblocking gap and action/owner/ISO deadline.",
            )


def _validate_pattern_adr(
    result: ValidationResult,
    path: Path,
    identifier: str,
    decision: str,
    materiality: str,
    adr: str,
    context: str,
) -> None:
    if materiality not in MATERIALITIES:
        result.error(
            "missing-pattern-materiality",
            path,
            f"{identifier} {context} must declare Trade-off material as SIM or NAO.",
        )
        if decision in NORMATIVE_DECISIONS and not ID["ADR"].search(adr):
            result.error(
                "missing-pattern-adr",
                path,
                f"Normative decision {identifier} needs ADR-NNN unless materiality is explicitly NAO.",
            )
        return
    if materiality == "SIM" and not ID["ADR"].search(adr):
        result.error(
            "missing-pattern-adr",
            path,
            f"Material pattern decision {identifier} needs ADR-NNN.",
        )
    elif materiality == "NAO" and not _adr_or_na(adr):
        result.error(
            "invalid-pattern-adr-na",
            path,
            f"Non-material pattern {identifier} needs ADR-NNN or a justified N/A.",
        )


def _validate_pattern(result: ValidationResult, path: Path) -> None:
    _, text = _read_artifact(result, path)
    result.validated.append(path.name)
    _require_headings(
        result, path, text, ("Catalogo", "Registro Detalhado", "Auditoria De Consistencia", "Veredito")
    )
    if not _valid_date(_metadata(text, "Data da auditoria")):
        result.error("invalid-date", path, "PATTERN_MAP needs a real ISO audit date.")
    for label in ("Escopo", "Dono"):
        if _placeholder(_metadata(text, label)):
            result.error("missing-metadata", path, f"PATTERN_MAP missing concrete {label}.")
    asis = _metadata(text, "AS-IS")
    if _starts_with_na(asis):
        if not _justified_na(asis) or "greenfield" not in _plain(asis):
            result.error(
                "invalid-pattern-asis",
                path,
                "PATTERN_MAP AS-IS N/A requires a concrete greenfield justification.",
            )
    elif _placeholder(asis):
        result.error("missing-metadata", path, "PATTERN_MAP missing concrete AS-IS.")

    catalog_tables = _find_tables(
        text, "ID", "Pattern", "Presenca", "Decisao", "Escopo", "Evidencia", "ADR", "Gate", "Dono"
    )
    catalog: dict[str, tuple[str, str, str, str, bool]] = {}
    if not catalog_tables:
        result.error("missing-pattern-catalog", path, "Pattern catalog table is missing.")
    else:
        table = catalog_tables[0]
        presence_col = _column(table, "Presenca")
        decision_col = _column(table, "Decisao")
        evidence_col = _column(table, "Evidencia")
        adr_col = _column(table, "ADR")
        gate_col = _column(table, "Gate")
        material_columns = [
            index
            for index, header in enumerate(table.headers)
            if "trade-off material" in _plain(header)
        ]
        material_col = material_columns[0] if material_columns else None
        for row in _actual_rows(table):
            identifier = row[0].strip()
            if not ID["PAT"].fullmatch(identifier):
                result.error("invalid-pattern-id", path, f"Invalid pattern ID {identifier!r}.")
                continue
            if identifier in catalog:
                result.error("duplicate-pattern", path, f"Duplicate pattern {identifier}.")
                continue
            presence = row[presence_col].strip()
            decision = row[decision_col].strip()
            adr = row[adr_col].strip()
            explicit_materiality = material_col is not None
            materiality = (
                row[material_col].strip()
                if material_col is not None
                else ("SIM" if ID["ADR"].search(adr) else "")
            )
            catalog[identifier] = (
                presence,
                decision,
                materiality,
                adr,
                explicit_materiality,
            )
            if presence not in PRESENCES:
                result.error("invalid-pattern-presence", path, f"{identifier} presence {presence!r} is invalid.")
            if decision not in DECISIONS:
                result.error("invalid-pattern-decision", path, f"{identifier} decision {decision!r} is invalid.")
            if decision == "DEPRECIADO" and presence not in {"OBSERVADO", "PARCIAL"}:
                result.error("invalid-deprecation-presence", path, f"{identifier} deprecated decision needs observed/partial presence.")
            _validate_pattern_adr(
                result,
                path,
                identifier,
                decision,
                materiality,
                adr,
                "catalog",
            )
            _validate_evidence(result, path, row[evidence_col], f"Pattern {identifier}")
            if _placeholder(row[gate_col]):
                result.error("missing-pattern-gate", path, f"{identifier} lacks a catalog gate.")

    blocks = _pattern_blocks(text)
    block_ids = [identifier for identifier, _ in blocks]
    seen_block_ids: set[str] = set()
    for identifier in block_ids:
        if identifier in seen_block_ids:
            result.error(
                "duplicate-pattern-detail",
                path,
                f"Detailed block {identifier} is defined more than once.",
            )
        else:
            seen_block_ids.add(identifier)
    if set(block_ids) != set(catalog):
        result.error(
            "pattern-detail-mismatch",
            path,
            f"Catalog/detail mismatch: catalog={sorted(catalog)}, detail={sorted(set(block_ids))}.",
        )
    required_sections = (
        "Evidencia",
        "Problema E Forcas",
        "Solucao",
        "Alternativas",
        "Contraindicacoes",
        "Trade-offs",
        "ADR E Evolucao",
        "Gate",
    )
    for identifier, block in blocks:
        presence = _metadata(block, "Presenca")
        decision = _metadata(block, "Decisao")
        evolution = _section(block, "ADR E Evolucao")
        adr = _metadata(evolution, "ADR")
        materiality = _metadata(block, "Trade-off material").strip()
        explicit_detail_materiality = materiality in MATERIALITIES
        if not explicit_detail_materiality and ID["ADR"].search(adr):
            materiality = "SIM"
        if presence not in PRESENCES:
            result.error("invalid-pattern-presence", path, f"{identifier} detail presence is invalid.")
        if decision not in DECISIONS:
            result.error("invalid-pattern-decision", path, f"{identifier} detail decision is invalid.")
        if identifier in catalog:
            catalog_presence, catalog_decision, catalog_materiality, _, catalog_explicit = catalog[
                identifier
            ]
            if (catalog_presence, catalog_decision) != (presence, decision):
                result.error(
                    "pattern-state-mismatch",
                    path,
                    f"{identifier} catalog/detail presence or decision differs.",
                )
            if catalog_materiality != materiality:
                result.error(
                    "pattern-materiality-mismatch",
                    path,
                    f"{identifier} catalog/detail materiality differs.",
                )
            if catalog_explicit and not explicit_detail_materiality:
                result.error(
                    "missing-pattern-materiality",
                    path,
                    f"{identifier} detail must explicitly declare Trade-off material.",
                )
        if decision == "DEPRECIADO" and presence not in {"OBSERVADO", "PARCIAL"}:
            result.error("invalid-deprecation-presence", path, f"{identifier} deprecated decision needs observed/partial presence.")
        if _placeholder(_metadata(block, "Escopo")):
            result.error("missing-pattern-scope", path, f"{identifier} lacks concrete scope.")
        headings = _headings(block)
        for heading in required_sections:
            if not _has_heading(headings, heading):
                result.error("missing-pattern-section", path, f"{identifier} missing {heading}.")

        evidence = _section(block, "Evidencia")
        _validate_evidence(result, path, evidence, f"Pattern detail {identifier}")
        forces = _section(block, "Problema E Forcas")
        if _placeholder(_metadata(forces, "Problema")) or _placeholder(_metadata(forces, "Forcas/tensoes")):
            result.error("missing-pattern-forces", path, f"{identifier} lacks problem or forces.")
        contraindications = _section(block, "Contraindicacoes")
        if _placeholder(_metadata(contraindications, "Nao usar quando")):
            result.error("missing-contraindications", path, f"{identifier} lacks contraindications.")
        tradeoffs = _section(block, "Trade-offs")
        if _placeholder(_metadata(tradeoffs, "Beneficios aceitos")) or _placeholder(_metadata(tradeoffs, "Custos/riscos aceitos")):
            result.error("missing-tradeoffs", path, f"{identifier} lacks explicit trade-offs.")
        alternatives = _find_tables(
            _section(block, "Alternativas"), "Alternativa", "Beneficios", "Custos", "Motivo"
        )
        if not alternatives or not _actual_rows(alternatives[0]):
            result.error("missing-alternatives", path, f"{identifier} lacks alternative comparison.")
        gates = _find_tables(
            _section(block, "Gate"), "Regra/comando", "Frequencia", "Evidencia esperada", "Falha bloqueia"
        )
        if not gates or not _actual_rows(gates[0]):
            result.error("missing-pattern-gate", path, f"{identifier} lacks an executable gate.")
        else:
            row = _actual_rows(gates[0])[0]
            if _placeholder(row[0]) or not ID["EVD"].search(row[2]):
                result.error("invalid-pattern-gate", path, f"{identifier} gate needs rule and EVD-NNN.")
            if decision == "PROIBIDO" and _plain(row[3]) != "sim":
                result.error("nonblocking-prohibition", path, f"{identifier} is prohibited but gate is nonblocking.")
        _validate_pattern_adr(
            result,
            path,
            identifier,
            decision,
            materiality,
            adr,
            "detail",
        )
        if decision == "DEPRECIADO" and any(
            _placeholder(_metadata(evolution, label))
            for label in ("Plano de migracao/remocao", "Dono/prazo")
        ):
            result.error("incomplete-deprecation", path, f"{identifier} lacks migration owner/deadline.")
    _validate_final_verdict(result, path, text)


def validate_architecture(path: str | Path) -> ValidationResult:
    target = Path(path).resolve()
    result = ValidationResult(str(target))
    if target.is_file():
        kind = target.name.upper()
        if kind == "ARCHITECTURE.MD":
            _validate_asis(result, target)
        elif kind == "TARGET_ARCHITECTURE.MD":
            _validate_target(result, target)
        elif kind == "PATTERN_MAP.MD":
            _validate_pattern(result, target)
        else:
            result.error(
                "unsupported-file",
                target,
                "Expected ARCHITECTURE.md, TARGET_ARCHITECTURE.md, or PATTERN_MAP.md.",
            )
        return result

    canonical = ("ARCHITECTURE.MD", "TARGET_ARCHITECTURE.MD", "PATTERN_MAP.MD")
    files = {name: target / name for name in canonical}
    if target.is_dir():
        files = {
            name: next((item for item in target.iterdir() if item.name.upper() == name), fallback)
            for name, fallback in files.items()
        }
    architecture = files["ARCHITECTURE.MD"]
    target_architecture = files["TARGET_ARCHITECTURE.MD"]
    pattern_map = files["PATTERN_MAP.MD"]
    has_target = target_architecture.is_file()
    if architecture.is_file():
        _validate_asis(result, architecture)
    elif has_target:
        target_text = _mask_fenced(
            _mask_indented_code(
                _mask_raw_html_blocks(
                    _mask_html_comments(
                        target_architecture.read_text(encoding="utf-8-sig")
                    )
                )
            )
        )
        greenfield = _metadata(target_text, "AS-IS de referencia")
        if not (_justified_na(greenfield) and "greenfield" in _plain(greenfield)):
            result.error("missing-asis", target, "Missing AS-IS requires explicit greenfield N/A in TO-BE.")
        else:
            result.warning("missing-asis", target, "Greenfield target has no observable AS-IS.")
    else:
        result.error("missing-architecture", target, "Provide AS-IS, TO-BE, or both.")
    if has_target:
        _validate_target(result, target_architecture)
    elif target.is_dir():
        result.warning("missing-tobe", target, "No TARGET_ARCHITECTURE.md to validate.")
    if pattern_map.is_file():
        _validate_pattern(result, pattern_map)
    elif target.is_dir():
        result.warning("missing-pattern-map", target, "No PATTERN_MAP.md to validate.")
    return result


def _print_human(result: ValidationResult) -> None:
    print(f"Architecture governance validation: {'OK' if result.ok else 'FAILED'}")
    print(f"Root: {result.root}")
    print(f"Validated: {', '.join(result.validated) or 'none'}")
    for issue in result.errors:
        suffix = f":{issue.line}" if issue.line else ""
        print(f"ERROR [{issue.code}] {issue.path}{suffix}: {issue.message}")
    for issue in result.warnings:
        suffix = f":{issue.line}" if issue.line else ""
        print(f"WARNING [{issue.code}] {issue.path}{suffix}: {issue.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".", help="architecture directory or file")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    result = validate_architecture(args.path)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_human(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
