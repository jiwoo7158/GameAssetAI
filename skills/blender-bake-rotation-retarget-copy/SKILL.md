---
name: blender-bake-rotation-retarget-copy
description: Bake a new unbound quaternion Action by sampling mapped pose-bone rotations from one explicitly named humanoid Armature onto an owned temporary copy of a different-rest target Armature. Use only for rotation-only local-basis transfer with an explicit frame range; do not use for root motion, location, scale, constraints, drivers, world-space pose matching, general Mixamo retargeting, or automatic binding.
---

# Bake a Rotation-only Retarget Copy

Create one independent, fake-user-protected, unbound Action. Evaluate only owned temporary
copies; preserve both original Armatures, the source Action, all bindings, context and files.

This transfers evaluated `matrix_basis` rotations in each mapped bone's local basis. It
does not normalize humanoid pose space or promise matching world-space limb orientation.

## Inputs and refusal

Require exact Scene, source/target Armature, source Action and unused result Action names;
explicit source and target humanoid mappings; exact source Action slot when present; and
integer start/end frames. The first bounded implementation requires `frame_step=1`.

Require these literal policies:

- `preserve_source=true`
- `bind_result=false`
- `set_fake_user=true`
- `rotation_only=true`

If any required input is absent, report it and stop without test-data creation. Refuse
unmapped animated bones, non-bone channels, location/scale channels, parents, non-identity
Armature Object transforms, Object/pose-bone constraints, Object drivers, differing
inherit-scale modes, multiple Action slots, target-name collisions, stale previews, ranges
over 10001 frames, or missing authorization.

## Execution

1. Inspect the Blender addon and Scene.
2. Read and execute these helpers in one shared globals/locals dictionary:
   - `scripts/inspect_humanoid.py`
   - `scripts/inspect_animation.py`
   - `scripts/inspect_action_loop.py`
   - `scripts/inspect_retarget_readiness.py`
   - `scripts/plan_action_copy.py`
   - `scripts/action_copy.py`
   - `scripts/aligned_retarget_action.py`
   - `scripts/bake_rotation_retarget.py`
3. Build the exact `gameassetai.rotation-retarget-bake-request.v1` request and call
   `preview_rotation_retarget_bake(request)`.
4. Report blockers, mapped animated roles, explicit frame count, result name and limits.
   Preview is never authorization.
5. Call `apply_rotation_retarget_bake(plan, authorization=True)` only after the user
   explicitly authorizes creation of that exact Action.
6. Verify an independent unbound result with fake user, quaternion curves on target bone
   paths, one linear key per integer frame, and unchanged source/target data and references.

## Result boundary

The only persistent successful change is one unbound Action. Temporary source/target Object
and Armature copies plus their Scene must be removed even on failure. Do not bind the result,
alter rest poses, rename bones, create constraints, transfer translation/scale/root motion,
export, save, or claim visual/deformation/Unity compatibility.

Different rests are permitted, but the copied local joint rotations may produce a different
world-space pose. Treat visual pose-space retargeting, hip translation scaling, root-motion
policy and production Mixamo validation as separate future workflows.

