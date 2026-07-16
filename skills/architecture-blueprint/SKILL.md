---
name: architecture-blueprint
description: Design, document, or validate technical architecture for new and existing software projects. Use when a task needs explicit AS-IS versus TO-BE architecture, modular boundaries, module ownership, public contracts, dependency rules, design-pattern mapping, ADRs, or executable architecture fitness gates before implementation.
---

# Architecture Blueprint

Create architecture that is specific enough to guide implementation and concrete enough to verify.

## Locate The Kit

Resolve `PROJECT_ROOT` as the nearest ancestor containing `AGENTS.md`. Then
resolve `KIT_ROOT` in this order:

1. `PROJECT_ROOT/.codex` when it contains the required kit directories.
2. `PROJECT_ROOT` itself when it contains them (kit-development checkout).
3. Otherwise stop with `QUESTIONAR`; do not infer sibling or copied paths.

Do not derive `KIT_ROOT` from the installed skill directory alone: repo-scoped
skills live under `PROJECT_ROOT/.agents/skills`, while their governed sources
live under `KIT_ROOT`. Require `KIT_ROOT` to contain `A_Architecture`,
`DOC_Documentation`, and `T_Templates`.

Read completely:

- `A_Architecture/A_Agent_CrossStackArchitect.md`
- `A_Architecture/A_Method_PlantaTecnica.md`
- `A_Architecture/A_Method_ModularArchitecture.md`
- `A_Architecture/A_Method_PatternMap.md`

Load the matching templates only when creating artifacts:

- Brownfield AS-IS: `DOC_Documentation/DOC_Template_ARCHITECTURE.md`
- Greenfield or planned change TO-BE: `DOC_Documentation/DOC_Template_TARGET_ARCHITECTURE.md`
- Pattern decisions: `DOC_Documentation/DOC_Template_PATTERN_MAP.md`

## Choose The Architecture Mode

1. Use `AS_IS` when documenting code that already exists. Derive every claim from files, manifests, schemas, routes, imports, deployment config, or tests.
2. Use `TO_BE` when designing a new system or structural change. Tie every
   proposed element to a requirement, migration step, and acceptance gate; tie
   material trade-offs to an ADR. Mark ADR `N/A` with reason when no material
   decision exists.
3. Use `TRANSITION` when comparing current and target states. Keep both artifacts separate and create an ordered migration path with compatibility and rollback.

Never describe a proposed module as if it already exists.

## Workflow

1. Identify `PROJECT_ROOT`, affected repositories, runtime environments, actors, critical flows, quality attributes, constraints, and existing ADRs.
2. Map problem domains, ubiquitous language, invariants, owners, data ownership, and external consumers.
3. Build the module catalog required by `A_Method_ModularArchitecture.md`: public API, owned data, dependencies, events, consistency, transactions, failure modes, and evolution rules.
4. Draw dependency and interaction views. Reject unexplained cycles and cross-module access that bypasses public contracts.
5. Discover or propose patterns through `A_Method_PatternMap.md`. Record code
   presence separately from normative decision, plus evidence, forces,
   alternatives, contraindications, trade-offs, ADR, and enforcement gate. Do
   not add patterns for prestige.
6. Define contracts and compatibility: HTTP/API, events, jobs, webhooks, schemas, error semantics, versioning, idempotency, and rollout order as applicable.
7. Define fitness gates that can detect drift: dependency rules, contract tests, schema checks, route checks, build/test commands, or review checks with an owner.
8. Materialize or update the correct artifacts. Keep AS-IS, TO-BE, ADRs, and pattern map linked but non-duplicated.
9. Return facts, inferences, gaps, trade-offs, validation commands, and the next mandatory agent.

## Completion Gate

Do not mark the architecture ready when any affected module lacks an owner or
public boundary, a dependency direction is ambiguous, an AS-IS claim lacks
evidence, a TO-BE element lacks a requirement, a material decision lacks an ADR,
a proposed transition lacks rollback, or a rule has no enforceable gate.

Report readiness separately as `READY_FOR_SPEC`, `READY_FOR_IMPLEMENTATION`, or
`NOT_READY`. Use only the canonical global verdict:
`APROVADO | APROVADO_COM_RESSALVAS | QUESTIONAR | REPROVADO`.
