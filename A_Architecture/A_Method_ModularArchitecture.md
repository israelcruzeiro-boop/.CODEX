# A_Method_ModularArchitecture - Arquitetura Modular Canonica

Metodo canonico para descrever, avaliar e evoluir modulos sem confundir o que
existe com o que se pretende construir.

## Artefatos E Fontes De Verdade

| Artefato | Horizonte | Fonte | Pode conter aspiracao? |
|---|---|---|---|
| `ARCHITECTURE.md` | AS-IS | Codigo, manifests, schema e runtime observados | Nao |
| `TARGET_ARCHITECTURE.md` | TO-BE | Spec e ADRs aplicaveis | Sim, sempre rotulada e com estado |
| `PATTERN_MAP.md` | Presenca + decisao dos patterns | Evidencia + decisao | Apenas como `PROPOSTO` |
| `DECISIONS.md` ou `docs/adr/*.md` | Decisoes | Trade-off aceito | Sim, como ADR |

Regra: `TARGET_ARCHITECTURE.md` nunca corrige silenciosamente o AS-IS.
Divergencia entre os dois vira gap, task de transicao e, quando houver
trade-off relevante, ADR. Mudanca TO-BE nao entra em implementacao sem spec
pronta para o handoff e ADR aceito quando altera fronteira, ownership,
persistencia, consistencia, API publica ou outro trade-off material. ADR `N/A`
exige justificativa explicita.

## Unidade De Modularidade

Modulo e uma fronteira de responsabilidade com API publica, ownership e
invariantes. Pasta, pacote, service ou microservico nao vira modulo apenas por
existir. Um modulo valido declara:

- ID estavel (`MOD-001`) e nome canonico.
- Problema que possui e responsabilidades que nao possui.
- Dono tecnico e, quando aplicavel, dono de negocio.
- API publica: contratos de entrada, saida, erros e eventos.
- Dados que possui; leitura/escrita permitida por outros modulos.
- Invariantes que protege e autoridade que as valida.
- Dependencias permitidas e proibidas.
- Modelo de consistencia, limites transacionais e efeitos externos.
- Gates que detectam violacao da fronteira.

## Catalogo Obrigatorio De Modulos

Todo desenho modular mantem uma tabela equivalente:

| ID | Modulo | Responsabilidade | API publica | Dados/owner | Invariantes | Dono | Estado |
|---|---|---|---|---|---|---|---|
| MOD-001 | ... | ... | CON-001 | ... | INV-001 | ... | OBSERVADO/ALVO |

IDs de contratos (`CON-*`), invariantes (`INV-*`) e eventos (`EVT-*`) devem
ser estaveis e rastreaveis ate specs, tasks, testes e evidencias.

## API Publica E Encapsulamento

1. Consumidores importam apenas a API publica declarada do modulo.
2. Tipos, tabelas e helpers internos nao sao contrato por conveniencia.
3. Acesso direto ao dado de outro modulo e proibido, salvo excecao temporal
   documentada em ADR com prazo de remocao.
4. Contrato publico declara compatibilidade, versionamento e politica de
   deprecacao.
5. Regra de negocio e invariantes permanecem no modulo que possui o problema,
   nao no cliente ou no orquestrador.

## Ownership De Dados E Invariantes

- Cada entidade/tabela/colecao tem um unico modulo owner de escrita.
- Leitura compartilhada usa API, view, replica ou evento conforme o caso.
- Constraint critica deve existir na autoridade adequada, inclusive no banco
  quando a integridade persistente depender dela.
- Fluxo multi-tenant declara chave de tenant, autorizacao e isolamento.
- Toda escrita critica mapeia quais invariantes valida e quais efeitos produz.

## Dependencias Permitidas E Proibidas

Mantenha duas matrizes explicitas:

| Origem | Destino | Tipo | Motivo | Gate |
|---|---|---|---|---|
| MOD-001 | MOD-002 | PERMITIDA | ... | lint/teste |

| Origem | Destino | Regra proibida | Motivo | Gate |
|---|---|---|---|---|
| MOD-002 | MOD-001 internals | Import interno | Preserva ownership | lint |

Dependencia sem declaracao e `QUESTIONAR`; dependencia proibida comprovada e
`REPROVADO` ate correcao ou ADR de excecao.

## Grafo E Ciclos

1. Gerar um grafo direcionado dos modulos e suas dependencias.
2. Detectar ciclos em build/CI quando a stack permitir.
3. Ciclo novo bloqueia o gate. Ciclo legado entra no AS-IS como gap com dono,
   risco e plano de quebra.
4. Nao mascarar ciclo usando interfaces vazias ou event bus sem necessidade.
5. O TO-BE mostra o grafo alvo e as etapas que mantem o sistema operavel
   durante a transicao.

## Transacoes, Consistencia E Eventos

Para cada fluxo que cruza modulos, declarar:

- Limite da transacao local e modulo que faz commit.
- Operacoes atomicas e invariantes protegidas.
- Consistencia forte ou eventual, com janela tolerada.
- Evento (`EVT-*`), produtor, consumidores, schema e versionamento.
- Idempotencia, deduplicacao, ordenacao, retry e dead-letter.
- Outbox/inbox, saga ou compensacao quando aplicavel; nunca por moda.
- Reconciliacao e observabilidade de falhas parciais.

Transacao distribuida, dual write ou efeito externo sem estrategia explicita
recebe `QUESTIONAR`.

## Evolucao Segura

Toda transicao AS-IS -> TO-BE informa:

1. Compatibilidade entre versoes e consumidores.
2. Sequencia expand/migrate/contract para contratos e dados.
3. Feature flag ou corte controlado quando necessario.
4. Backfill, replay ou reconciliacao idempotente.
5. Rollout, smoke, observabilidade e criterio de abortar.
6. Rollback tecnico; quando rollback de dados for inseguro, forward-fix e
   restauracao claramente separados.
7. Remocao de adapters, flags e caminhos de compatibilidade.

## Fitness Gates Minimos

| Gate | O que prova | Resultado bloqueante |
|---|---|---|
| Catalogo completo | Todo modulo tem owner, API, dados e invariantes | Campo critico ausente |
| Imports/dependencias | Apenas arestas permitidas existem | Aresta proibida |
| Ciclos | Grafo nao introduz ciclo novo | Ciclo novo |
| Contratos | API/eventos sao validados e compativeis | Breaking change sem plano |
| Dados | Escrita e constraints respeitam ownership | Cross-write nao autorizado |
| Consistencia | Fluxos multi-modulo tem idempotencia/compensacao | Dual write sem estrategia |
| Evolucao | Rollout e rollback/forward-fix sao executaveis | Sem caminho seguro |
| Drift | AS-IS corresponde ao codigo | Drift material nao registrado |

Cada gate deve apontar comando, teste, regra de lint ou checklist de review.
Gate sem executor, frequencia e evidencia e apenas intencao.

## Veredito

- `APROVADO`: catalogo, grafo, contratos, ownership, consistencia, evolucao e
  fitness gates estao completos e sustentados por evidencia.
- `APROVADO_COM_RESSALVAS`: lacunas nao bloqueantes tem dono e prazo.
- `QUESTIONAR`: falta evidencia ou decisao capaz de mudar a fronteira.
- `REPROVADO`: ha dependencia proibida, ciclo novo, cross-write, quebra de
  contrato ou evolucao insegura comprovada.
