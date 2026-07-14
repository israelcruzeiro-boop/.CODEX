# LOCATION_MODEL

## Decisao De Produto

- Finalidade da localizacao:
- Nivel de precisao necessario: pais | cidade | bairro | raio | coordenada exata
- Dados exibidos publicamente:
- Dados nunca exibidos publicamente:
- Retencao:

## Origem Da Localizacao

- Endereco cadastrado:
- GPS atual:
- IP aproximado:
- Autocomplete/geocoding:
- Provider:

## Raio / Proximidade

- Default:
- Minimo:
- Maximo:
- Personalizado permitido? sim/nao
- Ordenacao por distancia? sim/nao

## Tecnologia

- Banco:
- Suporte a indice geografico:
- Provider de mapa/geocoding:
- Rate limits/custo:

```sql
-- exemplo conceitual: adapte ao banco real
-- criar indice geografico/espacial quando a stack suportar
```

## Resposta Publica

Retornar:

- id publico
- nome/label publico
- categoria/servico
- distancia aproximada, se aplicavel
- area publica, se aplicavel

Nao retornar sem regra explicita:

- endereco completo
- coordenadas exatas
- dados privados
- historico de localizacao

## Testes

- endereco/localizacao invalida
- permissao negada
- raio maximo
- paginacao
- privacidade da resposta
- protecao contra scraping
- plano/performance da query quando aplicavel
