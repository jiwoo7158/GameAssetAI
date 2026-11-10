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

The repository is never an asset-output store. Installed copies never need its absolute path.
The Workspace does not contain or relocate existing game projects.

## Source layout

- `src/gameassetai/catalog.py`: data registry loader and state validation.
- `src/gameassetai/specification.py`: provider-neutral Asset Specification contract.
- `src/gameassetai/workspace.py`: create/connect/update and Profile persistence.
- `src/gameassetai/outputs.py`: collision-safe disposable output runs.
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

Fresh install is no-overwrite. Product update requires all four existing Skills plus an unused
backup directory. Old folders are moved to the backup and new staged folders are promoted; a
promotion error restores the old paths. Client discovery/refresh and live Blender behavior remain
separate manual gates.

## Workspace and outputs

Required Workspace state is only `AGENTS.md`, `config/`, and `profiles/`. `outputs/` and `notes/`
are optional. Profile JSON stores durable game rules. Project paths are bookmarks and never grant
write permission.

An output run contains a descriptive manifest and only requested artifacts. No catalog, provider,
Profile, Skill, or test reads prior runs as implicit state. A prior artifact becomes an input only
when the user explicitly selects it.

## Blender execution

Blender MCP is externally configured. Blender-dependent modules are not imported by the offline
foundation. Before an operation, inspect the current Scene and target data. Retained modules are
packaged as internal building blocks for bounded static creation/revision, template humanoids,
Rig/Action/Mixamo operations, FBX, and 2D output; capability labels remain narrower than their file
count.
