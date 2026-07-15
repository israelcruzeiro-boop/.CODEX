# P_Method_CacheStrategy - Estrategia Canonica de Cache

Metodo canonico do kit para desenhar, implementar e validar cache. Complementa
o `P_Agent_PerformanceValidator.toml` (que fiscaliza) com prescricao: o executor
que precisa desenhar um cache encontra aqui o norte antes do validador reprovar.

Regra de ouro: **cache e uma decisao de arquitetura, nao um remendo.** Todo
cache tem quatro perguntas obrigatorias: o que guarda, com qual chave, por
quanto tempo e como invalida. Sem as quatro respostas, nao ha cache aprovavel.

---

## Camadas De Cache (escolher a mais externa que resolve)

| Camada | Exemplos | Quando usar | Risco tipico |
|---|---|---|---|
| HTTP/navegador | `Cache-Control`, `ETag`, `Last-Modified` | Assets estaticos, GETs publicos e idempotentes | Header errado cacheia dado privado |
| CDN/edge | CloudFront, Cloudflare, Vercel edge | Conteudo publico de leitura intensa | Invalidar demora ou custa; versionar URL resolve |
| Aplicacao | Redis, Memcached, in-memory | Resultado caro por usuario/tenant, sessao, rate limit | Chave sem tenant vaza dado; stampede |
| Banco/query | Materialized view, query cache, read replica | Agregacoes pesadas, dashboards | Dado defasado apresentado como atual |
| Cliente (frontend) | React Query, SWR, Apollo, service worker | Server state em UI | Invalidacao esquecida pos-mutacao; SW segurando versao antiga |

Regras de escolha:

1. Comece pela camada mais externa que resolve: HTTP/CDN antes de Redis, Redis
   antes de view materializada. Camada externa e mais barata e mais simples.
2. Nao empilhe camadas para o mesmo dado sem declarar quem e a fonte de verdade
   e em que ordem invalidam.
3. Cache in-memory de processo so vale para dado imutavel ou por-instancia;
   com multiplas instancias, coerencia exige camada compartilhada.

## Chaves

- Toda chave declara escopo: `recurso:versao:tenant:usuario:parametros`.
- Dado por usuario/tenant/role SEMPRE inclui usuario/tenant/role na chave.
  Ausencia disso e vazamento entre usuarios: bloqueio de `@S` e `final_validator`.
- Parametros que mudam o resultado (filtros, periodo, idioma, permissao) entram
  na chave. Parametro fora da chave = bug de dado errado, nao de performance.
- Versionar a chave (`v2:...`) quando o formato do valor mudar; nunca fazer
  deploy que le formato antigo de cache sem plano de migracao ou flush.

## TTL E Invalidacao

- Todo cache tem TTL explicito. Cache sem TTL e vazamento de memoria com prazo.
- TTL e o teto de defasagem aceitavel para o negocio, nao um numero magico:
  declarar "este dado pode ficar X minutos defasado porque ...".
- Invalidacao por evento (write-through/delete-on-write) para dado que o proprio
  sistema muda; TTL curto para dado de terceiros que muda sem avisar.
- Toda mutacao lista quais chaves/tags invalida. Mutacao sem plano de
  invalidacao e a causa numero um de "salvei mas nao atualizou".
- No cliente: toda mutacao invalida ou atualiza as queries afetadas
  (`invalidateQueries`/tag). Service worker/PWA precisa de estrategia de update
  declarada (skipWaiting, prompt de reload) para nao segurar versao antiga.

## HTTP E CDN

- `Cache-Control` explicito em toda resposta: `no-store` para dado sensivel,
  `private` para dado por usuario, `public, max-age` so para conteudo publico.
- `ETag`/`Last-Modified` para GETs que valem revalidacao condicional.
- `stale-while-revalidate` quando servir dado levemente defasado for aceitavel
  e a latencia importar.
- Nunca cachear em CDN resposta autenticada sem `Vary` correto e decisao
  explicita; o padrao seguro e nao cachear.
- Asset com hash no nome (`app.3f2a.js`) recebe `immutable`; invalidacao de CDN
  por purge e excecao, versionamento de URL e a regra.

## Stampede E Concorrencia

- Hot key com recomputo caro precisa de protecao contra stampede: lock/single
  flight, request coalescing ou TTL com jitter.
- Expiracao em massa sincronizada (mesmo TTL para tudo, criado no mesmo deploy)
  derruba origem: usar jitter.
- Fallback declarado quando o cache falha: degradar para origem com timeout e
  circuit breaker, nunca erro 500 porque o Redis caiu.

## Seguranca (delegacao @S)

- Dado sensivel (PII, financeiro, medico) so entra em cache com decisao
  registrada, TTL curto e criptografia/`no-store` conforme a camada.
- Isolamento por usuario/tenant/role na chave e verificavel por teste negativo:
  usuario A nao pode receber cache do usuario B.
- Logout/troca de permissao invalida caches de sessao e autorizacao.

## Observabilidade (delegacao @O)

- Medir hit ratio, latencia com/sem cache e tamanho antes de declarar vitoria.
- Cache sem metrica de hit ratio e supersticao: nao da para saber se ajuda.
- Alertar em hit ratio despencando (invalidacao quebrada) e em memoria/evicao
  anomala.

## Checklist De Aprovacao (gates para @P, @S, @V, @GSD)

- [ ] O que guarda, chave, TTL e invalidacao declarados por escrito.
- [ ] Chave inclui usuario/tenant/role quando o dado e por usuario.
- [ ] Toda mutacao lista as chaves/queries que invalida.
- [ ] Camada escolhida justificada (a mais externa que resolve).
- [ ] Baseline medido antes; metrica de hit ratio depois.
- [ ] Stampede considerado em hot key com recomputo caro.
- [ ] Falha do cache degrada com timeout, nao derruba o fluxo.
- [ ] Headers HTTP corretos (`no-store`/`private`/`public`) quando a camada e HTTP/CDN.
- [ ] Teste negativo de isolamento entre usuarios quando aplicavel.

## Quem Usa

- Executores (`@B`, `@D`, `@M`, `@BI`): desenham cache seguindo este metodo
  antes de implementar; desvio exige ADR.
- `@A`: referencia este metodo na secao de escalabilidade da planta tecnica.
- `@P`: valida contra o checklist acima; item sem resposta = `QUESTIONAR`.
- `@S`: valida isolamento, dado sensivel e headers.
- `@V` / `@GSD`: cobram o checklist como gate antes do selo final.
