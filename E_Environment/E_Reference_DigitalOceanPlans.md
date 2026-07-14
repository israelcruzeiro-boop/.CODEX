# Referencia DigitalOcean Plans

Snapshot consultado na documentacao oficial em 2026-05-20.
Precos e planos mudam: antes de recomendar em projeto real, confirmar com a
documentacao atual e, quando houver token, com a API.

Fontes:
- App Platform Pricing: https://docs.digitalocean.com/products/app-platform/details/pricing/
- Choosing App Platform Plan: https://docs.digitalocean.com/products/app-platform/concepts/choosing-a-plan/
- Droplet Pricing: https://docs.digitalocean.com/products/droplets/details/pricing/
- Droplet Features: https://docs.digitalocean.com/products/droplets/details/features/
- Managed Databases: https://docs.digitalocean.com/products/databases/
- PostgreSQL Pricing: https://docs.digitalocean.com/products/databases/postgresql/details/pricing/
- Spaces Pricing: https://docs.digitalocean.com/products/spaces/details/pricing/
- Load Balancers Pricing: https://docs.digitalocean.com/products/networking/load-balancers/details/pricing/

---

## App Platform: Planos Atuais por Container

| Slug | CPU | RAM | Egress incluido | Preco mensal | Escala manual | Autoscaling |
|---|---:|---:|---:|---:|---|---|
| `apps-s-1vcpu-0.5gb` | 1 shared | 512 MiB | 50 GiB | US$5 | nao | nao |
| `apps-s-1vcpu-1gb-fixed` | 1 shared | 1 GiB | 100 GiB | US$10 | nao | nao |
| `apps-s-1vcpu-1gb` | 1 shared | 1 GiB | 150 GiB | US$12 | sim | nao |
| `apps-s-1vcpu-2gb` | 1 shared | 2 GiB | 200 GiB | US$25 | sim | nao |
| `apps-s-2vcpu-4gb` | 2 shared | 4 GiB | 250 GiB | US$50 | sim | nao |
| `apps-d-1vcpu-0.5gb` | 1 dedicated | 512 MiB | 100 GiB | US$29 | sim | sim |
| `apps-d-1vcpu-1gb` | 1 dedicated | 1 GiB | 200 GiB | US$34 | sim | sim |
| `apps-d-1vcpu-2gb` | 1 dedicated | 2 GiB | 300 GiB | US$39 | sim | sim |
| `apps-d-1vcpu-4gb` | 1 dedicated | 4 GiB | 400 GiB | US$49 | sim | sim |
| `apps-d-2vcpu-4gb` | 2 dedicated | 4 GiB | 500 GiB | US$78 | sim | sim |
| `apps-d-2vcpu-8gb` | 2 dedicated | 8 GiB | 600 GiB | US$98 | sim | sim |
| `apps-d-4vcpu-8gb` | 4 dedicated | 8 GiB | 700 GiB | US$156 | sim | sim |
| `apps-d-4vcpu-16gb` | 4 dedicated | 16 GiB | 800 GiB | US$196 | sim | sim |
| `apps-d-8vcpu-32gb` | 8 dedicated | 32 GiB | 900 GiB | US$392 | sim | sim |

Notas:
- Billing por segundo, minimo de um minuto.
- Custo = tamanho do container x quantidade de instancias por componente.
- Egress adicional em App Platform: US$0.02/GiB.
- Dedicated egress IP: ate US$25/mes.
- Development database: US$7/mes por database de 512 MB.

---

## Free Tier App Platform

Uso adequado:
- Static sites.
- Portfolio, landing simples, doc site, projeto pequeno.

Limites relevantes:
- Ate 3 apps contendo somente static site components.
- 1 GiB de egress por app.
- App extra com static site component: US$3/mes.

Nao usar como resposta automatica para backend/API: se existe service, worker ou
runtime backend, o app sai do caso de static-only.

---

## Shared vs Dedicated

Shared CPU:
- Melhor para baixo/medio trafego.
- Bom para blogs, pequenos sites, APIs basicas e microservicos simples.
- Custo menor, performance menos previsivel.

Dedicated CPU:
- Melhor para producao com performance previsivel.
- Necessario para autoscaling baseado em CPU.
- Bom para APIs pesadas, trafego alto, workloads de processamento ou picos.

Regra: iniciar pequeno, medir e subir com evidencia.

---

## Heuristica de Escolha

| Cenario | Recomendacao inicial | Quando subir |
|---|---|---|
| Static frontend | Free Tier | egress acima do limite, dominio/fluxo mais complexo |
| MVP API leve | `apps-s-1vcpu-0.5gb` | memoria p95 perto do limite, cold starts/restarts |
| API Node/Express padrao | `apps-s-1vcpu-1gb` | CPU/memoria p95 alto, mais concorrencia |
| API com ORM, jobs ou imagens | `apps-s-1vcpu-2gb` | memoria > 1.5 GiB, filas lentas, picos |
| SaaS pequeno em producao | `apps-s-1vcpu-1gb` ou `apps-s-1vcpu-2gb` | SLO/latencia ou restart count |
| Producao critica | `apps-d-1vcpu-1gb` ou maior | autoscaling, previsibilidade, carga alta |
| Processamento pesado | dedicated CPU | CPU-bound, jobs longos, picos fortes |

---

## Droplets

Droplets sao VMs Linux. Use quando o projeto precisa de controle de servidor,
processos longos, software customizado, volumes, proxy proprio ou custo menor com
maior responsabilidade operacional.

Familias de CPU Droplets:
- Basic: shared CPU, 1-8 vCPU, 1-32 GB RAM.
- General Purpose: dedicated CPU, 2-48 vCPU, 8-240 GB RAM, 4 GB/vCPU.
- CPU-Optimized: dedicated CPU, 2-48 vCPU, 4-120 GB RAM, 2 GB/vCPU.
- Memory-Optimized: dedicated CPU, 2-32 vCPU, 16-384 GB RAM, 8 GB/vCPU.
- Storage-Optimized: dedicated CPU, 2-32 vCPU, 16-384 GB RAM.

Como obter lista atual:
- API: `GET /v2/sizes`
- CLI: `doctl compute size list`

Alertas:
- Droplet desligado continua cobrando enquanto existir.
- Billing termina ao destruir o Droplet.
- Egress adicional em Droplets: US$0.01/GiB.
- Self-managed exige firewall, backups, updates, SSH, observabilidade e rollback.

---

## Managed Databases

Uso recomendado:
- Producao.
- Dados de clientes.
- Necessidade de backup, failover, SSL, patching gerenciado e isolamento.

PostgreSQL pricing snapshot:
- Single node inicia em US$15/mes para 1 GiB RAM.
- High availability inicia em US$30/mes para primary 2 GiB/1 vCPU, mais standby
  correspondente a partir de US$30/mes.
- Read-only nodes iniciam em US$15/mes.
- Storage adicional: US$0.21/GiB/mes.

Regra:
- Dev Database: prototipo/dev/teste.
- Managed Database: producao.
- HA com standby: producao critica.

---

## Spaces

Uso:
- Uploads de usuario.
- Imagens, documentos, backups de app, assets.
- Alternativa a salvar arquivos no filesystem do container.

Snapshot:
- Base: US$5/mes.
- Inclui 250 GiB de storage.
- Inclui 1,024 GiB de outbound transfer.
- Storage adicional: US$0.02/GiB/mes.
- Transfer adicional: US$0.01/GiB.
- CDN incluido.

---

## Load Balancers

Regional:
- HTTP: US$12/mes por node.
- Network: US$15/mes por node.

Global:
- US$15/mes.
- Inclui 25M HTTP/HTTPS requests/mes.
- Inclui 1 TB transfer/mes.

Usar quando:
- Multiplos Droplets/backend nodes.
- Alta disponibilidade.
- Rolling deploy com VMs.
- Separacao gateway/backend.

Em App Platform, avaliar recursos nativos antes de adicionar load balancer externo.

---

## Saida Obrigatoria da Recomendacao

Toda recomendacao de plano deve responder:

```text
Plano recomendado:
  - componente:
  - plano:
  - custo mensal estimado:
  - por que este plano:
  - por que nao menor:
  - por que nao maior:
  - metricas que confirmariam a escolha:
  - gatilhos para upgrade/downgrade:
  - lacunas:
```
