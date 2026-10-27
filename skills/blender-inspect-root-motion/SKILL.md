---
name: blender-inspect-root-motion
description: Read-only inspection of stored translation F-Curves for one explicitly named Blender Object or Armature bone over an explicit Action range. Use to identify root-motion evidence before cleanup, retargeting, or Unity preparation; do not guess the root, interpret game policy, evaluate poses, remove motion, bake, or edit animation.
---

# Inspect Explicit Root Motion

Analyze stored translation channels only. Do not change frames, selection, mode, Actions,
keys, NLA, objects, bones, constraints, drivers, or files.

## Inputs

Require exact Scene, Object and Action names, explicit start/end frames, and a finite
nonnegative value tolerance from the user or active Workspace Profile. Inspect either:

- Object-level `location` when no bone name is supplied, or
- one exact bone's `pose.bones[...].location` when an explicit bone name is supplied.

Never infer the root from names. Validate that an explicit bone exists on the named
Armature. Require an exact slot identifier for a multi-slot Action; a sole slot may be
used without asking the user to restate it.

If there is no Action/root target or required range/tolerance, report what is missing and
stop without creating test data.

## Execution

1. Inspect Blender addon and Scene state first.
2. Read and execute `scripts/inspect_animation.py`, `scripts/inspect_action_loop.py`, then
   `scripts/inspect_root_motion.py` in one shared globals/locals dictionary.
3. Call `inspect_root_motion(scene_name, object_name, action_name, start_frame,
   end_frame, value_tolerance, bone_name, slot_identifier)` in that same request.
4. Verify the current frame and animation inventory remain unchanged.

## Interpretation

Report each matching XYZ location channel's endpoint values, net delta, stored key-value
range, keyed span and whether those values exceed the supplied tolerance. Report the net
translation vector, missing axes, unmatched rotation channels and explicit target kind.

`translation_evidence=true` means stored endpoint or key-value movement exceeded the
tolerance. It does not decide whether the motion should stay on the root, be transferred
to an Object, removed for an in-place clip, or configured as Unity root motion. Those are
game/Profile policy decisions.

This check does not include interpolation extrema, evaluated poses, constraints, drivers,
NLA blending, rotation interpretation, world-space displacement, retarget quality or
engine behavior. State that Blender was not modified.
