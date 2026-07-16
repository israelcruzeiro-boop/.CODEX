#!/usr/bin/env python3
"""Run the repository's continuous Codex Agent Kit quality gate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


@dataclass(frozen=True)
class GateCommand:
    name: str
    argv: tuple[str, ...]
    require_empty_stdout: bool = False


@dataclass(frozen=True)
class GateEvidence:
    name: str
    argv: tuple[str, ...]
    exit_code: int
    output: str
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "argv": list(self.argv),
            "exit_code": self.exit_code,
            "passed": self.passed,
            "output": self.output,
        }


def kit_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_commands(python: str | None = None) -> tuple[GateCommand, ...]:
    interpreter = python or sys.executable
    scripts = "RUNTIME_Bridge/scripts"
    return (
        GateCommand("compileall", (interpreter, "-m", "compileall", "-q", scripts)),
        GateCommand("claude-wrapper-parity", (interpreter, f"{scripts}/sync_claude_from_codex.py", "--check")),
        GateCommand("arsenal-contract", (interpreter, f"{scripts}/validate_arsenal.py")),
        GateCommand("project-coverage", (interpreter, f"{scripts}/validate_project_coverage.py")),
        GateCommand("skill-contracts", (interpreter, f"{scripts}/run_skill_contract_evals.py")),
        GateCommand("unit-and-adversarial-tests", (interpreter, "-m", "unittest", "discover", "-s", scripts, "-p", "test_*.py", "-v")),
        GateCommand("diff-check", ("git", "diff", "--check")),
        GateCommand("generated-drift-check", ("git", "status", "--porcelain", "--untracked-files=all"), require_empty_stdout=True),
    )


Runner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]
OUTPUT_LIMIT = 12000


def _run(argv: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def _bounded_output(output: str, limit: int = OUTPUT_LIMIT) -> str:
    if len(output) <= limit:
        return output
    half = max(1, (limit - 200) // 2)
    removed = len(output) - (half * 2)
    marker = (
        f"\n... [TRUNCATED {removed} CHARACTERS; "
        "BEGINNING AND END PRESERVED] ...\n"
    )
    return output[:half] + marker + output[-half:]


def run_gate(root: Path | None = None, *, runner: Runner = _run, python: str | None = None) -> list[GateEvidence]:
    cwd = (root or kit_root()).resolve()
    evidence: list[GateEvidence] = []
    for command in build_commands(python):
        try:
            completed = runner(command.argv, cwd)
            output = completed.stdout or ""
            passed = completed.returncode == 0 and (not command.require_empty_stdout or not output.strip())
            evidence.append(GateEvidence(command.name, command.argv, completed.returncode, _bounded_output(output), passed))
        except OSError as exc:
            evidence.append(GateEvidence(command.name, command.argv, 127, str(exc), False))
    return evidence


def _console_safe(value: str) -> str:
    """Render captured output even when the host console is a legacy code page."""

    encoding = sys.stdout.encoding or "utf-8"
    return value.encode(encoding, errors="backslashreplace").decode(encoding)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="kit root; defaults to script-derived root")
    parser.add_argument("--json", action="store_true", help="emit machine-readable evidence")
    args = parser.parse_args(argv)
    evidence = run_gate(args.root)
    ok = all(item.passed for item in evidence)
    if args.json:
        payload = json.dumps(
            {
                "ok": ok,
                "root": str((args.root or kit_root()).resolve()),
                "evidence": [item.to_dict() for item in evidence],
            },
            ensure_ascii=False,
            indent=2,
        )
        print(_console_safe(payload))
    else:
        print(f"Codex Agent Kit quality gate: {'OK' if ok else 'FAILED'}")
        for item in evidence:
            print(f"\n[{'PASS' if item.passed else 'FAIL'}] {item.name} (exit {item.exit_code})")
            if item.output.strip():
                print(_console_safe(item.output.rstrip()))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
