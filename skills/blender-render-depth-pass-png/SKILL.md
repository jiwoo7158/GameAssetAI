---
name: blender-render-depth-pass-png
description: Render a new RGBA8 camera-linear depth PNG for one exact static Blender Mesh Object, normalized over that base Mesh's vertex depth range. Use for object-relative depth passes; does not edit sources, evaluate modifiers or animation, infer a range, or create normal, material-ID, silhouette, world-unit, scene-wide, or SDF passes.
---

# Render Blender Depth Pass PNG

Render one reviewed static Mesh to an object-relative camera-linear depth pass. The isolated
renderer writes a temporary 32-bit float OpenEXR and performs deterministic CPU conversion
to the new RGBA8 PNG without touching the interactive Blender Scene.

## Inputs and meaning

Require exact `scene_name` and `object_name`, orthographic direction/up, framing margin,
resolution and a new absolute `.png` target. Build `gameassetai.2d-depth-pass-request.v1`
with `CAMERA_LINEAR`, `BASE_MESH_POSITION`, `OBJECT_VERTEX_BOUNDS`,
`NEAR_BLACK_FAR_WHITE_UNORM_RGB`, transparent-black background, disabled anti-aliasing,
nearest neighbor, RGBA8 and `overwrite: false`. Never infer settings from an active Camera,
selection, material or Profile.

Project base-Mesh world vertices onto the view direction, which points back toward the
camera. Maximum projection is near/black; minimum is far/white. Refuse a depth span of
`1e-6` or less instead of inventing a constant range. This range is valid only for this
Object and request, not for comparing separate Objects or frames.

## Workflow

1. Validate the request outside Blender with `validate_2d_depth_pass_request.py`.
2. In Blender, load the validator and `inspect_2d_depth_pass_candidate.py`. Continue only
   for `candidate_for_review`; report blockers, Mesh facts, exact near/far projections and
   vertex indices, reference samples and source/setup/output fingerprints.
3. Load `preview_2d_depth_pass_framing.py` and report its exact orthographic plan. Obtain
   confirmation for this reviewed request and new output before writing.
4. After confirmation, create a fresh independent stage and hash-bound job with
   `stage_2d_depth_pass_source.py` and `build_2d_depth_pass_job.py`.
5. Launch a separate background Blender on that stage with `render_2d_depth_pass.py`, the
   exact job SHA-256 and this Skill's scripts directory. Remove this invocation's stage/job
   after success or failure; the renderer removes its owned EXR/PNG stages.
6. Accept only `status: created` and `png_published: true`. Report artifact/receipt hashes,
   dimensions, alpha bounds, foreground pixels, unique depth values and exact depth range.

## Safety and limits

Refuse missing, empty, hidden or Edit Mode Meshes; parents, constraints, modifiers,
animation, Shape Keys, linked data, stale fingerprints, insufficient depth span,
target/`.meta` collisions or missing authorization. Only the independent staged copy has its
materials replaced. Do not save or modify the interactive Scene.

This v1 workflow does not support perspective or clip/NDC depth, world-unit or scene-wide
normalization, named occluders, evaluated/deformed geometry, animation, anti-aliasing,
existing-output replacement, Unity import or visual-quality certification.
