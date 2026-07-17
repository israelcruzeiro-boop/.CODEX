# LOG - Codex Agent Kit

## 2026-07-16 - Correcao De Portabilidade Da CI P1

**Fase:** P1_VALIDATION

**Agentes usados:** integrador raiz, `p1_runtime_quality`,
`p1_arch_adversarial` e revisao independente `p1_spec_forward`.

**O que aconteceu:** o primeiro run GitHub Actions `29543436833` executou a
matriz completa e falhou. Windows expôs uma comparacao lexical entre nomes
curto/longo do mesmo arquivo no teste TOCTOU; Linux e Windows expuseram
classificacao de symlink/reparse dependente da ordem de resolucao. O teste
passou a comparar identidade real e provar que a corrida foi injetada. O
validador agora classifica componentes reparse antes da resolucao final, sem
remover a defesa fail-closed contra escape.

**Evidencia local:** commit `e793dda`; quality gate 8/8; 200 testes verdes; 4
skips locais de symlink por privilegio; testes portaveis cobrem os dois casos
mesmo sem privilegio nativo.

**Status:** APROVADO_COM_RESSALVAS

**Ressalva:** o snapshot corrigido ainda precisa passar nos quatro jobs remotos
Ubuntu/Windows com Python 3.11/3.14.

## 2026-07-16 - P1 Cobertura DEV Operacional

**Fase:** P1

**Agentes usados:** integrador raiz, `p1_dev_coverage`, `p1_patterns_skills`,
`p1_runtime_ci`, `p1_arch_adversarial`, `p1_spec_forward` e
`p1_runtime_quality`.

**O que aconteceu:** o arsenal ganhou perfis DEV verificaveis, quatro
especialistas recorrentes, catalogo de patterns, spec SDD canonica, contratos
de skills, validadores multiagente/Harness e CI propria. Revisoes independentes
encontraram e fecharam falsos positivos em cobertura, arquitetura, fan-in,
claims, rastreabilidade e portabilidade dos testes.

**Evidencia local:** commit `af94406`; quality gate 8/8; 198 testes verdes; 4
skips Windows de symlink por privilegio; 46 wrappers Codex/Claude; 13 perfis;
13 cenarios de perfil; 24 contratos de skills.

**Status:** APROVADO_COM_RESSALVAS

**Ressalvas:** a matriz remota Ubuntu/Windows ainda depende do push. Os 24
contratos de skills foram validados deterministicamente, mas uma execucao
forward-test completa das 24 invocacoes nao foi alegada.
