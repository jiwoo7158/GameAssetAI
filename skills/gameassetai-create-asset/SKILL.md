---
name: gameassetai-create-asset
description: Plan and execute a catalog-aware new game-asset task from text, style presets, and user-provided references while reporting unsupported generation capabilities honestly.
---

# GameAssetAI Create Asset

Use this Skill for a new 3D asset. Route Workspace/Profile setup to `gameassetai-workspace`, an
existing source revision to `gameassetai-modify-asset`, and accepted deliverable publication to
`gameassetai-output-asset`.

## Inputs and preparation

The normal input flow is a text description, a selected 3D style preset, and one or more reference
images supplied by the user, commonly generated with an external image AI. Record each reference's
role such as concept, front, side, back, or three-quarter. References are not mandatory for every
bounded task: if none are supplied, decide whether the active Profile and request are sufficient;
otherwise explain which views or design decisions are needed. Never pretend an absent image exists
or automatically call an external image service.

Before production:

1. Validate the Workspace and read the active Profile through the bundled CLI.
2. Compare the request and references with durable game rules; treat per-asset overrides as local.
3. Build and validate an Asset Specification containing asset type, description, references,
   independent 3D/2D styles, provider choice, Rig/animation intent, and requested outputs.
4. Inspect the current Blender/MCP environment and preserve unrelated Scene data.
5. Select only a provider whose implementation state covers the requested work.

Catalog registration does not mean generation is implemented. The bundled Runtime contains
bounded static assembly and template-humanoid helpers, not general prompt-to-mesh generation, all
creatures, or accepted generators for the four target 3D styles. Never force humanoid anatomy,
topology, Rig, or animation policy onto a nonhumanoid.

Define visible and semantic invariants, perform structural checks, and inspect relevant Blender
views. Stop on rejection before Rig, animation, 2D conversion, or export. Concept/reference images
used before modeling, Blender previews of the 3D source, and final PNG/pixel/sprite outputs are
three different stages.

If no implemented provider fits, return the validated specification, missing capability, and
needed user input instead of presenting primitive-only geometry as a finished asset. Do not mutate
an existing source under this Skill.
