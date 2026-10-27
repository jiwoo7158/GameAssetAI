---
name: blender-compose-retarget-actions
description: Compose one validated quaternion-rotation-only Action and one validated root-location-only Action into a new independent unbound Blender Action. Use after the narrow GameAssetAI rotation and root-translation bake workflows; do not merge arbitrary Actions, bind results, alter rigs, infer policies, export, or configure Unity.
---

# Compose Retarget Actions

Create one fake-user-protected, unbound Action by copying a strict rotation bake and adding
the strict root-translation bake. Preserve both inputs, their references, the target Rig,
context and files.

## Inputs and refusal

Require exact Scene, target Armature, rotation Action, translation Action, unused output
Action and target-root names plus an explicit integer frame range with `frame_step=1`.
Require `preserve_sources=true`, `bind_result=false`, and `set_fake_user=true`.

Both inputs must be unbound, fake-user protected, single Object-slot Actions. Rotation may
contain only target-bone quaternion curves with four linear keys channels; translation
must contain exactly target-root XYZ location curves. Every curve must have one linear key
per requested integer frame, no samples or modifiers, and reference an existing target
bone. Refuse missing data, collisions, constraints, malformed channels, stale previews,
name collisions, ranges over 10001 frames or missing authorization.

## Execution

1. Inspect Blender addon and Scene state.
2. Execute these helpers in one shared globals/locals dictionary:
   - `scripts/inspect_animation.py`
   - `scripts/action_copy.py`
   - `scripts/inspect_evaluated_root_motion.py`
   - `scripts/compose_retarget_actions.py`
3. Build `gameassetai.compose-retarget-actions-request.v1` and call
   `preview_retarget_action_composition(request)`.
4. Report input fingerprints, curve counts, range, output name and blockers. Preview is
   never authorization.
5. Call `apply_retarget_action_composition(plan, authorization=True)` only after explicit
   authorization for that exact plan.
6. Verify unchanged rotation/translation inputs and target Rig, an independent output with
   the original quaternion curves plus exactly three root-location curves, and no binding.

The only persistent successful change is the new unbound Action. Temporary Scene/Object/
Armature data must be removed even on failure. Do not bind the output, add NLA strips,
modify the Rig, merge arbitrary overlapping curves, export, save, or claim Mixamo,
deformation or Unity compatibility. Result binding is a separate guarded workflow.
