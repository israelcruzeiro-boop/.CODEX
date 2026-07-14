# Referencia Railway — Environment Variables e Deploy

Use esta referencia apenas quando o projeto realmente usar Railway. Ela e
condicional: nunca aplique como regra universal. Confirme detalhes de API/flags
na documentacao oficial atualizada antes de prescrever comandos exatos.

---

## Modelo Mental

- **Project**: o container de tudo.
- **Environment**: ambientes isolados dentro do projeto (ex.: `production`,
  `staging`, `pr-*`). Cada environment tem suas proprias variaveis e instancias.
- **Service**: cada app/processo (API, worker, banco, etc.) dentro de um
  environment.
- **Variaveis**: escopadas por **service x environment**. Ha tambem variaveis
  compartilhadas no nivel do projeto.
- **Variaveis de referencia**: use a sintaxe `${{Service.VAR}}` ou
  `${{shared.VAR}}` para referenciar valores entre services sem duplicar segredo.
- **Variaveis automaticas**: Railway injeta algumas (ex.: `PORT`, `RAILWAY_*`,
  e variaveis de conexao de plugins/databases). Nao redefina manualmente sem
  motivo.

## CLI (superficie mais estavel)

```bash
railway login                 # autentica
railway link                  # vincula a pasta a um project/environment/service
railway status                # mostra project/environment/service atuais
railway environment           # lista/troca de environment
railway service               # lista/seleciona service

railway variables             # lista variaveis do service/environment atual
railway variables --set "KEY=value"   # define variavel
railway run <cmd>             # roda comando local com as variaveis do Railway injetadas
railway up                    # faz deploy do diretorio atual
railway logs                  # logs do deploy/service
```

Observacoes:
- `railway run` e a forma correta de rodar localmente com as MESMAS variaveis do
  ambiente remoto, sem copiar segredo para `.env`.
- Confirme as flags exatas (`--set`, `--service`, `--environment`) com
  `railway <cmd> --help`, pois variam por versao da CLI.

## API Publica (GraphQL)

- Endpoint GraphQL: `https://backboard.railway.com/graphql/v2` (confirme na doc).
- Autenticacao por token via header `Authorization: Bearer <TOKEN>`.
  - **Account/Team token**: acesso amplo a recursos do usuario/time.
  - **Project token**: escopo restrito a um project/environment (geralmente via
    header de projeto). Prefira o token de menor escopo possivel.
- Use a API para automacao (CI/CD, provisionamento, leitura/escrita de
  variaveis). Para tarefas pontuais, a CLI costuma ser suficiente.

## Regras De Environment Aplicadas a Railway

1. Nunca imprimir valor de secret; referenciar a chave, nunca o conteudo.
2. Separar `production` de `staging`/preview em environments distintos.
3. Usar `${{...}}` para referenciar variaveis entre services em vez de duplicar
   segredo.
4. Variaveis sao por service x environment: confirme o escopo antes de afirmar
   que uma variavel "existe".
5. Apos mudar variavel, lembrar que o service normalmente precisa de
   redeploy/restart para aplicar.
6. Variaveis publicas de cliente (ex.: prefixadas para front-end) nunca devem
   conter segredo, mesmo no Railway.
7. Tokens de projeto > tokens de conta para automacao: menor escopo, menor risco.

## Validacao Rapida

- `railway status` confirma project/environment/service corretos antes de mexer.
- `railway variables` confirma o estado real antes de propor mudanca.
- Em CI, validar que o token tem escopo apenas no environment necessario.
