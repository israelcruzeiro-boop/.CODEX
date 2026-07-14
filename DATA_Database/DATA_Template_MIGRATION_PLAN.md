# MIGRATION_PLAN

Plano generico para uma mudanca de schema/dados com seguranca e rollback.

## Contexto
- Banco / versao:
- Ferramenta de migration / ORM:
- Diretorio canonico de migrations:
- Convencao de nome dos arquivos:
- Ambiente alvo: dev / staging / production
- Tabelas afetadas e volume estimado:

## Objetivo
- O que muda e por que:
- Tipo: schema (DDL) / dados (DML/backfill) / ambos

## Risco
- Reversivel? sim / nao (se nao, justificar)
- Destrutivo? sim / nao
- Tabela grande / lock / janela necessaria?
- Toca producao com dados/usuarios ativos?
- Classificacao: baixo / medio / alto

## Estrategia
- [ ] Direta
- [ ] Expand/contract (adiciona -> migra -> remove em releases separados)
- [ ] Backfill em lotes (idempotente)
- [ ] Indice concorrente / sem lock pesado

## Passos
1. Arquivo(s) de migration no diretorio canonico:
2. DDL (up):
3. Backfill/DML (idempotente, em lotes):
4. Constraints/indices:
5. Verificacao pos-migration (contagens, integridade, smoke de queries):

## Rollback (down)
- Passos de reversao:
- Ponto de restauracao / backup:
- Se irreversivel: motivo e mitigacao

## Replicacao Do Banco
- Comando ou procedimento para aplicar migrations em novo ambiente:
- Seeds ou dados estruturais necessarios:
- Backfills necessarios:
- Lacunas conhecidas para recriar o banco:

## Isolamento Multi-Tenant
- Chave de tenant garantida? filtros/RLS?

## Checklist Antes De Aplicar
- [ ] Migration salva no diretorio canonico declarado.
- [ ] Testado em ambiente equivalente.
- [ ] Backup/ponto de restauracao para mudanca de risco.
- [ ] Rollback testado.
- [ ] Ordem de deploy coordenada com a aplicacao (`@O`/`@REL`).
- [ ] PII/retencao revisadas com `@S`/`@GOV` quando aplicavel.
- [ ] `STATUS.md` atualizado com migration, ambiente alvo e lacunas de replicacao.
