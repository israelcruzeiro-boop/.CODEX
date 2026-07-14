#!/usr/bin/env python3
"""Regenerate Claude wrappers from Codex TOML wrappers.

This keeps `.codex/agents/*.toml` as the structured runtime source for wrapper
metadata while preserving original agent files as the behavioral source.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def kit_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = kit_root()
    codex_dir = root / ".codex" / "agents"
    claude_dir = root / ".claude" / "agents"
    claude_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for source in sorted(codex_dir.glob("*.toml")):
        data = tomllib.loads(source.read_text(encoding="utf-8-sig"))
        name = str(data.get("name", "")).strip()
        description = str(data.get("description", "")).strip()
        instructions = str(data.get("developer_instructions", "")).strip()
        if not name or not description or not instructions:
            print(f"skip {source.name}: missing name, description, or developer_instructions")
            continue
        target = claude_dir / f"{name}.md"
        body = (
            "---\n"
            f"name: {name}\n"
            f"description: {description}\n"
            "---\n\n"
            f"{instructions.replace('Codex wrapper', 'Claude Code wrapper')}\n"
        )
        target.write_text(body, encoding="utf-8", newline="\n")
        count += 1

    print(f"Regenerated {count} Claude wrappers from {codex_dir}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
