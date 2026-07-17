#!/usr/bin/env python3
"""Synchronize generated Claude wrappers from Codex TOML wrappers.

`.codex/agents/*.toml` is the structured wrapper source. Original agent files
remain the behavioral source of truth. The runtime manifest is the exhaustive
catalog: synchronization refuses to hide a missing or extra Codex wrapper.

The operation is idempotent: unchanged files are not rewritten, unmanaged
Claude wrappers are preserved as conflicts, and ``--check`` verifies parity
without writing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import tempfile
import tomllib
from pathlib import Path, PurePosixPath, PureWindowsPath


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def kit_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_reparse(path: Path) -> bool:
    """Return True for symlinks and Windows reparse points, including broken ones."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return path.is_symlink()
    return path.is_symlink() or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _relative_governed_path(root: Path, value: str, label: str) -> Path:
    raw = value.strip().strip("<>").replace("\\", "/")
    if not raw or "\x00" in raw:
        raise ValueError(f"{label}: path is empty")
    if PurePosixPath(raw).is_absolute() or PureWindowsPath(raw).is_absolute():
        raise ValueError(f"{label}: absolute paths are forbidden: {value!r}")
    parts = PurePosixPath(raw).parts
    if any(
        part == ".." or (not part.rstrip(" .") and part.count(".") >= 2)
        for part in parts
    ):
        raise ValueError(f"{label}: parent traversal is forbidden: {value!r}")
    if any(":" in part for part in parts):
        raise ValueError(f"{label}: drive/stream path syntax is forbidden: {value!r}")
    candidate = root / Path(*parts)
    resolved_root = root.resolve(strict=True)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"{label}: path escapes kit root: {value!r}") from exc
    return candidate


def _assert_no_reparse_chain(root: Path, path: Path, label: str) -> None:
    """Reject links/reparse points from the kit root down to a governed path."""
    resolved_root = root.resolve(strict=True)
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label}: path is outside kit root: {path}") from exc
    current = root
    for part in relative.parts:
        current /= part
        if _is_reparse(current):
            raise ValueError(f"{label}: symlink/reparse point is forbidden: {current}")
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"{label}: resolved path escapes kit root: {path}") from exc


def _safe_read_text(root: Path, path: Path, label: str) -> str:
    _assert_no_reparse_chain(root, path, label)
    if not path.is_file():
        raise ValueError(f"{label}: file does not exist: {path}")
    return path.read_text(encoding="utf-8-sig")


def _atomic_write(root: Path, path: Path, body: str, label: str) -> None:
    _assert_no_reparse_chain(root, path.parent, f"{label} parent")
    target_mode = 0o644
    if path.exists() or _is_reparse(path):
        _assert_no_reparse_chain(root, path, label)
        if not path.is_file():
            raise ValueError(f"{label}: target is not a regular file: {path}")
        target_mode = stat.S_IMODE(path.stat().st_mode)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, target_mode)
        # Recheck after writing the temporary file to reduce target-swap exposure.
        _assert_no_reparse_chain(root, path.parent, f"{label} parent")
        if path.exists() or _is_reparse(path):
            _assert_no_reparse_chain(root, path, label)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _manifest_agents(root: Path) -> dict[str, dict[str, str]]:
    manifest_path = root / "RUNTIME_Bridge" / "AGENT_RUNTIME_MAP.toml"
    data = tomllib.loads(_safe_read_text(root, manifest_path, "runtime manifest"))
    result: dict[str, dict[str, str]] = {}
    for entry in data.get("agents", []):
        name = str(entry.get("name", "")).strip()
        if not NAME_RE.fullmatch(name):
            raise ValueError(f"manifest agent has invalid name: {name!r}")
        if name in result:
            raise ValueError(f"manifest agent is duplicated: {name}")
        source = _relative_governed_path(
            root, str(entry.get("source", "")), f"manifest agent {name} source"
        )
        _safe_read_text(root, source, f"manifest agent {name} source")
        result[name] = {str(key): str(value) for key, value in entry.items()}
    if not result:
        raise ValueError("manifest contains no [[agents]] entries")
    return result


def _codex_wrappers(root: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    folder = root / ".codex" / "agents"
    _assert_no_reparse_chain(root, folder, "Codex wrapper directory")
    if not folder.is_dir():
        raise ValueError(f"Codex wrapper directory does not exist: {folder}")
    for path in sorted(folder.glob("*.toml")):
        data = tomllib.loads(_safe_read_text(root, path, "Codex wrapper"))
        name = str(data.get("name", "")).strip()
        description = str(data.get("description", "")).strip()
        instructions = str(data.get("developer_instructions", "")).strip()
        if not name or not description or not instructions:
            raise ValueError(
                f"{path.relative_to(root)}: missing name, description, or developer_instructions"
            )
        if not NAME_RE.fullmatch(name):
            raise ValueError(f"{path.relative_to(root)}: invalid name {name!r}")
        if path.stem != name:
            raise ValueError(
                f"{path.relative_to(root)}: filename must match wrapper name {name!r}"
            )
        if name in result:
            raise ValueError(f"duplicate Codex wrapper name: {name}")
        result[name] = {
            "name": name,
            "description": description,
            "developer_instructions": instructions,
        }
    return result


def _render(data: dict[str, str]) -> str:
    name = data["name"]
    description = json.dumps(data["description"], ensure_ascii=False)
    instructions = data["developer_instructions"].replace(
        "Codex wrapper", "Claude Code wrapper"
    )
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"{instructions}\n"
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify generated Claude wrappers without changing files",
    )
    return parser.parse_args()


def synchronize(root: Path, check: bool = False) -> int:
    root = root.resolve(strict=True)
    claude_dir = root / ".claude" / "agents"

    try:
        manifest = _manifest_agents(root)
        codex = _codex_wrappers(root)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    manifest_names = set(manifest)
    codex_names = set(codex)
    if manifest_names != codex_names:
        missing = sorted(manifest_names - codex_names)
        extra = sorted(codex_names - manifest_names)
        if missing:
            print(f"ERROR: Codex wrappers missing for manifest agents: {missing}")
        if extra:
            print(f"ERROR: Codex wrappers absent from manifest catalog: {extra}")
        return 1

    expected = {
        claude_dir / f"{name}.md": _render(data)
        for name, data in sorted(codex.items())
    }
    try:
        _assert_no_reparse_chain(root, claude_dir.parent, "Claude wrapper parent")
        if claude_dir.exists() or _is_reparse(claude_dir):
            _assert_no_reparse_chain(root, claude_dir, "Claude wrapper directory")
            if not claude_dir.is_dir():
                raise ValueError(f"Claude wrapper target is not a directory: {claude_dir}")
        existing = set(claude_dir.glob("*.md")) if claude_dir.exists() else set()
        extras = sorted(existing - set(expected))
        changed: list[Path] = []
        for path, body in expected.items():
            if path.exists() or _is_reparse(path):
                current = _safe_read_text(root, path, "Claude wrapper target")
                if current != body:
                    changed.append(path)
            else:
                changed.append(path)
        for path in extras:
            _safe_read_text(root, path, "extra Claude wrapper")
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Unknown files may be user-owned custom wrappers. Never delete them or
    # silently proceed: require an explicit catalog/ownership decision.
    if extras:
        for path in extras:
            print(
                f"CONFLICT: unmanaged Claude wrapper preserved: {path.relative_to(root)}",
                file=sys.stderr,
            )
        return 1

    if check:
        if changed:
            for path in changed:
                print(f"OUT OF SYNC: {path.relative_to(root)}")
            return 1
        print(f"OK: {len(expected)} Claude wrappers are in exact Codex parity.")
        return 0

    try:
        claude_dir.mkdir(parents=True, exist_ok=True)
        _assert_no_reparse_chain(root, claude_dir, "Claude wrapper directory")
        for path in changed:
            _atomic_write(root, path, expected[path], "Claude wrapper target")
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"Synchronized {len(expected)} Claude wrappers: "
        f"{len(changed)} written, 0 unmanaged files removed."
    )
    return 0


def main() -> int:
    args = _parse_args()
    return synchronize(kit_root(), check=args.check)


if __name__ == "__main__":
    sys.exit(main())
