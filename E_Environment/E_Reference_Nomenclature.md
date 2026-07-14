# Nomenclatura De Variaveis De Ambiente

Referencia generica para nomes, escopos e riscos de variaveis. Adapte a stack
real do projeto.

---

## Regras Gerais

| Regra | Descricao | Exemplo |
|---|---|---|
| UPPER_SNAKE_CASE | Nome em maiusculo com underscore | `DATABASE_URL` |
| Sem espacos/hifens | Use underscore como separador | `API_BASE_URL` |
| Sem digito inicial | Evita incompatibilidade entre shells/providers | `API_V2_KEY` |
| Nome sem valor | Nome nao deve conter segredo | `PAYMENT_SECRET`, nao `STRIPE_SK_LIVE_...` |

---

## Prefixos Publicos

Alguns frameworks exigem prefixo para expor variaveis ao cliente. Qualquer
variavel com estes prefixos deve ser tratada como publica:

- `NEXT_PUBLIC_`
- `VITE_`
- `EXPO_PUBLIC_`
- `PUBLIC_`
- `REACT_APP_`
- outros prefixos definidos pelo framework do projeto

Regra: segredo nunca usa prefixo publico.

---

## Escopos

| Escopo | Pode conter secret? | Exemplos |
|---|---|---|
| Browser/frontend | Nao | URL publica, feature flag publica, chave publishable |
| Mobile app | Nao, app empacotado e publico | URL publica, chave publishable |
| Backend/API | Sim | DB URL, JWT secret, service role, private API key |
| Worker/job/cron | Sim | Queue secret, webhook secret, DB URL |
| CI/CD | Sim, com menor privilegio | deploy token, package token |
| Build-time | Depende; cuidado com embed no bundle | flags, DSN publico, build metadata |

---

## Categorias Comuns

### URLs Publicas

```text
APP_URL
API_BASE_URL
PUBLIC_API_URL
```

Use prefixo publico somente quando o cliente precisa ler.

### Banco De Dados

```text
DATABASE_URL
DIRECT_DATABASE_URL
READ_REPLICA_DATABASE_URL
```

Nunca expor em frontend/mobile.

### Auth E Sessao

```text
JWT_SECRET
SESSION_SECRET
REFRESH_TOKEN_SECRET
AUTH_ISSUER
AUTH_AUDIENCE
OAUTH_CLIENT_ID
OAUTH_CLIENT_SECRET
```

`CLIENT_ID` pode ser publico dependendo do provider. `CLIENT_SECRET` nunca.

### Webhooks

```text
PAYMENT_WEBHOOK_SECRET
AUTH_WEBHOOK_SECRET
INTEGRATION_WEBHOOK_SECRET
```

Webhook secret fica no backend/worker que valida assinatura.

### Pagamentos

```text
PAYMENT_PUBLISHABLE_KEY
PAYMENT_SECRET_KEY
PAYMENT_WEBHOOK_SECRET
```

Publishable pode ir ao cliente se o gateway permitir. Secret fica no servidor.

### Storage

```text
STORAGE_BUCKET
STORAGE_REGION
STORAGE_ACCESS_KEY_ID
STORAGE_SECRET_ACCESS_KEY
```

Access secret fica no servidor/CI. Cliente deve usar URL assinada ou token
temporario quando aplicavel.

### Observabilidade

```text
SENTRY_DSN
SENTRY_AUTH_TOKEN
OTEL_EXPORTER_OTLP_ENDPOINT
OTEL_EXPORTER_OTLP_HEADERS
```

DSN frontend pode ser publico conforme ferramenta. Auth token de build/upload nao.

### IA / APIs Externas

```text
OPENAI_API_KEY
MAPS_API_KEY
EMAIL_API_KEY
SMS_API_KEY
```

Validar se a chave e publica, restrita por dominio/app ou secreta. Chave de IA
normalmente fica no backend.

---

## Cross-Checks

- URL do cliente aponta para API do mesmo ambiente?
- CORS/origin/callback URLs combinam com dominios reais?
- Chaves test/live nao se misturam?
- Secrets privados existem apenas em runtime privado?
- Variaveis publicas nao contem token, senha, private key, service role ou DB URL?
- CI tem variaveis necessarias para testar/buildar?
- Provider injeta variaveis automaticas que nao devem ser redefinidas?

---

## Checklist

- [ ] Nomes em UPPER_SNAKE_CASE.
- [ ] `.env.example` sem valores reais.
- [ ] Publico versus secreto classificado.
- [ ] Runtime consumidor identificado.
- [ ] Ambientes separados.
- [ ] Redeploy/restart necessario documentado.
- [ ] Secrets mascarados em logs e relatorios.
