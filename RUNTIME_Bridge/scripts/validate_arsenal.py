#!/usr/bin/env python3
"""Validate Codex Agent Kit runtime compatibility.

Checks:
- Codex wrappers are valid TOML and contain required fields.
- Claude wrappers have frontmatter name/description.
- Wrapper instructions point to at least one existing source file.
- Runtime skills have required frontmatter and UI metadata.
- Kit is under git version control (required) with remote and clean tree
  (warnings). O arsenal sem versionamento nao e auditavel.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path


REQUIRED_SKILLS = [
    "codex-agent-kit",
    "gsd-tdd-cli-harness",
    "agent-forge",
]


def _kit_root() -> Path:
    here = Path(__file__).resolve()
    return here.parents[2]


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end].strip()
    result: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def _candidate_paths(text: str) -> list[str]:
    patterns = [
        r"`([^`]+\.(?:md|toml))`",
        r"Prefer\s+([^\n\r]+?\.(?:md|toml))",
        r"use\s+([^\n\r]+?\.(?:md|toml))",
    ]
    found: list[str] = []
    for pattern in patterns:
        found.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    cleaned: list[str] = []
    for item in found:
        value = item.strip().strip("- ").replace("\\", "/")
        if value.startswith(".codex/"):
            value = value[len(".codex/") :]
        cleaned.append(value)
    return cleaned


def _has_existing_source(kit: Path, text: str) -> bool:
    for rel in _candidate_paths(text):
        if (kit / rel).exists():
            return True
    return False


def validate_codex_wrappers(kit: Path, errors: list[str]) -> int:
    folder = kit / ".codex" / "agents"
    files = sorted(folder.glob("*.toml"))
    if not files:
        errors.append("No Codex wrappers found in .codex/agents.")
        return 0

    for path in files:
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path.relative_to(kit)}: invalid TOML: {exc}")
            continue
        for key in ("name", "description", "developer_instructions"):
            if not str(data.get(key, "")).strip():
                errors.append(f"{path.relative_to(kit)}: missing {key}.")
        instructions = str(data.get("developer_instructions", ""))
        if instructions and not _has_existing_source(kit, instructions):
            errors.append(f"{path.relative_to(kit)}: no existing source file referenced.")
    return len(files)


def validate_claude_wrappers(kit: Path, errors: list[str]) -> int:
    folder = kit / ".claude" / "agents"
    files = sorted(folder.glob("*.md"))
    if not files:
        errors.append("No Claude wrappers found in .claude/agents.")
        return 0

    for path in files:
        text = path.read_text(encoding="utf-8-sig")
        fm = _frontmatter(text)
        for key in ("name", "description"):
            if not fm.get(key):
                errors.append(f"{path.relative_to(kit)}: missing frontmatter {key}.")
        if not _has_existing_source(kit, text):
            errors.append(f"{path.relative_to(kit)}: no existing source file referenced.")
    return len(files)


def validate_skills(kit: Path, errors: list[str]) -> int:
    count = 0
    for name in REQUIRED_SKILLS:
        folder = kit / "skills" / name
        skill = folder / "SKILL.md"
        openai_yaml = folder / "agents" / "openai.yaml"
        if not skill.exists():
            errors.append(f"skills/{name}: missing SKILL.md.")
            continue
        count += 1
        text = skill.read_text(encoding="utf-8-sig")
        fm = _frontmatter(text)
        if fm.get("name") != name:
            errors.append(f"skills/{name}/SKILL.md: frontmatter name mismatch.")
        if not fm.get("description"):
            errors.append(f"skills/{name}/SKILL.md: missing description.")
        if not openai_yaml.exists():
            errors.append(f"skills/{name}: missing agents/openai.yaml.")
        elif f"${name}" not in openai_yaml.read_text(encoding="utf-8-sig"):
            errors.append(f"skills/{name}/agents/openai.yaml: default_prompt should mention ${name}.")
    return count


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
    """O arsenal deve ser versionado em git (idealmente com remote no GitHub).

    Sem git: FALHA - copias divergem em silencio e os agentes nao sao
    auditaveis por terceiros. Sem remote ou com tree sujo: aviso.
    """
    code, _ = _git(kit, "rev-parse", "--git-dir")
    if code == 127:
        warnings.append("git indisponivel no PATH; versionamento nao verificado.")
        return "desconhecido"
    if code != 0:
        errors.append(
            "Kit NAO esta sob git. Versione o arsenal (git init + remote no "
            "GitHub) - regra de governanca: arsenal sem versionamento nao e "
            "auditavel e as copias divergem em silencio."
        )
        return "sem git"

    status = "git ok"
    code, remotes = _git(kit, "remote")
    if code == 0 and not remotes:
        warnings.append(
            "Kit versionado localmente mas SEM remote. Adicione um remote no "
            "GitHub para backup e auditoria (git remote add origin <url>)."
        )
        status = "git sem remote"

    code, dirty = _git(kit, "status", "--porcelain")
    if code == 0 and dirty:
        changed = len(dirty.splitlines())
        warnings.append(
            f"Kit com {changed} mudanca(s) nao commitada(s). Edicao de agente "
            "so termina com commit (e push, quando houver remote)."
        )
    return status


def main() -> int:
    kit = _kit_root()
    errors: list[str] = []
    warnings: list[str] = []

    required = ["AGENTS.md", ".codex/agents", ".claude/agents", "RUNTIME_Bridge/AGENT_RUNTIME_MAP.toml"]
    for rel in required:
        if not (kit / rel).exists():
            errors.append(f"Missing required path: {rel}")

    codex_count = validate_codex_wrappers(kit, errors)
    claude_count = validate_claude_wrappers(kit, errors)
    skill_count = validate_skills(kit, errors)
    versioning = validate_versioning(kit, errors, warnings)

    print("Codex Agent Kit runtime validation")
    print(f"Kit root: {kit}")
    print(f"Codex wrappers: {codex_count}")
    print(f"Claude wrappers: {claude_count}")
    print(f"Runtime skills: {skill_count}")
    print(f"Versionamento: {versioning}")

    for warning in warnings:
        print(f"AVISO: {warning}")

    if errors:
        print("\nFAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("\nOK: Codex wrappers, Claude wrappers, runtime skills, and bridge manifest are coherent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
