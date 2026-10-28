---
name: blender-prepare-game-action
description: Prepare one explicit Blender Armature Action as a new non-destructive game clip by evaluated-pose sampling, range/FPS rebasing, quaternion continuity, bounded exact-key cleanup, and loop/root-motion reporting. Use for imported or existing Actions whose Bezier curves or missing boundary keys exceed strict range extraction; do not use for retargeting, automatic loop repair, root-motion conversion, NLA editing, or engine export.
metadata:
  contract: gameassetai.skill-contract.v1
  requirements: REQ-ANIM, REQ-SAFE, REQ-WORKFLOW
  evidence: representative
  external-dependencies: none
---

# Blender Prepare Game Action

## Requirements and responsibility

This is the user-facing Action cleanup workflow. It creates one independent, protected and
unbound game clip from an explicit Action on an explicit Armature. It supports imported Bezier
Actions and ranges without exact boundary keys by evaluating the pose at explicit sample times.
Use `blender-extract-action-range` instead when its exact-key/LINEAR contract already applies.

The output is a sampled pose clip, not an Action copy: animated pose-bone transforms are baked to
quaternion rotation plus location and scale. Source Action, slot, current/NLA references,
Armature rest data, Mesh/UV data, Scene context and existing files remain unchanged.

## Implementation basis and dependencies

Use Blender's native Action, dependency-graph and pose APIs plus
`scripts/prepare_game_action.py`. Load `blender-inspect-animation/scripts/inspect_animation.py`,
then `blender-copy-action/scripts/action_copy.py`, then this Skill's script in the same
globals/locals dictionary to reuse their slot-aware curve, Action snapshot, reference and
fingerprint helpers. No external package is required.

## Workflow

1. Inspect the Scene with `blender-inspect-animation`; require exact Scene, Armature, source
   Action/slot, unused target name, source range, source/target FPS, output start 0 or 1 and an
   explicit root bone.
2. Prefer strict `blender-extract-action-range` when it accepts the request. Otherwise build
   `gameassetai.game-action-preparation-request.v1` and call
   `preview_game_action_preparation(request)`.
3. Report sampled frames, animated bones, unsupported channels, existing references, root delta,
   and that loop/root-motion results are inspection only.
4. After authorization for that exact fresh plan, call
   `apply_game_action_preparation(plan, authorization=True)`.
5. Validate the receipt, temporarily bind the result only on a duplicate for visible review, and
   use `blender-bind-action-empty` or `blender-replace-current-action` separately if the user later
   authorizes a persistent binding change.

## Preservation

The implementation evaluates the source on temporary Armature Object copies in a temporary Scene.
It never edits source curves, slots or references and never binds the result to the real rig.
Name collisions, stale plans, unsupported channels, constraints/drivers, linked Armature data and
invalid numeric data are refused. Failure removes only the new Action and temporary data.

## Validation and completion

Completion requires an independent fake-user Action, requested range/FPS/output start, normalized
sign-continuous quaternions, finite transforms, zero empty curves, source/reference/rest
preservation, sampled-pose error within the request tolerances and saved-file reopen. Loop endpoint,
boundary velocity and root translation metrics are metadata; they do not certify a seamless loop.

`EXACT_REDUNDANT` cleanup removes only an interior LINEAR scalar key that lies on the exact
neighbor interpolation within machine-scale epsilon, followed by evaluated-pose verification.
Use `NONE` when every sampled key must remain. No approximate key reduction is claimed.

## Boundary

Supported input is one local Object-slot Action containing pose-bone transform channels for the
selected Armature, with no object/custom-property channels, Armature/pose constraints or drivers.
The workflow does not retarget, infer cycles, force endpoints equal, convert root motion, edit NLA,
handle IK/constraint baking, optimize with perceptual tolerances or export to Unity. Source ranges
must map to an integral number of target-frame intervals.
