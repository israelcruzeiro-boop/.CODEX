---
name: agent-forge
description: Use this skill when a user asks to create, evolve, audit, promote, retire, or repair agents in the local Codex Agent Kit; when no existing agent covers a recurring gap; or when Codex/Claude wrappers need to be generated for a new agent.
---

# Agent Forge

Use this skill to create or evolve agents without weakening the kit.

## Locate The Kit

Resolve `PROJECT_ROOT` as the nearest ancestor containing `AGENTS.md`. Then
resolve `KIT_ROOT` in this order:

1. `PROJECT_ROOT/.codex` when it contains the required kit directories.
2. `PROJECT_ROOT` itself when it contains them (kit-development checkout).
3. Otherwise stop with `QUESTIONAR`; do not infer sibling or copied paths.

Do not derive `KIT_ROOT` from the installed skill directory alone: repo-scoped
skills live under `PROJECT_ROOT/.agents/skills`, while their governed sources
live under `KIT_ROOT`. Require `KIT_ROOT` to contain `F_AgentForge`,
`.codex/agents`, and `.claude/agents`.

Read these files as needed:

- `F_AgentForge/README.md`
- `F_AgentForge/F_Agent_Foreman.md`
- `F_AgentForge/F_Agent_ContextScanner.md`
- `F_AgentForge/F_Agent_AgentArchitect.md`
- `F_AgentForge/F_Agent_AgentComposer.md`
- `F_AgentForge/F_Agent_WorkAuditor.md`
- `F_AgentForge/F_Promoted/COLLECTIVE_MEMORY.md`
- `RUNTIME_Bridge/AGENT_RUNTIME_MAP.toml`

## Creation Gate

Create a new agent only when:

- The task is recurring or likely to recur.
- Existing agents do not cover at least 70 percent of the need.
- A specialist role would reduce real risk or repeated work.
- The new agent can name its triggers, inputs, outputs, delegation rules, and validation criteria.

If the task is one-off or already covered, route to the existing agent instead.

## Agent Design Requirements

Every new or evolved agent must define:

- Identity and mission.
- When to trigger and when not to trigger.
- Required evidence before opinion.
- Allowed and blocked actions.
- Delegation rules.
- Output format.
- Verdict vocabulary.
- Runtime wrappers for Codex and Claude when the agent is promoted.

## Runtime Integration

After creating or renaming an agent:

1. Add or update the source `.md` file in the correct semantic folder.
2. Add or update `.codex/agents/<name>.toml`.
3. Add or update `.claude/agents/<name>.md`.
4. Update `AGENTS.md` if the public catalog, prefix, alias, or pipeline changes.
5. Update `RUNTIME_Bridge/AGENT_RUNTIME_MAP.toml`.
6. Run `python RUNTIME_Bridge/scripts/validate_arsenal.py`.

## Promotion Rules

Promote into `F_AgentForge/F_Promoted` only after:

- The agent executed a real task.
- `F_Agent_WorkAuditor` found it useful.
- Failures and improvements were recorded.
- `COLLECTIVE_MEMORY.md` has any reusable lessons.

Do not delete retired agents; archive them.
