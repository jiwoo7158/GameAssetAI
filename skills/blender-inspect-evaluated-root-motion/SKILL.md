---
name: blender-inspect-evaluated-root-motion
description: Evaluate one explicitly named root bone and Action on an isolated Blender Armature copy, reporting integer-frame translation paths in local-basis, armature, and world space. Use when stored root-motion keys are insufficient; do not infer the root, edit animation, transfer motion, apply Unity policy, evaluate constraints/NLA, or create persistent test data.
---

# Inspect Evaluated Root Motion

Measure an explicit root bone's evaluated translation path while preserving the user's
Armature, Action, Scene, selection and mode. This is analysis, not a retarget or edit.

## Inputs

Require exact Scene, Armature Object, Action and root-bone names, an explicit integer
start/end range, `frame_step=1`, a finite nonnegative tolerance, and the exact Action slot
identifier when the Action has multiple slots. Never infer a root from bone names.

If the required Armature, Action or root bone is absent, report that fact and stop. Do not
create a demonstration rig or Action in the user's Scene.

## Execution

1. Inspect Blender addon and Scene state first.
2. Refuse parented Armature Objects, parented root bones, Object/pose-bone constraints,
   Object/Armature-data drivers, Object-transform channels, ranges over 10001 frames, or
   an Action without a matching root-bone location F-Curve.
3. Read and execute these helpers in one shared globals/locals dictionary:
   - `scripts/inspect_animation.py`
   - `scripts/inspect_action_loop.py`
   - `scripts/inspect_root_motion.py`
   - `scripts/action_copy.py`
   - `scripts/inspect_evaluated_root_motion.py`
4. Build the exact `gameassetai.evaluated-root-motion-request.v1` request and call
   `inspect_evaluated_root_motion(request)`.
5. Confirm the report is `ok`, temporary IDs were removed, and the original Scene,
   Armature and Action content/references remain unchanged.

The helper creates only an owned temporary Scene and independent Armature copy, binds the
existing Action to that copy, samples every integer frame, then removes the temporary IDs.
It never saves the Blender file or retains an output Action.

## Interpretation

Report start/end positions, net vector and distance, sampled path length, maximum distance
from the start and bounds for `LOCAL_BASIS`, `ARMATURE` and `WORLD` spaces. Distinguish:

- `net_translation_evidence`: start and end differ beyond tolerance.
- `path_translation_evidence`: sampled motion occurred even if the clip returns to start.

World metrics include the Armature Object's static transform. They do not decide whether
motion belongs on a bone or Object, whether a clip should be in-place, how target
proportions should scale it, or how Unity should import/apply root motion.

Integer-frame evaluation includes stored interpolation and bone hierarchy. It excludes
constraints, drivers, NLA blending, subframe extrema, retargeting, deformation quality,
motion transfer, export and engine behavior. State that no persistent Blender data was
modified.
