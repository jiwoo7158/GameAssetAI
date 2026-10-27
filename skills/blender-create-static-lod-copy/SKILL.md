---
name: blender-create-static-lod-copy
description: Preview and explicitly create one independent lower-detail copy of an existing static Blender base Mesh using a user-specified Decimate ratio. Use for guarded copy-only LOD generation; do not use to overwrite sources, infer ratios or chains, process rigged/evaluated assets, or configure Unity LODGroups.
---

# Blender Create Static LOD Copy

Create at most one exact-named independent Object/Mesh pair from one explicit static base Mesh.
Never infer the Scene, source, output names, ratio, chain length, or engine thresholds.

## Request

Build the exact `gameassetai.static-lod-copy-request.v1` object expected by
`scripts/validate_static_lod_copy_request.py`. V1 supports only:

- `DECIMATE_COLLAPSE` with an explicit finite ratio from `0.01` through `0.99`
- `triangulate: false`
- unused, distinct output Object and Mesh names
- fixed base-Mesh-only dependency refusal, source preservation, independent output, exact
  transform copy, shared read-only material datablocks, copied UV layers, and
  `PREVIEW_THEN_EXPLICIT_APPLY`

Reject missing/unknown fields and unsupported policy changes. Profile budgets are not ratios
or mutation permission.

## Preview before mutation

1. Load the packaged validator and `preview_static_lod_copy.py`.
2. Validate the request and retain its request SHA-256.
3. Run the preview with that expected hash. It uses disposable independent IDs and must return
   `candidate_for_review` with no errors or blockers.
4. Report the source/setup/preview fingerprints, requested versus actual triangle ratio,
   topology counts, UV-layer/material/transform preservation, bounds deltas, review items and
   limitations. The preview creates no requested persistent output.
5. Ask the user to approve this exact preview and intended output names. Do not apply within the
   same unconfirmed step.

## Apply only after explicit approval

Call `apply_static_lod_copy.py` with `authorized=true` and all four exact reviewed fingerprints.
The helper repeats the preview immediately before mutation, refuses drift or new name collisions,
creates one independent Object/Mesh, validates it against the review, and returns a receipt
fingerprint. Report the exact created names, triangle count/ratio, source preservation and receipt.

On failure, report `failure_cleanup`. The helper removes only IDs bearing its per-run ownership
token; `unverified` cleanup requires manual inspection and no retry. Never delete or replace an
existing Object/Mesh to make a request pass.

## Boundaries

Refuse parents, modifiers, constraints, Shape Keys, vertex groups, animation, linked/override or
shared Mesh data, color attributes, and unsupported custom attributes. This Skill does not certify
silhouette, UV layout quality, shading, normals/tangents, runtime cost, Unity import, transition
quality, or LODGroup thresholds. Generate additional levels only as separately named, separately
previewed and separately approved requests.
