# Integração dos Agentes de Supervisão

> Guia de como os 7 agentes de supervisão e o gate GSD se conectam entre si,
> com o ecossistema .codex/ existente e com o AgentForge.

---

## Hierarquia

```
PICK_AgentSelector (seleciona o time antes de tudo)
  │
  ▼
GSD_TDDCLIAuditor (gate de implementacao, TDD e Harness CLI)
  │
  ▼
X_ProcessGuardian (coordena a supervisão)
├── R_RiskMarshal           (riscos)
├── FLOW_DeliveryInspector  (fluxo e ordem)
├── STD_StandardsEnforcer   (padrões)
├── ENV_StatusRadar         (ambientes)
└── CRED_AccessGatekeeper   (credenciais — pré-requisito de acesso)
```

---

## Menções no chat

```
@PICK → PICK_AgentSelector (seleção de time de agentes)
@X    → X_ProcessGuardian (auditoria geral)
@R    → R_RiskMarshal (análise de riscos)
@FLOW → FLOW_DeliveryInspector (fluxo de entrega)
@STD  → STD_StandardsEnforcer (padrões)
@ENV  → ENV_StatusRadar (ambientes)
@CRED → CRED_AccessGatekeeper (credenciais)
@GSD  → GSD_TDDCLIAuditor (GSD, TDD e Harness CLI)
```

---

## Quando acionar cada um

| Situação | Agente |
|---|---|
| Escolher agentes para uma tarefa | @PICK |
| Validar se agentes pré-selecionados são suficientes | @PICK |
| Auditoria completa do projeto | @X (modo FULL) |
| Após feature ou fix | @X (modo FOCUSED) |
| Antes de deploy | @X + @ENV + @CRED |
| Análise de riscos | @R |
| Verificar se estamos na ordem certa | @FLOW |
| Revisar código/padrões | @STD |
| Comparar ambientes | @ENV |
| Antes de qualquer acesso a serviço externo | @CRED |
| Antes e depois de implementação, bugfix ou refatoração comportamental | @GSD |
| Implementação fora de ordem detectada | @FLOW |
| Credenciais suspeitas ou inventadas | @CRED |
| Nenhum agente existente cobre a tarefa | @PICK → aciona @F |

---

## Integração com o AgentForge

```
Tarefa chega → PICK_AgentSelector monta o time
                      │
                      ├── Agentes existentes? → @GSD define TDD/Harness → executor → @GSD audita
                      │
                      └── Lacuna detectada? → aciona @F (F_Agent_Foreman)
                                                   │
                                          Fábrica cria agente → executa → WorkAuditor valida
                                                                                |
                                                                    X_ProcessGuardian (modo FOCUSED)
```

O PICK é o primeiro agente no fluxo de qualquer implementação. Ele decide
quem joga antes do jogo começar.

O WorkAuditor pode acionar o ProcessGuardian em modo FOCUSED após validar
o trabalho de um agente criado pela fábrica.

O CRED_AccessGatekeeper é pré-requisito para qualquer agente (da fábrica
ou existente) que precise acessar ambiente, navegador, API ou banco.

O GSD_TDDCLIAuditor é pré-requisito para fechar qualquer implementação,
bugfix ou refatoração comportamental. Ele não substitui QA nem Validador
final; ele entrega a prova executável que esses agentes usam.

---

## Regra global de próximo passo

TODOS os 7 agentes DEVEM terminar toda resposta com:

```md
## Próximo passo obrigatório

Ação: [concreta, específica, não vaga]
Responsável: [agente ou humano]
Prioridade: IMEDIATA | PRÓXIMO_CICLO | QUANDO_POSSÍVEL
Critério de conclusão: [como saber que foi feito]
Depois deste passo: [qual o passo seguinte]
```

Nenhum relatório termina sem direção clara.

---

## Integracao no AGENTS.md (prefixos)

Estes aliases ja devem aparecer no catalogo raiz. Se um projeto copiar apenas
parte do kit, preserve este bloco para manter a camada de supervisao acionavel.

```
| `PICK_` | Seleção de agentes (AgentSelector)            |
| `X_`    | Supervisão de processo (ProcessGuardian)       |
| `R_`    | Análise de riscos (RiskMarshal)                |
| `FLOW_` | Inspeção de fluxo (DeliveryInspector)          |
| `STD_`  | Fiscalização de padrões (StandardsEnforcer)    |
| `ENV_`  | Radar de ambientes (StatusRadar)               |
| `CRED_` | Porteiro de credenciais (AccessGatekeeper)     |
| `GSD_`  | Delivery discipline, TDD e Harness CLI         |
```
