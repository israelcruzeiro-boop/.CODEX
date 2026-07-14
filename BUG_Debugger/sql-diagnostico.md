# SQL — Queries de Diagnóstico (Supabase / PostgreSQL)

> Consultar na FASE 2C do diagnóstico. Executar via SQL Editor do Supabase.

---

## Inspeção de Schema

```sql
-- Listar todas as tabelas do schema public
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Estrutura completa de uma tabela
SELECT
  column_name,
  data_type,
  character_maximum_length,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'NOME_DA_TABELA'
ORDER BY ordinal_position;

-- Constraints da tabela (PK, FK, UNIQUE, CHECK)
SELECT
  tc.constraint_name,
  tc.constraint_type,
  kcu.column_name,
  ccu.table_name AS foreign_table,
  ccu.column_name AS foreign_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
LEFT JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name
WHERE tc.table_name = 'NOME_DA_TABELA';

-- Indexes da tabela
SELECT
  indexname,
  indexdef
FROM pg_indexes
WHERE tablename = 'NOME_DA_TABELA';
```

---

## Inspeção de RLS

```sql
-- Verificar se RLS está habilitado por tabela
SELECT
  schemaname,
  tablename,
  rowsecurity AS rls_enabled,
  forcerowsecurity AS rls_forced
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Listar todas as policies de uma tabela
SELECT
  policyname,
  cmd,          -- SELECT, INSERT, UPDATE, DELETE, ALL
  roles,        -- quais roles se aplicam
  qual,         -- condição USING (leitura)
  with_check    -- condição WITH CHECK (escrita)
FROM pg_policies
WHERE tablename = 'NOME_DA_TABELA'
ORDER BY cmd, policyname;

-- Listar todas as policies de todas as tabelas
SELECT
  tablename,
  policyname,
  cmd,
  roles
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, cmd;

-- Testar acesso como role específico
SET role authenticated;
SELECT * FROM NOME_DA_TABELA LIMIT 5;
RESET role;

-- Verificar user/role atual
SELECT current_user, session_user;
```

---

## Diagnóstico de Performance

```sql
-- Queries mais lentas (requer pg_stat_statements habilitado no Supabase)
SELECT
  query,
  calls,
  round(mean_exec_time::numeric, 2) AS mean_ms,
  round(total_exec_time::numeric, 2) AS total_ms,
  rows
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Tabelas com mais dead tuples (candidatas a VACUUM)
SELECT
  schemaname,
  relname AS table_name,
  n_dead_tup AS dead_tuples,
  n_live_tup AS live_tuples,
  last_autovacuum,
  last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 10;

-- Tamanho das tabelas
SELECT
  table_name,
  pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) AS total_size
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;

-- Verificar se index está sendo usado
EXPLAIN ANALYZE
SELECT * FROM NOME_DA_TABELA WHERE coluna = 'valor';
-- Procurar: "Index Scan" (bom) vs "Seq Scan" (potencial problema em tabelas grandes)
```

---

## Diagnóstico de Dados

```sql
-- Contar registros com filtros
SELECT COUNT(*) FROM NOME_DA_TABELA WHERE condicao = true;

-- Verificar duplicatas
SELECT coluna, COUNT(*) as qtd
FROM NOME_DA_TABELA
GROUP BY coluna
HAVING COUNT(*) > 1
ORDER BY qtd DESC;

-- Verificar nulls em colunas críticas
SELECT
  COUNT(*) AS total,
  COUNT(coluna_critica) AS com_valor,
  COUNT(*) - COUNT(coluna_critica) AS nulos
FROM NOME_DA_TABELA;

-- Amostra dos dados mais recentes
SELECT *
FROM NOME_DA_TABELA
ORDER BY created_at DESC
LIMIT 10;

-- Verificar integridade referencial manualmente
SELECT f.*
FROM tabela_filha f
LEFT JOIN tabela_pai p ON f.foreign_key_id = p.id
WHERE p.id IS NULL;
-- Resultado não vazio = registros órfãos (FK violation potencial)
```

---

## Diagnóstico de Migrations

```sql
-- Verificar migrations aplicadas (Supabase usa schema_migrations)
SELECT version, inserted_at
FROM supabase_migrations.schema_migrations
ORDER BY inserted_at DESC
LIMIT 20;

-- Verificar se coluna existe antes de migration
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'NOME_DA_TABELA'
  AND column_name = 'NOME_DA_COLUNA';
-- Resultado vazio = coluna não existe ainda

-- Verificar se tabela existe
SELECT EXISTS (
  SELECT FROM information_schema.tables
  WHERE table_schema = 'public'
    AND table_name = 'NOME_DA_TABELA'
) AS tabela_existe;
```

---

## Diagnóstico de Funções e Triggers

```sql
-- Listar funções do schema public
SELECT
  routine_name,
  routine_type,
  data_type AS return_type
FROM information_schema.routines
WHERE routine_schema = 'public'
ORDER BY routine_name;

-- Listar triggers ativos
SELECT
  trigger_name,
  event_manipulation AS evento,
  event_object_table AS tabela,
  action_timing AS timing,
  action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY event_object_table, trigger_name;
```

---

## Operações de Emergência (usar com extremo cuidado)

```sql
-- Desabilitar RLS temporariamente para debug (NUNCA em produção)
-- ALTER TABLE nome_tabela DISABLE ROW LEVEL SECURITY;
-- (Reabilitar logo após: ALTER TABLE nome_tabela ENABLE ROW LEVEL SECURITY;)

-- Ver todas as conexões ativas
SELECT pid, usename, application_name, state, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY state;

-- Cancelar query específica (substituir PID)
-- SELECT pg_cancel_backend(PID);

-- Terminar conexão específica (mais agressivo)
-- SELECT pg_terminate_backend(PID);
```

> ⚠️ As operações de emergência estão comentadas propositalmente.
> Descomentar apenas quando necessário e com plena consciência do impacto.
