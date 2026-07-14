# Referencia DigitalOcean App Platform

Fonte base: documentacao oficial DigitalOcean consultada em 2026-05-20.
Antes de operar em producao, confirmar na documentacao atual.

Links principais:
- App Platform: https://docs.digitalocean.com/products/app-platform/
- Environment variables: https://docs.digitalocean.com/products/app-platform/how-to/use-environment-variables/
- App Spec: https://docs.digitalocean.com/products/app-platform/reference/app-spec/
- Limits: https://docs.digitalocean.com/products/app-platform/details/limits/
- Manage Databases in App Platform: https://docs.digitalocean.com/products/app-platform/how-to/manage-databases/

---

## App Spec: variaveis

Campos de `envs[]`:

```yaml
envs:
  - key: DATABASE_URL
    value: ${db.DATABASE_URL}
    scope: RUN_TIME
    type: SECRET
```

Regras:
- `key` deve seguir `^[_A-Za-z][_A-Za-z0-9]*$`.
- `scope`: `RUN_TIME`, `BUILD_TIME`, `RUN_AND_BUILD_TIME`.
- `type`: `GENERAL` ou `SECRET`.
- `SECRET` e criptografado no primeiro envio. Em envs ja salvos, a API pode
  retornar valor criptografado (`EV[...]`), nao o segredo puro.

---

## App-Level vs Component-Level

App-level envs:
- Disponiveis para todos os componentes.
- Disponiveis em build e runtime conforme scope.
- Devem ser usadas apenas para configuracao realmente compartilhada.

Component-level envs:
- Pertencem a `services[]`, `static_sites[]`, `workers[]`, `jobs[]` ou `functions[]`.
- Se tiverem a mesma `key` de uma app-level env, prevalecem no componente.
- Sao o padrao preferido para secrets com dono claro.

---

## Scopes

| Scope | Uso correto |
|---|---|
| `BUILD_TIME` | build command, bundle frontend, geracao estatica |
| `RUN_TIME` | processo em execucao, API, worker, job |
| `RUN_AND_BUILD_TIME` | quando o mesmo valor e necessario nos dois momentos |

Dockerfile: variaveis de build podem exigir `--build-arg`. Bindable variables
podem nao estar disponiveis no build de Dockerfile; valide no fluxo real.

---

## Bindable Variables

Use bindables para evitar hardcode de dominios e credenciais geradas pela
plataforma.

App-wide:
- `${APP_DOMAIN}` -> dominio primario.
- `${APP_URL}` -> URL primaria em HTTP/HTTPS.
- `${APP_ID}` -> ID da app.

Componentes:
- `${_self.PRIVATE_DOMAIN}` -> dominio interno para comunicacao entre services.
- `${_self.PRIVATE_URL}` -> URL interna com porta.
- `${_self.PRIVATE_PORT}` -> porta HTTP interna.
- `${_self.PUBLIC_URL}` -> URL publica do componente.
- `${_self.PUBLIC_ROUTE_PATH}` -> rota publica do componente.
- `${_self.COMMIT_HASH}` -> hash do commit usado no build.

Bancos:
- `${db.HOSTNAME}`
- `${db.PORT}`
- `${db.USERNAME}`
- `${db.PASSWORD}`
- `${db.DATABASE}`
- `${db.DATABASE_URL}`
- `${db.DATABASE_PRIVATE_URL}`
- `${db.CA_CERT}`

Troque `db` pelo nome do componente de banco. O prefixo antes do ponto em
`${prefixo.VARIAVEL}` tem limite de 32 caracteres.

Preferencia:
- Mesmo VPC/regiao: usar private URL quando disponivel.
- Producao: Managed Database.
- Desenvolvimento/prototipo: Dev Database pode ser aceito com aviso.

---

## Limites Operacionais Relevantes

- O filesystem local de containers App Platform nao e persistente.
- Filesystem local tem limite de 4 GiB e deve ser usado so para temporarios.
- Builds tem limite de recursos e timeout; se estourar, considerar build externo
  via CI ou imagem/container.
- Uploads para apps tem timeout; fluxos grandes devem usar object storage.
- App Platform nao suporta volumes persistentes.

Implicacao para variaveis:
- Uploads devem apontar para Spaces/S3, nao para disco local.
- Paths locais persistentes em env vars sao suspeitos.
- Jobs longos precisam timeout/configuracao adequada.

---

## Bancos no App Platform

Tipos:
- Dev Database: leve, desenvolvimento, PostgreSQL, sem garantias de producao.
- Managed Database: producao, engines gerenciadas, backups, failover e recursos
  avancados.

Checks:
- `DATABASE_URL` deve estar somente no backend/service/worker/job que usa banco.
- Se frontend precisa status publico do banco, exponha via API, nao via env.
- Para Prisma, validar tambem `DIRECT_URL` quando migrations exigirem conexao
  direta.
- Para pools, usar bindable especifico do pool quando existir.

---

## Alertas Minimos

Para producao, o app spec deve considerar:
- `DEPLOYMENT_FAILED`
- `DOMAIN_FAILED`
- `CPU_UTILIZATION`
- `MEM_UTILIZATION`
- `RESTART_COUNT`
- `REQUEST_RATE_PER_SECOND` quando aplicavel

Sem alertas, o agente deve registrar lacuna operacional.
