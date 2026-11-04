# Architecture

## Two-environment model

GameAssetAI intentionally separates **skill development** from **normal asset work**.

### A. GameAssetAI repository

Purpose:

- develop reusable skills
- test Blender MCP behavior
- keep documentation
- version changes in Git
- maintain locally installable skills and their regression evidence

This repository should not become a storage location for the user's game assets.

### B. GameAssetAI-Workspace

Purpose:

- provide a stable Codex source folder for everyday work
- store personal game profiles
- remember existing Unity / Unreal project locations
- select the current profile

Existing projects remain where they already are.

The source `workspace-template/` creates this personal workspace; it is not an asset
output folder. The concrete initial contract is in `docs/workspace-contract.md`.

### C. GameAssetAI_UnityWorkbench (future review environment)

`GameAssetAI_UnityWorkbench` is reserved for an isolated Unity asset-review project, not a
user's game project and not an automatic deployment target. Its intended responsibility is to
inspect imported Models, Rigs, Materials, Animation clips, character/equipment placement and
optional 2D outputs under repeatable camera, lighting and playback conditions.

No current workflow may assume that this project exists, copy assets into an unrelated Unity
project, or modify a user's game. Its path, Unity version, Scenes and installed review code must
be inspected before B6.4 work begins. Creation of the review project is a separate authorized
work item. B8 engine validation should use this isolated review boundary by default unless the
user explicitly selects another safe test project.

## Runtime relationship

```text
Installed GameAssetAI Skills
            +
GameAssetAI-Workspace
            +
       Codex
            +
      Blender MCP
            ↓
         Blender
            ↓
       Unity / files
```

## Development traceability

Significant capability work follows one chain:

```text
requirement ID
  -> bounded work package in roadmap/session state
  -> existing user-facing workflow or internal Skill
  -> native/existing/open-source/custom implementation decision
  -> focused contract tests
  -> representative Blender evidence
  -> optional engine proof
```

Do not infer the later states from the earlier ones. A documented or coded feature is not
necessarily representative, accepted or engine-proven. Tests and fixtures may validate internal
plumbing without changing the product capability status.

External open source is an optional implementation provider, not a new product layer. Evaluate it
in isolation before integration, keep its provenance and license explicit, and place any approved
adapter behind an existing Skill boundary when that Skill already owns the task. Installation and
integration require separate user approval.

## Core production boundary

The user-facing production surface is intentionally smaller than the set of installable helper
Skills:

```text
natural-language request
  -> creation/revision specification
  -> one owning production Skill
  -> internal inspection/copy/bake helpers
  -> visible and semantic acceptance
  -> optional rig/animation, 2D and engine output
```

The specification must carry semantic parts, explicit geometry requirements, art direction and
technical limits. Labels alone are not implementation: geometry, material and budget fields must
affect the Blender result or be reported as unsupported. Narrow validators and render passes are
internal stages unless the user explicitly requests them.

`blender-create-static-asset` v3 is the first bounded implementation of this boundary. It adds an
explicit profile-extrusion geometry operation and copy-only semantic geometry replacement while
retaining v1/v2 primitives and safety contracts. It does not create a general modeling framework;
new operations should be added only from representative production gaps.

## Development artifact boundary

Repository source and local run output are separate layers:

```text
Git repository: Skills + tests + small fixtures
External inputs: user/external FBX, Blend, templates (path + hash + provenance)
Development runs: <artifact-root>/<milestone>/<unique-run-id>/manifest.json
Workspace: installed Skills + profiles + project mappings + recovery backups
```

`scripts/artifact_lifecycle.py` creates and verifies unique development runs and provides a
manifest-gated cleanup operation. The normal default root is
`D:/Blender/MCP_Test/GameAssetAI/runs`, but every command takes an explicit root so another machine
or CI environment can choose its own location. A run manifest records the Skill/version, Git
identity, external input hashes, output hashes, validation state, preservation class,
reproduction command and deletion eligibility.

`ACCEPTED_EVIDENCE` is a minimal representative record, not a requirement to retain every Blend or
render. `TEMPORARY_RUN` is removable only after its manifest explicitly marks it deletion-eligible.
`EXTERNAL_INPUT` and `WORKSPACE_STATE` are never cleanup-tool-owned. Historical paths in validation
documents are citations and do not make those local files runtime dependencies.

## Responsibilities

### Installed skills

Reusable knowledge and procedures.

Examples of future skill categories:

- workspace/profile management
- Blender scene inspection
- game-ready modeling
- existing asset modification
- character preparation
- Mixamo workflow
- animation import / retarget / cleanup
- validation
- Unity export
- downstream 3D-to-2D pixel/cel rendering and sprite output

The final skill taxonomy should be decided through testing, not by creating many speculative skills up front.

The 2D pipeline extends this repository rather than creating a replacement 3D project. Existing
3D Skills remain the source/preparation layer. The Blender Add-on is now a retained execution/UI
layer over tested helpers; it does not replace Skills, profiles, or externally configured Blender
MCP. It is installed and enabled in Blender 5.0 Preferences, with hash alignment, transactional
update/restore and fresh-process survival verified. See
`docs/2d-pixel-pipeline-plan.md`.

### Workspace profile

Game-specific configuration.

Examples:

- engine
- art style
- target platform
- typical mesh budgets
- texture rules
- rig preference
- Mixamo policy
- animation policy
- export destination
- preservation rules for existing assets

### Blender

Blender MCP is externally configured tooling, not something installed by reusable skills.
Current-environment capability verification is planned in `docs/blender-verification.md`.

Source of truth for the current scene state.

When a user has already imported a model, rig, or animation into Blender, skills should prefer inspecting the current scene rather than forcing the user to copy the source file into a special GameAssetAI folder.

## File movement policy

Do not require users to reorganize existing projects.

Do not require normal use of:

- `input/`
- `references/`
- a shared parent directory containing all games

One-off references can be given directly to Codex when needed.

Persistent reusable project rules belong in profiles.

## Local Skill installation

The Git repository is the source of truth.

Validated skills may be installed into the user's own Workspace/client.

Installed copies are generated local copies; edits should happen in this repository
and be revalidated before local replacement. External/public releases are not planned.
Historical ZIP/package tests remain development evidence, not a distribution target.
