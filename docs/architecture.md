# Architecture

## Ownership domains

```text
GameAssetAI repository
  catalog + shared runtime + Skill source + packaging + tests + docs
        |
        | generated self-contained bundle
        v
Installed task-oriented Skills
  vendored runtime + catalog + Workspace template
        |
        | natural-language work in a user-selected folder
        v
GameAssetAI-Workspace
  Profiles + active selection + project bookmarks + preferences + notes + outputs
        |
        +--> Blender/MCP and external source files (explicit targets)
        +--> optional UnityWorkbench (explicit request only)
```

The tracked repository is never a user asset-output store. An ignored, optional `output/` tree may
hold disposable development experiments, but source, tests, catalogs, bundles, and independent
work never depend on it. Installed copies never need the checkout's absolute path. The Workspace
does not contain or relocate existing game projects.

## Source layout

- `src/gameassetai/catalog.py`: data registry loader and state validation.
- `src/gameassetai/specification.py`: provider-neutral Asset Specification contract.
- `src/gameassetai/workspace.py`: create/connect/update and Profile persistence.
- `src/gameassetai/outputs.py`: experiment metadata plus collision-safe disposable numbered tasks.
- `src/gameassetai/distribution.py`: self-contained build, install, backup update, and ZIP.
- `src/gameassetai/blender/`: retained bounded Blender execution modules. These are internal
  capabilities, not separate product Skills.
- `catalog/`: canonical asset/style/provider data.
- `skills/`: four instruction surfaces; generated runtime copies are not source.
- `blender_addon/`: retained optional Blender-native UI/execution layer.

## Provider abstraction

Providers are registered as data with capability, cost, implementation, and evidence fields. The
Asset Specification may name a provider or request `auto`; automatic selection must later filter
for implemented capability and Profile constraints. It must refuse when no suitable provider
exists. A catalog noun never creates a provider module automatically.

Approved external providers require a separate bounded decision covering requirement fit, output
quality, Blender compatibility, license, maintenance, headless behavior, integration cost,
rollback/removal, and an isolated representative test.

## Skill distribution

Source Skills contain only task instructions. The bundle builder copies the shared runtime and
canonical data into each built Skill, writes content hashes, and validates Python syntax. This
duplicates generated artifacts for portability while keeping source implementation single.

Fresh install is no-overwrite and rejects link/reparse-point components. Product update requires
all four existing Skills plus an unused real backup directory. Old folders are moved to the backup
and new staged folders are promoted; a promotion error restores the old paths. The supported Codex
layouts are project-scoped `.codex/skills/<name>/` or user-scoped `~/.codex/skills/<name>/`;
client discovery/refresh and live Blender behavior remain separate manual gates.

Project-scoped onboarding is transactional in order rather than in ownership: create or connect
the user-selected Workspace, validate it, install all four Skills into its `.codex/skills`, validate
the installed manifests, and then create/select a Profile. This prevents a premature `.codex`
directory from making a new target look like an unknown nonempty Workspace. User-scoped install
does not require a Workspace.

## Workspace and outputs

Required Workspace state is only `AGENTS.md`, `config/`, and `profiles/`. `outputs/` and `notes/`
are optional. Profile JSON stores durable game rules and supports explicit validated field-level
updates; per-asset requests do not become Profile rules implicitly. Project paths are bookmarks
and never grant write permission.

Development experiments use
`output/experiments/<experiment>/<category>/<asset>/<number>-<purpose>/`; `experiment.json`
describes the validation goal. User tasks use
`outputs/<active-profile>/<category>/<asset>/<number>-<purpose>/`. The experiment id answers what
is being evaluated, the catalog category answers what kind of asset it is, the asset id answers
which concrete target it is, and the task purpose answers what this preserved result does.

New-versus-existing experiment choice is explicit. The Runtime lists and validates metadata but
does not infer semantic equivalence from names. Allocation derives the next local number from the
current filesystem and claims the directory atomically; there is no date/UUID name or persistent
counter. It rejects linked intermediate directories, escape, unknown categories, active-game
mismatch, and collisions, and it creates no artifact subfolders in advance. Exact continuation
requires an existing in-progress task and recorded artifacts. No catalog, provider, Profile,
Skill, package, or test reads prior results as implicit state. A prior artifact becomes an input
only when the user explicitly selects it.

Legacy `gameassetai.output-run.v1` manifests remain read-only validatable. They are not moved,
renamed, deleted, or used for new allocation.

## Blender execution

Blender MCP is externally configured. Blender-dependent modules are not imported by the offline
foundation. Before an operation, inspect the current Scene and target data. Retained modules are
packaged as internal building blocks for bounded static creation/revision, template humanoids,
Rig/Action/Mixamo operations, FBX, and 2D output; capability labels remain narrower than their file
count.
