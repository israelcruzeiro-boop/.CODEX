# Claude Code Adapter - Codex Agent Kit

Este arquivo adapta o Codex Agent Kit para uso no Claude Code sem alterar a
estrutura original do arsenal.

Fonte-mestra do kit:

- `AGENTS.md`
- `C10_Maestro/C10_CAMISA10.md`
- `SUP_Supervisor/SUP_PICK_AgentSelector.md`
- `GSD_DeliveryDiscipline/GSD_Agent_TDDCLIAuditor.md`

Camada Claude:

- `.claude/agents/*.md`

Os arquivos em `.claude/agents/` sao wrappers. Eles existem para o Claude Code
delegar tarefas automaticamente, mas nao substituem os agentes originais. Quando
houver conflito, siga o documento original do agente em `.codex/` ou, quando
rodando dentro desta pasta, no caminho local correspondente.

## Governanca Da Raiz Geral

Em um projeto real, Claude Code deve operar a partir de `PROJECT_ROOT`, a raiz
geral que contem `.codex/`, `.claude/`, `AGENTS.md`, `CLAUDE.md` e os ambientes
do produto, como `back/`, `front/`, `admin/`, `mobile/`, `infra/`, `packages/`
ou equivalentes.

Regra: `.codex/` e a fonte de governanca transversal do projeto inteiro. Os
wrappers Claude podem delegar trabalho em qualquer subpasta da raiz geral quando
a tarefa exigir, mas devem preservar ownership, contratos e organizacao global.

Antes de implementar em uma subpasta, mapear:

- qual ambiente sera afetado;
- quais outros ambientes consomem seus contratos;
- quais comandos devem ser rodados em cada cwd relevante;
- quais arquivos de raiz (`AGENTS.md`, `PROJECT.md`, `STATUS.md`,
  `DECISIONS.md`, `CLAUDE.md`) precisam ser respeitados ou atualizados.

Mudancas que cruzam `back`, `front`, `admin`, `mobile`, infra ou pacotes
compartilhados devem ser tratadas como cross-stack e passar pelos agentes de
arquitetura, Harness, QA e validacao final aplicaveis.

## Regra De Entrada

Se a pessoa nao sabe por onde comecar, esta iniciando um projeto novo ou
retomando um projeto em andamento, use primeiro o subagente
`project-onboarding-guide`. Ele posiciona a fase, aponta gargalos, diz se esta
alinhado ou desalinhado e encaminha ao agente certo. E orientador, nunca trava.

Para tarefas complexas, ambiguas, multi-area, de implementacao, refatoracao,
bugfix, auditoria, release ou risco medio/alto:

1. Use primeiro o subagente `pick-agent-selector`.
2. Ele deve selecionar o time certo e a ordem de acionamento.
3. Se a tarefa nasce de ideia, legado ou feature grande, inclua
   `spec-architect` antes de arquitetura e execucao.
4. Se a tarefa envolve criar, auditar ou sincronizar documentacao estrutural,
   inclua `project-documentation-architect`.
5. Se houver implementacao, bugfix ou refatoracao comportamental, inclua
   `gsd-tdd-cli-auditor`.
6. Se a tarefa tocar banco de dados, schema ou migrations, inclua
   `data-migrations`.
7. Se a tarefa adicionar/atualizar dependencias ou houver CVE, inclua
   `dependency-steward`.
8. Se a entrega virar uma release (versao, changelog, deploy coordenado), inclua
   `release-manager`.
9. Se nenhum agente existente cobrir uma lacuna real, use
   `agent-forge-foreman`.

## Gates Obrigatorios

- Antes de implementar: planta tecnica do repo alvo existente e sincronizada
  (`ARCHITECTURE.md` conforme `A_Architecture/A_Method_PlantaTecnica.md`); se
  inexistente ou defasada, acionar `cross-stack-architect` +
  `project-documentation-architect` antes dos executores.
- Antes de implementar: `cetico` e, se relevante, `impact-validator`.
- Durante implementacao: `gsd-tdd-cli-auditor`.
- Mudancas de dados: `data-migrations` para schema, migrations e rollback.
- Mudancas de dependencias: `dependency-steward` para upgrades, CVEs e licencas.
- Superficies sensiveis: `security-validator`, `performance-validator`,
  `payments-marketplace`, `trust-safety`, `compliance-regulatory` e agentes
  regionais/de loja como `regional-platform-compliance` quando aplicaveis.
- Antes de fechar: `gsd-tdd-cli-auditor`, `test-engineer` quando houver lacunas
  de teste, e `final-validator`.
- Auditoria de processo: `process-guardian`.

## Metodo SDD

Use o metodo SDD do kit:

`State -> Spec -> Design -> Doubt -> Develop -> Demonstrate -> Document`

Arquivo canonico:

- `C10_Maestro/C10_Method_SDD.md`

Para transformar ideia, legado ou feature grande em specs executaveis, use:

- `SPEC_Specs/SPEC_Agent_SpecArchitect.md`
- wrapper Claude: `.claude/agents/spec-architect.md`

Para criar ou sincronizar documentacao completa do projeto, use:

- `DOC_Documentation/DOC_Agent_ProjectDocumentationArchitect.md`
- wrapper Claude: `.claude/agents/project-documentation-architect.md`

## Metodo Planta Tecnica

Todo repo/ambiente mantem `ARCHITECTURE.md` como planta tecnica derivada do
codigo (4 propriedades: especifica, derivada do codigo, verificavel, enxuta).
Mudanca estrutural atualiza a planta no mesmo ciclo. Arquivo canonico:

- `A_Architecture/A_Method_PlantaTecnica.md`

## Metodo Harness

Toda implementacao relevante precisa de prova executavel:

- comando;
- cwd;
- objetivo;
- exit code;
- resultado;
- falhas/warnings relevantes;
- lacunas.

Arquivo canonico:

- `SUP_Supervisor/SUP_Method_Harness.md`

Template:

- `T_Templates/T_Template_CLI_AUDIT.md`

## Politica De Organizacao

- Nao mova, renomeie ou reescreva os agentes originais para adequar ao Claude.
- Atualize wrappers em `.claude/agents/` apenas quando mudar o roteamento ou a
  descricao de acionamento.
- Atualize os agentes originais quando mudar regra, metodo, protocolo ou
  conteudo de dominio.
- Preserve a pasta `.codex/` como biblioteca principal e governanca da raiz
  geral.
- Use `RUNTIME_Bridge/RUNTIME.md` como mapa de compatibilidade quando precisar
  entender como Codex, Claude e skills se conectam.
- Depois de alterar wrappers ou agentes, rode:
  `python RUNTIME_Bridge/scripts/validate_arsenal.py`.
- `.codex/` deve estar sob git com remote no GitHub (o validador falha sem
  git). Edicao de agente so termina com commit + push. Copias em projetos sao
  checkouts do repositorio-template e sincronizam por `git pull`, nunca por
  copia manual. Se `.codex/` estiver fora de git, avise o usuario e trate como
  gargalo de governanca.
- Nao criar ambientes paralelos, duplicados ou temporarios sem decisao
  documentada.
- Nao mover codigo entre ambientes sem plano, impacto e validacao cross-stack.

## Comandos De Uso

Exemplos de pedidos ao Claude Code:

```text
Use the pick-agent-selector subagent to select the right team for this task.
```

```text
Use the gsd-tdd-cli-auditor subagent before and after this implementation.
```

```text
Use the final-validator subagent to review this diff before merge.
```

```text
Check RUNTIME_Bridge and validate that the Codex and Claude wrappers are still coherent.
```

## Observacao Para Projetos

Em um projeto real, este arquivo deve ficar na raiz do projeto como `CLAUDE.md`,
ao lado de `.claude/agents/`, `RUNTIME_Bridge/` e da pasta `.codex/`.
