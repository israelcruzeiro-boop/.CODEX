# DESIGN - [NOME DO PROJETO]

> Fonte de verdade visual do projeto. Regras detalhadas de execucao vivem em
> `D_Design/D_Agent_Design.md`; este documento registra as decisoes deste
> produto para qualquer agente replicar sem improvisar.

## Principios

**Produto:**
**Publico:**
**Tom visual:**
**Plataformas/resolucoes minimas:**
**Temas:** claro | escuro | ambos
**Idiomas:**

## Tokens De Design

| Token | Valor | Uso |
|---|---|---|
| Cor primaria |  |  |
| Cor de superficie |  |  |
| Cor de erro/sucesso/aviso |  |  |
| Fonte e escala tipografica |  |  |
| Espacamento (base e escala) |  |  |
| Raio de borda / sombra |  |  |

Regra: componente novo usa token existente; token novo exige atualizacao desta
tabela no mesmo ciclo.

## Componentes Padrao

| Componente | Regra | Variantes | Estados obrigatorios |
|---|---|---|---|
| Botao |  |  | default, hover, focus, loading, disabled |
| Input |  |  | default, focus, erro, disabled |
| Card |  |  |  |
| Modal |  |  |  |

## Estados Obrigatorios Por Tela

Toda tela com dados define os cinco estados. Estado ausente e Gap, nao detalhe.

- Loading (skeleton/spinner e onde).
- Vazio (mensagem + acao sugerida).
- Erro (mensagem honesta + recuperacao).
- Sucesso/feedback (toast, inline, redirect).
- Sem permissao (o que o usuario ve).

## Fluxos UX

### [Fluxo]

**Ator:**
**Objetivo:**
**Caminho feliz:**
**Estados vazios:**
**Erros:**
**Permissoes:**

## Telas

| Tela | Objetivo | Componentes | Estados obrigatorios |
|---|---|---|---|
|  |  |  |  |

## Acessibilidade

- Contraste minimo WCAG AA (4.5:1 texto normal, 3:1 texto grande).
- Navegacao completa por teclado; foco visivel em todo interativo.
- Labels/aria em inputs, botoes de icone e imagens significativas.
- Alvos de toque minimos em mobile (~44px).
- Nao comunicar estado apenas por cor.

## Responsividade

| Breakpoint | Largura | Comportamento |
|---|---|---|
| Mobile |  |  |
| Tablet |  |  |
| Desktop |  |  |

## Performance Visual

- Imagens com dimensoes declaradas, formato moderno e lazy loading fora da dobra.
- Sem layout shift (CLS) em carregamento de dados: reservar espaco/skeleton.
- Listas grandes paginadas ou virtualizadas.
- Animacoes respeitam `prefers-reduced-motion`.

## Criterios De Aceite Visual

- [ ] Responsivo nos breakpoints declarados.
- [ ] Texto nao sobrepoe componentes.
- [ ] Cinco estados obrigatorios definidos em toda tela com dados.
- [ ] Controles usam tokens e padroes do design system.
- [ ] Checklist de acessibilidade acima verificado.
- [ ] Temas declarados funcionam em todas as telas.

## Lacunas

- [ ]
