# Metodo Harness Canonico

Harness e o contrato de prova executavel do kit.

Uma entrega sem Harness pode ate estar correta, mas ainda nao foi demonstrada.
O Harness transforma "rodei uns testes" em evidencia auditavel.

---

## O Que Conta Como Harness

Harness e um conjunto de verificacoes reais, executadas ou justificadamente
registradas, com:

- Comando.
- Diretorio de execucao.
- Objetivo.
- Exit code.
- Resultado resumido.
- Falhas e warnings relevantes.
- Lacunas que nao puderam ser verificadas.
- Veredito.

Use `T_Templates/T_Template_CLI_AUDIT.md` para registrar.

O Harness e a ultima linha da matriz operacional:

```text
REQ/NFR -> MOD/CON/EVT -> TASK -> TEST/FIT -> EVD
```

Cada evidencia recebe ID `EVD-*` e aponta a exigencia, task e teste/gate que
prova. Saida de comando sem vinculo rastreavel e diagnostico, nao prova de
aceite.

---

## Ordem Recomendada

1. Descobrir scripts reais: `package.json`, `Makefile`, `pyproject.toml`,
   `Cargo.toml`, `go.mod`, CI ou docs.
2. Rodar o teste mais especifico primeiro.
3. Rodar validadores locais: lint, typecheck, unit, integration.
4. Rodar build quando a mudanca pode afetar empacotamento ou runtime.
5. Rodar smoke manual ou automatizado do fluxo principal.
6. Registrar falhas, lacunas e comandos nao encontrados.
7. Antes do fechamento, confirmar que `STATUS.md` sera atualizado com status
   geral, status por ambiente e migrations do ciclo quando houver.
8. Conferir DoR antes da implementacao e DoD antes do fechamento, conforme
   `T_Templates/T_Template_SPEC.md`.
9. Verificar que todos os `REQ-*` e `NFR-*` ativos possuem `TEST-*`/`FIT-*` e
   `EVD-*`, ou `N/A` justificado.

---

## Regras Duras

- Nunca inventar comando.
- Nunca esconder exit code diferente de zero.
- Nunca chamar warning de irrelevante sem justificar.
- Nunca aprovar fluxo critico sem teste ou prova substituta forte.
- Nunca usar producao como ambiente de teste sem `@CRED` e autorizacao explicita.
- Nunca imprimir secrets em log, terminal ou relatorio.
- Nunca fechar ciclo relevante sem registrar qual ambiente foi validado, qual
  ficou sem validacao e qual status por ambiente/progresso precisa entrar no
  `STATUS.md`.
- Nunca aprovar com elo quebrado na rastreabilidade de requisito critico.
- Nunca usar `PASS`/`FAIL` como veredito global; esses termos classificam
  somente resultados individuais de comandos.

---

## Classificacao De Resultado

- `PASS`: comando executou e validou o objetivo.
- `FAIL`: comando falhou ou revelou bug.
- `SKIP_JUSTIFICADO`: comando nao existe ou nao se aplica, com motivo.
- `LACUNA`: comando necessario nao pode ser executado ou falta contexto.

---

## Politica De Veredito

- Qualquer `FAIL` em teste, build, typecheck, lint critico ou smoke principal
  bloqueia fechamento.
- `LACUNA` em fluxo critico gera `QUESTIONAR` ou `REPROVADO`, conforme risco.
- `SKIP_JUSTIFICADO` e aceitavel apenas quando existe prova substituta.

O veredito global do Harness usa exclusivamente:

- `APROVADO`: DoD atendida, elos rastreaveis e nenhuma falha/lacuna bloqueante.
- `APROVADO_COM_RESSALVAS`: lacuna nao critica, explicita, com dono e follow-up.
- `QUESTIONAR`: falta contexto, acesso, comando ou evidencia para concluir.
- `REPROVADO`: falha comprovada, requisito nao atendido, regressao, risco
  critico ou lacuna bloqueante.

Se falta evidencia, use `QUESTIONAR`; se existe evidencia de falha, use
`REPROVADO`.

Harness bom nao e lista grande de comandos. E a menor prova forte o suficiente
para sustentar a entrega.
