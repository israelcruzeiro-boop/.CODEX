# Referencia DigitalOcean API e doctl

Base URL: `https://api.digitalocean.com/v2`
Auth: `Authorization: Bearer $DIGITALOCEAN_TOKEN`

Fonte oficial:
- API Apps: https://docs.digitalocean.com/reference/api/reference/apps/
- doctl: https://docs.digitalocean.com/reference/doctl/
- App Spec: https://docs.digitalocean.com/products/app-platform/reference/app-spec/

---

## Seguranca do Token

Regras:
- Nunca imprimir `DIGITALOCEAN_TOKEN`.
- Mascarar no maximo os ultimos 4 caracteres: `****abcd`.
- Pedir escopo minimo necessario.
- Operacoes de leitura antes de escrita.
- Confirmacao explicita antes de `PUT`, `POST`, `PATCH` ou `DELETE`.

Escopos conceituais:
- Leitura de apps: `app:read`.
- Atualizacao de apps: `app:update`.
- Criacao/delecao somente se o usuario pedir explicitamente.

---

## Autenticacao

```bash
curl -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  https://api.digitalocean.com/v2/account
```

Resposta esperada: `200`.

Erros:
- `401`: token invalido ou expirado.
- `403`: token sem permissao.
- `429`: rate limit. A API documenta limites por hora e por minuto; respeitar
  headers `ratelimit-*`.

---

## Apps

Listar apps:

```bash
curl -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  https://api.digitalocean.com/v2/apps
```

Buscar app:

```bash
curl -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  https://api.digitalocean.com/v2/apps/{id}
```

Buscar por nome:

```bash
curl -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  "https://api.digitalocean.com/v2/apps?name=my-app"
```

Atualizar app com app spec completo:

```bash
curl -X PUT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  https://api.digitalocean.com/v2/apps/{id} \
  -d @app-spec.json
```

Aviso: `PUT /v2/apps/{id}` deve preservar campos existentes. Sempre salvar uma
copia do app spec anterior antes de alterar.

---

## Instance Sizes

Listar tamanhos atuais de App Platform:

```bash
curl -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  https://api.digitalocean.com/v2/apps/tiers/instance_sizes
```

Buscar tamanho especifico:

```bash
curl -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  https://api.digitalocean.com/v2/apps/tiers/instance_sizes/apps-s-1vcpu-1gb
```

Use estes endpoints para validar snapshot de planos antes de recomendar custo.

---

## Regioes

```bash
curl -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  https://api.digitalocean.com/v2/apps/regions
```

Validar:
- frontend/backend/banco na mesma regiao quando latencia ou private networking
  importarem.
- disponibilidade do plano na regiao.

---

## Deploy e Restart

Criar novo deployment:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  https://api.digitalocean.com/v2/apps/{app_id}/deployments
```

Restart de componentes:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  https://api.digitalocean.com/v2/apps/{app_id}/restart \
  -d '{"components":["api"]}'
```

Mudancas de env/app spec normalmente exigem novo deploy ou restart. Confirmar no
estado do app apos a operacao.

---

## doctl

Autenticar:

```bash
doctl auth init
```

Listar apps:

```bash
doctl apps list
```

Obter app spec:

```bash
doctl apps spec get <app-id> > app.yaml
```

Atualizar app:

```bash
doctl apps update <app-id> --spec app.yaml
```

Listar tamanhos de Droplet:

```bash
doctl compute size list
```

Regra: `doctl apps update` tambem e escrita. Exigir confirmacao antes.

---

## Checklist de Escrita Segura

Antes:
- [ ] app spec atual salvo
- [ ] diff do app spec revisado
- [ ] secrets nao impressos
- [ ] component-level preferido para secrets
- [ ] scope/type corretos
- [ ] plano de rollback declarado
- [ ] confirmacao explicita recebida

Depois:
- [ ] app spec recuperado novamente
- [ ] deployment/restart verificado
- [ ] logs/eventos revisados
- [ ] smoke test executado quando possivel
- [ ] custo estimado atualizado
