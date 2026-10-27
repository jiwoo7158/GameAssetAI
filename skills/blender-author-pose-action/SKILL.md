---
name: blender-author-pose-action
description: Create and bind one explicit Blender pose Action from complete per-frame XYZ Euler rotations and optional explicit local bone locations, with an explicit character front axis and Blender 5 layered-Action verification. Use for reviewed key-pose animation on an empty Armature. Do not infer motion, replace Actions, animate scale, retarget, or certify final animation quality.
---

# Blender Author Pose Action

Create one reviewed key-pose Action on an explicit empty Armature. The request must define the
same complete animated-bone set at every supplied frame and must match the rig's recorded front
axis. This prevents local Euler signs from silently turning the upper body backward.

Validate with `scripts/validate_pose_action_request.py`, show the complete frame/bone plan, and
require explicit authorization before running `scripts/author_pose_action.py`.

The v1 workflow creates rotation-Euler XYZ channels only. The v2 workflow additionally accepts
complete per-frame local-space location triples for an explicit bone set, intended for reviewed
root or pelvis height/translation corrections. Both use Bezier AUTO_CLAMPED handles,
requires empty current Action/NLA/drivers, refuses occupied Action names, binds the created Action,
and reports Blender 5 layered F-Curve/key counts. It does not replace or delete existing
animation or infer root motion/gameplay timing.

After creation, inspect endpoint and important intermediate frames from front and side views.
For characters whose front is `-Y`, evaluated forward hand/foot motion must remain in the `-Y`
hemisphere unless the reviewed pose explicitly requires otherwise.
