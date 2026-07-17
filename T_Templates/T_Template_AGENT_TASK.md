# AGENT TASK - [TASK_ID]

**Objetivo:**
**Fora de escopo:**
**Depende de:**
**Grupo paralelo:**
**Agente/papel:**
**Criterio de conclusao:**
**Versao das fontes (branch + commit + hash do diff/working tree):**
**Timeout:**
**Retry de:** N/A | AGT-NNN
**Modo:** READ | WRITE
**Read-set:**
**Write-set exclusivo:**
**Isolation:** SNAPSHOT:<fingerprint> | WORKTREE:<id> | N/A - motivo
**Contexto minimo e decisoes aceitas:**
**Artefatos/evidencias primarias:**
**Evidencia esperada/formato:** claims namespaced + arquivo:linha/comando + exit codes
**Comandos esperados ou permitidos:**
**Riscos e limites de permissao:**
**Formato de saida:** `T_Templates/T_Template_AGENT_RESULT.md`
**Destino do handoff:**

O envelope deve repetir exatamente dependencias, grupo, agente, fingerprint,
modo, read-set, write-set, isolation, timeout e retry declarados para a task no plano. Mudanca exige
replanejamento pelo integrador antes da execucao.
