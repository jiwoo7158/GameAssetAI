---
name: blender-render-object-id-png
description: Render a new RGBA8 color-ID PNG for 2 to 63 explicitly named static Blender Mesh Objects, preserving mutual depth occlusion. Use for object-level segmentation/selection passes; does not infer Scene members, edit sources, evaluate modifiers or animation, or create material-slot, normal, depth, silhouette, impostor, or SDF passes.
---

# Render Blender Object-ID PNG

Render an explicit ordered set of static Mesh Objects to one color-ID image. Only listed
Objects participate in union framing and mutual depth occlusion. An isolated float stage
uses internal numeric IDs, then CPU-remaps them to the exact requested RGBA8 colors without
touching the interactive Blender Scene.

## Inputs

Build `gameassetai.2d-object-id-request.v1` with exact `scene_name` and 2 to 63 `objects`.
Each entry requires a unique exact `object_name` and opaque normalized `id_rgba`; colors must
remain unique after RGBA8 rounding. Also require orthographic direction/up, framing margin,
resolution and a new absolute `.png` target. Sampling is fixed to disabled anti-aliasing and
nearest neighbor; output is RGBA8 with `overwrite: false`. Never infer members or colors
from the Scene, selection, collections, materials, visibility, names or Profile.

## Workflow

1. Validate with `validate_2d_object_id_request.py` outside Blender.
2. In Blender, load the validator and `inspect_2d_object_id_candidate.py`. Continue only for
   `candidate_for_review`; report the exact ordered names/colors, per-Mesh facts, union
   bounds, blockers, camera basis and source/setup/output fingerprints.
3. Use `preview_2d_object_id_framing.py` to review the exact union-framing plan. Obtain
   confirmation for this request and new output before writing.
4. After confirmation, use `stage_2d_object_id_source.py` and
   `build_2d_object_id_job.py` to make a fresh independent stage and hash-bound job.
5. Launch separate background Blender on the stage with `render_2d_object_id.py`, the exact
   job SHA-256 and this Skill's scripts directory. Remove this invocation's stage/job after
   success or failure; the renderer removes its owned EXR/PNG stages.
6. Accept only `status: created` and `png_published: true`. Report artifact/receipt hashes,
   dimensions, alpha bounds, exact visible colors and per-Object visible pixel counts.

## Safety and limits

Refuse missing, duplicate, non-Mesh, empty, hidden or Edit Mode Objects; parents,
constraints, modifiers, animation, Shape Keys, linked data, duplicate quantized colors,
stale fingerprints, target/`.meta` collisions or missing authorization. Unlisted Objects
must be absent from the stage even if they would visually occlude a listed Object. Only
independent staged copies have materials replaced.

Fully occluded listed Objects are valid and report zero visible pixels, but a wholly empty
output fails. This v1 workflow does not support per-face/material IDs, unlisted occluders,
evaluated/deformed geometry, anti-aliased edges, more than 63 IDs, output replacement,
Unity import or visual-quality certification.
