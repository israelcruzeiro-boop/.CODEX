# Metodo SDD Canonico

SDD, neste kit, significa `Spec-Driven Delivery`.

O objetivo e transformar cada tarefa em uma entrega guiada por especificacao,
evidencia e aprendizado. Nao e burocracia; e o trilho minimo para evitar que
um MVP bonito cresca sobre base fragil.

---

## Cadeia SDD

Use sempre esta sequencia:

1. `STATE`: entender o estado real.
2. `SPEC`: definir comportamento esperado e criterio de aceite.
3. `DESIGN`: desenhar a solucao minima e mapear impacto.
4. `DOUBT`: confrontar o plano com riscos, lacunas e codigo real.
5. `DEVELOP`: implementar o menor diff que satisfaz a spec.
6. `DEMONSTRATE`: provar por testes, comandos e smoke que funciona.
7. `DOCUMENT`: registrar decisoes, aprendizados, status geral, status por
   ambiente e proximos passos.

---

## Como Cada Etapa Se Materializa

| Etapa | Evidencia minima | Agentes naturais |
|---|---|---|
| STATE | `PROJECT.md`, `STATUS.md`, `LOG.md`, codigo afetado | `@C10`, `@PICK` |
| SPEC | criterio de aceite, escopo, fora de escopo | `@C10`, `@PR`, especialista |
| DESIGN | arquivos, contratos, consumidores, rollback | `@A`, especialista |
| DOUBT | riscos, lacunas, veredito proporcional | `@C`, `impact_validator` |
| DEVELOP | diff pequeno, TDD proporcional | executor, `@GSD` |
| DEMONSTRATE | Harness CLI, testes, smoke, bug sweep | `@GSD`, `@Q`, `final_validator` |
| DOCUMENT | LOG, STATUS geral/por ambiente, DECISIONS, LEARNINGS | Documentador |

---

## Regras Nao Negociaveis

- Sem `SPEC`, nao existe implementacao; existe chute.
- Sem `DOUBT`, nao existe plano aprovado; existe otimismo.
- Sem `DEMONSTRATE`, nao existe pronto; existe "parece pronto".
- Sem `DOCUMENT`, o projeto perde memoria e repete erro.

---

## Checklist SDD Por Tarefa

```md
## SDD Checklist

STATE
- [ ] PROJECT/STATUS/LOG lidos quando existirem.
- [ ] Arquivos e fluxos afetados localizados.
- [ ] Consumidores e contratos rastreados.

SPEC
- [ ] Comportamento esperado escrito.
- [ ] Criterios de aceite testaveis.
- [ ] Fora de escopo declarado.

DESIGN
- [ ] Plano minimo.
- [ ] Riscos e rollback.
- [ ] Dependencias e validadores necessarios.

DOUBT
- [ ] Cético ou validador de impacto revisou.
- [ ] Lacunas explicitadas.
- [ ] Veredito proporcional.

DEVELOP
- [ ] TDD ou excecao TDD justificada.
- [ ] Diff pequeno e sem refatoracao lateral.

DEMONSTRATE
- [ ] Harness CLI executado.
- [ ] Testes/smoke proporcionais.
- [ ] Bug sweep feito.

DOCUMENT
- [ ] STATUS/LOG atualizados quando for ciclo significativo.
- [ ] Status geral do projeto atualizado.
- [ ] Status/progresso de cada ambiente afetado atualizado.
- [ ] Migrations registradas no diretorio canonico, quando houver.
- [ ] ADR ou LEARNING registrado quando houver decisao ou erro reutilizavel.
```

---

## Veredito SDD

- `SDD_OK`: todas as etapas aplicaveis tem evidencia.
- `SDD_COM_RESSALVAS`: lacunas nao criticas foram registradas.
- `SDD_QUESTIONAR`: falta decisao ou contexto que impede seguir.
- `SDD_REPROVADO`: etapa obrigatoria foi pulada ou evidencia contradiz a entrega.

O metodo SDD e o contrato de qualidade do kit. Agentes especializados podem ter
protocolos proprios, mas nenhum pode violar esta cadeia.
