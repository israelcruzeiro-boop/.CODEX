# QUALITY_PIPELINE - [NOME DO PROJETO/UNIDADE]

## Perfil E Canal

**Perfil(es):** ...
**CI detectado:** GitHub Actions | GitLab CI | Azure Pipelines | Jenkins | outro | N/A
**Artefato:** app | service | package | binary | dataset/job | model | IaC | outro
**Canal:** deploy | registry | store | orchestrator | model registry | apply | N/A

## Responsabilidades

| Responsavel | Entrega aplicavel |
|---|---|
| `@Q` | Matriz de testes proporcional ao perfil |
| `@O` | Pipeline no CI detectado, artefatos e operacao |
| Especialista | Invariantes: `@B`/`@D`/`@PKG`/`@DE`/`@ML`/`@IAC`/outro |
| `@DEP` + `@S` | Supply-chain, secrets e controles aplicaveis |
| `@REL` | Versao, canal, gate, comunicacao e recovery |
| `@GSD` + `@V` | Evidencia CLI e selo final |

## Gates Proporcionais

| Gate | Aplicavel? | Comando/evidencia real | Criterio | Owner |
|---|---|---|---|---|
| Instalacao/build reproduzivel | ... | ... | ... | ... |
| Unit/component/domain | ... | ... | ... | ... |
| API/contract | ... | ... | ... | ... |
| Browser/device/installer smoke | ... | ... | ... | ... |
| Consumer/package/install | ... | ... | ... | ... |
| Data quality/replay | ... | ... | ... | ... |
| ML eval/drift/rollback | ... | ... | ... | ... |
| IaC validate/policy/plan | ... | ... | ... | ... |
| Audit/SCA/secret scan | ... | ... | ... | ... |

Playwright e apenas para UI browser critica. API, cobertura backend, device,
data quality, ML eval e IaC plan entram somente quando o perfil exigir.

## Fluxo De Promocao

```text
change -> gates do perfil -> artefato imutavel -> aprovacao do canal
-> deploy/publish/promote/apply -> smoke/reconciliacao -> rollback/yank/replay/recovery
```

## Evidencia Por Execucao

| Comando | CWD | Exit code | Resultado | Artefato/EVD | Responsavel |
|---|---|---:|---|---|---|
| ... | ... | ... | ... | ... | ... |

## Pendencias E Excecoes

- Gate `N/A` + motivo:
- Excecao de cobertura/threshold:
- Vulnerabilidade/policy finding:
- Falta de ambiente/runner:
- Plano de rollback/yank/replay/recovery:
