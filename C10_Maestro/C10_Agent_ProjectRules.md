# Regras do Agente - [NOME DO PROJETO]

> Template de `AGENTS.md` para projetos que usam este arsenal.
> Copie/adapte para a raiz do projeto real.

---

## Identidade E Contexto

Voce esta trabalhando no projeto **[NOME DO PROJETO]**.

Antes de agir, leia quando existirem:

- `PROJECT.md`
- `STATUS.md`
- `LOG.md`
- `DECISIONS.md`
- `LEARNINGS.md`
- `AGENTS.md`
- README e docs relevantes

O agente maestro e `@C10` em `.codex/C10_Maestro/C10_CAMISA10.md`.

---

## Raiz Geral E Governanca Multiambiente

Este `AGENTS.md` deve ficar em `PROJECT_ROOT`, a raiz geral do projeto. A pasta
`.codex/` tambem deve ficar nessa raiz e governa todos os ambientes, apps,
servicos e pacotes abaixo dela.

Depois de checkout ou `git pull` do kit, executar a partir de `PROJECT_ROOT`:

```powershell
python .codex/RUNTIME_Bridge/scripts/install_project_runtime.py --project-root .
python .codex/RUNTIME_Bridge/scripts/install_project_runtime.py --project-root . --check
```

Nao copiar wrappers ou skills manualmente. O instalador projeta as skills em
`.agents/skills`, preserva customizacoes e reporta
drift/conflito sem sobrescrever arquivo de raiz alterado pelo projeto.

Modelo esperado:

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

Os nomes reais podem variar. Antes de agir, mapear a estrutura existente e
classificar cada pasta como backend, frontend, admin, mobile, pacote
compartilhado, CLI, desktop, infra/IaC, data pipeline, ML, docs, scripts,
dados, testes ou outro. Classificar tambem o perfil de cada unidade conforme
`.codex/C10_Maestro/C10_Method_ProjectProfiles.md`; nunca alegar cobertura total.

Regra de autoridade: os agentes do arsenal podem trabalhar dentro de qualquer
subpasta de `PROJECT_ROOT` quando a tarefa exigir, mas devem preservar a
organizacao global. A autoridade da `.codex/` e transversal: ela coordena
contratos, memoria, specs, validacoes, seguranca, performance, release e
documentacao de todos os ambientes.

Regras de preservacao da raiz:

- manter `.codex/`, `AGENTS.md`, `CLAUDE.md` e documentos estruturais na raiz;
- respeitar ownership de cada ambiente e seus comandos locais;
- rastrear contratos entre ambientes antes de alterar API, DTO, schema, env,
  permissao, build, deploy ou pacote compartilhado;
- nao criar pasta paralela ou duplicada sem decisao registrada em `DECISIONS.md`;
- nao misturar secrets, envs, builds ou artefatos entre ambientes;
- validar cada ambiente afetado com comando proporcional e registrar cwd, comando,
  exit code, resultado e lacunas no Harness.

Se a mudanca cruza dois ou mais ambientes, tratar como entrega cross-stack e
acionar `@A`, `@GSD`, `@Q`, `@V` e especialistas aplicaveis.

Ao final de cada ciclo relevante, e obrigatorio atualizar:

- status geral do projeto em `STATUS.md`;
- status/progresso de cada ambiente afetado;
- bloqueios, lacunas e proximas tarefas por ambiente;
- LOG do ciclo e decisoes/aprendizados quando existirem.

Mudancas de banco devem declarar o diretorio canonico de migrations do projeto.
Padrao sugerido: `PROJECT_ROOT/database/migrations/`. Se a stack exigir outro
caminho, como `back/prisma/migrations/` ou `supabase/migrations/`, esse caminho
vira o canonico e precisa estar documentado em `PROJECT.md`, `DATA_MODEL.md` ou
`OPERATIONS.md`. Nunca deixar migration solta fora do caminho canonico.

---

## Stack Do Projeto

Preencher com a stack real. Nao use estes exemplos como padrao obrigatorio.

- **Produto/plataforma:** [web | mobile | API | CLI/package/SDK | desktop | automacao | ETL/data | ML | IA/LLM | IaC | embedded | game | outro]
- **Frontend/UI:** [stack real ou N/A]
- **Backend/API:** [stack real ou N/A]
- **Banco/dados:** [stack real ou N/A]
- **Infra/deploy:** [provider real ou N/A]
- **Auth:** [provider/modelo real ou N/A]
- **Filas/jobs:** [stack real ou N/A]
- **Observabilidade:** [stack real ou N/A]
- **Testes:** [frameworks reais]
- **Perfil(es) de engenharia:** [IDs de `C10_Method_ProjectProfiles.md` por unidade]
- **CI e canal de release:** [provider e deploy/registry/store/model registry/apply/N/A]

---

## Estrutura De Pastas

```text
[descrever estrutura real do PROJECT_ROOT e dos ambientes]
```

Regra: seguir a estrutura existente da raiz geral. Se precisar criar nova pasta,
justificar por dominio, contrato, ownership ou manutencao, e verificar se ela
pertence a raiz, a um ambiente especifico ou a um pacote compartilhado.

---

## Convencoes Do Projeto

Preencher a partir de configs reais:

- Linguagem principal:
- Padrao de nomes:
- Formatador/linter:
- Test runner:
- Estilo de commits:
- Idioma de codigo:
- Idioma de documentacao:
- Idioma de usuario final:

Se uma convencao nao estiver definida, inferir do codigo dominante e sugerir
formalizacao. Nao impor preferencia pessoal.

---

## Regras De Comportamento

### Deve Fazer

1. Ler contexto antes de opinar ou editar.
2. Separar fato observado, inferencia e lacuna.
3. Seguir SDD: State, Spec, Design, Doubt, Develop, Demonstrate, Document.
4. Usar `@SPEC` para features grandes, ideias nebulosas ou legado.
5. Usar `@A` para fronteiras, contratos e arquitetura.
6. Usar `@GSD` para criterio de aceite, TDD proporcional, Harness CLI e bug sweep.
7. Usar `@S` quando tocar auth, PII, secrets, permissoes, uploads, webhooks ou pagamentos.
8. Usar `@P` quando tocar hot path, cache, queries, listas grandes, concorrencia ou custo.
9. Usar `@Q` para testes e regressao.
10. Usar `@V` antes de fechar entregas relevantes.
11. Atualizar documentacao/memoria quando houver decisao, entrega ou aprendizado relevante.
12. Fechar cada ciclo com `STATUS.md` geral e status dos ambientes afetados atualizados.
13. Salvar toda migration no diretorio canonico de migrations definido para o projeto.
14. Versionar lockfiles aplicaveis de cada ecossistema e executar instalacao/build reproduzivel antes de validar.
15. Executar audit de dependencias e tratar findings bloqueantes; manter Dependabot configurado para os ecossistemas reais do repositorio.
16. Criar/manter testes proporcionais ao perfil: Playwright apenas para UI
    browser critica; API apenas quando houver API; consumer/install para
    package/SDK; data-quality/replay para pipelines; eval/drift para ML; plan/policy
    para IaC. Thresholds devem vir da politica real e toda excecao e documentada.
17. Definir dominios de problema, ownership e contratos antes de criar modulos relevantes.
18. Garantir logs estruturados e seguros nos erros relevantes.

### Nunca Fazer

1. Nunca assumir stack, provider, dominio ou arquitetura sem evidencia.
2. Nunca implementar sem criterio de aceite em tarefa relevante.
3. Nunca fechar sem prova proporcional: teste, build, lint, typecheck, smoke ou equivalente.
4. Nunca hardcodar secret.
5. Nunca expor secret em chat, log, screenshot ou codigo.
6. Nunca colocar secret em variavel publica de frontend/mobile.
7. Nunca manter regra critica apenas na UI.
8. Nunca carregar listas/logs sem paginacao quando podem crescer.
9. Nunca mascarar lacuna como sucesso.
10. Nunca reverter mudanca de usuario sem pedido explicito.
11. Nunca encerrar ciclo relevante com progresso de ambiente desatualizado.
12. Nunca criar migration fora do caminho canonico ou sem plano de rollback/replicacao.
13. Nunca aceitar ecossistema sem lockfile aplicavel ou mudanca de manifesto sem atualizar lockfile.
14. Nunca silenciar audit, cobertura ou teste para liberar merge sem excecao rastreavel e aprovada.

---

## Gate De Saude Sistemica

Toda entrega relevante deve avaliar:

| Eixo | Pergunta | Agente |
|---|---|---|
| Arquitetura | Fronteiras, dominios de problema, ownership e contratos estao claros? | `@A` |
| Dominio/backend | Regra critica esta na camada correta? | `@B` |
| Dados | Schema, migration, constraint, indice e rollback foram considerados? | `@A`/`@B` |
| Seguranca | Auth, roles, PII, secrets, uploads, logs e webhooks estao seguros? | `@S` |
| Performance | Hot paths, listas, cache, queries, concorrencia e custo foram avaliados? | `@P` |
| Observabilidade | Logs, metricas, traces, alertas e health checks existem para fluxos criticos? | `@O` |
| Testes | As provas sao proporcionais ao perfil, contrato e risco reais? | `@GSD`/`@Q` |
| Operacao | CI detectado, canal, artefato, promocao e recovery estao planejados ou `N/A` justificado? | `@E`/`@O`/`@REL` |
| Dependencias | Lockfile, audit, Dependabot, CVEs e licencas estao sob controle? | `@DEP`/`@S` |
| Produto/UX | Estados vazios, erro, permissoes, acessibilidade e copy foram pensados? | `@D`/`@I18N` |
| Compliance | Ha requisito legal, loja, setor regulado, pagamento ou dado sensivel? | agente aplicavel |
| Documentacao | Decisoes, status, handoff e aprendizados foram registrados? | `@DOC`/`@C10` |

---

## Subagentes

Consultar `.codex/AGENTS.md` para catalogo completo.

Agentes comuns:

- `@C10`: orquestracao.
- `@PICK`: selecionar time.
- `@SPEC`: specs SDD.
- `@A`: arquitetura.
- `@B`: backend/API/dominio.
- `@D`: design/frontend/UX.
- `@PKG`: CLI/packages/bibliotecas/SDKs.
- `@DE`: data engineering/ETL/ELT.
- `@ML`: ML classico/MLOps; nao LLM/RAG.
- `@IAC`: Infrastructure as Code/state/plan/apply/drift.
- `@E`: environment/secrets.
- `@GSD`: TDD/Harness.
- `@S`: seguranca.
- `@P`: performance.
- `@Q`: testes.
- `@O`: observabilidade/deploy.
- `@BUG`: debug.
- `@PAY`: pagamentos.
- `@GEO`: localizacao.
- `@MOD`: trust & safety.
- `@I18N`: localizacao linguistica.
- `@GOV`: compliance geral, privacidade e regulacao.
- `@V`: validacao final.
- `@DOC`: documentacao.

Para duas ou mais frentes independentes, usar
`.codex/SUP_Supervisor/SUP_Method_MultiAgentDelivery.md` e a skill
`multi-agent-delivery`. Antes do primeiro spawn, definir task IDs, dependencias,
grupos paralelos, read-set, write-set, fingerprint, join e integrador. O
write-set de um subagente nao pode sobrepor read-set ou write-set concorrente
sem snapshot/worktree imutavel. O agente raiz aguarda todos os joins
obrigatorios, reconcilia contradicoes pela evidencia primaria e revalida o
resultado integrado.

---

## Variaveis De Ambiente

Consultar `.codex/E_Environment/E_Agent_Environment.md`.

Regras rapidas:

- Variavel publica de frontend/mobile nao e lugar de secret.
- Secret fica em backend/worker/CI/secrets manager.
- `.env.example` documenta nomes e finalidade, nunca valores reais.
- Ambientes test/staging/prod devem ter credenciais separadas quando o servico permitir.
- Mudanca de env normalmente exige redeploy/restart.

---

## Atualizacao Deste Arquivo

Atualizar quando:

- Stack muda.
- Convencao muda.
- Novo agente entra no fluxo.
- Learning vira regra.
- ADR muda o modo de trabalhar.

**Versao:** 2.0
**Ultima atualizacao:** [data]
