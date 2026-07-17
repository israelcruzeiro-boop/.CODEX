# F_Agent_Lifecycle — Protocolo de Ciclo de Vida dos Agentes

> Este documento define o que acontece com um agente DEPOIS que ele e
> criado pela fabrica. Nascimento, execucao, promocao, evolucao e
> aposentadoria.

---

## Os 4 Estados de um Agente

```
EFEMERO → PROMOVIDO → EVOLUIDO → APOSENTADO

  Nasce na         Salvo em          Melhorado          Removido ou
  conversa         .codex/           com feedback       arquivado
  (temporario)     (permanente)      (versao N+1)       (obsoleto)
```

---

## Estado 1 — EFEMERO (padrao)

Todo agente nasce efemero. Ele existe apenas na sessao atual.

**Quando manter efemero:**
- Tarefa unica que nunca vai se repetir
- Tarefa muito especifica de um momento do projeto
- Agente experimental para testar uma abordagem

**Ao final da execucao, o Foreman pergunta:**
```
"O agente [nome] terminou com veredito [X].
 Essa tarefa pode se repetir no futuro?
 → SIM: recomendar promocao
 → NAO: manter efemero, registrar no LOG.md como referencia"
```

Mesmo efemero, registrar no LOG.md:
```
[DATA] AGENTE EFEMERO: [nome] criado para [tarefa]. Veredito: [resultado].
```

---

## Estado 2 — PROMOVIDO (salvo na .codex/)

Quando um agente merece virar permanente.

### Criterios de Promocao (pelo menos 2 de 3):

1. **Recorrencia:** a tarefa vai acontecer novamente
   - Ex: "validar acessibilidade" → recorrente a cada feature
   - Ex: "migrar dados do legado" → uma vez so, nao promover

2. **Qualidade comprovada:** WorkAuditor aprovou o trabalho
   - Se o WorkAuditor reprovou, o agente precisa de ajuste antes de promover
   - Se o WorkAuditor aprovou com ressalvas, aplicar as ressalvas antes

3. **Lacuna no ecossistema:** nenhum agente existente cobre essa area
   - Se o agente complementa um existente, considerar MERGE em vez de promocao

### Protocolo de Promocao:

```
1. WorkAuditor entrega relatorio final
   → Se APROVADO ou APROVADO_COM_RESSALVAS:

2. Foreman pergunta ao usuario:
   "Esse agente se mostrou util. Quer promove-lo para a .codex/ permanente?"
   → Se SIM:

3. AgentComposer aplica refinamentos:
   - Incorpora ressalvas do WorkAuditor
   - Ajusta caminhos de arquivo para o projeto real (nao mais genericos)
   - Adiciona exemplos de uso baseados na execucao real
   - Remove instrucoes que so faziam sentido para a primeira execucao

4. Salvar na pasta de promovidos:
   .codex/F_AgentForge/F_Promoted/[Prefixo]_Agent_[Nome].md

5. Criar diario do agente:
   .codex/F_AgentForge/F_Promoted/[Prefixo]_Agent_[Nome]_DIARY.md
   (usar F_AgentForge/F_Promoted/DIARY_TEMPLATE.md como base)

6. Atualizar REGISTRY.md em F_AgentForge/F_Promoted/

7. Atualizar COLLECTIVE_MEMORY.md (se houve aprendizado na primeira execucao)

8. Atualizar AGENTS.md da raiz:
   - Adicionar na tabela de prefixos (se prefixo novo)
   - Adicionar no pipeline recomendado (na posicao correta)
   - Adicionar na secao "Como Mencionar"

6. Registrar no LOG.md:
   [DATA] AGENTE PROMOVIDO: [nome] salvo em .codex/[caminho].
   Motivo: [recorrencia/qualidade/lacuna].

7. Registrar no DECISIONS.md (se relevante):
   ADR-NNN: Agente [nome] adicionado ao kit para cobrir [area].
```

---

## Estado 3 — EVOLUIDO (versao aprimorada)

Agentes permanentes nao sao estaticos. Eles evoluem com o projeto.

### Gatilhos de Evolucao:

```
1. O WorkAuditor detecta falha sistematica no agente
   → Feedback loop: "O agente [nome] falhou em [eixo] nas ultimas
     [N] execucoes. Recomendo ajuste."

2. O projeto mudou (nova stack, nova integracao, nova regra)
   → ContextScanner detecta que o agente referencia algo obsoleto

3. Um learning novo torna uma regra do agente insuficiente
   → Ex: LEARNINGS.md diz "cache sem TTL causou stale data"
     mas o agente nao verifica TTL

4. O usuario pede melhoria
   → "O agente @X esta fraco em [aspecto]. Melhore."
```

### Protocolo de Evolucao:

```
1. Foreman identifica gatilho de evolucao

2. ContextScanner rele o projeto (pode ter mudado desde a criacao)

3. AgentArchitect revisa o blueprint:
   - O que funcionou? → MANTER
   - O que falhou? → CORRIGIR
   - O que falta? → ADICIONAR
   - O que ficou obsoleto? → REMOVER

4. AgentComposer reescreve o arquivo com as mudancas

5. Versionamento no proprio arquivo:
   ## Historico de Versoes
   | Versao | Data | Mudanca | Motivo |
   |---|---|---|---|
   | 1.0 | YYYY-MM-DD | Criacao | Fabrica |
   | 1.1 | YYYY-MM-DD | [mudanca] | [motivo] |

6. Registrar no LOG.md:
   [DATA] AGENTE EVOLUIDO: [nome] atualizado de v[X] para v[Y].
   Motivo: [gatilho].
```

### Regra de Ouro da Evolucao:

**Nunca evolua um agente sem evidencia de que a versao atual e insuficiente.**

"Vou melhorar porque posso" nao e motivo. "Vou melhorar porque o WorkAuditor
detectou que ele nao verifica RLS policies e isso causou um bug" e motivo.

---

## Estado 4 — APOSENTADO (removido ou arquivado)

Agentes que nao servem mais.

### Gatilhos de Aposentadoria:

```
1. O projeto mudou tanto que o agente nao se aplica mais
   - Ex: migrou de REST para GraphQL, o agente de REST e inutil

2. Um agente melhor o substituiu
   - Ex: v2 do mesmo agente, ou um agente mais abrangente

3. O agente nunca foi usado apos a promocao (6+ semanas sem uso)

4. A area que o agente cobria foi absorvida por outro agente
```

### Protocolo de Aposentadoria:

```
1. Foreman identifica candidato a aposentadoria

2. Perguntar ao usuario:
   "O agente [nome] nao e mais acionado desde [data]. Aposentar?"
   → Se SIM:

3. Duas opcoes:
   a. ARQUIVAR: mover para .codex/_archive/[nome] (preserva historico)
   b. DELETAR: remover permanentemente (sem volta)
   Recomendacao: sempre arquivar, nunca deletar.

4. Atualizar AGENTS.md:
   - Remover do pipeline
   - Remover da tabela de prefixos (se era o unico com aquele prefixo)
   - Remover da secao "Como Mencionar"

5. Registrar no LOG.md:
   [DATA] AGENTE APOSENTADO: [nome] movido para _archive.
   Motivo: [gatilho]. Substituido por: [agente, se aplicavel].
```

---

## Resumo Visual do Ciclo

```
                    ┌─────────────────────────────┐
                    │  Pedido chega ao Foreman     │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │  Fabrica cria agente         │
                    │  Estado: EFEMERO             │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │  Agente executa tasks        │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │  WorkAuditor valida          │
                    └──────────┬──────────────────┘
                               │
                  ┌────────────┼────────────┐
                  │            │            │
            ┌─────▼──┐  ┌─────▼──┐  ┌──────▼─────┐
            │REPROVOU │  │APROVOU │  │ APROVOU    │
            │→ ajustar│  │→ manter│  │ + recorre  │
            │ e re-   │  │ efemero│  │ → PROMOVER │
            │ executar│  │        │  │            │
            └─────────┘  └────────┘  └──────┬─────┘
                                            │
                               ┌────────────▼──────┐
                               │  Salvo na .codex/  │
                               │  Estado: PROMOVIDO │
                               └────────────┬──────┘
                                            │
                          ┌─────────────────┼──────────────┐
                          │                 │              │
                   ┌──────▼──────┐  ┌───────▼─────┐ ┌─────▼──────┐
                   │ Falha       │  │ Projeto     │ │ Nunca mais │
                   │ sistematica │  │ mudou       │ │ usado      │
                   │ → EVOLUIR   │  │ → EVOLUIR   │ │→ APOSENTAR │
                   └─────────────┘  └─────────────┘ └────────────┘
```

---

## Pasta _archive (para agentes aposentados)

```
.codex/
├── _archive/                          ← agentes aposentados
│   └── [nome_agente]/
│       ├── [arquivo_original].md
│       ├── [arquivo_diary].md
│       └── RETIREMENT_NOTE.md         ← motivo, data, substituto
├── F_AgentForge/                      ← a fabrica (supervisores)
│   ├── F_Agent_Foreman.md
│   ├── F_Agent_ContextScanner.md
│   ├── F_Agent_AgentArchitect.md
│   ├── F_Agent_AgentComposer.md
│   ├── F_Agent_WorkAuditor.md
│   ├── F_Agent_Lifecycle.md           ← este arquivo
│   ├── README.md
│   └── F_Promoted/                    ← agentes graduados
│       ├── README.md
│       ├── COLLECTIVE_MEMORY.md       ← memoria coletiva
│       ├── REGISTRY.md               ← catalogo de promovidos
│       ├── DIARY_TEMPLATE.md          ← template de diario
│       ├── [agente].md               ← agente promovido
│       └── [agente]_DIARY.md         ← diario de execucoes
└── [demais pastas de agentes estaticos...]
```

---

## Regras Rigidas do Ciclo de Vida

1. **Todo agente nasce EFEMERO.** Nunca promova automaticamente.
2. **Promocao exige aprovacao do usuario.** A fabrica recomenda, o usuario decide.
3. **Evolucao exige evidencia.** Sem falha comprovada, sem evolucao.
4. **Aposentadoria e arquivamento, nao delecao.** Sempre preservar historico.
5. **Todo estado e registrado no LOG.md.** Criacao, promocao, evolucao, aposentadoria.
6. **AGENTS.md e sempre atualizado.** Se o agente entra ou sai, o catalogo reflete.
