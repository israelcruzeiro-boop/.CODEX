from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_architecture  # noqa: E402
import validate_specs  # noqa: E402


VALID_SPEC = """# Change 001
## 0. Identificacao
**Spec:** SPEC-001
## 1. State
**Contexto lido:** src/app.py
**Atores e papeis:** editor publishes; reader views
**Precondicoes:** editor is authenticated and item is valid
**Fatos observados:** current behavior
## 2. Escopo
**Objetivo mensuravel:** publish safely
### Inclui
- flow
### NAO inclui
- unrelated work
## 3. Requisitos Funcionais E Criterios De Aceite
| ID | Requisito | Estado |
|---|---|---|
| REQ-001 | Publish item | ATIVO |

| ID | Requisito relacionado | Criterio de aceite | Estado |
|---|---|---|---|
| AC-001 | REQ-001 | Response is 201 and persisted | ATIVO |

| ID/relacao | Regra | Erros/estados | Permissoes |
|---|---|---|---|
| REQ-001 / AC-001 | persist once | 409 on duplicate | editor only |
## 4. Requisitos Nao Funcionais
| ID | Eixo | Limite | Gate |
|---|---|---|---|
| NFR-001 | performance | p95 under 200ms | TEST-001 |
## 5. Definition Of Ready - DoR
- [x] Requirements are testable.
- [x] Rollback is planned.
**Veredito DoR:** APROVADO
## 6. Design E Contratos
| ID | Modulo/owner | Responsabilidade | API publica | Dados/invariantes |
|---|---|---|---|---|
| MOD-001 | Publishing team | Own item publication | CON-001 | items / exactly once |

| ID | Tipo | Owner/produtor | Consumidores | Schema/semantica | Compatibilidade |
|---|---|---|---|---|---|
| CON-001 | API | MOD-001 | web client | POST Item -> Item | additive v1 |
## 7. Doubt
No blocking gaps.
## 8. Backlog Executavel
| ID | Entrega | Agente/dono | Entrada | Saida | Read-set | Write-set | Dependencias | Criterio de conclusao |
|---|---|---|---|---|---|---|---|---|
| TASK-001 | Implement publish | backend | REQ-001 | endpoint | src/app.py | src/publish.py | none | TEST-001 / EVD-001 |
## 9. Rastreabilidade Obrigatoria
| Requisito | Modulo/contrato | Task | Teste/gate | Evidencia |
|---|---|---|---|---|
| REQ-001 / AC-001 / NFR-001 | MOD-001 / CON-001 | TASK-001 | TEST-001 | EVD-001 |
## 10. Rollout E Rollback
Deploy canary; rollback application artifact on failed smoke.
## 11. Demonstrate - Testes, Harness E Evidencias
| ID | Requisito | Tipo | Resultado esperado |
|---|---|---|---|
| TEST-001 | REQ-001 / AC-001 / NFR-001 | integration | all assertions pass |

| ID | Prova | Fonte |
|---|---|---|
| EVD-001 | test report | artifacts/test.xml |
## 12. Definition Of Done - DoD
- [x] Traceability is complete.
- [x] Evidence is retained.
**Veredito DoD:** APROVADO
## 13. Document
**LOG:** sim
**Proximo passo obrigatorio:** handoff
"""


VALID_ASIS = """# ARCHITECTURE - API
**Fonte:** analise direta do codigo
**Data da analise:** 2026-07-16
**Horizonte:** AS-IS
## 1. Stack Real
Python 3.13 from pyproject.toml.
## 2. Visao Geral E Fluxo De Referencia
src/api.py -> src/domain.py.
## 3. Modelo De Dominio
Item is persisted by Publishing.
## 4. Estrutura Real De Pastas
src/api.py and src/domain.py.
## 5. Contratos De API
POST /items uses CON-001.
## 6. Autenticacao E Autorizacao
Bearer auth with editor role.
## 7. Regras De Camada
| Regra | Gate que a cobra |
|---|---|
| API imports only public domain API | python scripts/check_imports.py |
## 8. Gerenciamento De Estado (frontends)
N/A - backend repository.
## 9. Requisitos Minimos De Plataforma
Linux amd64.
## 10. Escalabilidade E Cache
Stateless API and cursor pagination.
## 11. Gaps E Pontos De Atencao
No material drift.
## 12. Catalogo Modular Observado
| ID | Modulo real | Responsabilidade | API publica | Dados/owner | Invariantes | Dono |
|---|---|---|---|---|---|---|
| MOD-001 | API | HTTP boundary | CON-001 | none | INV-001 | API team |
| MOD-002 | Publishing | publishing rules | CON-002 | items/write | INV-002 | Domain team |
### Dependencias Observadas
| Origem | Destino | Tipo | Evidencia | Estado |
|---|---|---|---|---|
| MOD-001 | MOD-002 | sync | src/api.py:publish_item | PERMITIDA |
## 13. Transacoes, Consistencia E Eventos Observados
Local transaction in MOD-002.
## 14. Patterns Observados
PAT-001 presence observed at src/repository.py:Repository.
"""


VALID_TARGET = """# TARGET_ARCHITECTURE - API
**Horizonte:** TO-BE
**Data:** 2026-07-16
**Spec(s) de origem e estado:** SPEC-001 / REQ-001 / NFR-001 | READY_FOR_ARCH
**ADR(s) aplicaveis:** ADR-001
**AS-IS de referencia:** ARCHITECTURE.md analisado em 2026-07-16
**Dono:** Architecture team
**Estado:** APROVADO
## 1. Objetivo E Drivers
Separate API and publishing ownership.
## 2. Delta AS-IS -> TO-BE
| ID | AS-IS observado | TO-BE desejado | Motivo | Spec/ADR aplicavel | Task de transicao |
|---|---|---|---|---|---|
| DELTA-001 | mixed write | owned write | integrity | REQ-001 / ADR-001 | TASK-001 |
## 3. Catalogo Alvo De Modulos
| ID | Modulo | Responsabilidade | API publica | Dados/owner | Invariantes | Dono |
|---|---|---|---|---|---|---|
| MOD-001 | API | HTTP boundary | CON-001 | none | INV-001 | API team |
| MOD-002 | Publishing | item writes | CON-002 | items/write | INV-002 | Domain team |
## 4. APIs Publicas, Contratos E Eventos
| ID | Tipo/protocolo | Operacao/rota/topico | Produtor/owner | Consumidor | Entrada/saida/schema | Erros/semantica | AuthN/AuthZ | Versao/depreciacao | Idempotencia/deduplicacao | Compatibilidade | Gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CON-001 | HTTP | POST /items | MOD-001 | EXTERNO: web client | ItemRequest/Item | 400 invalid; 409 duplicate | Bearer token / editor role | v1; deprecate with 90 days | idempotency-key deduplicated 24h | additive | contract test |
| CON-002 | in-process command | publish(command) | MOD-002 | MOD-001 | PublishCommand/Item | domain errors are typed | service identity / publishing policy | v1; deprecate with adapter | command id deduplicated | additive | schema test |
| EVT-001 | evento/schema | items.published.v1 | MOD-002 | EXTERNO: audit service | ItemPublished v1 | at-least-once semantic | N/A - broker ACL enforced outside event schema | v1; additive evolution | event id deduplicated | backward compatible | schema test |
## 5. Ownership De Dados E Invariantes
| Dado/entidade | Modulo owner | Escritores permitidos | Leitores | Invariantes | Gate |
|---|---|---|---|---|---|
| items | MOD-002 | MOD-002 | MOD-001 | INV-002 | ownership test |
## 6. Dependencias
### Permitidas
| Origem | Destino | Tipo | Motivo | Gate |
|---|---|---|---|---|
| MOD-001 | MOD-002 | sync | publish item | import check |
### Proibidas
| Origem | Destino | Regra | Motivo | Gate bloqueante |
|---|---|---|---|---|
| MOD-001 | MOD-002 internals | internal import | preserve owner | import check |
## 7. Grafo E Ciclos
```mermaid
flowchart LR
  M1["MOD-001"] --> M2["MOD-002"]
```
- Ciclos permitidos: nenhum
- Gate de deteccao: python scripts/check_cycles.py
## 8. Transacoes, Consistencia E Eventos
| Fluxo | Limite transacional | Consistencia | Evento/efeito | Ordenacao | Idempotencia/retry | DLQ/replay | Compensacao/reconciliacao |
|---|---|---|---|---|---|---|---|
| publish | MOD-002 local commit | eventual under 5s | EVT-001 | per item ID | idempotency key; retry 3x | DLQ after 3 retries; idempotent replay | reconcile from outbox |
## 9. Patterns
| Pattern | Presenca alvo | Decisao atual | Decisao alvo | Modulos | ADR | Gate |
|---|---|---|---|---|---|---|
| PAT-001 | PRESENTE | APROVADO | APROVADO | MOD-002 | ADR-001 | python scripts/check_repository.py |
## 10. Evolucao, Rollout E Rollback
| Etapa | Mudanca | Compatibilidade | Rollout/smoke | Abort criterion | Rollback/forward-fix |
|---|---|---|---|---|---|
| 1 | add public API | old route remains | canary and smoke | error rate above 1% | rollback deploy artifact |
## 11. Fitness Gates
| Gate | Comando/regra | Frequencia | Evidencia | Resultado bloqueante | Dono |
|---|---|---|---|---|---|
| FIT-001 | python scripts/check_imports.py | PR/CI | EVD-001 | forbidden edge | Architecture team |
## 12. Rastreabilidade
| Requisito | Modulo/contrato | ADR | Task | Teste | Evidencia |
|---|---|---|---|---|---|
| REQ-001 / NFR-001 | MOD-001 / CON-001 | ADR-001 | TASK-001 | TEST-001 | EVD-001 |
## 13. Lacunas E Decisoes Pendentes
No blocking gaps.
"""


VALID_PATTERN = """# PATTERN_MAP - API
**Data da auditoria:** 2026-07-16
**Escopo:** API repository boundary
**AS-IS:** ARCHITECTURE.md
**TO-BE:** TARGET_ARCHITECTURE.md
**Dono:** Architecture team
## Catalogo
| ID | Pattern | Familia | Tags | Presenca | Decisao | Trade-off material | Escopo | Evidencia | ADR | Gate | Dono |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PAT-001 | Repository | DESIGN | BOUNDARY, DOMAIN | OBSERVADO | APROVADO | SIM | MOD-002 | src/repository.py:Repository | ADR-001 | python scripts/check_repository.py | Architecture team |
## Registro Detalhado
### PAT-001 - Repository
**Presenca:** OBSERVADO
**Decisao:** APROVADO
**Familia:** DESIGN
**Tags:** BOUNDARY, DOMAIN
**Trade-off material:** SIM
**Escopo:** MOD-002 writes
**Modulos/contratos:** MOD-002 / CON-002
**Data/decisor:** 2026-07-16 / Architecture team
#### Evidencia
- Codigo/simbolo: src/repository.py:Repository
- Comando/resultado: python tests/test_repository.py passed
#### Problema E Forcas
- Problema: preserve aggregate invariants
- Forcas/tensoes: testability versus abstraction cost
- Restricoes: no cross-module writes
#### Solucao
- Estrutura: public repository port and adapter
- Responsabilidades: domain owns the port
- Exemplo de referencia: src/repository.py:Repository
#### Alternativas
| Alternativa | Beneficios | Custos | Motivo da decisao |
|---|---|---|---|
| direct ORM | less code | leaks persistence | rejected to preserve ownership |
#### Contraindicacoes
- Nao usar quando: read-only projection has no invariant
- Sinais de uso indevido: pass-through repository
#### Trade-offs
- Beneficios aceitos: isolated rules and tests
- Custos/riscos aceitos: one extra adapter
#### ADR E Evolucao
- ADR: ADR-001
- Decisao anterior: SEM_DECISAO
- Plano de migracao/remocao: migrate writes in TASK-001
- Dono/prazo: Domain team / 2026-08-01
#### Gate
| Regra/comando | Frequencia | Evidencia esperada | Falha bloqueia? |
|---|---|---|---|
| python scripts/check_repository.py | PR/CI | EVD-001 | SIM |
## Auditoria De Consistencia
- [x] Presenca `OBSERVADO` nao foi tratada automaticamente como decisao `APROVADO`.
- [x] Decisao `PROPOSTO` com presenca `NAO_OBSERVADO` nao aparece no AS-IS como implementada.
- [x] Todo `DESCARTADO` preserva o motivo e nao aparece como regra vigente.
- [x] Todo `DEPRECIADO` possui migracao, dono e prazo.
- [x] Todo `PROIBIDO` possui gate bloqueante.
- [x] Todo pattern declara `Trade-off material = SIM/NAO`.
- [x] Todo pattern declara uma familia primaria e ao menos uma tag canonica; catalogo e detalhe concordam.
- [x] Toda escolha material aponta ADR; `N/A` so aparece em escolha nao material e possui justificativa concreta.
- [x] Links de MOD-/CON-/REQ-/TASK-/TEST-/EVD- existem.
## Veredito
APROVADO
**Justificativa:** evidence and ADR complete
"""


class SpecValidatorTests(unittest.TestCase):
    def _project(self, spec: str = VALID_SPEC) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temporary = tempfile.TemporaryDirectory()
        project = Path(temporary.name)
        root = project / ".codex" / "specs"
        change = root / "changes" / "001-publish-item"
        change.mkdir(parents=True)
        (change / "spec.md").write_text(spec, encoding="utf-8")
        (root / "EXECUTAR-TODAS.md").write_text("# Queue\n- 001-publish-item\n", encoding="utf-8")
        return temporary, project, root

    def _add_second(self, root: Path, spec: str, name: str = "002-reuse-module") -> None:
        change = root / "changes" / name
        change.mkdir()
        number = name.split("-", 1)[0]
        spec = re.sub(r"\*\*Spec:\*\* SPEC-\d{3}", f"**Spec:** SPEC-{number}", spec)
        (change / "spec.md").write_text(spec, encoding="utf-8")
        index = root / "EXECUTAR-TODAS.md"
        index.write_text(index.read_text(encoding="utf-8") + f"- {name}\n", encoding="utf-8")

    def test_valid_complete_change(self) -> None:
        temporary, project, _ = self._project()
        self.addCleanup(temporary.cleanup)
        self.assertTrue(validate_specs.validate_specs(project).ok)

    def test_fenced_whole_artifact_is_rejected(self) -> None:
        temporary, project, _ = self._project(f"```md\n{VALID_SPEC}\n```")
        self.addCleanup(temporary.cleanup)
        codes = {issue.code for issue in validate_specs.validate_specs(project).errors}
        self.assertIn("fenced-artifact", codes)
        self.assertIn("missing-section", codes)

    def test_repo_scoped_ids_may_repeat_only_with_same_meaning(self) -> None:
        temporary, project, root = self._project()
        self.addCleanup(temporary.cleanup)
        self._add_second(root, VALID_SPEC)
        self.assertTrue(validate_specs.validate_specs(project).ok)
        conflict = VALID_SPEC.replace("Own item publication", "Own user authentication")
        (root / "changes" / "002-reuse-module" / "spec.md").write_text(conflict, encoding="utf-8")
        codes = {issue.code for issue in validate_specs.validate_specs(project).errors}
        self.assertIn("repo-id-conflict", codes)

    def test_spec_scoped_ids_can_repeat_across_changes(self) -> None:
        temporary, project, root = self._project()
        self.addCleanup(temporary.cleanup)
        self._add_second(root, VALID_SPEC)
        self.assertNotIn(
            "duplicate-definition",
            {issue.code for issue in validate_specs.validate_specs(project).errors},
        )

    def test_missing_actor_precondition_rule_and_file_sets_are_rejected(self) -> None:
        bad = VALID_SPEC.replace("**Atores e papeis:** editor publishes; reader views", "**Atores e papeis:**")
        bad = bad.replace("**Precondicoes:** editor is authenticated and item is valid", "**Precondicoes:**")
        bad = bad.replace("| REQ-001 / AC-001 | persist once | 409 on duplicate | editor only |", "| REQ-001 / AC-001 | | | |")
        bad = bad.replace("| src/app.py | src/publish.py |", "| | |")
        temporary, project, _ = self._project(bad)
        self.addCleanup(temporary.cleanup)
        codes = {issue.code for issue in validate_specs.validate_specs(project).errors}
        self.assertIn("missing-behavior-context", codes)
        self.assertIn("incomplete-rule-matrix", codes)
        self.assertIn("missing-task-file-set", codes)

    def test_broken_traceability_is_rejected(self) -> None:
        bad = VALID_SPEC.replace(
            "| REQ-001 / AC-001 / NFR-001 | MOD-001 / CON-001 | TASK-001 | TEST-001 | EVD-001 |",
            "| REQ-001 / AC-001 / NFR-001 | MOD-001 / CON-001 | TASK-001 | TEST-001 | |",
        )
        temporary, project, _ = self._project(bad)
        self.addCleanup(temporary.cleanup)
        self.assertIn(
            "broken-traceability-row",
            {issue.code for issue in validate_specs.validate_specs(project).errors},
        )

    def test_json_cli_output(self) -> None:
        temporary, project, _ = self._project()
        self.addCleanup(temporary.cleanup)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = validate_specs.main([str(project), "--json"])
        self.assertEqual(status, 0)
        self.assertTrue(json.loads(output.getvalue())["ok"])


class ArchitectureValidatorTests(unittest.TestCase):
    def _project(
        self,
        asis: str = VALID_ASIS,
        target: str = VALID_TARGET,
        pattern: str = VALID_PATTERN,
    ) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "ARCHITECTURE.md").write_text(asis, encoding="utf-8")
        (root / "TARGET_ARCHITECTURE.md").write_text(target, encoding="utf-8")
        (root / "PATTERN_MAP.md").write_text(pattern, encoding="utf-8")
        (root / "src").mkdir()
        (root / "src" / "api.py").write_text("def publish_item(): pass\n", encoding="utf-8")
        (root / "src" / "repository.py").write_text("class Repository: pass\n", encoding="utf-8")
        return temporary, root

    def test_valid_architecture_package(self) -> None:
        temporary, root = self._project()
        self.addCleanup(temporary.cleanup)
        result = validate_architecture.validate_architecture(root)
        self.assertTrue(result.ok, result.to_dict())

    def test_fenced_whole_architecture_is_rejected(self) -> None:
        temporary, root = self._project(asis=f"```md\n{VALID_ASIS}\n```")
        self.addCleanup(temporary.cleanup)
        codes = {issue.code for issue in validate_architecture.validate_architecture(root / "ARCHITECTURE.md").errors}
        self.assertIn("fenced-artifact", codes)
        self.assertIn("missing-section", codes)

    def test_greenfield_target_without_asis_is_valid(self) -> None:
        greenfield = VALID_TARGET.replace(
            "ARCHITECTURE.md analisado em 2026-07-16",
            "N/A - greenfield sem codigo observavel",
        )
        temporary, root = self._project(target=greenfield)
        self.addCleanup(temporary.cleanup)
        (root / "ARCHITECTURE.md").unlink()
        result = validate_architecture.validate_architecture(root)
        self.assertTrue(result.ok, result.to_dict())
        self.assertIn("missing-asis", {issue.code for issue in result.warnings})

    def test_adr_can_be_justified_na(self) -> None:
        no_adr = VALID_TARGET.replace("**ADR(s) aplicaveis:** ADR-001", "**ADR(s) aplicaveis:** N/A - no material trade-off")
        no_adr = no_adr.replace("REQ-001 / ADR-001", "REQ-001 / N/A - additive contract only")
        no_adr = no_adr.replace("| ADR-001 | TASK-001", "| N/A - no trade-off | TASK-001")
        temporary, root = self._project(target=no_adr)
        self.addCleanup(temporary.cleanup)
        result = validate_architecture.validate_architecture(root / "TARGET_ARCHITECTURE.md")
        self.assertTrue(result.ok, result.to_dict())

    def test_unknown_dependency_module_and_empty_gate_are_rejected(self) -> None:
        bad = VALID_TARGET.replace(
            "| MOD-001 | MOD-002 | sync | publish item | import check |",
            "| MOD-001 | MOD-999 | sync | publish item | |",
        )
        temporary, root = self._project(target=bad)
        self.addCleanup(temporary.cleanup)
        codes = {issue.code for issue in validate_architecture.validate_architecture(root / "TARGET_ARCHITECTURE.md").errors}
        self.assertIn("unknown-dependency-module", codes)
        self.assertIn("empty-dependency-gate", codes)

    def test_contract_party_and_semantics_are_enforced(self) -> None:
        bad = VALID_TARGET.replace("EXTERNO: web client", "web client")
        bad = bad.replace("400 invalid; 409 duplicate", "")
        temporary, root = self._project(target=bad)
        self.addCleanup(temporary.cleanup)
        codes = {issue.code for issue in validate_architecture.validate_architecture(root / "TARGET_ARCHITECTURE.md").errors}
        self.assertIn("invalid-contract-party", codes)
        self.assertIn("incomplete-contract", codes)

    def test_contract_interface_and_auth_are_enforced(self) -> None:
        bad = VALID_TARGET.replace(
            "| CON-001 | HTTP | POST /items |",
            "| CON-001 | | |",
        )
        bad = bad.replace(
            "Bearer token / editor role",
            "N/A - endpoint is internal",
        )
        bad = bad.replace(
            "N/A - broker ACL enforced outside event schema",
            "N/A",
        )
        temporary, root = self._project(target=bad)
        self.addCleanup(temporary.cleanup)
        codes = {
            issue.code
            for issue in validate_architecture.validate_architecture(
                root / "TARGET_ARCHITECTURE.md"
            ).errors
        }
        self.assertIn("incomplete-contract-interface", codes)
        self.assertIn("invalid-contract-auth", codes)

    def test_consistency_ordering_dlq_and_compensation_are_enforced(self) -> None:
        bad = VALID_TARGET.replace(
            "| per item ID | idempotency key; retry 3x | DLQ after 3 retries; idempotent replay | reconcile from outbox |",
            "| | idempotency key; retry 3x | N/A | |",
        )
        temporary, root = self._project(target=bad)
        self.addCleanup(temporary.cleanup)
        codes = {
            issue.code
            for issue in validate_architecture.validate_architecture(
                root / "TARGET_ARCHITECTURE.md"
            ).errors
        }
        self.assertIn("incomplete-consistency-plan", codes)
        self.assertIn("unjustified-consistency-na", codes)

    def test_draft_target_keeps_proposal_separate_from_target_decision(self) -> None:
        draft = VALID_TARGET.replace("**Estado:** APROVADO", "**Estado:** RASCUNHO")
        draft = draft.replace(
            "| PAT-001 | PRESENTE | APROVADO | APROVADO |",
            "| PAT-001 | PRESENTE | PROPOSTO | APROVADO |",
        )
        temporary, root = self._project(target=draft)
        self.addCleanup(temporary.cleanup)
        result = validate_architecture.validate_architecture(
            root / "TARGET_ARCHITECTURE.md"
        )
        self.assertTrue(result.ok, result.to_dict())

    def test_accepted_target_rejects_unaccepted_pattern_decision(self) -> None:
        bad = VALID_TARGET.replace(
            "| PAT-001 | PRESENTE | APROVADO | APROVADO |",
            "| PAT-001 | PRESENTE | PROPOSTO | APROVADO |",
        )
        temporary, root = self._project(target=bad)
        self.addCleanup(temporary.cleanup)
        codes = {
            issue.code
            for issue in validate_architecture.validate_architecture(
                root / "TARGET_ARCHITECTURE.md"
            ).errors
        }
        self.assertIn("unaccepted-target-pattern-decision", codes)

    def test_accepted_target_allows_matching_discarded_pattern_decision(self) -> None:
        discarded = VALID_TARGET.replace(
            "| PAT-001 | PRESENTE | APROVADO | APROVADO |",
            "| PAT-001 | AUSENTE | DESCARTADO | DESCARTADO |",
        )
        temporary, root = self._project(target=discarded)
        self.addCleanup(temporary.cleanup)
        result = validate_architecture.validate_architecture(
            root / "TARGET_ARCHITECTURE.md"
        )
        self.assertTrue(result.ok, result.to_dict())

    def test_graph_cycle_policy_and_gate_are_enforced(self) -> None:
        bad = VALID_TARGET.replace("M1[\"MOD-001\"] --> M2[\"MOD-002\"]", "M1[\"module\"]")
        bad = bad.replace("- Ciclos permitidos: nenhum", "- Ciclos permitidos:")
        bad = bad.replace("- Gate de deteccao: python scripts/check_cycles.py", "- Gate de deteccao:")
        temporary, root = self._project(target=bad)
        self.addCleanup(temporary.cleanup)
        codes = {issue.code for issue in validate_architecture.validate_architecture(root / "TARGET_ARCHITECTURE.md").errors}
        self.assertIn("placeholder-graph", codes)
        self.assertIn("missing-cycle-policy", codes)
        self.assertIn("missing-cycle-gate", codes)

    def test_missing_internal_evidence_path_is_rejected(self) -> None:
        bad = VALID_ASIS.replace("src/api.py:publish_item", "src/missing.py:publish_item")
        temporary, root = self._project(asis=bad)
        self.addCleanup(temporary.cleanup)
        codes = {issue.code for issue in validate_architecture.validate_architecture(root / "ARCHITECTURE.md").errors}
        self.assertIn("missing-evidence-path", codes)

    def test_external_label_does_not_hide_missing_internal_evidence(self) -> None:
        bad = VALID_ASIS.replace(
            "src/api.py:publish_item",
            "EXTERNO: vendor docs; src/missing.py:publish_item",
        )
        temporary, root = self._project(asis=bad)
        self.addCleanup(temporary.cleanup)
        codes = {
            issue.code
            for issue in validate_architecture.validate_architecture(
                root / "ARCHITECTURE.md"
            ).errors
        }
        self.assertIn("missing-evidence-path", codes)

    def test_pattern_presence_decision_must_agree(self) -> None:
        bad = VALID_PATTERN.replace("**Presenca:** OBSERVADO", "**Presenca:** PARCIAL")
        temporary, root = self._project(pattern=bad)
        self.addCleanup(temporary.cleanup)
        self.assertIn(
            "pattern-state-mismatch",
            {issue.code for issue in validate_architecture.validate_architecture(root / "PATTERN_MAP.md").errors},
        )

    def test_pattern_family_must_be_canonical(self) -> None:
        bad = VALID_PATTERN.replace("| DESIGN | BOUNDARY, DOMAIN |", "| PLATFORM | BOUNDARY, DOMAIN |")
        temporary, root = self._project(pattern=bad)
        self.addCleanup(temporary.cleanup)
        self.assertIn(
            "invalid-pattern-family",
            {issue.code for issue in validate_architecture.validate_architecture(root / "PATTERN_MAP.md").errors},
        )

    def test_pattern_tags_must_be_unique_and_canonical(self) -> None:
        bad = VALID_PATTERN.replace("BOUNDARY, DOMAIN", "BOUNDARY, MAGIC, BOUNDARY")
        temporary, root = self._project(pattern=bad)
        self.addCleanup(temporary.cleanup)
        self.assertIn(
            "invalid-pattern-tags",
            {issue.code for issue in validate_architecture.validate_architecture(root / "PATTERN_MAP.md").errors},
        )

    def test_pattern_catalog_and_detail_taxonomy_must_match(self) -> None:
        bad = VALID_PATTERN.replace("**Tags:** BOUNDARY, DOMAIN", "**Tags:** BOUNDARY, COMPOSITION")
        temporary, root = self._project(pattern=bad)
        self.addCleanup(temporary.cleanup)
        self.assertIn(
            "pattern-taxonomy-mismatch",
            {issue.code for issue in validate_architecture.validate_architecture(root / "PATTERN_MAP.md").errors},
        )

    def test_greenfield_pattern_map_without_asis_is_valid(self) -> None:
        greenfield = VALID_PATTERN.replace(
            "**AS-IS:** ARCHITECTURE.md",
            "**AS-IS:** N/A - greenfield sem codigo observavel",
        )
        temporary, root = self._project(pattern=greenfield)
        self.addCleanup(temporary.cleanup)
        result = validate_architecture.validate_architecture(root / "PATTERN_MAP.md")
        self.assertTrue(result.ok, result.to_dict())

    def test_deprecated_pattern_requires_observed_presence(self) -> None:
        bad = VALID_PATTERN.replace("OBSERVADO | APROVADO", "NAO_OBSERVADO | DEPRECIADO")
        bad = bad.replace("**Presenca:** OBSERVADO", "**Presenca:** NAO_OBSERVADO")
        bad = bad.replace("**Decisao:** APROVADO", "**Decisao:** DEPRECIADO")
        temporary, root = self._project(pattern=bad)
        self.addCleanup(temporary.cleanup)
        self.assertIn(
            "invalid-deprecation-presence",
            {issue.code for issue in validate_architecture.validate_architecture(root / "PATTERN_MAP.md").errors},
        )

    def test_normative_pattern_requires_adr(self) -> None:
        bad = VALID_PATTERN.replace("ADR-001", "N/A - no decision record")
        temporary, root = self._project(pattern=bad)
        self.addCleanup(temporary.cleanup)
        self.assertIn(
            "missing-pattern-adr",
            {issue.code for issue in validate_architecture.validate_architecture(root / "PATTERN_MAP.md").errors},
        )

    def test_pattern_verdict_banana_is_rejected(self) -> None:
        bad = VALID_PATTERN.replace("\nAPROVADO\n**Justificativa", "\nBANANA\n**Justificativa")
        temporary, root = self._project(pattern=bad)
        self.addCleanup(temporary.cleanup)
        self.assertIn(
            "invalid-final-verdict",
            {issue.code for issue in validate_architecture.validate_architecture(root / "PATTERN_MAP.md").errors},
        )

    def test_architecture_json_cli_output(self) -> None:
        temporary, root = self._project()
        self.addCleanup(temporary.cleanup)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = validate_architecture.main([str(root), "--json"])
        self.assertEqual(status, 0)
        self.assertTrue(json.loads(output.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
