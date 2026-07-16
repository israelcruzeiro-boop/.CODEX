# Template CLI Audit Harness

Use este template para registrar a prova executavel de uma entrega.

## Contexto

**Tarefa:**  
**Spec/tasks:** SPEC- / TASK-
**Requisitos/NFRs:** REQ- / NFR-
**Modulos/contratos:** MOD- / CON- / EVT-
**Branch/commit:**  
**Diretorio raiz:**  
**Ambientes afetados:** back / front / admin / mobile / infra / packages / outro / N/A
**Arquivos alterados:**  
**Data:**  

## Scripts Descobertos

| Fonte | Scripts/comandos relevantes |
|---|---|
| `package.json` |  |
| `Makefile` |  |
| `pyproject.toml` |  |
| CI/docs |  |

## Comandos Executados

| # | Evidencia | Comando | CWD | Objetivo | Exit code | Resultado | Observacao/prova substituta |
|---:|---|---|---|---|---:|---|---|
| 1 | EVD-001 |  |  |  |  | PASS/FAIL/LACUNA/SKIP_JUSTIFICADO | resumo concreto; justificativa obrigatoria em LACUNA/SKIP |

## Saidas Relevantes

```text
Cole apenas trechos essenciais: erro, warning relevante, resumo de testes ou build.
Nao cole secrets.
```

## Testes E Provas

**Teste especifico:**  
**Teste de regressao:**  
**Build/typecheck/lint:**  
**Smoke:**  

## Rastreabilidade Demonstrada

| Requisito | Modulo/contrato | Task | Teste/gate | Evidencia | Resultado |
|---|---|---|---|---|---|
| REQ-/AC-/NFR- | MOD-/CON-/EVT- | TASK- | TEST-/FIT- | EVD- | PROVADO/FALHOU/LACUNA/N/A |

Todo `N/A` exige justificativa. Elo ausente em fluxo critico impede aprovacao.

## Lacunas

- N/A - nenhuma lacuna livre; use a tabela abaixo para lacuna com ownership.

| ID | Lacuna | Bloqueante? | Acao | Responsavel | Prazo/criterio |
|---|---|---|---|---|---|
| GAP-001 |  | SIM/NAO |  |  | data ISO ou criterio verificavel |

`REPROVADO` sem comando `FAIL` exige ao menos uma lacuna estruturada
`Bloqueante? = SIM`, com acao, responsavel e prazo/criterio concretos.

## Fechamento De Ciclo

**Status geral atualizado em `STATUS.md`:** SIM | N/A - motivo verificavel
**Status por ambiente atualizado em `STATUS.md`:** SIM | N/A - motivo verificavel
**Ambientes sem validacao e motivo:** N/A - todos validados | ambientes + motivo
**Migrations do ciclo:** caminhos | N/A - nenhuma migration
**Diretorio canonico de migrations confirmado:** caminho | N/A - nenhuma migration
**Lacunas de replicacao do banco:** N/A - nenhuma | lacuna concreta

## Falhas

-  

Coerencia obrigatoria dos resultados individuais: `PASS` usa exit `0`; `FAIL`
usa exit diferente de zero; `LACUNA`/`SKIP_JUSTIFICADO` usam exit `N/A` e
justificativa concreta. Falha comprovada exige o veredito global `REPROVADO`;
aprovacao nao mascara lacuna e ressalva exige acao, responsavel e
prazo/criterio.

## Veredito

**Veredito:** APROVADO | APROVADO_COM_RESSALVAS | QUESTIONAR | REPROVADO
**Justificativa:**  
**Proximo passo:** N/A - nenhuma acao | acao concreta
**Ressalva:** N/A - sem ressalva | lacuna nao critica concreta
**Acao da ressalva:** N/A - sem ressalva | acao concreta
**Responsavel pela ressalva:** N/A - sem ressalva | owner
**Prazo/criterio da ressalva:** N/A - sem ressalva | data ISO ou criterio verificavel
