---
name: multi-agent-delivery
description: Coordinate complex software work with parallel Codex subagents while protecting context and file ownership. Use when a task has two or more independent workstreams, needs specialist reviews, can benefit from parallel exploration or validation, or requires an explicit plan for partitioning, spawning, waiting, reconciling, integrating, and proving multi-agent results.
---

# Multi-Agent Delivery

Run bounded subagent work as a controlled delivery graph. Keep the root agent responsible for requirements, integration, decisions, and the final verdict.

## Locate The Kit

Resolve `PROJECT_ROOT` as the nearest ancestor containing `AGENTS.md`. Then
resolve `KIT_ROOT` in this order:

1. `PROJECT_ROOT/.codex` when it contains the required kit directories.
2. `PROJECT_ROOT` itself when it contains them (kit-development checkout).
3. Otherwise stop with `QUESTIONAR`; do not infer sibling or copied paths.

Do not derive `KIT_ROOT` from the installed skill directory alone: repo-scoped
skills live under `PROJECT_ROOT/.agents/skills`, while their governed sources
live under `KIT_ROOT`. Require `KIT_ROOT` to contain `SUP_Supervisor`,
`C10_Maestro`, and `T_Templates`.

Read completely:

- `SUP_Supervisor/SUP_Method_MultiAgentDelivery.md`
- `SUP_Supervisor/SUP_PICK_AgentSelector.md`
- `C10_Maestro/C10_CAMISA10.md`
- `T_Templates/T_Template_MULTI_AGENT_PLAN.md`
- `T_Templates/T_Template_AGENT_TASK.md`
- `T_Templates/T_Template_AGENT_RESULT.md`

## Delegation Gate

Use subagents only for concrete bounded work that can progress independently. Prefer parallel read-heavy discovery, review, tests, log analysis, or isolated write-sets. Keep serial work in the root thread when tasks share decisions, files, or an unresolved contract.

## Workflow

1. Create a DAG with stable task IDs, dependencies, join conditions, agent role, read-set, write-set, and expected evidence.
2. Reserve one runtime thread for the root. Respect the active runtime cap; never assume every planned task can run simultaneously. Keep direct-child fan-out as the default and recursive delegation disabled unless configuration and the plan explicitly allow it.
3. Give each subagent the minimum context packet from `T_Template_AGENT_TASK.md`. Include raw artifacts and constraints, not the intended answer.
4. Spawn independent tasks in parallel. A writer's write-set must not overlap
   another concurrent task's read-set or write-set. Use immutable
   snapshots/worktrees or serialize when isolation cannot be proven.
5. Monitor and steer only when scope, evidence, or blockers change. Do not duplicate a running task silently.
6. Wait for every required join dependency. Collect the result envelope from `T_Template_AGENT_RESULT.md` instead of raw logs.
7. Reconcile contradictions against primary evidence. Record unresolved conflicts and run a bounded challenge pass when the decision is material.
8. Integrate writes through one owner, then rerun affected validation after integration.
9. Synthesize facts, inferences, gaps, commands, exit codes, and the final verdict in the root thread.

## Hard Rules

- The root agent owns the plan, user communication, integration, and final claim.
- A subagent result is evidence, not automatic truth.
- Do not close while a required agent is still running or a join condition is unmet.
- Do not let two agents edit the same file concurrently.
- Do not let an agent read a mutable file while another concurrent task writes
  it; pin a source fingerprint or isolate the reader.
- Do not broaden permissions through delegation; subagents inherit the parent runtime boundary.
- Record timeouts, interrupted agents, and incomplete evidence as gaps.

## Output

Return the DAG, agents actually used, skipped or failed tasks, evidence ledger,
conflicts and resolutions, integration validation, remaining gaps, and a run
status: `COMPLETE | COMPLETE_COM_RESSALVAS | INCOMPLETE`. Report the verdict
separately using only
`APROVADO | APROVADO_COM_RESSALVAS | QUESTIONAR | REPROVADO`.
