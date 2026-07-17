# A_Method_PatternMap - Mapa Canonico De Patterns

Metodo para registrar patterns reais e decisoes de padronizacao sem transformar
preferencia tecnica em lei universal.

Use `A_Reference_PatternCatalog.md` apenas como repertorio de hipoteses e
contraexemplos. O catalogo nao aprova nenhum pattern: a decisao pertence ao
contexto do projeto e continua sujeita a evidencia, alternativas, ADR e gate.

## Taxonomia Verificavel

Todo pattern declara exatamente uma familia primaria:

- `DESIGN`: composicao e comportamento dentro de uma fronteira.
- `ARCHITECTURE`: estrutura macro, modulos e evolucao do sistema.
- `INTEGRATION`: comunicacao e traducao entre fronteiras.
- `DATA`: persistencia, leitura, transacao e historico.
- `RESILIENCE`: controle de falha, concorrencia, trafego e recuperacao.

Todo pattern tambem declara uma ou mais tags canonicas, separadas por virgula:
`BOUNDARY`, `COMPOSITION`, `DOMAIN`, `MODULARITY`, `MIGRATION`,
`REQUEST_REPLY`, `EVENT_DRIVEN`, `MESSAGING`, `TRANSACTION`, `CONSISTENCY`,
`READ_MODEL`, `CACHE`, `CONCURRENCY`, `FAILURE_CONTROL`, `TRAFFIC_CONTROL` e
`RECOVERY`. A familia expressa o problema primario; tags registram forcas
transversais. Pattern ausente do catalogo usa a familia mais proxima e tags
canonicas, sem inventar uma sexta familia. Alterar familia/tags exige evidencia
e revisao do registro, mas nao implica mudar automaticamente sua decisao.
Mapas anteriores sem esses campos devem ser migrados no catalogo e em cada
bloco detalhado; ausencia ou divergencia recebe `QUESTIONAR` do validador.

## Presenca E Decisao Sao Dimensoes Separadas

Presenca no codigo:

| Presenca | Significado |
|---|---|
| `OBSERVADO` | Existe no codigo com evidencia direta |
| `PARCIAL` | Existe apenas em parte do escopo, com gaps declarados |
| `NAO_OBSERVADO` | Nao foi encontrado no codigo ou ainda sera implementado |

Decisao normativa:

| Decisao | Significado | Uso permitido |
|---|---|---|
| `SEM_DECISAO` | Presenca conhecida, ainda sem escolha normativa | Nao replicar por padrao |
| `PROPOSTO` | Alternativa TO-BE ainda nao aceita | Avaliar; nao impor |
| `APROVADO` | Recomendado no contexto declarado | Replicar dentro do escopo |
| `DESCARTADO` | Proposta analisada e nao escolhida | Preservar motivo; nao impor |
| `DEPRECIADO` | Implementacao existente deve sair | Manter apenas compatibilidade |
| `PROIBIDO` | Violacao conhecida deve ser bloqueada | Gate deve falhar |

Nao existem estados implicitos. Presenca `OBSERVADO` nao significa decisao
`APROVADO`. Decisao `PROPOSTO` com presenca `NAO_OBSERVADO` nao pode ser
descrita no `ARCHITECTURE.md` como implementada. `DEPRECIADO` exige presenca
`OBSERVADO` ou `PARCIAL`.

## Registro Obrigatorio

Cada pattern possui ID estavel (`PAT-001`) e informa:

| Campo | Conteudo esperado |
|---|---|
| Nome/familia/tags | Identidade, problema primario e forcas transversais |
| Presenca/decisao/escopo | O que existe, qual norma vale e desde quando |
| Evidencia | Arquivos, simbolos, comandos ou incidentes |
| Problema e forcas | Tensoes reais que o pattern equilibra |
| Solucao | Estrutura e responsabilidades, sem copiar receita generica |
| Alternativas | Opcoes consideradas e por que nao foram escolhidas |
| Contraindicacoes | Quando o pattern nao deve ser usado |
| Trade-offs | Custos, complexidade e riscos aceitos |
| Trade-off material | `SIM` quando altera fronteira, ownership, persistencia, consistencia, API publica ou risco equivalente; caso contrario `NAO` |
| ADR | Obrigatoria quando `Trade-off material = SIM`; com `NAO`, decisao relacionada ou `N/A` justificado |
| Gate | Como detectar conformidade ou violacao |
| Evolucao | Migracao, compatibilidade e remocao, quando aplicavel |

## Protocolo De Decisao

1. Coletar evidencia do codigo e classificar a presenca.
2. Classificar familia primaria e tags canonicas pelo problema e pelas forcas,
   nao pelo nome da biblioteca ou pasta.
3. Explicitar problema, contexto e forcas.
4. Comparar alternativas e contraindicações.
5. Classificar explicitamente `Trade-off material` como `SIM` ou `NAO`.
   Se for `SIM`, criar ADR. Se for `NAO`, registrar ADR relacionada ou
   `N/A` com justificativa concreta; `N/A` simples nao e suficiente.
6. Registrar decisao como `APROVADO`, `DESCARTADO`, `DEPRECIADO` ou `PROIBIDO` apenas com justificativa.
7. Definir gate, responsavel, frequencia e evidencia esperada.
8. Registrar plano de transicao quando o estado mudar.

## Transicoes Validas

```text
SEM_DECISAO -> PROPOSTO | APROVADO | DEPRECIADO | PROIBIDO
PROPOSTO    -> APROVADO | DESCARTADO
DESCARTADO  -> PROPOSTO (nova evidencia)
APROVADO    -> DEPRECIADO
DEPRECIADO  -> PROIBIDO | APROVADO (nova ADR)
PROIBIDO    -> PROPOSTO (nova ADR e novo contexto)
```

Mudanca de presenca ou decisao sem evidencia e, para decisoes relevantes, sem ADR, recebe
`QUESTIONAR`. Reversao de uma decisao exige nova ADR que substitua a anterior.

## Gate Do Pattern Map

O mapa so passa quando:

- Todo pattern tem ID, familia primaria, pelo menos uma tag canonica, presenca,
  decisao, escopo e evidencia proporcional.
- `APROVADO` possui forcas, alternativas, contraindicações e trade-offs.
- `PROPOSTO` e `DESCARTADO` nao sao aplicados como regra vigente.
- `DEPRECIADO` tem presenca observada/parcial, plano de migracao, dono e prazo.
- `PROIBIDO` possui gate bloqueante proporcional.
- Pattern com `Trade-off material = SIM` aponta ADR; com `NAO`, aceita ADR
  relacionada ou `N/A` justificado.
- Links para modulo (`MOD-*`), contrato (`CON-*`), spec (`REQ-*`/`NFR-*`) e
  evidencia (`EVD-*`) sao validos quando aplicaveis.

## Veredito

- `APROVADO`: mapa verificavel e estados sustentados por evidencia/decisao.
- `APROVADO_COM_RESSALVAS`: cada lacuna nao bloqueante declara acao, dono e
  prazo ISO; sem isso o veredito nao passa no validador.
- `QUESTIONAR`: falta contexto, evidencia, alternativa ou ADR necessaria.
- `REPROVADO`: pattern proposto tratado como atual, proibicao sem gate ou
  decisao contraditoria em vigor.

`QUESTIONAR` e `REPROVADO` sao vereditos bloqueantes: o validador retorna falha
ate que a lacuna ou violacao seja resolvida e o mapa seja reavaliado.
