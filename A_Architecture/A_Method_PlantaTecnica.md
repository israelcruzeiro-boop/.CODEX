# A_Method_PlantaTecnica - Planta Tecnica do Projeto

Metodo canonico do kit para criar e manter a **planta tecnica** de cada
repositorio/ambiente. Nasceu de review senior real (2026-07-13): um projeto com
otima documentacao de produto e IA "delirante" na implementacao, porque faltava
a descricao tecnica. Analogia canonica: a definicao de produto diz quantos
quartos e banheiros a casa tem; a planta tecnica e a planta eletrica e
hidraulica. Sem ela, o pedreiro (a IA) constroi cada comodo do jeito dele.

Regra de ouro: **quanto mais refinada a descricao tecnica do projeto, menos
delirante e a IA.** A IA e um pedreiro incansavel: sem planta, "o que vier,
veio".

---

## O Que E

Um documento por repositorio/ambiente (`ARCHITECTURE.md` na raiz do repo) que
descreve **como a aplicacao e por dentro**, derivado do codigo real - nunca um
plano aspiracional. E o contrato tecnico que todos os agentes executores leem
antes de implementar.

## Separacao Obrigatoria AS-IS E TO-BE

- `ARCHITECTURE.md` e exclusivamente **AS-IS**: codigo, manifests, schema e
  runtime observados. Nao aceita status "planta de intencao".
- `TARGET_ARCHITECTURE.md` e **TO-BE**: mudancas desejadas, rastreadas a spec
  e, quando houver trade-off material, ADR, seguindo
  `A_Method_ModularArchitecture.md`.
- `PATTERN_MAP.md` separa presenca no codigo de decisao normativa, seguindo
  `A_Method_PatternMap.md`.
- `DECISIONS.md` ou `docs/adr/*.md` registra o trade-off que autoriza o TO-BE.

O AS-IS nunca e reescrito para parecer o alvo. A diferenca vira delta
rastreavel, task de transicao, rollout/rollback e fitness gate.

## As 4 Propriedades Inegociaveis

1. **Especifica** - entidades reais, fluxos reais, exemplos do proprio codigo.
   Planta generica multi-projeto nao e planta; cada produto tem a sua.
2. **Derivada do codigo** - o cabecalho declara "Fonte: analise direta do
   codigo" + data. A planta so afirma o que o codigo confirma.
3. **Verificavel** - cada regra tem um gate que a cobra (lint, CI, teste ou
   item de checklist de review). Regra sem cobranca e letra morta.
4. **Enxuta** - cabe no contexto de uma sessao de IA, 100% verdadeira, sem
   ruido. Menos arquivos dizendo mais.

## Secoes Minimas

Por repositorio, a planta cobre:

1. **Stack real com versoes** (do manifest: package.json, pyproject, go.mod) +
   bloco explicito "NAO existem no projeto" para libs que docs antigos citem.
2. **Visao geral** - diagrama enxuto + **fluxo de uma feature de referencia
   camada a camada, arquivo por arquivo** (o molde que a IA replica).
3. **Modelo de dominio** - entidades reais em tabela: papel, relacoes/FKs,
   quirks de tipo. Corresponde aos modulos/pastas reais do projeto.
4. **Estrutura real de pastas** + padrao interno de cada modulo de dominio.
   Pastas vazias/reservadas marcadas: "VAZIO - nao usar sem ADR".
5. **Contratos de API reais** - rota, metodo, auth, papel; convencoes de
   serializacao (ex.: opcionais como null -> zod `.nullish()`).
6. **Autenticacao e autorizacao** - mecanismos, roles, assinaturas de webhook,
   fluxo de sessao.
7. **Regras de camada** - quem pode importar quem; onde vive regra de negocio;
   o que rota/handler NAO faz.
8. **Gerenciamento de estado** (frontends) - onde vive cada tipo de estado
   (inicial, server state, UI local, global) + proibicoes explicitas (ex.:
   nunca Redux junto de outra lib global; nunca useEffect+fetch em fluxo
   principal). Dois sistemas de estado global convivendo = "dois monstrinhos".
9. **Requisitos minimos de plataforma** - roda em celular? qual resolucao?
   idioma? temas? offline? acessibilidade?
10. **Gaps e pontos de atencao com severidade** - o debito tecnico honesto,
    visivel, priorizavel. Nunca esconder.
11. **Catalogo modular observado** - modulos reais com IDs, API publica,
    ownership de dados, invariantes e dependencias observadas. O catalogo
    detalhado segue `A_Method_ModularArchitecture.md`.
12. **Patterns observados** - referencias a `PATTERN_MAP.md`; observar um
    pattern nao equivale a aprova-lo.

## Regra De Manutencao

- Mudanca estrutural (rota, tabela, integracao, camada, lib, modulo novo)
  atualiza a planta **no mesmo PR/ciclo**. O `C10_DOCUMENTADOR` cobra isso no
  fechamento.
- Secao que virar promessa: remover ou mover para Gaps.
- Auditoria periodica de drift codigo x planta. Dono: `@A` com `@DOC`.
- Mudanca estrutural pretendida atualiza `TARGET_ARCHITECTURE.md` e ADR antes
  do codigo; somente depois de implementada e comprovada atualiza o AS-IS.

## Anti-Padroes (proibidos)

1. **Doc aspiracional** - descrever camadas/pastas/libs que nao existem como se
   existissem. E pior que doc nenhuma: a IA constroi em cima da ficcao.
2. **Stack fantasma** - listar dependencias que nao estao no manifest.
3. **Regra decorativa** - regra sem gate; o codigo a viola em silencio.
4. **Planta congelada** - data de atualizacao antiga com produto evoluindo.
5. **Verdade duplicada** - a mesma informacao em varios arquivos, divergindo.
   A planta e a fonte unica; os demais docs apontam para ela.
6. **Alvo travestido de presente** - copiar `TARGET_ARCHITECTURE.md` para o
   AS-IS antes de a mudanca existir no codigo.
7. **Pattern por imitacao** - declarar `APROVADO` algo apenas porque foi
   observado em um trecho do codigo.

## Gates De Verificacao (para @V, @C, @GSD e validadores)

- Existe `ARCHITECTURE.md` com cabecalho "fonte: analise direta do codigo" e
  data recente?
- Os endpoints da planta batem com as rotas reais do codigo?
- A stack da planta bate com o manifest?
- Pastas vazias e promessas estao marcadas como tal?
- A feature nova seguiu o fluxo de referencia e as regras de camada?
- A mudanca estrutural deste ciclo atualizou a planta?
- O documento contem apenas AS-IS? Toda intencao esta no TO-BE + ADR?
- Catalogo modular, grafo, ciclos, ownership e APIs publicas batem com o codigo?
- Patterns observados apontam evidencia e nao foram promovidos sem decisao?

## Exemplo De Referencia

Implementacao completa deste metodo: projeto "IA de SDR" -
`SDR Back/Architecture.md` e `SDR Front/Architecture.md` (v2.0, 2026-07-13),
reescritos por analise direta do codigo apos a review que originou o metodo.

## Quem Usa

- `@ONB`: diagnostica existencia/drift da planta no onboarding e exige a planta
  no kickoff de projeto novo.
- `@A`: audita o AS-IS, desenha o TO-BE e audita o drift; drift e finding,
  nao detalhe.
- `@DOC`: materializa e mantem o documento; aplica as 4 propriedades.
- `@SPEC`: specs novas referenciam o AS-IS e rastreiam mudancas no TO-BE/ADR.
- Executores (`@B`, `@GSD`, especialistas): tratam a planta como contrato de
  implementacao; padrao fora da planta exige ADR antes.
- `@V` / `@C`: validam entregas contra a planta usando os gates acima.
