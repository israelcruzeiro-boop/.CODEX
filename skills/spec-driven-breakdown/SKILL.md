---
name: spec-driven-breakdown
description: Turn ideas, requirements, legacy behavior, or large features into granular, testable, traceable SDD specifications. Use when Codex must define exactly what to build, split work into executable changes, assign stable requirement and task IDs, map requirements to architecture and tests, or establish Definition of Ready and Definition of Done before implementation.
---

# Spec Driven Breakdown

Convert ambiguous work into a contract that implementers and validators can execute without reconstructing intent from chat.

## Locate The Kit

Resolve `PROJECT_ROOT` as the nearest ancestor containing `AGENTS.md`. Then
resolve `KIT_ROOT` in this order:

1. `PROJECT_ROOT/.codex` when it contains the required kit directories.
2. `PROJECT_ROOT` itself when it contains them (kit-development checkout).
3. Otherwise stop with `QUESTIONAR`; do not infer sibling or copied paths.

Do not derive `KIT_ROOT` from the installed skill directory alone: repo-scoped
skills live under `PROJECT_ROOT/.agents/skills`, while their governed sources
live under `KIT_ROOT`. Require `KIT_ROOT` to contain `SPEC_Specs`, `C10_Maestro`,
and `T_Templates`.

Read completely:

- `SPEC_Specs/SPEC_Agent_SpecArchitect.md`
- `C10_Maestro/C10_Method_SDD.md`
- `T_Templates/T_Template_SPEC.md`
- `A_Architecture/A_Method_ModularArchitecture.md` when architecture or module ownership is affected
- `SUP_Supervisor/SUP_Method_Harness.md` when executable proof is required

## Workflow

1. Reconstruct `STATE` from requirements, current code, project memory, architecture, contracts, and consumers. Separate facts, inferences, decisions, and gaps.
2. Assign stable IDs using the canonical prefixes: `SPEC`, `REQ`, `AC`, `NFR`,
   `MOD`, `CON`, `EVT`, `TASK`, `TEST`, `FIT`, and `EVD`. Make `SPEC-NNN`
   match the `changes/NNN-name` folder.
3. Define actors, preconditions, business rules, expected behavior, error and permission cases, non-functional targets, in-scope work, and explicit exclusions.
4. Split distinct executable changes into `.codex/specs/changes/NNN-name/`. Keep one behavioral objective per change.
5. Map affected modules, public contracts, data/migrations, compatibility, rollout, rollback, observability, security, and performance.
6. Produce small tasks with owner, dependencies, input, output, read-set,
   write-set, execution/isolation (`SERIAL`, `PARALLEL`, `SNAPSHOT`, or
   `WORKTREE`), completion criterion, and Harness evidence. Keep task
   dependencies acyclic; self-cycles and longer cycles block the handoff.
7. Build bidirectional traceability: every requirement/acceptance criterion,
   task, test/fitness gate, and evidence must participate in a complete
   requirement -> module/contract/event -> task -> test/fitness -> evidence chain.
8. Mark safe parallel groups only when dependencies are satisfied and no
   write-set overlaps another concurrent read-set or write-set. Use immutable
   snapshots/worktrees or `multi-agent-delivery` when isolation is required.
9. Evaluate Definition of Ready before handoff and Definition of Done before closure.
10. Emit readiness, the canonical global verdict, and the next mandatory agent.

## Quality Rules

- Write measurable acceptance criteria; never use "works well" or equivalent.
- Mark unknown decisions as `PENDENTE`; never fill them with assumptions.
- For a true greenfield or hypothetical spec, mark AS-IS `N/A` with the reason
  and design only the TO-BE. Missing code alone is not blocking; missing product,
  contract, risk, or ownership decisions that change the solution are blocking.
- For brownfield work without repository evidence, do not invent AS-IS; use
  `QUESTIONAR` until the affected code and consumers can be inspected.
- Keep product requirements distinct from implementation choices.
- Keep `REQ/AC/NFR/TASK/TEST/EVD` spec-scoped and qualify cross-spec references
  with `SPEC-NNN:`; every qualifier must resolve to an existing spec and ID.
  Treat `MOD/CON/EVT/INV/PAT/ADR/FIT` as repository-scoped and never qualify
  them with a spec; reuse their canonical IDs without requiring a local
  redefinition for an external `EVT` or `FIT`.
- Require compatibility and rollback for public contracts, data, or deploy changes.
- Require quantified NFRs when performance, capacity, availability, latency, cost, or security is material.
- Do not mark the DoR `APROVADO` while a blocking row in the traceability matrix is empty.
- `APROVADO` requires every DoR/DoD checkbox checked;
  `APROVADO_COM_RESSALVAS` requires a concrete nonblocking gap, action, owner,
  and valid ISO deadline or verifiable `TEST/FIT/EVD` closure criterion, while
  `QUESTIONAR` and `REPROVADO` block the handoff/closure.
- Treat tasks without a dependency as potentially concurrent. Reject literal
  write/read or write/write collisions unless a dependency, serialization,
  immutable snapshot, or worktree isolation is declared.
- Reject every dependency cycle before concurrency analysis. A cyclic edge is
  invalid and must never serialize tasks or suppress a file-set collision.

## Output

Return the generated or updated spec paths, stable IDs, Definition of Ready
result, parallelization groups, blocking gaps, required validators, and a
spec state: `DRAFT | READY_FOR_ARCH | READY_FOR_BREAKDOWN | QUESTIONAR`.
Implementation readiness is the separate DoR verdict. Report that verdict using only
`APROVADO | APROVADO_COM_RESSALVAS | QUESTIONAR | REPROVADO`.
