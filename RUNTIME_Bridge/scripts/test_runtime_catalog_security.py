"""Adversarial tests for runtime catalog path and synchronization security."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sync = _load("runtime_sync_security", "sync_claude_from_codex.py")
validator = _load("runtime_validator_security", "validate_arsenal.py")


class VerdictContractParsingTests(unittest.TestCase):
    def test_labeled_verdict_line_is_collected(self) -> None:
        text = """## Definition Of Ready
**Veredito DoR:** APROVADO | APROVADO_COM_RESSALVAS | QUESTIONAR | REPROVADO
## Next
ignored
"""
        section = validator._verdict_section(text)
        self.assertIn("Veredito DoR", section)
        self.assertNotIn("ignored", section)

    def test_fenced_commented_and_indented_verdicts_are_not_semantic(self) -> None:
        hidden = """<!-- ## Veredito
APROVADO APROVADO_COM_RESSALVAS QUESTIONAR REPROVADO
-->
```md
## Veredito
APROVADO APROVADO_COM_RESSALVAS QUESTIONAR REPROVADO
```
    ## Veredito
    APROVADO APROVADO_COM_RESSALVAS QUESTIONAR REPROVADO
"""
        semantic = validator._mask_nonsemantic_markdown(hidden)
        self.assertEqual(validator._verdict_section(semantic), "")

    def test_commented_yaml_fields_do_not_count(self) -> None:
        fields = validator._simple_yaml_fields(
            "# display_name: Fake\n# short_description: Fake\n# default_prompt: Use $fake\n"
        )
        self.assertEqual(fields, {})

    def test_openai_yaml_fields_must_belong_to_interface(self) -> None:
        invalid_documents = (
            "metadata:\n  display_name: Fake\n  short_description: Fake\n"
            "  default_prompt: Use $fake\n",
            "  display_name: Fake\n  short_description: Fake\n"
            "  default_prompt: Use $fake\n",
        )
        for document in invalid_documents:
            with self.subTest(document=document):
                self.assertEqual(validator._simple_yaml_fields(document), {})

        valid = validator._simple_yaml_fields(
            "interface:\n  display_name: Real\n  short_description: Useful\n"
            "  default_prompt: Use $real\n"
        )
        self.assertEqual(valid["display_name"], "Real")

    def test_verdict_contract_cannot_be_satisfied_only_by_fenced_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            kit = Path(directory)
            contract = kit / "contract.md"
            contract.write_text(
                "```md\n## Veredito\n"
                "APROVADO APROVADO_COM_RESSALVAS QUESTIONAR REPROVADO\n```\n",
                encoding="utf-8",
            )
            manifest = {
                "verdicts": {
                    "canonical": sorted(validator.CANONICAL_VERDICTS),
                    "forbidden": [],
                    "contract_files": ["contract.md"],
                }
            }
            errors: list[str] = []
            validator.validate_verdicts(kit, manifest, errors)
            self.assertIn("canonical verdicts missing", "\n".join(errors))

    def test_hidden_raw_html_cannot_supply_verdict_contract(self) -> None:
        hidden = (
            '<div hidden>\n## Veredito\n'
            'APROVADO APROVADO_COM_RESSALVAS QUESTIONAR REPROVADO\n</div>\n'
        )
        semantic = validator._mask_nonsemantic_markdown(hidden)
        self.assertEqual(validator._verdict_section(semantic), "")

        for tag in ("script", "style", "template", "details"):
            with self.subTest(tag=tag):
                wrapped = f"<{tag}>\n## Veredito\nAPROVADO\n</{tag}>\n"
                self.assertEqual(
                    validator._verdict_section(
                        validator._mask_nonsemantic_markdown(wrapped)
                    ),
                    "",
                )

        multiline_wrappers = (
            "<div\n hidden>\n## Veredito\nAPROVADO\n</div>\n",
            "<div hidden\n>\n## Veredito\nAPROVADO\n</div>\n",
            "<x:div hidden\n>\n## Veredito\nAPROVADO\n</x:div>\n",
            "<div hidden/>\n## Veredito\nAPROVADO\n</div>\n",
        )
        for wrapped in multiline_wrappers:
            with self.subTest(wrapped=wrapped):
                self.assertEqual(
                    validator._verdict_section(
                        validator._mask_nonsemantic_markdown(wrapped)
                    ),
                    "",
                )


class RuntimeFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "RUNTIME_Bridge").mkdir(parents=True)
        (root / ".codex" / "agents").mkdir(parents=True)
        (root / ".claude" / "agents").mkdir(parents=True)
        (root / "Source").mkdir()
        (root / "Source" / "Agent.md").write_text("# Agent\n", encoding="utf-8")
        (root / "RUNTIME_Bridge" / "AGENT_RUNTIME_MAP.toml").write_text(
            """
[[agents]]
name = "sample-agent"
source = "Source/Agent.md"
alias = "@SAMPLE"
purpose = "Exercise synchronization."
""".lstrip(),
            encoding="utf-8",
        )
        self.codex_body = (
            'name = "sample-agent"\n'
            'description = "Sample wrapper"\n'
            'developer_instructions = "Read the source completely."\n'
        )
        (root / ".codex" / "agents" / "sample-agent.toml").write_text(
            self.codex_body, encoding="utf-8"
        )


class SyncSecurityTests(unittest.TestCase):
    def test_unmanaged_claude_wrapper_is_preserved_and_blocks_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = RuntimeFixture(Path(directory))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sync.synchronize(fixture.root), 0)
            custom = fixture.root / ".claude" / "agents" / "custom-local.md"
            custom.write_text("user owned\n", encoding="utf-8")

            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(sync.synchronize(fixture.root, check=True), 1)
                self.assertEqual(sync.synchronize(fixture.root, check=False), 1)
            self.assertEqual(custom.read_text(encoding="utf-8"), "user owned\n")

    def test_generated_write_is_atomic_and_leaves_no_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = RuntimeFixture(Path(directory))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sync.synchronize(fixture.root), 0)
            target = fixture.root / ".claude" / "agents" / "sample-agent.md"
            self.assertIn("name: sample-agent", target.read_text(encoding="utf-8"))
            self.assertEqual(list(target.parent.glob(".*.tmp")), [])

    def test_external_codex_wrapper_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            fixture = RuntimeFixture(Path(directory))
            wrapper = fixture.root / ".codex" / "agents" / "sample-agent.toml"
            wrapper.unlink()
            external = Path(outside) / "sample-agent.toml"
            external.write_text(fixture.codex_body, encoding="utf-8")
            try:
                wrapper.symlink_to(external)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable on this platform: {exc}")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(sync.synchronize(fixture.root), 1)

    def test_external_claude_target_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            fixture = RuntimeFixture(Path(directory))
            target = fixture.root / ".claude" / "agents" / "sample-agent.md"
            external = Path(outside) / "sample-agent.md"
            external.write_text("external target\n", encoding="utf-8")
            try:
                target.symlink_to(external)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable on this platform: {exc}")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(sync.synchronize(fixture.root), 1)
            self.assertEqual(
                external.read_text(encoding="utf-8"), "external target\n"
            )


class ValidatorPathSecurityTests(unittest.TestCase):
    def test_manifest_rejects_traversal_and_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            kit = Path(directory)
            errors: list[str] = []
            manifest = {
                "agents": [
                    {
                        "name": "traversal-agent",
                        "source": "../outside.md",
                        "alias": "@T",
                        "purpose": "test",
                    },
                    {
                        "name": "absolute-agent",
                        "source": str((kit.parent / "outside.md").resolve()),
                        "alias": "@A",
                        "purpose": "test",
                    },
                ],
                "skills": [],
            }
            validator._manifest_indexes(kit, manifest, errors)
            joined = "\n".join(errors)
            self.assertIn("parent traversal is forbidden", joined)
            self.assertIn("absolute paths are forbidden", joined)

    def test_manifest_rejects_external_source_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            kit = Path(directory)
            link = kit / "linked.md"
            external = Path(outside) / "external.md"
            external.write_text("external\n", encoding="utf-8")
            try:
                link.symlink_to(external)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable on this platform: {exc}")
            errors: list[str] = []
            manifest = {
                "agents": [
                    {
                        "name": "linked-agent",
                        "source": "linked.md",
                        "alias": "@L",
                        "purpose": "test",
                    }
                ],
                "skills": [],
            }
            validator._manifest_indexes(kit, manifest, errors)
            self.assertIn("outside kit root", "\n".join(errors))

    def test_broken_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            kit = Path(directory)
            link = kit / "broken.md"
            try:
                link.symlink_to(kit / "missing.md")
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable on this platform: {exc}")
            errors: list[str] = []
            self.assertIsNone(
                validator._validate_governed_path(
                    kit, "broken.md", "broken source", errors, expect_file=True
                )
            )
            self.assertIn("broken symlink/reparse point", "\n".join(errors))


class GitPolicyTests(unittest.TestCase):
    def _validate(self, results: list[tuple[int, str]]) -> tuple[list[str], str]:
        errors: list[str] = []
        warnings: list[str] = []
        with mock.patch.object(validator, "_git", side_effect=results):
            status = validator.validate_versioning(Path.cwd(), errors, warnings)
        return errors, status

    def test_remote_command_failure_is_an_error(self) -> None:
        errors, status = self._validate([(0, ".git"), (1, ""), (0, "")])
        self.assertIn("git remote -v failed", "\n".join(errors))
        self.assertEqual(status, "git remote error")

    def test_non_github_remote_is_an_error(self) -> None:
        errors, status = self._validate(
            [
                (0, ".git"),
                (
                    0,
                    "origin https://gitlab.example/team/kit.git (fetch)\n"
                    "origin https://gitlab.example/team/kit.git (push)",
                ),
                (0, ""),
            ]
        )
        self.assertIn("requires GitHub", "\n".join(errors))
        self.assertEqual(status, "git without governed GitHub origin")

    def test_github_decoy_does_not_override_non_github_origin(self) -> None:
        errors, status = self._validate(
            [
                (0, ".git"),
                (
                    0,
                    "origin https://gitlab.example/team/kit.git (fetch)\n"
                    "origin https://gitlab.example/team/kit.git (push)\n"
                    "decoy https://github.com/team/kit.git (fetch)",
                ),
                (0, ""),
            ]
        )
        self.assertIn("requires GitHub", "\n".join(errors))
        self.assertEqual(status, "git without governed GitHub origin")

    def test_status_command_failure_is_an_error(self) -> None:
        errors, status = self._validate(
            [
                (0, ".git"),
                (
                    0,
                    "origin git@github.com:team/kit.git (fetch)\n"
                    "origin git@github.com:team/kit.git (push)",
                ),
                (1, ""),
            ]
        )
        self.assertIn("git status --porcelain failed", "\n".join(errors))
        self.assertEqual(status, "git status error")

    def test_github_https_and_ssh_remotes_are_accepted(self) -> None:
        for remote in (
            "origin https://github.com/team/kit.git (fetch)\n"
            "origin https://github.com/team/kit.git (push)",
            "origin ssh://git@github.com/team/kit.git (fetch)\n"
            "origin ssh://git@github.com/team/kit.git (push)",
        ):
            with self.subTest(remote=remote):
                errors, status = self._validate(
                    [(0, ".git"), (0, remote), (0, "")]
                )
                self.assertEqual(errors, [])
                self.assertEqual(status, "git ok")


if __name__ == "__main__":
    unittest.main()
