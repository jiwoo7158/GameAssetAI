# GameAssetAI Development Instructions

This repository develops reusable skills and support tooling for Blender game-asset workflows.

## Mission

Build a reliable, testable skill system that lets Codex use Blender through MCP for game-asset work.

The system must support:

- new asset creation
- modification of existing assets
- static meshes
- characters
- existing armatures and skeletons
- Mixamo-oriented humanoid workflows
- imported animations
- animation cleanup / editing
- Unity-first export
- Unity export and import validation
- different art styles per game
- a Blender-native Add-on as the repeatable UI/execution layer over tested Skills
- optional downstream Pixel/Cel/Toon image and sprite output after a 3D source is accepted

## Important boundaries

Do not assume that:

- every asset should be generated from scratch
- every character should be rigged by GameAssetAI
- every animation should be authored from scratch
- all projects share one art style
- all projects share one polygon budget
- Unity or Blender projects will be moved into this repository
- the user will maintain `input/` or `references/` folders for normal work

Existing models, rigs, animations, Blender scenes, Unity projects, and Unreal projects may live anywhere.

Current scope decision (2026-09-21): do not develop Unreal-specific support or
external/public Skill distribution. Keep local Skill installation and regression
testing so the personal GameAssetAI-Workspace remains usable. Do not delete or
relocate any pre-existing Unreal project, user source asset, Git-tracked decision history, or
non-reproducible external input. This does not require permanent retention of GameAssetAI-owned
local test output that is reproducible from Repository code and explicit external inputs.

Game-specific settings belong in a workspace profile, not in reusable skills.

## Development approach

Prefer evidence-driven development.

For each significant skill:

1. define the use case
2. identify Blender / MCP capabilities needed
3. document assumptions
4. use fixtures for contracts/plumbing and representative assets for semantic capability claims
5. record failure cases
6. update the skill
7. re-run regression tests
8. only then treat the workflow as stable

Do not create large collections of untested skills merely to fill the repository.

Before a new Skill or a substantial implementation change, record a bounded work package in the
active roadmap or session state. It must identify the requirement IDs being advanced, the existing
Skills/helpers to reuse, the concrete gap, non-goals, affected files, validation asset, acceptance
criteria and any decision that still requires user approval. A test asset is evidence for the work
package, not the product objective.

Before choosing a new capability or continuation point, read the current decisions in this order:

1. `AGENTS.md`
2. the user's current requirements and the relevant implementation code
3. `docs/audits/2026-11-02-repository-review.md`
4. `docs/IMPLEMENTATION_MEMORY.md`
5. `docs/SESSION_STATE.md`
6. the active section of `docs/roadmap.md`

`docs/PROJECT_AUDIT.md`, older Skill audits, validation reports and session history remain useful
evidence, but they are historical inputs rather than current work-order authority. When a status
claim conflicts with implementation, inspect the code and representative evidence before deciding.

Do not let optional render passes, collider/LOD diagnostics, Unity-only checks, or additional
micro-Skills displace a missing core creation, rig/adaptation, Mixamo, export, or Add-on gate.

Choose implementation technology in this order:

1. Blender's supported native capability;
2. an existing GameAssetAI Skill/helper;
3. a reviewed external open-source project;
4. bounded project-owned implementation.

This is a decision order, not a requirement to use every layer. Before adopting open source,
record requirement fit, output quality, Blender-version compatibility, license, maintenance,
automation/headless behavior, integration cost, rollback/removal path and a representative
isolated test. Do not install or make an external project a required dependency without explicit
user approval. Studying its workflow or algorithms does not authorize copying incompatible code.

## Skill design rules

A reusable skill should:

- solve a repeatable task
- avoid hard-coding one game's art direction
- read the active game profile when project-specific constraints matter
- inspect the current Blender scene before destructive changes
- preserve existing mesh / rig / animation data unless replacement is explicitly requested
- prefer reversible or duplicated changes before destructive edits
- distinguish analysis from modification
- validate results after modification
- state uncertainty when Blender state cannot be verified
- keep game-engine export as a separate concern when practical
- link its responsibility to stable IDs in `docs/requirements.md`
- state whether it uses only Blender/GameAssetAI code or an approved external dependency
- distinguish its implementation state from its strongest evidence state

The Skill folders are implementation modules, not all separate user-facing product commands.
Prefer a small product surface for static creation/revision, character creation/revision,
existing-character rig/animation work, engine export, and optional 3D-to-2D output. Route narrow
inspect/copy/bake/pass helpers internally or expose them only when explicitly needed.

Skills that opt into `gameassetai.skill-contract.v1` must follow `docs/skill-design.md`. The
repository validator enforces only the contract's structural fields; Blender and representative
evidence still determine whether the capability is usable.

## Blender / MCP rules

Before relying on an MCP behavior, verify it in the current environment.

Do not assume a tool exists because an older README mentioned it.

When performing potentially destructive operations:

- inspect the target first
- save or duplicate when appropriate
- avoid deleting existing armatures or actions without explicit need
- report what changed

Prefer Blender's native data model and Python API when this is more deterministic than UI-driven actions.

## Semantic and visual acceptance

Structural evidence is necessary but does not certify a usable asset. Counts, one connected
component, watertight/manifold topology, normalized weights, lower numerical error, successful
rendering, or successful export are not substitutes for semantic and visual acceptance.

Before a generated or materially revised asset is routed downstream:

- define the visible and semantic invariants for that asset type
- run structural and preservation checks
- inspect representative views in the actual Blender Scene
- record explicit accept/reject evidence
- stop when the source is visibly or semantically invalid

For humanoids, at minimum check intended body-part connectivity, left/right limb and foot
clearance, unintended bridges/self-intersection, and front, side, and three-quarter silhouettes.
A rejected source must not feed rigging, weight refinement, animation, 2D output, or engine export.
Downstream algorithms may remain valid implementation evidence, but their results are not product
quality evidence when the input was rejected.

Keeping one current candidate visible is a review convenience, not a user-imposed preservation
mandate. Do not claim that the user required a Scene, Object, or Blender process to remain open
unless they explicitly did. When a verified checkpoint exists, lifecycle tests such as a fresh
Blender-process or restart check may proceed without accumulating candidates. Distinguish:

- preserving recoverable work and avoiding accidental loss;
- keeping one current candidate visible for review;
- an explicit user requirement not to close, replace, or restart something.

Only the third is a user constraint. The first two are implementation choices and must be stated
as such.

Cube and synthetic fixtures are appropriate for API, encoding, rollback, cleanup, and other
plumbing tests where semantic shape is irrelevant. They cannot establish character, weapon,
enemy, prop, rig, animation, or general modeling quality.

## Rigging and animation principles

Humanoid characters may use Mixamo.

Existing rigs and animations are first-class inputs.

A valid workflow may be:

```text
existing mesh/rig/animation
→ inspect
→ adapt / retarget / clean
→ validate
→ export
```

Do not force Rigify, Mixamo, or any other rigging system when an existing rig is already suitable.

## Workspace contract

Normal user work happens in a separate `GameAssetAI-Workspace`.

The workspace contains:

- one stable workspace `AGENTS.md`
- game profiles
- optional mappings to existing Unity / Unreal projects
- current active profile
- optional notes

This repository contains the template and tooling used to create that workspace.

## Documentation policy

Keep:

- `README.md` user-facing
- `AGENTS.md` development-facing
- `docs/` for architecture, requirements, research, and decisions
- `skills/` for installable skill source
- `tests/` for validation plans / fixtures
- `scripts/` for reusable development tooling

Update documentation when architecture, priority, capability status, or acceptance evidence
changes. Preserve failed experiments as clearly labeled `rejected`, `experimental`, or historical
evidence; never leave them described as the current successful continuation point.

When Skill instructions change, update the installed local copy through the hash-checked
deployment/update workflow and preserve the previous installed copy. Source-only edits do not
prove that normal Workspace sessions will use the new behavior.

The Blender Add-on is a retained core product layer. Do not infer availability from source tests
or session-only registration. Persistent Preferences installation, version/update verification,
and survival in a fresh Blender process are required before calling it installed or available.

## Development artifact lifecycle

The Git repository is the only source baseline for reusable Skill code, tests and small legal
fixtures. Local `.blend`, `.fbx`, `.png`, `.json`, ZIP and experiment directories are evidence or
inputs, never implicit runtime dependencies.

- Put new development/validation outputs under an explicit artifact root, normally
  `D:/Blender/MCP_Test/GameAssetAI/runs`, using `scripts/artifact_lifecycle.py`. Do not force this
  location on normal user asset output.
- Give each run a unique directory and manifest. Never silently overwrite an earlier run.
- Classify files as `PERMANENT_SOURCE`, `ACCEPTED_EVIDENCE`, `TEMPORARY_RUN`, `EXTERNAL_INPUT`, or
  `WORKSPACE_STATE`. Only source belongs automatically in Git; retain accepted evidence minimally.
- Treat user-supplied Mixamo files, external templates and original assets as `EXTERNAL_INPUT`.
  Record path/hash/provenance when used; do not copy or delete them implicitly.
- Active tests must accept external input and output paths. If an optional binary input is absent,
  skip or refuse with the exact reason instead of depending on a developer's private directory.
- Cleanup is dry-run by default. Delete only an exact, manifest-owned `TEMPORARY_RUN` explicitly
  marked deletion-eligible; never follow links/junctions or intersect the repository, Workspace,
  personal profiles, external projects, or original inputs.
- Pre-lifecycle legacy output may lack a manifest. It may be deleted only in a bounded cleanup
  requested by the user after active code/reference checks establish GameAssetAI ownership,
  reproducibility and that it is not a unique input. Exact paths/patterns, dry-run facts and the
  deletion result must be recorded; absence of `manifest.json` alone is neither protection nor
  deletion authority.
- At work-package closeout, verify accepted evidence, remove owned disposable intermediates, and
  record reproduction instructions. Historical absolute paths may remain as evidence citations,
  but must not be described as required current inputs.

## Completion policy

A skill is not "done" because its `SKILL.md` exists.

A skill is considered stable only after:

- expected inputs are defined
- expected outputs are defined
- failure behavior is defined
- at least one representative Blender test succeeds
- important destructive operations are guarded
- known limitations are documented

Use evidence labels precisely:

- `tested`: a bounded helper or contract passed its focused checks
- `representative`: it ran on an asset whose semantics match the claimed use case
- `accepted`: structural checks plus recorded visible/semantic review passed
- `engine-proven`: the actual exported artifact passed the intended engine import/runtime gate

Do not promote a modeling, rigging, animation, or end-to-end workflow to stable from a synthetic
fixture alone. At least one representative accepted Blender asset is required, and engine claims
require an actual engine round trip.

## Long-running work

For long tasks, work in recoverable checkpoints.

If execution may stop because of usage limits or another external constraint:

- finish the current atomic change when possible
- run relevant validation
- avoid leaving knowingly broken intermediate state
- update `docs/SESSION_STATE.md` with the exact continuation point

Never invent remaining Codex quota if it cannot be inspected from the current environment.
