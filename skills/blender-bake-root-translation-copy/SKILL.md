---
name: blender-bake-root-translation-copy
description: Bake one independent unbound Action containing only an explicitly mapped parentless root bone's location, using a required TRANSFER or IN_PLACE policy, explicit Armature-space XYZ mask, and explicit scale. Use for guarded root-translation preparation; do not infer roots or proportions, copy rotation, merge Actions, bind results, export, or configure Unity root motion.
---

# Bake a Root Translation Copy

Create one location-only, fake-user-protected, unbound Action on owned temporary rig
copies. Preserve both original Armatures, the source Action, bindings, context and files.

## Required policy

Require exact Scene, source/target Armature, source Action, unused target Action,
parentless source/target root-bone names, source Action slot, integer frame range and:

- `motion_policy`: exactly `TRANSFER` or `IN_PLACE`
- `translation_scale`: explicit finite value greater than 0 and at most 1000
- `axis_mask`: exactly three booleans for source Armature-space XYZ
- `preserve_source=true`, `bind_result=false`, `set_fake_user=true`

`TRANSFER` requires at least one enabled axis. `IN_PLACE` requires all axes disabled and
`translation_scale=1`. Never infer a root, target proportion, axis, scale or policy from
names or geometry. The first bounded version requires `frame_step=1`.

If inputs are missing, report them and stop without test-data creation. Refuse parented
roots or Armature Objects, nonidentity Armature transforms, constraints, drivers, Object
transform Action channels, missing root location curves, ambiguous slots, collisions,
stale previews, ranges over 10001 frames or missing authorization.

## Execution

1. Inspect the Blender addon and Scene.
2. Read and execute these helpers in one shared globals/locals dictionary:
   - `scripts/inspect_animation.py`
   - `scripts/inspect_action_loop.py`
   - `scripts/inspect_root_motion.py`
   - `scripts/action_copy.py`
   - `scripts/inspect_evaluated_root_motion.py`
   - `scripts/bake_root_translation.py`
3. Build the exact `gameassetai.root-translation-bake-request.v1` request and call
   `preview_root_translation_bake(request)`.
4. Report the policy, scale, Armature-space XYZ mask, frame count, output name and all
   blockers. Preview is never authorization.
5. Call `apply_root_translation_bake(plan, authorization=True)` only after explicit
   authorization for that exact candidate.
6. Verify exactly three linear location curves, one key per integer frame, an independent
   fake-user Action with no binding, and unchanged source/target data and references.

## Transfer semantics

For `TRANSFER`, each evaluated source `matrix_basis.translation` is transformed through
the source root rest orientation into source Armature space. Disabled XYZ components are
zeroed, the explicit scalar is applied, then the displacement is converted through the
inverse target root rest orientation into target local location.

This transfers absolute sampled root location, not displacement relative to the first
frame. `IN_PLACE` writes zero target root location on every sampled frame.

The persistent output contains root location only. Do not copy rotations or scale, merge
with a rotation Action, bind it, alter rest poses, export, save or claim Mixamo,
deformation or Unity compatibility. Action composition and Unity root-motion import policy
remain separate workflows.
