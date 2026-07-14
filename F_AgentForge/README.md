# F_AgentForge - Fabrica de Agentes

5 supervisores que criam, calibram e validam agentes sob demanda. Nenhum deles
implementa. Todos garantem que o agente certo nasca para uma lacuna real.

---

## O Problema Que Resolve

Agentes estaticos sao bons para tarefas recorrentes. Quando o projeto precisa de
algo que nenhum agente existente cobre bem, ou quando uma tarefa exige uma
combinacao recorrente de competencias, a fabrica cria um agente sob medida.

A fabrica so cria agente quando:

- a lacuna e real;
- a lacuna e recorrente ou claramente reutilizavel;
- nenhum agente atual cobre pelo menos 70% do dominio necessario;
- criar um novo papel reduz risco ou repeticao de trabalho.

Quando a lacuna e pontual, use prompt, checklist, template ou composicao dos
agentes atuais.

---

## Os 5 Supervisores

```text
F_Agent_Foreman.md         Orquestrador da fabrica
F_Agent_ContextScanner.md  Le projeto, status, regras, stack
F_Agent_AgentArchitect.md  Projeta estrutura, escopo, regras do agente
F_Agent_AgentComposer.md   Escreve o arquivo .md/.toml final
F_Agent_WorkAuditor.md     Valida o trabalho do agente criado
```

---

## Fluxo De Execucao

```text
Pedido do usuario ou do Camisa10
        |
   F_Foreman - entende, classifica, aplica regra dos 70%
        |
   F_ContextScanner - le o projeto inteiro, entrega relatorio
        |
   F_AgentArchitect - projeta blueprint do agente
        |
   F_AgentComposer - escreve o arquivo final
        |
   Agente criado executa tarefas reais
        |
   F_WorkAuditor - valida entrega, aprova ou rejeita
        |
   Feedback loop - ajusta agente se necessario
```

---

## Como Usar

### Invocacao Simples

```text
"Crie um agente para [tarefa recorrente]."
"Preciso de um agente que [faca X] considerando [Y]."
"Monte um agente para cobrir o fluxo recorrente de [A ate B]."
```

### Invocacao Via Camisa10

```text
"@C10, essa tarefa nao tem agente adequado. Acione a fabrica."
```

### Invocacao Direta

```text
"@F, avalie se preciso de um agente de auditoria de acessibilidade WCAG para o frontend."
```

---

## Integracao Com A .codex Existente

A fabrica nao substitui nenhum agente existente. Ela os complementa criando
agentes dinamicos quando necessario.

Os agentes criados pela fabrica:

- seguem o padrao de nomenclatura da `.codex/`;
- herdam o protocolo anti-alucinacao do `AGENTS.md`;
- respeitam `CONSTITUTION.md` e `DECISIONS.md` quando existirem;
- se encaixam no pipeline existente;
- delegam para especialistas (`@S`, `@P`, `@A`, `@V`) quando necessario.

---

## Quando Nao Usar

- A tarefa ja e coberta por um agente existente: use o existente.
- Um agente existente cobre pelo menos 70% do dominio: use ou evolua esse agente.
- A tarefa e trivial e cabe em um prompt curto: nao precisa de agente.
- A tarefa e unica e nao vai se repetir: prompt direto e suficiente.
- A lacuna ainda nao foi comprovada: use `@PICK` ou um checklist antes.

---

## Prefixo E Mencao

- Prefixo de pasta e arquivo: `F_`
- Mencao no chat: `@F` (Forge/Fabrica)
- Pipeline: camada de meta-agente acima do pipeline de execucao
