# Architecture

## Ownership domains

```text
GameAssetAI repository
  catalog + shared runtime + Skill source + packaging + tests + docs
        |
        | verified build from an approved master commit
        v
Generated dist/workspace product tree
  product instructions + four self-contained Skills + initialization templates
        |
        | project clone, or copy the same Skills to user scope
        v
GameAssetAI-Workspace
  tracked product files + ignored Profiles/settings/notes/results
        |
        +--> Blender/MCP and external source files (explicit targets)
        +--> optional UnityWorkbench (explicit request only)
```

The development repository is never a user asset-output store. The generated `dist/workspace`
branch is product output, not a development branch; it is updated only by the master-push
publication workflow and keeps normal append-only Git history. An ignored, optional `output/` tree may
hold disposable development experiments, but source, tests, catalogs, bundles, and independent
work never depend on it. Installed copies never need the checkout's absolute path. The Workspace
does not contain or relocate existing game projects.

## Source layout

- `src/gameassetai/catalog.py`: data registry loader and state validation.
- `src/gameassetai/specification.py`: provider-neutral Asset Specification contract.
- `src/gameassetai/workspace.py`: create/connect/update and Profile persistence.
- `src/gameassetai/outputs.py`: experiment metadata plus collision-safe disposable numbered tasks.
- `src/gameassetai/distribution.py`: self-contained Skill and Workspace-distribution build,
  validation, install, backup update, and ZIP.
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

The Workspace-distribution builder allowlists product files into one generated tree: root product
instructions, four Skills under `.agents/skills/`, initialization templates under
`templates/workspace/`, Git ownership rules, and source/version/hash metadata. Development tests,
roadmaps, source layout, local experiments, Profiles, settings, notes, and results are not product
branch inputs. Text hashes are line-ending neutral and the generated `.gitattributes` fixes LF so
normal Windows and Linux clones validate identically.

Fresh standalone Skill install is no-overwrite and rejects link/reparse-point components. Product update requires
all four existing Skills plus an unused real backup directory. Old folders are moved to the backup
and new staged folders are promoted; a promotion error restores the old paths. The supported Codex
layouts are project-scoped `.agents/skills/<name>/` and user-scoped
`$HOME/.agents/skills/<name>/`. Existing legacy `.codex/skills` copies are neither moved nor
deleted automatically. Client discovery/refresh and live Blender behavior remain separate manual
gates.

Normal project-scoped onboarding clones `dist/workspace`, verifies its metadata and four installed
Skills, then initializes only missing ignored personal state. Initialization requires a real Git
clone, preflights the complete candidate Workspace, and never replaces a Profile or setting. The
older bundle installation route remains transactional in order: create/connect and validate the
Workspace, install into `.agents/skills`, validate, then create/select a Profile. User-scoped
installation is a copy of those same four Skill directories and does not require a Workspace.

## Workspace and outputs

Required initialized Workspace state is only `AGENTS.md`, `config/`, and `profiles/`. `outputs/`
and `notes/` are optional personal data. In a distribution clone, tracked root instructions,
`.agents/skills`, templates, and distribution metadata are product-managed while `config/`,
`profiles/`, `notes/`, `outputs/`, and `AGENTS.local.md` are ignored personal paths. Profile JSON
stores durable game rules and supports explicit validated field-level updates; per-asset requests
do not become Profile rules implicitly. Project paths are bookmarks and never grant write
permission.

Development experiments use
`output/experiments/<experiment>/<category>/<asset>/<number>-<purpose>/`; `experiment.json`
describes the validation goal. User tasks use
`<selected-root>/<active-profile>/<category>/<asset>/<number>-<purpose>/`. The selected root is, in
descending precedence, an explicit one-task root, Profile `output_defaults.root`, Workspace
`settings.preferences.output_root`, or internal `<workspace>/outputs`. External roots must already
exist and require the owning Workspace when validating or continuing a task. The experiment id
answers what is being evaluated, the catalog category answers what kind of asset it is, the asset id answers
which concrete target it is, and the task purpose answers what this preserved result does.

New-versus-existing experiment choice is explicit. The Runtime lists and validates metadata but
does not infer semantic equivalence from names. Allocation derives the next local number from the
current filesystem and claims the directory atomically; there is no date/UUID name or persistent
counter. It rejects linked intermediate directories, escape, unknown categories, active-game
mismatch, and collisions, and it creates no artifact subfolders in advance. Exact continuation
requires an existing in-progress task and recorded artifacts. No catalog, provider, Profile,
Skill, package, or test reads prior results as implicit state. A prior artifact becomes an input
only when the user explicitly selects it.

The official artifact kinds map to on-demand `models/`, `previews/`, `sprites/`, and `exports/`
directories. A producer first atomically reserves a descriptive no-overwrite path in the local
manifest, writes the real nonempty file, and registers it to consume the reservation. An abandoned
reservation can be released only while no file exists at that path. `complete` records that production ended without
a quality decision. `accepted` and `rejected` require a human-visible/semantic review summary and
distinct registered evidence that is still an existing nonempty real file inside the exact task
at transition time; linked/Junction evidence and path escape are refused. Tests or successful file
creation do not confer acceptance. Reviewed states are terminal, while `complete` may later
receive a review without reopening publication. Later evidence movement/deletion does not rewrite
the historical decision or block independent allocation.

Asset Specification output formats are logical requests, while artifact kinds describe files the
task lifecycle can safely reserve and register. The explicit contract maps `blend` to model
`.blend`, `fbx` to export `.fbx`, plain `png` to preview or sprite `.png`, and sprite-sheet/sequence
requests to sprite `.png`. Extra registrable export and preview extensions preserve existing-file
workflows and are not implementation claims for generation, Blender export, or engine import.

Legacy `gameassetai.output-run.v1` and prior numbered-task manifests remain read-only validatable.
They are not moved, renamed, deleted, or used for new allocation.

## Blender execution

Blender MCP is externally configured. Blender-dependent modules are not imported by the offline
foundation. Before an operation, inspect the current Scene and target data. Retained modules are
packaged as internal building blocks for bounded static creation/revision, template humanoids,
Rig/Action/Mixamo operations, FBX, and 2D output; capability labels remain narrower than their file
count.
