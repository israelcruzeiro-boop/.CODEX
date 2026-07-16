# C10_Method_ProjectProfiles - Perfis De Engenharia

Este metodo impede o kit de aplicar gates web/backend a qualquer artefato e de
alegar cobertura universal. A fonte executavel e
`RUNTIME_Bridge/PROJECT_COVERAGE_MAP.toml`.

## Principios

1. Classifique o artefato antes de selecionar executor, testes, CI e release.
2. Um repositorio pode ter varios perfis; classifique por app/servico/pacote.
3. `OBSERVADO` significa cobertura direta: cada owner resolve no manifesto para
   uma fonte original e wrapper validos, a fonte aparece nas evidencias do
   perfil e existe um cenario machine-readable coerente com status/rota/limite.
4. `PARCIAL` exige limitacao explicita e fallback `@F` para a parte nao coberta.
5. `AUSENTE` exige `@F` antes de implementar; governanca generica nao vira expertise.
6. Nunca promova um status por confianca abstrata. Exija fonte, wrapper e cenario.
   Fallback e obrigatorio em `PARCIAL/AUSENTE` e vazio em `OBSERVADO`; a politica
   precisa ser explicita, nao necessariamente a lista preenchida em todo status.
7. Testes e release seguem o perfil real, nao um checklist web universal.

## Perfis Canonicos

| ID | Escopo | Owner principal |
|---|---|---|
| `WEB_FRONTEND` | UI/browser | `@D` |
| `API_BACKEND` | API e dominio server-side | `@B` |
| `WORKER_AUTOMATION` | workers, jobs, filas e automacoes | `@B`/`@O` |
| `MOBILE` | mobile nativo/hibrido | `@M`/`@IOS` |
| `DESKTOP` | aplicacao desktop | cobertura parcial + `@F` |
| `MONOREPO` | topologia multi-app/package e releases coordenadas | cobertura parcial + `@F` |
| `CLI_SDK_PACKAGE` | CLI, biblioteca, package e SDK | `@PKG` |
| `DATA_ENGINEERING` | ETL/ELT, batch/stream e data quality | `@DE` |
| `ML_ENGINEERING` | ML classico e MLOps | `@ML` |
| `INFRASTRUCTURE_AS_CODE` | state, plan/apply, drift e policy | `@IAC` |
| `AI_LLM` | LLM, prompts, RAG e evals | `@AI` |
| `EMBEDDED` | firmware/IoT | ausente + `@F` |
| `GAME` | engines/gameplay | ausente + `@F` |

## Descoberta

1. Localizar raiz, manifests, entrypoints, artefatos gerados e consumidores.
2. Preencher `T_Template_PROJECT_PROFILE.md` por unidade publicavel/operavel.
3. Consultar o coverage map e separar cobertura direta, parcial e ausente.
4. Acionar `@PICK` com os perfis e riscos, nao apenas com nomes de pastas.
5. Se uma necessidade nao estiver coberta em pelo menos 70%, acionar `@F`.

O limiar de 70% e calculado por capacidade, nao por confianca subjetiva. Liste
as capacidades necessarias com pesos que totalizem 100; marque cada uma como
`1` (fonte+contrato+gate comprovados), `0.5` (parcial com limite explicito) ou
`0` (ausente). A cobertura e `soma(peso * nota)`. Sem matriz e evidencia, o
resultado e desconhecido e nao pode justificar `OBSERVADO`.

## Teste Proporcional Por Perfil

- Web UI: unit/component, acessibilidade e browser E2E apenas em fluxo critico.
- API: unit/domain, contrato, integracao e carga quando o risco exigir.
- Worker/automacao: unidade, integracao do scheduler/fila, idempotencia, retry e recovery.
- Mobile/desktop: unit/integracao e smoke no runtime/device/installer aplicavel.
- Monorepo: affected graph, fronteiras de workspace, consumer contracts e release graph.
- CLI/package/SDK: golden/contract, consumer matrix e instalacao limpa.
- Data: schema/data-quality, idempotencia, replay/backfill e reconciliacao.
- ML: baseline reproduzivel, segmentos, serving, drift e rollback.
- IaC: format/validate, policy/security, plan sanitizado e recovery.
- LLM: schema/invariantes, golden-set, retrieval, fallback e custo.

Playwright, cobertura backend, device smoke, model eval e IaC plan nunca sao
gates universais. Cada um e obrigatorio apenas quando o perfil/risco o exigir.

## CI E Release

- Detectar GitHub Actions, GitLab CI, Azure Pipelines, Jenkins, Buildkite ou outro.
- Detectar canal: deploy, registry, binario, store, model registry, orchestrator ou apply.
- Promover apenas o artefato testado e preservar provenance/rastreabilidade.
- Separar deploy de app, publicacao de pacote, promocao de modelo e apply de IaC.
- Se nao houver release/operacao, registrar `N/A` com motivo verificavel.

## Gate De Cobertura

Antes de `READY_FOR_IMPLEMENTATION`, declarar:

- perfis por unidade e evidencias;
- fonte original, wrapper derivado do manifesto e cenario de rota por perfil;
- matriz ponderada de capacidades quando o gate de 70% for usado;
- owner executor e gates aplicaveis;
- testes e release especificos;
- limitacoes e fallback para `PARCIAL`/`AUSENTE`;
- validacao com `python RUNTIME_Bridge/scripts/validate_project_coverage.py`.

Veredito global: `APROVADO | APROVADO_COM_RESSALVAS | QUESTIONAR | REPROVADO`.
