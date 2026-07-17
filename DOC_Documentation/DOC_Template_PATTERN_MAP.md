# PATTERN_MAP - [NOME DO PROJETO/REPO]

> Registro verificavel de patterns observados e normativos. Segue
> `A_Architecture/A_Method_PatternMap.md`.

**Data da auditoria:** YYYY-MM-DD
**Escopo:**
**AS-IS:** `ARCHITECTURE.md` | N/A - greenfield sem codigo observavel
**TO-BE:** `TARGET_ARCHITECTURE.md` | N/A
**Dono:** @A / @DOC / [time]

## Catalogo

Familias: `DESIGN`, `ARCHITECTURE`, `INTEGRATION`, `DATA`, `RESILIENCE`.
Tags canonicas: `BOUNDARY`, `COMPOSITION`, `DOMAIN`, `MODULARITY`,
`MIGRATION`, `REQUEST_REPLY`, `EVENT_DRIVEN`, `MESSAGING`, `TRANSACTION`,
`CONSISTENCY`, `READ_MODEL`, `CACHE`, `CONCURRENCY`, `FAILURE_CONTROL`,
`TRAFFIC_CONTROL`, `RECOVERY`.

| ID | Pattern | Familia | Tags | Presenca | Decisao | Trade-off material | Escopo | Evidencia | ADR | Gate | Dono |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PAT-001 |  | DESIGN/ARCHITECTURE/INTEGRATION/DATA/RESILIENCE | BOUNDARY, DOMAIN | OBSERVADO/PARCIAL/NAO_OBSERVADO | SEM_DECISAO/PROPOSTO/APROVADO/DESCARTADO/DEPRECIADO/PROIBIDO | SIM/NAO |  | arquivo:simbolo ou evidencia da necessidade | ADR- se SIM; ADR-/N/A justificado se NAO |  |  |

## Registro Detalhado

### PAT-001 - [Nome]

**Presenca:** OBSERVADO | PARCIAL | NAO_OBSERVADO
**Decisao:** SEM_DECISAO | PROPOSTO | APROVADO | DESCARTADO | DEPRECIADO | PROIBIDO
**Familia:** DESIGN | ARCHITECTURE | INTEGRATION | DATA | RESILIENCE
**Tags:** BOUNDARY, DOMAIN
**Trade-off material:** SIM | NAO
**Escopo:**
**Modulos/contratos:** MOD- / CON- / EVT-
**Data/decisor:**

#### Evidencia

- Codigo/simbolo:
- Comando/resultado:
- Incidente ou necessidade:

#### Problema E Forcas

- Problema:
- Forcas/tensoes:
- Restricoes:

#### Solucao

- Estrutura:
- Responsabilidades:
- Exemplo de referencia:

#### Alternativas

| Alternativa | Beneficios | Custos | Motivo da decisao |
|---|---|---|---|
|  |  |  |  |

#### Contraindicacoes

- Nao usar quando:
- Sinais de uso indevido:

#### Trade-offs

- Beneficios aceitos:
- Custos/riscos aceitos:

#### ADR E Evolucao

- ADR: ADR- quando `Trade-off material = SIM` | ADR- ou N/A justificado quando `NAO`
- Decisao anterior:
- Plano de migracao/remocao:
- Dono/prazo:

#### Gate

| Regra/comando | Frequencia | Evidencia esperada | Falha bloqueia? |
|---|---|---|---|
|  | PR/CI/release | EVD- | SIM/NAO |

## Auditoria De Consistencia

- [ ] Presenca `OBSERVADO` nao foi tratada automaticamente como decisao `APROVADO`.
- [ ] Decisao `PROPOSTO` com presenca `NAO_OBSERVADO` nao aparece no AS-IS como implementada.
- [ ] Todo `DESCARTADO` preserva o motivo e nao aparece como regra vigente.
- [ ] Todo `DEPRECIADO` possui migracao, dono e prazo.
- [ ] Todo `PROIBIDO` possui gate bloqueante.
- [ ] Todo pattern declara `Trade-off material = SIM/NAO`.
- [ ] Todo pattern declara uma familia primaria e ao menos uma tag canonica;
      catalogo e detalhe concordam.
- [ ] Toda escolha material aponta ADR; `N/A` so aparece em escolha nao
      material e possui justificativa concreta.
- [ ] Links de MOD-/CON-/REQ-/TASK-/TEST-/EVD- existem.

## Veredito

APROVADO | APROVADO_COM_RESSALVAS | QUESTIONAR | REPROVADO

**Justificativa:**
**Lacuna nao bloqueante:** N/A para APROVADO | [lacuna concreta]
**Acao/dono/prazo:** N/A para APROVADO | [acao] / [dono] / YYYY-MM-DD
**Proximo passo obrigatorio:**
