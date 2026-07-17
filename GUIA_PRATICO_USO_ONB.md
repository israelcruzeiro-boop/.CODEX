# Guia Prático de Uso do @ONB

Atualizado em: 2026-07-16

Este guia explica como usar o `@ONB` como porta de entrada do Codex Agent Kit,
quando ele deve apenas diagnosticar e quando o pedido deve autorizar a execução
coordenada com outros agentes e subagentes.

Fonte de verdade do papel: `ONB_Onboarding/ONB_Agent_ProjectOnboardingGuide.md`.

## Resposta Curta

Sim: em um projeto corretamente configurado com o arsenal, você pode começar o
prompt com `@ONB`.

Porém, `@ONB` não significa automaticamente "execute tudo até o deploy". Ele é
o guia de entrada: reconstrói o estado real, identifica fase e gargalos, diz se
o projeto está alinhado e encaminha a pessoa ao agente certo. Para transformar
o diagnóstico em execução completa, o prompt deve autorizar explicitamente a
continuação, a delegação e a integração dos resultados.

## O Que O @ONB Faz

Ao receber um pedido de onboarding, ele deve:

1. descobrir se o projeto é novo ou está em andamento;
2. ler código, memória e documentação antes de opinar;
3. identificar stack, ambientes, módulos e contratos observáveis;
4. separar fatos observados, inferências e lacunas;
5. verificar se código, specs, arquitetura e documentação concordam;
6. encontrar gargalos capazes de travar a próxima fase;
7. indicar um próximo passo concreto;
8. encaminhar o trabalho ao agente ou à sequência de agentes adequada.

O `@ONB` orienta e entrega contexto. Os donos naturais do trabalho posterior
são, entre outros:

- `@PICK`: seleção do time para uma tarefa concreta;
- `@SPEC`: especificações executáveis e critérios de aceite;
- `@DOC`: documentação estrutural;
- `@A`: arquitetura modular, fronteiras, ownership e contratos;
- `@C10`: coordenação contínua, fases e memória;
- agentes especialistas e validadores aplicáveis.

## Encaminhamento Não É O Mesmo Que Execução

Um pedido simples como:

```text
@ONB, analise este projeto e diga qual é o próximo passo.
```

autoriza principalmente diagnóstico e recomendação. A saída pode indicar:

```text
Próximo passo: criar as especificações.
Agente: @SPEC.
Sequência: @SPEC -> @A -> @C10 -> @PICK.
```

Isso não garante, por si só, que todas as etapas serão executadas na mesma
tarefa. Para pedir execução real, seja explícito:

```text
@ONB, diagnostique o projeto.

Depois do diagnóstico:
- entregue as especificações para @SPEC;
- entregue a arquitetura para @A;
- use @PICK para selecionar os especialistas;
- use @C10 para coordenar a execução;
- utilize subagentes para frentes independentes;
- aguarde todos os resultados;
- integre e valide o resultado final.

Pode executar a sequência, não apenas recomendá-la.
```

Essa formulação distingue três autorizações:

- analisar e recomendar;
- delegar trabalho;
- implementar, integrar e validar.

## Projeto Novo: Modo Kickoff Completo

Use o Modo Kickoff Completo quando quiser iniciar um produto com base técnica,
documentação, specs e governança suficientes para evitar improviso.

```text
@ONB, este é um projeto novo. Use o Modo Kickoff Completo.

Projeto: [nome]
Objetivo: [problema que resolve]
Produto: [web, mobile, API, SaaS, CLI etc.]
Público: [público-alvo]
Fluxo principal: [principal jornada]
Stack desejada: [stack ou "a definir"]
Ambientes: [local, preview, staging, produção]
Superfícies sensíveis: [auth, pagamentos, PII, uploads, IA etc.]
Requisitos de plataforma: [mobile, resolução, idioma, tema, offline etc.]

Gere os briefings para @DOC, @SPEC e @C10.
Depois, use @C10 para coordenar a criação da fundação do projeto.
Utilize subagentes nas frentes independentes e valide tudo antes de encerrar.
```

Sequência de referência:

```text
@ONB
  -> @DOC
  -> @SPEC
  -> @A
  -> @C10
  -> @PICK
  -> especialistas
  -> @GSD / @Q
  -> @V
  -> documentação final
```

Antes de existir código, a arquitetura pretendida deve ser registrada em
`TARGET_ARCHITECTURE.md`, sustentada por specs e ADRs. `ARCHITECTURE.md` é a
planta AS-IS e deve descrever apenas arquitetura observada diretamente no código.

## Projeto Em Andamento

Para projeto herdado, parado ou potencialmente desalinhado:

```text
@ONB, este é um projeto em andamento.

Leia o código e a documentação real antes de opinar. Reconstrua:
- fase atual;
- ambientes e módulos;
- arquitetura observada;
- contratos entre frontend, backend, banco e terceiros;
- tarefas concluídas e pendentes;
- gargalos;
- divergências entre código, specs e documentação;
- testes e validações disponíveis.

Separe fatos, inferências e lacunas.
Não edite nada ainda.
Entregue o próximo passo e a sequência recomendada de agentes.
```

Depois de revisar o diagnóstico, a execução pode ser autorizada assim:

```text
Pode executar o plano recomendado.

Use @C10 como coordenador, @PICK para selecionar o time e subagentes para
frentes realmente independentes. Antes de implementar, exija specs e
arquitetura. Ao final, execute os gates aplicáveis, atualize STATUS e LOG
e apresente as evidências.
```

## Prompt Recomendado Para Uso Geral

```text
@ONB, faça o onboarding deste projeto.

Determine se ele é novo ou em andamento e leia todas as evidências disponíveis.
Identifique fase, stack, ambientes, módulos, arquitetura, contratos, gargalos,
riscos e desalinhamentos. Separe fatos, inferências e lacunas.

Depois:
1. use @PICK para selecionar os agentes;
2. use @SPEC quando faltarem especificações;
3. use @A para validar a arquitetura modular;
4. use @C10 para coordenar o ciclo;
5. delegue frentes independentes a subagentes;
6. aguarde e integre todos os resultados;
7. execute os gates aplicáveis;
8. atualize STATUS, LOG e decisões;
9. encerre com evidências e o próximo passo.

Pode executar o trabalho, não apenas recomendar.
Não implemente antes de existirem critérios de aceite e arquitetura suficiente.
```

## Como Usar Durante O Ciclo Do Projeto

`@ONB` não precisa ser chamado em cada alteração. Use-o nos momentos em que a
posição do projeto precisa ser reconstruída:

- primeiro contato com o projeto;
- início de um projeto novo;
- retomada depois de uma pausa;
- entrada de uma nova pessoa ou equipe;
- mudança relevante de fase;
- dúvida sobre prioridade ou próximo passo;
- suspeita de divergência entre código e documentação.

Para o trabalho cotidiano, acione o papel mais específico:

| Situação | Entrada recomendada |
|---|---|
| Não sei por onde começar | `@ONB` |
| Preciso coordenar uma fase inteira | `@C10` |
| Preciso montar o time desta tarefa | `@PICK` |
| A ideia ainda está vaga | `@SPEC` |
| Preciso definir modularidade e contratos | `@A` |
| Preciso implementar com critérios e prova | `@GSD` + especialista |
| Preciso investigar um defeito | `@BUG` |
| Preciso validar antes de fechar | `@Q` + `@V` |

Para uma feature isolada, normalmente é mais eficiente começar diretamente com:

```text
@SPEC e @PICK, transformem este pedido em uma spec executável e selecionem
o time necessário. Depois use @C10 para coordenar a implementação.
```

## Uso Correto De Subagentes

Pedir "use muitos subagentes" não significa dividir qualquer trabalho de forma
arbitrária. A delegação deve ocorrer apenas quando houver frentes independentes
ou revisões que realmente se beneficiem de contextos separados.

Uma boa instrução é:

```text
Use subagentes para frentes independentes. Antes de delegar, defina tarefas,
dependências, read-set, write-set, critérios de conclusão e integrador.
Evite escrita concorrente nos mesmos arquivos. Aguarde todos os resultados,
reconcilie divergências pela evidência primária e revalide o resultado integrado.
```

O agente raiz continua responsável por:

- controlar dependências e ordem;
- impedir conflitos de escrita;
- aguardar os joins obrigatórios;
- resolver conclusões contraditórias;
- integrar os resultados;
- executar a validação final.

## Como Garantir Que O Alias Funcione

`@ONB` não é uma macro universal do Codex. Ele depende de o projeto carregar o
arsenal, as regras da raiz e os wrappers do runtime.

Estrutura esperada:

```text
PROJECT_ROOT/
  .codex/
  .agents/
  AGENTS.md
  CLAUDE.md
  back/
  front/
  ...
```

Depois de instalar ou atualizar o checkout do arsenal:

```powershell
python .codex/RUNTIME_Bridge/scripts/install_project_runtime.py --project-root .
python .codex/RUNTIME_Bridge/scripts/install_project_runtime.py --project-root . --check
```

O `AGENTS.md` da raiz deve ser criado ou adaptado a partir de
`.codex/C10_Maestro/C10_Agent_ProjectRules.md`. Sem essa integração, `@ONB` pode
ser tratado apenas como texto comum, sem carregar seu contrato completo.

## Limites E Segurança

Mesmo em modo de execução completa, o `@ONB` e os agentes delegados não devem:

- inventar o estado do projeto quando faltarem evidências;
- implementar uma entrega relevante sem critérios de aceite;
- tratar intenção arquitetural como arquitetura já existente;
- ignorar autorização necessária para produção, credenciais ou ação externa;
- usar subagentes concorrentes com write-sets incompatíveis;
- declarar sucesso sem comandos, resultados e lacunas proporcionais ao risco.

Uma ordem como "não pare até terminar" aumenta a persistência, mas não amplia
automaticamente permissões nem autoriza operações externas destrutivas.

## Checklist Rápido

Antes de enviar o prompt, confirme:

- [ ] Informei se o projeto é novo ou existente, quando sei?
- [ ] Dei objetivo, produto, público e fluxo principal?
- [ ] Declarei se quero diagnóstico ou execução?
- [ ] Pedi fatos, inferências e lacunas separados?
- [ ] Autorizei `@C10` e `@PICK` quando quero continuidade?
- [ ] Pedi subagentes apenas para frentes independentes?
- [ ] Exigi integração, validação e atualização da memória?
- [ ] O projeto possui `.codex/`, `AGENTS.md` e runtime instalados?

## Regra De Bolso

Use `@ONB` para descobrir onde o projeto está e para onde deve ir. Use `@C10`
para conduzir a jornada, `@PICK` para montar o time e os especialistas para
executar. Quando quiser tudo na mesma tarefa, diga explicitamente: **pode
executar a sequência, não apenas recomendá-la**.
