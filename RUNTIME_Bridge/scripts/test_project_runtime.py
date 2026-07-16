#!/usr/bin/env python3
"""Tests for the project runtime installer."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import install_project_runtime as installer


TEST_SKILLS = (
    "agent-forge",
    "architecture-blueprint",
    "codex-agent-kit",
    "gsd-tdd-cli-harness",
    "multi-agent-delivery",
    "spec-driven-breakdown",
)


class ProjectRuntimeInstallerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project_root = Path(self.temporary.name) / "project"
        self.kit_root = self.project_root / ".codex"
        (self.kit_root / ".codex" / "agents").mkdir(parents=True)
        (self.kit_root / ".claude" / "agents").mkdir(parents=True)
        (self.kit_root / "C10_Maestro").mkdir(parents=True)
        (self.kit_root / "RUNTIME_Bridge").mkdir(parents=True)
        for skill_name in TEST_SKILLS:
            skill_root = self.kit_root / "skills" / skill_name
            (skill_root / "agents").mkdir(parents=True)
            (skill_root / "SKILL.md").write_text(
                f"# {skill_name}\n", encoding="utf-8"
            )
            (skill_root / "agents" / "openai.yaml").write_text(
                f"name: {skill_name}\n", encoding="utf-8"
            )

        runtime_manifest = ["[runtime]", "schema_version = 1", ""]
        for skill_name in TEST_SKILLS:
            runtime_manifest.extend(
                [
                    "[[skills]]",
                    f'name = "{skill_name}"',
                    f'path = "skills/{skill_name}/SKILL.md"',
                    'purpose = "fixture"',
                    "",
                ]
            )
        (self.kit_root / "RUNTIME_Bridge" / "AGENT_RUNTIME_MAP.toml").write_text(
            "\n".join(runtime_manifest), encoding="utf-8"
        )

        (self.kit_root / ".codex" / "agents" / "architect.toml").write_text(
            'name = "architect"\n', encoding="utf-8"
        )
        (self.kit_root / ".claude" / "agents" / "architect.md").write_text(
            "# Architect\n", encoding="utf-8"
        )
        (self.kit_root / "C10_Maestro" / "C10_Agent_ProjectRules.md").write_text(
            "# Project rules\n", encoding="utf-8"
        )
        (
            self.kit_root / "C10_Maestro" / "C10_Agent_ClaudeProjectRules.md"
        ).write_text("# Claude rules\n", encoding="utf-8")
        self._git("init", "--quiet")
        self._git("config", "user.name", "Runtime Fixture")
        self._git("config", "user.email", "runtime-fixture@example.invalid")
        self._git("config", "core.autocrlf", "false")
        self._git("add", ".")
        self._git("commit", "--quiet", "-m", "fixture v1")

    def _git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.kit_root), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )

    def _write_manifest(self, files: dict[str, dict[str, str]]) -> None:
        manifest = {"version": installer.MANIFEST_VERSION, "files": files}
        (self.kit_root / ".runtime-install-manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    def _run_cli(self, *arguments: str) -> int:
        output = StringIO()
        with (
            patch.object(installer, "default_kit_root", return_value=self.kit_root),
            redirect_stdout(output),
            redirect_stderr(output),
        ):
            return installer.main(
                ["--project-root", str(self.project_root), *arguments]
            )

    def test_check_install_idempotency_and_user_file_preservation(self) -> None:
        user_file = self.project_root / ".codex" / "agents" / "user.toml"
        user_file.parent.mkdir(parents=True, exist_ok=True)
        user_file.write_text('name = "mine"\n', encoding="utf-8")

        check = installer.install_runtime(self.kit_root, self.project_root, dry_run=True)
        self.assertTrue(check.drifted)
        self.assertFalse((self.project_root / "AGENTS.md").exists())
        self.assertFalse((self.project_root / ".agents" / "skills").exists())

        first = installer.install_runtime(self.kit_root, self.project_root)
        self.assertEqual(first.conflicts, [])
        self.assertEqual(len(first.actions), 16)
        self.assertEqual(user_file.read_text(encoding="utf-8"), 'name = "mine"\n')
        self.assertEqual(
            (self.project_root / ".codex" / "agents" / "architect.toml").read_text(
                encoding="utf-8"
            ),
            'name = "architect"\n',
        )
        self.assertEqual(
            (
                self.project_root
                / ".agents"
                / "skills"
                / "architecture-blueprint"
                / "agents"
                / "openai.yaml"
            ).read_text(encoding="utf-8"),
            "name: architecture-blueprint\n",
        )

        manifest = self.kit_root / ".runtime-install-manifest.json"
        manifest_before = manifest.read_bytes()
        second = installer.install_runtime(self.kit_root, self.project_root)
        self.assertEqual(second.actions, [])
        self.assertEqual(second.conflicts, [])
        self.assertFalse(second.manifest_changed)
        self.assertEqual(manifest.read_bytes(), manifest_before)
        self.assertEqual(user_file.read_text(encoding="utf-8"), 'name = "mine"\n')

        clean_check = installer.install_runtime(
            self.kit_root, self.project_root, dry_run=True
        )
        self.assertFalse(clean_check.drifted)

    def test_source_drift_and_stale_wrappers_are_preserved_as_conflicts(self) -> None:
        installer.install_runtime(self.kit_root, self.project_root)
        codex_source = self.kit_root / ".codex" / "agents" / "architect.toml"
        codex_target = self.project_root / ".codex" / "agents" / "architect.toml"
        claude_target = self.project_root / ".claude" / "agents" / "architect.md"
        user_file = self.project_root / ".claude" / "agents" / "user.md"

        codex_source.write_text('name = "architect-v2"\n', encoding="utf-8")
        claude_target.write_text("# My custom wrapper\n", encoding="utf-8")
        user_file.write_text("# User-owned\n", encoding="utf-8")

        update = installer.install_runtime(self.kit_root, self.project_root)
        self.assertTrue(any(".codex/agents/architect.toml" in item for item in update.conflicts))
        self.assertTrue(any(".claude/agents/architect.md" in item for item in update.conflicts))
        self.assertEqual(codex_target.read_text(encoding="utf-8"), 'name = "architect"\n')
        self.assertEqual(claude_target.read_text(encoding="utf-8"), "# My custom wrapper\n")

        refreshed = installer.install_runtime(
            self.kit_root, self.project_root, refresh_managed=True
        )
        self.assertTrue(any(".claude/agents/architect.md" in item for item in refreshed.conflicts))
        self.assertIn("update .codex/agents/architect.toml", refreshed.actions)
        self.assertEqual(
            codex_target.read_text(encoding="utf-8"), 'name = "architect-v2"\n'
        )
        self.assertEqual(claude_target.read_text(encoding="utf-8"), "# My custom wrapper\n")

        codex_source.unlink()
        stale = installer.install_runtime(self.kit_root, self.project_root)
        self.assertTrue(
            any("stale .codex/agents/architect.toml" in item for item in stale.conflicts)
        )
        self.assertTrue(codex_target.exists())
        self.assertEqual(user_file.read_text(encoding="utf-8"), "# User-owned\n")
        self.assertEqual(claude_target.read_text(encoding="utf-8"), "# My custom wrapper\n")

        manifest = json.loads(
            (self.kit_root / ".runtime-install-manifest.json").read_text(encoding="utf-8")
        )
        self.assertIn(".codex/agents/architect.toml", manifest["files"])
        self.assertIn(".claude/agents/architect.md", manifest["files"])

    def test_existing_root_documents_are_not_overwritten(self) -> None:
        existing = self.project_root / "AGENTS.md"
        existing.write_text("# Project rules\n", encoding="utf-8")

        result = installer.install_runtime(self.kit_root, self.project_root)

        self.assertFalse(any("AGENTS.md" in item for item in result.conflicts))
        self.assertEqual(existing.read_text(encoding="utf-8"), "# Project rules\n")
        self.assertEqual(
            (self.project_root / "CLAUDE.md").read_text(encoding="utf-8"),
            "# Claude rules\n",
        )
        manifest = json.loads(
            (self.kit_root / ".runtime-install-manifest.json").read_text(encoding="utf-8")
        )
        self.assertIn("AGENTS.md", manifest["files"])

    def test_cli_check_is_read_only_and_reports_drift(self) -> None:
        drift_exit = self._run_cli("--check")
        self.assertEqual(drift_exit, 1)
        self.assertFalse((self.project_root / "AGENTS.md").exists())
        self.assertFalse(
            (self.kit_root / ".runtime-install-manifest.json").exists()
        )

        installer.install_runtime(self.kit_root, self.project_root)
        clean_exit = self._run_cli("--check")
        self.assertEqual(clean_exit, 0)

    def test_refresh_managed_dry_run_plans_without_writing(self) -> None:
        installer.install_runtime(self.kit_root, self.project_root)
        source = self.kit_root / ".codex" / "agents" / "architect.toml"
        target = self.project_root / ".codex" / "agents" / "architect.toml"
        source.write_text('name = "architect-v2"\n', encoding="utf-8")

        plan = installer.install_runtime(
            self.kit_root,
            self.project_root,
            dry_run=True,
            refresh_managed=True,
        )

        self.assertIn("update .codex/agents/architect.toml", plan.actions)
        self.assertEqual(target.read_text(encoding="utf-8"), 'name = "architect"\n')

    def test_refresh_after_reachable_git_upgrade(self) -> None:
        installer.install_runtime(self.kit_root, self.project_root)
        source = self.kit_root / ".codex" / "agents" / "architect.toml"
        target = self.project_root / ".codex" / "agents" / "architect.toml"
        source.write_text('name = "architect-v2"\n', encoding="utf-8")
        self._git("add", ".codex/agents/architect.toml")
        self._git("commit", "--quiet", "-m", "upgrade canonical wrapper")

        reviewed = installer.install_runtime(self.kit_root, self.project_root)
        self.assertTrue(
            any("--refresh-managed" in conflict for conflict in reviewed.conflicts)
        )
        refreshed = installer.install_runtime(
            self.kit_root, self.project_root, refresh_managed=True
        )

        self.assertIn("update .codex/agents/architect.toml", refreshed.actions)
        self.assertEqual(target.read_text(encoding="utf-8"), 'name = "architect-v2"\n')

    def test_refresh_allows_working_tree_source_drift_from_committed_target(self) -> None:
        installer.install_runtime(self.kit_root, self.project_root)
        source = self.kit_root / "skills" / "architecture-blueprint" / "SKILL.md"
        target = (
            self.project_root
            / ".agents"
            / "skills"
            / "architecture-blueprint"
            / "SKILL.md"
        )
        source.write_text("# Uncommitted architecture v2\n", encoding="utf-8")

        refreshed = installer.install_runtime(
            self.kit_root, self.project_root, refresh_managed=True
        )

        self.assertIn(
            "update .agents/skills/architecture-blueprint/SKILL.md",
            refreshed.actions,
        )
        self.assertEqual(
            target.read_text(encoding="utf-8"),
            "# Uncommitted architecture v2\n",
        )

    def test_tampered_stale_manifest_cannot_delete_user_owned_file(self) -> None:
        user_file = self.project_root / ".codex" / "agents" / "user.toml"
        user_file.parent.mkdir(parents=True, exist_ok=True)
        user_file.write_text('name = "user-owned"\n', encoding="utf-8")
        self._write_manifest(
            {
                ".codex/agents/user.toml": {
                    "source": ".codex/agents/user.toml",
                    "sha256": installer.sha256_file(user_file),
                }
            }
        )

        exit_code = self._run_cli("--refresh-managed")

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            user_file.read_text(encoding="utf-8"),
            'name = "user-owned"\n',
        )

    def test_tampered_manifest_cannot_authorize_overwrite(self) -> None:
        installer.install_runtime(self.kit_root, self.project_root)
        target = (
            self.project_root
            / ".agents"
            / "skills"
            / "architecture-blueprint"
            / "SKILL.md"
        )
        source = (
            self.kit_root / "skills" / "architecture-blueprint" / "SKILL.md"
        )
        target.write_text("# User customization\n", encoding="utf-8")
        manifest_path = self.kit_root / ".runtime-install-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"][
            ".agents/skills/architecture-blueprint/SKILL.md"
        ]["sha256"] = installer.sha256_file(target)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        source.write_text("# Malicious replacement\n", encoding="utf-8")

        exit_code = self._run_cli("--refresh-managed")

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            target.read_text(encoding="utf-8"),
            "# User customization\n",
        )

    def test_refresh_proof_is_bound_to_the_exact_canonical_source_path(self) -> None:
        installer.install_runtime(self.kit_root, self.project_root)
        target = (
            self.project_root
            / ".agents"
            / "skills"
            / "architecture-blueprint"
            / "SKILL.md"
        )
        other_source = (
            self.kit_root / "skills" / "spec-driven-breakdown" / "SKILL.md"
        )
        target.write_bytes(other_source.read_bytes())
        manifest_path = self.kit_root / ".runtime-install-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"][
            ".agents/skills/architecture-blueprint/SKILL.md"
        ]["sha256"] = installer.sha256_file(target)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        architecture_source = (
            self.kit_root / "skills" / "architecture-blueprint" / "SKILL.md"
        )
        architecture_source.write_text("# Architecture v2\n", encoding="utf-8")

        result = installer.install_runtime(
            self.kit_root, self.project_root, refresh_managed=True
        )

        self.assertTrue(
            any(
                "not a reachable Git version" in conflict
                for conflict in result.conflicts
            )
        )
        self.assertEqual(target.read_bytes(), other_source.read_bytes())

    def test_refresh_does_not_trust_content_reachable_only_from_lateral_ref(self) -> None:
        installer.install_runtime(self.kit_root, self.project_root)
        main_branch = self._git("branch", "--show-current").stdout.strip()
        source = self.kit_root / "skills" / "architecture-blueprint" / "SKILL.md"
        target = (
            self.project_root
            / ".agents"
            / "skills"
            / "architecture-blueprint"
            / "SKILL.md"
        )
        self._git("switch", "--quiet", "-c", "untrusted-lateral")
        source.write_text("# Lateral-only content\n", encoding="utf-8")
        self._git("add", "skills/architecture-blueprint/SKILL.md")
        self._git("commit", "--quiet", "-m", "lateral content")
        lateral_content = source.read_bytes()
        self._git("switch", "--quiet", main_branch)

        target.write_bytes(lateral_content)
        manifest_path = self.kit_root / ".runtime-install-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"][
            ".agents/skills/architecture-blueprint/SKILL.md"
        ]["sha256"] = installer.sha256_file(target)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        source.write_text("# Legitimate worktree update\n", encoding="utf-8")

        result = installer.install_runtime(
            self.kit_root, self.project_root, refresh_managed=True
        )

        self.assertTrue(
            any(
                "not a reachable Git version" in conflict
                for conflict in result.conflicts
            )
        )
        self.assertEqual(target.read_bytes(), lateral_content)

    def test_manifest_change_after_initial_parse_aborts_installation(self) -> None:
        installer.install_runtime(self.kit_root, self.project_root)
        manifest_path = self.kit_root / ".runtime-install-manifest.json"
        original_desired_files = installer._desired_files

        def tamper_after_manifest_parse(kit_root: Path):
            desired = original_desired_files(kit_root)
            manifest_path.write_text('{"concurrent": true}\n', encoding="utf-8")
            return desired

        with (
            patch.object(
                installer,
                "_desired_files",
                side_effect=tamper_after_manifest_parse,
            ),
            self.assertRaisesRegex(
                installer.InstallError,
                "manifest changed during installation",
            ),
        ):
            installer.install_runtime(self.kit_root, self.project_root)

    def test_refresh_aborts_if_target_changes_before_atomic_replace(self) -> None:
        installer.install_runtime(self.kit_root, self.project_root)
        source = self.kit_root / ".codex" / "agents" / "architect.toml"
        target = self.project_root / ".codex" / "agents" / "architect.toml"
        source.write_text('name = "architect-v2"\n', encoding="utf-8")
        original_atomic_write = installer._atomic_write

        def race_target(path: Path, content: bytes, *, guard=None) -> None:
            if path == target:
                target.write_text('name = "concurrent-user-change"\n', encoding="utf-8")
            original_atomic_write(path, content, guard=guard)

        with (
            patch.object(installer, "_atomic_write", side_effect=race_target),
            self.assertRaisesRegex(
                installer.InstallError,
                "managed target changed during refresh",
            ),
        ):
            installer.install_runtime(
                self.kit_root,
                self.project_root,
                refresh_managed=True,
            )

        self.assertEqual(
            target.read_text(encoding="utf-8"),
            'name = "concurrent-user-change"\n',
        )

    def test_manifest_rejects_traversal_and_absolute_targets(self) -> None:
        user_file = Path(self.temporary.name) / "outside-user-file.txt"
        user_file.write_text("do not delete\n", encoding="utf-8")
        malicious_targets = (
            "../outside-user-file.txt",
            user_file.resolve().as_posix(),
        )

        for malicious_target in malicious_targets:
            with self.subTest(target=malicious_target):
                self._write_manifest(
                    {
                        malicious_target: {
                            "source": malicious_target,
                            "sha256": installer.sha256_file(user_file),
                        }
                    }
                )
                self.assertEqual(self._run_cli(), 2)
                self.assertEqual(
                    user_file.read_text(encoding="utf-8"),
                    "do not delete\n",
                )

    def test_manifest_rejects_mismatched_traversal_and_absolute_sources(self) -> None:
        user_file = self.project_root / ".codex" / "agents" / "user.toml"
        user_file.parent.mkdir(parents=True, exist_ok=True)
        user_file.write_text("user content\n", encoding="utf-8")
        malicious_sources = (
            "skills/agent-forge/SKILL.md",
            "../user.toml",
            user_file.resolve().as_posix(),
        )

        for malicious_source in malicious_sources:
            with self.subTest(source=malicious_source):
                self._write_manifest(
                    {
                        ".codex/agents/user.toml": {
                            "source": malicious_source,
                            "sha256": installer.sha256_file(user_file),
                        }
                    }
                )
                self.assertEqual(self._run_cli(), 2)
                self.assertEqual(
                    user_file.read_text(encoding="utf-8"),
                    "user content\n",
                )

    def test_manifest_rejects_external_symlink_target(self) -> None:
        external = Path(self.temporary.name) / "external-user-file.toml"
        external.write_text("external content\n", encoding="utf-8")
        target = self.project_root / ".codex" / "agents" / "linked.toml"
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.symlink_to(external)
        except OSError as exc:
            if os.name != "nt":
                self.skipTest(f"symlink creation is unavailable: {exc}")
            target.parent.rmdir()
            external_directory = Path(self.temporary.name) / "external-agents"
            external_directory.mkdir()
            external = external_directory / "linked.toml"
            external.write_text("external content\n", encoding="utf-8")
            junction = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(target.parent), str(external_directory)],
                check=False,
                capture_output=True,
                text=True,
            )
            if junction.returncode != 0:
                self.skipTest(
                    f"symlink and junction creation are unavailable: {exc}; "
                    f"{junction.stderr.strip()}"
                )
        self._write_manifest(
            {
                ".codex/agents/linked.toml": {
                    "source": ".codex/agents/linked.toml",
                    "sha256": installer.sha256_file(external),
                }
            }
        )

        self.assertEqual(self._run_cli(), 2)
        self.assertEqual(external.read_text(encoding="utf-8"), "external content\n")
        self.assertTrue(
            target.is_symlink() or installer._is_link_or_reparse(target.parent)
        )

    def test_missing_canonical_skill_entrypoint_is_rejected(self) -> None:
        (
            self.kit_root / "skills" / "codex-agent-kit" / "SKILL.md"
        ).unlink()

        with self.assertRaisesRegex(
            installer.InstallError,
            "canonical skill has no regular SKILL.md",
        ):
            installer.install_runtime(self.kit_root, self.project_root)

        self.assertFalse((self.project_root / ".agents" / "skills").exists())

    def test_runtime_manifest_is_the_exhaustive_skill_source_of_truth(self) -> None:
        unlisted = self.kit_root / "skills" / "unlisted-skill"
        unlisted.mkdir()
        (unlisted / "SKILL.md").write_text("# Unlisted\n", encoding="utf-8")

        with self.assertRaisesRegex(
            installer.InstallError,
            "runtime skill catalog mismatch.*unlisted-skill",
        ):
            installer.install_runtime(self.kit_root, self.project_root)

    def test_runtime_manifest_rejects_noncanonical_skill_path_and_schema(self) -> None:
        manifest_path = (
            self.kit_root / "RUNTIME_Bridge" / "AGENT_RUNTIME_MAP.toml"
        )
        original = manifest_path.read_text(encoding="utf-8")
        manifest_path.write_text(
            original.replace(
                "skills/agent-forge/SKILL.md",
                "skills/agent-forge/../architecture-blueprint/SKILL.md",
                1,
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(installer.InstallError, "must use manifest path"):
            installer.install_runtime(self.kit_root, self.project_root)

        manifest_path.write_text(
            original.replace("schema_version = 1", "schema_version = 99", 1),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(installer.InstallError, "unsupported runtime manifest schema"):
            installer.install_runtime(self.kit_root, self.project_root)

    def test_skill_source_drift_conflict_and_unmanaged_skill_preservation(self) -> None:
        unmanaged_skill = (
            self.project_root / ".agents" / "skills" / "user-skill" / "SKILL.md"
        )
        unmanaged_skill.parent.mkdir(parents=True)
        unmanaged_skill.write_text("# User skill\n", encoding="utf-8")
        installer.install_runtime(self.kit_root, self.project_root)

        updated_source = (
            self.kit_root / "skills" / "architecture-blueprint" / "SKILL.md"
        )
        updated_target = (
            self.project_root
            / ".agents"
            / "skills"
            / "architecture-blueprint"
            / "SKILL.md"
        )
        conflicted_source = (
            self.kit_root / "skills" / "spec-driven-breakdown" / "SKILL.md"
        )
        conflicted_target = (
            self.project_root
            / ".agents"
            / "skills"
            / "spec-driven-breakdown"
            / "SKILL.md"
        )
        updated_source.write_text("# Architecture v2\n", encoding="utf-8")
        conflicted_source.write_text("# Spec source v2\n", encoding="utf-8")
        conflicted_target.write_text("# Project customization\n", encoding="utf-8")

        result = installer.install_runtime(self.kit_root, self.project_root)

        self.assertTrue(
            any(
                ".agents/skills/architecture-blueprint/SKILL.md" in conflict
                for conflict in result.conflicts
            )
        )
        self.assertTrue(
            any(
                ".agents/skills/spec-driven-breakdown/SKILL.md" in conflict
                for conflict in result.conflicts
            )
        )
        self.assertEqual(
            updated_target.read_text(encoding="utf-8"),
            "# architecture-blueprint\n",
        )
        self.assertEqual(
            conflicted_target.read_text(encoding="utf-8"),
            "# Project customization\n",
        )
        self.assertEqual(unmanaged_skill.read_text(encoding="utf-8"), "# User skill\n")

        refreshed = installer.install_runtime(
            self.kit_root, self.project_root, refresh_managed=True
        )
        self.assertIn(
            "update .agents/skills/architecture-blueprint/SKILL.md",
            refreshed.actions,
        )
        self.assertTrue(
            any(
                ".agents/skills/spec-driven-breakdown/SKILL.md" in conflict
                for conflict in refreshed.conflicts
            )
        )
        self.assertEqual(updated_target.read_text(encoding="utf-8"), "# Architecture v2\n")
        self.assertEqual(
            conflicted_target.read_text(encoding="utf-8"),
            "# Project customization\n",
        )

    def test_external_reparse_source_directory_is_rejected(self) -> None:
        source_directory = self.kit_root / ".codex" / "agents"
        external_directory = Path(self.temporary.name) / "external-agents"
        external_directory.mkdir()
        (external_directory / "external.toml").write_text(
            'name = "EXTERNAL"\n', encoding="utf-8"
        )
        for child in source_directory.iterdir():
            child.unlink()
        source_directory.rmdir()
        try:
            source_directory.symlink_to(external_directory, target_is_directory=True)
        except OSError as exc:
            if os.name != "nt":
                self.skipTest(f"directory symlink creation is unavailable: {exc}")
            junction = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(source_directory), str(external_directory)],
                check=False,
                capture_output=True,
                text=True,
            )
            if junction.returncode != 0:
                self.skipTest(
                    f"directory symlink and junction creation are unavailable: {exc}; "
                    f"{junction.stderr.strip()}"
                )

        with self.assertRaisesRegex(installer.InstallError, "runtime source.*reparse"):
            installer.install_runtime(self.kit_root, self.project_root)
        self.assertFalse(
            (self.project_root / ".codex" / "agents" / "external.toml").exists()
        )

    def test_stale_managed_skill_file_and_directories_are_preserved(self) -> None:
        source = (
            self.kit_root
            / "skills"
            / "agent-forge"
            / "assets"
            / "nested"
            / "legacy.txt"
        )
        source.parent.mkdir(parents=True)
        source.write_text("legacy\n", encoding="utf-8")
        installer.install_runtime(self.kit_root, self.project_root)
        target = (
            self.project_root
            / ".agents"
            / "skills"
            / "agent-forge"
            / "assets"
            / "nested"
            / "legacy.txt"
        )
        custom = target.parents[1] / "keep.txt"
        custom.write_text("keep\n", encoding="utf-8")
        source.unlink()

        result = installer.install_runtime(self.kit_root, self.project_root)

        self.assertTrue(
            any(
                "stale .agents/skills/agent-forge/assets/nested/legacy.txt"
                in conflict
                for conflict in result.conflicts
            )
        )
        self.assertTrue(target.exists())
        self.assertTrue(target.parent.exists())
        self.assertTrue(target.parents[1].is_dir())
        self.assertEqual(custom.read_text(encoding="utf-8"), "keep\n")

    def test_missing_stale_skill_file_is_forgotten_without_directory_cleanup(self) -> None:
        source = (
            self.kit_root
            / "skills"
            / "multi-agent-delivery"
            / "assets"
            / "old"
            / "prompt.txt"
        )
        source.parent.mkdir(parents=True)
        source.write_text("prompt\n", encoding="utf-8")
        installer.install_runtime(self.kit_root, self.project_root)
        target = (
            self.project_root
            / ".agents"
            / "skills"
            / "multi-agent-delivery"
            / "assets"
            / "old"
            / "prompt.txt"
        )
        target.unlink()
        source.unlink()

        result = installer.install_runtime(self.kit_root, self.project_root)

        self.assertIn(
            "forget missing .agents/skills/multi-agent-delivery/assets/old/prompt.txt",
            result.actions,
        )
        self.assertTrue(target.parent.exists())
        self.assertTrue(target.parents[1].exists())
        self.assertTrue(target.parents[2].is_dir())


if __name__ == "__main__":
    unittest.main(verbosity=2)
