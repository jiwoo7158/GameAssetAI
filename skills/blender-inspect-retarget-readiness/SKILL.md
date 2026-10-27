---
name: blender-inspect-retarget-readiness
description: Read-only comparison of two explicitly mapped Blender humanoid Armatures and one source Action before retargeting. Use to inventory mapped animation coverage, rest-bone length/direction differences, Action ownership, transforms, and preservation risks; do not retarget, pose, rename bones, bake, or edit data.
---

# Inspect Retarget Readiness

Compare a named source Armature, target Armature, and source Action without changing
Blender data or evaluating a retarget result.

## Inputs

Require exact Scene, source Armature, target Armature, and source Action names. Require
separate explicit humanoid role-to-bone mappings for both rigs; never infer mappings from
bone names. Use the active Workspace Profile only when it supplies these exact mappings.

Require an exact source Action slot identifier when the Action has multiple slots. A sole
slot may be used without asking the user to restate it. If any required input is absent,
report what is missing and stop without creating test data.

## Execution

1. Inspect Blender addon and Scene state first.
2. Read and execute, in one shared globals/locals dictionary:
   - `scripts/inspect_humanoid.py`
   - `scripts/inspect_animation.py`
   - `scripts/inspect_action_loop.py`
   - `scripts/inspect_retarget_readiness.py`
3. Call `inspect_retarget_readiness(scene_name, source_armature_name,
   target_armature_name, source_mapping, target_mapping, source_action_name,
   required_roles, source_slot_identifier)`.
4. Confirm the Scene, current frame, mode, selection, objects, Armatures, Actions and
   bindings remain unchanged.

## Interpretation

Report mapping completeness for both rigs, mapped roles that have source transform
channels, animated bones outside the mapping, non-bone channels, whether the source
Armature references the Action, target animation sensitivity, Object transforms, and
per-role rest-bone length ratio/direction dot product.

`retarget_candidate=true` means only that both explicit mappings are structurally
complete, the source references the Action, at least one mapped role is animated, and no
mapped rest bone has near-zero length. It is not authorization to write and does not
certify pose alignment, bone roll/axes, constraints, skin weights, deformation, root
motion policy, scale correctness, visual quality, Mixamo compatibility, or Unity import.

Do not create constraints, change rest poses, rename bones, assign Actions, bake keys,
or perform retargeting. State that Blender was not modified.

