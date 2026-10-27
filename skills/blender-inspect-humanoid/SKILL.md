---
name: blender-inspect-humanoid
description: Inspect an existing Blender armature against an explicit humanoid bone mapping, including required roles, ancestry, deform flags, roots, and animation sensitivity. Use before Mixamo preparation, retargeting, or Unity Humanoid work; do not use it to guess mappings, edit bones, rig, or retarget animation.
---

# Inspect Humanoid Armature

Analyze only. Do not rename, create, delete, reparent, transform, or change deform flags,
constraints, Actions, NLA tracks, meshes, vertex groups, or modifiers.

## Inputs

Require a named Armature Object and Scene. Accept the canonical role-to-bone mapping as
explicit data from the user or active Workspace Profile. Do not infer a complete mapping
from bone names. If no mapping exists, return the inventory and `incomplete` result so a
later mapping workflow can resolve it.

Supported roles are defined by `scripts/inspect_humanoid.py`. `chest` is optional in the
minimal mapping; the remaining canonical roles are required unless the caller supplies a
deliberately different `required_roles` list.

## Execution

1. Inspect the current Scene and addon status before executing code.
2. Read `scripts/inspect_humanoid.py` and execute it in one Blender MCP Python request.
   Use one shared dictionary for `exec` globals and locals, then call
   `inspect_humanoid(armature_name, mapping, scene_name, required_roles)` in that same
   request. Do not assume Python definitions survive a later MCP call.
3. Never switch out of Edit Mode to make inspection succeed. Report the refusal.
4. Treat `reviews` as preservation/compatibility findings, not permission to repair.

## Result boundaries

- `ok` means the supplied mapping exists and passes the bounded ancestry checks.
- `incomplete` means roles/bones are missing or mapped ancestry is inconsistent.
- A non-deform mapped bone, multiple roots, or existing animation is a review finding;
  it is not automatically invalid because export/engine policy belongs to the Profile.
- This result does not certify bone orientation, T/A pose, skin weights, twist-bone
  policy, Mixamo upload acceptance, retarget quality, Unity Avatar validity, or export.

Report the inspected Armature, explicit mapping source, missing roles/bones, failed
hierarchy checks and preservation-sensitive animation. State that Blender was not
modified.
