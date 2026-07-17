# Regras Claude Code - Codex Agent Kit

Use este arquivo para gerar `PROJECT_ROOT/CLAUDE.md` quando um projeto for usar
Claude Code junto com o Codex Agent Kit.

## Objetivo

Adaptar o kit para Claude Code sem duplicar nem desorganizar os agentes
originais. Claude deve usar `.claude/agents/*.md` como camada de delegacao, mas
as regras completas continuam nos arquivos da pasta `.codex/`.

## Setup Recomendado No Projeto

```text
PROJECT_ROOT/
  AGENTS.md
  CLAUDE.md
  .claude/
    agents/
      pick-agent-selector.md
      gsd-tdd-cli-auditor.md
      ...
  .codex/
    AGENTS.md
    C10_Maestro/
    SUP_Supervisor/
    ...
  back/
  front/
  admin/
  mobile/
  infra/
  packages/
  docs/
```

Os nomes das pastas podem variar, mas `PROJECT_ROOT` deve ser tratado como a
raiz geral. `.codex/` e `.claude/` ficam na raiz e governam todos os ambientes,
apps, servicos, pacotes e docs abaixo dela.

## Governanca Multiambiente

Claude Code deve usar `.codex/` como fonte de autoridade transversal. Os
subagentes podem trabalhar em qualquer subpasta de `PROJECT_ROOT` quando a
tarefa exigir, mas precisam preservar:

- ownership de cada ambiente;
- contratos entre backend, frontend, admin, mobile, workers e pacotes;
- separacao de secrets e variaveis por ambiente;
- comandos de build, lint, test, typecheck e smoke de cada cwd afetado;
- documentacao de decisoes estruturais na raiz.

Nao criar pastas paralelas, duplicar apps ou mover codigo entre ambientes sem
plano, impacto, validacao e decisao documentada.

## Regras

1. Para tarefa complexa, começar por `pick-agent-selector`.
   Classificar tambem o artefato por
   `.codex/RUNTIME_Bridge/PROJECT_COVERAGE_MAP.toml`; perfil parcial/ausente
   exige limitacao e fallback explicitos.
2. Para qualquer implementacao, bugfix ou refatoracao comportamental, usar
   `gsd-tdd-cli-auditor`.
3. Para plano antes de codigo, usar `cetico` e `impact-validator` quando houver
   risco cross-stack.
4. Para superficie sensivel, usar os validadores especializados.
5. Antes de fechar, usar `final-validator`.
6. Para lacuna real sem agente, usar `agent-forge-foreman`.
7. Para duas ou mais frentes independentes, planejar DAG, ownership, contexto,
   joins e integracao conforme
   `.codex/SUP_Supervisor/SUP_Method_MultiAgentDelivery.md`.
8. Usar `package-cli-sdk`, `data-pipeline`, `ml-engineering` e
   `infrastructure-as-code` quando esses forem os artefatos principais.

Subagentes escritores nunca compartilham arquivos ao mesmo tempo. O agente
principal aguarda os joins obrigatorios, confronta resultados pela evidencia
primaria e revalida a integracao antes do veredito.

Validadores aplicaveis:

- `.codex/RUNTIME_Bridge/scripts/validate_multi_agent.py`
- `.codex/RUNTIME_Bridge/scripts/validate_cli_audit.py`
- `.codex/RUNTIME_Bridge/scripts/run_quality_gate.py`

## Fonte Da Verdade

Wrappers Claude apontam para a fonte original:

- `.codex/AGENTS.md`
- `.codex/C10_Maestro/C10_CAMISA10.md`
- `.codex/SUP_Supervisor/SUP_PICK_AgentSelector.md`
- `.codex/GSD_DeliveryDiscipline/GSD_Agent_TDDCLIAuditor.md`
- demais agentes de dominio conforme necessario.

Se wrapper e fonte original divergirem, atualizar a fonte original primeiro e o
wrapper depois.
