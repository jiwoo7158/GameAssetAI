---
name: blender-inspect-mixamo-preflight
description: Read-only preparation review for an existing Mixamo-style Blender armature and bound meshes. Use before Mixamo animation import, retargeting, or Unity Humanoid preparation; do not use it to upload, rig, rename bones, change weights, retarget, or export.
---

# Inspect Mixamo Preflight

Analyze existing data only. Do not change Armatures, bones, meshes, vertex groups,
modifiers, transforms, Actions, NLA tracks, selection, mode, or files.

## Scope

Use the exact Mixamo suffix signature in the packaged helper. A complete unique signature
may produce an explicit humanoid mapping; a missing or ambiguous signature remains
`incomplete`. Do not extend this into fuzzy name matching. An optional exact prefix may
come from the user or active Workspace Profile.

## Execution

1. Inspect Blender addon/Scene state and identify a named Armature Object.
2. Read both packaged helpers. Execute them in order in one Blender MCP Python request,
   using the same dictionary for globals and locals:
   `inspect_humanoid.py`, then `inspect_mixamo_preflight.py`.
3. Call `inspect_mixamo_preflight(armature_name, scene_name, expected_prefix)` in that
   same request. Do not assume definitions survive another MCP call.
4. Never leave Edit Mode or modify a rig to make inspection pass.

## Interpretation

- `ok` means one complete exact naming signature and the bounded humanoid ancestry check
  passed. It is not Mixamo or Unity certification.
- Report bound Meshes, missing mapped vertex groups, non-identity Armature transform,
  existing animation, optional known bones and all review findings.
- Preserve uncertainty: this does not validate T/A pose, bone axes, weights, twist-bone
  policy, facial bones, Mixamo upload acceptance, retarget quality, root motion, Unity
  Avatar generation, or FBX export.

State explicitly that the inspection made no Blender changes.
