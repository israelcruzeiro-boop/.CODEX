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

import validate_multi_agent as validator


FINGERPRINT = "branch=codex/p1 commit=" + "a" * 40 + " diff=" + "b" * 64


def plan(*, rows: str, ledger: str, operational: str = "COMPLETE", verdict: str = "APROVADO") -> str:
    return f"""# MULTI-AGENT PLAN - P1

## Controle

**Objetivo:** validar o gate P1 com evidencia reproduzivel
**Agente raiz/integrador:** root
**Risco:** MEDIO
**Limite de threads observado:** 4
**Profundidade permitida:** 1
**Versao das fontes (branch + commit + hash do diff/working tree):** {FINGERPRINT}
**Politica de timeout/retry:** timeout por task; no maximo 1 retry
**Challenge pass:** N/A - nenhum conflito material identificado
**Status operacional da DAG:** {operational}
**Veredito global:** {verdict}
**Prova pos-fan-in:** python -m unittest, exit 0, EVD-900
**Ressalvas finais:** N/A - nenhuma ressalva

## DAG

| Task ID | Objetivo | Depende de | Grupo paralelo | Agente | Modo | Read-set | Write-set | Isolation | Timeout | Retry de | Evidencia/saida | Join/aceite | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
{rows}

## Evidence Ledger

| Claim ID | Claim | Fonte primaria | Agente | Status | Conflito | Decisao do integrador |
|---|---|---|---|---|---|---|
{ledger}
"""


def task(task_id: str, mode: str, reads: str, writes: str, isolation: str, retry: str = "N/A - tentativa inicial", agent: str = "auditor") -> str:
    return f"""# AGENT TASK - {task_id}

**Objetivo:** executar {task_id} com escopo limitado
**Fora de escopo:** deploy e producao
**Depende de:** nenhuma
**Grupo paralelo:** G1
**Agente/papel:** {agent}
**Criterio de conclusao:** resultado e evidencia entregues
**Versao das fontes (branch + commit + hash do diff/working tree):** {FINGERPRINT}
**Timeout:** 10 minutos
**Retry de:** {retry}
**Modo:** {mode}
**Read-set:** {reads}
**Write-set exclusivo:** {writes}
**Isolation:** {isolation}
**Evidencia esperada/formato:** claims com arquivo:linha e comandos
**Destino do handoff:** root integrador
"""


def result(task_id: str, mode: str, reads: str, writes: str, isolation: str, claim: str, *, status: str = "COMPLETE", end: str = FINGERPRINT) -> str:
    return f"""# AGENT RESULT - {task_id}

**Agente/papel:** auditor
**Status:** {status}
**Modo executado:** {mode}
**Retry de:** N/A - tentativa inicial
**Escopo executado:** validacao limitada ao envelope
**Read-set efetivamente usado:** {reads}
**Write-set alterado:** {writes}
**Isolation usada:** {isolation}
**Fingerprint lido no inicio:** {FINGERPRINT}
**Fingerprint confirmado no fim:** {end}

## Fatos Observados

| Claim ID | Fato | Evidencia primaria (arquivo:linha/comando) |
|---|---|---|
| {claim} | contrato validado | tests/example.py:10 |

## Conflitos, Riscos E Lacunas

- Conflitos com outra claim/contrato: N/A - nenhum conflito
- Riscos: N/A - nenhum risco residual
- Lacunas: N/A - nenhuma lacuna
**Precisa de challenge pass:** NAO

## Handoff

**Join condition atendida:** SIM
**Proxima tarefa desbloqueada:** integracao final
**Recomendacao ao integrador:** executar gate final
"""


class MultiAgentValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.tasks = self.root / "tasks"
        self.results = self.root / "results"
        self.tasks.mkdir()
        self.results.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_valid(self) -> Path:
        rows = "\n".join(
            (
                "| AGT-001 | auditar runtime | nenhuma | G1 | auditor | READ | src/** | N/A - tarefa somente leitura | SNAPSHOT:s1 | 10 minutos | N/A - tentativa inicial | claims e comandos | envelope completo | COMPLETE |",
                "| AGT-002 | editar docs | nenhuma | G1 | escritor | WRITE | docs/** | docs/p1.md | WORKTREE:w2 | 10 minutos | N/A - tentativa inicial | diff e teste | arquivo criado | COMPLETE |",
            )
        )
        ledger = "\n".join(
            (
                "| CLM-AGT-001-001 | contrato validado | tests/example.py:10 | AGT-001 | CONFIRMADO | N/A - nenhum | aceito pelo integrador |",
                "| CLM-AGT-002-001 | contrato validado | tests/example.py:10 | AGT-002 | CONFIRMADO | N/A - nenhum | aceito pelo integrador |",
            )
        )
        plan_path = self.root / "plan.md"
        plan_path.write_text(plan(rows=rows, ledger=ledger), encoding="utf-8")
        (self.tasks / "AGT-001.md").write_text(task("AGT-001", "READ", "src/**", "N/A - tarefa somente leitura", "SNAPSHOT:s1"), encoding="utf-8")
        (self.tasks / "AGT-002.md").write_text(task("AGT-002", "WRITE", "docs/**", "docs/p1.md", "WORKTREE:w2", agent="escritor"), encoding="utf-8")
        (self.results / "AGT-001.md").write_text(result("AGT-001", "READ", "src/file.py", "N/A - tarefa somente leitura", "SNAPSHOT:s1", "CLM-AGT-001-001"), encoding="utf-8")
        result_two = result("AGT-002", "WRITE", "docs/base.md", "docs/p1.md", "WORKTREE:w2", "CLM-AGT-002-001", end=FINGERPRINT + " changed=docs/p1.md").replace("**Agente/papel:** auditor", "**Agente/papel:** escritor")
        (self.results / "AGT-002.md").write_text(result_two, encoding="utf-8")
        return plan_path

    def test_complete_package_is_valid(self) -> None:
        result_obj = validator.validate_multi_agent(self.write_valid(), tasks_dir=self.tasks, results_dir=self.results, phase="complete")
        self.assertTrue(result_obj.ok, [issue.to_dict() for issue in result_obj.errors])

    def test_cycle_and_orphan_retry_are_rejected(self) -> None:
        rows = "\n".join(
            (
                "| AGT-001 | first | AGT-002 | G1 | a | READ | a/** | N/A - leitura | SNAPSHOT:s1 | 5 min | N/A - inicial | facts | join | PENDING |",
                "| AGT-002-R2 | retry | AGT-001 | G1 | b | READ | b/** | N/A - leitura | SNAPSHOT:s2 | 5 min | AGT-002 | facts | join | PENDING |",
            )
        )
        path = self.root / "plan.md"
        path.write_text(plan(rows=rows, ledger="| CLM-AGT-001-001 | x | x.py:1 | AGT-001 | NAO_AVALIADO | N/A - none | pending |", operational="INCOMPLETE", verdict="QUESTIONAR"), encoding="utf-8")
        checked = validator.validate_multi_agent(path)
        codes = {issue.code for issue in checked.errors}
        self.assertIn("invalid-retry", codes)
        self.assertIn("retry-limit", codes)

    def test_directory_glob_and_case_collision_is_rejected(self) -> None:
        rows = "\n".join(
            (
                "| AGT-001 | first | nenhuma | G1 | a | WRITE | src/** | SRC/Domain/*.PY | N/A - shared tree | 5 min | N/A - inicial | diff | join | PENDING |",
                "| AGT-002 | second | nenhuma | G1 | b | READ | src/domain/user.py | N/A - leitura | N/A - mutable | 5 min | N/A - inicial | facts | join | PENDING |",
            )
        )
        path = self.root / "plan.md"
        path.write_text(plan(rows=rows, ledger="| CLM-AGT-001-001 | x | x.py:1 | AGT-001 | NAO_AVALIADO | N/A - none | pending |", operational="INCOMPLETE", verdict="QUESTIONAR"), encoding="utf-8")
        checked = validator.validate_multi_agent(path)
        self.assertIn("concurrent-file-set-conflict", {issue.code for issue in checked.errors})

    def test_distinct_worktrees_allow_overlap(self) -> None:
        rows = "\n".join(
            (
                "| AGT-001 | first | nenhuma | G1 | a | WRITE | src/** | src/** | WORKTREE:w1 | 5 min | N/A - inicial | diff | join | PENDING |",
                "| AGT-002 | second | nenhuma | G1 | b | WRITE | src/** | src/** | WORKTREE:w2 | 5 min | N/A - inicial | diff | join | PENDING |",
            )
        )
        path = self.root / "plan.md"
        path.write_text(plan(rows=rows, ledger="| CLM-AGT-001-001 | x | x.py:1 | AGT-001 | NAO_AVALIADO | N/A - none | pending |", operational="INCOMPLETE", verdict="QUESTIONAR"), encoding="utf-8")
        checked = validator.validate_multi_agent(path)
        self.assertNotIn("concurrent-file-set-conflict", {issue.code for issue in checked.errors})

    def test_same_or_one_sided_worktree_does_not_isolate(self) -> None:
        rows = "\n".join(
            (
                "| AGT-001 | first | nenhuma | G1 | a | WRITE | src/** | src/** | WORKTREE:shared | 5 min | N/A - inicial | diff | join | PENDING |",
                "| AGT-002 | second | nenhuma | G1 | b | WRITE | src/** | src/** | WORKTREE:shared | 5 min | N/A - inicial | diff | join | PENDING |",
            )
        )
        path = self.root / "plan.md"
        path.write_text(plan(rows=rows, ledger="| CLM-AGT-001-001 | x | x.py:1 | AGT-001 | NAO_AVALIADO | N/A - none | pending |", operational="INCOMPLETE", verdict="QUESTIONAR"), encoding="utf-8")
        checked = validator.validate_multi_agent(path)
        self.assertIn("concurrent-file-set-conflict", {issue.code for issue in checked.errors})

    def test_empty_requested_task_directory_is_not_silently_accepted(self) -> None:
        path = self.write_valid()
        for envelope in self.tasks.glob("*.md"):
            envelope.unlink()
        checked = validator.validate_multi_agent(path, tasks_dir=self.tasks)
        self.assertEqual(sum(issue.code == "missing-task-envelope" for issue in checked.errors), 2)

    def test_fan_in_rejects_empty_or_missing_results(self) -> None:
        path = self.write_valid()
        (self.results / "AGT-002.md").unlink()
        checked = validator.validate_multi_agent(
            path,
            tasks_dir=self.tasks,
            results_dir=self.results,
            phase="fan-in",
        )
        self.assertIn("missing-result-envelope", {issue.code for issue in checked.errors})

        (self.results / "AGT-001.md").unlink()
        empty = validator.validate_multi_agent(
            path,
            tasks_dir=self.tasks,
            results_dir=self.results,
            phase="fan-in",
        )
        self.assertEqual(sum(issue.code == "missing-result-envelope" for issue in empty.errors), 2)

    def test_fenced_plan_cannot_supply_contract(self) -> None:
        path = self.root / "plan.md"
        path.write_text("```md\n" + plan(rows="| AGT-001 | x | nenhuma | G1 | a | READ | x | N/A - read | SNAPSHOT:s | 1 min | N/A - initial | x | x | PENDING |", ledger="| CLM-AGT-001-001 | x | x.py:1 | AGT-001 | NAO_AVALIADO | none | pending |") + "\n```\n", encoding="utf-8")
        checked = validator.validate_multi_agent(path)
        self.assertIn("missing-dag", {issue.code for issue in checked.errors})

    def test_result_cannot_expand_write_set_or_claim_namespace(self) -> None:
        path = self.write_valid()
        bad = result("AGT-002", "WRITE", "docs/base.md", "secrets.txt", "WORKTREE:w2", "CLM-AGT-001-999", end=FINGERPRINT + " changed=x")
        (self.results / "AGT-002.md").write_text(bad, encoding="utf-8")
        checked = validator.validate_multi_agent(path, tasks_dir=self.tasks, results_dir=self.results, phase="complete")
        codes = {issue.code for issue in checked.errors}
        self.assertIn("unauthorized-write-set", codes)
        self.assertIn("invalid-claim-namespace", codes)

    def test_ledger_reconciles_claim_content_and_primary_source(self) -> None:
        path = self.write_valid()
        text = path.read_text(encoding="utf-8").replace(
            "| CLM-AGT-001-001 | contrato validado | tests/example.py:10 |",
            "| CLM-AGT-001-001 | fato divergente | tests/other.py:99 |",
        )
        path.write_text(text, encoding="utf-8")
        checked = validator.validate_multi_agent(
            path,
            tasks_dir=self.tasks,
            results_dir=self.results,
            phase="complete",
        )
        codes = {issue.code for issue in checked.errors}
        self.assertIn("ledger-claim-content-mismatch", codes)
        self.assertIn("ledger-claim-source-mismatch", codes)

    def test_approved_verdict_requires_confirmed_ledger_claims(self) -> None:
        path = self.write_valid()
        text = path.read_text(encoding="utf-8").replace(
            "| AGT-001 | CONFIRMADO |",
            "| AGT-001 | PARCIAL |",
            1,
        )
        path.write_text(text, encoding="utf-8")
        checked = validator.validate_multi_agent(
            path,
            tasks_dir=self.tasks,
            results_dir=self.results,
            phase="complete",
        )
        self.assertIn("approval-masks-claim-gap", {issue.code for issue in checked.errors})

    def test_escaped_pipe_is_valid_inside_plan_table_cell(self) -> None:
        path = self.write_valid()
        text = path.read_text(encoding="utf-8").replace(
            "claims e comandos",
            r"claims \| comandos",
            1,
        )
        path.write_text(text, encoding="utf-8")
        checked = validator.validate_multi_agent(
            path,
            tasks_dir=self.tasks,
            results_dir=self.results,
            phase="complete",
        )
        self.assertTrue(checked.ok, [issue.to_dict() for issue in checked.errors])

    def test_stale_fingerprint_and_unsatisfied_join_are_rejected(self) -> None:
        path = self.write_valid()
        bad = result("AGT-001", "READ", "src/file.py", "N/A - tarefa somente leitura", "SNAPSHOT:s1", "CLM-AGT-001-001")
        bad = bad.replace(FINGERPRINT, "branch=stale commit=" + "c" * 40 + " diff=" + "d" * 64, 1)
        bad = bad.replace("**Join condition atendida:** SIM", "**Join condition atendida:** NAO")
        (self.results / "AGT-001.md").write_text(bad, encoding="utf-8")
        checked = validator.validate_multi_agent(path, tasks_dir=self.tasks, results_dir=self.results, phase="complete")
        codes = {issue.code for issue in checked.errors}
        self.assertIn("stale-start-fingerprint", codes)
        self.assertIn("unsatisfied-result-join", codes)

    def test_unsafe_traversal_in_file_set_is_rejected(self) -> None:
        rows = "| AGT-001 | escape | nenhuma | G1 | a | WRITE | src/** | ../outside.txt | WORKTREE:w1 | 5 min | N/A - inicial | diff | join | PENDING |"
        path = self.root / "plan.md"
        path.write_text(plan(rows=rows, ledger="| CLM-AGT-001-001 | x | x.py:1 | AGT-001 | NAO_AVALIADO | N/A - none | pending |", operational="INCOMPLETE", verdict="QUESTIONAR"), encoding="utf-8")
        checked = validator.validate_multi_agent(path)
        self.assertIn("unsafe-file-set", {issue.code for issue in checked.errors})

    def test_approved_verdict_cannot_mask_failed_task(self) -> None:
        path = self.write_valid()
        text = path.read_text(encoding="utf-8").replace("| COMPLETE |", "| FAILED |", 1)
        path.write_text(text, encoding="utf-8")
        checked = validator.validate_multi_agent(path, tasks_dir=self.tasks, results_dir=self.results, phase="complete")
        self.assertIn("approval-masks-task-failure", {issue.code for issue in checked.errors})

    def test_json_shape_is_machine_readable(self) -> None:
        checked = validator.validate_multi_agent(self.write_valid(), tasks_dir=self.tasks, results_dir=self.results, phase="complete")
        payload = json.loads(json.dumps(checked.to_dict()))
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["tasks"], 2)

    def test_json_cli_contract_and_exit_code(self) -> None:
        plan_path = self.write_valid()
        completed = subprocess.run(
            [
                sys.executable,
                str(Path(validator.__file__)),
                str(plan_path),
                "--tasks-dir",
                str(self.tasks),
                "--results-dir",
                str(self.results),
                "--phase",
                "complete",
                "--json",
            ],
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
