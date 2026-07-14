# Runtime Bridge

This folder makes the arsenal executable across Codex, Claude, and Hermes-style runtimes without replacing the original agents.

## Layout

- `../AGENTS.md`: catalog and governance source of truth.
- `../.codex/agents/*.toml`: Codex wrappers.
- `../.claude/agents/*.md`: Claude wrappers.
- `../skills/*/SKILL.md`: compact workflow skills.
- `AGENT_RUNTIME_MAP.toml`: runtime manifest.
- `scripts/validate_arsenal.py`: local validation.

## Rules

1. Original agent files stay in semantic folders such as `A_Architecture`, `SUP_Supervisor`, and `F_AgentForge`.
2. Runtime wrappers must point back to the original source file.
3. Skills are reserved for reusable workflows, not every specialist.
4. Validate after adding, renaming, or promoting an agent.

## Validation

Run from the kit root:

```powershell
python RUNTIME_Bridge/scripts/validate_arsenal.py
```

Use a clean result as the baseline before copying this kit into a project.
