#!/usr/bin/env python3
"""Materialize Codex Agent Kit runtime files into a project root.

The kit is expected to be checked out at ``PROJECT_ROOT/.codex``. Runtime
wrappers live one level deeper inside that checkout so the kit repository can
remain the source of truth without confusing source wrappers with installed
wrappers. Canonical repository skills are projected to the runtime discovery
path at ``PROJECT_ROOT/.agents/skills``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable, Mapping


MANIFEST_RELATIVE_PATH = PurePosixPath(".codex/.runtime-install-manifest.json")
MANIFEST_VERSION = 1
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
CANONICAL_SKILLS = (
    "agent-forge",
    "architecture-blueprint",
    "codex-agent-kit",
    "gsd-tdd-cli-harness",
    "multi-agent-delivery",
    "spec-driven-breakdown",
)


class InstallError(RuntimeError):
    """Raised when the runtime cannot be installed safely."""


@dataclass(frozen=True)
class ManagedFile:
    source: str
    sha256: str


@dataclass
class InstallResult:
    actions: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    unchanged: int = 0
    manifest_changed: bool = False

    @property
    def drifted(self) -> bool:
        return bool(self.actions or self.conflicts or self.manifest_changed)


def default_kit_root() -> Path:
    return Path(__file__).resolve().parents[2]


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stable_regular_file_bytes(
    path: Path, *, guard: Callable[[], object] | None = None
) -> bytes:
    """Read one regular file while detecting path swaps and concurrent writes."""

    try:
        if guard is not None:
            guard()
        before = path.lstat()
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise InstallError(f"file is not a regular file: {path}")
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            content = stream.read()
        if guard is not None:
            guard()
        after = path.lstat()
    except InstallError:
        raise
    except OSError as exc:
        raise InstallError(f"cannot read stable regular file {path}: {exc}") from exc

    identity_before = (before.st_dev, before.st_ino)
    identity_opened = (opened.st_dev, opened.st_ino)
    identity_after = (after.st_dev, after.st_ino)
    state_before = (before.st_size, before.st_mtime_ns)
    state_after = (after.st_size, after.st_mtime_ns)
    if (
        identity_before != identity_opened
        or identity_opened != identity_after
        or state_before != state_after
        or len(content) != opened.st_size
    ):
        raise InstallError(f"file changed while it was being read: {path}")
    return content


def _git_command(kit_root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    """Run a read-only Git query without invoking a shell or optional locks."""

    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        return subprocess.run(
            ["git", "-C", str(kit_root), *arguments],
            check=False,
            capture_output=True,
            env=environment,
        )
    except OSError as exc:
        raise InstallError(f"cannot execute Git history check: {exc}") from exc


def _is_reachable_git_source_version(
    kit_root: Path, source_relative: str, content: bytes
) -> bool:
    """Prove that content existed at the canonical path in reachable Git history."""

    top_level = _git_command(kit_root, "rev-parse", "--show-toplevel")
    if top_level.returncode != 0:
        raise InstallError("--refresh-managed requires the kit to be a Git checkout")
    try:
        repository_root = Path(os.fsdecode(top_level.stdout.strip())).resolve()
    except (OSError, ValueError) as exc:
        raise InstallError("cannot resolve the kit Git repository root") from exc
    if repository_root != kit_root.resolve():
        raise InstallError(
            "--refresh-managed requires KIT_ROOT itself to be the Git repository root"
        )

    revisions = _git_command(
        kit_root,
        "rev-list",
        "HEAD",
        "--full-history",
        "--",
        source_relative,
    )
    if revisions.returncode != 0:
        raise InstallError(
            f"cannot inspect reachable Git history for {source_relative!r}"
        )

    for commit in revisions.stdout.splitlines():
        if not re.fullmatch(rb"[0-9a-fA-F]+", commit):
            raise InstallError("Git returned an invalid reachable commit identifier")
        historical = _git_command(
            kit_root,
            "cat-file",
            "blob",
            f"{commit.decode('ascii')}:{source_relative}",
        )
        if historical.returncode == 0 and historical.stdout == content:
            return True
    return False


def _validate_layout(kit_root: Path, project_root: Path) -> None:
    expected = (project_root / ".codex").resolve()
    if kit_root.resolve() != expected:
        raise InstallError(
            "invalid layout: the kit must be checked out at "
            f"PROJECT_ROOT/.codex (expected {expected}, got {kit_root.resolve()})"
        )


def _is_allowed_target(relative_path: str) -> bool:
    path = PurePosixPath(relative_path)
    if path.is_absolute() or ".." in path.parts:
        return False
    if path in {PurePosixPath("AGENTS.md"), PurePosixPath("CLAUDE.md")}:
        return True
    if (
        len(path.parts) >= 4
        and path.parts[:2] == (".agents", "skills")
        and path.parts[2] in CANONICAL_SKILLS
    ):
        return True
    return (
        len(path.parts) == 3
        and path.parts[1] == "agents"
        and (
            (path.parts[0] == ".codex" and path.suffix == ".toml")
            or (path.parts[0] == ".claude" and path.suffix == ".md")
        )
        and bool(path.parts[2])
    )


def _expected_source_for_target(relative_path: str) -> str | None:
    """Return the only canonical source allowed to manage a target path."""

    path = PurePosixPath(relative_path)
    if relative_path != path.as_posix() or not _is_allowed_target(relative_path):
        return None
    if path == PurePosixPath("AGENTS.md"):
        return "C10_Maestro/C10_Agent_ProjectRules.md"
    if path == PurePosixPath("CLAUDE.md"):
        return "C10_Maestro/C10_Agent_ClaudeProjectRules.md"
    if path.parts[:2] in {(".codex", "agents"), (".claude", "agents")}:
        return path.as_posix()
    if path.parts[:2] == (".agents", "skills"):
        return PurePosixPath("skills", *path.parts[2:]).as_posix()
    return None


def _is_link_or_reparse(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(metadata.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    file_attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(reparse_flag and file_attributes & reparse_flag)


def _reject_link_or_reparse_components(
    root: Path, relative_path: str, *, kind: str = "managed target"
) -> None:
    current = root
    if os.path.lexists(current) and _is_link_or_reparse(current):
        raise InstallError(f"{kind} root is a symlink or reparse point: {root}")
    for part in PurePosixPath(relative_path).parts:
        current = current / part
        if os.path.lexists(current) and _is_link_or_reparse(current):
            raise InstallError(
                f"{kind} contains a symlink or reparse point: {relative_path!r}"
            )


def _target_path(project_root: Path, relative_path: str) -> Path:
    if not _is_allowed_target(relative_path):
        raise InstallError(f"manifest contains disallowed target: {relative_path!r}")
    _reject_link_or_reparse_components(project_root, relative_path)
    target = project_root.joinpath(*PurePosixPath(relative_path).parts)
    try:
        target.resolve(strict=False).relative_to(project_root.resolve())
    except ValueError as exc:
        raise InstallError(f"target escapes project root: {relative_path!r}") from exc
    return target


def _source_path(kit_root: Path, path: Path) -> Path:
    """Validate one canonical source without following links or reparse points."""

    try:
        relative = path.relative_to(kit_root).as_posix()
    except ValueError as exc:
        raise InstallError(f"runtime source escapes kit root: {path}") from exc
    _reject_link_or_reparse_components(kit_root, relative, kind="runtime source")
    try:
        path.resolve(strict=False).relative_to(kit_root.resolve())
    except ValueError as exc:
        raise InstallError(f"runtime source escapes kit root: {path}") from exc
    return path


def _manifest_path(project_root: Path) -> Path:
    return project_root.joinpath(*MANIFEST_RELATIVE_PATH.parts)


def _manifest_snapshot(project_root: Path) -> bytes | None:
    path = _manifest_path(project_root)
    _reject_link_or_reparse_components(
        project_root,
        MANIFEST_RELATIVE_PATH.as_posix(),
        kind="runtime manifest",
    )
    if not path.exists():
        if os.path.lexists(path):
            raise InstallError(f"manifest is not a regular file: {path}")
        return None
    return _stable_regular_file_bytes(
        path,
        guard=lambda: _reject_link_or_reparse_components(
            project_root,
            MANIFEST_RELATIVE_PATH.as_posix(),
            kind="runtime manifest",
        ),
    )


def _load_manifest(path: Path, content: bytes | None) -> dict[str, ManagedFile]:
    if content is None:
        return {}
    try:
        raw = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InstallError(f"cannot read managed runtime manifest {path}: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("version") != MANIFEST_VERSION:
        raise InstallError(f"unsupported managed runtime manifest: {path}")
    files = raw.get("files")
    if not isinstance(files, dict):
        raise InstallError(f"invalid files table in managed runtime manifest: {path}")

    result: dict[str, ManagedFile] = {}
    for relative_path, metadata in files.items():
        if not isinstance(relative_path, str) or not _is_allowed_target(relative_path):
            raise InstallError(f"invalid managed target in manifest: {relative_path!r}")
        if not isinstance(metadata, dict):
            raise InstallError(f"invalid metadata for managed target: {relative_path!r}")
        source = metadata.get("source")
        content_hash = metadata.get("sha256")
        expected_source = _expected_source_for_target(relative_path)
        if (
            not isinstance(source, str)
            or not source
            or source != expected_source
            or not isinstance(content_hash, str)
            or not HASH_PATTERN.fullmatch(content_hash)
        ):
            raise InstallError(f"invalid metadata for managed target: {relative_path!r}")
        result[relative_path] = ManagedFile(source=source, sha256=content_hash)
    return result


def _manifest_bytes(files: Mapping[str, ManagedFile]) -> bytes:
    payload = {
        "version": MANIFEST_VERSION,
        "files": {
            path: {"source": item.source, "sha256": item.sha256}
            for path, item in sorted(files.items())
        },
    }
    return (json.dumps(payload, indent=2, sort_keys=False) + "\n").encode("utf-8")


def _atomic_write(
    path: Path, content: bytes, *, guard: Callable[[], object] | None = None
) -> None:
    if guard is not None:
        guard()
    path.parent.mkdir(parents=True, exist_ok=True)
    if guard is not None:
        guard()
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if guard is not None:
            guard()
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _guard_target_state(
    project_root: Path,
    relative_path: str,
    *,
    expected_content: bytes | None,
) -> None:
    """Recheck a target immediately before an atomic create or replacement."""

    target = _target_path(project_root, relative_path)
    if expected_content is None:
        if os.path.lexists(target):
            raise InstallError(
                f"managed target appeared during installation: {relative_path!r}"
            )
        return
    if not target.exists():
        raise InstallError(f"managed target disappeared during refresh: {relative_path!r}")
    current = _stable_regular_file_bytes(
        target,
        guard=lambda: _target_path(project_root, relative_path),
    )
    if current != expected_content:
        raise InstallError(f"managed target changed during refresh: {relative_path!r}")


def _guard_manifest_state(project_root: Path, expected_content: bytes | None) -> None:
    """Prevent a concurrent manifest change from being silently overwritten."""

    manifest_path = _manifest_path(project_root)
    _reject_link_or_reparse_components(
        project_root,
        MANIFEST_RELATIVE_PATH.as_posix(),
        kind="runtime manifest",
    )
    if expected_content is None:
        if os.path.lexists(manifest_path):
            raise InstallError("runtime manifest appeared during installation")
        return
    if not manifest_path.exists():
        raise InstallError("runtime manifest disappeared during installation")
    current = _stable_regular_file_bytes(
        manifest_path,
        guard=lambda: _reject_link_or_reparse_components(
            project_root,
            MANIFEST_RELATIVE_PATH.as_posix(),
            kind="runtime manifest",
        ),
    )
    if current != expected_content:
        raise InstallError("runtime manifest changed during installation")


def _source_files(kit_root: Path, directory: Path, pattern: str) -> Iterable[Path]:
    _source_path(kit_root, directory)
    if not directory.is_dir():
        raise InstallError(f"runtime source directory does not exist: {directory}")
    for source in sorted(directory.glob(pattern), key=lambda item: item.name):
        _source_path(kit_root, source)
        if not source.is_file():
            raise InstallError(f"runtime source must be a regular file: {source}")
        yield source


def _source_tree_files(kit_root: Path, directory: Path) -> Iterable[Path]:
    _source_path(kit_root, directory)
    if not directory.is_dir():
        raise InstallError(f"canonical skill source directory does not exist: {directory}")
    for source in sorted(directory.rglob("*"), key=lambda item: item.as_posix()):
        _source_path(kit_root, source)
        if source.is_file():
            yield source
        elif not source.is_dir():
            raise InstallError(f"canonical skill source must be a regular file: {source}")


def _desired_files(kit_root: Path) -> dict[str, tuple[Path, bytes, ManagedFile]]:
    desired: dict[str, tuple[Path, bytes, ManagedFile]] = {}

    def add(relative_target: PurePosixPath, source: Path) -> None:
        _source_path(kit_root, source)
        if not source.is_file():
            raise InstallError(f"runtime source does not exist or is not regular: {source}")
        content = _stable_regular_file_bytes(
            source,
            guard=lambda source=source: _source_path(kit_root, source),
        )
        source_relative = source.relative_to(kit_root).as_posix()
        target_key = relative_target.as_posix()
        desired[target_key] = (
            source,
            content,
            ManagedFile(source=source_relative, sha256=sha256_bytes(content)),
        )

    codex_sources = kit_root / ".codex" / "agents"
    for source in _source_files(kit_root, codex_sources, "*.toml"):
        add(PurePosixPath(".codex/agents") / source.name, source)

    claude_sources = kit_root / ".claude" / "agents"
    for source in _source_files(kit_root, claude_sources, "*.md"):
        add(PurePosixPath(".claude/agents") / source.name, source)

    skill_sources = kit_root / "skills"
    for skill_name in CANONICAL_SKILLS:
        skill_root = skill_sources / skill_name
        entrypoint = skill_root / "SKILL.md"
        _source_path(kit_root, entrypoint)
        if not entrypoint.is_file():
            raise InstallError(f"canonical skill has no regular SKILL.md: {skill_root}")
        found = False
        for source in _source_tree_files(kit_root, skill_root):
            found = True
            relative_source = source.relative_to(skill_root)
            add(
                PurePosixPath(".agents/skills")
                / skill_name
                / PurePosixPath(relative_source.as_posix()),
                source,
            )
        if not found:
            raise InstallError(f"canonical skill source is empty: {skill_root}")

    add(
        PurePosixPath("AGENTS.md"),
        kit_root / "C10_Maestro" / "C10_Agent_ProjectRules.md",
    )
    add(
        PurePosixPath("CLAUDE.md"),
        kit_root / "C10_Maestro" / "C10_Agent_ClaudeProjectRules.md",
    )
    return desired


def install_runtime(
    kit_root: Path,
    project_root: Path,
    *,
    dry_run: bool = False,
    refresh_managed: bool = False,
) -> InstallResult:
    """Synchronize managed runtime files and return the planned/applied result."""

    kit_root = kit_root.expanduser().resolve()
    project_root = project_root.expanduser().resolve()
    _validate_layout(kit_root, project_root)
    if not project_root.is_dir():
        raise InstallError(f"project root does not exist: {project_root}")

    manifest_path = _manifest_path(project_root)
    initial_manifest = _manifest_snapshot(project_root)
    previous = _load_manifest(manifest_path, initial_manifest)
    desired = _desired_files(kit_root)
    next_manifest = dict(previous)
    result = InstallResult()

    for relative_path in sorted(set(previous) - set(desired)):
        target = _target_path(project_root, relative_path)
        if not target.exists():
            next_manifest.pop(relative_path, None)
            result.actions.append(f"forget missing {relative_path}")
        elif target.is_symlink() or not target.is_file():
            result.conflicts.append(
                f"preserve {relative_path}: managed target is no longer a regular file"
            )
        else:
            result.conflicts.append(
                f"preserve stale {relative_path}: an untrusted manifest cannot authorize deletion"
            )

    for relative_path, (_source, content, wanted) in sorted(desired.items()):
        target = _target_path(project_root, relative_path)
        old = previous.get(relative_path)

        if target.exists() and (target.is_symlink() or not target.is_file()):
            result.conflicts.append(f"preserve {relative_path}: target is not a regular file")
            continue

        if not target.exists():
            if not dry_run:
                _atomic_write(
                    target,
                    content,
                    guard=lambda relative_path=relative_path: _guard_target_state(
                        project_root,
                        relative_path,
                        expected_content=None,
                    ),
                )
            next_manifest[relative_path] = wanted
            result.actions.append(f"create {relative_path}")
            continue

        current_content = _stable_regular_file_bytes(
            target,
            guard=lambda relative_path=relative_path: _target_path(
                project_root, relative_path
            ),
        )
        current_hash = sha256_bytes(current_content)
        if current_hash == wanted.sha256:
            next_manifest[relative_path] = wanted
            result.unchanged += 1
            continue

        if old is None:
            result.conflicts.append(f"preserve {relative_path}: existing user file")
            continue

        if not refresh_managed:
            if current_hash == old.sha256:
                result.conflicts.append(
                    f"preserve {relative_path}: managed source changed; review and rerun "
                    "with --refresh-managed"
                )
            else:
                result.conflicts.append(
                    f"preserve {relative_path}: locally modified managed target"
                )
            continue

        if not _is_reachable_git_source_version(
            kit_root, wanted.source, current_content
        ):
            result.conflicts.append(
                f"preserve {relative_path}: current content is not a reachable Git "
                f"version of canonical source {wanted.source}"
            )
            continue

        if not dry_run:
            _atomic_write(
                target,
                content,
                guard=lambda relative_path=relative_path, current_content=current_content: (
                    _guard_target_state(
                        project_root,
                        relative_path,
                        expected_content=current_content,
                    )
                ),
            )
        next_manifest[relative_path] = wanted
        result.actions.append(f"update {relative_path}")

    current_manifest = _manifest_snapshot(project_root)
    if current_manifest != initial_manifest:
        raise InstallError("runtime manifest changed during installation")
    wanted_manifest = _manifest_bytes(next_manifest)
    result.manifest_changed = initial_manifest != wanted_manifest
    if result.manifest_changed and not dry_run:
        _atomic_write(
            manifest_path,
            wanted_manifest,
            guard=lambda initial_manifest=initial_manifest: _guard_manifest_state(
                project_root, initial_manifest
            ),
        )
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install Codex Agent Kit runtime adapters into PROJECT_ROOT safely."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        help="Project root; defaults to the parent of this .codex kit checkout.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="Do not write; return 1 when synchronization or conflict is detected.",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned actions without writing; conflicts still return 2.",
    )
    parser.add_argument(
        "--refresh-managed",
        action="store_true",
        help=(
            "After review, replace only previously managed targets whose current "
            "content matches the canonical source at a reachable Git commit."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    kit_root = default_kit_root()
    project_root = args.project_root or kit_root.parent
    try:
        result = install_runtime(
            kit_root,
            project_root,
            dry_run=args.check or args.dry_run,
            refresh_managed=args.refresh_managed,
        )
    except InstallError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for action in result.actions:
        print(action)
    for conflict in result.conflicts:
        print(f"conflict: {conflict}", file=sys.stderr)
    mode = "checked" if args.check else "planned" if args.dry_run else "installed"
    print(
        f"{mode}: {len(result.actions)} action(s), "
        f"{result.unchanged} unchanged, {len(result.conflicts)} conflict(s)"
    )

    if result.conflicts:
        return 2
    if args.check and result.drifted:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
