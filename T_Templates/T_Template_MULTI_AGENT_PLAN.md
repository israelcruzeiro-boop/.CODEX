# MULTI-AGENT PLAN - [ENTREGA]

## Controle

**Objetivo:**
**Agente raiz/integrador:**
**Risco:** BAIXO | MEDIO | ALTO | CRITICO
**Limite de threads observado:**
**Profundidade permitida:**
**Versao das fontes (branch + commit + hash do diff/working tree):**
**Politica de timeout/retry:** timeout por task; no maximo [N] retries como `AGT-NNN-R1`
**Challenge pass:** papel/dono, timeout e criterio de desempate | N/A - motivo verificavel
**Status operacional da DAG:** COMPLETE | COMPLETE_COM_RESSALVAS | INCOMPLETE
**Veredito global:** APROVADO | APROVADO_COM_RESSALVAS | QUESTIONAR | REPROVADO
**Prova pos-fan-in:** comando/artefato + exit code/status + EVD-ID
**Ressalvas finais:** N/A - nenhuma | lacuna nao critica + acao + dono + prazo/criterio

## DAG

| Task ID | Objetivo | Depende de | Grupo paralelo | Agente | Modo | Read-set | Write-set | Isolation | Timeout | Retry de | Evidencia/saida | Join/aceite | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AGT-001 |  | nenhuma | G1 |  | READ/WRITE |  | N/A - READ ou paths WRITE | SNAPSHOT:id / WORKTREE:id / N/A justificado |  | N/A - tentativa inicial | claims + fontes + comandos |  | PENDING |

**Status de task:** PENDING | RUNNING | COMPLETE | PARTIAL | BLOCKED | TIMEOUT | INTERRUPTED | FAILED | CONFLICT

`Isolation` e parte do contrato, nao comentario livre: `SNAPSHOT:<fingerprint>`
protege somente o leitor; writers concorrentes exigem `WORKTREE:<id>` distintos.
`SERIAL` somente vale quando a dependencia correspondente existe na DAG.

## Regras De Integracao

- Arquivos com owner exclusivo:
- Tarefas que exigem worktree:
- Ordem das barreiras:
- Integrador final:
- Validacao obrigatoria depois do fan-in, inclusive em sintese READ-only:
- Regra de invalidacao se branch/SHA/hash mudar:
- Evidencia da reconciliacao entre write-set planejado e alterado:

## Evidence Ledger

| Claim ID | Claim | Fonte primaria | Agente | Status | Conflito | Decisao do integrador |
|---|---|---|---|---|---|---|
| CLM-AGT-001-001 |  |  | AGT-001 | NAO_AVALIADO/CONFIRMADO/PARCIAL/REFUTADO |  |  |

Claim IDs usam `CLM-<TASK_ID>-NNN`; nunca reiniciam como `CLM-001` em envelopes
de agentes diferentes.

Na fase `complete`, toda claim de resultado aparece exatamente uma vez no
ledger, nenhuma permanece `NAO_AVALIADO`, conflitos possuem decisao e a prova
pos-fan-in sustenta o veredito global.
