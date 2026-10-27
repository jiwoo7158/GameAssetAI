---
name: blender-render-2d-batch
description: Render an explicit ordered batch of reviewed static Blender Mesh views and Action PNG sequences with collision checks and all-or-nothing rollback. Use for multiple directions or Actions only when every child request, output name, frame range, and setting source is explicit. Does not infer direction sets, Actions, layouts, or game style.
---

# Render 2D Batch

Coordinate existing static-PNG and Action-sequence render contracts without changing their
inspection or rendering rules. Keep the interactive Blender Scene unsaved and unchanged.

## Required boundary

- Use `gameassetai.2d-render-batch-request.v1` with 1-64 ordered child items and at most
  2,048 total PNG outputs.
- Each item is `STATIC` or `ACTION_SEQUENCE`, has a safe unique id, and embeds one complete
  request already accepted by the corresponding single-render contract.
- Every direction, Action, slot, frame range, filename and output is explicit. Never generate
  a compass set, guess an Action, or infer naming from object data.
- All outputs share one existing directory and must be absent together with sibling `.meta`
  files. Execution is `LIST_ORDER`, publication is `ALL_OR_NOTHING`, and failure policy is
  `ROLL_BACK_BATCH_OUTPUTS`.
- Each item chooses `EXPLICIT` settings with a four-null binding, or
  `ACTIVE_PROFILE_PRESET` with the complete name/reference/Profile/preset hash binding.
  Do not partially merge those modes.

## Workflow

1. Inspect Blender MCP status and the exact Scene/assets. Load the static, Action, Profile and
   batch helpers from this Skill's `scripts` directory. Keep static and Action helper execution
   namespaces separate where their constants overlap.
2. Build every complete child request. For a Profile-backed item, freshly read the active
   Profile context, resolve `STATIC_RENDER` or `ACTION_SEQUENCE`, and retain the four-hash
   binding. Build the exact batch request and call `validate_2d_render_batch_request`.
3. Show item order, directions, Actions, output count/paths, settings sources and fixed rollback
   policy. Stop without writing when the batch or any child is invalid.
4. After the user has requested those exact outputs, run each child's existing inspection and
   framing preview. Create a fresh, unique child stage and child job only after that child is
   reviewable. If preparation fails, remove only stages/jobs created by this attempt and render
   nothing.
5. Immediately before the batch job, reread and resolve every Profile-backed item using its
   retained `expected_binding`; refuse absence or any hash change. Revalidate the whole batch.
   Build one new sibling `.gameassetai-2d-batch-<token>.job.json` with
   `build_2d_render_batch_job(..., authorize=True)`.
6. Outside the interactive Blender process, run `run_2d_render_batch.py` with the exact batch
   job/hash and Blender executable. It launches each staged child in an isolated background
   Blender, verifies child/helper hashes and receipts, and rolls back verified earlier outputs
   if a later child fails.
7. Accept success only when status is `created`, the published count equals the reviewed total,
   all artifact hashes and the batch receipt hash are present, and the interactive Scene is
   unchanged. Remove only this attempt's batch job and child stage/job files; retain requested
   successful PNGs.

## Fail closed

Refuse stale Profile bindings, changed batch/child/stage/job/helper hashes, output collisions,
mixed output directories, reordered items/artifacts, missing receipts or incomplete child
publication. Rollback removes an earlier output only while its bytes still match the recorded
hash. If another process changes it, preserve it and report incomplete rollback.

## Boundaries

This Skill does not create rigs or Actions, retarget, edit animation, invent view sets, render
in parallel, resume partial batches, assemble sprite sheets, configure Unity, or delete unknown
files. A successful PNG batch is not engine-import or visual-quality certification.
