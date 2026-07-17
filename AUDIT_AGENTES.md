# AUDIT_AGENTES

## Auditoria Atual - P1 Arsenal Generico

**Data:** 2026-07-16

**Runtime:** 1.1.0

**Veredito:** APROVADO_COM_RESSALVAS

Este arquivo registra a diretriz atual do kit: nenhum agente principal deve ficar
vinculado a um projeto, stack, fornecedor, pais, loja ou dominio especifico.

## Regra De Ouro

Agentes centrais descobrem o contexto antes de prescrever:

- `@C10`: nao assume projeto, stack ou provider.
- `@PICK`: seleciona agentes por evidencia.
- `@SPEC`: gera specs por feature sem herdar contexto de projetos antigos.
- `@A`, `@B`, `@DATA`, `@DE`, `@DEP`, `@D`, `@E`, `@IAC`, `@ML`, `@PKG`,
  `@BUG`, `@M`, `@PAY`, `@GEO`, `@I18N`, `@MOD`: adaptam-se ao dominio real.
- `@ONB`: onboarding generico; descobre se o projeto e novo ou em andamento, nunca assume estado.
- `@REL`: release generico; descobre esquema de versao e fluxo de branch reais.
- `@REG`: ESPECIALISTA proposital por regiao/loja; descobre pais e plataforma antes de prescrever, nunca fixa um mercado.
- Agentes setoriais ou de fornecedor entram apenas quando aplicaveis.

## Ajustes Aplicados

- Removidas amarracoes a projetos especificos do `@SPEC` e da memoria `C10_LOG`.
- Refatorados `@E`, `@BUG`, `@M`, `@PAY`, `@GEO`, `@I18N`, `@MOD`, `@C10`, `@PICK`, `@X` para postura stack-agnostic.
- Transformadas referencias de Vercel/DigitalOcean/Supabase/PostGIS/Expo/Play Store/regiao em caminhos condicionais, nao defaults.
- Removido arquivo de spec de projeto especifico de dentro do arsenal.
- Templates de pagamento, localizacao e i18n foram generalizados.
- Renomeado o antigo agente de compliance, que vinha atado a um projeto especifico, para `@REG` (regional-platform-compliance): generico e adaptavel a qualquer pais/regiao e plataforma/loja que o projeto definir; removidas as notas de "nome historico" espalhadas pelo kit.
- Adicionados 4 agentes genericos: `@ONB` (onboarding), `@DATA` (banco/migrations), `@DEP` (dependencias/supply-chain) e `@REL` (release/versionamento), com wrappers Claude e Codex e registro no catalogo, CLAUDE.md, CAMISA10 e Gate de Saude.
- Environment ganhou referencia condicional de Railway (`E_Reference_RailwayAPI.md`); dados pessoais de exemplo nas referencias foram trocados por placeholders.
- Adicionados quatro especialistas recorrentes e stack-agnostic: `@PKG` para
  packages/CLI/SDK, `@DE` para pipelines de dados, `@ML` para ML/MLOps e `@IAC`
  para Infrastructure as Code.
- Criado `PROJECT_COVERAGE_MAP.toml` com 13 perfis verificaveis. Desktop e
  monorepo estao `PARCIAL`; embedded e game estao `AUSENTE`; nenhum deles pode
  ser apresentado como cobertura especializada total.
- Cada perfil possui cenario de rota e os perfis com owner precisam resolver
  fonte original e wrapper canonicos; arquivo generico nao conta como evidencia
  de cobertura.
- Criado catalogo de 30 patterns/anti-patterns com selecao contextual,
  contraindicacoes, ADRs e fitness gates.
- Criados validadores semanticos de arquitetura, multiagente e Harness CLI,
  contratos de cenarios das seis skills e gate continuo Linux/Windows.
- Generalizados frontend, QA, observabilidade, release e templates para
  selecionar controles pelo perfil real; Playwright, 100% de cobertura e GitHub
  Actions deixaram de ser defaults universais.

## Ressalvas De Cobertura

| Perfil | Status | Lacuna/fallback |
|---|---|---|
| Desktop | `PARCIAL` | Windows/Linux nativo, signing, IPC e auto-update podem exigir `@F` |
| Monorepo | `PARCIAL` | grafo afetado, cache remoto e versionamento coordenado podem exigir `@F` |
| Embedded/IoT | `AUSENTE` | criar especialista contextual via `@F` |
| Game dev | `AUSENTE` | criar especialista contextual via `@F` |

O P1 prova contratos estaticos das skills e executa forward-tests
representativos. Nao prova que todo modelo, prompt ou runtime acionara a skill
correta em 100% dos casos.

## Como Auditar Futuramente

Procure termos de amarracao:

```bash
rg -n -i "nome do projeto|stack especifica|provider especifico|pais especifico|fase fixa|default obrigatorio"
```

Classifique cada achado:

- `OK_CONDICIONAL`: referencia usada apenas quando aplicavel.
- `ESPECIALISTA`: agente propositalmente setorial/fornecedor.
- `TRAVA`: premissa indevida em agente generico, deve ser refatorada.
- `HISTORICO`: registro antigo que nao orienta execucao.

Qualquer `TRAVA` deve ser corrigida no agente fonte e nos wrappers correspondentes.
