---
name: blender-render-action-png-sequence
description: Render one explicitly named Blender Action on one reviewed skinned Mesh as a collision-safe orthographic pixel-style PNG sequence in an isolated background Blender process. Use for animation sprite frames with stable range-wide framing, optional palette/value-step/one-pixel outline processing, and no overwrite. Does not retarget, edit, create, or guess rigs, Actions, root bones, frame ranges, or game-specific settings.
---

# Render Action PNG Sequence

Render one reviewed Mesh/Armature/Action to a complete ordered PNG sequence without saving
or rendering in the interactive Blender Scene. Existing Mesh, rig, Action and files are user
data. Inspect them before staging and leave them unchanged.

## Required inputs

Collect exact Scene, Mesh Object, Armature Object and Action names; an Action slot identifier
when needed; inclusive integer start/end/step; playback FPS; an existing absolute output
directory; filename prefix/index/padding; and all static pixel-render settings. Choose either
one complete explicit settings set or the complete active Profile `gameassetai-2d-preset`;
never merge them. Use active Profile name/reference/profile hashes only when that preset
supplies the settings. Otherwise set all three Profile fields to `null` and do not infer or
reuse game rules.

The first version requires:

- request schema `gameassetai.2d-action-sequence-request.v1`
- one exact Armature modifier and at least one matching deform vertex group
- pose-transform F-Curves referencing existing bones, with no constraints, drivers, Shape
  Keys, linked data or unsupported parents
- `ACTION_RANGE` bounds, `OBJECT_ORIGIN` anchor, integer sampling and at most 2048 frames
- one stable orthographic camera fitted to all sampled frames
- the static v3 `PIXEL`/`OWNED_NEUTRAL`/RGBA8/no-overwrite style contract
- `overwrite: false`; every target PNG and sibling `.meta` must be absent

## Workflow

1. Check Blender MCP status and inspect the current Scene. Refuse a disconnected or
   incompatible target rather than guessing state.
2. Load these scripts into one shared Blender execution namespace in this order:
   `validate_2d_static_render_request.py`, `extract_2d_profile_preset.py`,
   `resolve_2d_profile_preset.py`, `validate_2d_action_sequence_request.py`,
   `inspect_2d_action_sequence_candidate.py`, `preview_2d_action_sequence_framing.py`,
   `stage_2d_action_sequence_source.py`, and `build_2d_action_sequence_job.py`.
3. For Profile settings, freshly read the active Profile context, resolve
   `ACTION_SEQUENCE`, and retain its complete four-hash binding. An absent/invalid preset is
   not a default. Explicit mode must not consult or partially merge a preset. Build the exact
   request and run validation, candidate inspection and framing. Report any
   blocker and create no file unless the results are respectively ready, reviewable and
   planned. Never bind the requested Action to the user's Armature merely for inspection.
4. After the user has requested the exact render/settings, reread and resolve any selected
   Profile preset with the retained `expected_binding`; refuse any change. Create fresh
   sibling paths named
   `.gameassetai-2d-sequence-<token>.stage.blend` and
   `.gameassetai-2d-sequence-<token>.job.json`. Authorize staging and job creation only for
   this freshly reviewed hash chain. Never reuse a prior preview, stage or job.
5. Start a separate background Blender with the returned stage loaded. Run
   `render_2d_action_sequence.py` with `--job`, the exact returned `--job-sha256`, and
   `--helper-root` pointing to this Skill's `scripts` directory. Do not execute the renderer
   inside the interactive Blender process.
6. Accept success only when the child reports `created`, `pngs_published: true`, the published
   count equals the planned frame count, every target is a new regular PNG, and the ordered
   artifact hashes and receipt hash are present. Report the output range, dimensions, hashes,
   alpha bounds, anchor, and receipt SHA-256.
7. Remove only the exact job and stage created by this request. The renderer removes its own
   exact temporary PNGs. Never remove a target, `.meta`, user `.blend`, or unknown file.
   Reinspect the interactive Scene and report whether its inventory changed.

## Atomic publication and refusal

The renderer must finish and validate every temporary frame before publishing any target.
If publication fails partway, it rolls back only targets created by that invocation. Refuse
existing targets or `.meta` files, changed hashes, malformed stages/jobs, unexpected rig
bindings, unsupported render modes, empty frames, temporary-path collisions, or any request
to overwrite. Never describe a partial or failed sequence as usable output.

## Boundaries

This Skill does not create or repair rigs, retarget or edit Actions, guess a root bone,
sample subframes, use per-frame camera framing, assemble sprite sheets, import into Unity,
resume partial output, render multiple Actions/directions, or guarantee visual loop quality.
Those remain separately reviewed stages.
