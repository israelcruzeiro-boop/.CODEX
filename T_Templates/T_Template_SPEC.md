# Template SPEC Operacional

Use este template antes de implementar qualquer tarefa pelo metodo SDD. IDs
sao estaveis: nao renumerar nem reutilizar ID removido; marque-o `DEPRECIADO`.

## 0. Identificacao

**Spec:** SPEC-NNN
**Titulo:**
**Responsavel:**
**Data:**
**Fase:**
**Risco:** BAIXO | MEDIO | ALTO | CRITICO
**Estado:** DRAFT | READY_FOR_ARCH | READY_FOR_BREAKDOWN | QUESTIONAR
**AS-IS:** `ARCHITECTURE.md` analisado em YYYY-MM-DD | N/A
**TO-BE/ADRs:** `TARGET_ARCHITECTURE.md`; ADR- | N/A justificado

`SPEC-NNN` deve usar o mesmo `NNN` da pasta `changes/NNN-nome`. Referencias a
IDs locais de outra mudanca usam `SPEC-NNN:ID-NNN` e precisam resolver para uma
spec existente; IDs de repositorio (`MOD/CON/EVT/INV/PAT/ADR/FIT`) nao recebem
qualificador de spec.

## 1. State

**Contexto lido:**
**Arquivos/fluxos afetados:**
**Consumidores conhecidos:**
**Atores e papeis:**
**Precondicoes:**
**Fatos observados:**
**Inferencias:**
**Lacunas de contexto:**

## 2. Escopo

**Objetivo mensuravel:**

### Inclui

-

### NAO inclui

-

## 3. Requisitos Funcionais E Criterios De Aceite

| ID | Requisito/comportamento observavel | Prioridade | Estado |
|---|---|---|---|
| REQ-001 |  | MUST/SHOULD/COULD | ATIVO/DEPRECIADO |

| ID | Requisito relacionado | Criterio de aceite mensuravel | Estado |
|---|---|---|---|
| AC-001 | REQ-001 |  | ATIVO/DEPRECIADO |

**Regras de negocio e invariantes:**

| ID/relacao | Regra | Erros/estados | Permissoes |
|---|---|---|---|
| REQ-001 / AC-001 |  |  |  |

## 4. Requisitos Nao Funcionais

Todo NFR deve ter medida, condicao e gate. `N/A` exige motivo.

| ID | Eixo | Requisito/limite | Condicao/carga | Gate/teste | Estado |
|---|---|---|---|---|---|
| NFR-001 | seguranca/performance/disponibilidade/observabilidade/compliance/acessibilidade |  |  | TEST-/FIT- | ATIVO/N/A |

## 5. Definition Of Ready - DoR

- [ ] `REQ-*`, `AC-*` e `NFR-*` possuem definicoes testaveis.
- [ ] Escopo e `NAO inclui` estao explicitos.
- [ ] AS-IS foi lido; delta TO-BE esta em `TARGET_ARCHITECTURE.md` + ADR quando aplicavel.
- [ ] Modulos/contratos/dados/consumidores afetados foram identificados.
- [ ] Riscos, decisoes pendentes e validadores estao registrados.
- [ ] Tasks possuem entrada, saida, dependencia e dono.
- [ ] Tasks paralelas possuem read/write-set sem colisao ou isolamento explicito.
- [ ] Testes, Harness, rollout e rollback/forward-fix estao planejados.
- [ ] Nenhuma lacuna bloqueante permanece sem decisor e proximo passo.

**Veredito DoR:** APROVADO | APROVADO_COM_RESSALVAS | QUESTIONAR | REPROVADO
**Justificativa/lacunas:**
**Lacuna nao bloqueante:** N/A para APROVADO | [lacuna concreta]
**Acao:** N/A para APROVADO | [acao verificavel]
**Dono:** N/A para APROVADO | [pessoa/time responsavel]
**Prazo ISO/criterio verificavel:** N/A para APROVADO | YYYY-MM-DD | TEST-/FIT-/EVD- + condicao de fechamento

`APROVADO` exige todos os itens marcados. `APROVADO_COM_RESSALVAS` exige
lacuna nao bloqueante, acao, dono e prazo ISO valido ou criterio verificavel;
`QUESTIONAR` e `REPROVADO` bloqueiam implementacao.

## 6. Design E Contratos

**Plano minimo:**

`MOD-*` e `CON-*` abaixo usam namespace do repositorio. Reutilize IDs canonicos
ou troque os exemplos pelo proximo ID livre; nunca reinicie `MOD-001`/`CON-001`
com significado diferente em outra spec.

| ID | Modulo/owner | Responsabilidade | API publica | Dados/invariantes |
|---|---|---|---|---|
| MOD-001 |  |  | CON-001 |  |

| ID | Tipo | Owner/produtor | Consumidores | Schema/semantica | Compatibilidade |
|---|---|---|---|---|---|
| CON-001 | API/DTO/evento/job/webhook | MOD-001 |  |  |  |

**Eventos adicionais:** EVT-
**Dados/migrations:**
**Invariantes/transacoes/consistencia:** INV-
**Patterns:** PAT-
**Seguranca/permissoes:**
**Observabilidade:**
**Compatibilidade:**

## 7. Doubt

| ID | Risco/pergunta/hipotese | Impacto | Dono/decisor | Evidencia para fechar | Bloqueia? |
|---|---|---|---|---|---|
| RISK-001 |  |  |  | EVD- | SIM/NAO |

**Validadores obrigatorios:**
**Criterios de reabertura da spec:**

## 8. Backlog Executavel

| ID | Entrega | Agente/dono | Entrada | Saida | Read-set | Write-set | Dependencias | Execucao/isolamento | Criterio de conclusao |
|---|---|---|---|---|---|---|---|---|---|
| TASK-001 |  |  | REQ-/MOD-/CON- |  |  |  | TASK-/ADR- ou nenhuma | SERIAL/PARALELO/SNAPSHOT:hash/WORKTREE:id | TEST-/FIT-/EVD- |

Tasks sem dependencia podem executar concorrentemente. Um write-set nao pode
tocar read-set ou write-set concorrente; serialize por dependencia/`SERIAL` ou
declare snapshot/worktree imutavel com identidade rastreavel.
Dependencias `TASK-*` formam DAG: self-cycle ou ciclo de qualquer tamanho
reprova a spec e nunca conta como serializacao valida.

## 9. Rastreabilidade Obrigatoria

Nenhuma linha pode terminar sem teste e evidencia, salvo `N/A` justificado.
Todos os `REQ/AC/NFR`, `TASK`, `TEST/FIT` e `EVD` definidos devem aparecer na
matriz. `EVT-*` e `FIT-*` canonicos podem ser reutilizados do namespace do
repositorio sem redefinicao local.

| Requisito | Modulo/contrato | Task | Teste/gate | Evidencia | Estado |
|---|---|---|---|---|---|
| REQ-001 / AC-001 / NFR-001 | MOD-001 / CON-001 / EVT- | TASK-001 | TEST-001 / FIT-001 | EVD-001 | PLANEJADO/PROVADO/FALHOU/N/A |

## 10. Rollout E Rollback

**Ambientes e ordem:**
**Migration expand/migrate/contract:**
**Feature flags/adapters:**
**Compatibilidade entre versoes:**
**Smoke e observabilidade:**
**Criterio de abortar:**
**Rollback de aplicacao:**
**Rollback de dados:**
**Forward-fix/restauracao quando rollback for inseguro:**

Ambientes/ordem, smoke/observabilidade, criterio de aborto e rollback de
aplicacao sao obrigatorios. Rollback de dados ou forward-fix deve ser concreto;
quando nao se aplicar, use `N/A - motivo`.

## 11. Demonstrate - Testes, Harness E Evidencias

| ID | Requisito/risco | Tipo | Arquivo/comando | Resultado esperado | Evidencia |
|---|---|---|---|---|---|
| TEST-001 | REQ-001 | unit/integration/contract/e2e/smoke/fitness |  |  | EVD-001 |

| ID | Prova produzida | Fonte/caminho | Retencao/owner |
|---|---|---|---|
| EVD-001 |  |  |  |

**Teste falhando primeiro:**
**Harness CLI planejado:** `T_Templates/T_Template_CLI_AUDIT.md`
**Bug sweep/regressao:**
**Ambientes nao validados e motivo:**

## 12. Definition Of Done - DoD

- [ ] Todos os `REQ-*`, `AC-*` e `NFR-*` ativos estao `PROVADO` ou possuem ressalva aceita.
- [ ] Matriz `REQ/AC/NFR -> MOD/CON/EVT -> TASK -> TEST/FIT -> EVD` nao tem elo quebrado.
- [ ] Contratos e migrations foram validados com consumidores.
- [ ] Harness foi executado e usa veredito canonico.
- [ ] Rollout, smoke, rollback/forward-fix e observabilidade foram demonstrados.
- [ ] Nenhum bug conhecido, falha ou lacuna critica foi mascarado.
- [ ] `ARCHITECTURE.md` AS-IS foi atualizado apenas apos codigo comprovado.
- [ ] ADRs, `TARGET_ARCHITECTURE.md`, `PATTERN_MAP.md`, LOG e STATUS foram atualizados quando aplicavel.

**Veredito DoD:** APROVADO | APROVADO_COM_RESSALVAS | QUESTIONAR | REPROVADO
**Justificativa/lacunas:**
**Lacuna nao bloqueante:** N/A para APROVADO | [lacuna concreta]
**Acao:** N/A para APROVADO | [acao verificavel]
**Dono:** N/A para APROVADO | [pessoa/time responsavel]
**Prazo ISO/criterio verificavel:** N/A para APROVADO | YYYY-MM-DD | TEST-/FIT-/EVD- + condicao de fechamento

`APROVADO` exige todos os itens marcados. `APROVADO_COM_RESSALVAS` exige
lacuna nao bloqueante, acao, dono e prazo ISO valido ou criterio verificavel;
`QUESTIONAR` e `REPROVADO` bloqueiam fechamento.

## 13. Document

**LOG:** sim | nao | N/A
**DECISIONS/ADRs:** sim | nao | N/A
**TARGET_ARCHITECTURE/PATTERN_MAP:** sim | nao | N/A
**LEARNINGS:** sim | nao | N/A
**STATUS geral e por ambiente:** sim | nao | N/A
**Proximo passo obrigatorio:**
