---
name: blender-extract-action-range
description: Extract one explicit exact-key linear frame interval from an existing Blender Action into a new protected unbound Action, optionally rebased to frame 0 or 1, while preserving the source and all references. Use for strict non-destructive take splitting when every F-Curve already has exact boundary keys; do not use for boundary sampling, Bezier editing, binding, retargeting, export, or Unity configuration.
---

# Extract Action Range

Create one independent Action containing only an explicit existing frame interval. Preserve
the source Action, its current/NLA references, context and files. Either keep original
frame numbers or shift the copy to frame 0 or 1; retain only in-range pose markers.

## Inputs and refusal

Require exact Scene, source Action, source slot, unused target Action and integer start/end
frames. Require `frame_policy` to be `KEEP_FRAMES`, `REBASE_TO_ZERO`, or
`REBASE_TO_ONE`, plus `preserve_source=true`, `bind_result=false`, and
`set_fake_user=true`.

The source must have exactly one Object slot and at least one F-Curve. Every curve must
have unique key times, exact keys at both requested boundaries, and only LINEAR keyframes.
Refuse sampled points, modifiers, missing boundaries, ranges over 10001 frames, collisions,
stale previews and missing authorization. Do not synthesize boundary values or infer a take.

## Execution

1. Inspect Blender addon and Scene state.
2. Execute these helpers in one shared globals/locals dictionary:
   - `scripts/inspect_animation.py`
   - `scripts/action_copy.py`
   - `scripts/extract_action_range.py`
3. Build `gameassetai.action-range-extraction-request.v1` and call
   `preview_action_range_extraction(request)`.
4. Report source fingerprint/references, curve and retained key/marker counts, source and
   output ranges, exact time offset, output name and blockers. Preview is never authorization.
5. Call `apply_action_range_extraction(plan, authorization=True)` only after explicit
   authorization for that exact plan.
6. Verify unchanged source content/references, exact retained key range and markers, and an
   independent fake-user-protected unbound result.

The only persistent successful change is the new unbound Action. Never bind it, rename or
delete the source, edit Bezier/tangent behavior, create missing keys, alter
the Rig, export, save, or claim loop, deformation or Unity compatibility.
