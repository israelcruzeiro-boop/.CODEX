# AGENT RESULT - [TASK_ID]

**Agente/papel:**
**Status:** COMPLETE | PARTIAL | BLOCKED | TIMEOUT | INTERRUPTED | FAILED | CONFLICT
**Modo executado:** READ | WRITE
**Retry de:** N/A - tentativa inicial | AGT-NNN
**Escopo executado:**
**Read-set efetivamente usado:**
**Write-set alterado:**
**Isolation usada:** SNAPSHOT:<fingerprint> | WORKTREE:<id> | N/A - motivo
**Fingerprint lido no inicio:** branch + commit + hash do diff/working tree
**Fingerprint confirmado no fim:**

## Fatos Observados

| Claim ID | Fato | Evidencia primaria (arquivo:linha/comando) |
|---|---|---|
| CLM-AGT-001-001 |  |  |

Claim IDs usam `CLM-<TASK_ID>-NNN` e sao globais dentro da DAG.

## Inferencias E Propostas

- Inferencia/proposta:
- Evidencia que sustenta:
- Confianca: ALTA | MEDIA | BAIXA

## Comandos

| CWD | Comando | Exit code | Resultado |
|---|---|---:|---|
|  |  |  |  |

## Conflitos, Riscos E Lacunas

- Conflitos com outra claim/contrato:
- Riscos:
- Lacunas:
- Precisa de challenge pass: SIM | NAO

## Handoff

**Join condition atendida:** SIM | NAO
**Proxima tarefa desbloqueada:**
**Recomendacao ao integrador:**

O read-set e o write-set realizados devem estar contidos nos conjuntos
autorizados. Um resultado `READ` nao altera arquivos. O integrador rejeita
fingerprint inicial diferente do plano, claim fora do namespace da task ou
write-set expandido sem replanejamento.
