# Guia Completo do Codex Agent Kit

Atualizado em: 2026-05-30  
Base: `C:\Users\israe\Downloads\.codex`

Este guia e o manual humano do arsenal `.codex/`. Ele explica o que cada
agente faz hoje, quando acionar cada parte do kit e como manter uma entrega com
evidencia, escopo e memoria operacional.

Para operacao automatica dentro de um projeto, a fonte curta e `AGENTS.md`. Para
instalar o kit em um produto real, copie ou adapte
`C10_Maestro/C10_Agent_ProjectRules.md` para `PROJECT_ROOT/AGENTS.md`.

## Ideia Central

O Codex Agent Kit nao e uma colecao solta de prompts. Ele e uma camada de
governanca para projetos de software, com:

- roteamento inteligente de agentes;
- SDD, specs e documentacao estrutural;
- arquitetura cross-stack e revisao cetica;
- backend, banco, frontend, mobile, iOS, ambientes, observabilidade e release;
- seguranca, performance, QA, dependencias e compliance;
- pagamentos, BI, geolocalizacao, i18n, trust & safety e debug;
- fabrica de agentes sob demanda;
- compatibilidade com Claude Code por wrappers dedicados.

A regra principal e simples: ler o contexto real, ativar o especialista certo,
provar com comandos quando houver implementacao e registrar o que mudou.

## Raiz Geral Do Projeto

O kit deve operar a partir de `PROJECT_ROOT`, a raiz geral do produto, nao de uma
subpasta isolada. Um projeto tipico pode ter:

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

Antes de qualquer mudanca relevante, o agente deve identificar:

- qual e a raiz geral do produto;
- quais pastas sao apps, servicos, pacotes, infra, docs ou automacoes;
- quais contratos conectam frontend, backend, banco, mobile, workers e terceiros;
- quais comandos validam cada ambiente afetado;
- quais arquivos sao fonte de verdade global e quais pertencem a um ambiente.

O kit evita bagunca estrutural: nao cria `frontend2`, `backend-new` ou
`app-final` sem decisao documentada; nao duplica schemas, tipos, envs ou logica
compartilhada sem ownership claro; nao trata `front`, `admin`, `mobile` e `back`
como projetos isolados quando existe contrato comum.

## Resposta Direta: Quem Ativa O Necessario?

O roteador principal e:

- `SUP_Supervisor/SUP_PICK_AgentSelector.md`
- Alias: `@PICK`
- Funcao: analisar o pedido, escolher o time certo de agentes, definir ordem de
  acionamento, remover excesso e detectar lacunas.

Quando o pedido ainda esta no comeco do projeto ou a pessoa nao sabe o proximo
passo, comece por:

- `ONB_Onboarding/ONB_Agent_ProjectOnboardingGuide.md`
- Alias: `@ONB`
- Funcao: descobrir se o projeto e novo ou em andamento, posicionar fase,
  gargalos e alinhamento, e encaminhar ao agente certo.
- Modo especial: **Kickoff Completo**, que gera briefings iniciais para `@DOC`,
  `@SPEC` e `@C10` quando a pessoa quer criar a fundacao inteira do projeto.

Quando nenhum agente existente cobre uma lacuna real e recorrente, use:

- `F_AgentForge/F_Agent_Foreman.md`
- Alias: `@F`
- Funcao: criar, auditar, evoluir e eventualmente promover um agente sob demanda.

Regra pratica: use `@PICK` em tarefas grandes, ambiguas, multiambiente ou de risco
medio/alto. Use `@ONB` em comecos e retomadas. Use `@F` apenas quando a lacuna
foi comprovada, for recorrente ou claramente reutilizavel, e nenhum agente atual
cobrir pelo menos 70% do dominio.

## Pipeline Recomendado

0. `@ONB` orienta a entrada quando o projeto, fase ou proximo passo ainda nao
   esta claro. Se o pedido for fundacao completa, usar o Modo Kickoff Completo
   para gerar briefings para `@DOC`, `@SPEC` e `@C10`.
1. `@PICK` seleciona o time certo e detecta lacunas.
2. `@CRED` valida credenciais antes de acesso externo, API, banco, navegador,
   deploy ou producao.
3. `@C10` entende fase, memoria, brief e coordenacao.
4. `@SPEC` transforma ideia, legado ou feature grande em Pacote de Specs SDD.
5. `@DOC` cria ou sincroniza documentacao estrutural quando ela estiver ausente.
6. `@A` valida arquitetura, fronteiras, contratos e ownership cross-stack.
7. `@C` revisa o plano contra codigo real, consumidores e evidencias.
8. `impact_validator` mapeia impacto cross-stack antes de codar.
9. `@GSD` converte plano em criterio de aceite, TDD proporcional e Harness CLI.
10. Especialistas executam por dominio: `@B`, `@DATA`, `@D`, `@E`, `@GEO`,
    `@I18N`, `@IOS`, `@M`, `@MOD`, `@PAY`, `@BI`, `@BUG`, `@DEP`, etc.
11. Validadores especializados entram quando aplicavel: `@S`, `@P`, `@O`,
    `@Q`, `@GOV`, `@REG`, `@REL`.
12. `@GSD` volta depois da implementacao para auditar CLI, bug sweep e lacunas.
13. `@STD` e `@FLOW` verificam padroes e ordem de entrega quando necessario.
14. `final_validator` revisa o diff final antes de merge/deploy.
15. `@X` audita o processo em modo FOCUSED ou FULL.
16. `C10_DOCUMENTADOR` registra LOG, STATUS, DECISIONS e LEARNINGS.

O pipeline e recomendado, nao ritual cego. Tarefa pequena pode pular etapas, mas
tarefa relevante precisa declarar o que foi validado, o que e inferencia e o que
ficou como lacuna.

## Gate De Saude Sistemica

Toda spec, plano ou implementacao relevante deve declarar impacto nos eixos
abaixo. Se nao se aplicar, registre `N/A` com motivo. Se houver impacto, acione o
agente responsavel antes do selo final.

| Eixo | Pergunta minima | Agente natural |
|---|---|---|
| Arquitetura | Fronteiras, contratos e responsabilidades estao claros? | `@A` |
| Backend/dominio | Regra critica mora no backend/servico certo? | `@B` |
| Dados | Schema, migration, constraint, indice e rollback estao definidos? | `@DATA` |
| Seguranca | Auth, roles, PII, secrets, uploads, webhooks e logs estao protegidos? | `@S` |
| Performance | Hot paths, listas, queries, cache, concorrencia e custo foram avaliados? | `@P` |
| Observabilidade | Logs, metricas, traces, alertas e health checks existem? | `@O` |
| Testes | Criterios de aceite, TDD, regressao e smoke estao cobertos? | `@GSD` / `@Q` |
| Operacao | Ambientes, deploy, rollback, migrations e smoke pos-deploy estao planejados? | `@E` / `@O` / `@REL` |
| Dependencias | Libs, lockfiles, CVEs e licencas estao sob controle? | `@DEP` |
| Produto/UX | Estados vazios, erros, permissoes, acessibilidade e copy foram considerados? | `@D` / `@I18N` |
| Compliance | Ha requisito legal, loja, pagamento, dado sensivel ou setor regulado? | `@GOV` / `@REG` / `@PAY` |
| Documentacao | Decisoes, status, handoff e aprendizados serao registrados? | `@DOC` / `C10_DOCUMENTADOR` |

Feature de risco ALTO ou CRITICO nao deve chegar a `@V` sem evidencias de `@A`,
`@GSD`, `@Q` e dos validadores especializados aplicaveis.

## Catalogo Por Area

### Raiz

- `AGENTS.md`: catalogo mestre, governanca de raiz geral, pipeline, prefixos,
  gates e regras globais.
- `CLAUDE.md`: adaptador para Claude Code usar o arsenal.
- `.claude/agents/*.md`: wrappers de subagentes Claude apontando para os agentes
  originais.
- `.codex/agents/*.toml`: wrappers estruturados para Codex.
- `skills/`: skills locais para workflows recorrentes (`codex-agent-kit`,
  `gsd-tdd-cli-harness`, `agent-forge`).
- `RUNTIME_Bridge/`: manifesto, validadores e ponte Codex/Claude/Hermes-style.
- `AUDIT_AGENTES.md`: auditoria atual do arsenal, com foco em manter agentes
  genericos e stack-agnostic.
- `GUIA_COMPLETO_CODEX_AGENT_KIT.md`: este guia.

### C10_Maestro - Orquestracao E Memoria

- `C10_CAMISA10.md`: maestro do projeto; identifica fase, monta brief, coordena
  agentes e protege a governanca da raiz geral.
- `C10_DOCUMENTADOR.md`: fecha ciclos com LOG, DECISIONS, LEARNINGS e STATUS.
- `C10_Agent_ProjectRules.md`: template de `PROJECT_ROOT/AGENTS.md`.
- `C10_Agent_ClaudeProjectRules.md`: regras para gerar `CLAUDE.md` e wrappers
  em projetos reais.
- `C10_Method_SDD.md`: metodo SDD canonico.
- `C10_Skill_Strategy.md`: estrategia para promover partes do kit a skills.
- `C10_STATUS.md`, `C10_LOG.md`, `C10_DECISIONS.md`, `C10_LEARNINGS.md`:
  memoria operacional e templates vivos.

Use `@C10` no inicio de ciclo grande, retomada de contexto, decisao com varios
agentes ou quando a entrega precisa de memoria confiavel.

### SUP_Supervisor - Supervisao E Roteamento

- `SUP_PICK_AgentSelector.md`: `@PICK`, seleciona agentes por evidencia e define
  ordem de acionamento.
- `SUP_CRED_AccessGatekeeper.md`: `@CRED`, gate de credenciais, acesso externo,
  producao, browser, APIs e banco.
- `SUP_X_ProcessGuardian.md`: `@X`, auditoria geral de processo em modo FULL ou
  FOCUSED.
- `SUP_FLOW_DeliveryInspector.md`: `@FLOW`, detecta etapas puladas e ordem
  incorreta de entrega.
- `SUP_STD_StandardsEnforcer.md`: `@STD`, fiscaliza padroes declarados,
  inferidos e universais.
- `SUP_ENV_StatusRadar.md`: `@ENV`, mapeia paridade entre local, dev, staging e
  prod.
- `SUP_RiskMarshal.md`: `@R`, matriz de riscos tecnicos, operacionais, legais e
  financeiros.
- `SUP_Method_Harness.md`: metodo Harness canonico.
- `SUP_INTEGRATION_GUIDE.md`: integra os supervisores no pipeline.

Use `@PICK` como entrada padrao para trabalho complexo. Use `@X` antes de marcos
importantes, releases ou auditorias.

### ONB_Onboarding - Porta De Entrada

- `ONB_Agent_ProjectOnboardingGuide.md`: guia a pessoa por projeto novo ou em
  andamento, identifica fase, gargalos e proximo passo. Ele orienta e delega; nao
  trava a execucao.

Use `@ONB` em primeiro contato, retomada de projeto parado ou quando a pessoa
quer ajuda para decidir por onde comecar. Use o Modo Kickoff Completo quando a
pessoa pedir a fundacao inteira do projeto, documentacao base, specs iniciais e
orquestracao para comecar sem improviso.

### SPEC_Specs - Specs SDD

- `SPEC_Agent_SpecArchitect.md`: transforma ideias, features grandes, legados e
  ambiguidades em Pacotes de Specs SDD antes de arquitetura e execucao.

Use `@SPEC` quando o pedido ainda nao tem comportamento claro, criterio de
aceite, fronteiras, riscos, contratos ou plano de demonstracao.

### DOC_Documentation - Documentacao Estrutural

- `DOC_Agent_ProjectDocumentationArchitect.md`: cria e sincroniza documentacao
  estrutural de projeto, progresso, arquitetura, design, handoff e indice.
- `DOC_Template_DOCUMENTATION_INDEX.md`: indice de documentacao.
- `DOC_Template_ARCHITECTURE.md`: arquitetura.
- `DOC_Template_DESIGN.md`: design.
- `DOC_Template_HANDOFF.md`: handoff.
- `DOC_Template_ROADMAP.md`: roadmap.

Use `@DOC` quando a documentacao do produto esta incompleta, obsoleta ou
insuficiente para handoff, auditoria ou onboarding de outro agente.

### GSD_DeliveryDiscipline - TDD, CLI E Prova

- `GSD_Agent_TDDCLIAuditor.md`: `@GSD`, gate de implementacao, bugfix e
  refatoracao comportamental.

O `@GSD` define criterio de aceite, pede TDD proporcional, registra Harness CLI,
faz bug sweep e declara lacunas. Ele nao substitui executor nem QA; ele garante
que a entrega tenha prova.

### A_Architecture - Arquitetura Cross-Stack

- `A_Agent_CrossStackArchitect.md`: define fronteiras, contratos, camadas,
  responsabilidades, idempotencia, concorrencia e riscos cross-stack.

Use `@A` antes de APIs, schemas, auth, jobs, webhooks, integracoes, workers,
pagamentos ou qualquer mudanca que atravesse ambientes.

### AI_AIIntegration - Integracao De IA/LLM

- `AI_Agent_AIIntegrationArchitect.md`: prompts como contrato versionado, RAG,
  evals e golden sets, custo de tokens, guardrails, prompt injection, fallback
  e politica de dados enviados a provedores de modelo.

Use `@AI` sempre que o produto usar LLM/IA em producao: criacao ou mudanca de
prompt de produto, escolha/troca de modelo, RAG, custo, ou conteudo de usuario
enviado a provedor externo.

### B_BackendDomain - Backend E Dominio

- `B_Agent_BackendDomain.md`: APIs, DTOs, permissoes, regras de negocio,
  services, repositories, dominio backend e contratos.
- `B_Template_API_SPEC.md`: especificacao de API.

Use `@B` quando a regra nao pode ficar so na UI/mobile/admin e precisa morar no
backend com autorizacao, validacao e contrato claro.

### DATA_Database - Banco, Migrations E Integridade

- `DATA_Agent_DataMigrations.md`: schema, migrations, rollback, backfill,
  indices, constraints, integridade, replicacao e isolamento multi-tenant.
- `DATA_Template_MIGRATION_PLAN.md`: plano seguro de mudanca de schema/dados.

Use `@DATA` sempre que a entrega tocar estado persistente. Toda migration deve
ficar em diretorio canonico, versionado e rastreavel, com estrategia de rollback
e replicacao.

### BI_Dashboards - Metricas E Dashboards

- `BI_Agent_DashboardDesigner.md`: dashboards, KPIs, fonte da verdade, filtros,
  permissoes, performance e hierarquia visual.
- `BI_Template_DASHBOARD_SPEC.md`: especificacao de dashboard.
- `BI_Template_DASHBOARD_QA.md`: QA de dashboard.
- `BI_Template_METRIC_DICTIONARY.md`: dicionario de metricas.

Use `@BI` para relatorios, indicadores, funis, graficos e qualquer decisao
baseada em dados.

### BUG_Debugger - Debug Cirurgico Full-Stack

- `BUG_Agent_Debugger.md`: triagem, reproducao, diagnostico por camada,
  pre-validacao, intervencao cirurgica e pos-validacao.
- `patterns-bugs-comuns.md`: padroes de bugs comuns.
- `checklist-ambiente.md`: checklist de divergencia de ambiente.
- `sql-diagnostico.md`: consultas de diagnostico quando houver banco compativel.
- `erros-vercel.md`: referencia condicional para deploys Vercel.

Use `@BUG` para bug, regressao, 4xx/5xx, timeout, ambiente divergente, dado
inconsistente ou comportamento inesperado.

### C_Cetico - Revisao Critica

- `C_Agent_Cetico.md`: revisa planos contra codigo real, consumidores,
  contratos, riscos, ownership e lacunas.

Use `@C` antes de implementar. Se falta evidencia, o veredito correto e
`QUESTIONAR`, nao aprovar no escuro.

### D_Design - UX, UI E Paridade Visual

- `D_Agent_Design.md`: UX/UI, componentes, responsividade, acessibilidade,
  preservacao de logica, performance visual e validacao.
- `D_Agent_LayoutReplicator.md`: replica layout autorizado ou adapta referencia
  de terceiro com cuidado de propriedade intelectual e paridade visual.
- `D_Template_LAYOUT_REPLICATION_BRIEF.md`: briefing de replicacao.
- `D_Template_VISUAL_PARITY_REPORT.md`: relatorio de paridade visual.

Use `@D` para telas, polimento visual, design system, acessibilidade, estados de
UI, experiencia responsiva e replicacao/adaptacao de layouts.

### E_Environment - Ambientes, Secrets E Cloud

- `E_Agent_Environment.md`: env vars, secrets, CORS, paridade, deploy vars,
  fronteira frontend/backend e ambientes.
- `E_Agent_DigitalOceanEnvironment.md`: DigitalOcean, App Platform, planos,
  bancos gerenciados, custos e deploy.
- Referencias condicionais: `E_Reference_VercelAPI.md`,
  `E_Reference_RailwayAPI.md`, `E_Reference_DigitalOceanAPI.md`,
  `E_Reference_DigitalOceanAppPlatform.md`, `E_Reference_DigitalOceanPlans.md`,
  `E_Reference_Nomenclature.md`, `E_Reference_CrossValidation.md`.

Use `@E` antes de deploy, ao configurar env, corrigir CORS/secrets, trocar cloud,
validar custo ou comparar local/staging/producao.

### F_AgentForge - Fabrica De Agentes

- `F_Agent_Foreman.md`: orquestra a criacao de agentes sob demanda.
- `F_Agent_ContextScanner.md`: le contexto antes de criar agente.
- `F_Agent_AgentArchitect.md`: desenha blueprint.
- `F_Agent_AgentComposer.md`: escreve o agente.
- `F_Agent_WorkAuditor.md`: audita o trabalho do agente criado.
- `F_Agent_Lifecycle.md`: promocao, memoria, evolucao e aposentadoria.
- `F_AGENTS_INTEGRATION.md`: integracao da fabrica ao kit.
- `F_Promoted/*`: registro, diario e memoria coletiva de agentes promovidos.

Use `@F` quando `@PICK` detectar lacuna real e recorrente. Nao use a fabrica
para inflar o arsenal com papeis raros. Crie agentes apenas quando houver
recorrencia, valor claro e nenhum agente existente cobrir pelo menos 70% do
dominio necessario.

### GEO_Location - Localizacao, Enderecos E Proximidade

- `GEO_Agent_Location.md`: enderecos, coordenadas, raio, proximidade, geocoding,
  privacidade geografica e queries geoespaciais.
- `GEO_Template_LOCATION_MODEL.md`: modelo de decisao e dados de localizacao.

Use `@GEO` para mapas, busca por proximidade, GPS, raio, geocoding, privacidade
de endereco ou PostGIS/geospatial quando aplicavel.

### GOV_Compliance - Compliance Geral

- `GOV_Agent_ComplianceRegulatory.md`: compliance regulatorio geral, privacidade,
  retencao, consentimento, dados sensiveis e requisitos legais/setoriais.

Use `@GOV` quando houver risco legal, privacidade, setor regulado, tratamento de
dado sensivel ou politica de retencao/consentimento.

### I18N_LocalizationUX - Localizacao E UX Writing

- `I18N_Agent_LocalizationUX.md`: i18n, UX writing, ingles de produto, strings,
  emails, notificacoes, loja e glossario.
- `I18N_Template_GLOSSARY.md`: glossario.
- `I18N_Template_STRING_MAP.md`: mapa de strings.
- `I18N_Template_PLAYSTORE_TEXTS.md`: textos de Play Store.

Use `@I18N` para copy de UI, erros, notificacoes, textos de loja, traducao,
tom de voz e consistencia terminologica.

### IOS_AppleAppstore - iOS Nativo E App Store

- `IOS_Agent_AppleNativeAppstore.md`: iOS nativo, Swift/SwiftUI, signing,
  TestFlight, App Store Connect, privacy labels, StoreKit e review.
- `IOS_Template_NATIVE_PROJECT.md`: projeto iOS nativo.
- `IOS_Template_PRIVACY.md`: privacidade.
- `IOS_Template_APPSTORE_REVIEW.md`: checklist de review.

Use `@IOS` para Apple platforms, entitlements, permissions, compra in-app,
TestFlight e aprovacao App Store.

### M_MobilePlaystore - Mobile Apps E Play Store

- `M_Agent_MobilePlaystore.md`: apps mobile nativos/hibridos, offline,
  permissoes, seguranca, performance, testes em device e release.
- Templates: `M_Template_MOBILE_PROJECT.md`, `M_Template_MOBILE_RELEASE.md`,
  `M_Template_MOBILE_SECURITY.md`, `M_Template_MOBILE_TEST_PLAN.md`,
  `M_Template_MOBILE_OFFLINE.md`.

Use `@M` para mobile, Android/Play Store, sync offline, device real, permissions,
data safety e release em loja/canal aplicavel.

### MOD_TrustSafety - Trust & Safety

- `MOD_Agent_TrustSafety.md`: denuncias, moderacao, bloqueio, abuso, UGC,
  retencao, admin flow e protecao de usuarios.
- `MOD_Template_TRUST_SAFETY.md`: especificacao de trust & safety.

Use `@MOD` para chat, reviews, conteudo de usuario, denuncia, suporte,
moderacao, abuso e escalonamento operacional.

### O_Observability - Observabilidade E Operacao

- `O_Agent_DeployObservability.md`: logs, metricas, traces, alertas,
  healthchecks, smoke tests, rollback e operacao critica.

Use `@O` antes de producao, em incidentes, webhooks, filas, jobs, deploys e
fluxos que precisam ser monitorados.

### PAY_PaymentsMarketplace - Pagamentos E Monetizacao

- `PAY_Agent_PaymentsMarketplace.md`: pagamentos, marketplace, comissao, ledger,
  webhooks, refunds, disputes, risco regulatorio, app stores e monetizacao.
- `PAY_Template_PAYMENT_STRATEGY.md`: estrategia de pagamentos.

Use `@PAY` para Stripe ou outro PSP, split, payout, refund, fee, wallet, ledger,
escrow prometido, booking financeiro e monetizacao.

### PR_PromptOps - Prompt Engineering

- `PR_Agent_PromptRefiner_v2.md`: transforma pedidos vagos em prompts
  cirurgicos, validaveis, seguros e acionaveis.
- `PR_Template_PROMPT_BRIEF.md`: briefing de prompt.

Use `@PR` para refinar pedido antes de implementacao, investigacao, plano,
hotfix, validacao ou delegacao a outro agente.

### P_Performance - Performance E Escalabilidade

- `P_Agent_PerformanceValidator.toml`: valida hot paths, queries, cache,
  payloads, imagens, concorrencia, custo, baseline e regressao.

Use `@P` quando houver lista grande, dashboard pesado, query critica, imagem,
fila, cache, mobile lento, latencia ou custo operacional.

### Q_Quality - QA E Testes

- `Q_Agent_TestEngineer.md`: matriz de testes, aceite, regressao, unit,
  integracao, contrato, e2e, smoke e riscos residuais.

Use `@Q` antes de fechar feature, release, bugfix critico ou quando `@GSD`
apontar lacunas de Harness.

### DEP_Dependencies - Dependencias E Supply-Chain

- `DEP_Agent_DependencySteward.md`: upgrades, CVEs, lockfiles, licencas,
  breaking changes e plano de validacao para gerenciadores de pacotes.

Use `@DEP` ao adicionar/atualizar dependencia, mexer em lockfile, responder CVE
ou avaliar licenca. Em CVE, `@DEP` mapeia upgrade e `@S` avalia explorabilidade.

### REG_RegionalCompliance - Compliance Regional E De Plataforma

- `REG_Agent_RegionalCompliance.md`: compliance por pais/regiao e por plataforma
  ou loja, incluindo App Store, Play Store, marketplaces, permissoes,
  classificacao etaria e gates por mercado.
- `REG_Template_STORE_COMPLIANCE.md`: checklist generico de compliance de loja.

Use `@REG` quando o produto for publicar em pais, regiao, loja ou marketplace
especifico. Pareie com `@GOV` para base legal de dados e privacidade.

### REL_Release - Release E Versionamento

- `REL_Agent_ReleaseManager.md`: versionamento, changelog, branch/tag, escopo,
  gate de release, ordem de migration/deploy e rollback.

Use `@REL` ao cortar release. Ele define o que entra, numero de versao, riscos e
sequencia; `@O` cuida do deploy/operacao e `@V` valida o conteudo final.

### S_Seguranca - Seguranca

- `S_Agent_SecurityValidator.toml`: auth, autorizacao, PII, secrets, tokens,
  uploads, headers, CORS, CSP, pagamentos, input externo, logs e superficie de
  ataque.

Use `@S` quando tocar login, roles, storage, arquivos, logs, webhooks, tokens,
segredos, dados sensiveis ou dinheiro.

### T_Templates - Templates Reutilizaveis

- `T_Template_PROJECT.md`: visao inicial do projeto.
- `T_Template_STATUS.md`: status atual.
- `T_Template_LOG.md`: log cronologico.
- `T_Template_DECISIONS.md`: ADRs.
- `T_Template_LEARNINGS.md`: aprendizados.
- `T_Template_SPEC.md`: especificacao SDD.
- `T_Template_CLI_AUDIT.md`: auditoria Harness CLI.
- `T_Template_CLAUDE.md`: template de `CLAUDE.md`.

Use templates no onboarding, specs, handoff, memoria e entregas que precisam
virar referencia confiavel.

### V_Validation - Validadores De Impacto E Final

- `V_Agent_ImpactValidator.toml`: valida impacto cross-stack antes de
  implementar.
- `V_Agent_FinalValidator.toml`: selo final pos-implementacao, com diff, escopo,
  bug, regressao, seguranca, performance e testes.
- `V_Agent_ImpactGuard.md`: guia humano do ImpactValidator.
- `V_Agent_QualitySeal.md`: guia humano do selo final.

Use `@V` como portao antes de codar e antes de merge/deploy. O validador nao
aprova por simpatia; aprova por evidencia.

## Cobertura Atual Do Arsenal

### Coberto Como Nucleo

- Entrada e proximo passo: `@ONB`.
- Selecao inteligente de agentes: `@PICK`.
- Criacao sob demanda: `@F`.
- Orquestracao e memoria: `@C10` e `C10_DOCUMENTADOR`.
- Specs SDD: `@SPEC`.
- Documentacao estrutural: `@DOC`.
- Evidencia e anti-alucinacao: `@C`, `impact_validator`, `final_validator`.
- GSD/TDD/Harness: `@GSD`.
- Arquitetura, backend, banco, frontend, mobile, iOS, ambiente e observabilidade.
- Seguranca, performance, QA, dependencias, release, compliance geral e regional.
- Pagamentos, marketplace, trust & safety, BI, localizacao, i18n, debug e prompt
  ops.
- Integracao de IA/LLM em producao: `@AI` (prompts, RAG, evals, custo,
  guardrails e dados a provedores).
- Compatibilidade Claude Code por wrappers em `.claude/agents/`.

### Especializacoes Que Podem Virar Agentes Sob Demanda

Estas lacunas nao bloqueiam o kit hoje porque agentes existentes cobrem parte do
dominio. Crie via `@F` apenas se virarem recorrentes e nenhum agente atual cobrir
pelo menos 70% do dominio:

| Candidato | Quando criar | Cobertura atual |
|---|---|---|
| `A11Y_Agent_AccessibilityAuditor` | Produto web/mobile precisa WCAG formal e auditoria dedicada | `@D`, `@Q`, `@M`, `@IOS` |
| `SEO_Agent_GrowthWeb` | Site publico depende de SEO tecnico, schema.org e conteudo indexavel | `@D`, `@I18N`, `@BI` |
| `LEGAL_Agent_ContractReviewer` | Produto passa a depender de termos, contratos comerciais ou DPA recorrentes | `@GOV`, `@REG`, `@PAY` |

Decisao atual: nao criar todos agora. O arsenal fica melhor quando promove
agentes a partir de uso real, nao quando acumula papeis especulativos.

## Compatibilidade Com Claude Code

O kit inclui uma camada separada para Claude Code:

```text
CLAUDE.md
.claude/
  agents/
    pick-agent-selector.md
    project-onboarding-guide.md
    spec-architect.md
    project-documentation-architect.md
    gsd-tdd-cli-auditor.md
    final-validator.md
    ...
```

Os wrappers em `.claude/agents/` tem frontmatter no formato esperado pelo Claude
Code e apontam para os agentes originais como fonte da verdade. Eles nao
substituem o arsenal; apenas adaptam o roteamento.

Wrappers existentes hoje:

- `agent-forge-foreman`
- `ai-integration-architect`
- `backend-domain`
- `bi-dashboard`
- `camisa10-maestro`
- `cetico`
- `compliance-regulatory`
- `cross-stack-architect`
- `data-migrations`
- `debugger`
- `dependency-steward`
- `design-ux`
- `environment-manager`
- `final-validator`
- `gsd-tdd-cli-auditor`
- `impact-validator`
- `ios-appstore`
- `localization-ux`
- `location`
- `mobile-playstore`
- `observability-deploy`
- `payments-marketplace`
- `performance-validator`
- `pick-agent-selector`
- `process-guardian`
- `project-documentation-architect`
- `project-onboarding-guide`
- `regional-platform-compliance`
- `release-manager`
- `security-validator`
- `spec-architect`
- `test-engineer`
- `trust-safety`

Para aplicar em um projeto real:

1. Defina `PROJECT_ROOT` como a raiz geral do produto.
2. Coloque `.codex/` nessa raiz.
3. Copie/adapte `C10_Maestro/C10_Agent_ProjectRules.md` para
   `PROJECT_ROOT/AGENTS.md`.
4. Coloque `CLAUDE.md` na raiz geral quando usar Claude Code.
5. Coloque `.claude/agents/` na raiz geral quando usar Claude Code.
6. Trate `.codex/` como governanca transversal de todos os ambientes.
7. Em pedidos complexos ao Claude, comece por:

```text
Use the pick-agent-selector subagent to select the right team for this task.
```

Quando houver implementacao:

```text
Use the gsd-tdd-cli-auditor subagent before and after this implementation.
```

Antes de merge/deploy:

```text
Use the final-validator subagent to review this diff before merge.
```

## Metodologias Do Kit

### SDD - Spec-Driven Delivery

SDD e o metodo oficial para transformar pedido em entrega confiavel:

```text
State -> Spec -> Design -> Doubt -> Develop -> Demonstrate -> Document
```

- `State`: entender o estado real por arquivos, status, logs, codigo e contexto.
- `Spec`: definir comportamento esperado, aceite, riscos e contratos.
- `Design`: planejar menor diff, ownership, consumidores e rollback.
- `Doubt`: passar por `@C`, `@V` e validadores aplicaveis.
- `Develop`: implementar com escopo pequeno e TDD proporcional.
- `Demonstrate`: provar com Harness CLI, testes, smoke e bug sweep.
- `Document`: registrar status, decisoes, lacunas e aprendizados.

Arquivo canonico: `C10_Maestro/C10_Method_SDD.md`.

### Harness CLI

Harness e o contrato de prova executavel. Uma validacao deve registrar:

- comando executado;
- diretorio (`cwd`);
- objetivo;
- exit code;
- resultado;
- warnings/falhas relevantes;
- lacunas;
- veredito.

Arquivo canonico: `SUP_Supervisor/SUP_Method_Harness.md`. Uma entrega sem
Harness pode estar correta, mas ainda nao foi demonstrada.

### Anti-Alucinacao

Todo agente cirurgico segue esta cadeia:

1. Ler contexto do projeto.
2. Localizar arquivos e fluxos afetados.
3. Ler codigo real antes de opinar.
4. Rastrear consumidores e contratos.
5. Confrontar proposta contra evidencia.
6. Declarar lacunas explicitamente.
7. Emitir veredito proporcional ao que foi comprovado.

Se faltam arquivos, comandos ou contexto, o veredito correto e `QUESTIONAR`.

### Gates De Qualidade

O kit empilha gates em vez de depender de um unico revisor:

- `@SPEC` clarifica comportamento antes de arquitetura.
- `@A` valida fronteiras e contratos.
- `@C` revisa plano contra o real.
- `impact_validator` mapeia consequencia cross-stack.
- `@GSD` exige prova executavel.
- `@S`, `@P`, `@O`, `@PAY`, `@GOV`, `@REG` entram em superficies sensiveis.
- `@Q` transforma risco em teste.
- `final_validator` revisa o diff final.
- `@X` audita o processo.

### Memoria Operacional

O ciclo so fecha quando a memoria fica atualizada:

- `LOG`: o que aconteceu e quando.
- `STATUS`: estado atual, por ambiente e por frente.
- `DECISIONS`: decisoes arquiteturais e tradeoffs.
- `LEARNINGS`: erros, padroes e aprendizados reutilizaveis.
- `DOC`: arquitetura, design, roadmap, handoff e indice quando aplicavel.

Mudanca relevante sem memoria vira divida de contexto.

## Politica De Execucao

- Antes de editar: ler arquivos relevantes completos, mapear dependencias e
  proteger mudancas do usuario.
- Antes de dar veredito: separar fato observado, inferencia e lacuna.
- Durante implementacao: escopo pequeno, sem refatoracao lateral, sem dependencia
  pesada sem justificativa.
- Depois de editar: rodar validacoes reais quando existirem.
- Depois de implementar: registrar comandos, `cwd`, exit code, resultado e
  lacunas no formato Harness.
- Ao encontrar erro preexistente: documentar sem mascarar como sucesso.
- Ao tocar secrets: nunca imprimir valores, nunca hardcodar credencial e nunca
  criar `NEXT_PUBLIC_` com segredo.

## Estrategia De Skills

Nao crie uma skill para cada pasta de agente. Skills devem ser enxutas, com
gatilho claro, workflow recorrente e recursos reutilizaveis.

Skills recomendadas quando o objetivo for transformar o kit em capacidade
automatica do Codex:

1. `codex-agent-kit`: usa `AGENTS.md`, `C10_Maestro` e `SUP_Supervisor`.
2. `gsd-tdd-cli-harness`: aciona `@GSD`, SDD e Harness em implementacoes.
3. `agent-forge`: usa `F_AgentForge` para criar e evoluir agentes sob demanda.

A decisao esta documentada em `C10_Maestro/C10_Skill_Strategy.md`.

## Comandos De Auditoria Do Arsenal

Para verificar se o guia e o arsenal continuam alinhados:

```powershell
rg --files
rg -n -i "nome do projeto|stack especifica|provider especifico|pais especifico|fase fixa|default obrigatorio"
Get-ChildItem -Recurse -File .claude\agents | Select-Object -ExpandProperty FullName
```

Classifique achados conforme `AUDIT_AGENTES.md`:

- `OK_CONDICIONAL`: referencia usada somente quando aplicavel.
- `ESPECIALISTA`: agente propositalmente setorial ou de fornecedor.
- `TRAVA`: premissa indevida em agente generico.
- `HISTORICO`: registro antigo que nao orienta execucao.

Qualquer `TRAVA` deve ser corrigida no agente fonte e nos wrappers
correspondentes.

## Como Pedir Ao Kit

Para tarefa complexa:

```text
@PICK, selecione o time certo para esta tarefa, inclua @GSD se houver
implementacao e acione @F apenas se existir lacuna real.
```

Para projeto novo ou retomada:

```text
@ONB, descubra a fase do projeto, gargalos, contexto minimo e proximo passo.
```

Para feature grande:

```text
@SPEC, gere um Pacote de Specs SDD; depois acione @A, @C, @V e @GSD conforme o
impacto.
```

Para implementar com seguranca:

```text
@GSD, defina criterio de aceite e Harness CLI antes da implementacao; retorne
apos o diff para auditar comandos, bug sweep e lacunas.
```

Para fechar ciclo:

```text
C10_DOCUMENTADOR, atualize LOG, STATUS, DECISIONS e LEARNINGS conforme o que foi
comprovado neste ciclo.
```

## Regra Final

O arsenal absoluto nao e o que tem mais agentes. E o que ativa o agente certo,
na ordem certa, com evidencia suficiente, impacto declarado, validacao real e
memoria atualizada.
