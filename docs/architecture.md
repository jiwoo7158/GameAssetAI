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
