---
name: blender-render-normal-pass-png
description: Render a new RGBA8 camera-basis shading-normal PNG for one exact static Blender Mesh Object. Use for normal-map-like 2D passes that preserve flat and smooth base-Mesh shading; does not edit sources, evaluate modifiers or animation, infer settings, or create tangent-space, depth, material-ID, silhouette, or SDF passes.
---

# Render Blender Normal Pass PNG

Render one reviewed static Mesh to a camera-basis shading-normal pass. The isolated renderer
writes a temporary 32-bit float OpenEXR, then performs deterministic CPU conversion to the
new RGBA8 PNG. It never renders directly to the published PNG because Blender's direct
shader-to-PNG conversion is not byte-exact.

## Inputs

Require exact `scene_name` and `object_name`, orthographic direction/up, framing margin,
resolution and a new absolute `.png` target. Build
`gameassetai.2d-normal-pass-request.v1` with `CAMERA_BASIS`, `SHADING_NORMAL`,
`SIGNED_XYZ_TO_UNORM_RGB`, transparent-black background, disabled anti-aliasing, nearest
neighbor, RGBA8 and `overwrite: false`. Do not infer any field from the active Camera,
selection, material or Profile.

Camera-basis X is camera right, Y is camera up and Z is camera back toward the camera. The
Blender shading normal is face-forward, so a visible front-facing surface has positive Z.

## Workflow

1. Validate the request outside Blender with `validate_2d_normal_pass_request.py`.
2. In Blender, load that validator and `inspect_2d_normal_pass_candidate.py`. Continue only
   for `candidate_for_review`; report blockers, Mesh facts, camera basis, flat-face reference
   samples and all three source/setup/output fingerprints.
3. Load `preview_2d_normal_pass_framing.py`; report its exact orthographic plan. Obtain
   confirmation for this reviewed request and new output before writing anything.
4. After confirmation, use `stage_2d_normal_pass_source.py` and
   `build_2d_normal_pass_job.py` to create a fresh hash-bound stage/job beside the target.
5. Launch a separate background Blender on that stage with `render_2d_normal_pass.py`, the
   exact job SHA-256 and this Skill's scripts directory. Remove only this invocation's
   stage/job after success or failure; the renderer removes its owned EXR/PNG stages.
6. Accept only `status: created` and `png_published: true`. Report artifact/receipt hashes,
   dimensions, alpha bounds, foreground pixels, unique RGBA count and camera basis.

## Safety and limits

Refuse missing, empty, hidden or Edit Mode Meshes; parents, constraints, modifiers,
animation, Shape Keys, linked data, stale fingerprints, target/`.meta` collisions or missing
authorization. The isolated stage contains one independent Object/Mesh copy and replaces
only that copy's materials. Do not save or modify the interactive Scene.

This v1 workflow uses the static base Mesh and Blender's face-forward shading normal. It
does not support evaluated/deformed geometry, Actions, custom pass composition, alternate
normal spaces/sources/encodings, anti-aliasing, existing-output replacement, Unity import or
visual-quality certification.
