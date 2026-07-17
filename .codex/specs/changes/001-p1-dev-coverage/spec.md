# [001] P1 - Cobertura DEV Operacional

## 0. Identificacao

**Spec:** SPEC-001

**Titulo:** Cobertura DEV operacional e verificavel do Codex Agent Kit

**Responsavel:** integrador raiz do P1

**Data:** 2026-07-16

**Fase:** P1

**Risco:** ALTO

**Estado:** READY_FOR_BREAKDOWN

**AS-IS:** `AGENTS.md`, `RUNTIME_Bridge/RUNTIME.md`, `RUNTIME_Bridge/AGENT_RUNTIME_MAP.toml` e fontes P0 analisados em 2026-07-16

**TO-BE/ADRs:** N/A - o P1 evolui contratos de governanca, wrappers, validadores e CI dentro das fronteiras existentes do Runtime Bridge; nao altera fronteira de produto, persistencia ou API de aplicacao que exija `TARGET_ARCHITECTURE.md` ou ADR material.

`SPEC-001` corresponde a `changes/001-p1-dev-coverage`. IDs locais desta
mudanca nao devem ser reutilizados em outra spec.

## 1. State

**Contexto lido:** `AGENTS.md`; `C10_Maestro/C10_Method_SDD.md`; `C10_Maestro/C10_Method_ProjectProfiles.md`; `C10_Maestro/C10_Skill_Strategy.md`; `SPEC_Specs/SPEC_Agent_SpecArchitect.md`; `T_Templates/T_Template_SPEC.md`; `T_Templates/T_Template_PROJECT_PROFILE.md`; `A_Architecture/A_Method_ModularArchitecture.md`; `SUP_Supervisor/SUP_Method_Harness.md`; `RUNTIME_Bridge/P1_ACCEPTANCE.md`; `RUNTIME_Bridge/PROJECT_COVERAGE_MAP.toml`; `RUNTIME_Bridge/evals/skills/cases.toml`.

**Arquivos/fluxos afetados:** selecao de perfil por `@PICK`; fontes e wrappers dos especialistas; catalogo e mapa de patterns; contratos das seis skills; validadores multiagente e Harness; manifesto/instalador do runtime; quality gate e CI; orientacoes proporcionais de QA, frontend, operacao e release.

**Consumidores conhecidos:** mantenedores do kit; projetos que instalam os adapters; Codex e Claude via wrappers; agentes `@PICK`, `@PKG`, `@DE`, `@ML`, `@IAC`, `@A`, `@GSD`, `@Q`, `@O`, `@REL` e `@V`; CI do repositorio.

**Atores e papeis:** o mantenedor decide e integra o P1; `@PICK` classifica o artefato e seleciona owners/gates; especialistas executam o dominio coberto; `@F` recebe gaps abaixo de 70%; validadores produzem resultado deterministico; CI executa o gate em Linux e Windows; consumidores do kit usam apenas fontes e wrappers governados.

**Precondicoes:** checkout Git do kit na branch de trabalho; Python 3.11 ou superior; `RUNTIME_Bridge/AGENT_RUNTIME_MAP.toml` como manifesto versionado; fontes P0 presentes; nenhuma credencial ou acesso de producao necessario; qualquer medicao de cobertura abaixo de 70% deve registrar a matriz de requisitos do caso concreto.

**Fatos observados:** o P0 estabeleceu seis skills, wrappers Codex/Claude, validadores de specs/arquitetura e instalador; os casos versionados de skills e os quatro especialistas DEV nao existiam no baseline P0; desktop e monorepo nao possuem especialista dedicado completo; embedded/firmware e game/engine nao possuem especialista; o repositorio precisa distinguir manifesto de casos de um forward-test realmente observado.

**Inferencias:** quatro gaps recorrentes justificam ownership dedicado para package/CLI/SDK, data engineering, ML classico/MLOps e IaC; coverage status sem owner, fonte, wrapper, cenario, limite e gate favorece falsa confianca; um gate unico reduz drift entre validadores e wrappers, desde que nao se apresente como prova de CI ainda nao executada.

**Lacunas de contexto:** resultados observados de forward-test e execucoes remotas da matriz CI nao fazem parte da evidência inicial desta spec; thresholds de dominio, fornecedor e hardware continuam dependentes do projeto consumidor; essas lacunas nao bloqueiam o contrato de execucao, mas bloqueiam o DoD e a release ate produzirem as evidencias planejadas.

## 2. Escopo

**Objetivo mensuravel:** entregar nove capacidades DEV rastreaveis, cada uma com
owner, contrato, task, teste/gate e evidencia planejada, sem alegar cobertura
universal e com fallback explicito para cobertura parcial ou ausente.

### Inclui

- Mapa machine-readable dos 13 perfis canonicos e validador adversarial.
- Especialistas canonicos `@PKG`, `@DE`, `@ML` e `@IAC`, com wrappers governados.
- Catalogo neutro de patterns e metodo de decisao contextual.
- Dois triggers, um boundary e um non-trigger para cada uma das seis skills.
- Validadores semanticos de multiagente e Harness CLI.
- Quality gate local e CI Linux/Windows com controles de supply-chain.
- Manifesto unico para instalacao de agentes, wrappers e skills.
- Selecao proporcional de QA, CI, release e frontend pelo perfil observado.

### NAO inclui

- Prometer cobertura especializada universal ou equivaler `OBSERVADO` a cobertura total.
- Criar uma skill por agente ou por dominio.
- Promover especialista dedicado de desktop Windows/Linux, monorepo, embedded/IoT ou game dev sem recorrencia e coverage matrix suficientes.
- Definir thresholds de negocio, fairness, hardware, provedor ou loja sem evidencia do projeto consumidor.
- Executar deploy, publicar pacote, criar tag ou release antes do merge e do CI verde.
- Tratar o linter do manifesto de casos como forward-test isolado do modelo.

## 3. Requisitos Funcionais E Criterios De Aceite

| ID | Requisito/comportamento observavel | Prioridade | Estado |
|---|---|---|---|
| REQ-001 | Classificar cada unidade publicavel/operavel em um ou mais perfis canonicos e declarar cobertura, owners, gates, testes, release, limites, fallback e evidencia. | MUST | ATIVO |
| REQ-002 | Fornecer ownership especializado distinto para package/CLI/SDK, data engineering, ML classico/MLOps e Infrastructure as Code. | MUST | ATIVO |
| REQ-003 | Disponibilizar catalogo nao prescritivo de patterns de design, arquitetura, integracao, dados e resiliencia. | MUST | ATIVO |
| REQ-004 | Versionar contratos de trigger, boundary e non-trigger das seis skills sem confundir manifest lint com execucao observada. | MUST | ATIVO |
| REQ-005 | Validar semanticamente planos e resultados multiagente nas fases plan, fan-in e complete. | MUST | ATIVO |
| REQ-006 | Validar auditorias Harness distinguindo resultado individual de veredito global. | MUST | ATIVO |
| REQ-007 | Executar um gate continuo reproduzivel em Linux e Windows. | MUST | ATIVO |
| REQ-008 | Derivar skills e adapters do manifesto versionado, rejeitando path, schema ou catalogo divergente. | MUST | ATIVO |
| REQ-009 | Selecionar controles de QA, CI/CD, release e frontend pela evidencia do perfil, sem gate de framework ou provider universal. | MUST | ATIVO |

| ID | Requisito relacionado | Criterio de aceite mensuravel | Estado |
|---|---|---|---|
| AC-001 | REQ-001 | `validate_project_coverage.py --json` retorna exit 0 somente para os 13 perfis canonicos; `OBSERVADO` possui owner, fonte, wrapper/cenario rastreavel e limitacao; `PARCIAL`/`AUSENTE` possuem limitacao e fallback `@F`; paths de evidencia permanecem dentro do kit. | ATIVO |
| AC-002 | REQ-002 | Fontes e wrappers distintos declaram `@PKG`, `@DE`, `@ML` e `@IAC`, exigem leitura integral da fonte e passam os testes de coverage/runtime. | ATIVO |
| AC-003 | REQ-003 | O catalogo cobre as cinco familias, registra forcas, alternativas, contraindicacoes, trade-offs e gate, e nunca promove um pattern por simples presenca. | ATIVO |
| AC-004 | REQ-004 | O manifesto contem exatamente dois triggers, um boundary e um non-trigger por skill; o runner valida schema/evidencia e informa `execution_proven=false` sem results observados. | ATIVO |
| AC-005 | REQ-005 | Fixtures adversariais provam exit 1 para ciclos, dependencia invalida, retry orfao, colisao, fingerprint stale, claim inconsistente e fechamento incompleto; fixtures validas retornam exit 0. | ATIVO |
| AC-006 | REQ-006 | Fixtures adversariais provam exit 1 para PASS com exit nao zero, FAIL/LACUNA mascarado, evidencia sem rastreabilidade e veredito incoerente; auditoria valida retorna exit 0. | ATIVO |
| AC-007 | REQ-007 | Cada job da matriz Ubuntu/Windows em Python 3.11 e 3.14 executa compilacao, sync check, arsenal validator, testes, diff check e worktree check com `contents: read`, actions fixadas, timeout e concurrency. | ATIVO |
| AC-008 | REQ-008 | Instalador e validadores leem a lista de skills do `AGENT_RUNTIME_MAP.toml`; testes rejeitam traversal, reparse/symlink, schema divergente, catalogo duplicado e wrapper fora de paridade. | ATIVO |
| AC-009 | REQ-009 | Testes negativos confirmam: CLI nao exige Playwright, GitLab nao e convertido para GitHub Actions, ML classico pertence a `@ML` e ETL pertence a `@DE`; controles especificos exigem evidencia do projeto. | ATIVO |

**Regras de negocio e invariantes:**

| ID/relacao | Regra | Erros/estados | Permissoes |
|---|---|---|---|
| REQ-001 / AC-001 | Status nunca representa cobertura total; coverage abaixo de 70% no caso concreto encaminha para `@F`. | Schema, alias, evidence path ou fallback incoerente retorna exit 1; status valido e sempre limitado. | Mantenedor altera o mapa; `@PICK` e projetos consumidores leem. |
| REQ-002 / AC-002 | Cada especialista possui fonte canonica e wrappers apenas roteiam. | Fonte/wrapper ausente, divergente ou sem leitura integral retorna exit 1. | Mantenedor promove; runtime consome. |
| REQ-003 / AC-003 | Catalogo e repertorio; decisao normativa vive no `PATTERN_MAP.md` e ADR quando material. | Pattern sem familia, evidencia, contraindicao ou gate recebe `QUESTIONAR`/exit 1. | `@A` propoe; decisor do projeto aprova. |
| REQ-004 / AC-004 | Manifest lint e forward-test observado sao evidencias diferentes. | Cobertura insuficiente ou results incompletos retorna exit 1; sem results o runner alerta que execucao nao foi provada. | Mantenedor versiona casos; executor isolado registra results. |
| REQ-005 / AC-005 | Fan-out so ocorre com DAG, ownership, fingerprint e joins validos. | Violacao semantica retorna exit 1 em sua fase. | Integrador raiz aprova plano e fechamento. |
| REQ-006 / AC-006 | `PASS/FAIL/LACUNA/SKIP_JUSTIFICADO` classificam comandos; somente vereditos canonicos classificam a entrega. | Evidencia ou veredito incoerente retorna exit 1. | `@GSD` registra; `@Q`/`@V` auditam. |
| REQ-007 / AC-007 | CI executa somente codigo versionado com permissoes minimas. | Job, diff ou worktree sujo falha e bloqueia merge/release. | GitHub runner le; mantenedor aprova workflow. |
| REQ-008 / AC-008 | Manifesto e a lista unica; adapters projetados nao viram fonte. | Drift, path inseguro ou catalogo duplicado retorna exit 1. | Mantenedor altera manifesto; instalador projeta. |
| REQ-009 / AC-009 | Provider, framework e canal sao detectados antes dos controles. | Evidencia ausente produz lacuna/fallback, nunca presuncao de stack. | `@PICK` seleciona; especialista executa. |

## 4. Requisitos Nao Funcionais

| ID | Eixo | Requisito/limite | Condicao/carga | Gate/teste | Estado |
|---|---|---|---|---|---|
| NFR-001 | portabilidade | Validadores e instalador executam com Python 3.11 e 3.14 em Ubuntu e Windows. | Matriz completa do workflow do arsenal. | FIT-001 | ATIVO |
| NFR-002 | seguranca/supply-chain | CI usa somente `contents: read`, actions fixadas por commit e o instalador rejeita path absoluto, traversal e reparse/symlink. | Todo PR/push coberto e toda entrada de path governada. | TEST-007 / TEST-008 | ATIVO |
| NFR-003 | desempenho operacional | Cada job da matriz termina em no maximo 20 minutos e cancela execucao concorrente obsoleta da mesma ref. | Quality gate completo no runner hospedado. | FIT-001 | ATIVO |
| NFR-004 | manutenibilidade | A lista canonica de skills existe uma unica vez no manifesto; installer, docs e validadores derivam dela. | Inclusao, remocao ou rename de skill. | TEST-008 | ATIVO |
| NFR-005 | honestidade de cobertura | Nenhum perfil usa linguagem de cobertura total; `PARCIAL`/`AUSENTE` sempre declaram limite e `@F`. | Todos os 13 perfis e quatro cenarios negativos. | TEST-001 / TEST-009 | ATIVO |
| NFR-006 | observabilidade de validacao | Todo validador novo oferece exit code deterministico e JSON com `ok`, erros e contexto do artefato. | Caso valido e ao menos uma fixture adversarial por contrato. | TEST-001 / TEST-004 / TEST-005 / TEST-006 | ATIVO |

## 5. Definition Of Ready - DoR

- [x] `REQ-*`, `AC-*` e `NFR-*` possuem definicoes testaveis.
- [x] Escopo e `NAO inclui` estao explicitos.
- [x] AS-IS foi lido; TO-BE/ADR esta marcado N/A com justificativa proporcional.
- [x] Modulos, contratos, dados e consumidores afetados foram identificados.
- [x] Riscos, decisoes, validadores e criterios de reabertura estao registrados.
- [x] Tasks possuem entrada, saida, dependencia, dono e criterio de conclusao.
- [x] Tasks paralelas possuem read/write-set disjunto ou dependencia explicita.
- [x] Testes, Harness, rollout e rollback/forward-fix estao planejados.
- [x] Nenhuma decisao bloqueante permanece sem owner e proximo passo.

**Veredito DoR:** APROVADO

**Justificativa/lacunas:** contrato pronto para execucao; evidencias de implementacao permanecem deliberadamente planejadas e pertencem ao DoD.

**Lacuna nao bloqueante:** N/A para APROVADO

**Acao:** N/A para APROVADO

**Dono:** N/A para APROVADO

**Prazo ISO/criterio verificavel:** N/A para APROVADO

## 6. Design E Contratos

**Plano minimo:** manter o Runtime Bridge como fronteira; adicionar capacidades
por fontes canonicas, wrappers finos, manifestos versionados, validadores stdlib
e um gate composto, preservando fallback explicito onde nao existe especialista.

| ID | Modulo/owner | Responsabilidade | API publica | Dados/invariantes |
|---|---|---|---|---|
| MOD-001 | Capability registry / `@PICK` | Classificar perfil, cobertura, gaps e fallback. | CON-001 | Mapa TOML versionado; status nunca significa cobertura total. |
| MOD-002 | Specialist agents / `@F` | Governar quatro gaps recorrentes e rotear lacunas remanescentes. | CON-002 | Fontes canonicas e aliases exclusivos. |
| MOD-003 | Architecture catalog / `@A` | Orientar selecao contextual de patterns. | CON-003 | Presenca e decisao normativa permanecem separadas. |
| MOD-004 | Skill contracts / `@C10` | Versionar casos e resultados observados. | CON-004 | Manifest lint nunca falsifica forward-test. |
| MOD-005 | Multi-agent validation / integrador raiz | Validar DAG, ownership, envelopes, claims e joins. | CON-005 | Fases e fingerprints coerentes. |
| MOD-006 | Harness validation / `@GSD` | Validar comandos, evidencias e veredito. | CON-006 | Resultado individual separado do global. |
| MOD-007 | CI / `@O` | Executar gate reproduzivel em Linux e Windows. | CON-007 | Permissao minima e checkout limpo. |
| MOD-008 | Runtime manifest / `@C10` | Ser fonte unica de agentes, skills e compatibilidade. | CON-008 | Paths seguros e schema versionado. |
| MOD-009 | Project profiles / `@PICK` | Selecionar QA, CI e release pelo artefato real. | CON-009 | Provider/framework somente quando observado. |

| ID | Tipo | Owner/produtor | Consumidores | Schema/semantica | Compatibilidade |
|---|---|---|---|---|---|
| CON-001 | TOML + CLI JSON | MOD-001 | `@PICK`, projetos, CI | Schema 1; 13 perfis; status `OBSERVADO/PARCIAL/AUSENTE`; limitações e fallback. | Campos novos sao aditivos dentro do schema; quebra exige bump. |
| CON-002 | Agent source + wrappers | MOD-002 | Codex, Claude, installer | Fonte original e canonica; wrapper exige leitura completa e so roteia. | Aliases e paths permanecem estaveis; rename exige adapters. |
| CON-003 | Markdown + validator JSON | MOD-003 | `@A`, `@SPEC`, `@V` | Catalogo neutro; decisao no `PATTERN_MAP.md` + ADR/gate. | Entradas novas sao aditivas; IDs nao sao reutilizados. |
| CON-004 | TOML + CLI JSON | MOD-004 | skills, CI, mantenedor | Casos positivos, boundary e negativos; results observados sao artefato separado. | Schema versionado; ausencia de results nao vira sucesso de execucao. |
| CON-005 | Markdown + CLI JSON | MOD-005 | integrador e subagentes | Fases `plan/fan-in/complete`; exit 0 valido e 1 invalido. | Templates e validator evoluem juntos. |
| CON-006 | Markdown + CLI JSON | MOD-006 | `@GSD`, `@Q`, `@V` | Comando, cwd, objetivo, exit, status, EVD e veredito coerentes. | Campos obrigatorios so mudam com template/teste correspondentes. |
| CON-007 | GitHub Actions | MOD-007 | mantenedores e branch protection | Matriz, permissoes minimas, SHA pin, timeout, concurrency e gate unico. | CI do kit usa GitHub; projetos consumidores detectam seu provider. |
| CON-008 | TOML + installer CLI | MOD-008 | instalador, validators, docs | Schema 1, SemVer, Python >=3.11, Linux/Windows e paths governados. | Projecao preserva customizacao e falha em drift inseguro. |
| CON-009 | Markdown + TOML | MOD-009 | `@PICK`, `@Q`, `@O`, `@REL`, `@D` | Controles proporcionais e evidencias por unidade. | Perfil novo exige schema, owner, limite, testes e fallback. |

**Eventos adicionais:** N/A - o P1 nao cria eventos de runtime ou webhooks.

**Dados/migrations:** N/A - somente Markdown, TOML, Python e workflow versionados; sem schema persistente.

**Invariantes/transacoes/consistencia:** o manifesto e fonte unica; wrappers nao duplicam conhecimento; validadores retornam exit deterministico; artefatos gerados nao substituem fontes.

**Patterns:** N/A - o P1 cria o mecanismo de catalogo, mas esta spec nao aprova pattern de produto.

**Seguranca/permissoes:** paths confinados ao kit, rejeicao de traversal/reparse, CI `contents: read`, actions fixadas, nenhuma credencial persistida ou impressa.

**Observabilidade:** cada comando registra cwd, exit code, resultado e `EVD-*`; CI retém logs por job.

**Compatibilidade:** mudancas aditivas sob schema 1; alias/path removido exige adapter ou bump; instalador deve continuar operando em Linux/Windows e Python >=3.11.

## 7. Doubt

| ID | Risco/pergunta/hipotese | Impacto | Dono/decisor | Evidencia para fechar | Bloqueia? |
|---|---|---|---|---|---|
| RISK-001 | Results observados dos 24 casos de skills ainda nao foram produzidos em contexto isolado. | Nao impede manifest lint, mas impede alegar execucao comportamental. | mantenedor de skills | EVD-004 com results completos ou declaracao explicita `execution_proven=false`. | NAO para DoR; SIM para alegar forward-test no DoD. |
| RISK-002 | O primeiro run remoto revelou diferencas de identidade e classificacao de paths entre runners; `e793dda` corrige os casos localmente. | O snapshot corrigido ainda pode divergir em Python 3.11/3.14 ou no symlink nativo dos runners. | integrador raiz / `@O` | EVD-011 e FIT-001 passam sem falha em todos os jobs do snapshot corrigido. | NAO para DoR; SIM para release. |
| RISK-003 | Semantica especifica de registry, warehouse, model serving e provider IaC depende do projeto. | Generalizacao indevida produziria falsa cobertura. | `@PICK` e especialista do perfil | PROJECT_PROFILE do consumidor com limitacao/fallback e evidence ledger. | NAO; fallback `@F` e obrigatorio quando cobertura medida ficar abaixo de 70%. |
| RISK-004 | Quality gate local em worktree com alteracoes intencionais pode falhar apenas no generated-drift-check. | Nao deve ser mascarado como gate verde. | integrador raiz | EVD-007 produzido em checkout limpo ou falha registrada antes do merge. | NAO para escrever a spec; SIM para merge. |

**Validadores obrigatorios:** `@A` para contratos/patterns; `@GSD` para Harness; `@Q` para adversariais; `@S` para paths e workflow; `@O` para CI; `@V` para diff final.

**Criterios de reabertura da spec:** perfil canonico novo; mudanca de status/owner; skill adicionada/removida; schema do runtime alterado; provider CI do kit trocado; validator deixa de rejeitar fixture adversarial; alias/path publico renomeado; evidence ledger contradiz um aceite.

## 8. Backlog Executavel

| ID | Entrega | Agente/dono | Entrada | Saida | Read-set | Write-set | Dependencias | Execucao/isolamento | Criterio de conclusao |
|---|---|---|---|---|---|---|---|---|---|
| TASK-001 | Mapa e validador de cobertura | p1_dev_coverage | REQ-001, AC-001, NFR-005, AGENT_RUNTIME_MAP | mapa, metodo, template, validator e testes | `AGENTS.md`, `RUNTIME_Bridge/AGENT_RUNTIME_MAP.toml`, `SUP_Supervisor/SUP_PICK_AgentSelector.md` | `RUNTIME_Bridge/PROJECT_COVERAGE_MAP.toml`, `C10_Maestro/C10_Method_ProjectProfiles.md`, `T_Templates/T_Template_PROJECT_PROFILE.md`, `RUNTIME_Bridge/scripts/validate_project_coverage.py`, `RUNTIME_Bridge/scripts/test_project_coverage.py` | nenhuma | WORKTREE:p1-dev-coverage | TEST-001 e EVD-001 passam; status e fallback respeitam AC-001. |
| TASK-002 | Quatro especialistas recorrentes | p1_dev_coverage | TASK-001, REQ-002, AC-002 | fontes e wrappers Codex para `@PKG/@DE/@ML/@IAC` | `RUNTIME_Bridge/PROJECT_COVERAGE_MAP.toml`, `F_AgentForge/F_Agent_Foreman.md`, `AGENTS.md` | `PKG_PackageSDK/PKG_Agent_PackageCLISDK.md`, `DE_DataEngineering/DE_Agent_DataPipeline.md`, `ML_MLEngineering/ML_Agent_MLEngineering.md`, `IAC_PlatformEngineering/IAC_Agent_InfrastructureAsCode.md`, `.codex/agents/package-cli-sdk.toml`, `.codex/agents/data-pipeline.toml`, `.codex/agents/ml-engineering.toml`, `.codex/agents/infrastructure-as-code.toml` | TASK-001 | SERIAL | TEST-002 e EVD-002 provam fontes/wrappers coerentes. |
| TASK-003 | Catalogo e governanca de patterns | p1_patterns_skills | REQ-003, AC-003, metodo modular | catalogo, metodo, template e adversariais | `A_Architecture/A_Method_ModularArchitecture.md`, `A_Architecture/A_Agent_CrossStackArchitect.md` | `A_Architecture/A_Reference_PatternCatalog.md`, `A_Architecture/A_Method_PatternMap.md`, `DOC_Documentation/DOC_Template_PATTERN_MAP.md`, `RUNTIME_Bridge/scripts/validate_architecture.py`, `RUNTIME_Bridge/scripts/test_architecture_adversarial.py` | nenhuma | WORKTREE:p1-patterns-skills | TEST-003 e EVD-003 cobrem familias, decisoes e gates. |
| TASK-004 | Contratos das seis skills | p1_patterns_skills | TASK-003, REQ-004, AC-004, skills canonicas | cases, runner e skills alinhadas | `skills/agent-forge/SKILL.md`, `skills/codex-agent-kit/SKILL.md`, `skills/gsd-tdd-cli-harness/SKILL.md`, `skills/multi-agent-delivery/SKILL.md`, `A_Architecture/A_Method_PatternMap.md` | `RUNTIME_Bridge/evals/skills/cases.toml`, `RUNTIME_Bridge/scripts/run_skill_contract_evals.py`, `RUNTIME_Bridge/scripts/test_skill_contract_evals.py`, `skills/architecture-blueprint/SKILL.md`, `skills/spec-driven-breakdown/SKILL.md`, `C10_Maestro/C10_Skill_Strategy.md` | TASK-003 | SERIAL | TEST-004 e EVD-004 provam cobertura do manifesto sem falsificar execution proof. |
| TASK-005 | Validador multiagente | p1_runtime_ci | REQ-005, AC-005, metodo multiagente | validator, templates e testes | `SUP_Supervisor/SUP_Method_MultiAgentDelivery.md`, `C10_Maestro/C10_CAMISA10.md` | `SUP_Supervisor/SUP_Method_MultiAgentDelivery.md`, `T_Templates/T_Template_MULTI_AGENT_PLAN.md`, `T_Templates/T_Template_AGENT_TASK.md`, `T_Templates/T_Template_AGENT_RESULT.md`, `RUNTIME_Bridge/scripts/validate_multi_agent.py`, `RUNTIME_Bridge/scripts/test_multi_agent_validator.py` | nenhuma | WORKTREE:p1-runtime-ci | TEST-005 e EVD-005 passam para fixtures validas e adversariais. |
| TASK-006 | Validador Harness | p1_runtime_ci | TASK-005, REQ-006, AC-006, metodo Harness | validator, template, skill e testes | `SUP_Supervisor/SUP_Method_Harness.md`, `GSD_DeliveryDiscipline/GSD_Agent_TDDCLIAuditor.md` | `T_Templates/T_Template_CLI_AUDIT.md`, `GSD_DeliveryDiscipline/GSD_Agent_TDDCLIAuditor.md`, `skills/gsd-tdd-cli-harness/SKILL.md`, `RUNTIME_Bridge/scripts/validate_cli_audit.py`, `RUNTIME_Bridge/scripts/test_cli_audit_validator.py` | TASK-005 | SERIAL | TEST-006 e EVD-006 rejeitam mascaramento e aceitam Harness coerente. |
| TASK-007 | Quality gate e CI do arsenal | p1_runtime_ci | TASK-005, TASK-006, REQ-007, AC-007 | runner do gate, workflow e testes | `RUNTIME_Bridge/scripts/validate_arsenal.py`, `RUNTIME_Bridge/scripts/sync_claude_from_codex.py`, `RUNTIME_Bridge/scripts/test_*.py` | `RUNTIME_Bridge/scripts/run_quality_gate.py`, `RUNTIME_Bridge/scripts/test_quality_gate.py`, `.github/workflows/arsenal-ci.yml`, `.github/dependabot.yml` | TASK-005, TASK-006 | SERIAL | TEST-007/EVD-007 passam localmente; FIT-001/EVD-011 passam remotamente. |
| TASK-009 | Generalizacao transversal por perfil | p1_dev_coverage | TASK-001, REQ-009, AC-009 | agentes e templates sem defaults web/provider universais | `RUNTIME_Bridge/PROJECT_COVERAGE_MAP.toml`, `C10_Maestro/C10_Method_ProjectProfiles.md` | `D_Design/D_Agent_Design.md`, `Q_Quality/Q_Agent_TestEngineer.md`, `O_Observability/O_Agent_DeployObservability.md`, `REL_Release/REL_Agent_ReleaseManager.md`, `SUP_Supervisor/SUP_PICK_AgentSelector.md`, `T_Templates/T_Template_PROJECT.md`, `T_Templates/T_Template_QUALITY_PIPELINE.md` | TASK-001 | PARALELO | TEST-009 e EVD-009 provam os quatro cenarios negativos. |
| TASK-008 | Manifesto, instalador, documentacao e integracao | integrador raiz | TASK-002, TASK-004, TASK-007, TASK-009, REQ-008, AC-008 | runtime map unico, installer, wrappers Claude, catalogo publico e spec validada | `RUNTIME_Bridge/PROJECT_COVERAGE_MAP.toml`, `RUNTIME_Bridge/evals/skills/cases.toml`, `RUNTIME_Bridge/scripts/run_quality_gate.py`, fontes/wrappers dos quatro especialistas | `RUNTIME_Bridge/AGENT_RUNTIME_MAP.toml`, `RUNTIME_Bridge/scripts/install_project_runtime.py`, `RUNTIME_Bridge/RUNTIME.md`, `AGENTS.md`, `.claude/agents/package-cli-sdk.md`, `.claude/agents/data-pipeline.md`, `.claude/agents/ml-engineering.md`, `.claude/agents/infrastructure-as-code.md`, `.codex/specs/EXECUTAR-TODAS.md`, `.codex/specs/changes/001-p1-dev-coverage/spec.md`, `RUNTIME_Bridge/P1_ACCEPTANCE.md` | TASK-002, TASK-004, TASK-007, TASK-009 | SERIAL | TEST-008, TEST-010, EVD-008 e EVD-010 passam; integracao nao deixa fonte duplicada. |

## 9. Rastreabilidade Obrigatoria

| Requisito | Modulo/contrato | Task | Teste/gate | Evidencia | Estado |
|---|---|---|---|---|---|
| REQ-001 / AC-001 / NFR-005 / NFR-006 | MOD-001 / CON-001 | TASK-001 | TEST-001 | EVD-001 | PROVADO |
| REQ-002 / AC-002 | MOD-002 / CON-002 | TASK-002 | TEST-002 | EVD-002 | PROVADO |
| REQ-003 / AC-003 | MOD-003 / CON-003 | TASK-003 | TEST-003 | EVD-003 | PROVADO |
| REQ-004 / AC-004 / NFR-006 | MOD-004 / CON-004 | TASK-004 | TEST-004 | EVD-004 | PROVADO |
| REQ-005 / AC-005 / NFR-006 | MOD-005 / CON-005 | TASK-005 | TEST-005 | EVD-005 | PROVADO |
| REQ-006 / AC-006 / NFR-006 | MOD-006 / CON-006 | TASK-006 | TEST-006 | EVD-006 | PROVADO |
| REQ-007 / AC-007 / NFR-002 | MOD-007 / CON-007 | TASK-007 | TEST-007 | EVD-007 | PROVADO |
| REQ-007 / AC-007 / NFR-001 / NFR-003 | MOD-007 / CON-007 | TASK-007 | FIT-001 | EVD-011 | PLANEJADO |
| REQ-008 / AC-008 / NFR-002 / NFR-004 | MOD-008 / CON-008 | TASK-008 | TEST-008 | EVD-008 | PROVADO |
| REQ-001 / REQ-002 / REQ-003 / REQ-004 / REQ-005 / REQ-006 / REQ-007 / REQ-008 / REQ-009 | MOD-001 / MOD-002 / MOD-003 / MOD-004 / MOD-005 / MOD-006 / MOD-007 / MOD-008 / MOD-009 | TASK-008 | TEST-010 | EVD-010 | PROVADO |
| REQ-009 / AC-009 / NFR-005 | MOD-009 / CON-009 | TASK-009 | TEST-009 | EVD-009 | PROVADO |

## 10. Rollout E Rollback

**Ambientes e ordem:** validar no worktree local; integrar por owner unico; abrir PR; executar matriz Ubuntu/Windows; somente apos todos os jobs verdes fazer merge em `main`; tag/release 1.1.0 permanece etapa posterior.

**Migration expand/migrate/contract:** N/A - nao ha banco; novos campos TOML/Markdown sao aditivos no schema 1, e remocao futura exige bump/adapters.

**Feature flags/adapters:** wrappers Codex/Claude e instalador sao adapters; N/A para feature flag porque o kit nao executa trafego de usuario.

**Compatibilidade entre versoes:** preservar aliases e paths existentes; projetar wrappers sem sobrescrever customizacao; Python minimo 3.11; validar Linux/Windows antes do merge.

**Smoke e observabilidade:** executar TEST-001 a TEST-010 e FIT-001; registrar cwd, comando, exit code, erros/warnings e `EVD-*`; CI retém logs por job.

**Criterio de abortar:** qualquer exit nao zero em validator/teste, drift gerado, diff check, wrapper fora de paridade, path inseguro ou job da matriz falhando interrompe merge/release.

**Rollback de aplicacao:** reverter atomicamente o commit/PR P1 e reinstalar o runtime a partir do ultimo manifesto aprovado; nao copiar wrappers manualmente.

**Rollback de dados:** N/A - nenhum dado persistente ou migration e alterado.

**Forward-fix/restauracao quando rollback for inseguro:** se um consumidor ja tiver materializado adapters P1, preservar alias/path via adapter compatível e publicar forward-fix do manifesto/installer antes de remover a entrada antiga.

## 11. Demonstrate - Testes, Harness E Evidencias

| ID | Requisito/risco | Tipo | Arquivo/comando | Resultado esperado | Evidencia |
|---|---|---|---|---|---|
| TEST-001 | REQ-001 / AC-001 / NFR-005 / NFR-006 | contract/adversarial | `python -B RUNTIME_Bridge/scripts/validate_project_coverage.py --json` | Exit 0 no mapa canonico; fixtures invalidas dos testes retornam findings esperados. | EVD-001 |
| TEST-002 | REQ-002 / AC-002 | contract/runtime | `python -B RUNTIME_Bridge/scripts/validate_arsenal.py` | Exit 0; fontes e wrappers dos quatro especialistas existem e apontam a fonte completa. | EVD-002 |
| TEST-003 | REQ-003 / AC-003 | unit/adversarial | `python -B -m unittest RUNTIME_Bridge.scripts.test_architecture_adversarial -v` | Exit 0; familias, estados, ADR/gates e casos adversariais permanecem cobertos. | EVD-003 |
| TEST-004 | REQ-004 / AC-004 / NFR-006 | contract | `python -B RUNTIME_Bridge/scripts/run_skill_contract_evals.py --json` | Exit 0, 24 casos, 2/1/1 por skill; sem results, `execution_proven=false` e warning explicito. | EVD-004 |
| TEST-005 | REQ-005 / AC-005 / NFR-006 | unit/adversarial | `python -B -m unittest RUNTIME_Bridge.scripts.test_multi_agent_validator -v` | Exit 0; todas as fixtures validas/adversariais passam. | EVD-005 |
| TEST-006 | REQ-006 / AC-006 / NFR-006 | unit/adversarial | `python -B -m unittest RUNTIME_Bridge.scripts.test_cli_audit_validator -v` | Exit 0; falha/lacuna mascarada e veredito incoerente sao rejeitados. | EVD-006 |
| TEST-007 | REQ-007 / AC-007 / NFR-002 | integration/quality-gate | `python -B RUNTIME_Bridge/scripts/run_quality_gate.py --json` | Exit 0 em checkout limpo; compile, sync, validators, tests, diff e drift passam. | EVD-007 |
| FIT-001 | REQ-007 / AC-007 / NFR-001 / NFR-003 | CI/fitness | `.github/workflows/arsenal-ci.yml` na matriz Ubuntu/Windows e Python 3.11/3.14 | Todos os jobs terminam verdes em ate 20 minutos, com permissao minima e concurrency ativa. | EVD-011 |
| TEST-008 | REQ-008 / AC-008 / NFR-002 / NFR-004 | integration/security | `python -B -m unittest RUNTIME_Bridge.scripts.test_project_runtime -v` | Exit 0; manifesto unico, instalacao/check, paths e preservacao de customizacao passam. | EVD-008 |
| TEST-009 | REQ-009 / AC-009 / NFR-005 | unit/negative-routing | `python -B -m unittest RUNTIME_Bridge.scripts.test_project_coverage -v` | Exit 0; CLI, provider CI, ML e ETL nao herdam owners/gates incorretos. | EVD-009 |
| TEST-010 | SPEC-001 / risco de contrato incompleto | spec/fitness | `python -B RUNTIME_Bridge/scripts/validate_specs.py . --json` | Exit 0; uma change valida, sem elo quebrado, ciclo ou colisao insegura. | EVD-010 |

| ID | Prova produzida | Fonte/caminho | Retencao/owner | Estado |
|---|---|---|---|---|
| EVD-001 | JSON do coverage validator e transcript dos adversariais. | quality gate local no commit `af94406`; 13 perfis e 13 cenarios. | ate release 1.1.0 / p1_dev_coverage | PROVADO |
| EVD-002 | Relatorio de coerencia de agentes/wrappers. | quality gate local no commit `af94406`; 46/46 wrappers. | ate release 1.1.0 / p1_dev_coverage | PROVADO |
| EVD-003 | Transcript dos testes de arquitetura/patterns. | 64 testes focados e suite integrada do commit `af94406`. | ate release 1.1.0 / p1_patterns_skills | PROVADO |
| EVD-004 | JSON do manifesto de casos; results observados permanecem evidencia separada. | 24 casos validos; `execution_proven=false` declarado no quality gate. | ate proxima mudanca material das skills / mantenedor de skills | PROVADO |
| EVD-005 | Transcript dos testes multiagente. | 17 testes focados e suite integrada do commit `af94406`. | ate release 1.1.0 / p1_runtime_ci | PROVADO |
| EVD-006 | Transcript dos testes Harness. | 15 testes focados e suite integrada do commit `af94406`. | ate release 1.1.0 / p1_runtime_ci | PROVADO |
| EVD-007 | JSON do quality gate local em worktree limpo. | 8/8 gates e 200 testes no commit `e793dda`. | ate release 1.1.0 / `@O` | PROVADO |
| EVD-008 | Transcript dos testes do runtime/installer. | 23 testes por invocacao de modulo e suite integrada do commit `af94406`. | ate release 1.1.0 / integrador raiz | PROVADO |
| EVD-009 | Transcript dos cenarios negativos por perfil. | 14 testes de coverage e suite integrada do commit `af94406`. | ate release 1.1.0 / p1_dev_coverage | PROVADO |
| EVD-010 | JSON do validador da spec canonica: uma change, zero erros e zero warnings. | stdout do TEST-010 executado em 2026-07-16 no handoff desta mudanca. | ate merge da spec / integrador raiz | PROVADO |
| EVD-011 | URLs e logs dos quatro jobs remotos de FIT-001. | Run inicial `29543436833` vermelho; rerun do snapshot corrigido ainda planejado. | conforme retencao do CI e ate release 1.1.0 / `@O` | PLANEJADO |

**Teste falhando primeiro:** fixtures adversariais de cada validator devem retornar exit 1 ou finding esperado antes da implementação correspondente; o mapa/spec canonicos devem retornar exit 0.

**Harness CLI planejado:** registrar TEST-001 a TEST-010 e FIT-001 com cwd `C:\Users\israe\Downloads\.codex`, comando, exit, warning e evidência no formato `T_Templates/T_Template_CLI_AUDIT.md`.

**Bug sweep/regressao:** cobrir path traversal/reparse, wrapper/source drift, status/fallback incoerente, case count, ciclo/colisao/retry, PASS/FAIL mascarado, provider universal, manifest duplicado, diff sujo e compatibilidade Linux/Windows.

**Ambientes nao validados e motivo:** o snapshot anterior executou na CI remota e falhou; Ubuntu/Windows com o snapshot corrigido e o forward-test isolado permanecem planejados. Esta spec nao os marca como aprovados.

## 12. Definition Of Done - DoD

- [x] Todos os `REQ-*`, `AC-*` e `NFR-*` ativos estao provados localmente ou possuem a ressalva FIT-001 explicitamente aceita.
- [x] A matriz `REQ/AC/NFR -> MOD/CON -> TASK -> TEST/FIT -> EVD` possui todos os elos planejados.
- [x] Contratos e adapters foram validados com seus consumidores por TEST-002 e TEST-008.
- [x] Harness integrado foi executado e recebeu veredito canonico.
- [ ] Rollout, smoke, FIT-001, rollback/forward-fix e observabilidade foram demonstrados.
- [x] Bug sweep completo foi executado sem mascarar falha conhecida ou lacuna critica.
- [x] `ARCHITECTURE.md` nao foi alterado por intencao futura; TO-BE/ADR permanece N/A justificado para esta mudanca de governanca.
- [x] LOG, STATUS geral/ambientes e changelog foram atualizados para o snapshot local.

**Veredito DoD:** APROVADO_COM_RESSALVAS

**Justificativa/lacunas:** implementacao e gate local corrigido estao comprovados; a entrega permanece com uma unica ressalva operacional ate o rerun executar FIT-001 remotamente.

**Lacuna nao bloqueante:** a matriz remota Ubuntu/Windows ainda nao aprovou o snapshot corrigido; isso impede merge/release, nao invalida o gate local.

**Acao:** fazer push da branch, observar os quatro jobs e rebaixar o veredito se qualquer combinacao de OS/Python falhar.

**Dono:** integrador raiz com `@GSD`, `@Q`, `@O` e `@V`.

**Prazo ISO/criterio verificavel:** FIT-001 passa sem falha em Ubuntu/Windows e Python 3.11/3.14 antes de merge ou release.

## 13. Document

**LOG:** sim - `LOG.md` registra o ciclo P1.

**DECISIONS/ADRs:** N/A - nenhuma nova decisao arquitetural material nesta formalizacao.

**TARGET_ARCHITECTURE/PATTERN_MAP:** N/A - esta spec governa a entrega P1, sem declarar arquitetura de produto implementada.

**LEARNINGS:** sim - cobertura declarada, manifest lint e execucao observada sao evidencias diferentes.

**STATUS geral e por ambiente:** sim - `STATUS.md` separa gate local corrigido e aprovado do rerun remoto pendente.

**Validacao da spec:** TEST-010 executado em 2026-07-16 com exit 0, uma change, zero erros e zero warnings.

**Proximo passo obrigatorio:** `@O` confirma FIT-001 apos publicar o snapshot corrigido; merge, tag e release 1.1.0 permanecem proibidos ate a matriz remota ficar verde.
