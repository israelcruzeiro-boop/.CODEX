# Changelog

Todas as mudancas relevantes do Codex Agent Kit sao registradas neste arquivo.
O versionamento segue SemVer; tags sao criadas somente depois de merge e CI verde.

## [1.1.0] - 2026-07-16

### Adicionado

- Mapa verificavel de cobertura com 13 perfis de projeto.
- Especialistas para packages/CLI/SDK, engenharia de dados, ML/MLOps e IaC.
- Catalogo contextual com 30 patterns e anti-patterns.
- 24 contratos versionados de cenarios para as seis skills.
- Validadores semanticos de entrega multiagente e Harness CLI.
- Gate continuo do proprio arsenal em Linux e Windows.

### Alterado

- QA, frontend, CI/CD e release passaram a selecionar controles pelo perfil real.
- O manifesto runtime ganhou schema, SemVer, compatibilidade e mapa de cobertura.
- O instalador passou a derivar skills do manifesto em vez de manter lista duplicada.

## [1.0.0] - 2026-07-16

- Baseline P0 no commit `6d07a93`: governanca Git, runtime Codex/Claude, seis
  skills transversais, specs SDD, arquitetura modular, pattern map, entrega
  multiagente e validadores adversariais.
