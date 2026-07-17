#!/usr/bin/env python3
"""Validate Codex Agent Kit runtime and catalog coherence.

The validator treats ``AGENT_RUNTIME_MAP.toml`` as the exhaustive runtime
manifest and original agent files as behavioral sources of truth. It checks:

- manifest coverage and uniqueness for every custom agent and runtime skill;
- Codex TOML shape, filename/name parity, complete-source reading requirement,
  exact manifest source references, and source existence;
- Claude wrapper set, metadata, body, and source-reference parity with Codex;
- skill frontmatter, UI metadata, declared paths, and concrete internal links;
- canonical Harness verdict vocabulary in the configured contract files;
- git versioning, remote presence, and working-tree state.
"""

from __future__ import annotations

import json
import re
import stat
import subprocess
import sys
import tomllib
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


SUPPORTED_RUNTIME_SCHEMA = 1
SEMVER_RE = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$")
CANONICAL_VERDICTS = {
    "APROVADO",
    "APROVADO_COM_RESSALVAS",
    "QUESTIONAR",
    "REPROVADO",
}
FULL_SOURCE_INSTRUCTION = (
    "Before acting, read the selected source file completely; "
    "do not rely on this wrapper as a substitute."
)
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
BACKTICK_PATH_RE = re.compile(
    r"`([^`\r\n]+?\.(?:md|toml|py|ya?ml))`", re.IGNORECASE
)
PATH_ERROR_OUTSIDE_ROOT = "path-outside-kit-root"
PATH_ERROR_BROKEN_REPARSE = "broken-symlink-or-reparse-point"


def _mask_nonsemantic_markdown(text: str) -> str:
    """Remove comments, fenced blocks, and indented code from policy parsing."""

    def blank(match: re.Match[str]) -> str:
        return "".join("\n" if char == "\n" else " " for char in match.group(0))

    text = re.sub(r"<!--.*?(?:-->|\Z)", blank, text, flags=re.DOTALL)
    text = re.sub(r"<\?.*?(?:\?>|\Z)", blank, text, flags=re.DOTALL)
    text = re.sub(r"<!\[CDATA\[.*?(?:\]\]>|\Z)", blank, text, flags=re.DOTALL)
    text = re.sub(r"<![A-Za-z].*?(?:>|\Z)", blank, text, flags=re.DOTALL)
    output: list[str] = []
    fence_char = ""
    fence_size = 0
    html_tag = ""
    html_depth = 0
    void_tags = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }
    for line in text.splitlines(keepends=True):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if not fence_char and match:
            token = match.group(1)
            fence_char, fence_size = token[0], len(token)
            output.append("\n" if line.endswith("\n") else "")
            continue
        if fence_char:
            if match and match.group(1)[0] == fence_char and len(match.group(1)) >= fence_size:
                fence_char, fence_size = "", 0
            output.append("\n" if line.endswith("\n") else "")
            continue
        if html_tag:
            openings = len(
                re.findall(rf"<\s*{re.escape(html_tag)}\b(?![^>]*?/\s*>)", line, re.IGNORECASE)
            )
            closings = len(
                re.findall(rf"</\s*{re.escape(html_tag)}\s*>", line, re.IGNORECASE)
            )
            html_depth += openings - closings
            if html_depth <= 0:
                html_tag, html_depth = "", 0
            output.append("\n" if line.endswith("\n") else "")
            continue
        html_open = re.match(r"^ {0,3}<([A-Za-z][A-Za-z0-9:-]*)\b[^>]*>", line)
        if html_open:
            tag = html_open.group(1).lower()
            same_line_close = bool(re.search(rf"</\s*{re.escape(tag)}\s*>", line, re.IGNORECASE))
            # HTML ignores XML-style '/>' on non-void elements such as div.
            self_closing = tag in void_tags
            if not same_line_close and not self_closing:
                html_tag, html_depth = tag, 1
            output.append("\n" if line.endswith("\n") else "")
            continue
        html_pending = re.match(
            r"^ {0,3}<([A-Za-z][A-Za-z0-9:-]*)(?:\s.*)?$", line.rstrip("\r\n")
        )
        if html_pending and ">" not in line:
            html_tag, html_depth = html_pending.group(1).lower(), 1
            output.append("\n" if line.endswith("\n") else "")
            continue
        if line.startswith(("    ", "\t")):
            output.append("\n" if line.endswith("\n") else "")
        else:
            output.append(line)
    return "".join(output)


def _simple_yaml_fields(text: str) -> dict[str, str]:
    """Parse the scalar top-level fields used by agents/openai.yaml."""

    fields: dict[str, str] = {}
    parent = ""
    for line in text.splitlines():
        top_level = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(?:#.*)?$", line)
        if top_level:
            parent = top_level.group(1)
            continue
        match = re.match(
            r"^ {2}(display_name|short_description|default_prompt):\s*(.*?)\s*$",
            line,
        )
        if not match or parent != "interface":
            continue
        value = match.group(2).strip()
        if value.startswith(("'", '"')) and len(value) >= 2 and value[-1] == value[0]:
            value = value[1:-1]
        else:
            value = re.sub(r"\s+#.*$", "", value).strip()
        fields[match.group(1)] = value
    return fields


def _kit_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_reparse(path: Path) -> bool:
    """Identify symlinks and Windows reparse points, including broken links."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return path.is_symlink()
    return path.is_symlink() or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _validate_governed_path(
    kit: Path,
    value: str,
    label: str,
    errors: list[str],
    *,
    must_exist: bool = True,
    expect_file: bool | None = None,
    strip_installed_prefix: bool = True,
) -> Path | None:
    """Resolve an untrusted kit-relative path without allowing root escape."""
    raw = value.strip().strip("<>").replace("\\", "/")
    windows = PureWindowsPath(raw)
    if not raw or "\x00" in raw:
        errors.append(f"{label}: path is empty.")
        return None
    if (
        PurePosixPath(raw).is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
    ):
        errors.append(f"{label}: absolute paths are forbidden: {value!r}.")
        return None
    raw_parts = PurePosixPath(raw).parts
    if any(
        part == ".." or (not part.rstrip(" .") and part.count(".") >= 2)
        for part in raw_parts
    ):
        errors.append(f"{label}: parent traversal is forbidden: {value!r}.")
        return None

    normalized = _normalize_kit_path(raw) if strip_installed_prefix else raw
    normalized_windows = PureWindowsPath(normalized)
    if (
        PurePosixPath(normalized).is_absolute()
        or normalized_windows.is_absolute()
        or bool(normalized_windows.drive)
    ):
        errors.append(f"{label}: normalized path is absolute: {value!r}.")
        return None
    parts = PurePosixPath(normalized).parts
    if (
        not normalized
        or any(
            part == ".." or (not part.rstrip(" .") and part.count(".") >= 2)
            for part in parts
        )
        or any(":" in part for part in parts)
    ):
        errors.append(f"{label}: invalid governed path: {value!r}.")
        return None
    candidate = kit / Path(*parts)
    root = kit.resolve(strict=True)
    try:
        relative = candidate.relative_to(kit)
    except ValueError:
        errors.append(
            f"{label} [{PATH_ERROR_OUTSIDE_ROOT}]: path is outside kit root: {value!r}."
        )
        return None

    # Classify each link before resolving the complete candidate.  On Windows,
    # resolving a dangling reparse point first can produce a misleading root-
    # escape result; on POSIX, an external symlink otherwise bypasses the more
    # specific reparse diagnostic.  The final resolved-path check below remains
    # a fail-closed defense against link chains and changes during validation.
    current = kit
    for part in relative.parts:
        current /= part
        if not _is_reparse(current):
            continue
        if not current.exists():
            errors.append(
                f"{label} [{PATH_ERROR_BROKEN_REPARSE}]: "
                f"broken symlink/reparse point: {current}."
            )
            return None
        target = current.resolve(strict=True)
        try:
            target.relative_to(root)
        except ValueError:
            errors.append(
                f"{label} [{PATH_ERROR_OUTSIDE_ROOT}]: symlink/reparse point "
                f"resolves outside kit root: {current}."
            )
            return None

    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError:
        errors.append(
            f"{label} [{PATH_ERROR_OUTSIDE_ROOT}]: resolved path is outside "
            f"kit root: {value!r}."
        )
        return None

    if must_exist and not candidate.exists():
        errors.append(f"{label}: path does not exist: {normalized}.")
        return None
    if must_exist and expect_file is True and not candidate.is_file():
        errors.append(f"{label}: expected a regular file: {normalized}.")
        return None
    if must_exist and expect_file is False and not candidate.is_dir():
        errors.append(f"{label}: expected a directory: {normalized}.")
        return None
    return candidate


def _validate_existing_path(
    kit: Path,
    path: Path,
    label: str,
    errors: list[str],
    *,
    expect_file: bool | None = None,
) -> bool:
    try:
        relative = path.relative_to(kit).as_posix()
    except ValueError:
        errors.append(f"{label}: path is outside kit root: {path}.")
        return False
    return (
        _validate_governed_path(
            kit,
            relative,
            label,
            errors,
            expect_file=expect_file,
            strip_installed_prefix=False,
        )
        is not None
    )


def _read_toml(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{path}: invalid TOML: {exc}")
        return {}


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n?", text, re.DOTALL)
    if not match:
        return {}, text
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        value = raw.strip()
        if value.startswith(('"', "'")):
            try:
                parsed = json.loads(value) if value.startswith('"') else value[1:-1]
                value = str(parsed)
            except json.JSONDecodeError:
                value = value.strip('"').strip("'")
        result[key.strip()] = value
    return result, text[match.end() :]


def _normalize_kit_path(value: str) -> str:
    normalized = value.strip().strip("<>").replace("\\", "/")
    if normalized.startswith(".codex/"):
        normalized = normalized[len(".codex/") :]
    return normalized


def _concrete_backtick_paths(text: str) -> list[str]:
    found: list[str] = []
    for match in BACKTICK_PATH_RE.findall(text):
        value = _normalize_kit_path(match)
        if any(char in value for char in ("*", "<", ">", "$", "{", "}")):
            continue
        found.append(value)
    return found


def _manifest_indexes(
    kit: Path, manifest: dict[str, Any], errors: list[str]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    agents: dict[str, dict[str, Any]] = {}
    for entry in manifest.get("agents", []):
        if not isinstance(entry, dict):
            errors.append("Manifest [[agents]] entry must be a table.")
            continue
        name = str(entry.get("name", "")).strip()
        source_raw = str(entry.get("source", ""))
        source = _normalize_kit_path(source_raw)
        alias = str(entry.get("alias", "")).strip()
        purpose = str(entry.get("purpose", "")).strip()
        if not NAME_RE.fullmatch(name):
            errors.append(f"Manifest agent has invalid name: {name!r}.")
            continue
        if name in agents:
            errors.append(f"Manifest agent duplicated: {name}.")
            continue
        for key, value in (("source", source), ("alias", alias), ("purpose", purpose)):
            if not value:
                errors.append(f"Manifest agent {name}: missing {key}.")
        if source:
            _validate_governed_path(
                kit,
                source_raw,
                f"Manifest agent {name} source",
                errors,
                expect_file=True,
            )
        agents[name] = dict(entry, source=source)

    skills: dict[str, dict[str, Any]] = {}
    for entry in manifest.get("skills", []):
        if not isinstance(entry, dict):
            errors.append("Manifest [[skills]] entry must be a table.")
            continue
        name = str(entry.get("name", "")).strip()
        path_raw = str(entry.get("path", ""))
        path = _normalize_kit_path(path_raw)
        purpose = str(entry.get("purpose", "")).strip()
        if not NAME_RE.fullmatch(name):
            errors.append(f"Manifest skill has invalid name: {name!r}.")
            continue
        if name in skills:
            errors.append(f"Manifest skill duplicated: {name}.")
            continue
        if not path or not purpose:
            errors.append(f"Manifest skill {name}: path and purpose are required.")
        expected_path = f"skills/{name}/SKILL.md"
        if path and path != expected_path:
            errors.append(
                f"Manifest skill {name}: path must be exactly {expected_path!r}."
            )
        if path:
            _validate_governed_path(
                kit,
                path_raw,
                f"Manifest skill {name} path",
                errors,
                expect_file=True,
            )
        skills[name] = dict(entry, path=path)

    skill_root = kit / "skills"
    actual_skill_names = {
        path.parent.name
        for path in skill_root.glob("*/SKILL.md")
        if path.is_file()
    }
    manifest_skill_names = set(skills)
    if manifest_skill_names != actual_skill_names:
        missing = sorted(actual_skill_names - manifest_skill_names)
        extra = sorted(manifest_skill_names - actual_skill_names)
        if missing:
            errors.append(f"Manifest missing canonical runtime skills: {missing}.")
        if extra:
            errors.append(f"Manifest references absent runtime skills: {extra}.")
    return agents, skills


def validate_runtime_metadata(
    kit: Path, manifest: dict[str, Any], errors: list[str]
) -> None:
    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict):
        errors.append("Manifest is missing the [runtime] table.")
        return

    if runtime.get("schema_version") != SUPPORTED_RUNTIME_SCHEMA:
        errors.append(
            "Manifest runtime.schema_version must be "
            f"{SUPPORTED_RUNTIME_SCHEMA}, got {runtime.get('schema_version')!r}."
        )
    kit_version = str(runtime.get("kit_version", "")).strip()
    if not SEMVER_RE.fullmatch(kit_version):
        errors.append("Manifest runtime.kit_version must be SemVer MAJOR.MINOR.PATCH.")
    release_date = str(runtime.get("release_date", "")).strip()
    try:
        date.fromisoformat(release_date)
    except ValueError:
        errors.append("Manifest runtime.release_date must be a valid ISO date.")
    if str(runtime.get("python_requires", "")).strip() != ">=3.11":
        errors.append("Manifest runtime.python_requires must be '>=3.11'.")
    supported_os = runtime.get("supported_os")
    if not isinstance(supported_os, list) or not {"linux", "windows"}.issubset(
        {str(value).strip().lower() for value in supported_os}
    ):
        errors.append(
            "Manifest runtime.supported_os must include both 'linux' and 'windows'."
        )

    coverage_map = str(runtime.get("coverage_map", "")).strip()
    if not coverage_map:
        errors.append("Manifest runtime.coverage_map is required.")
    else:
        _validate_governed_path(
            kit,
            coverage_map,
            "Manifest runtime.coverage_map",
            errors,
            expect_file=True,
        )


def _validate_wrapper_source_contract(
    kit: Path,
    label: str,
    instructions: str,
    source: str,
    errors: list[str],
) -> None:
    if FULL_SOURCE_INSTRUCTION not in instructions:
        errors.append(f"{label}: does not require complete source reading before acting.")
    installed = f"`.codex/{source}`"
    local = f"`{source}`"
    if installed not in instructions:
        errors.append(f"{label}: missing installed-kit source reference {installed}.")
    if local not in instructions:
        errors.append(f"{label}: missing kit-root source reference {local}.")
    references = set(_concrete_backtick_paths(instructions))
    if source not in references:
        errors.append(f"{label}: manifest source is not referenced: {source}.")
    roots = _known_kit_roots(kit)
    for reference in references:
        first = reference.split("/", 1)[0]
        if reference != source and first not in roots:
            # Wrappers may name artifacts they create in a target project.
            continue
        if _validate_governed_path(
            kit,
            reference,
            f"{label} referenced source/path",
            errors,
        ) is None:
            errors.append(f"{label}: referenced source/path does not exist: {reference}.")


def validate_codex_wrappers(
    kit: Path, agents: dict[str, dict[str, Any]], errors: list[str]
) -> tuple[int, dict[str, dict[str, str]]]:
    folder = kit / ".codex" / "agents"
    if not _validate_existing_path(
        kit, folder, "Codex wrapper directory", errors, expect_file=False
    ):
        return 0, {}
    files = sorted(folder.glob("*.toml"))
    wrappers: dict[str, dict[str, str]] = {}
    if not files:
        errors.append("No Codex wrappers found in .codex/agents.")
        return 0, wrappers

    for path in files:
        relative = path.relative_to(kit).as_posix()
        if not _validate_existing_path(
            kit, path, f"Codex wrapper {relative}", errors, expect_file=True
        ):
            continue
        data = _read_toml(path, errors)
        name = str(data.get("name", "")).strip()
        description = str(data.get("description", "")).strip()
        instructions = str(data.get("developer_instructions", "")).strip()
        for key, value in (
            ("name", name),
            ("description", description),
            ("developer_instructions", instructions),
        ):
            if not value:
                errors.append(f"{relative}: missing {key}.")
        if not name:
            continue
        if not NAME_RE.fullmatch(name):
            errors.append(f"{relative}: invalid wrapper name {name!r}.")
        if path.stem != name:
            errors.append(f"{relative}: filename must match name {name!r}.")
        if name in wrappers:
            errors.append(f"Duplicate Codex wrapper name: {name}.")
            continue
        wrappers[name] = {
            "name": name,
            "description": description,
            "developer_instructions": instructions,
        }
        entry = agents.get(name)
        if entry is None:
            errors.append(f"{relative}: absent from manifest [[agents]].")
            continue
        _validate_wrapper_source_contract(
            kit, relative, instructions, str(entry["source"]), errors
        )

    file_names = set(wrappers)
    manifest_names = set(agents)
    if file_names != manifest_names:
        missing = sorted(manifest_names - file_names)
        extra = sorted(file_names - manifest_names)
        if missing:
            errors.append(f"Codex wrappers missing for manifest agents: {missing}.")
        if extra:
            errors.append(f"Codex wrappers not declared in manifest: {extra}.")
    return len(files), wrappers


def _render_expected_claude(data: dict[str, str]) -> str:
    description = json.dumps(data["description"], ensure_ascii=False)
    instructions = data["developer_instructions"].replace(
        "Codex wrapper", "Claude Code wrapper"
    )
    return (
        "---\n"
        f"name: {data['name']}\n"
        f"description: {description}\n"
        "---\n\n"
        f"{instructions}\n"
    )


def validate_claude_wrappers(
    kit: Path,
    agents: dict[str, dict[str, Any]],
    codex: dict[str, dict[str, str]],
    errors: list[str],
) -> int:
    folder = kit / ".claude" / "agents"
    if not _validate_existing_path(
        kit, folder, "Claude wrapper directory", errors, expect_file=False
    ):
        return 0
    files = sorted(folder.glob("*.md"))
    if not files:
        errors.append("No Claude wrappers found in .claude/agents.")
        return 0

    found: set[str] = set()
    for path in files:
        relative = path.relative_to(kit).as_posix()
        if not _validate_existing_path(
            kit, path, f"Claude wrapper {relative}", errors, expect_file=True
        ):
            continue
        text = path.read_text(encoding="utf-8-sig")
        fm, body = _frontmatter(text)
        name = fm.get("name", "").strip()
        description = fm.get("description", "").strip()
        for key, value in (("name", name), ("description", description)):
            if not value:
                errors.append(f"{relative}: missing frontmatter {key}.")
        if name:
            if path.stem != name:
                errors.append(f"{relative}: filename must match name {name!r}.")
            if name in found:
                errors.append(f"Duplicate Claude wrapper name: {name}.")
            found.add(name)
        source_data = codex.get(name)
        if source_data is None:
            errors.append(f"{relative}: has no matching Codex wrapper.")
            continue
        if description != source_data["description"]:
            errors.append(f"{relative}: description differs from Codex wrapper.")
        expected_body = source_data["developer_instructions"].replace(
            "Codex wrapper", "Claude Code wrapper"
        )
        if body.strip() != expected_body.strip():
            errors.append(f"{relative}: instructions differ from generated Codex parity.")
        entry = agents.get(name)
        if entry is not None:
            _validate_wrapper_source_contract(
                kit, relative, body, str(entry["source"]), errors
            )
        expected = _render_expected_claude(source_data)
        if text != expected:
            errors.append(
                f"{relative}: generated bytes are stale; run "
                "python RUNTIME_Bridge/scripts/sync_claude_from_codex.py."
            )

    expected_names = set(codex)
    if found != expected_names:
        missing = sorted(expected_names - found)
        extra = sorted(found - expected_names)
        if missing:
            errors.append(f"Claude wrappers missing for Codex agents: {missing}.")
        if extra:
            errors.append(f"Claude wrappers without Codex counterparts: {extra}.")
    return len(files)


def _known_kit_roots(kit: Path) -> set[str]:
    return {path.name for path in kit.iterdir() if path.is_dir()}


def _validate_backtick_references(
    kit: Path, path: Path, text: str, roots: set[str], errors: list[str]
) -> None:
    for reference in sorted(set(_concrete_backtick_paths(text))):
        first = reference.split("/", 1)[0]
        if reference not in {"AGENTS.md", "CLAUDE.md"} and first not in roots:
            # Project artifacts named by a skill are not necessarily kit links.
            continue
        resolved = _validate_governed_path(
            kit,
            reference,
            f"{path.relative_to(kit).as_posix()} internal reference",
            errors,
        )
        if resolved is None:
            errors.append(
                f"{path.relative_to(kit).as_posix()}: broken internal reference {reference}."
            )


def _validate_markdown_links(
    kit: Path, path: Path, text: str, roots: set[str], errors: list[str]
) -> None:
    for raw in MARKDOWN_LINK_RE.findall(text):
        target = raw.strip().strip("<>").split("#", 1)[0]
        if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
            continue
        target = target.replace("\\", "/")
        if any(char in target for char in ("*", "<", ">", "$", "{", "}")):
            continue
        normalized = _normalize_kit_path(target)
        first = normalized.split("/", 1)[0]
        if target.startswith(("./", "../")):
            candidate = path.parent / target
            try:
                relative = candidate.relative_to(kit).as_posix()
            except ValueError:
                errors.append(
                    f"{path.relative_to(kit).as_posix()}: Markdown link escapes kit root: {raw}."
                )
                continue
            resolved = _validate_governed_path(
                kit,
                relative,
                f"{path.relative_to(kit).as_posix()} Markdown link",
                errors,
            )
        elif normalized in {"AGENTS.md", "CLAUDE.md"} or first in roots:
            resolved = _validate_governed_path(
                kit,
                normalized,
                f"{path.relative_to(kit).as_posix()} Markdown link",
                errors,
            )
        else:
            continue
        if resolved is None:
            errors.append(
                f"{path.relative_to(kit).as_posix()}: broken Markdown link {raw}."
            )


def validate_skills(
    kit: Path, skills: dict[str, dict[str, Any]], errors: list[str]
) -> int:
    roots = _known_kit_roots(kit)
    count = 0
    for name, entry in sorted(skills.items()):
        skill = _validate_governed_path(
            kit,
            str(entry["path"]),
            f"Manifest skill {name} path",
            errors,
            expect_file=True,
        )
        if skill is None:
            continue
        folder = skill.parent
        openai_yaml = folder / "agents" / "openai.yaml"
        count += 1
        text = skill.read_text(encoding="utf-8-sig")
        fm, _ = _frontmatter(text)
        unexpected_frontmatter = sorted(set(fm) - {"name", "description"})
        if unexpected_frontmatter:
            errors.append(
                f"{skill.relative_to(kit).as_posix()}: unsupported frontmatter "
                f"fields {unexpected_frontmatter}."
            )
        if fm.get("name") != name:
            errors.append(f"{skill.relative_to(kit).as_posix()}: frontmatter name mismatch.")
        description = fm.get("description", "")
        if not description:
            errors.append(f"{skill.relative_to(kit).as_posix()}: missing description.")
        if "TODO" in description or "Complete and informative" in description:
            errors.append(f"{skill.relative_to(kit).as_posix()}: placeholder description remains.")
        if len(text.splitlines()) >= 500:
            errors.append(
                f"{skill.relative_to(kit).as_posix()}: SKILL.md must stay below 500 lines."
            )
        if not openai_yaml.exists() and not _is_reparse(openai_yaml):
            errors.append(f"skills/{name}: missing agents/openai.yaml.")
        else:
            if not _validate_existing_path(
                kit,
                openai_yaml,
                f"skills/{name}/agents/openai.yaml",
                errors,
                expect_file=True,
            ):
                continue
            ui = openai_yaml.read_text(encoding="utf-8-sig")
            ui_fields = _simple_yaml_fields(ui)
            for field in ("display_name", "short_description", "default_prompt"):
                if not ui_fields.get(field):
                    errors.append(f"skills/{name}/agents/openai.yaml: missing {field}.")
            for field in ("display_name", "short_description", "default_prompt"):
                if not re.search(
                    rf"^  {field}:\s*(['\"]).*\1\s*$",
                    ui,
                    flags=re.MULTILINE,
                ):
                    errors.append(
                        f"skills/{name}/agents/openai.yaml: {field} must be a quoted string."
                    )
            short_description = ui_fields.get("short_description", "")
            if short_description and not 25 <= len(short_description) <= 64:
                errors.append(
                    f"skills/{name}/agents/openai.yaml: short_description must have "
                    "25 to 64 characters."
                )
            if not re.search(
                rf"(?<![a-z0-9-])\${re.escape(name)}(?![a-z0-9-])",
                ui_fields.get("default_prompt", ""),
            ):
                errors.append(
                    f"skills/{name}/agents/openai.yaml: default_prompt should mention ${name}."
                )
            _validate_markdown_links(kit, openai_yaml, ui, roots, errors)
        _validate_backtick_references(kit, skill, text, roots, errors)
        _validate_markdown_links(kit, skill, text, roots, errors)
    return count


def _verdict_section(text: str) -> str:
    captured: list[str] = []
    active = False
    for line in text.splitlines():
        lower = line.lower()
        is_heading = bool(re.match(r"^\s*#{1,6}\s+", line))
        if is_heading:
            active = "veredit" in lower
        if re.search(r"\b(?:verdict|veredito)(?:\s+[\w-]+)*\s*:", lower):
            active = True
        if active:
            captured.append(line)
    return "\n".join(captured)


def validate_verdicts(kit: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    config = manifest.get("verdicts", {})
    canonical = {str(item) for item in config.get("canonical", [])}
    forbidden = {str(item) for item in config.get("forbidden", [])}
    if canonical != CANONICAL_VERDICTS:
        errors.append(
            "Manifest canonical verdicts must be APROVADO, "
            "APROVADO_COM_RESSALVAS, QUESTIONAR, and REPROVADO."
        )
    if canonical & forbidden:
        errors.append("Manifest verdict canonical and forbidden sets overlap.")

    contract_files = [str(item) for item in config.get("contract_files", [])]
    if not contract_files:
        errors.append("Manifest verdicts.contract_files must not be empty.")
    for relative in contract_files:
        path = _validate_governed_path(
            kit,
            relative,
            "Verdict contract file",
            errors,
            expect_file=True,
        )
        if path is None:
            continue
        semantic_text = _mask_nonsemantic_markdown(
            path.read_text(encoding="utf-8-sig")
        )
        section = _verdict_section(semantic_text)
        label = path.relative_to(kit).as_posix()
        missing = sorted(
            token for token in canonical if not re.search(rf"\b{re.escape(token)}\b", section)
        )
        present_forbidden = sorted(
            token for token in forbidden if re.search(rf"\b{re.escape(token)}\b", section)
        )
        if missing:
            errors.append(f"{label}: canonical verdicts missing from verdict contract: {missing}.")
        if present_forbidden:
            errors.append(f"{label}: forbidden legacy verdicts remain: {present_forbidden}.")


def validate_internal_links(
    kit: Path,
    agents: dict[str, dict[str, Any]],
    skills: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    roots = _known_kit_roots(kit)
    paths = [kit / str(entry["source"]) for entry in agents.values()]
    paths.extend(kit / str(entry["path"]) for entry in skills.values())
    runtime_doc = kit / "RUNTIME_Bridge" / "RUNTIME.md"
    if runtime_doc.exists():
        paths.append(runtime_doc)
    seen: set[Path] = set()
    for path in paths:
        if path in seen or path.suffix.lower() != ".md":
            continue
        if not _validate_existing_path(
            kit,
            path,
            f"Internal-link source {path}",
            errors,
            expect_file=True,
        ):
            continue
        seen.add(path)
        _validate_markdown_links(
            kit, path, path.read_text(encoding="utf-8-sig"), roots, errors
        )


def _git(kit: Path, *args: str) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(kit), *args],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""
    return proc.returncode, proc.stdout.strip()


def validate_versioning(kit: Path, errors: list[str], warnings: list[str]) -> str:
    code, _ = _git(kit, "rev-parse", "--git-dir")
    if code != 0:
        errors.append(
            "Git rev-parse failed; the governed arsenal must be auditable and synchronized."
        )
        return "no git"

    status = "git ok"
    code, remotes = _git(kit, "remote", "-v")
    if code != 0:
        errors.append("git remote -v failed; GitHub remote policy was not verified.")
        status = "git remote error"
    elif not remotes:
        errors.append("Kit has no git remote; a governed GitHub remote is required.")
        status = "git without remote"
    else:
        remotes_by_name: dict[str, list[tuple[str, str]]] = {}
        for line in remotes.splitlines():
            fields = line.split()
            if len(fields) >= 2:
                kind = fields[2].strip("()") if len(fields) >= 3 else ""
                remotes_by_name.setdefault(fields[0], []).append((fields[1], kind))
        github = re.compile(
            r"^(?:https://github\.com/[^/\s]+/[^/\s]+|"
            r"git@github\.com:[^/\s]+/[^/\s]+|"
            r"ssh://(?:git@)?github\.com(?::\d+)?/[^/\s]+/[^/\s]+?)(?:\.git)?/?$",
            re.IGNORECASE,
        )
        origin_entries = remotes_by_name.get("origin", [])
        origin_kinds = {kind for _url, kind in origin_entries}
        if (
            not origin_entries
            or not all(github.fullmatch(url) for url, _kind in origin_entries)
            or not {"fetch", "push"}.issubset(origin_kinds)
        ):
            errors.append(
                "Kit remote policy requires GitHub HTTPS/SSH origin fetch and push URLs."
            )
            status = "git without governed GitHub origin"
    code, dirty = _git(kit, "status", "--porcelain")
    if code != 0:
        errors.append("git status --porcelain failed; working-tree state is unknown.")
        status = "git status error"
    elif dirty:
        warnings.append(f"Kit has {len(dirty.splitlines())} uncommitted change(s).")
    return status


def main() -> int:
    kit = _kit_root().resolve(strict=True)
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = kit / "RUNTIME_Bridge" / "AGENT_RUNTIME_MAP.toml"

    required = [
        ("AGENTS.md", True),
        (".codex/agents", False),
        (".claude/agents", False),
        ("RUNTIME_Bridge/AGENT_RUNTIME_MAP.toml", True),
    ]
    validated_required: dict[str, Path] = {}
    for relative, expect_file in required:
        path = _validate_governed_path(
            kit,
            relative,
            f"Required path {relative}",
            errors,
            expect_file=expect_file,
            strip_installed_prefix=False,
        )
        if path is not None:
            validated_required[relative] = path

    manifest = (
        _read_toml(validated_required["RUNTIME_Bridge/AGENT_RUNTIME_MAP.toml"], errors)
        if "RUNTIME_Bridge/AGENT_RUNTIME_MAP.toml" in validated_required
        else {}
    )
    validate_runtime_metadata(kit, manifest, errors)
    agents, skills = _manifest_indexes(kit, manifest, errors)
    codex_count, codex = validate_codex_wrappers(kit, agents, errors)
    claude_count = validate_claude_wrappers(kit, agents, codex, errors)
    skill_count = validate_skills(kit, skills, errors)
    validate_verdicts(kit, manifest, errors)
    validate_internal_links(kit, agents, skills, errors)
    versioning = validate_versioning(kit, errors, warnings)

    print("Codex Agent Kit runtime validation")
    print(f"Kit root: {kit}")
    print(f"Manifest agents: {len(agents)}")
    print(f"Codex wrappers: {codex_count}")
    print(f"Claude wrappers: {claude_count}")
    print(f"Runtime skills: {skill_count}/{len(skills)}")
    print(f"Versioning: {versioning}")

    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        print("\nFAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "\nOK: manifest, source files, Codex/Claude parity, complete-source "
        "instructions, skills, internal links, and verdict contracts are coherent."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
