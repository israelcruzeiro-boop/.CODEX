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

## Regra De Manutencao

- Mudanca estrutural (rota, tabela, integracao, camada, lib, modulo novo)
  atualiza a planta **no mesmo PR/ciclo**. O `C10_DOCUMENTADOR` cobra isso no
  fechamento.
- Secao que virar promessa: remover ou mover para Gaps.
- Auditoria periodica de drift codigo x planta. Dono: `@A` com `@DOC`.

## Anti-Padroes (proibidos)

1. **Doc aspiracional** - descrever camadas/pastas/libs que nao existem como se
   existissem. E pior que doc nenhuma: a IA constroi em cima da ficcao.
2. **Stack fantasma** - listar dependencias que nao estao no manifest.
3. **Regra decorativa** - regra sem gate; o codigo a viola em silencio.
4. **Planta congelada** - data de atualizacao antiga com produto evoluindo.
5. **Verdade duplicada** - a mesma informacao em varios arquivos, divergindo.
   A planta e a fonte unica; os demais docs apontam para ela.

## Gates De Verificacao (para @V, @C, @GSD e validadores)

- Existe `ARCHITECTURE.md` com cabecalho "fonte: analise direta do codigo" e
  data recente?
- Os endpoints da planta batem com as rotas reais do codigo?
- A stack da planta bate com o manifest?
- Pastas vazias e promessas estao marcadas como tal?
- A feature nova seguiu o fluxo de referencia e as regras de camada?
- A mudanca estrutural deste ciclo atualizou a planta?

## Exemplo De Referencia

Implementacao completa deste metodo: projeto "IA de SDR" -
`SDR Back/Architecture.md` e `SDR Front/Architecture.md` (v2.0, 2026-07-13),
reescritos por analise direta do codigo apos a review que originou o metodo.

## Quem Usa

- `@ONB`: diagnostica existencia/drift da planta no onboarding e exige a planta
  no kickoff de projeto novo.
- `@A`: desenha a arquitetura e audita o drift; drift e finding, nao detalhe.
- `@DOC`: materializa e mantem o documento; aplica as 4 propriedades.
- `@SPEC`: specs novas referenciam a planta (nao a contradizem sem ADR).
- Executores (`@B`, `@GSD`, especialistas): tratam a planta como contrato de
  implementacao; padrao fora da planta exige ADR antes.
- `@V` / `@C`: validam entregas contra a planta usando os gates acima.
