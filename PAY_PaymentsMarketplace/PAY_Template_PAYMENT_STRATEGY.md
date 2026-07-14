# PAYMENT_STRATEGY

## Contexto

**Pais/mercado:** [definir]
**Moeda:** [definir]
**Tipo de transacao:** digital | fisica/presencial | SaaS | marketplace | produto fisico | mista
**Gateway/provedor:** [definir ou PENDENTE]
**Merchant of record:** plataforma | vendedor/prestador | terceiro | PENDENTE

## Decisao Atual

- [ ] Sem pagamento real nesta fase.
- [ ] Preparar dominio para pagamento futuro.
- [ ] Implementar pagamento real nesta fase.
- [ ] PENDENTE: decisao de gateway/regra de loja/regiao.

## Fora De Escopo Nesta Fase

- Checkout:
- Split/comissao:
- Payout:
- Refund:
- Dispute/chargeback:
- Wallet/saldo:
- Escrow/custodia formal:

## Modelo De Dominio

Status financeiros necessarios:

- ...

Entidades necessarias:

- ...

## Regras Obrigatorias

- API/backend como autoridade financeira.
- Webhooks idempotentes e assinados.
- Ledger/reconciliacao quando houver dinheiro real.
- Sem armazenamento de dados de cartao.
- Sem promessa de escrow/custodia/garantia sem revisao juridica.
- Chaves test/live separadas por ambiente.

## Riscos / Revisao Necessaria

- Juridico/regulatorio:
- Fiscal/contabil:
- Loja/app review:
- Seguranca/PCI:
- Operacao/reconciliacao:
