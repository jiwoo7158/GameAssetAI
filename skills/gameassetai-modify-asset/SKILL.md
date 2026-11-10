---
name: gameassetai-modify-asset
description: Inspect and revise an explicitly selected existing game asset with copy-first preservation, including bounded mesh, rig, Mixamo, and Action workflows.
---

# GameAssetAI Modify Asset

Use this Skill for natural-language revisions such as proportion, silhouette, part, color,
material, Rig, or animation changes. First resolve the exact source and inspect the current Blender
Scene. Create a copy or verified checkpoint before a material change, and validate preservation
afterward.

The bundled runtime retains tested narrow helpers for static semantic replacement, transform and
mesh cleanup, humanoid inspection, Mixamo-oriented import/retarget preparation, Action copying and
editing, and a bounded template-character revision. These helpers are internal building blocks.
They do not implement arbitrary semantic mesh editing, clothing/hair fitting, facial work, or
non-humanoid Rig generation.

Reject a request or narrow its scope when the selected asset is outside an implemented contract.
Never delete existing Armatures, Actions, meshes, materials, or external source files merely to
simplify the operation.
