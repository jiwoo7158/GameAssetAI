---
name: gameassetai-create-asset
description: Plan and execute a catalog-aware new game-asset task from text, style presets, and user-provided references while reporting unsupported generation capabilities honestly.
---

# GameAssetAI Create Asset

Use this Skill for a new 3D asset. Route Workspace/Profile setup to `gameassetai-workspace`, an
existing source revision to `gameassetai-modify-asset`, and result-path allocation/publication to
`gameassetai-output-asset`.

Use the bundled CLI from the Skill's actual installation. From a project-scoped distribution root,
the shared entrypoint is `.agents/skills/gameassetai-workspace/scripts/gameassetai.py`; at user
scope resolve the copied `gameassetai-workspace/scripts/gameassetai.py`. Never assume that the
Workspace root contains the development-only `scripts/gameassetai.py`.

## Inputs and preparation

The normal input flow is a text description, a selected 3D style preset, and one or more reference
images supplied by the user, commonly generated with an external image AI. Record each reference's
role using the built-in concept/front/side/back/three-quarter/source ids or a bounded lowercase
portable custom id such as top/detail/material/silhouette. A role is not a path or prose.
References are not mandatory for every
bounded task: if none are supplied, decide whether the active Profile and request are sufficient;
otherwise explain which views or design decisions are needed. Never pretend an absent image exists
or automatically call an external image service.

Before production:

1. Validate the Workspace and read the active Profile through the bundled CLI.
2. Compare the request and references with durable game rules; treat per-asset overrides as local.
3. Build and validate an Asset Specification containing asset type, description, references,
   independent 3D/2D styles, provider choice, Rig/animation intent, and requested outputs.
4. Inspect the current Blender/MCP environment and preserve unrelated Scene data.
5. Choose a bounded authoring route: Blender native operations and task-specific code directed by
   Codex, or a provider whose current implementation/evidence covers the request. A prewritten
   generator is not required merely because the asset noun is new. If considering a registered
   external tool, query the Workspace Skill's common Tools registry and last-check status, then
   verify the current real environment. Registration or cached status alone is not availability
   or capability evidence. If the user selected an unavailable tool, explain why and request a
   decision before using an alternative.
6. Before writing a result, route path allocation through the output Skill. For a user task, use
   the active Profile game id, catalog top-level category, concrete new asset id, and descriptive
   task purpose. For a development experiment, inspect `experiment.json` metadata and explicitly
   select an experiment with the same validation goal or create a descriptive new experiment.

Do not create a new experiment merely because the request is new, and do not reuse one merely
because the asset name matches. Different validation goals remain separate; revisions and method
comparisons under the same goal reuse the experiment. If the request does not establish that
choice, ask the minimum clarification instead of using a default. A revision of the same concrete
asset keeps its asset id and receives a new numbered task when a distinct result must be preserved.

Catalog registration does not mean generation is implemented. Unverified historical Blender
helpers and Add-on code are isolated outside the bundled Runtime and must not be imported or
treated as capabilities. Codex may write bounded code for the exact task in its temporary/output
context, but must not accumulate numbered variants in product source or advertise one success as a
general generator. Never force humanoid anatomy, topology, Rig, or animation policy onto a
nonhumanoid.

Define visible and semantic invariants, perform structural checks, and inspect relevant Blender
views. Stop on rejection before Rig, animation, 2D conversion, or export. Concept/reference images
used before modeling, Blender previews of the 3D source, and final PNG/pixel/sprite outputs are
three different stages.

Use the output Skill to obtain every deliverable path, publish without overwrite, register the
actual nonempty file, and record `complete`, `accepted`, or `rejected` explicitly. A successful
generator call or structural test is not acceptance evidence.

For new 3D work, reserve and preserve an editable `.blend` model as the first primary artifact
unless the user explicitly requests a different bounded source contract. Treat FBX, preview PNG,
pixel frames, and sprite sheets as explicit downstream tasks after source review. Report the exact
registered `.blend` path; open it in Blender GUI only when the user chooses that review method,
with automatic script execution disabled and without saving or revising the file implicitly.

If neither native/task-specific work nor a verified provider can safely meet the request, return
the validated specification, missing capability, and needed user input instead of presenting
primitive-only geometry as a finished asset. Do not mutate an existing source under this Skill.
Result folders and manifests are local descriptions, not Runtime dependencies; never make later
independent creation require an earlier output tree.
