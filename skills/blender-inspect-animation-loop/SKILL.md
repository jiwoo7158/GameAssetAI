---
name: blender-inspect-animation-loop
description: Read-only comparison of stored Blender Action F-Curve values at explicit loop start and end frames. Use to find endpoint component mismatches or missing boundary keys before animation cleanup; do not use it to certify visual loop quality, evaluate poses, edit curves, bake, or retarget.
---

# Inspect Animation Loop Endpoints

Compare stored F-Curve components only. Do not change the current frame, selection, mode,
Action, keys, modifiers, NLA, object data, or files.

## Inputs

Require exact Scene and Action names, explicit `start_frame` and `end_frame`, and an
explicit finite nonnegative `value_tolerance` from the user or active Workspace Profile.
Do not invent a game-specific tolerance. `frame_tolerance` only determines whether a key
is considered present at a boundary; it is not an animation-value tolerance.

If the current file has no Action or the request does not identify the Action/range/value
tolerance, report what is missing and stop without creating test data.

## Execution

1. Inspect Blender addon and Scene state first.
2. Read `scripts/inspect_animation.py` and `scripts/inspect_action_loop.py`. Execute both
   in order in one Blender MCP request with one shared globals/locals dictionary.
3. Call `inspect_action_loop(scene_name, action_name, start_frame, end_frame,
   value_tolerance, frame_tolerance)` in that same request. Do not assume definitions
   survive a later MCP call.
4. Verify that the current frame and inspected Action inventory did not change.

## Interpretation

- `component_match` means only that one stored F-Curve's evaluated scalar values differ
  by no more than the supplied tolerance at the two explicit frames.
- `endpoint_candidate` additionally requires every discovered channel to have keys at
  both boundaries. It is still not a loop-quality certificate.
- Report mismatched channels, absolute deltas, missing boundary keys and Cycles modifiers.
- Rotation components are not normalized: wrapped Euler values and sign-equivalent
  quaternions may be reported as different.
- Constraints, drivers, NLA blending, tangent/velocity continuity, evaluated poses,
  root-motion policy and visual motion are outside this check.

State that Blender was not modified and keep any cleanup or curve editing as a separate,
explicitly authorized workflow.
