# Codex Agent Kit - Catalogo Mestre

Este arquivo e o ponto de entrada da pasta `.codex/`. Use-o como catalogo e como contrato minimo de qualidade para qualquer projeto que receba este kit.

Importante: para o Codex carregar instrucoes automaticamente ao trabalhar na raiz do projeto, copie ou adapte `C10_Maestro/C10_Agent_ProjectRules.md` para `PROJECT_ROOT/AGENTS.md`. A pasta `.codex/` funciona como biblioteca de agentes, templates, validadores e camada de governanca da raiz geral do projeto.

## Governanca Da Raiz Geral

Este arsenal deve operar a partir de `PROJECT_ROOT`, a raiz geral do produto. Essa
raiz pode conter varios ambientes, apps e servicos, por exemplo:

```text
PROJECT_ROOT/
  .codex/
  AGENTS.md
  CLAUDE.md
  back/
  front/
  admin/
  mobile/
  infra/
  packages/
  docs/
```

Regra: `.codex/` governa o projeto inteiro, nao apenas uma subpasta. Todos os
agentes tem autoridade operacional para ler, planejar, editar e validar arquivos
em qualquer ambiente dentro de `PROJECT_ROOT`, desde que respeitem escopo,
contratos, evidencias, credenciais, seguranca e validacoes do kit.

Regra de versionamento do arsenal: a pasta `.codex/` DEVE estar sob git, com
remote no GitHub. A fonte da verdade e o repositorio-template do kit; copias em
projetos sao checkouts desse repositorio e sincronizam por `git pull`, nunca
por copia manual. Toda edicao de agente/metodo/wrapper termina com commit (e
push quando houver remote). Se qualquer agente detectar `.codex/` fora de git,
deve avisar o usuario e tratar como gargalo de governanca antes de prosseguir
com mudancas no arsenal - `validate_arsenal.py` falha nessa condicao. Agentes
especificos de um projeto (fora do template) vivem no proprio repositorio do
projeto ou em branch dedicada, nunca soltos e nao rastreados.

Depois do checkout ou `git pull`, materialize e confira os adapters de runtime
com `python .codex/RUNTIME_Bridge/scripts/install_project_runtime.py --project-root .`
e o respectivo `--check`, executados a partir de `PROJECT_ROOT`. O instalador e a unica ponte suportada
para projetar wrappers em `PROJECT_ROOT/.codex/agents`, wrappers Claude em
`PROJECT_ROOT/.claude/agents` e skills descobertas pelo Codex em
`PROJECT_ROOT/.agents/skills`; nao copie esses arquivos manualmente.

Antes de qualquer mudanca, o agente deve identificar:

- qual e a raiz geral (`PROJECT_ROOT`);
- quais subpastas sao apps, servicos, pacotes compartilhados, infra, docs ou
  automacoes;
- quais contratos existem entre `back`, `front`, `admin`, `mobile`, workers,
  banco e terceiros;
- quais comandos de validacao pertencem a cada ambiente afetado;
- quais arquivos sao fonte de verdade na raiz e quais pertencem a um ambiente
  especifico.

Ao trabalhar em um ambiente especifico, o agente nao pode desorganizar a raiz:

- nao criar pastas paralelas como `frontend2`, `backend-new`, `app-final` sem
  decisao documentada;
- nao mover codigo entre ambientes sem plano de migracao e impacto cross-stack;
- nao duplicar contratos, tipos, schemas, envs ou logica compartilhada sem
  justificar ownership;
- nao tratar `front`, `admin`, `mobile` ou `back` como projetos isolados quando
  houver contrato comum;
- nao alterar configuracao global da raiz sem avaliar efeito nos ambientes
  consumidores.

Quando houver duvida sobre ownership, acionar `@A`, `@C`, `@GSD` e o agente
especialista do ambiente afetado antes de implementar.

Compatibilidade Claude Code: este kit tambem inclui `CLAUDE.md` e wrappers em
`.claude/agents/`. Eles nao substituem os agentes originais; apenas permitem que
Claude Code delegue tarefas aos mesmos papeis usando o formato de subagentes.

## Padrao de Nomenclatura

Todo agente deve usar o prefixo semantico no nome da pasta e do arquivo:

| Prefixo | Area | Exemplo |
|---|---|---|
| `C10_` | Maestro, orquestracao e memoria do projeto | `C10_Maestro/C10_CAMISA10.md` |
| `A_` | Arquitetura cross-stack | `A_Architecture/A_Agent_CrossStackArchitect.md` |
| `AI_` | Integracao de IA/LLM em producao: prompts, RAG, evals, custo e guardrails | `AI_AIIntegration/AI_Agent_AIIntegrationArchitect.md` |
| `B_` | Backend, API e dominio | `B_BackendDomain/B_Agent_BackendDomain.md` |
| `BI_` | Business Intelligence, metricas e dashboards | `BI_Dashboards/BI_Agent_DashboardDesigner.md` |
| `BUG_` | Debug cirurgico full-stack | `BUG_Debugger/BUG_Agent_Debugger.md` |
| `C_` | Cetico cirurgico e revisao de planos | `C_Cetico/C_Agent_Cetico.md` |
| `D_` | Design, UX, frontend visual e replicacao fiel de layout | `D_Design/D_Agent_Design.md`, `D_Design/D_Agent_LayoutReplicator.md` |
| `DATA_` | Banco de dados, migrations, integridade e modelagem de dados | `DATA_Database/DATA_Agent_DataMigrations.md` |
| `DE_` | Engenharia de dados, ETL/ELT, lineage, replay e data quality | `DE_DataEngineering/DE_Agent_DataPipeline.md` |
| `DEP_` | Dependencias, supply-chain, upgrades, CVEs e licencas | `DEP_Dependencies/DEP_Agent_DependencySteward.md` |
| `DOC_` | Documentacao estrutural do projeto, progresso e handoff | `DOC_Documentation/DOC_Agent_ProjectDocumentationArchitect.md` |
| `E_` | Environment, secrets, deploy vars e paridade de ambientes | `E_Environment/E_Agent_Environment.md`, `E_Environment/E_Agent_DigitalOceanEnvironment.md` |
| `F_` | Fabrica de agentes sob demanda | `F_AgentForge/F_Agent_Foreman.md` |
| `GEO_` | Localizacao, enderecos, raio e proximidade | `GEO_Location/GEO_Agent_Location.md` |
| `GOV_` | Compliance geral, privacidade e regulacao | `GOV_Compliance/GOV_Agent_ComplianceRegulatory.md` |
| `GSD_` | Delivery discipline, TDD e auditoria CLI | `GSD_DeliveryDiscipline/GSD_Agent_TDDCLIAuditor.md` |
| `I18N_` | Localizacao, ingles de produto e UX writing | `I18N_LocalizationUX/I18N_Agent_LocalizationUX.md` |
| `IAC_` | Infrastructure as Code, state, drift, policy e apply seguro | `IAC_PlatformEngineering/IAC_Agent_InfrastructureAsCode.md` |
| `IOS_` | iOS nativo, Apple platforms e App Store approval | `IOS_AppleAppstore/IOS_Agent_AppleNativeAppstore.md` |
| `M_` | Mobile, apps nativos/hibridos, lojas e release | `M_MobilePlaystore/M_Agent_MobilePlaystore.md` |
| `MKT_` | Marketing, SEO, landing pages, persona, copy, conversao e validacao MKT | `MKT_Marketing/MKT_Agent_SEOGrowthStrategist.md`, `MKT_Marketing/MKT_Agent_MarketingSEOValidator.toml` |
| `ML_` | ML classico e MLOps: datasets, treino, registry, serving e drift | `ML_MLEngineering/ML_Agent_MLEngineering.md` |
| `MOD_` | Trust & Safety, denuncias e moderacao | `MOD_TrustSafety/MOD_Agent_TrustSafety.md` |
| `O_` | Observabilidade, deploy e operacao | `O_Observability/O_Agent_DeployObservability.md` |
| `ONB_` | Onboarding e pontape inicial: guia a pessoa por fase e proximo passo | `ONB_Onboarding/ONB_Agent_ProjectOnboardingGuide.md` |
| `P_` | Performance e escalabilidade | `P_Performance/P_Agent_PerformanceValidator.toml` |
| `PAY_` | Pagamentos, marketplace e monetizacao | `PAY_PaymentsMarketplace/PAY_Agent_PaymentsMarketplace.md` |
| `PKG_` | Packages, bibliotecas, CLI e SDK: contratos, compatibilidade e publicacao | `PKG_PackageSDK/PKG_Agent_PackageCLISDK.md` |
| `PR_` | Prompt engineering, briefing e refinamento de pedidos | `PR_PromptOps/PR_Agent_PromptRefiner_v2.md` |
| `Q_` | QA, testes e confiabilidade | `Q_Quality/Q_Agent_TestEngineer.md` |
| `S_` | Seguranca | `S_Seguranca/S_Agent_SecurityValidator.toml` |
| `SPEC_` | Specs SDD, produto e handoff Codex/Claude | `SPEC_Specs/SPEC_Agent_SpecArchitect.md` |
| `SUP_` | Supervisao, selecao de agentes, riscos, padroes e ambientes | `SUP_Supervisor/SUP_INTEGRATION_GUIDE.md` |
| `T_` | Templates reutilizaveis | `T_Templates/T_Template_PROJECT.md` |
| `REG_` | Compliance por regiao/pais e por plataforma/loja | `REG_RegionalCompliance/REG_Agent_RegionalCompliance.md` |
| `REL_` | Release, versionamento, changelog e gate de release | `REL_Release/REL_Agent_ReleaseManager.md` |
| `V_` | Validacao de impacto e selo final | `V_Validation/V_Agent_ImpactValidator.toml` |

Regra: nomes de pasta e arquivo devem evitar acentos e espacos para funcionar bem em Windows, Linux, CI/CD, scripts e automacoes.

## Pipeline Recomendado

0. `ONB_Onboarding/ONB_Agent_ProjectOnboardingGuide.md`: porta de entrada da pessoa. Descobre se o projeto e novo ou em andamento, posiciona fase/gargalos/alinhamento e encaminha ao agente certo. Quando o usuario pedir fundacao completa, usar o **Modo Kickoff Completo** para gerar briefings iniciais para `@DOC`, `@SPEC` e `@C10`. Opcional quando o pedido ja e uma tarefa clara.
1. `SUP_Supervisor/SUP_PICK_AgentSelector.md`: identifica o perfil do artefato,
consulta `PROJECT_COVERAGE_MAP.toml`, seleciona o time certo e encaminha para
`@F` quando a cobertura comprovada ficar abaixo de 70%.
1b. `skills/multi-agent-delivery`: quando houver dois ou mais workstreams
independentes, cria DAG, ownership, pacotes de contexto, fan-out e fan-in.
2. `SUP_Supervisor/SUP_CRED_AccessGatekeeper.md`: entra antes de qualquer acesso externo, API, banco, navegador, deploy ou producao.
3. `C10_Maestro`: entende o projeto, define fase, monta brief e coordena.
4. `SPEC_Specs/SPEC_Agent_SpecArchitect.md`: transforma ideia/legado em Pacote de Specs SDD antes de arquitetura e execucao.
5. `DOC_Documentation/DOC_Agent_ProjectDocumentationArchitect.md`: cria/sincroniza documentacao estrutural quando projeto, progresso, agentes, design ou handoff estiverem incompletos.
6. `A_Architecture`: valida desenho desacoplado, contratos, fronteiras e riscos antes de codar.
7. `C_Cetico`: revisa plano contra codigo real antes da implementacao.
8. `V_Validation/impact_validator`: revisa plano e impacto cross-stack.
8b. `MKT_Marketing/MKT_Agent_MarketingSEOValidator.toml`: entra desde a
primeira validacao quando o perfil tocar site, landing page, campanha, SEO,
copy, oferta comercial, persona, schema, CTA ou medicao; valida de novo antes
de entrega/deploy/campanha.
9. `GSD_DeliveryDiscipline/GSD_Agent_TDDCLIAuditor.md`: transforma o plano em criterio de aceite, TDD proporcional e Harness CLI.
10. `S_Seguranca/security_validator`: entra quando tocar auth, PII, secrets, upload, headers, permissoes ou pagamentos.
11. `P_Performance/performance_validator`: entra quando tocar hot path, cache, queries, listas grandes, imagens, filas, concorrencia ou custo.
12. `DEP_Dependencies`: garante lockfiles, audit/SCA, Dependabot e higiene de supply-chain antes de aprovar dependencias.
13. Agente executor especializado, escolhido pelo perfil real: `B_BackendDomain`, `DATA_Database`, `DE_DataEngineering`, `D_Design`, `E_Environment`, `IAC_PlatformEngineering`, `MKT_Marketing`, `ML_MLEngineering`, `PKG_PackageSDK`, `GEO_Location`, `I18N_LocalizationUX`, `IOS_AppleAppstore`, `M_MobilePlaystore`, `MOD_TrustSafety`, `PAY_PaymentsMarketplace`, `BI_Dashboards`, `BUG_Debugger`, etc.
14. `GSD_DeliveryDiscipline/GSD_Agent_TDDCLIAuditor.md`: audita comandos reais, bug sweep e lacunas antes de QA/final.
15. `Q_Quality`: seleciona e implementa testes proporcionais ao artefato e ao risco: unitarios, contrato/consumidor, integracao, sistema, UI ou hardware quando aplicavel.
16. `O_Observability`: implementa ou ajusta a pipeline CI/CD observada no projeto, sem impor GitHub Actions quando outro provedor for a fonte real.
17. `SUP_Supervisor/SUP_STD_StandardsEnforcer.md` e `SUP_Supervisor/SUP_FLOW_DeliveryInspector.md`: verificam padrao e ordem quando necessario.
18. `V_Validation/final_validator`: revisa diff final antes de merge/deploy.
19. `REL_Release/REL_Agent_ReleaseManager.md`: define versao, changelog, gate de release e ordem de migration/deploy quando a entrega vira uma release.
20. `SUP_Supervisor/SUP_X_ProcessGuardian.md`: entra em modo FOCUSED para entregas relevantes ou FULL em auditorias.
21. `C10_DOCUMENTADOR`: registra LOG, STATUS, ADRs e aprendizados.

## Metodos Canonicos

- SDD oficial do kit: `C10_Maestro/C10_Method_SDD.md`.
- Harness oficial do kit: `SUP_Supervisor/SUP_Method_Harness.md`.
- Planta AS-IS oficial do kit: `A_Architecture/A_Method_PlantaTecnica.md`
  (`ARCHITECTURE.md` por repo, sempre derivado do codigo). Para sistemas novos
  ou mudancas futuras, nenhum executor implementa sem `TARGET_ARCHITECTURE.md`
  rastreavel conforme `A_Method_ModularArchitecture.md`.
- Arquitetura modular oficial: `A_Architecture/A_Method_ModularArchitecture.md`
  (catalogo de modulos, dependencias, contratos, consistencia e fitness gates).
- Mapa de padroes oficial: `A_Architecture/A_Method_PatternMap.md` (padroes
  observados/propostos/aprovados/depreciados/proibidos, sempre com evidencia e gate).
- Catalogo contextual de patterns: `A_Architecture/A_Reference_PatternCatalog.md`;
  e referencia neutra, nunca aprovacao global.
- Perfis de projeto oficiais: `C10_Maestro/C10_Method_ProjectProfiles.md` e
  `T_Templates/T_Template_PROJECT_PROFILE.md`.
- Mapa verificavel de cobertura: `RUNTIME_Bridge/PROJECT_COVERAGE_MAP.toml`;
  perfil parcial/ausente exige limitacao e fallback explicitos.
- Estrategia de cache oficial do kit: `P_Performance/P_Method_CacheStrategy.md` (camadas, chaves, TTL, invalidacao, stampede; executor desenha, `@P`/`@S` validam).
- Entrega multiagente oficial: `SUP_Supervisor/SUP_Method_MultiAgentDelivery.md`
  (DAG, contexto minimo, write-set, join, evidence ledger e integracao).
- Template de especificacao: `T_Templates/T_Template_SPEC.md`.
- Template de auditoria CLI: `T_Templates/T_Template_CLI_AUDIT.md`.
- Template Claude Code: `T_Templates/T_Template_CLAUDE.md`.
- Estrategia de skills: `C10_Maestro/C10_Skill_Strategy.md`.
- Runtime bridge Codex/Claude/Hermes-style: `RUNTIME_Bridge/RUNTIME.md`.
- Gate integrado do arsenal: `RUNTIME_Bridge/scripts/run_quality_gate.py`.
- Validadores multiagente e Harness: `RUNTIME_Bridge/scripts/validate_multi_agent.py`
  e `RUNTIME_Bridge/scripts/validate_cli_audit.py`.
- Manifesto de compatibilidade runtime: `RUNTIME_Bridge/AGENT_RUNTIME_MAP.toml`.
- Validador local do arsenal: `RUNTIME_Bridge/scripts/validate_arsenal.py`.
- Validador semantico de specs: `RUNTIME_Bridge/scripts/validate_specs.py`.
- Validador semantico de arquitetura e patterns:
  `RUNTIME_Bridge/scripts/validate_architecture.py`.
- Agente de specs SDD: `SPEC_Specs/SPEC_Agent_SpecArchitect.md`.
- Agente de documentacao estrutural: `DOC_Documentation/DOC_Agent_ProjectDocumentationArchitect.md`.
- Templates de documentacao estrutural: `DOC_Documentation/DOC_Template_*.md`.

## Runtime Bridge E Skills

Este kit agora possui uma camada de runtime dentro de `RUNTIME_Bridge/`.
Ela nao substitui agentes originais; apenas valida e conecta:

- `.codex/agents/*.toml`: fontes canonicas dos wrappers Codex dentro do kit;
  o instalador as projeta em `PROJECT_ROOT/.codex/agents`.
- `.claude/agents/*.md`: fontes canonicas dos wrappers Claude; o instalador as
  projeta em `PROJECT_ROOT/.claude/agents`.
- `skills/*/SKILL.md`: fontes canonicas dos workflows compactos; o instalador
  as projeta em `PROJECT_ROOT/.agents/skills`, local de descoberta repo-scoped
  do Codex.
- `RUNTIME_Bridge/scripts/validate_arsenal.py`: checagem de coerencia.

Skills oficiais locais:

- `skills/codex-agent-kit`: selecao, governanca e coordenacao do arsenal.
- `skills/gsd-tdd-cli-harness`: TDD proporcional, Harness CLI e prova.
- `skills/agent-forge`: criacao, evolucao e promocao de agentes.
- `skills/architecture-blueprint`: arquitetura AS-IS/TO-BE, modularidade e pattern map.
- `skills/spec-driven-breakdown`: specs granulares com IDs e rastreabilidade.
- `skills/multi-agent-delivery`: execucao paralela controlada e protecao de contexto.

Os contratos de trigger, boundary e non-trigger das seis skills vivem em
`RUNTIME_Bridge/evals/skills/cases.toml` e sao verificados por
`RUNTIME_Bridge/scripts/run_skill_contract_evals.py`. Essa verificacao
deterministica nao substitui forward-test isolado quando o comportamento mudar.

Regra: nao criar uma skill por agente. Promova para skill apenas workflows
recorrentes, enxutos e acionaveis. Os agentes `.md` continuam sendo a fonte
de verdade.

Para validar compatibilidade depois de qualquer mudanca em wrappers, skills ou
agentes promovidos:

```powershell
python RUNTIME_Bridge/scripts/run_quality_gate.py
```

## Compatibilidade Claude Code

- `CLAUDE.md`: adaptador para usar este arsenal no Claude Code.
- `.claude/agents/*.md`: wrappers de subagentes Claude. Cada wrapper aponta
  para um agente original como fonte da verdade.
- `C10_Maestro/C10_Agent_ClaudeProjectRules.md`: guia para gerar `CLAUDE.md`
  em projetos reais.
- `RUNTIME_Bridge/scripts/sync_claude_from_codex.py`: regenera wrappers Claude
  a partir dos wrappers Codex quando a metadata estruturada mudar.
- `RUNTIME_Bridge/scripts/install_project_runtime.py`: projeta wrappers, skills
  e adapters no `PROJECT_ROOT` sem sobrescrever customizacoes.

Regra: mantenha `.codex/` como fonte principal. Atualize wrappers Claude apenas
quando mudar o nome, descricao ou roteamento de acionamento.

## Regras Globais Extraidas do Guia Vibe Coding

Todo agente desta pasta deve proteger a base oculta do iceberg, nao apenas a ponta visual do MVP.

- Projetar para sistemas desacoplados: frontend, backend e banco com contratos claros.
- Nunca dar acesso de escrita/exclusao em banco de producao para agente autonomo.
- Separar ambientes local, homologacao/staging e producao.
- Tratar entrada externa como nao confiavel: validar, sanitizar e autorizar.
- Usar idempotencia em acoes criticas, especialmente pagamentos, webhooks, filas e retries.
- Aplicar deduplicacao contra duplo clique, reenvio de formulario e eventos repetidos.
- Usar operacoes atomicas/transacoes quando uma mudanca depende de varias etapas.
- Implementar retry com exponential backoff, limite de tentativas e timeout.
- Prevenir race conditions com locks, constraints, transacoes ou filas quando houver concorrencia.
- Paginar listas e logs; nunca carregar tudo por padrao.
- Medir antes de otimizar quando possivel; otimizar hot paths, nao preferencias esteticas.
- Incluir observabilidade: logs estruturados, metricas, traces e alertas para fluxos criticos.
- Rodar validacoes possiveis antes de fechar: build, lint, typecheck, testes e smoke test.
- Aplicar SDD em toda entrega relevante: State, Spec, Design, Doubt, Develop, Demonstrate, Document.
- Todo backend com ecossistema que suporte lockfile deve manter seu lockfile correto versionado; manifesto alterado sem lockfile correspondente e divergente bloqueia merge.
- Todo projeto deve executar audit de dependencias no ciclo de CI e em mudancas de dependencias; findings bloqueantes exigem correcao ou excecao rastreavel.
- Audit de dependencias nao substitui varredura de secrets: o pipeline e `@S` devem tratar vazamento de credenciais como gate independente.
- Todo repositorio GitHub deve avaliar/ajustar `.github/dependabot.yml` aos ecossistemas e diretorios reais; nao copiar configuracao generica sem adequacao.
- Testes sao obrigatorios de forma proporcional ao perfil, ao risco e ao comportamento afetado. Metas de cobertura precisam ser declaradas pelo projeto; 100% so e gate quando houver justificativa e contrato explicito.
- APIs, eventos, CLIs, SDKs, packages, pipelines e modelos cobrem seus contratos e consumidores afetados. Teste end-to-end de UI usa a ferramenta observada no projeto; Playwright e condicional a uma UI web que o adote, nunca requisito universal.
- Erros relevantes devem gerar logs estruturados, correlacionaveis e seguros; logs nunca podem vazar secrets ou PII indevida.
- A arquitetura deve declarar dominios de problema, ownership e contratos entre dominios antes de expandir modulos relevantes.
- Aplicar Harness CLI em toda implementacao, bugfix ou refatoracao com risco comportamental.
- Em entrega multiagente, definir DAG, dependencias, read-set/write-set,
  fingerprint, join e integrador antes do primeiro spawn; write-set paralelo
  nunca sobrepoe read-set ou write-set concorrente sem snapshot/worktree imutavel.
- Ao final de cada ciclo relevante, atualizar `STATUS.md` geral e o status/progresso
  de cada ambiente afetado (`back`, `front`, `admin`, `mobile`, `infra`,
  `packages` ou equivalentes), alem de registrar LOG, decisoes e lacunas.
- Toda migration de banco deve estar em um diretório canônico declarado no
  projeto, versionado e rastreavel, para permitir replicacao do banco em outro
  ambiente sem depender de historico de chat ou arquivos soltos.
- Nunca declarar "sem bugs" quando houver lacunas nao verificadas; declarar a lacuna e baixar o veredito.

## Gate De Saude Sistemica

Toda spec, plano ou implementacao relevante deve declarar impacto em cada eixo abaixo.
Quando um eixo nao se aplicar, registrar `N/A` com motivo. Quando houver impacto,
acionar o agente responsavel antes do selo final.

| Eixo | Pergunta minima | Agente natural |
|---|---|---|
| Arquitetura | AS-IS/TO-BE, fronteiras, modulos, ownership, dependencias, contratos, pattern map e gates estao claros? | `@A` |
| Backend/dominio | Regra critica esta no backend/servico certo, nao so na UI? | `@B` |
| Dados | Schema, migration, constraint, indice, integridade e rollback estao definidos? | `@DATA` / `@B` / `@A` |
| Engenharia de dados | Lineage, watermark, replay, idempotencia, data quality e SLA do pipeline estao definidos? | `@DE` / `@DATA` / `@O` |
| Seguranca | Auth, roles, PII, secrets, uploads, webhooks e logs estao protegidos? | `@S` |
| Performance | Hot paths, listas, queries, cache, concorrencia e custo foram avaliados? | `@P` |
| Observabilidade | Logs, metricas, traces, alertas e health checks existem para fluxos criticos? | `@O` |
| Testes | Os testes adequados ao perfil, contratos, consumidores e risco estao cobertos? | `@GSD` / `@Q` |
| Operacao | CI/CD observada, ambientes, deploy/distribuicao, rollback, migrations e smoke estao planejados? | `@E` / `@O` / `@REL` |
| Dependencias | Lockfile, audit/SCA, Dependabot, CVEs e licencas estao sob controle? | `@DEP` / `@S` |
| Packages/CLI/SDK | API/ABI, exit codes, stdout/stderr, matriz de versoes, packaging, publicacao e consumer tests estao definidos? | `@PKG` / `@DEP` / `@REL` |
| IaC/plataforma | State, plan/apply, drift, policy-as-code, teardown e rollback de infra estao controlados? | `@IAC` / `@E` / `@O` / `@S` |
| Produto/UX | Estados vazios, erros, permissoes, acessibilidade e copy foram considerados? | `@D` / `@I18N` |
| Marketing/SEO | Persona, intencao de busca, conteudo util, on-page SEO, conversao, prova e medicao estao claros? | `@MKT` / `@MKT:persona` / `@MKT:validator` / `@BI` / `@D` |
| IA/LLM | Prompts versionados, evals, custo de tokens, fallback e dados enviados a provedores estao sob controle? | `@AI` |
| ML/MLOps | Dataset, leakage, treino, metricas, registry, serving, drift e retraining estao sob controle? | `@ML` / `@DATA` / `@O` |
| Compliance | Ha requisito legal, loja, pagamento, dado sensivel ou setor regulado? | `@GOV` / `@REG` / `@PAY` / `@S` |
| Documentacao | Decisoes, status, handoff e aprendizados serao registrados? | `@DOC` / `C10_DOCUMENTADOR` |

Regra: uma feature com risco ALTO ou CRITICO nao pode chegar a `@V` sem evidencias
de `@A`, `@GSD`, `@Q` e dos validadores especializados aplicaveis (`@S`, `@P`,
`@O`, `@PAY`, etc.).

## Politica de Execucao no Codex

- Antes de editar: ler arquivos completos relevantes, mapear dependencias e proteger mudancas do usuario.
- Antes de dar veredito: separar fato observado, inferencia e lacuna. Vereditos tecnicos precisam citar arquivos, simbolos, linhas ou comandos que sustentam a conclusao.
- Nenhum agente deve aprovar plano, diff, arquitetura, seguranca, performance ou release apenas por padrao generico. Se faltam arquivos ou contexto, o veredito correto e `QUESTIONAR`.
- Durante a implementacao: escopo pequeno, sem refatoracao lateral e sem dependencias pesadas sem justificativa.
- Depois de editar: validar com comandos reais do projeto quando existirem.
- Depois de implementar: registrar comandos, cwd, exit code, resultado e lacunas no formato Harness.
- Ao encontrar erro preexistente: documentar claramente, sem mascarar como sucesso.
- Ao tocar secrets: nunca imprimir valores, nunca criar `NEXT_PUBLIC_` com segredo, nunca hardcodar credencial.

## Padrao Anti-Alucinacao

Todo agente cirurgico deve trabalhar com esta cadeia:

1. Ler contexto do projeto.
2. Localizar arquivos e fluxos afetados.
3. Ler codigo real antes de opinar.
4. Rastrear consumidores e contratos.
5. Confrontar proposta contra evidencia.
6. Declarar lacunas explicitamente.
7. Emitir veredito proporcional ao que foi comprovado.

## Como Mencionar

Use o prefixo para marcar rapido no chat:

- `@ONB` para onboarding, pontape inicial e proximo passo do projeto (porta de entrada da pessoa).
- `@C10` para orquestrar.
- `@A` para arquitetura.
- `@AI` para IA/LLM em producao: prompts de produto, RAG, evals, custo de tokens, guardrails e dados enviados a provedores.
- `@B` para backend, API e dominio.
- `@BI` para dashboards, metricas e business intelligence.
- `@BUG` para debug cirurgico full-stack.
- `@C` para revisao cetica de planos.
- `@D` para design/frontend visual.
- `@DATA` para banco de dados, migrations, integridade e isolamento multi-tenant.
- `@DE` para ETL/ELT, pipelines de dados, lineage, replay, qualidade e SLAs.
- `@DEP` para dependencias, supply-chain, upgrades, CVEs e licencas.
- `@DOC` para documentacao estrutural: progresso, status, agents, Claude, design, arquitetura, contratos e handoff.
- `@E` para environment, secrets, deploy vars e paridade de ambientes.
- `@F` para criar agente sob demanda com AgentForge, apenas quando a lacuna for recorrente real e nenhum agente atual cobrir pelo menos 70% do dominio.
- `@GEO` para localizacao, enderecos, raio e proximidade.
- `@GOV` para compliance geral, privacidade, retencao, consentimento e regulacao.
- `@GSD` para GSD, TDD proporcional, Harness CLI e auditoria de bug antes de fechar implementacao.
- `@I18N` para i18n, ingles de produto e UX writing.
- `@IAC` para Infrastructure as Code, state, plan/apply, drift, policy e teardown seguro.
- `@IOS` para iOS nativo, Apple platforms, TestFlight e App Store approval.
- `@M` para mobile, apps nativos/hibridos, lojas e release.
- `@MKT` para marketing, SEO, sites, landing pages, persona, copy, conversao e crescimento organico; use `@MKT:persona` para mensagem/persona, `@MKT:supermercado` para cliente oculto em supermercados e `@MKT:validator` desde a primeira validacao e antes de deploy ou campanha.
- `@ML` para ML classico/MLOps; `@AI` continua dono de LLM, prompts, RAG e evals generativos.
- `@MOD` para trust & safety, denuncias e moderacao.
- `@P` para performance.
- `@PAY` para pagamentos, marketplace e monetizacao.
- `@PKG` para packages, bibliotecas, CLI e SDK, incluindo compatibilidade, packaging, publicacao e consumer tests.
- `@PR` para transformar ideias em prompts cirurgicos.
- `@Q` para testes.
- `@REL` para release, versionamento, changelog e gate de release.
- `@S` para seguranca.
- `@SPEC` para transformar ideias, legados e features grandes em Pacotes de Specs SDD.
- `@REG` para compliance por regiao/pais e por plataforma/loja (App Store, Play Store, marketplaces) quando o projeto publicar em um mercado especifico.
- `@V` para validacao de impacto/final.

Aliases internos da camada `SUP_`:

- `@PICK` para selecao de agentes.
- `@X` para auditoria geral de processo.
- `@R` para analise de riscos.
- `@FLOW` para inspecao de fluxo de entrega.
- `@STD` para fiscalizacao de padroes.
- `@ENV` para radar de ambientes.
- `@CRED` para validacao de credenciais e acesso.
