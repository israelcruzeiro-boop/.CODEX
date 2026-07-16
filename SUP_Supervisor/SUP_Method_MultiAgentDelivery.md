# Metodo Multi-Agent Delivery

Metodo canonico para decompor, executar e consolidar trabalho com subagentes sem perder contexto, duplicar esforco ou corromper arquivos compartilhados.

## Principios

1. O agente raiz conserva requisitos, decisoes, comunicacao com o usuario, integracao e veredito final.
2. Subagente recebe tarefa pequena, evidencia primaria e contrato de saida; nao recebe a conclusao desejada.
3. Paralelismo e usado para independencia real, nao para transformar toda etapa em cerimonia.
4. Resultado de subagente e evidencia a ser confrontada, nao autoridade automatica.
5. Paralelismo exige isolamento comprovado: nenhum `WRITE` pode tocar o
   `READ` ou `WRITE` de outra task concorrente, salvo snapshot/worktree imutavel
   com fingerprint proprio.

## Gate De Decomposicao

Use subagentes quando houver pelo menos dois workstreams independentes, como:

- exploracao de areas diferentes do codigo;
- revisoes especializadas de seguranca, testes, performance ou arquitetura;
- execucao de suites de teste independentes;
- implementacoes em arquivos e contratos sem sobreposicao;
- analise de muitos artefatos que retornam resumos estruturados.

Nao delegue quando a tarefa e pequena, quando uma decisao bloqueia todas as demais, quando os agentes disputariam os mesmos arquivos ou quando o custo de reconciliacao supera o ganho.

## Plano Em DAG

Antes do primeiro spawn, preencher `T_Templates/T_Template_MULTI_AGENT_PLAN.md`.
Cada no declara:

- `task_id` estavel;
- objetivo e criterio de conclusao;
- dependencias e condicao de join;
- agente/papel;
- modo `READ` ou `WRITE`;
- read-set e write-set;
- contexto minimo;
- evidencia e formato de saida;
- timeout ou criterio de interrupcao quando aplicavel.

Toda DAG declara a versao das fontes (branch, commit e hash do diff/working tree
ou equivalente). Cada resultado registra o fingerprint efetivamente lido no
inicio e no fim. Mudanca dessa identidade antes do fan-in invalida resultados dependentes e exige
replanejamento. Cada task recebe timeout explicito; nao existe duracao global
arbitraria. Retry e limitado pelo plano e ganha sufixo `-R1`, `-R2`, sem apagar
a tentativa anterior.

O plano deve distinguir grupos paralelos de barreiras seriais. Reservar capacidade para o agente raiz e respeitar o limite real exposto pelo runtime. O Codex usa filhos diretos como padrao; profundidade recursiva so pode ser usada quando configurada e justificada. Mais profundidade aumenta custo, latencia e risco de fan-out descontrolado.

## Pacote De Contexto

Usar `T_Templates/T_Template_AGENT_TASK.md`. Incluir apenas:

- objetivo e fora de escopo;
- arquivos, simbolos ou artefatos primarios;
- restricoes e decisoes ja aceitas;
- read-set/write-set;
- comandos permitidos ou esperados;
- contrato de evidencia e saida;
- dependencias e destino do handoff.

Nao incluir raciocinio privado do raiz, conclusao esperada ou ruido de outras tarefas.

## Execucao

1. Spawnar apenas nos prontos da DAG.
2. Nunca iniciar um escritor cujo write-set sobreponha o read-set ou write-set
   de outra task concorrente.
3. Para sobreposicao inevitavel, serializar ou dar ao leitor snapshot/worktree
   imutavel e definir um integrador unico.
4. Acompanhar status sem reenviar a mesma tarefa.
5. Enviar follow-up somente quando surgir evidencia ou restricao nova.
6. Interromper agente que saiu do escopo, produz risco ou trabalha sobre premissa invalidada.
7. Registrar timeout, interrupcao e falha; nao substitui-los silenciosamente por sucesso.

## Fan-In E Evidence Ledger

Na barreira de join:

1. Esperar todos os resultados obrigatorios.
2. Validar cada envelope por `T_Templates/T_Template_AGENT_RESULT.md`.
3. Separar fato observado, inferencia, decisao proposta e lacuna.
4. Deduplicar achados pela mesma evidencia primaria.
5. Confrontar conclusoes contraditorias com arquivos, comandos e contratos.
6. Executar challenge pass independente quando a contradicao muda arquitetura, seguranca, dados, escopo ou release.
7. Registrar no ledger: claim, fonte, agente, status, conflito e decisao do integrador.

Antes da coleta, a claim usa `NAO_AVALIADO`; depois, somente `CONFIRMADO`,
`PARCIAL` ou `REFUTADO`. O challenge pass usa `@C` por padrao, salvo especialista
mais adequado declarado no plano, e recebe timeout e criterio de desempate. O
raiz decide pela evidencia primaria; conflito material ainda sem prova vira
`QUESTIONAR`.

## Integracao De Escrita

- Um unico integrador aplica ou aceita a combinacao final, inclusive quando a
  entrega e uma sintese READ-only sem diff.
- A integracao respeita ownership e preserva mudancas preexistentes do usuario.
- Depois do merge logico, rodar novamente validacoes afetadas; testes isolados dos agentes nao provam a integracao.
- Conflito nao resolvido vira `QUESTIONAR` ou `REPROVADO`, conforme evidencia e risco.

## Falhas E Retomada

- `TIMEOUT`: registrar evidencia parcial e decidir retry unico, replanejamento ou lacuna.
- `BLOCKED`: confirmar se outra tarefa da DAG pode desbloquear; nao pedir ao usuario antes de esgotar leitura segura.
- `CONFLICT`: usar estado proprio, manter as duas claims com fontes e acionar challenge pass.
- `FAILED`: registrar falha terminal e impedir o join, salvo fallback explicito na DAG.
- `PARTIAL`: aceitar somente se a join condition permitir e a lacuna nao for critica.
- `INTERRUPTED`: descartar conclusoes nao sustentadas e registrar o motivo.

## Status E Veredito

O status operacional e:

- `COMPLETE`: todos os joins obrigatorios foram satisfeitos e nenhuma lacuna
  do criterio de conclusao permaneceu;
- `COMPLETE_COM_RESSALVAS`: joins satisfeitos, com lacunas nao criticas aceitas
  explicitamente fora do criterio de conclusao;
- `INCOMPLETE`: join obrigatorio, fonte estavel ou evidencia material faltou.

O veredito global usa somente:

- `APROVADO`: DAG concluida, joins satisfeitos, conflitos resolvidos e integracao validada.
- `APROVADO_COM_RESSALVAS`: lacunas nao criticas registradas e fora do criterio de conclusao.
- `QUESTIONAR`: falta decisao, acesso ou evidencia que muda a entrega.
- `REPROVADO`: conflito material, write collision, falha de gate ou afirmacao sem prova invalida a entrega.

Referencia de runtime atual: https://learn.chatgpt.com/docs/agent-configuration/subagents.md
