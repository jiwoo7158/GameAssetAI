---
name: blender-render-material-mask-png
description: Render a new RGBA8 PNG mask for one exact material slot on one static Blender Mesh while preserving visibility and occlusion. Use when a material-assignment mask is needed from existing geometry; does not infer materials, edit the source Scene, support modifiers/animation, or create object-ID, normal, depth, silhouette, or SDF passes.
---

# Render Blender Material Mask PNG

Render one exact material slot from one static Mesh as an opaque-color mask. The isolated
copy temporarily replaces material appearance with internal ID shaders so non-target faces
still occlude target faces. Never alter or save the interactive Blender Scene.

## Inputs

Require exact Scene and Mesh Object names, a nonnegative `material_slot_index`, opaque
normalized `visible_rgba`, an orthographic direction/up pair, framing margin, resolution,
and a new absolute `.png` path. Sampling is fixed to disabled anti-aliasing and nearest
neighbor. Output is RGBA8 with `overwrite: false`. Do not select a slot by appearance or
guess from a material name.

## Workflow

1. Build `gameassetai.2d-material-mask-request.v1` and run
   `validate_2d_material_mask_request.py` outside Blender.
2. In Blender, load the validator plus `inspect_2d_material_mask_candidate.py`. Continue
   only for `candidate_for_review`; report the exact slot name/index, assigned polygon
   count, Mesh facts, bounds, blockers and four fingerprints.
3. Load `preview_2d_material_mask_framing.py` and report its camera plan. Confirm this
   exact request and new output before any write.
4. After confirmation, load `stage_2d_material_mask_source.py` and stage an independent
   Mesh copy beside the target. Create the hash-bound job with
   `build_2d_material_mask_job.py`. Reuse neither stage nor job after any change.
5. Launch a separate background Blender with the reviewed stage and
   `render_2d_material_mask.py`, passing the exact job SHA-256 and this Skill's scripts
   directory. Delete only this invocation's stage/job after success or failure.
6. Accept only `status: created` and `png_published: true`. Report the artifact and receipt
   hashes, dimensions, alpha bounds, visible pixels, unique RGBA count, material slot and
   non-target occluder pixels.

## Safety and limits

Refuse missing/empty/unassigned slots, invalid face slot indices, Edit Mode, hidden or
empty Meshes, parents, constraints, modifiers, animation, Shape Keys, linked data, stale
fingerprints, output/`.meta` collisions and missing authorization. The whole base Object
defines stable framing. Original material shaders and textures are ignored and untouched.
The internal red/green ID render is converted to the requested two-color PNG before atomic
no-overwrite publication. This is a static base-Mesh material mask, not an object-ID,
silhouette, normal, depth, SDF, compositor, evaluated-deformation, Unity-import or visual
quality workflow.
