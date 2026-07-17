# PROJECT - [NOME DO PROJETO]

## Visao

**Objetivo:** [o que o sistema resolve]
**Publico-alvo:** [quem usa]
**Resultado esperado:** [como sabemos que deu certo]

## Arquitetura

**Frontend:** [stack]
**Backend:** [stack]
**Banco:** [stack]
**Hospedagem:** [onde roda]
**Integracoes:** [auth, pagamentos, email, storage, IA, etc.]
**AS-IS:** `ARCHITECTURE.md` derivado do codigo, quando houver implementacao
**TO-BE:** `TARGET_ARCHITECTURE.md` + ADRs para decisoes ainda nao implementadas
**Mapa de padroes:** `PATTERN_MAP.md`

## Fronteiras

- Frontend:
- Backend:
- Banco:
- Workers/jobs:
- Terceiros:

## Dominios De Problema

| Dominio | Responsabilidade e invariantes | Owner | Contratos/consumidores |
|---|---|---|---|
| ... | ... | ... | ... |

## Catalogo De Modulos

| Modulo | Dominio/owner | API publica | Dados possuidos | Dependencias permitidas | Eventos/consumidores | Fitness gate |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |

## Fluxos Criticos

- [ ] Auth
- [ ] Cadastro/onboarding
- [ ] Fluxo principal
- [ ] Pagamento/checkout, se houver
- [ ] Admin, se houver
- [ ] Deploy e rollback

## Regras de Producao

- Idempotencia:
- Deduplicacao:
- Rate limit:
- Paginacao:
- Observabilidade:
- Backups/migrations:
- Lockfiles do backend:
- Audit de dependencias e Dependabot:
- Metas de cobertura por artefato/risco:
- Testes de sistema/E2E aplicaveis e ferramenta observada:
- Provedor e pipeline CI/CD/release observados:
