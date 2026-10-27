---
name: blender-inspect-evaluated-pose-loop
description: Compare evaluated endpoint poses and finite-difference seam velocities for an explicit complete set of pose bones and one Blender Action on an isolated Armature copy. Use when stored key equality is insufficient for loop review; do not infer bones, edit animation, evaluate constraints/NLA, or certify deformation, visual, or engine loop behavior.
---

# Inspect Evaluated Pose Loop

Compare explicit endpoint poses while preserving the user's Armature, Action, Scene,
selection and mode. This is read-only analysis, not animation editing.

## Inputs

Require exact Scene, Armature Object and Action names, a nonempty unique list containing
every animated pose bone in the selected slot, an exact slot identifier when the Action
has multiple slots, distinct integer start/end frames, a positive noncrossing velocity
sample interval, and finite nonnegative endpoint and per-frame velocity tolerances. Never
guess bones or a frame range.

If any input is absent, report that fact and stop. Do not create a demonstration rig or
Action in the user's Scene.

## Execution

1. Inspect Blender addon and Scene state first.
2. Refuse parented Armature Objects, constraints, drivers, Object/custom-property curves,
   unlisted animated bones, unsupported pose properties, or ranges over 10000 frames.
3. Read and execute these helpers in one shared globals/locals dictionary:
   - `scripts/inspect_animation.py`
   - `scripts/inspect_action_loop.py`
   - `scripts/inspect_root_motion.py`
   - `scripts/action_copy.py`
   - `scripts/inspect_evaluated_root_motion.py`
   - `scripts/inspect_evaluated_pose_loop.py`
4. Build the exact `gameassetai.evaluated-pose-loop-request.v2` request and call
   `inspect_evaluated_pose_loop(request)`.
5. Confirm the report is `ok`, temporary IDs were removed, and source state, Action
   content and current/NLA references remain unchanged.

The helper creates only an owned temporary Scene and independent Armature Object/data
copy, binds the existing Action to that copy, evaluates the endpoint and inner sample
frames, then removes all temporary IDs. It never saves the file or retains an Action.

## Interpretation

For each requested bone, report local-basis translation distance, shortest quaternion
angle and maximum scale-component delta plus their tolerance results. Also report start
forward and end backward finite-difference translation, rotation-vector and scale velocity,
their seam deltas, and `all_tangents_match`.

Finite differences provide bounded seam-velocity evidence but do not certify subframe
extrema, motion between samples, root-motion policy, skin deformation, visual continuity,
export, or Unity behavior. Constraints, drivers and NLA blending are excluded. State that
no persistent Blender data was modified.
