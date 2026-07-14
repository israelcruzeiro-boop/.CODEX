# Patterns — Bugs Comuns no Stack Next.js / Express / Supabase / Vercel

> Referência rápida para o BUG_Agent_Debugger. Consultar na FASE 2 do diagnóstico.

---

## FRONTEND — Next.js / React

### BUG-PATTERN-F001 — Hydration Mismatch
```
Sintoma: "Text content does not match server-rendered HTML"
Causa:   Componente renderiza diferente no servidor vs cliente
         (ex: Date.now(), Math.random(), window, localStorage no render)
Fix:     Usar useEffect para código client-only
         Usar suppressHydrationWarning apenas quando inevitável
         Dynamic import com ssr: false para componentes client-only
```

### BUG-PATTERN-F002 — useEffect com Dependências Erradas
```
Sintoma: Estado não atualiza / atualiza infinitamente / dado desatualizado
Causa:   Array de dependências incompleto ou incorreto
Fix:     Usar eslint-plugin-react-hooks para detectar
         Verificar se funções dentro do efeito precisam ser memoizadas
         Considerar useCallback/useMemo se necessário
```

### BUG-PATTERN-F003 — Variável de Ambiente NEXT_PUBLIC_ Ausente
```
Sintoma: undefined no cliente para variável de env
Causa:   Variável não tem prefixo NEXT_PUBLIC_ (não exposta ao bundle)
         Variável não está no .env.local / Vercel dashboard
Fix:     Adicionar prefixo NEXT_PUBLIC_ para variáveis client-side
         Server-side pode acessar sem prefixo via process.env
         Verificar Vercel → Settings → Environment Variables
```

### BUG-PATTERN-F004 — Stale Closure em Event Handler
```
Sintoma: Handler usa valor antigo do estado
Causa:   Closure capturou referência antiga
Fix:     Usar forma funcional do setState: setState(prev => ...)
         Usar useRef para valores que precisam ser atuais no handler
```

### BUG-PATTERN-F005 — Erro Silenciado no Fetch
```
Sintoma: Request falha mas UI não mostra erro, dados ficam undefined
Causa:   try/catch vazio ou erro não propagado
Fix:     Sempre checar response.ok antes de parsear JSON
         Implementar error boundary ou error state no componente
         Garantir que Zod valida o response e lança erro em falha
```

### BUG-PATTERN-F006 — Race Condition em useEffect com Fetch
```
Sintoma: Dado mais antigo sobrescreve o mais novo após mudança rápida
Causa:   Múltiplas requests em flight, sem cancelamento
Fix:     Usar AbortController no cleanup do useEffect
         Usar flag isMounted para ignorar response de efeito desmontado
```

---

## BACKEND — Express / Vercel Functions

### BUG-PATTERN-B001 — CORS Bloqueando Request do Front
```
Sintoma: "CORS policy: No 'Access-Control-Allow-Origin'"
Causa:   Origin do front não está na whitelist do CORS
         Método OPTIONS (preflight) não tratado
Fix:     Verificar lista de origins permitidas no middleware CORS
         Garantir que OPTIONS retorna 200 com headers corretos
         Em Vercel: configurar headers no vercel.json se necessário
```

### BUG-PATTERN-B002 — JWT Expirado ou Inválido
```
Sintoma: 401 Unauthorized em todas as requests autenticadas
Causa:   Token expirado / secret errado / algoritmo diferente
Fix:     Verificar JWT_SECRET é o mesmo em todos os ambientes
         Verificar tempo de expiração do token
         Checar se refresh token está implementado e funcionando
         Inspecionar payload do JWT em jwt.io (sem expor em produção)
```

### BUG-PATTERN-B003 — Body Parser Não Configurado
```
Sintoma: req.body é undefined no handler
Causa:   Middleware express.json() não aplicado na rota
Fix:     Garantir app.use(express.json()) antes das rotas
         Em Vercel Functions: o body precisa ser parseado manualmente
         Verificar Content-Type: application/json no request
```

### BUG-PATTERN-B004 — Vercel Function Timeout
```
Sintoma: 504 Gateway Timeout após ~10 segundos
Causa:   Operação excede limite padrão de 10s (free/hobby)
Fix:     Otimizar query/operação para ser mais rápida
         Configurar maxDuration no vercel.json (até 60s no Pro)
         Considerar background job para operações longas
```

### BUG-PATTERN-B005 — Variável de Ambiente Indefinida em Produção
```
Sintoma: Funciona local, quebra em produção com undefined
Causa:   Variável existe no .env local mas não no Vercel dashboard
Fix:     Verificar Vercel → Settings → Environment Variables
         Confirmar que está no ambiente correto (Production/Preview/Development)
         Redeploy após adicionar variável (não recarrega automaticamente)
```

### BUG-PATTERN-B006 — Rate Limit Bloqueando Usuário Legítimo
```
Sintoma: 429 Too Many Requests para usuário normal
Causa:   Janela de rate limit muito restritiva
         IP compartilhado sendo penalizado
Fix:     Ajustar windowMs e max no express-rate-limit
         Implementar rate limit por usuário autenticado, não por IP
         Whitelist de IPs se necessário
```

---

## BANCO DE DADOS — Supabase / PostgreSQL

### BUG-PATTERN-D001 — RLS Bloqueando Acesso Legítimo
```
Sintoma: Query retorna [] vazio mesmo com dados existentes
         Ou erro: "new row violates row-level security policy"
Causa:   Policy RLS não permite o role atual acessar os dados
Fix:     Verificar se RLS está habilitado na tabela
         Checar as policies para o role correto (anon/authenticated)
         Testar query com service_role para confirmar dados existem
         Criar/corrigir policy que autorize o acesso necessário
```

### BUG-PATTERN-D002 — N+1 Query
```
Sintoma: Endpoint lento, muitas queries sendo disparadas
Causa:   Loop fazendo SELECT para cada item em vez de JOIN
Fix:     Substituir loop + SELECT por JOIN ou IN clause
         Usar select com relacionamentos no Supabase client
         Monitorar com pg_stat_statements
```

### BUG-PATTERN-D003 — Migration Não Aplicada
```
Sintoma: Coluna/tabela não existe, erro de schema
Causa:   Migration criada mas não executada no ambiente
Fix:     Verificar status das migrations
         Executar migration pendente no ambiente correto
         Nunca editar schema diretamente em produção sem migration
```

### BUG-PATTERN-D004 — Tipo de Dado Incompatível
```
Sintoma: Erro de cast / dado salvo incorretamente
Causa:   Frontend envia string, banco espera integer (ou vice-versa)
Fix:     Verificar tipo da coluna no banco
         Garantir que Zod schema no backend faz a coerção correta
         Validar payload antes de inserir
```

### BUG-PATTERN-D005 — Foreign Key Violation
```
Sintoma: "violates foreign key constraint"
Causa:   Tentando inserir referência para registro inexistente
         Tentando deletar registro referenciado por outro
Fix:     Verificar que o registro pai existe antes de inserir filho
         Implementar cascade delete se necessário
         Checar ordem das operações (criar pai antes do filho)
```

### BUG-PATTERN-D006 — Supabase Client com Permissão Errada
```
Sintoma: Operações administrativas falhando com 403
Causa:   Usando anon key onde precisa do service_role
Fix:     Operações admin/server-side: usar SUPABASE_SERVICE_ROLE_KEY
         Client-side: usar SUPABASE_ANON_KEY com RLS correto
         Nunca expor service_role key no frontend
```

---

## INTEGRAÇÃO / AMBIENTE

### BUG-PATTERN-I001 — Diferença de Comportamento Dev vs Produção
```
Sintoma: Funciona local, quebra no Vercel
Causas comuns:
  - Variável de ambiente ausente em produção
  - Dependência instalada como devDependency (não vai para produção)
  - Caminho de arquivo case-sensitive (Linux vs macOS)
  - Timeout de função serverless
  - Cold start de função
Fix:     Checar as causas na ordem acima
```

### BUG-PATTERN-I002 — CORS entre Dois Projetos Vercel
```
Sintoma: Front (projeto A) não consegue chamar back (projeto B)
Causa:   Origin do projeto A não está liberada no back do projeto B
Fix:     No backend, adicionar URL do frontend na lista de origins
         Lembrar que Preview URLs são dinâmicas — usar padrão regex se necessário
         Testar com curl para confirmar que é CORS e não outra coisa
```

### BUG-PATTERN-I003 — Webhook Não Recebido
```
Sintoma: Evento externo disparado mas backend não reage
Causa:   URL do webhook desatualizada
         Endpoint não está acessível publicamente
         Payload não está sendo parseado corretamente
         Verificação de assinatura falhando
Fix:     Confirmar URL do webhook no provider externo
         Testar endpoint com ferramenta como webhook.site
         Verificar logs do servidor para ver se request chega
         Temporariamente desabilitar verificação de assinatura para debug
```
