# A_Reference_PatternCatalog - Catalogo De Apoio A Decisao

Referencia nao prescritiva para reconhecer, comparar e governar patterns. Este
catalogo nao cria padrao oficial por si so: cada uso real recebe `PAT-NNN`,
evidencia, escopo, decisao e gate conforme `A_Method_PatternMap.md`. A ausencia
de um pattern desta lista nao o proibe; classifique-o pela familia e tags
canonicas e registre as mesmas dimensoes de decisao.

## Como Usar

1. Comece pelo problema, pelas forcas e pelos modos de falha observados.
2. Compare a opcao mais simples e pelo menos uma alternativa real.
3. Use `Bom encaixe` como hipotese, nunca como autorizacao automatica.
4. Trate `Contraindicacoes` e `Combinacoes perigosas` como perguntas de gate.
5. Registre telemetria e uma forma executavel de detectar drift.
6. Nao combine patterns apenas porque aparecem juntos neste catalogo.

Tags canonicas: `BOUNDARY`, `COMPOSITION`, `DOMAIN`, `MODULARITY`,
`MIGRATION`, `REQUEST_REPLY`, `EVENT_DRIVEN`, `MESSAGING`, `TRANSACTION`,
`CONSISTENCY`, `READ_MODEL`, `CACHE`, `CONCURRENCY`, `FAILURE_CONTROL`,
`TRAFFIC_CONTROL` e `RECOVERY`.

## DESIGN

### Strategy / Policy

- **Tags:** `COMPOSITION`, `DOMAIN`.
- **Problema:** uma regra varia por contexto sem justificar condicionais espalhadas.
- **Sinais/forcas:** variantes legitimas, selecao explicita, extensibilidade versus indirecao.
- **Bom encaixe:** calculo, autorizacao ou politica com contrato estavel e variantes testaveis.
- **Contraindicacoes:** uma unica regra simples ou variantes que nao compartilham semantica.
- **Falhas tipicas:** strategies sem comportamento, selecao oculta e explosao de classes.
- **Observabilidade:** variante selecionada, motivo e resultado sem dados sensiveis.
- **Gate:** testes de contrato para todas as variantes e busca por condicionais duplicadas.
- **Combinacoes perigosas:** Service Locator torna a selecao invisivel; Factory generica mascara dependencias.

### Factory

- **Tags:** `COMPOSITION`, `DOMAIN`.
- **Problema:** construcao valida exige invariantes ou escolha de implementacao.
- **Sinais/forcas:** criacao complexa, defaults controlados, acoplamento versus consistencia.
- **Bom encaixe:** aggregate ou adapter que nao pode nascer em estado invalido.
- **Contraindicacoes:** construtor direto e claro ja protege o objeto.
- **Falhas tipicas:** factory que apenas chama construtor, estado global e retorno parcialmente inicializado.
- **Observabilidade:** falhas de criacao classificadas e variante criada.
- **Gate:** testes de invariantes na criacao e proibicao de bypass quando material.
- **Combinacoes perigosas:** Abstract Factory prematura e DI container usado como dominio.

### Adapter

- **Tags:** `BOUNDARY`, `COMPOSITION`.
- **Problema:** interfaces externas ou legadas nao correspondem ao contrato interno.
- **Sinais/forcas:** mudanca de protocolo, schema ou semantica; isolamento versus traducao adicional.
- **Bom encaixe:** banco, SDK, API externa, fila ou legado atras de um port estavel.
- **Contraindicacoes:** wrapper um-para-um sem fronteira ou diferenca semantica.
- **Falhas tipicas:** vazar tipos externos, engolir erros e duplicar regra de negocio.
- **Observabilidade:** latencia, erro externo, traducao aplicada e versao do contrato.
- **Gate:** imports externos limitados ao adapter e contract tests do port.
- **Combinacoes perigosas:** adapter mais cache sem ownership de invalidacao; adapter encadeado sem tracing.

### Decorator

- **Tags:** `COMPOSITION`, `FAILURE_CONTROL`.
- **Problema:** adicionar comportamento transversal preservando o contrato base.
- **Sinais/forcas:** logging, metricas, cache ou autorizacao combinavel; reuso versus ordem implicita.
- **Bom encaixe:** comportamento ortogonal com ordem declarada e testes de composicao.
- **Contraindicacoes:** regra central de dominio ou cadeia cuja ordem altera semantica sem ficar visivel.
- **Falhas tipicas:** dupla execucao, excecao escondida e pilha impossivel de depurar.
- **Observabilidade:** cadeia e ordem ativas, duracao por camada e correlacao.
- **Gate:** teste da ordem e da equivalencia do contrato com e sem decorator.
- **Combinacoes perigosas:** retry fora de idempotencia; cache fora de autorizacao tenant-aware.

### Repository

- **Tags:** `BOUNDARY`, `DOMAIN`, `TRANSACTION`.
- **Problema:** dominio precisa carregar e persistir aggregates sem possuir detalhes do storage.
- **Sinais/forcas:** invariantes de aggregate, queries orientadas ao dominio, isolamento versus abstracao.
- **Bom encaixe:** escrita de aggregate com contrato de persistencia semanticamente rico.
- **Contraindicacoes:** CRUD trivial, projection read-only ou wrapper generico do ORM.
- **Falhas tipicas:** repository por tabela, `findAll` sem limite e cross-write entre modulos.
- **Observabilidade:** query/command, latencia, cardinalidade e conflito transacional.
- **Gate:** ownership de escrita, queries paginadas e imports do ORM confinados.
- **Combinacoes perigosas:** Generic Repository apaga a linguagem do dominio; CQRS duplicado sem necessidade.

### Specification

- **Tags:** `DOMAIN`, `COMPOSITION`.
- **Problema:** predicados de negocio reutilizaveis precisam ser compostos e explicados.
- **Sinais/forcas:** filtros complexos, regra nomeada, execucao em memoria ou storage.
- **Bom encaixe:** elegibilidade ou selecao com semantica estavel e testes de verdade.
- **Contraindicacoes:** filtro local simples ou traducao para query que muda a semantica.
- **Falhas tipicas:** DSL opaca, N+1 e regra divergente entre runtime e banco.
- **Observabilidade:** specification aplicada, parametros seguros e cardinalidade resultante.
- **Gate:** testes equivalentes nas implementacoes e plano de query inspecionado quando critico.
- **Combinacoes perigosas:** Repository generico mais Specification pode recriar um ORM inferior.

## ARCHITECTURE

### Modular Monolith

- **Tags:** `MODULARITY`, `BOUNDARY`, `TRANSACTION`.
- **Problema:** separar dominios e ownership sem custo operacional distribuido.
- **Sinais/forcas:** um deploy, time pequeno/medio, transacoes locais, autonomia futura.
- **Bom encaixe:** produto em evolucao com fronteiras validaveis no build e runtime.
- **Contraindicacoes:** isolamento operacional/regulatorio obrigatorio ou escalabilidade independente comprovada.
- **Falhas tipicas:** pastas chamadas modulos sem API publica, cross-write e ciclos.
- **Observabilidade:** dependencia entre modulos, chamadas e falhas por dominio.
- **Gate:** grafo aciclico, imports permitidos e owner unico de dados.
- **Combinacoes perigosas:** banco compartilhado sem ownership cria monolito acoplado; event bus interno pode mascarar ciclo.

### Layered Architecture

- **Tags:** `MODULARITY`, `BOUNDARY`.
- **Problema:** separar apresentacao, aplicacao, dominio e infraestrutura por responsabilidade.
- **Sinais/forcas:** fluxo uniforme, onboarding, clareza versus mudancas atravessando camadas.
- **Bom encaixe:** sistema coeso com regras de dependencia simples e verificaveis.
- **Contraindicacoes:** features independentes sofrem acoplamento horizontal ou dominio nao e o centro.
- **Falhas tipicas:** camada pass-through, regra em controller e dominio dependente de framework.
- **Observabilidade:** latencia por camada apenas quando ajuda diagnostico, sem spans artificiais.
- **Gate:** imports direcionais e testes que localizam regras no owner correto.
- **Combinacoes perigosas:** camadas globais mais microservicos geram mudanca coordenada em muitos repos.

### Hexagonal / Ports And Adapters

- **Tags:** `BOUNDARY`, `DOMAIN`, `COMPOSITION`.
- **Problema:** proteger regras centrais de protocolos, frameworks e fornecedores.
- **Sinais/forcas:** multiplos adapters, testes sem infraestrutura, estabilidade interna versus interfaces extras.
- **Bom encaixe:** dominio relevante com entradas/saidas volateis ou varios canais.
- **Contraindicacoes:** CRUD simples onde ports apenas renomeiam SDK/ORM.
- **Falhas tipicas:** port definido pelo fornecedor, adapter com regra e interface para cada classe.
- **Observabilidade:** adapter, port, versao e erro de traducao.
- **Gate:** dominio sem imports externos e contract tests por adapter.
- **Combinacoes perigosas:** DI magica esconde grafo; Repository generico enfraquece o port.

### Vertical Slice

- **Tags:** `MODULARITY`, `DOMAIN`.
- **Problema:** reduzir mudancas transversais agrupando comportamento por caso de uso.
- **Sinais/forcas:** features independentes, ownership por fluxo, duplicacao local versus acoplamento global.
- **Bom encaixe:** comandos/queries com limites claros e pouca logica compartilhada essencial.
- **Contraindicacoes:** invariantes compartilhadas seriam copiadas entre slices.
- **Falhas tipicas:** duplicar autorizacao, transacao ou linguagem de dominio.
- **Observabilidade:** fluxo/slice, comando e resultado correlacionados.
- **Gate:** testes por slice e regras comuns explicitamente owned.
- **Combinacoes perigosas:** CQRS por pasta sem necessidade; slices escrevendo dados uns dos outros.

### Strangler Fig

- **Tags:** `MIGRATION`, `BOUNDARY`, `RECOVERY`.
- **Problema:** substituir legado gradualmente mantendo consumidores operacionais.
- **Sinais/forcas:** corte incremental, coexistencia, risco de big bang versus custo temporario.
- **Bom encaixe:** roteamento por capability e criterio observavel de paridade/remocao.
- **Contraindicacoes:** nao ha seam de roteamento ou coexistencia viola integridade.
- **Falhas tipicas:** proxy permanente, dupla fonte de verdade e caminhos nunca removidos.
- **Observabilidade:** percentual roteado, divergencia, fallback e uso do legado.
- **Gate:** paridade, rollback de rota e deadline de remocao por etapa.
- **Combinacoes perigosas:** dual write sem reconciliacao; cache compartilhado entre semanticas diferentes.

## INTEGRATION

### Request / Reply

- **Tags:** `REQUEST_REPLY`, `BOUNDARY`.
- **Problema:** consumidor precisa de resposta imediata com semantica de erro definida.
- **Sinais/forcas:** baixa latencia, acoplamento temporal, simplicidade versus disponibilidade conjunta.
- **Bom encaixe:** consulta/comando curto cujo resultado e necessario para continuar.
- **Contraindicacoes:** trabalho longo, fan-out fragil ou consumidor tolera assincronia.
- **Falhas tipicas:** timeout ausente, retry de escrita nao idempotente e cadeia sincronica longa.
- **Observabilidade:** latencia, timeout, status semantico e dependencia chamada.
- **Gate:** budgets de timeout, contract test e limite de profundidade sincronica.
- **Combinacoes perigosas:** retry multiplicado em cada hop causa retry storm.

### Publish / Subscribe

- **Tags:** `EVENT_DRIVEN`, `MESSAGING`, `CONSISTENCY`.
- **Problema:** varios consumidores reagem a um fato sem acoplamento direto ao produtor.
- **Sinais/forcas:** fan-out, autonomia, consistencia eventual versus operacao mais complexa.
- **Bom encaixe:** fato imutavel com owner, schema e consumidores tolerantes a repeticao.
- **Contraindicacoes:** comando dirigido, resposta imediata ou ausencia de ownership do evento.
- **Falhas tipicas:** evento generico, ordem presumida, consumidor nao idempotente e schema quebrado.
- **Observabilidade:** lag, redelivery, versao, DLQ e resultado por consumidor.
- **Gate:** schema compatibility, idempotencia e replay testado.
- **Combinacoes perigosas:** event bus como Service Locator; coreografia sem limite vira saga invisivel.

### Transactional Outbox / Inbox

- **Tags:** `EVENT_DRIVEN`, `MESSAGING`, `TRANSACTION`, `CONSISTENCY`.
- **Problema:** persistir mudanca e intencao de publicar sem dual write inseguro.
- **Sinais/forcas:** banco local, entrega at-least-once, consistencia versus latencia/operacao.
- **Bom encaixe:** escrita critica seguida de evento ou comando assincrono.
- **Contraindicacoes:** storage nao oferece transacao local ou efeito tolera perda explicitamente.
- **Falhas tipicas:** outbox sem limpeza, publisher sem lease e inbox sem chave de deduplicacao.
- **Observabilidade:** idade/backlog, tentativas, duplicatas, poison messages e reconciliacao.
- **Gate:** teste atomico, replay idempotente, retention e alerta de lag.
- **Combinacoes perigosas:** presumir exactly-once; combinar com Saga sem correlacao e ownership.

### Saga

- **Tags:** `EVENT_DRIVEN`, `TRANSACTION`, `CONSISTENCY`, `RECOVERY`.
- **Problema:** coordenar mudancas locais quando nao existe transacao distribuida aceitavel.
- **Sinais/forcas:** fluxo longo, falha parcial, compensacao versus estados intermediarios.
- **Bom encaixe:** passos com invariantes locais, correlacao e compensacoes semanticamente validas.
- **Contraindicacoes:** invariant global exige atomicidade ou compensacao nao desfaz dano real.
- **Falhas tipicas:** mega-saga, compensacao cega, timeout sem reconciliacao e ownership difuso.
- **Observabilidade:** estado, passo, correlacao, tentativas, compensacao e stuck instances.
- **Gate:** testes de falha em cada passo e reconciliacao operacional.
- **Combinacoes perigosas:** coreografia densa sem mapa; retry nao idempotente em compensacao.

### Anti-Corruption Layer

- **Tags:** `BOUNDARY`, `MIGRATION`, `DOMAIN`.
- **Problema:** modelo externo/legado conflita com linguagem e invariantes internas.
- **Sinais/forcas:** semanticas diferentes, migracao, isolamento versus custo de traducao.
- **Bom encaixe:** fronteira com fornecedor ou bounded context que muda independentemente.
- **Contraindicacoes:** modelos ja equivalentes e estaveis.
- **Falhas tipicas:** copia estrutural sem traducao, regra duplicada e tipos externos vazando.
- **Observabilidade:** versao externa, mapping usado, falhas e campos descartados.
- **Gate:** contract tests dos dois lados e imports externos confinados.
- **Combinacoes perigosas:** Adapter e ACL duplicados sem ownership; cache antes da traducao mistura semanticas.

### Webhook Inbox

- **Tags:** `MESSAGING`, `BOUNDARY`, `CONSISTENCY`, `RECOVERY`.
- **Problema:** receber callbacks nao confiaveis, repetidos e fora de ordem sem perder prova.
- **Sinais/forcas:** assinatura, retries do provedor, resposta rapida versus processamento duravel.
- **Bom encaixe:** pagamento, identidade ou integracao que exige deduplicacao e replay.
- **Contraindicacoes:** callback descartavel sem efeito e sem requisito de auditoria.
- **Falhas tipicas:** processar antes de persistir, confiar no payload e deduplicar pelo timestamp.
- **Observabilidade:** event ID, assinatura, idade, duplicatas, estado e replay.
- **Gate:** teste de assinatura, persistencia-before-ack, idempotencia e replay.
- **Combinacoes perigosas:** retry interno mais retry do provedor; DLQ sem runbook.

## DATA

### Unit Of Work

- **Tags:** `TRANSACTION`, `CONSISTENCY`.
- **Problema:** coordenar escritas relacionadas sob um limite transacional explicito.
- **Sinais/forcas:** varias mudancas atomicas, commit unico, clareza versus estado rastreado.
- **Bom encaixe:** caso de uso local com invariantes persistentes no mesmo storage.
- **Contraindicacoes:** fluxo distribuido ou operacao independente por item.
- **Falhas tipicas:** unidade longa, commit implicito e transacao atravessando rede.
- **Observabilidade:** duracao, lock wait, conflito, rollback e quantidade de mudancas.
- **Gate:** limite de transacao em teste e nenhum efeito externo antes do commit.
- **Combinacoes perigosas:** Saga dentro de transacao longa; Repository com commits proprios.

### CQRS

- **Tags:** `READ_MODEL`, `DOMAIN`, `CONSISTENCY`.
- **Problema:** modelos de escrita e leitura tem necessidades comprovadamente diferentes.
- **Sinais/forcas:** consultas complexas, invariantes de escrita, escala assimetrica versus duplicacao.
- **Bom encaixe:** separacao mensuravel melhora modelos, permissao ou performance.
- **Contraindicacoes:** CRUD simples ou equipe nao opera consistencia eventual.
- **Falhas tipicas:** duas arquiteturas sem beneficio, regra de negocio no read model e drift.
- **Observabilidade:** lag de projection, versao, rebuild e divergencia.
- **Gate:** contrato de consistencia, rebuild testado e ownership separado.
- **Combinacoes perigosas:** Event Sourcing por associacao; Vertical Slice duplicando invariantes.

### Event Sourcing

- **Tags:** `EVENT_DRIVEN`, `CONSISTENCY`, `RECOVERY`.
- **Problema:** estado precisa ser derivado de historico imutavel com valor de auditoria/temporalidade.
- **Sinais/forcas:** fatos de negocio, consultas temporais, replay versus schema e operacao complexos.
- **Bom encaixe:** historico e requisito central, nao efeito colateral tecnico.
- **Contraindicacoes:** estado atual basta, retencao/privacidade conflita ou replay nao e dominado.
- **Falhas tipicas:** eventos tecnicos, mutacao historica, upcaster ausente e side effects no replay.
- **Observabilidade:** versao, replay, projection lag, evento invalido e snapshot.
- **Gate:** compatibilidade de eventos, replay deterministico e politica de dados.
- **Combinacoes perigosas:** CQRS automatico; publicar log interno como contrato publico.

### Materialized View

- **Tags:** `READ_MODEL`, `CONSISTENCY`.
- **Problema:** leitura critica exige forma ou custo diferente da fonte de escrita.
- **Sinais/forcas:** agregacao cara, alta leitura, frescor versus duplicacao.
- **Bom encaixe:** SLA e janela de staleness quantificados com rebuild possivel.
- **Contraindicacoes:** query/indice simples resolve ou dado precisa ser estritamente atual.
- **Falhas tipicas:** projection sem checkpoint, rebuild destrutivo e permissao divergente.
- **Observabilidade:** lag, checkpoint, divergencia, tempo de rebuild e freshness.
- **Gate:** teste de rebuild, reconciliacao e autorizacao equivalente.
- **Combinacoes perigosas:** cache adicional sem distinguir staleness; eventos sem versionamento.

### Cache-Aside

- **Tags:** `CACHE`, `CONSISTENCY`, `CONCURRENCY`.
- **Problema:** reduzir custo/latencia de leitura mantendo fonte autoritativa separada.
- **Sinais/forcas:** hot reads, recomputacao, staleness versus invalidacao.
- **Bom encaixe:** chave, TTL, invalidador e comportamento de miss mensuraveis.
- **Contraindicacoes:** dado sensivel sem isolamento, escrita frequente ou consistencia forte.
- **Falhas tipicas:** chave sem tenant, stampede, TTL infinito e cache de erro.
- **Observabilidade:** hit ratio, miss cost, eviction, stale serve e cardinalidade.
- **Gate:** testes de chave/invalidation, limite de TTL e protecao contra stampede.
- **Combinacoes perigosas:** decorator de cache fora da auth; replicas mais cache ampliam staleness.

### Change Data Capture

- **Tags:** `EVENT_DRIVEN`, `CONSISTENCY`, `MIGRATION`.
- **Problema:** propagar mudancas persistidas sem alterar imediatamente o writer.
- **Sinais/forcas:** legado, migracao, alto volume, baixo acoplamento versus semantica tecnica.
- **Bom encaixe:** captura controlada com schema, ordering e ownership da traducao.
- **Contraindicacoes:** evento de negocio exige intencao que o log do banco nao possui.
- **Falhas tipicas:** expor schema fisico, perder DDL, reprocessar sem idempotencia.
- **Observabilidade:** offset, lag, schema change, throughput e poison record.
- **Gate:** replay, compatibilidade de schema e traducao para contrato owned.
- **Combinacoes perigosas:** CDC tratado como domain event; dual pipeline sem reconciliacao.

## RESILIENCE

### Timeout Budget

- **Tags:** `FAILURE_CONTROL`, `REQUEST_REPLY`.
- **Problema:** impedir espera indefinida e preservar budget ponta a ponta.
- **Sinais/forcas:** dependencia remota, latencia caudal, completude versus capacidade.
- **Bom encaixe:** toda chamada remota ou espera bloqueante com deadline propagado.
- **Contraindicacoes:** operacao local deterministica onde timeout mascara bug.
- **Falhas tipicas:** timeout maior que o caller, default infinito e cancelamento nao propagado.
- **Observabilidade:** deadline, timeout por dependencia e trabalho cancelado.
- **Gate:** testes de timeout/cancelamento e soma dos budgets abaixo do SLO.
- **Combinacoes perigosas:** retry sem budget; saga com timeout menor que commit confirmado.

### Retry With Backoff And Jitter

- **Tags:** `FAILURE_CONTROL`, `RECOVERY`.
- **Problema:** recuperar falha transitoria sem sincronizar carga ou repetir dano.
- **Sinais/forcas:** erro transitorio classificado, idempotencia, recuperacao versus amplificacao.
- **Bom encaixe:** operacao idempotente com tentativas, backoff, jitter e deadline limitados.
- **Contraindicacoes:** validacao, auth negada, conflito permanente ou escrita nao idempotente.
- **Falhas tipicas:** retry em todas as camadas, sem jitter, fila infinita e erro indiscriminado.
- **Observabilidade:** tentativa, classe do erro, atraso, exaustao e sucesso posterior.
- **Gate:** testes de classificacao, limite e budget; uma camada dona do retry.
- **Combinacoes perigosas:** retry storm com Request/Reply; Circuit Breaker contando erro de cliente.

### Circuit Breaker

- **Tags:** `FAILURE_CONTROL`, `TRAFFIC_CONTROL`.
- **Problema:** parar chamadas temporariamente quando uma dependencia remota falha sistemicamente.
- **Sinais/forcas:** falha correlacionada, recuperacao sondavel, fail-fast versus falso positivo.
- **Bom encaixe:** dependencia remota e fallback/erro rapido semanticamente aceitos.
- **Contraindicacoes:** chamada local, erro por request ou baixa amostra sem politica.
- **Falhas tipicas:** estado global entre tenants, threshold arbitrario e half-open sem limite.
- **Observabilidade:** estado, transicoes, taxa por classe e probe outcome.
- **Gate:** teste open/half-open/close e exclusao de erros nao atribuiveis ao servidor.
- **Combinacoes perigosas:** breaker mais retry sem budget; fallback stale sem rotulo.

### Bulkhead

- **Tags:** `CONCURRENCY`, `FAILURE_CONTROL`.
- **Problema:** impedir que uma carga/dependencia esgote recursos de fluxos independentes.
- **Sinais/forcas:** pools compartilhados, workloads heterogeneos, isolamento versus ociosidade.
- **Bom encaixe:** limites por dependencia, tenant ou classe de prioridade mensuravel.
- **Contraindicacoes:** recurso unico nao particionavel ou volume insuficiente para configurar.
- **Falhas tipicas:** muitos pools minimos, starvation e fila sem limite.
- **Observabilidade:** ocupacao, fila, rejeicao, espera e utilizacao por particao.
- **Gate:** limites finitos e teste de saturacao/isolamento.
- **Combinacoes perigosas:** retry realimenta particao saturada; rate limit sem prioridade.

### Idempotency And Deduplication

- **Tags:** `CONSISTENCY`, `RECOVERY`, `CONCURRENCY`.
- **Problema:** repeticao legitima de request/evento nao pode duplicar efeito.
- **Sinais/forcas:** retries, double click, at-least-once, storage de chave versus seguranca.
- **Bom encaixe:** efeito critico com identidade, escopo e janela de deduplicacao definidos.
- **Contraindicacoes:** operacao naturalmente idempotente ou chave sem autenticidade/escopo.
- **Falhas tipicas:** chave global, payload diferente com mesma chave e resultado nao persistido.
- **Observabilidade:** chave hash segura, hit, conflito de payload e expiracao.
- **Gate:** testes concorrentes/replay e constraint atomica no owner.
- **Combinacoes perigosas:** cache usado como unico ledger; retry antes de persistir resultado.

### Rate Limiting / Load Shedding

- **Tags:** `TRAFFIC_CONTROL`, `CONCURRENCY`, `FAILURE_CONTROL`.
- **Problema:** proteger capacidade e fairness antes da saturacao total.
- **Sinais/forcas:** limite conhecido, abuso/burst, disponibilidade versus rejeicao.
- **Bom encaixe:** cota por identidade/tenant e prioridade com resposta/retry semantics.
- **Contraindicacoes:** gargalo desconhecido ou limite global que pune todos por um tenant.
- **Falhas tipicas:** chave spoofable, contador nao atomico e `Retry-After` ausente.
- **Observabilidade:** permitido/rejeitado, chave agregada, saturacao e prioridade.
- **Gate:** teste de burst/fairness, limites configurados e fail mode definido.
- **Combinacoes perigosas:** retries imediatos amplificam rejeicao; breaker global confunde limite com outage.

### Dead Letter And Replay

- **Tags:** `MESSAGING`, `RECOVERY`, `FAILURE_CONTROL`.
- **Problema:** isolar mensagens irrecuperaveis sem bloquear o fluxo e permitir reparo auditavel.
- **Sinais/forcas:** poison message, tentativas esgotadas, continuidade versus operacao manual.
- **Bom encaixe:** fila com owner, retention, runbook e replay idempotente.
- **Contraindicacoes:** DLQ vira destino silencioso sem SLA de tratamento.
- **Falhas tipicas:** PII sem protecao, replay em massa e perda de motivo/contexto.
- **Observabilidade:** volume, idade, motivo, owner, replay e reincidencia.
- **Gate:** alerta, runbook testado, retention e replay seguro em amostra.
- **Combinacoes perigosas:** Outbox sem reconciliacao; Saga sem correlacao no DLQ.

## Anti-Patterns E Sinais De Bloqueio

| Anti-pattern | Sinal | Risco | Pergunta/gate minimo |
|---|---|---|---|
| Pattern por prestigio | decisao cita tendencia, nao problema/forcas | complexidade sem retorno | alternativa simples foi medida? |
| Distributed Monolith | deploys separados, mudanca e falha coordenadas | custo distribuido sem autonomia | contract/dependency graph prova independencia? |
| Shared Database Writes | varios modulos escrevem a mesma entidade | invariantes e ownership quebrados | gate de owner unico bloqueia cross-write? |
| Dual Write ingenuo | banco e broker/terceiro atualizados sem estrategia | estado parcial e perda | existe outbox, idempotencia ou reconciliacao? |
| Generic Repository | CRUD generico esconde linguagem e limites | queries ilimitadas e dominio anemico | contrato expressa aggregate/caso de uso? |
| Event Bus como Service Locator | qualquer modulo publica/consome qualquer coisa | dependencias invisiveis | produtor, consumidor e schema estao catalogados? |
| Retry indiscriminado | qualquer erro e repetido em varias camadas | storm e efeito duplicado | erro, owner, limite, jitter e idempotencia existem? |
| Cache sem politica | TTL/chave/invalidation/tenant nao declarados | dado stale ou vazamento | gate testa chave, invalidacao e isolamento? |
| Mega-Saga | um fluxo coordena muitos dominios sem limites | estado impossivel de operar | pode dividir capability ou reduzir participantes? |
| CQRS/Event Sourcing por padrao | duplicacao sem driver mensurado | custo operacional e drift | NFR ou requisito historico exige isso? |
| Circuit Breaker local | breaker envolve codigo deterministico/local | mascara defeito e adiciona estado | ha dependencia remota e fallback valido? |
| Pastas como arquitetura | nomes existem, imports/ownership nao sao cobrados | fronteira ficticia | fitness gate prova dependencia e dados? |

Anti-pattern comprovado recebe `PROIBIDO` somente quando existe gate bloqueante.
Quando ainda houver duvida, use `SEM_DECISAO` ou `PROPOSTO` e colete evidencia.
