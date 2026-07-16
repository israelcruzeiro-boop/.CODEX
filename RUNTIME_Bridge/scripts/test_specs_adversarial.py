from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_specs  # noqa: E402
from test_governance_validators import VALID_SPEC  # noqa: E402


class SpecAdversarialTests(unittest.TestCase):
    def _project(
        self, specs: dict[str, str]
    ) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        project = Path(temporary.name)
        root = project / ".codex" / "specs"
        changes = root / "changes"
        changes.mkdir(parents=True)
        for name, content in specs.items():
            change = changes / name
            change.mkdir()
            (change / "spec.md").write_text(content, encoding="utf-8")
        (root / "EXECUTAR-TODAS.md").write_text(
            "# Queue\n" + "".join(f"- {name}\n" for name in specs),
            encoding="utf-8",
        )
        return temporary, project

    def _codes(self, specs: dict[str, str]) -> set[str]:
        temporary, project = self._project(specs)
        self.addCleanup(temporary.cleanup)
        return {issue.code for issue in validate_specs.validate_specs(project).errors}

    def test_current_complete_fixture_remains_valid(self) -> None:
        temporary, project = self._project({"001-publish-item": VALID_SPEC})
        self.addCleanup(temporary.cleanup)
        result = validate_specs.validate_specs(project)
        self.assertTrue(result.ok, result.to_dict())

    def test_spec_id_must_match_change_number(self) -> None:
        self.assertIn(
            "spec-id-mismatch",
            self._codes({"002-publish-item": VALID_SPEC}),
        )

    def test_cross_spec_qualified_reference_resolves(self) -> None:
        second = VALID_SPEC.replace("**Spec:** SPEC-001", "**Spec:** SPEC-002")
        second = second.replace(
            "## 7. Doubt\nNo blocking gaps.",
            "## 7. Doubt\nDepends on SPEC-001:REQ-001; no blocking gaps.",
        )
        temporary, project = self._project(
            {"001-publish-item": VALID_SPEC, "002-reuse-module": second}
        )
        self.addCleanup(temporary.cleanup)
        result = validate_specs.validate_specs(project)
        self.assertTrue(result.ok, result.to_dict())

    def test_unknown_cross_spec_and_unknown_cross_spec_id_are_rejected(self) -> None:
        absent_spec = VALID_SPEC.replace(
            "No blocking gaps.", "Depends on SPEC-999:REQ-001."
        )
        self.assertIn(
            "unknown-cross-spec",
            self._codes({"001-publish-item": absent_spec}),
        )
        absent_id = VALID_SPEC.replace(
            "No blocking gaps.", "Depends on SPEC-001:REQ-999."
        )
        self.assertIn(
            "unknown-cross-spec-id",
            self._codes({"001-publish-item": absent_id}),
        )

    def test_incomplete_nfr_is_rejected(self) -> None:
        bad = VALID_SPEC.replace(
            "| NFR-001 | performance | p95 under 200ms | TEST-001 |",
            "| NFR-001 | | | |",
        )
        self.assertIn("incomplete-nfr", self._codes({"001-publish-item": bad}))

    def test_blank_rollout_is_rejected(self) -> None:
        bad = VALID_SPEC.replace(
            "## 10. Rollout E Rollback\n"
            "Deploy canary; rollback application artifact on failed smoke.\n"
            "## 11.",
            "## 10. Rollout E Rollback\n\n## 11.",
        )
        self.assertIn("missing-rollout-plan", self._codes({"001-publish-item": bad}))

    def test_approved_requires_every_checkbox_checked(self) -> None:
        bad = VALID_SPEC.replace("- [x] Requirements are testable.", "- [ ] Requirements are testable.")
        self.assertIn(
            "inconsistent-approved-checklist",
            self._codes({"001-publish-item": bad}),
        )

    def test_dor_and_dod_require_exactly_one_verdict(self) -> None:
        for label in ("DoR", "DoD"):
            for duplicate in ("APROVADO", "REPROVADO"):
                with self.subTest(label=label, duplicate=duplicate):
                    original = f"**Veredito {label}:** APROVADO"
                    bad = VALID_SPEC.replace(
                        original,
                        f"{original}\n**Veredito {label}:** {duplicate}",
                    )
                    self.assertIn(
                        "duplicate-verdict",
                        self._codes({"001-publish-item": bad}),
                    )

    def _with_reservations(self, label: str, closure: str) -> str:
        return VALID_SPEC.replace(
            f"**Veredito {label}:** APROVADO",
            f"**Veredito {label}:** APROVADO_COM_RESSALVAS\n"
            "**Lacuna nao bloqueante:** smoke de staging ainda nao executado\n"
            "**Acao:** executar smoke isolado e anexar o relatorio\n"
            "**Dono:** equipe QA\n"
            f"**Prazo ISO/criterio verificavel:** {closure}",
        )

    def test_approved_with_reservations_requires_structured_followup(self) -> None:
        for label in ("DoR", "DoD"):
            good = self._with_reservations(label, "2026-07-20")
            for field, value in (
                ("Lacuna nao bloqueante", "x"),
                ("Acao", "x"),
                ("Dono", "x"),
                ("Prazo ISO/criterio verificavel", "x"),
                ("Prazo ISO/criterio verificavel", "2026-02-30"),
                ("Prazo ISO/criterio verificavel", "ate revisao manual"),
            ):
                with self.subTest(label=label, field=field, value=value):
                    bad = re.sub(
                        rf"(?m)^\*\*{re.escape(field)}:\*\*.*$",
                        f"**{field}:** {value}",
                        good,
                    )
                    self.assertIn(
                        "incomplete-reservations",
                        self._codes({"001-publish-item": bad}),
                    )

    def test_approved_with_reservations_accepts_iso_date_or_verifiable_criterion(self) -> None:
        for label in ("DoR", "DoD"):
            for closure in (
                "2026-07-20",
                "TEST-001 passa e EVD-001 fica registrado",
            ):
                with self.subTest(label=label, closure=closure):
                    good = self._with_reservations(label, closure)
                    temporary, project = self._project({"001-publish-item": good})
                    self.addCleanup(temporary.cleanup)
                    result = validate_specs.validate_specs(project)
                    self.assertTrue(result.ok, result.to_dict())

    def test_questionar_and_reprovado_are_blocking(self) -> None:
        for verdict in ("QUESTIONAR", "REPROVADO"):
            with self.subTest(verdict=verdict):
                bad = VALID_SPEC.replace("**Veredito DoR:** APROVADO", f"**Veredito DoR:** {verdict}")
                self.assertIn(
                    "blocking-verdict",
                    self._codes({"001-publish-item": bad}),
                )

    def test_traceability_is_bidirectional(self) -> None:
        bad = VALID_SPEC.replace(
            "| TASK-001 | Implement publish | backend | REQ-001 | endpoint | src/app.py | src/publish.py | none | TEST-001 / EVD-001 |",
            "| TASK-001 | Implement publish | backend | REQ-001 | endpoint | src/app.py | src/publish.py | none | TEST-001 / EVD-001 |\n"
            "| TASK-002 | Orphan work | backend | MOD-001 | helper | src/orphan-input.py | src/orphan.py | TASK-001 | TEST-002 / EVD-002 |",
        )
        bad = bad.replace(
            "| TEST-001 | REQ-001 / AC-001 / NFR-001 | integration | all assertions pass |",
            "| TEST-001 | REQ-001 / AC-001 / NFR-001 | integration | all assertions pass |\n"
            "| TEST-002 | TASK-002 | unit | orphan passes |",
        )
        bad = bad.replace(
            "| EVD-001 | test report | artifacts/test.xml |",
            "| EVD-001 | test report | artifacts/test.xml |\n"
            "| EVD-002 | orphan report | artifacts/orphan.xml |",
        )
        codes = self._codes({"001-publish-item": bad})
        self.assertIn("uncovered-task", codes)
        self.assertIn("uncovered-test", codes)
        self.assertIn("uncovered-evidence", codes)

    def test_repo_scoped_evt_and_fit_need_no_local_definition(self) -> None:
        good = VALID_SPEC.replace("p95 under 200ms | TEST-001", "p95 under 200ms | FIT-001")
        good = good.replace("TEST-001 / EVD-001 |", "FIT-001 / EVD-001 |")
        good = good.replace(
            "| REQ-001 / AC-001 / NFR-001 | MOD-001 / CON-001 | TASK-001 | TEST-001 | EVD-001 |",
            "| REQ-001 / AC-001 / NFR-001 | EVT-001 | TASK-001 | FIT-001 | EVD-001 |",
        )
        good = good.replace(
            "| TEST-001 | REQ-001 / AC-001 / NFR-001 | integration | all assertions pass |\n",
            "",
        )
        temporary, project = self._project({"001-publish-item": good})
        self.addCleanup(temporary.cleanup)
        result = validate_specs.validate_specs(project)
        self.assertTrue(result.ok, result.to_dict())

    def _overlapping_tasks(self, isolation: bool = False) -> str:
        header = "| ID | Entrega | Agente/dono | Entrada | Saida | Read-set | Write-set | Dependencias | Criterio de conclusao |"
        separator = "|---|---|---|---|---|---|---|---|---|"
        first = "| TASK-001 | Implement publish | backend | REQ-001 | endpoint | src/app.py | src/publish.py | none | TEST-001 / EVD-001 |"
        second = "| TASK-002 | Update client | frontend | CON-001 | client | src/publish.py | front/client.ts | none | TEST-002 / EVD-002 |"
        if isolation:
            header = header.replace("| Dependencias |", "| Dependencias | Execucao/isolamento |")
            separator = separator.replace("|---|---|", "|---|---|---|", 1)
            first = first.replace("| none | TEST", "| none | WORKTREE: backend | TEST")
            second = second.replace("| none | TEST", "| none | WORKTREE: frontend | TEST")
        spec = VALID_SPEC.replace(
            "| ID | Entrega | Agente/dono | Entrada | Saida | Read-set | Write-set | Dependencias | Criterio de conclusao |\n"
            "|---|---|---|---|---|---|---|---|---|\n"
            "| TASK-001 | Implement publish | backend | REQ-001 | endpoint | src/app.py | src/publish.py | none | TEST-001 / EVD-001 |",
            f"{header}\n{separator}\n{first}\n{second}",
        )
        spec = spec.replace(
            "| REQ-001 / AC-001 / NFR-001 | MOD-001 / CON-001 | TASK-001 | TEST-001 | EVD-001 |",
            "| REQ-001 / AC-001 / NFR-001 | MOD-001 / CON-001 | TASK-001 / TASK-002 | TEST-001 / TEST-002 | EVD-001 / EVD-002 |",
        )
        spec = spec.replace(
            "| TEST-001 | REQ-001 / AC-001 / NFR-001 | integration | all assertions pass |",
            "| TEST-001 | REQ-001 / AC-001 / NFR-001 | integration | all assertions pass |\n"
            "| TEST-002 | REQ-001 / CON-001 | contract | client accepts contract |",
        )
        return spec.replace(
            "| EVD-001 | test report | artifacts/test.xml |",
            "| EVD-001 | test report | artifacts/test.xml |\n"
            "| EVD-002 | contract report | artifacts/contract.xml |",
        )

    def test_literal_read_write_collision_is_rejected(self) -> None:
        self.assertIn(
            "concurrent-file-set-conflict",
            self._codes({"001-publish-item": self._overlapping_tasks()}),
        )

    def test_declared_worktrees_allow_literal_overlap(self) -> None:
        temporary, project = self._project(
            {"001-publish-item": self._overlapping_tasks(isolation=True)}
        )
        self.addCleanup(temporary.cleanup)
        result = validate_specs.validate_specs(project)
        self.assertTrue(result.ok, result.to_dict())

    def test_same_worktree_does_not_bypass_collision(self) -> None:
        bad = self._overlapping_tasks(isolation=True).replace(
            "WORKTREE: frontend", "WORKTREE: backend"
        )
        self.assertIn(
            "concurrent-file-set-conflict",
            self._codes({"001-publish-item": bad}),
        )

    def test_one_sided_worktree_does_not_bypass_collision(self) -> None:
        bad = self._overlapping_tasks(isolation=True).replace(
            "WORKTREE: frontend", "PARALELO"
        )
        self.assertIn(
            "concurrent-file-set-conflict",
            self._codes({"001-publish-item": bad}),
        )

    def test_acyclic_dependency_serializes_overlap(self) -> None:
        good = self._overlapping_tasks().replace(
            "| none | TEST-002 / EVD-002 |",
            "| TASK-001 | TEST-002 / EVD-002 |",
        )
        temporary, project = self._project({"001-publish-item": good})
        self.addCleanup(temporary.cleanup)
        result = validate_specs.validate_specs(project)
        self.assertTrue(result.ok, result.to_dict())

    def test_self_dependency_cycle_is_rejected(self) -> None:
        bad = VALID_SPEC.replace(
            "| none | TEST-001 / EVD-001 |",
            "| TASK-001 | TEST-001 / EVD-001 |",
        )
        self.assertIn(
            "task-dependency-cycle",
            self._codes({"001-publish-item": bad}),
        )

    def test_dependency_cycle_never_suppresses_collision(self) -> None:
        bad = self._overlapping_tasks()
        bad = bad.replace(
            "| none | TEST-001 / EVD-001 |",
            "| TASK-002 | TEST-001 / EVD-001 |",
        ).replace(
            "| none | TEST-002 / EVD-002 |",
            "| TASK-001 | TEST-002 / EVD-002 |",
        )
        codes = self._codes({"001-publish-item": bad})
        self.assertIn("task-dependency-cycle", codes)
        self.assertIn("concurrent-file-set-conflict", codes)

    def test_dependency_cycle_longer_than_two_tasks_is_rejected(self) -> None:
        bad = self._overlapping_tasks()
        second = (
            "| TASK-002 | Update client | frontend | CON-001 | client | "
            "src/publish.py | front/client.ts | none | TEST-002 / EVD-002 |"
        )
        third = (
            "| TASK-003 | Verify delivery | qa | REQ-001 | report | "
            "tests/input.json | artifacts/report.json | TASK-002 | TEST-003 / EVD-003 |"
        )
        bad = bad.replace(second, second.replace("| none |", "| TASK-001 |") + "\n" + third)
        bad = bad.replace(
            "| TASK-001 | Implement publish | backend | REQ-001 | endpoint | "
            "src/app.py | src/publish.py | none | TEST-001 / EVD-001 |",
            "| TASK-001 | Implement publish | backend | REQ-001 | endpoint | "
            "src/app.py | src/publish.py | TASK-003 | TEST-001 / EVD-001 |",
        )
        bad = bad.replace(
            "TASK-001 / TASK-002 | TEST-001 / TEST-002 | EVD-001 / EVD-002 |",
            "TASK-001 / TASK-002 / TASK-003 | TEST-001 / TEST-002 / TEST-003 | "
            "EVD-001 / EVD-002 / EVD-003 |",
        )
        bad = bad.replace(
            "| TEST-002 | REQ-001 / CON-001 | contract | client accepts contract |",
            "| TEST-002 | REQ-001 / CON-001 | contract | client accepts contract |\n"
            "| TEST-003 | TASK-003 | smoke | report is retained |",
        ).replace(
            "| EVD-002 | contract report | artifacts/contract.xml |",
            "| EVD-002 | contract report | artifacts/contract.xml |\n"
            "| EVD-003 | smoke report | artifacts/report.json |",
        )
        self.assertIn(
            "task-dependency-cycle",
            self._codes({"001-publish-item": bad}),
        )

    def test_html_commented_and_indented_artifacts_are_nonsemantic(self) -> None:
        for hidden in (
            f"<!--\n{VALID_SPEC}\n-->",
            "\n".join(f"    {line}" for line in VALID_SPEC.splitlines()),
        ):
            with self.subTest(prefix=hidden[:8]):
                codes = self._codes({"001-publish-item": hidden})
                self.assertIn("fenced-artifact", codes)
                self.assertIn("missing-section", codes)

    def test_raw_html_wrappers_cannot_hide_semantic_spec(self) -> None:
        wrappers = (
            ("<div hidden>", "</div>"),
            ("<script type=\"text/plain\">", "</script>"),
            ("<style>", "</style>"),
            ("<template>", "</template>"),
            ("<details>", "</details>"),
            ("<custom-spec hidden>", "</custom-spec>"),
            ("<x:div hidden>", "</x:div>"),
            ("<div hidden/>", "</div>"),
            ("<x:div hidden/>", "</x:div>"),
            ("<div\n hidden>", "</div>"),
            ("<div hidden\n>", "</div>"),
            ("<script\n type=\"text/plain\">", "</script>"),
        )
        for opening, closing in wrappers:
            with self.subTest(opening=opening):
                hidden = f"{opening}\n{VALID_SPEC}\n{closing}"
                codes = self._codes({"001-publish-item": hidden})
                self.assertIn("fenced-artifact", codes)
                self.assertIn("missing-section", codes)

    def test_namespaced_html_closing_mismatch_never_reveals_content(self) -> None:
        hidden = f"<x:div hidden>\n{VALID_SPEC}\n</div>"
        codes = self._codes({"001-publish-item": hidden})
        self.assertIn("fenced-artifact", codes)
        self.assertIn("missing-section", codes)

    def test_raw_html_masking_preserves_visible_markdown(self) -> None:
        self.assertEqual(
            validate_specs._mask_fenced("<https://example.com>"),
            "<https://example.com>",
        )
        inline = VALID_SPEC.replace(
            "editor publishes; reader views",
            "editor <span>publishes</span>; reader views",
        )
        visible_after_block = (
            "<div hidden>\n# fake hidden spec\n</div>\n" + inline
        )
        visible_after_void = "<br/>\n" + inline
        for spec in (inline, visible_after_block, visible_after_void):
            with self.subTest(prefix=spec[:20]):
                temporary, project = self._project({"001-publish-item": spec})
                self.addCleanup(temporary.cleanup)
                result = validate_specs.validate_specs(project)
                self.assertTrue(result.ok, result.to_dict())


if __name__ == "__main__":
    unittest.main()
