# CLAUDE.md - [NOME DO PROJETO]

Este projeto usa o Codex Agent Kit com compatibilidade para Claude Code.

Fonte-mestra:

- `.codex/AGENTS.md`
- `.codex/C10_Maestro/C10_CAMISA10.md`
- `.codex/SUP_Supervisor/SUP_PICK_AgentSelector.md`
- `.codex/GSD_DeliveryDiscipline/GSD_Agent_TDDCLIAuditor.md`

Subagentes Claude:

- `.claude/agents/*.md`

## Governanca Da Raiz Geral

Claude Code deve trabalhar a partir de `PROJECT_ROOT`, a raiz geral que contem
`.codex/`, `.claude/`, `AGENTS.md`, `CLAUDE.md` e os ambientes do produto, como
`back/`, `front/`, `admin/`, `mobile/`, `infra/`, `packages/` ou equivalentes.

Regra: `.codex/` governa o projeto inteiro. Os subagentes podem atuar dentro de
qualquer ambiente da raiz quando a tarefa exigir, mas devem preservar ownership,
contratos, comandos locais e organizacao global.

Antes de editar uma subpasta:

- mapear qual ambiente sera afetado;
- verificar consumidores em outros ambientes;
- respeitar contratos compartilhados;
- rodar validacoes nos cwd relevantes;
- registrar lacunas no Harness CLI.

Mudancas que cruzam ambientes sao cross-stack e devem envolver arquitetura,
Harness, QA e validacao final proporcional ao risco.

## Regra De Entrada

Para tarefas complexas, ambiguas, multi-area, de implementacao, refatoracao,
bugfix, auditoria, release ou risco medio/alto, use primeiro:

```text
pick-agent-selector
```

Ele seleciona o time certo, ordem de agentes, gates necessarios e lacunas.

## Gates Obrigatorios

- Plano antes de codigo: `cetico` e, quando relevante, `impact-validator`.
- Toda implementacao, bugfix ou refatoracao comportamental: `gsd-tdd-cli-auditor`.
- Seguranca: `security-validator`.
- Performance: `performance-validator`.
- Testes: `test-engineer`.
- Selo final: `final-validator`.
- Processo: `process-guardian`.

## SDD

Siga:

`State -> Spec -> Design -> Doubt -> Develop -> Demonstrate -> Document`

## Harness CLI

Toda entrega relevante deve registrar:

- comando;
- cwd;
- objetivo;
- exit code;
- resultado;
- falhas/warnings relevantes;
- lacunas.

## Organizacao

- `.codex/` contem os agentes originais e metodos.
- `.claude/agents/` contem wrappers para Claude Code.
- Nao mova ou duplique a logica dos agentes originais nos wrappers.
- Nao criar pastas paralelas como `frontend2`, `backend-new` ou `app-final` sem
  decisao documentada.
- Nao tratar `back`, `front`, `admin` ou `mobile` como ilhas quando houver
  contratos entre eles.
