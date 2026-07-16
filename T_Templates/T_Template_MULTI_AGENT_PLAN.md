# MULTI-AGENT PLAN - [ENTREGA]

## Controle

**Objetivo:**
**Agente raiz/integrador:**
**Risco:** BAIXO | MEDIO | ALTO | CRITICO
**Limite de threads observado:**
**Profundidade permitida:**
**Versao das fontes (branch + commit + hash do diff/working tree):**
**Politica de timeout/retry:** timeout por task; no maximo [N] retries como `AGT-NNN-R1`
**Challenge pass:** papel/dono, timeout e criterio de desempate

## DAG

| Task ID | Objetivo | Depende de | Grupo paralelo | Agente | Modo | Read-set | Write-set | Join/aceite | Status |
|---|---|---|---|---|---|---|---|---|---|
| AGT-001 |  | nenhuma | G1 |  | READ/WRITE |  |  |  | PENDING |

**Status de task:** PENDING | RUNNING | COMPLETE | PARTIAL | BLOCKED | TIMEOUT | INTERRUPTED | FAILED | CONFLICT
**Status operacional da DAG:** COMPLETE | COMPLETE_COM_RESSALVAS | INCOMPLETE

## Regras De Integracao

- Arquivos com owner exclusivo:
- Tarefas que exigem worktree:
- Ordem das barreiras:
- Integrador final:
- Validacao obrigatoria depois do fan-in, inclusive em sintese READ-only:
- Regra de invalidacao se branch/SHA/hash mudar:

## Evidence Ledger

| Claim ID | Claim | Fonte primaria | Agente | Status | Conflito | Decisao do integrador |
|---|---|---|---|---|---|---|
| CLM-AGT-001-001 |  |  | AGT-001 | NAO_AVALIADO/CONFIRMADO/PARCIAL/REFUTADO |  |  |

Claim IDs usam `CLM-<TASK_ID>-NNN`; nunca reiniciam como `CLM-001` em envelopes
de agentes diferentes.
