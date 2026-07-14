---
name: gsd-tdd-cli-harness
description: Use this skill for implementation, bugfix, refactor, release, or validation work that needs acceptance criteria, proportional TDD, real CLI evidence, bug sweep, test planning, and final delivery proof using the Codex Agent Kit GSD method.
---

# GSD TDD CLI Harness

Use this skill to make implementation work provable.

## Locate The Kit

Resolve `KIT_ROOT` as the nearest folder containing `AGENTS.md`, `GSD_DeliveryDiscipline`, `SUP_Supervisor`, and `T_Templates`.

Read these files as needed:

- `GSD_DeliveryDiscipline/GSD_Agent_TDDCLIAuditor.md`
- `SUP_Supervisor/SUP_Method_Harness.md`
- `C10_Maestro/C10_Method_SDD.md`
- `T_Templates/T_Template_CLI_AUDIT.md`

## Before Editing

1. Identify the project root and affected apps/services/packages.
2. Read the real files and contracts involved.
3. Define acceptance criteria.
4. Decide proportional validation:
   - No-risk docs/config change: inspect and explain.
   - Small code change: targeted test or smoke command.
   - Behavior change: test first where feasible, then implementation.
   - Cross-stack/high-risk change: lint, typecheck, tests, smoke, and final validator.

## During Work

- Keep scope small.
- Do not refactor sideways.
- Do not hide pre-existing failures.
- Track commands with cwd, command, exit code, and result.
- If a command is unavailable, record why and choose the next best evidence.

## After Editing

Run the strongest reasonable command set for the project:

1. Formatter/lint if configured.
2. Typecheck/build if configured.
3. Unit or integration tests for affected area.
4. Smoke/manual verification when tests do not cover behavior.

Then perform a bug sweep:

- Broken imports or names.
- Missing env variables or secrets exposure.
- Contract mismatch between frontend/backend/mobile.
- Missing auth/permission check.
- Missing migration/rollback when data changes.
- Missing empty/error/loading states for UI.
- Race/idempotency issue in critical flows.

## Output Shape

Return a compact Harness report:

- Scope.
- Acceptance criteria.
- Commands run with cwd and exit code.
- Evidence summary.
- Bugs or risks found.
- Lacunas not verified.
- Verdict: `APROVADO`, `APROVADO_COM_LACUNAS`, `QUESTIONAR`, or `BLOQUEADO`.
