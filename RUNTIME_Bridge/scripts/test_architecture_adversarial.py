from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_architecture  # noqa: E402
from test_governance_validators import (  # noqa: E402
    VALID_ASIS,
    VALID_PATTERN,
    VALID_TARGET,
)


TRACE_ROW = (
    "| REQ-001 / NFR-001 | MOD-001 / CON-001 | ADR-001 | TASK-001 | "
    "TEST-001 | EVD-001 |"
)


def pattern_with_materiality(materiality: str, adr: str) -> str:
    pattern = VALID_PATTERN.replace(
        "| PAT-001 | Repository | DESIGN | BOUNDARY, DOMAIN | OBSERVADO | APROVADO | SIM | MOD-002 | src/repository.py:Repository | ADR-001 | python scripts/check_repository.py | Architecture team |",
        f"| PAT-001 | Repository | DESIGN | BOUNDARY, DOMAIN | OBSERVADO | APROVADO | {materiality} | MOD-002 | src/repository.py:Repository | {adr} | python scripts/check_repository.py | Architecture team |",
    ).replace("**Trade-off material:** SIM", f"**Trade-off material:** {materiality}")
    return pattern.replace("- ADR: ADR-001", f"- ADR: {adr}")


class ArchitectureAdversarialTests(unittest.TestCase):
    def _file(self, name: str, content: str) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "src").mkdir()
        (root / "src" / "repository.py").write_text(
            "class Repository: pass\n", encoding="utf-8"
        )
        path = root / name
        path.write_text(content, encoding="utf-8")
        return path

    def _codes(self, name: str, content: str) -> set[str]:
        result = validate_architecture.validate_architecture(self._file(name, content))
        return {issue.code for issue in result.errors}

    def _package_result(
        self,
        *,
        asis: str = VALID_ASIS,
        target: str = VALID_TARGET,
        pattern: str = VALID_PATTERN,
    ) -> validate_architecture.ValidationResult:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "src").mkdir()
        (root / "src" / "api.py").write_text(
            "def publish_item(): pass\n", encoding="utf-8"
        )
        (root / "src" / "repository.py").write_text(
            "class Repository: pass\n", encoding="utf-8"
        )
        (root / "ARCHITECTURE.md").write_text(asis, encoding="utf-8")
        (root / "TARGET_ARCHITECTURE.md").write_text(target, encoding="utf-8")
        (root / "PATTERN_MAP.md").write_text(pattern, encoding="utf-8")
        return validate_architecture.validate_architecture(root)

    def test_actual_dependency_cycles_and_self_loops_are_rejected(self) -> None:
        cycle = VALID_TARGET.replace(
            "| MOD-001 | MOD-002 | sync | publish item | import check |",
            "| MOD-001 | MOD-002 | sync | publish item | import check |\n"
            "| MOD-002 | MOD-001 | sync | callback | cycle check |",
        ).replace(
            '  M1["MOD-001"] --> M2["MOD-002"]',
            '  M1["MOD-001"] --> M2["MOD-002"]\n'
            '  M2["MOD-002"] --> M1["MOD-001"]',
        )
        self.assertIn(
            "dependency-cycle",
            self._codes("TARGET_ARCHITECTURE.md", cycle),
        )

        self_loop = VALID_TARGET.replace(
            "| MOD-001 | MOD-002 | sync | publish item | import check |",
            "| MOD-001 | MOD-002 | sync | publish item | import check |\n"
            "| MOD-002 | MOD-002 | sync | recursive call | cycle check |",
        ).replace(
            '  M1["MOD-001"] --> M2["MOD-002"]',
            '  M1["MOD-001"] --> M2["MOD-002"]\n'
            '  M2["MOD-002"] --> M2["MOD-002"]',
        )
        self.assertIn(
            "dependency-cycle",
            self._codes("TARGET_ARCHITECTURE.md", self_loop),
        )

    def test_same_dependency_rule_cannot_be_permitted_and_prohibited(self) -> None:
        contradictory = VALID_TARGET.replace(
            "| MOD-001 | MOD-002 internals | internal import | preserve owner | import check |",
            "| MOD-001 | MOD-002 | same edge also prohibited | preserve owner | import check |",
        )
        self.assertIn(
            "contradictory-dependency-policy",
            self._codes("TARGET_ARCHITECTURE.md", contradictory),
        )

    def test_module_public_contract_owner_must_match(self) -> None:
        bad = VALID_TARGET.replace(
            "| CON-001 | HTTP | POST /items | MOD-001 |",
            "| CON-001 | HTTP | POST /items | MOD-002 |",
        )
        self.assertIn(
            "public-contract-owner-mismatch",
            self._codes("TARGET_ARCHITECTURE.md", bad),
        )

    def test_target_pattern_must_exist_in_pattern_map(self) -> None:
        bad = VALID_TARGET.replace("| PAT-001 | PRESENTE |", "| PAT-999 | PRESENTE |")
        result = self._package_result(target=bad)
        self.assertIn(
            "unknown-pattern-map-reference",
            {issue.code for issue in result.errors},
        )

    def test_pattern_materiality_is_explicit_in_catalog_and_detail(self) -> None:
        bad = VALID_PATTERN.replace(
            "| ID | Pattern | Familia | Tags | Presenca | Decisao | Trade-off material | Escopo | Evidencia | ADR | Gate | Dono |",
            "| ID | Pattern | Familia | Tags | Presenca | Decisao | Escopo | Evidencia | ADR | Gate | Dono |",
        ).replace(
            "|---|---|---|---|---|---|---|---|---|---|---|---|",
            "|---|---|---|---|---|---|---|---|---|---|---|",
            1,
        ).replace(
            "| OBSERVADO | APROVADO | SIM | MOD-002 |",
            "| OBSERVADO | APROVADO | MOD-002 |",
        ).replace("**Trade-off material:** SIM\n", "")
        self.assertIn(
            "missing-pattern-materiality",
            self._codes("PATTERN_MAP.md", bad),
        )

    def test_approved_pattern_requires_every_canonical_audit_item(self) -> None:
        bad = VALID_PATTERN.replace(
            "- [x] Links de MOD-/CON-/REQ-/TASK-/TEST-/EVD- existem.\n",
            "",
        )
        self.assertIn(
            "incomplete-audit-checklist",
            self._codes("PATTERN_MAP.md", bad),
        )

    def test_deprecated_pattern_requires_owner_and_iso_deadline(self) -> None:
        bad = VALID_PATTERN.replace(
            "| OBSERVADO | APROVADO | SIM |",
            "| OBSERVADO | DEPRECIADO | SIM |",
        ).replace(
            "**Decisao:** APROVADO",
            "**Decisao:** DEPRECIADO",
        ).replace(
            "- Dono/prazo: Domain team / 2026-08-01",
            "- Dono/prazo: someday",
        )
        self.assertIn(
            "incomplete-deprecation",
            self._codes("PATTERN_MAP.md", bad),
        )

    def test_approved_target_rejects_blocking_gap(self) -> None:
        variants = (
            "| ID | Lacuna | Impacto | Dono | Prazo | Bloqueia? |\n"
            "|---|---|---|---|---|---|\n"
            "| GAP-001 | ownership unresolved | cross-write | Architecture team | 2026-08-01 | SIM |",
            "GAP-001: ownership unresolved; Bloqueia? SIM",
        )
        for gap in variants:
            with self.subTest(gap=gap):
                bad = VALID_TARGET.replace("No blocking gaps.", gap)
                self.assertIn(
                    "blocking-target-gap",
                    self._codes("TARGET_ARCHITECTURE.md", bad),
                )

    def test_internal_evidence_symbol_must_exist(self) -> None:
        bad = VALID_PATTERN.replace(
            "src/repository.py:Repository",
            "src/repository.py:MissingSymbol",
        )
        self.assertIn(
            "missing-evidence-symbol",
            self._codes("PATTERN_MAP.md", bad),
        )

    def test_target_asis_reference_date_must_match_document(self) -> None:
        stale = VALID_ASIS.replace(
            "**Data da analise:** 2026-07-16",
            "**Data da analise:** 2026-07-15",
        )
        result = self._package_result(asis=stale)
        self.assertIn(
            "asis-reference-date-mismatch",
            {issue.code for issue in result.errors},
        )

    def test_graph_rejects_modules_absent_from_catalog(self) -> None:
        bad = VALID_TARGET.replace(
            'M1["MOD-001"] --> M2["MOD-002"]',
            'M1["MOD-998"] --> M2["MOD-999"]',
        )
        self.assertIn(
            "unknown-graph-module",
            self._codes("TARGET_ARCHITECTURE.md", bad),
        )

    def test_graph_and_dependency_policy_must_match_bidirectionally(self) -> None:
        bad = VALID_TARGET.replace(
            'M1["MOD-001"] --> M2["MOD-002"]',
            'M2["MOD-002"] --> M1["MOD-001"]',
        )
        codes = self._codes("TARGET_ARCHITECTURE.md", bad)
        self.assertIn("undeclared-graph-edge", codes)
        self.assertIn("missing-graph-edge", codes)

    def test_graph_supports_separate_mermaid_alias_definitions(self) -> None:
        target = VALID_TARGET.replace(
            '  M1["MOD-001"] --> M2["MOD-002"]',
            '  M1["MOD-001"]\n  M2["MOD-002"]\n  M1 --> M2',
        )
        result = validate_architecture.validate_architecture(
            self._file("TARGET_ARCHITECTURE.md", target)
        )
        self.assertTrue(result.ok, result.to_dict())

    def test_traceability_rejects_unknown_mod_con_and_evt(self) -> None:
        bad = VALID_TARGET.replace(
            TRACE_ROW,
            "| REQ-001 / NFR-001 | MOD-999 / CON-999 / EVT-999 | ADR-001 | TASK-001 | TEST-001 | EVD-001 |",
        )
        self.assertIn(
            "unknown-traceability-reference",
            self._codes("TARGET_ARCHITECTURE.md", bad),
        )

    def test_traceability_accepts_defined_event(self) -> None:
        target = VALID_TARGET.replace(
            "MOD-001 / CON-001 | ADR-001 | TASK-001",
            "MOD-001 / CON-001 / EVT-001 | ADR-001 | TASK-001",
        )
        result = validate_architecture.validate_architecture(
            self._file("TARGET_ARCHITECTURE.md", target)
        )
        self.assertTrue(result.ok, result.to_dict())

    def test_duplicate_module_definitions_are_rejected_in_asis_and_target(self) -> None:
        asis_row = (
            "| MOD-001 | API | HTTP boundary | CON-001 | none | INV-001 | API team |"
        )
        target_row = (
            "| MOD-001 | API | HTTP boundary | CON-001 | none | INV-001 | API team |"
        )
        variants = (
            ("ARCHITECTURE.md", VALID_ASIS.replace(asis_row, f"{asis_row}\n{asis_row}")),
            (
                "TARGET_ARCHITECTURE.md",
                VALID_TARGET.replace(
                    target_row,
                    f"{target_row}\n| MOD-001 | API duplicate | conflicting owner | CON-001 | other | INV-099 | Other team |",
                ),
            ),
        )
        for name, content in variants:
            with self.subTest(name=name):
                self.assertIn(
                    "duplicate-module-definition",
                    self._codes(name, content),
                )

    def test_duplicate_invariant_definitions_are_rejected(self) -> None:
        target = VALID_TARGET.replace(
            "| MOD-001 | API | HTTP boundary | CON-001 | none | INV-001 | API team |",
            "| MOD-001 | API | HTTP boundary | CON-001 | none | INV-002 | API team |",
        )
        self.assertIn(
            "duplicate-invariant-definition",
            self._codes("TARGET_ARCHITECTURE.md", target),
        )

    def test_duplicate_contract_and_event_definitions_are_rejected(self) -> None:
        contract_row = (
            "| CON-001 | HTTP | POST /items | MOD-001 | EXTERNO: web client | "
            "ItemRequest/Item | 400 invalid; 409 duplicate | Bearer token / editor role | "
            "v1; deprecate with 90 days | idempotency-key deduplicated 24h | additive | contract test |"
        )
        event_row = (
            "| EVT-001 | evento/schema | items.published.v1 | MOD-002 | EXTERNO: audit service | "
            "ItemPublished v1 | at-least-once semantic | N/A - broker ACL enforced outside event schema | "
            "v1; additive evolution | event id deduplicated | backward compatible | schema test |"
        )
        variants = (
            (contract_row, "duplicate-contract-definition"),
            (event_row, "duplicate-event-definition"),
        )
        for row, expected in variants:
            with self.subTest(expected=expected):
                target = VALID_TARGET.replace(row, f"{row}\n{row}")
                self.assertIn(
                    expected,
                    self._codes("TARGET_ARCHITECTURE.md", target),
                )

    def test_duplicate_delta_fitness_and_target_pattern_definitions_are_rejected(self) -> None:
        delta_row = (
            "| DELTA-001 | mixed write | owned write | integrity | REQ-001 / ADR-001 | TASK-001 |"
        )
        fitness_row = (
            "| FIT-001 | python scripts/check_imports.py | PR/CI | EVD-001 | forbidden edge | Architecture team |"
        )
        pattern_row = (
            "| PAT-001 | PRESENTE | APROVADO | APROVADO | MOD-002 | ADR-001 | python scripts/check_repository.py |"
        )
        variants = (
            (delta_row, "duplicate-delta-definition"),
            (fitness_row, "duplicate-fitness-definition"),
            (pattern_row, "duplicate-target-pattern-definition"),
        )
        for row, expected in variants:
            with self.subTest(expected=expected):
                target = VALID_TARGET.replace(row, f"{row}\n{row}")
                self.assertIn(
                    expected,
                    self._codes("TARGET_ARCHITECTURE.md", target),
                )

    def test_duplicate_pattern_catalog_definition_does_not_overwrite_first(self) -> None:
        catalog_row = (
            "| PAT-001 | Repository | DESIGN | BOUNDARY, DOMAIN | OBSERVADO | APROVADO | SIM | MOD-002 | "
            "src/repository.py:Repository | ADR-001 | python scripts/check_repository.py | Architecture team |"
        )
        contradictory = catalog_row.replace("APROVADO", "PROIBIDO").replace(
            "Architecture team", "Other team"
        )
        pattern = VALID_PATTERN.replace(
            catalog_row,
            f"{catalog_row}\n{contradictory}",
        )
        self.assertIn(
            "duplicate-pattern",
            self._codes("PATTERN_MAP.md", pattern),
        )

    def test_duplicate_pattern_detail_blocks_are_always_rejected(self) -> None:
        start = VALID_PATTERN.index("### PAT-001 - Repository")
        end = VALID_PATTERN.index("## Auditoria De Consistencia")
        detail = VALID_PATTERN[start:end]
        variants = (
            detail,
            detail.replace("**Decisao:** APROVADO", "**Decisao:** PROIBIDO"),
        )
        for duplicate in variants:
            with self.subTest(contradictory=duplicate != detail):
                pattern = VALID_PATTERN[:end] + duplicate + VALID_PATTERN[end:]
                self.assertIn(
                    "duplicate-pattern-detail",
                    self._codes("PATTERN_MAP.md", pattern),
                )

    def test_nonmaterial_pattern_accepts_justified_adr_na(self) -> None:
        pattern = pattern_with_materiality(
            "NAO", "N/A - local naming choice without architectural trade-off"
        )
        result = validate_architecture.validate_architecture(
            self._file("PATTERN_MAP.md", pattern)
        )
        self.assertTrue(result.ok, result.to_dict())

    def test_material_pattern_requires_adr(self) -> None:
        pattern = pattern_with_materiality(
            "SIM", "N/A - material decision intentionally left undocumented"
        )
        self.assertIn(
            "missing-pattern-adr",
            self._codes("PATTERN_MAP.md", pattern),
        )

    def test_nonmaterial_pattern_rejects_unjustified_adr_na(self) -> None:
        pattern = pattern_with_materiality("NAO", "N/A")
        self.assertIn(
            "invalid-pattern-adr-na",
            self._codes("PATTERN_MAP.md", pattern),
        )

    def test_questionar_and_reprovado_are_blocking_verdicts(self) -> None:
        for verdict in ("QUESTIONAR", "REPROVADO"):
            with self.subTest(verdict=verdict):
                pattern = VALID_PATTERN.replace(
                    "\nAPROVADO\n**Justificativa",
                    f"\n{verdict}\n**Justificativa",
                )
                path = self._file("PATTERN_MAP.md", pattern)
                result = validate_architecture.validate_architecture(path)
                self.assertFalse(result.ok)
                self.assertIn(
                    "blocking-final-verdict",
                    {issue.code for issue in result.errors},
                )
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(validate_architecture.main([str(path)]), 1)

    def test_reservations_require_gap_action_owner_and_iso_deadline(self) -> None:
        incomplete = VALID_PATTERN.replace(
            "\nAPROVADO\n**Justificativa",
            "\nAPROVADO_COM_RESSALVAS\n**Justificativa",
        )
        self.assertIn(
            "incomplete-reservations",
            self._codes("PATTERN_MAP.md", incomplete),
        )
        invalid_deadline = incomplete.replace(
            "**Justificativa:** evidence and ADR complete",
            "**Justificativa:** evidence complete\n"
            "**Lacuna nao bloqueante:** gate ainda roda apenas no CI\n"
            "**Acao/dono/prazo:** adicionar gate / Architecture team / 2026-99-99",
        )
        self.assertIn(
            "incomplete-reservations",
            self._codes("PATTERN_MAP.md", invalid_deadline),
        )
        complete = incomplete.replace(
            "**Justificativa:** evidence and ADR complete",
            "**Justificativa:** evidence complete\n"
            "**Lacuna nao bloqueante:** gate ainda roda apenas no CI\n"
            "**Acao/dono/prazo:** adicionar gate no pre-commit / Architecture team / 2026-08-01",
        )
        result = validate_architecture.validate_architecture(
            self._file("PATTERN_MAP.md", complete)
        )
        self.assertTrue(result.ok, result.to_dict())

    def test_html_comment_cannot_supply_traceability(self) -> None:
        trace_start = VALID_TARGET.index("## 12. Rastreabilidade")
        gaps_start = VALID_TARGET.index("## 13. Lacunas E Decisoes Pendentes")
        fake_trace = VALID_TARGET[trace_start:gaps_start]
        target = (
            VALID_TARGET[:trace_start]
            + "## 12. Rastreabilidade\n<!--\n"
            + fake_trace
            + "-->\n"
            + VALID_TARGET[gaps_start:]
        )
        self.assertIn(
            "missing-traceability",
            self._codes("TARGET_ARCHITECTURE.md", target),
        )

    def test_hidden_or_indented_whole_artifact_cannot_validate(self) -> None:
        hidden_variants = (
            f"<!--\n{VALID_PATTERN}\n-->\n",
            "\n".join(f"    {line}" for line in VALID_PATTERN.splitlines()),
            "\n".join(f"\t{line}" for line in VALID_PATTERN.splitlines()),
        )
        for content in hidden_variants:
            with self.subTest(prefix=repr(content[:12])):
                codes = self._codes("PATTERN_MAP.md", content)
                self.assertIn("fenced-artifact", codes)
                self.assertIn("missing-section", codes)

    def test_raw_html_wrappers_cannot_hide_whole_artifact(self) -> None:
        wrappers = (
            ("<div hidden>", "</div>"),
            ("<script type=\"text/plain\">", "</script>"),
            ("<style>", "</style>"),
            ("<template>", "</template>"),
            ("<details>", "</details>"),
            ("<section>", "</section>"),
            ("<custom-architecture-block>", "</custom-architecture-block>"),
        )
        for opening, closing in wrappers:
            with self.subTest(opening=opening):
                content = f"{opening}\n{VALID_PATTERN}\n{closing}\n"
                codes = self._codes("PATTERN_MAP.md", content)
                self.assertIn("fenced-artifact", codes)
                self.assertIn("missing-section", codes)

    def test_self_closing_syntax_only_terminates_real_void_elements(self) -> None:
        non_void = (
            "<div hidden/>",
            "<details/>",
            "<script/>",
            "<custom-architecture-block/>",
        )
        for opening in non_void:
            with self.subTest(non_void=opening):
                codes = self._codes(
                    "PATTERN_MAP.md",
                    f"{opening}\n{VALID_PATTERN}\n",
                )
                self.assertIn("fenced-artifact", codes)
                self.assertIn("missing-section", codes)

        for opening in ("<hr/>", "<br />", '<img src="diagram.png"/>'):
            with self.subTest(void=opening):
                result = validate_architecture.validate_architecture(
                    self._file("PATTERN_MAP.md", f"{opening}\n{VALID_PATTERN}")
                )
                self.assertTrue(result.ok, result.to_dict())

    def test_raw_html_cannot_supply_verdict_or_audit_checklist(self) -> None:
        hidden_verdict = VALID_PATTERN.replace(
            "\nAPROVADO\n",
            "\n<div hidden>\nAPROVADO\n</div>\n",
        )
        self.assertIn(
            "invalid-final-verdict",
            self._codes("PATTERN_MAP.md", hidden_verdict),
        )
        hidden_checklist = VALID_PATTERN.replace(
            "- [x] Presenca `OBSERVADO` nao foi tratada automaticamente como decisao `APROVADO`.",
            "<details>\n- [x] Presenca `OBSERVADO` nao foi tratada automaticamente como decisao `APROVADO`.\n</details>",
        )
        self.assertIn(
            "incomplete-audit-checklist",
            self._codes("PATTERN_MAP.md", hidden_checklist),
        )

    def test_approved_pattern_requires_checked_audit_and_concrete_justification(self) -> None:
        bad = VALID_PATTERN.replace(
            "- [x] Presenca `OBSERVADO` nao foi tratada automaticamente como decisao `APROVADO`.",
            "- [ ] Presenca `OBSERVADO` nao foi tratada automaticamente como decisao `APROVADO`.",
        ).replace(
            "**Justificativa:** evidence and ADR complete",
            "**Justificativa:** x",
        )
        codes = self._codes("PATTERN_MAP.md", bad)
        self.assertIn("incomplete-audit-checklist", codes)
        self.assertIn("missing-verdict-justification", codes)

        result = validate_architecture.validate_architecture(
            self._file("PATTERN_MAP.md", VALID_PATTERN)
        )
        self.assertTrue(result.ok, result.to_dict())

    def test_commented_or_indented_verdict_cannot_bypass_parser(self) -> None:
        variants = (
            VALID_PATTERN.replace("\nAPROVADO\n", "\n<!--\nAPROVADO\n-->\n"),
            VALID_PATTERN.replace("\nAPROVADO\n", "\n    APROVADO\n"),
            VALID_PATTERN.replace("\nAPROVADO\n", "\n\tAPROVADO\n"),
        )
        for pattern in variants:
            with self.subTest(marker=repr(pattern[-80:])):
                self.assertIn(
                    "invalid-final-verdict",
                    self._codes("PATTERN_MAP.md", pattern),
                )

    def test_nonsemantic_maskers_preserve_line_count(self) -> None:
        html = "before\n<!--\nfake\n-->\nafter\n"
        raw_html = "before\n<div hidden>\nfake\n</div>\nafter\n"
        indented = "before\n    fake\n\tfake\nafter\n"
        self.assertEqual(
            len(html.splitlines()),
            len(validate_architecture._mask_html_comments(html).splitlines()),
        )
        self.assertEqual(
            len(raw_html.splitlines()),
            len(validate_architecture._mask_raw_html_blocks(raw_html).splitlines()),
        )
        self.assertEqual(
            len(indented.splitlines()),
            len(validate_architecture._mask_indented_code(indented).splitlines()),
        )


if __name__ == "__main__":
    unittest.main()
