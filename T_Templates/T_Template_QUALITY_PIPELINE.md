# QUALITY_PIPELINE - [NOME DO PROJETO]

## Responsabilidades

| Responsavel | Entrega |
|---|---|
| `@Q` | Testes unitarios front/back, API e happy paths Playwright |
| `@O` | Workflow GitHub Actions, caches, artefatos, secrets de CI e protecao de branch |
| `@DEP` + `@S` | Lockfiles, audit/SCA, Dependabot e tratamento de alertas |
| `@REL` | Gate, versao, changelog, rollback e promocao de release |
| `@GSD` + `@V` | Evidencia CLI e selo final |

## Gates Obrigatorios de Pull Request

- Instalar dependencias de forma reproduzivel a partir do lockfile.
- Lint, typecheck, build e testes unitarios do frontend e backend.
- Cobertura do backend: 100% lines/functions/branches/statements, exceto exclusoes documentadas.
- Testes de API/contrato afetados.
- Playwright somente para happy paths de funcionalidades criticas afetadas.
- Audit de dependencias sem vulnerabilidade bloqueante sem plano de remediacao aprovado.
- Verificacao de lockfile: todo manifesto alterado deve atualizar o lockfile correspondente.

## Fluxo De Release

```text
pull request -> quality/security gates -> merge protegido
-> deploy em staging -> smoke/Playwright selecionado -> aprovacao de release
-> tag + deploy de producao -> smoke + observabilidade -> rollback se necessario
```

## Evidencia Por Execucao

| Comando | CWD | Exit code | Resultado | Responsavel |
|---|---|---:|---|---|
| ... | ... | ... | ... | ... |

## Pendencias E Excecoes

- Excecao de cobertura:
- Vulnerabilidade sem fix:
- E2E temporariamente indisponivel:
- Plano de rollback:
