from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_cli_audit as validator


def audit(
    *,
    command_rows: str,
    trace_rows: str,
    verdict: str = "APROVADO",
    context_requirements: str = "REQ-001",
    gaps: str = "- N/A - nenhuma lacuna",
    failures: str = "- N/A - nenhuma falha",
    reservation: str = "",
    cycle_close: str | None = None,
) -> str:
    closing = cycle_close if cycle_close is not None else """
**Status geral atualizado em `STATUS.md`:** SIM
**Status por ambiente atualizado em `STATUS.md`:** SIM
**Ambientes sem validacao e motivo:** N/A - todos os ambientes aplicaveis foram validados
**Migrations do ciclo:** N/A - nenhuma migration neste ciclo
**Diretorio canonico de migrations confirmado:** N/A - nenhuma migration neste ciclo
**Lacunas de replicacao do banco:** N/A - nenhuma lacuna de replicacao
"""
    return f"""# CLI Audit Harness

## Contexto

**Tarefa:** validar runtime P1
**Spec/tasks:** SPEC-101 / TASK-001
**Requisitos/NFRs:** {context_requirements}
**Modulos/contratos:** MOD-001 / CON-001
**Branch/commit:** codex/p1 / {'a' * 40}
**Diretorio raiz:** .
**Ambientes afetados:** infra
**Arquivos alterados:** RUNTIME_Bridge/scripts/gate.py
**Data:** 2026-07-16

## Comandos Executados

| # | Evidencia | Comando | CWD | Objetivo | Exit code | Resultado | Observacao/prova substituta |
|---:|---|---|---|---|---:|---|---|
{command_rows}

## Rastreabilidade Demonstrada

| Requisito | Modulo/contrato | Task | Teste/gate | Evidencia | Resultado |
|---|---|---|---|---|---|
{trace_rows}

## Lacunas

{gaps}

## Fechamento De Ciclo

{closing}

## Falhas

{failures}

## Veredito

**Veredito:** {verdict}
**Justificativa:** veredito sustentado pelos comandos e pela rastreabilidade
**Proximo passo:** revisar e integrar o resultado
{reservation}
"""


class CLIAuditValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "CLI_AUDIT.md"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, body: str) -> validator.ValidationResult:
        self.path.write_text(body, encoding="utf-8")
        return validator.validate_cli_audit(self.path)

    def test_valid_approved_audit(self) -> None:
        checked = self.write(audit(
            command_rows="| 1 | EVD-001 | python -m unittest | . | executar testes | 0 | PASS | 10 testes aprovados |",
            trace_rows="| REQ-001 | MOD-001 / CON-001 | TASK-001 | TEST-001 | EVD-001 | PROVADO |",
        ))
        self.assertTrue(checked.ok, [issue.to_dict() for issue in checked.errors])

    def test_pass_requires_zero_exit(self) -> None:
        checked = self.write(audit(
            command_rows="| 1 | EVD-001 | python -m unittest | . | executar testes | 2 | PASS | testes falharam |",
            trace_rows="| REQ-001 | MOD-001 | TASK-001 | TEST-001 | EVD-001 | PROVADO |",
        ))
        self.assertIn("pass-with-nonzero-exit", {issue.code for issue in checked.errors})

    def test_failure_cannot_be_masked_by_approval(self) -> None:
        checked = self.write(audit(
            command_rows="| 1 | EVD-001 | python -m unittest | . | executar testes | 1 | FAIL | uma regressao |",
            trace_rows="| REQ-001 | MOD-001 | TASK-001 | TEST-001 | EVD-001 | FALHOU |",
            failures="- regressao reproduzida em test_gate",
        ))
        codes = {issue.code for issue in checked.errors}
        self.assertIn("failure-masked-by-verdict", codes)
        self.assertIn("approval-masks-gap", codes)

    def test_reservation_requires_structured_followup(self) -> None:
        checked = self.write(audit(
            command_rows="| 1 | EVD-001 | playwright test | front | validar navegador | N/A | SKIP_JUSTIFICADO | ambiente sem browser; unitario EVD-002 substitui |\n| 2 | EVD-002 | npm test | front | validar unidade | 0 | PASS | testes aprovados |",
            trace_rows="| REQ-001 | MOD-002 | TASK-001 | TEST-001 | EVD-002 | PROVADO |",
            verdict="APROVADO_COM_RESSALVAS",
            gaps="- navegador nao validado neste ambiente",
        ))
        self.assertIn("incomplete-reservation", {issue.code for issue in checked.errors})

    def test_complete_reservation_is_valid(self) -> None:
        reservation = """
**Ressalva:** navegador nao disponivel neste runner
**Acao da ressalva:** executar Playwright em staging
**Responsavel pela ressalva:** equipe QA
**Prazo/criterio da ressalva:** antes do merge da PR
"""
        checked = self.write(audit(
            command_rows="| 1 | EVD-001 | playwright test | front | validar navegador | N/A | SKIP_JUSTIFICADO | ambiente sem browser; unitario EVD-002 substitui |\n| 2 | EVD-002 | npm test | front | validar unidade | 0 | PASS | testes aprovados |",
            trace_rows="| REQ-001 | MOD-002 | TASK-001 | TEST-001 | EVD-002 | PROVADO |",
            verdict="APROVADO_COM_RESSALVAS",
            gaps="- navegador nao validado neste ambiente",
            reservation=reservation,
        ))
        self.assertTrue(checked.ok, [issue.to_dict() for issue in checked.errors])

    def test_traceability_cannot_reference_unknown_evidence(self) -> None:
        checked = self.write(audit(
            command_rows="| 1 | EVD-001 | python -m unittest | . | executar testes | 0 | PASS | testes aprovados |",
            trace_rows="| REQ-001 | MOD-001 | TASK-001 | TEST-001 | EVD-999 | PROVADO |",
        ))
        codes = {issue.code for issue in checked.errors}
        self.assertIn("unknown-traceability-evidence", codes)
        self.assertIn("unmapped-command-evidence", codes)

    def test_traceability_requires_complete_chain_and_context_coverage(self) -> None:
        checked = self.write(audit(
            command_rows="| 1 | EVD-001 | python -m unittest | . | executar testes | 0 | PASS | testes aprovados |",
            trace_rows="| REQ-001 |  |  |  | EVD-001 | PROVADO |",
            context_requirements="REQ-001 / NFR-001",
        ))
        codes = {issue.code for issue in checked.errors}
        self.assertIn("invalid-traceability-module", codes)
        self.assertIn("invalid-traceability-task", codes)
        self.assertIn("invalid-traceability-test", codes)
        self.assertIn("unmapped-declared-requirement", codes)

    def test_traceability_covers_all_declared_req_and_nfr_ids(self) -> None:
        checked = self.write(audit(
            command_rows="| 1 | EVD-001 | python -m unittest | . | executar testes | 0 | PASS | testes aprovados |",
            trace_rows="| REQ-001 / NFR-001 | MOD-001 / CON-001 | TASK-001 | TEST-001 | EVD-001 | PROVADO |",
            context_requirements="REQ-001 / NFR-001",
        ))
        self.assertTrue(checked.ok, [issue.to_dict() for issue in checked.errors])

    def test_escaped_pipe_is_valid_inside_command_cell(self) -> None:
        checked = self.write(audit(
            command_rows=r"| 1 | EVD-001 | python -m unittest \| Tee-Object results.txt | . | executar e registrar testes | 0 | PASS | testes aprovados |",
            trace_rows="| REQ-001 | MOD-001 / CON-001 | TASK-001 | TEST-001 | EVD-001 | PROVADO |",
        ))
        self.assertTrue(checked.ok, [issue.to_dict() for issue in checked.errors])

    def test_reprovado_accepts_structured_blocking_gap(self) -> None:
        structured_gap = """| ID | Lacuna | Bloqueante? | Acao | Responsavel | Prazo/criterio |
|---|---|---|---|---|---|
| GAP-001 | ambiente critico indisponivel | SIM | restaurar runner e repetir gate | equipe de plataforma | antes do merge |"""
        checked = self.write(audit(
            command_rows="| 1 | EVD-001 | integration test | . | validar ambiente critico | N/A | LACUNA | runner indisponivel |",
            trace_rows="| REQ-001 | MOD-001 / CON-001 | TASK-001 | TEST-001 | EVD-001 | LACUNA |",
            verdict="REPROVADO",
            gaps=structured_gap,
        ))
        self.assertTrue(checked.ok, [issue.to_dict() for issue in checked.errors])

    def test_cycle_close_is_required(self) -> None:
        checked = self.write(audit(
            command_rows="| 1 | EVD-001 | python -m unittest | . | executar testes | 0 | PASS | testes aprovados |",
            trace_rows="| REQ-001 | MOD-001 / CON-001 | TASK-001 | TEST-001 | EVD-001 | PROVADO |",
            cycle_close="",
        ))
        self.assertIn("incomplete-cycle-close", {issue.code for issue in checked.errors})

    def test_fenced_or_commented_contract_does_not_count(self) -> None:
        body = "<!--\n" + audit(
            command_rows="| 1 | EVD-001 | python -m unittest | . | executar testes | 0 | PASS | ok |",
            trace_rows="| REQ-001 | MOD-001 | TASK-001 | TEST-001 | EVD-001 | PROVADO |",
        ) + "\n-->"
        checked = self.write(body)
        self.assertIn("missing-command-table", {issue.code for issue in checked.errors})

    def test_duplicate_semantic_verdict_is_rejected(self) -> None:
        body = audit(
            command_rows="| 1 | EVD-001 | python -m unittest | . | executar testes | 0 | PASS | ok |",
            trace_rows="| REQ-001 | MOD-001 | TASK-001 | TEST-001 | EVD-001 | PROVADO |",
        ) + "\n**Veredito:** APROVADO\n"
        checked = self.write(body)
        self.assertIn("verdict-cardinality", {issue.code for issue in checked.errors})

    def test_json_shape_is_machine_readable(self) -> None:
        checked = self.write(audit(
            command_rows="| 1 | EVD-001 | python -m unittest | . | executar testes | 0 | PASS | testes aprovados |",
            trace_rows="| REQ-001 | MOD-001 | TASK-001 | TEST-001 | EVD-001 | PROVADO |",
        ))
        payload = json.loads(json.dumps(checked.to_dict()))
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["commands"], 1)

    def test_json_cli_contract_and_exit_code(self) -> None:
        self.path.write_text(audit(
            command_rows="| 1 | EVD-001 | python -m unittest | . | executar testes | 0 | PASS | testes aprovados |",
            trace_rows="| REQ-001 | MOD-001 | TASK-001 | TEST-001 | EVD-001 | PROVADO |",
        ), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(Path(validator.__file__)), str(self.path), "--json"],
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
