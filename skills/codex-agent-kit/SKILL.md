---
name: codex-agent-kit
description: Use this skill when a user asks Codex to use, validate, organize, evolve, install, or operate the local Codex Agent Kit; when a task needs agent selection, project governance, SDD/spec flow, cross-stack gates, or coordination between Codex and Claude wrappers.
---

# Codex Agent Kit

Use this skill to operate the local agent arsenal as a runtime-aware governance layer.

## Locate The Kit

Resolve the kit root in this order:

1. If this skill is inside the kit, use the directory two levels above this file.
2. Otherwise search upward for a folder containing `AGENTS.md`, `.codex/agents`, `.claude/agents`, and `C10_Maestro`.
3. Treat the found folder as `KIT_ROOT`.

Never duplicate agent content into this skill. The source of truth remains the original agent files under `KIT_ROOT`.

## Load Order

For agent selection or governance work, read only what is needed:

1. `AGENTS.md` for the catalog, rules, gates, and aliases.
2. `SUP_Supervisor/SUP_PICK_AgentSelector.md` for routing complex work.
3. `C10_Maestro/C10_CAMISA10.md` when orchestration, phase, memory, or brief is needed.
4. `RUNTIME_Bridge/AGENT_RUNTIME_MAP.toml` when checking runtime compatibility.
5. The selected agent source files only after the team is chosen.

## Operating Rules

- Keep `.codex/` as the source of truth for original agents and templates.
- Keep `.codex/agents/*.toml` as Codex wrappers.
- Keep `.claude/agents/*.md` as Claude wrappers.
- Keep `skills/` for compact reusable workflows, not one skill per agent.
- Use `RUNTIME_Bridge/scripts/validate_arsenal.py` before declaring the arsenal functional.
- Prefer evidence from files and commands over generic confidence.

## Standard Flow

For complex, risky, ambiguous, multi-domain, implementation, refactor, bugfix, audit, planning, or agent-selection requests:

1. Use `@PICK` to choose the team and order.
2. Use `@CRED` before external access, browser, APIs, database, deploy, or production.
3. Use `@C10`, `@SPEC`, `@DOC`, `@A`, `@C`, `@GSD`, and validators as required by `AGENTS.md`.
4. Load specialist agents only when their domain is actually involved.
5. Finish with real validation evidence and a clear list of gaps.

For small tasks, use the minimal relevant agent and skip ceremonial steps.

## Compatibility Checks

When asked whether the kit works in Codex and Claude:

1. Run `python RUNTIME_Bridge/scripts/validate_arsenal.py` from `KIT_ROOT`.
2. Confirm every Codex wrapper has `name`, `description`, and `developer_instructions`.
3. Confirm every Claude wrapper has frontmatter `name` and `description`.
4. Confirm each wrapper points to an existing source file.
5. Confirm the three runtime skills validate with the Codex skill validator.

## Output Shape

When selecting agents, return:

- Task understood.
- Selected team and order.
- Agents intentionally not used.
- Gaps or missing context.
- Next mandatory step.

When validating the kit, return:

- Codex status.
- Claude status.
- Skills status.
- Runtime bridge status.
- Blocking issues.
- Recommended next actions.
