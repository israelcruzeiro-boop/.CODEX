# Runtime Bridge

This folder makes the arsenal executable across Codex, Claude, and
Hermes-style runtimes without replacing the original agents.

The runtime contract is versioned in `AGENT_RUNTIME_MAP.toml`. Schema `1`
requires Python 3.11 or newer and is validated on Linux and Windows. Project
coverage is a separate, machine-readable contract in
`PROJECT_COVERAGE_MAP.toml`; it records limitations and fallbacks instead of
claiming universal specialist coverage.

## Source And Installed Layout

The kit is a Git checkout at `PROJECT_ROOT/.codex`. Files inside the checkout
remain the source of truth; the installer materializes only the runtime-facing
copies:

```text
PROJECT_ROOT/
  AGENTS.md                         # managed project template when available
  CLAUDE.md                         # managed Claude template when available
  .agents/skills/                   # installed repository skills (generated)
    agent-forge/
    architecture-blueprint/
    codex-agent-kit/
    gsd-tdd-cli-harness/
    multi-agent-delivery/
    spec-driven-breakdown/
  .codex/                           # kit checkout (KIT_ROOT)
    .codex/agents/*.toml            # Codex wrapper sources
    .claude/agents/*.md             # Claude wrapper sources
    agents/*.toml                   # installed Codex wrappers (generated)
    skills/<canonical-skill>/       # repository skill sources and assets
    RUNTIME_Bridge/
  .claude/agents/*.md               # installed Claude wrappers (generated)
```

Original agent files stay in semantic folders such as `A_Architecture`,
`SUP_Supervisor`, and `F_AgentForge`. Runtime wrappers point back to those
sources. Skills remain reserved for reusable workflows, not every specialist.
The manifest is the exhaustive source of the canonical skill set; the
installer rejects unlisted directories, noncanonical paths and unsupported
schema versions.

## Installation

Clone the governed kit to the exact case-sensitive destination and run from
`PROJECT_ROOT`:

```powershell
git clone <GITHUB_REPOSITORY_URL> .codex
```

```powershell
python .codex/RUNTIME_Bridge/scripts/install_project_runtime.py --project-root .
```

The installer:

- copies Codex wrappers from `KIT_ROOT/.codex/agents` to
  `PROJECT_ROOT/.codex/agents`;
- copies Claude wrappers from `KIT_ROOT/.claude/agents` to
  `PROJECT_ROOT/.claude/agents`;
- recursively projects the six canonical skills from `KIT_ROOT/skills` to the
  Codex repository discovery path at `PROJECT_ROOT/.agents/skills`, including
  `SKILL.md`, `agents/openai.yaml`, and future nested assets;
- creates `PROJECT_ROOT/AGENTS.md` and `PROJECT_ROOT/CLAUDE.md` from the
  project templates only when they are absent; exact existing copies are
  recognized as synchronized, while different content is preserved;
- records managed paths and content hashes in
  `PROJECT_ROOT/.codex/.runtime-install-manifest.json`.

Existing unowned files and locally modified managed files are preserved and
reported as conflicts. The manifest is treated as untrusted input: every entry
must have an exact canonical source-to-target mapping, and its hash alone never
authorizes an overwrite or deletion. A source removal with an existing target
is therefore reported as a stale conflict; remove that target manually after
review and rerun the installer to forget the missing entry. The installer never
removes an unmanaged file, a noncanonical skill, or an empty directory based on
manifest claims. Symlinks and reparse points in managed target paths are
rejected. Canonical source paths are subjected to the same component-by-component
check, so a junction inside the kit cannot redirect installation outside the
Git checkout.

After `git pull`, first inspect the read-only refresh plan and then explicitly
authorize updates whose installed content is provably a historical version of
the same canonical source path in the ancestry of the kit checkout's `HEAD`:

```powershell
python .codex/RUNTIME_Bridge/scripts/install_project_runtime.py --project-root . --dry-run --refresh-managed
python .codex/RUNTIME_Bridge/scripts/install_project_runtime.py --project-root . --refresh-managed
```

`--refresh-managed` does not trust the manifest hash as overwrite authority.
It compares the current target bytes with the canonical path in commits
reachable from `HEAD`; content found only in another local branch, tag, reflog,
or dangling object does not qualify. This allows both an upgrade after
`git pull` and a reviewed working-tree source change while preserving a target
that diverged from governed history. It never overwrites a locally modified
target and never adopts a noncanonical source/target mapping. An existing file
already byte-identical to the canonical source is adopted without overwrite.
Review the dry run and the kit's Git diff before granting the explicit refresh
authority.

Use read-only modes in CI or before upgrading the kit:

```powershell
python .codex/RUNTIME_Bridge/scripts/install_project_runtime.py --project-root . --check
python .codex/RUNTIME_Bridge/scripts/install_project_runtime.py --project-root . --dry-run
```

`--check` exits `0` only when the installed runtime is synchronized, `1` when
safe actions are pending, and `2` on a conflict or unsafe/invalid state.
`--dry-run` prints the same plan without changing files and exits `2` when
conflicts require resolution.

## Validation

Validate the kit sources from the kit root:

```powershell
python RUNTIME_Bridge/scripts/run_quality_gate.py
```

The quality gate compiles the Python tooling, checks generated Claude wrappers,
validates runtime and coverage catalogs, validates skill contracts, executes
the complete unittest suite and rejects a generated diff. The same gate runs
in the repository CI on Linux and Windows.

Validate semantic artifacts in a target project:

```powershell
python RUNTIME_Bridge/scripts/validate_specs.py PROJECT_ROOT
python RUNTIME_Bridge/scripts/validate_architecture.py PROJECT_ROOT
python RUNTIME_Bridge/scripts/validate_multi_agent.py MULTI_AGENT_PLAN.md --phase complete --tasks-dir agent-tasks --results-dir agent-results
python RUNTIME_Bridge/scripts/validate_cli_audit.py CLI_AUDIT.md
```

The semantic validators are read-only, use only the Python standard library,
support `--json`, and return a nonzero exit code when a blocking contract fails.

Run the installer after adding, renaming, or removing wrappers or canonical
skill assets. Run both kit-validation commands before publishing a kit change.
