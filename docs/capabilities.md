# Capability Status

Status terms: `available` means the current active foundation feature is usable; `environment-ready`
means a tool can be invoked safely but no representative asset capability was proved; `planned`
means catalog/design only. Evidence labels follow `AGENTS.md`. Archived code and historical tests
are never current evidence by themselves.

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Catalog and style registry | available | tested | JSON registration and validation; no generator implied. |
| Asset Specification | available | tested | Provider-neutral validation; no automatic production orchestration yet. |
| Reusable generation providers | planned | none | `blender-native`, `procedural-python`, and `existing-asset-revision` remain registered planning ids with no adopted reusable implementation or current evidence. This does not prohibit Codex-directed native operations or bounded task-specific code. |
| Workspace create/connect/update | available | tested | Current v2 plus non-mutating legacy recognition; no automatic legacy migration. |
| Profile persistence/switching | available | tested | JSON Profiles, exact active selection, explicit atomic field get/set, and catalog/dimension validation of official style ids; freeform game rules remain separate. |
| Development experiment and user output tasks | available | tested | Explicit goal/game, catalog category, concrete asset, atomic local numbering, on-demand registered artifacts, live review-evidence validation, safe external roots, and disposable result trees. |
| Workspace distribution and Skill install/update | available | tested | One allowlisted cloneable product tree, four self-contained Skills under official `.agents/skills` roots, hash validation, safe initialization/update, and ignored personal-data preservation; live Codex discovery remains unverified. |
| Foundation CI and distribution workflow | available | tested | Linux/Windows product CI and separate master-only non-force publication; generated `dist/workspace` pushes are excluded from Foundation CI. |
| Local Blender executable configuration | environment-ready | tested | Ignored local config selects a real executable. Blender 5.2.4 LTS completed factory-startup background Python diagnostics and propagated an intentional Python error as exit 7; no asset was made. |
| Codex-directed Blender authoring | planned | none | The architecture permits native operations and bounded task-specific code without a prewritten generator, but no representative asset has been executed or accepted under this active boundary. |
| Blender MCP connection | planned | none | The Codex server entry and `uvx` launcher exist locally, but a live Blender connection was unavailable during the 2026-11-13 check. Registration is not connectivity. |
| Static Blender creation/revision | planned | none | No active adopted production helper or representative accepted asset. Historical candidates are isolated. |
| Humanoid base creation/revision | planned | none | Catalog/design only in the active product; no active adopted template path. |
| Nonhumanoid/creature generation | planned | none | Catalog only. |
| Rig, weights, Mixamo, and Action work | planned | none | Asset-specific policy exists; no archived implementation is an active capability. |
| Static or animated FBX | planned | none | Artifact registration contracts exist, but no active exporter or current engine round trip is claimed. |
| Static/action PNG and sprite sheet | planned | none | Logical formats and artifact paths exist; no active renderer/assembler or accepted end-to-end workflow is claimed. |
| Four target 3D styles | planned | none | Specifications exist; no style has an accepted generator or Codex-authored representative asset. |
| 8-direction pixel sprite | planned | none | Style registered; no accepted end-to-end workflow. |
| Blender Add-on | planned | none | The historical Add-on is isolated under `archive/legacy/`, not installed, packaged, or supported. Blender 5.2 had no GameAssetAI/MCP Add-on enabled in the inspected user configuration. |
| UnityWorkbench | planned | none | Optional explicit review environment; not created or configured. |
| External/local AI generation | planned | none | Replaceable provider entries only; no model, subscription, API, or generic integration framework is active. |

## Legacy boundary

The 70 historical Blender Runtime files, 14 Add-on files, and six retained contract-test files are
inventoried under `archive/legacy/` with the decision `미검증·보류` (unverified and held). They are
outside Python imports, formal test discovery, generated Skills, Workspace distributions, and CI.
The active product is automatically tested from a temporary checkout with the complete archive
absent. Future adoption is file-by-file through a bounded work package and current representative
evidence, not by restoring the directory wholesale.

The previous 45 narrow Skill folders were implementation surfaces rather than 45 product features.
The supported user surface remains exactly four task-oriented Skills. Temporary code written for a
single asset remains task-local unless it earns a durable active responsibility through review.
