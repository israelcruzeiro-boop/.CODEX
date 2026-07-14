# Troubleshooting — Vercel & Deploy

> Consultar na FASE 2 quando o bug suspeitar de problema de ambiente ou deploy.

---

## Erros Comuns de Deploy

### Build Falhou

```
Diagnóstico:
1. Ler o build log completo no Vercel dashboard
2. O erro mais relevante geralmente está no final do log
3. Erros comuns:

  "Module not found: Can't resolve 'X'"
  → Dependência não instalada ou import com caminho errado
  → Verificar package.json e se está em dependencies (não devDependencies)

  "Type error: ..."
  → Erro TypeScript que passa local mas não no build
  → Rodar: npm run build localmente para replicar
  → Verificar tsconfig.json (strict mode ativo?)

  "Export 'X' (imported as 'Y') was not found in 'Z'"
  → Named export não existe no módulo
  → Verificar se o export foi renomeado ou removido

  "Cannot read properties of undefined"
  → Variável de ambiente undefined no build
  → Verificar NEXT_PUBLIC_ prefix e Vercel env vars
```

### Vercel Function Errors

```
502 Bad Gateway
→ Função crashou durante execução
→ Verificar logs em: Vercel Dashboard → Deployment → Functions → Logs
→ Adicionar try/catch para capturar e logar o erro

504 Gateway Timeout
→ Função excedeu o tempo limite
→ Limite padrão: 10s (Hobby), 60s (Pro), 900s (Enterprise)
→ Configurar em vercel.json:
   {
     "functions": {
       "api/rota-lenta.ts": {
         "maxDuration": 60
       }
     }
   }

500 Internal Server Error
→ Erro não tratado na função
→ Verificar logs com detalhes
→ Garantir que todos os paths têm return com response
```

---

## Variáveis de Ambiente no Vercel

### Estrutura

```
Vercel → Settings → Environment Variables

Ambientes disponíveis:
  ✅ Production    → branch main/master
  ✅ Preview       → pull requests e outros branches
  ✅ Development   → vercel dev local

Regras críticas:
  - Variável adicionada não recarrega deploy existente
  - Sempre fazer redeploy após adicionar/alterar variável
  - NEXT_PUBLIC_ = exposta no bundle do cliente
  - Sem prefixo = apenas server-side
  - Nunca commitar .env.local no git (está no .gitignore)
```

### Checklist de Variáveis por Ambiente

```
Verificar se as seguintes variáveis estão configuradas em TODOS os ambientes:

BACKEND (Express / Vercel Functions):
  [ ] DATABASE_URL ou SUPABASE_URL
  [ ] SUPABASE_SERVICE_ROLE_KEY
  [ ] JWT_SECRET
  [ ] NODE_ENV

FRONTEND (Next.js):
  [ ] NEXT_PUBLIC_SUPABASE_URL
  [ ] NEXT_PUBLIC_SUPABASE_ANON_KEY
  [ ] NEXT_PUBLIC_API_URL (URL do backend)

INTEGRAÇÕES (se aplicável):
  [ ] PAGAR_ME_API_KEY
  [ ] GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET
  [ ] RESEND_API_KEY (ou similar para email)
```

### Como Debugar Variável Indefinida

```typescript
// Temporário para debug — REMOVER após confirmar
console.log('[DEBUG] Env vars:', {
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL ? '✅ SET' : '❌ MISSING',
  apiUrl: process.env.NEXT_PUBLIC_API_URL ? '✅ SET' : '❌ MISSING',
})

// No servidor (API route / Express):
console.log('[DEBUG] Server env:', {
  jwtSecret: process.env.JWT_SECRET ? '✅ SET' : '❌ MISSING',
  serviceRole: process.env.SUPABASE_SERVICE_ROLE_KEY ? '✅ SET' : '❌ MISSING',
})
```

---

## Diferenças Dev vs Produção (armadilhas comuns)

```
1. Case-sensitivity nos imports
   Local (macOS):  import Button from './Button'  ← funciona
   Produção (Linux): import Button from './button' ← quebra
   Fix: sempre usar o case exato do nome do arquivo

2. devDependencies em produção
   Local: todas as deps instaladas
   Produção: apenas dependencies, não devDependencies
   Fix: mover para dependencies o que for usado no build/runtime

3. Caminho relativo vs absoluto
   Local: '../../../components/Button' funciona mas é frágil
   Fix: configurar path aliases no tsconfig.json (@/components/Button)

4. Porta hardcoded
   Local: http://localhost:3001/api
   Produção: https://meu-backend.vercel.app/api
   Fix: sempre usar NEXT_PUBLIC_API_URL via variável de ambiente

5. Vercel Function cold start
   Sintoma: primeira request lenta (~500ms-2s), depois rápida
   Não é bug — é comportamento esperado de serverless
   Para mitigar: Vercel Pro tem "Fluid compute" que reduz cold starts
```

---

## Logs em Produção no Vercel

```
Acessar logs:
  Vercel Dashboard → Projeto → Deployments → [deployment] → Functions

Filtros úteis:
  - Por função específica
  - Por nível: error / warn / info
  - Por período de tempo

Boas práticas de logging:
```

```typescript
// Estruturado para facilitar filtro nos logs Vercel
console.log(JSON.stringify({
  level: 'error',
  event: 'auth_failed',
  userId: req.user?.id,
  endpoint: req.path,
  message: error.message,
  timestamp: new Date().toISOString(),
}))

// Evitar:
console.log('erro:', error) // difícil de filtrar
console.log(error)          // pode expor dados sensíveis
```

---

## vercel.json — Configurações de Debug

```json
{
  "functions": {
    "api/*.ts": {
      "maxDuration": 30
    },
    "api/relatorio.ts": {
      "maxDuration": 60
    }
  },
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "https://meu-frontend.vercel.app" },
        { "key": "Access-Control-Allow-Methods", "value": "GET,POST,PUT,DELETE,PATCH,OPTIONS" },
        { "key": "Access-Control-Allow-Headers", "value": "Content-Type, Authorization" }
      ]
    }
  ],
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://meu-backend.vercel.app/api/:path*"
    }
  ]
}
```

---

## Checklist Pré-Deploy

```
[ ] npm run build passa localmente sem erros
[ ] npm run lint não reporta erros críticos
[ ] Variáveis de ambiente do novo feature adicionadas no Vercel
[ ] Migration do banco aplicada no ambiente de destino
[ ] Testado em staging/preview antes de produção
[ ] Rollback planejado (deployment anterior identificado no Vercel)
[ ] Sem console.log de debug no código
[ ] Sem variáveis hardcoded (API keys, URLs, secrets)
```
