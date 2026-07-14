# Checklist de Ambiente — Diagnóstico de Configuração

> Consultar quando o bug suspeita de problema de ambiente, não de código.
> A regra: **descarte ambiente antes de olhar código**.

---

## Checklist Rápido de Ambiente

```
GERAL:
  [ ] O erro acontece em todos os ambientes ou só em um?
  [ ] O erro começou após um deploy ou mudança de configuração?
  [ ] Outros desenvolvedores/usuários reproduzem o mesmo erro?

VARIÁVEIS DE AMBIENTE:
  [ ] .env.local existe e tem todas as variáveis necessárias?
  [ ] Vercel tem as variáveis no ambiente correto (Prod/Preview/Dev)?
  [ ] Alguma variável foi adicionada recentemente e não tem redeploy?
  [ ] JWT_SECRET é o mesmo entre backend e qualquer serviço que valida?

NODE / NPM:
  [ ] Versão do Node é compatível? (verificar .nvmrc ou engines no package.json)
  [ ] node_modules está atualizado? (npm install após pull)
  [ ] Alguma dependência foi atualizada com breaking change?
  [ ] package-lock.json está em sync com package.json?

BANCO DE DADOS:
  [ ] Connection string aponta para o banco correto (dev vs prod)?
  [ ] Migrations pendentes foram aplicadas?
  [ ] Usuário do banco tem permissões necessárias?
  [ ] Supabase project está ativo (não pausado por inatividade)?

REDE:
  [ ] URL do backend está correta no frontend?
  [ ] Backend está deployado e acessível?
  [ ] Não há firewall/VPN bloqueando?
```

---

## Mapa de Ambientes do Projeto

```
DESENVOLVIMENTO LOCAL:
  Frontend:  http://localhost:3000
  Backend:   http://localhost:3001 (ou porta configurada)
  Banco:     Supabase project DEV (URL no .env.local)
  Envs:      .env.local (nunca commitar)

PREVIEW (Vercel):
  Frontend:  https://projeto-git-branch-user.vercel.app
  Backend:   https://backend-git-branch-user.vercel.app (se separado)
  Banco:     Supabase project STAGING (idealmente separado do prod)
  Envs:      Vercel → Environment Variables → Preview

PRODUÇÃO:
  Frontend:  https://www.dominio.com.br
  Backend:   https://api.dominio.com.br (ou backend.vercel.app)
  Banco:     Supabase project PROD
  Envs:      Vercel → Environment Variables → Production
```

---

## Diagnóstico por Sintoma de Ambiente

### "Funciona local, quebra no Vercel"

```
Investigar nesta ordem:
1. Variável de ambiente ausente no Vercel
2. Dependência em devDependencies (não vai para produção)
3. Import com case errado (macOS é case-insensitive, Linux não)
4. Caminho hardcoded localhost:PORTA em vez de variável de env
5. Timeout de Vercel Function (10s padrão)
6. Diferença de versão Node (verificar .nvmrc vs Vercel settings)
7. Build error silencioso (verificar build logs no Vercel dashboard)
```

### "Funciona em produção, quebra local"

```
Investigar nesta ordem:
1. .env.local não tem a variável de produção (esperado, mas confirmar)
2. Migration de produção não aplicada localmente
3. Dado de produção necessário não existe localmente
4. Versão diferente de dependência entre local e deployed
```

### "Funciona para mim, não funciona para o cliente"

```
Investigar nesta ordem:
1. Cache do browser do cliente (pedir para limpar)
2. Sessão/JWT expirado do cliente
3. Permissão RLS baseada em role/user_id do cliente
4. Dado específico do cliente causando edge case
5. Versão antiga do app em cache (service worker?)
6. Localização/timezone do cliente afetando algo
```

### "Funcionou, parou de funcionar sem mudança de código"

```
Investigar nesta ordem:
1. Supabase project pausado (plano free pausa após inatividade)
2. API key/token de terceiro expirou
3. Cota de terceiro atingida (rate limit da API externa)
4. Certificado SSL expirado
5. DNS alterado
6. Dependência externa com breaking change (atualização automática?)
```

---

## Comandos de Verificação de Ambiente

```bash
# Verificar versão do Node
node --version

# Verificar variáveis de ambiente carregadas (sem expor valores)
node -e "
const vars = ['NEXT_PUBLIC_API_URL', 'NEXT_PUBLIC_SUPABASE_URL', 'JWT_SECRET'];
vars.forEach(v => console.log(v + ':', process.env[v] ? '✅ SET' : '❌ MISSING'));
" --env-file=.env.local

# Verificar se backend está acessível
curl -I https://SEU_BACKEND_URL/health

# Verificar se frontend builda sem erro
npm run build 2>&1 | tail -30

# Verificar dependências desatualizadas
npm outdated

# Reinstalar dependências do zero (última opção)
rm -rf node_modules package-lock.json && npm install
```
