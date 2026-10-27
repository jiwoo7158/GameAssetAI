---
name: blender-render-impostor-bundle
description: Render an explicit static Blender Mesh into a hash-bound COLOR/NORMAL/DEPTH impostor bundle with one shared orthographic framing plan, all-or-nothing rollback, and manifest-last publication. Use only when every view, pass, child request, and new output path is explicit; this Skill does not infer directions, animate geometry, include Object-ID, or configure Unity.
---

# Blender Render Impostor Bundle

Coordinate existing static color, camera-basis normal, and camera-linear depth renderers. Do not create a second rendering implementation or modify the interactive Blender Scene.

## Accepted boundary

- Use `gameassetai.2d-impostor-bundle-request.v1` with 1-32 explicit views and 2-96 child requests.
- Every view must contain the same ordered set of at least two distinct passes from `COLOR`, `NORMAL`, and `DEPTH`.
- All children must name one exact Scene and one exact static base-Mesh Object and share each view's projection, direction, up vector, margin, and resolution.
- COLOR children are explicit-only: all Profile provenance fields must be null. Do not read or infer an active Profile.
- Require fixed `LIST_ORDER / ALL_OR_NOTHING / ROLL_BACK_BUNDLE_OUTPUTS / REJECT` policy.
- Require every PNG and the JSON result manifest to be a new regular path in one existing directory. Refuse an existing target or adjacent `.meta` file.

## Workflow

1. Inspect the exact Scene/Object through Blender MCP. Load the packaged helpers from `scripts/`; keep the three child helper stacks in separate namespaces when executing them together.
2. Run `validate_2d_impostor_bundle_request.py`, then `preview_2d_impostor_shared_framing.py`. The preview is read-only: it reruns every candidate and calculates one canonical base-Mesh camera plan per view without creating a Camera.
3. Report the ordered views/passes, common plans, request/source/plan fingerprints, output paths, and every blocker. Do not stage or render until the user explicitly approves these exact settings and targets.
4. After approval, rerun the complete preflight and shared preview. For each child, run its packaged validator, candidate inspection, framing preview, staging helper, and job builder. Require its common plan to equal the reviewed shared plan; only the COLOR renderer's redundant `camera_frame` field may be ignored in this comparison.
5. Run `build_2d_impostor_bundle_job.py` with the fresh preflight, shared preview, child stage/job paths, exact helper descriptors, and explicit authorization. Never hand-edit a job.
6. Run `run_2d_impostor_bundle.py` outside the interactive Blender process with the exact job path/hash and Blender executable. It renders children sequentially in isolated processes, validates every receipt and artifact, rolls back unchanged outputs from this attempt on failure, validates the result manifest, and publishes the manifest last.
7. Report success only when the runner returns `created`, every PNG is published, and the JSON manifest is published. Report artifact and receipt hashes. Remove only stage/job files created by this attempt; retain the approved PNGs and manifest.

## Fail closed

Refuse stale request/source/shared-plan bindings, missing or changed helpers, child-plan disagreement, linked or unsupported Blender data, collisions, output drift, malformed receipts, partial success, or uncertain cleanup. Never delete a changed output. Do not save the interactive `.blend` or change its selection, frame, Scene, Object, Mesh, materials, or render settings.

## Non-goals

This Skill does not support Object-ID, Actions, evaluated/deformed geometry, inferred compass directions, Profile merging, sprite-sheet assembly, Unity import/material setup, LOD generation, or visual-quality certification. Use the dedicated Skills for those separate tasks.
