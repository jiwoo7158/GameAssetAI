# GameAssetAI Development Instructions

## Product authority

GameAssetAI is an installable Codex Skill system for style-driven, extensible game-asset creation,
revision, and output through Blender and replaceable generation providers. The current product
definition supersedes all historical B-stage, M-stage, audit, and session plans.

Read current authority in this order:

1. `AGENTS.md`
2. the user's current request
3. `docs/product-definition.md`
4. `docs/requirements.md`
5. `docs/architecture.md`
6. `docs/capabilities.md`
7. the active work package in `docs/roadmap.md`
8. implementation and focused tests

For Skill installation or user-Workspace operations, also read `docs/distribution.md` and
`docs/workspace.md` before acting; they provide the current host-path and Profile procedures but do
not override the authority order above.

Git history and the local-only `backup/pre-foundation-20261110` branch preserve the earlier
implementation and evidence record; the branch is not asserted to exist on GitHub and neither is
an active work instruction.

## Product boundaries

- Do not limit characters to humanoids. Anatomy, topology, Rig, parts, and animation policy are
  asset-specific. Humanoid and Mixamo behavior applies only to eligible explicitly selected work.
- Catalog registration is planning data, not implementation or validation evidence.
- Do not claim a generation, revision, style, Rig, animation, 2D, or engine capability that the
  current capability matrix and representative evidence do not support.
- Visual/semantic game usability is the success criterion. Counts, schema validation, topology,
  successful rendering, or export alone do not establish acceptable asset quality.
- Do not finish a production asset as an unrefined collection of primitives merely because a
  structural test passes.
- 3D style specifications and 2D output styles are independent and combinable.
- External AI and paid services are optional providers. The Workspace, catalog, specifications,
  and local core must remain usable without them.
- UnityWorkbench is an optional review mapping used only on explicit request. Never create it or
  modify a real game project implicitly.

## Repository and code rules

- Shared runtime code belongs in `src/gameassetai/`. Do not copy source implementations into
  multiple Skill folders. Installable bundles vendor the shared runtime as generated output.
- Catalog entries and style presets belong in `catalog/`, separate from implementation code and
  personal game Profiles.
- Expose a small task-oriented Skill surface. Add a new Skill only for a distinct repeated user
  task, not for every asset noun or narrow Blender operation.
- Add a Python module only when it has a durable independent responsibility. Do not accumulate
  experiments, numbered variants, backups, or test-output scripts in production source.
- Before a substantial capability change, record one bounded work package in `docs/roadmap.md`
  with requirements, reused components, gap, non-goals, affected files, representative asset,
  acceptance criteria, and unresolved user decisions.
- Prefer Blender native capability, then an existing GameAssetAI helper, then a reviewed external
  open-source provider, then bounded project-owned code. External integration requires explicit
  fit, version, license, maintenance, automation, rollback, and representative-test review.
- When a capability is replaced, remove obsolete implementation, tests, and active documentation
  in the same package. Git history is the recovery mechanism.

## Workspace and data protection

- The development repository, installed Skills, user Workspace, external projects, and output
  runs are separate ownership domains.
- Never hard-code a personal Workspace path. Accept a user-selected path.
- Never overwrite a personal Workspace's `AGENTS.md`, Profiles, settings, notes, or outputs during
  creation or update. Existing recognized Workspaces connect without recreation.
- Existing Blender scenes, models, Rigs, Actions, reference images, game projects, and external
  inputs may live anywhere. Inspect exact targets and preserve originals unless replacement is
  explicitly requested.
- `outputs/` is disposable user output, not runtime state. Code, catalog, Profiles, new generation,
  and independent tests must still work after the entire output tree is deleted.
- Do not require `input/` or `references/` folders. A user may provide direct paths or attachments.
- Never write generated user assets to Git. Development tests use isolated temporary directories.

## Output classification and allocation

- Development experiments belong only under
  `output/experiments/<experiment-id>/<asset-category>/<asset-id>/<number>-<purpose>/`; user game
  work belongs only under
  `<workspace>/outputs/<game-id>/<asset-category>/<asset-id>/<number>-<purpose>/`. General tests
  use operating-system temporary directories.
- An experiment id identifies one validation goal, an asset id identifies one concrete target, and
  a numbered purpose identifies one preserved result for that target. Do not create an experiment
  for every request, merge different validation goals because they share an asset, or create a new
  asset id for a revision of the same target.
- Before development work, inspect existing `experiment.json` metadata and explicitly choose an
  existing experiment or create a descriptive new one. Never infer reuse from a similar folder
  name. If the validation goal is ambiguous, obtain the minimum user clarification.
- Asset categories are the catalog top-level ids `character`, `equipment-prop`, `environment`, and
  `vfx-mesh`. Do not add arbitrary output hierarchy levels.
- Allocate paths only through the shared Runtime. New task folders use the next existing local
  number and a descriptive purpose; never use a date, time, UUID, generic `test`/`final` name, or
  overwrite an existing task. Continue work only from an exact validated in-progress task path.
- Repository `output/` and Workspace `outputs/` are disposable local results, not registries,
  fixtures, package input, or hidden Runtime state. Partial or complete movement/deletion is valid;
  report failure only for a specifically requested missing continuation and allow independent new
  work.

For a fresh project-scoped installation, create or connect and validate the Workspace before
installing all four Skills into its `.codex/skills`. Validate that installation, then create and
select a Profile. User-scoped installation is independent of Workspace creation.

## Blender and acceptance rules

- Verify the current Blender/MCP environment before relying on a tool or behavior.
- Inspect before destructive operations; prefer copies, checkpoints, rollback, and no-overwrite
  publication; report exactly what changed.
- Existing Rigs and animations are first-class inputs. Do not force Rigify, Mixamo, or a new Rig
  when an existing Rig is suitable.
- Define visible and semantic invariants for each representative asset. Review relevant views in
  the actual Blender Scene and record accept/reject evidence before downstream work.
- For humanoids, at minimum check body-part connectivity, left/right limb and foot clearance,
  unintended bridges/self-intersection, and front/side/three-quarter silhouettes.
- A rejected source must not become quality evidence for Rig, animation, 2D, or export, although a
  bounded algorithmic test may remain labeled `tested`.

## Evidence labels

- `tested`: a focused contract or helper passed.
- `representative`: it ran on a semantically relevant asset.
- `accepted`: structural, preservation, and recorded visible/semantic review passed.
- `engine-proven`: the exported artifact passed the intended engine import/runtime gate.

Do not promote a modeling, Rig, animation, style, or end-to-end workflow from synthetic fixtures.
Engine claims require an actual engine round trip.

## Long work and Git safety

Work in recoverable checkpoints. Keep the active branch reviewable, preserve user changes, and
never modify `master` or merge without user approval. If work must stop, finish the atomic change,
run proportionate validation, and update the active roadmap package with the exact continuation.
