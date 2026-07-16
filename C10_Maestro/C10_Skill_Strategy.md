# Estrategia De Skills Do Agent Kit

Este kit nao deve criar uma skill para cada pasta de agente por padrao.

Skills sao melhores quando carregam um workflow recorrente, enxuto e acionavel.
Agentes sao melhores quando representam papeis, criterios de decisao e
especialidades dentro do pipeline.

---

## Decisao

Nao criar skill por pasta.

Criar skills apenas quando houver:

- Gatilho recorrente claro.
- Workflow que Codex deve executar automaticamente.
- Recursos reutilizaveis que evitam reescrever scripts, referencias ou templates.
- Baixa duplicacao com documentos ja presentes na pasta `.codex/`.

---

## Skills Recomendadas

1. `codex-agent-kit`
   - Aciona quando o usuario pede para usar, auditar ou evoluir o kit.
   - Le `AGENTS.md`, `C10_Maestro`, `SUP_Supervisor` e catalogo de agentes.
   - Implementada em `skills/codex-agent-kit/SKILL.md`.

2. `gsd-tdd-cli-harness`
   - Aciona em implementacao, bugfix e refatoracao.
   - Usa `GSD_DeliveryDiscipline/GSD_Agent_TDDCLIAuditor.md`,
     `C10_Method_SDD.md` e `SUP_Method_Harness.md`.
   - Implementada em `skills/gsd-tdd-cli-harness/SKILL.md`.

3. `agent-forge`
   - Aciona quando o usuario pede para criar, evoluir ou promover agentes.
   - Usa `F_AgentForge`.
   - Implementada em `skills/agent-forge/SKILL.md`.

4. `architecture-blueprint`
   - Aciona em arquitetura AS-IS, TO-BE, modularidade, dependencias, ADRs e
     mapeamento de padroes.
   - Usa `A_Architecture` e os templates de arquitetura/pattern map.
   - Implementada em `skills/architecture-blueprint/SKILL.md`.

5. `spec-driven-breakdown`
   - Aciona quando requisitos precisam virar specs granulares, IDs estaveis,
     tasks, testes e rastreabilidade executavel.
   - Usa `SPEC_Specs`, SDD e Harness.
   - Implementada em `skills/spec-driven-breakdown/SKILL.md`.

6. `multi-agent-delivery`
   - Aciona quando dois ou mais workstreams independentes justificam fan-out,
     isolamento de contexto e fan-in controlado.
   - Usa `SUP_Method_MultiAgentDelivery` e templates de task/result.
   - Implementada em `skills/multi-agent-delivery/SKILL.md`.

---

## Quando Promover Uma Pasta Para Skill

Promova somente se a pasta:

- For usada em varios projetos.
- Tiver instrucoes estaveis.
- Tiver referencias ou scripts que devem ser carregados sob demanda.
- Nao depender de todo o contexto do kit para funcionar.

Se a pasta e apenas um agente especializado, mantenha como agente.

---

## Skills Reais Criadas

As seis skills recomendadas tem fonte canonica dentro deste kit em `skills/`.
O instalador as projeta em `PROJECT_ROOT/.agents/skills`, caminho repo-scoped
descoberto pelo Codex. Elas referenciam os agentes originais em vez de duplicar
conteudo.

Valide com:

```powershell
python C:\Users\israe\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\codex-agent-kit
python C:\Users\israe\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\gsd-tdd-cli-harness
python C:\Users\israe\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\agent-forge
python C:\Users\israe\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\architecture-blueprint
python C:\Users\israe\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\spec-driven-breakdown
python C:\Users\israe\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\multi-agent-delivery
python RUNTIME_Bridge\scripts\validate_arsenal.py
```

## Proximo Passo Para Criar Novas Skills

Quando o usuario pedir explicitamente novas skills, criar em `skills/` dentro
deste kit ou no caminho escolhido pelo usuario, seguindo `skill-creator`:

1. Definir exemplos de uso.
2. Inicializar com `init_skill.py`.
3. Manter `SKILL.md` com menos de 500 linhas.
4. Referenciar arquivos do kit em vez de duplicar conteudo.
5. Validar com `quick_validate.py`.
