---
name: blender-retarget-aligned-action-copy
description: Create an unbound copied Blender Action by remapping pose-bone F-Curve paths between two explicitly mapped humanoid Armatures whose rest matrices, Object transforms, rotation modes, and supported animation channels are already aligned. Use only for strict name-only retarget copies; do not use for differing rest poses, bone axes, proportions, constraints, general Mixamo retargeting, pose conversion, or baking.
---

# Retarget an Aligned Action Copy

This is a narrow name-only Action remap, not general retargeting. Preserve both Armatures,
the source Action, all current/NLA bindings, frames, selection, mode, and files.

## Inputs and refusal

Require exact Scene, source Armature, target Armature, source Action and unused result
Action names. Require explicit source and target humanoid role-to-bone mappings, the exact
source slot identifier when present, and a finite nonnegative rest tolerance. Never guess
bone roles or engine policy from names.

The request must explicitly require:

- `preserve_source=true`
- `bind_result=false`
- `set_fake_user=true`

If the required objects, Action, mappings or names are absent, report that and stop without
creating test data. Refuse unless every animated pose bone is mapped and every curve is a
supported pose-bone transform. Refuse differing mapped rest matrices, Object transforms,
animated rotation modes, parents, Object/pose-bone constraints, Object drivers, multiple
Action slots, name collisions, stale previews, or unsupported channels.

## Execution

1. Inspect Blender addon and Scene state.
2. Read and execute these helpers in one shared globals/locals dictionary:
   - `scripts/inspect_humanoid.py`
   - `scripts/inspect_animation.py`
   - `scripts/inspect_action_loop.py`
   - `scripts/inspect_retarget_readiness.py`
   - `scripts/plan_action_copy.py`
   - `scripts/action_copy.py`
   - `scripts/aligned_retarget_action.py`
3. Construct the exact `gameassetai.aligned-retarget-request.v1` request and call
   `preview_aligned_retarget(request)`.
4. Show the candidate, blockers, mapped animated roles, alignment deltas, result name, and
   preservation limits. Preview is not authorization.
5. Call `apply_aligned_retarget(plan, authorization=True)` only after the user explicitly
   authorizes that exact result Action creation.
6. Verify the new Action is independent, fake-user protected and unbound; its paths and
   slot display name target the explicit target mapping. Recheck that source references,
   target Armature state and context are unchanged.

## Result boundary

The only persistent change is one new, unused Action datablock. The helper copies stored
key values/settings and changes mapped bone data paths; it does not evaluate poses,
convert coordinate spaces, create constraints, bind the Action, bake keys, modify rigs,
transfer root motion, test deformation, export, or save the file.

Success on aligned synthetic rigs does not establish compatibility with ordinary Mixamo
or production rigs. If rest pose, axes, proportions or constraints differ, stop and use a
future pose-space/bake workflow rather than weakening these guards.

