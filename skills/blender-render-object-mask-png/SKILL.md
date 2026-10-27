---
name: blender-render-object-mask-png
description: Render a new RGBA8 visibility mask for one exact static Blender Mesh Object against an explicit list of Mesh occluders. Use for object-level selection or ID-style masks that must preserve depth occlusion; does not infer Scene participants, edit sources, support evaluated animation, or create material, normal, depth, silhouette, or SDF passes.
---

# Render Blender Object Mask PNG

Render one exact static target Mesh as an opaque-color mask. Only an explicit ordered list
of other Mesh Objects participates as occluders; unrelated Scene Objects are excluded. An
isolated stage uses internal ID shaders so depth visibility is retained without touching the
interactive Blender Scene.

## Inputs

Require exact `scene_name`, `target_object_name`, and `occluder_object_names` (zero to 63
unique names that exclude the target), plus opaque normalized `visible_rgba`, orthographic
direction/up, framing margin, resolution and a new absolute `.png` path. Sampling is fixed
to disabled anti-aliasing and nearest neighbor; output is RGBA8 with `overwrite: false`.
Never infer occluders from the active collection, selection, visibility or Scene contents.

## Workflow

1. Build `gameassetai.2d-object-mask-request.v1`; validate it with
   `validate_2d_object_mask_request.py` outside Blender.
2. In Blender, load the validator and `inspect_2d_object_mask_candidate.py`. Continue only
   for `candidate_for_review`; report the exact target/occluder names, Mesh facts, union
   bounds, blockers and four fingerprints.
3. Load `preview_2d_object_mask_framing.py`. It frames the union of exactly those Objects.
   Confirm this exact request and new output before any write.
4. After confirmation, use `stage_2d_object_mask_source.py` to copy only the reviewed
   Objects into an owned stage and `build_2d_object_mask_job.py` to create its hash-bound
   job. Reuse neither artifact after any change.
5. Launch a separate background Blender on that stage with `render_2d_object_mask.py`, the
   exact job SHA-256 and this Skill's scripts directory. Remove only this invocation's
   stage/job after success or failure.
6. Accept only `status: created` and `png_published: true`. Report target/occluder names,
   artifact and receipt hashes, dimensions, alpha bounds, target pixels, unique RGBA count
   and occluder pixels.

## Safety and limits

Refuse missing or duplicate Objects, non-Mesh/empty/hidden/Edit Mode inputs, parents,
constraints, modifiers, animation, Shape Keys, linked data, stale fingerprints,
output/`.meta` collisions and missing authorization. An entirely occluded target fails
instead of publishing an empty mask. Original geometry and materials are ignored only on
independent staged copies and are never saved. This is a static base-Mesh visibility mask,
not a multi-color object-ID atlas, material mask, evaluated/deformed pass, normal, depth,
SDF, compositor, Unity-import or visual-quality workflow.
