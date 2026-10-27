---
name: derive-png-silhouette-mask
description: Derive a new solid-color RGBA8 silhouette mask from the alpha channel of one existing PNG. Use after a verified static or animation-frame render when an exact binary or alpha-preserving mask is needed; does not render Blender geometry, infer colors, overwrite files, or create normal/depth/object-ID passes.
---

# Derive PNG Silhouette Mask

Create one new mask from one exact RGBA8 PNG without changing the source. This is a
deterministic file postprocess, so do not call Blender or alter its Scene.

## Inputs

Require all of the following:

- absolute existing non-linked source `.png` path and its lowercase SHA-256;
- absolute new target `.png` path in an existing non-linked directory;
- one explicit opaque normalized `visible_rgba` color;
- `alpha_policy`: `BINARY_NONZERO` or `PRESERVE_ALPHA`;
- `overwrite: false`.

`BINARY_NONZERO` makes every source pixel with alpha above zero fully opaque.
`PRESERVE_ALPHA` replaces visible RGB while retaining every source alpha byte. Fully
transparent output pixels are canonical transparent black in both modes. Do not infer a
threshold, mask color or game-specific policy.

## Workflow

1. Build an exact `gameassetai.2d-silhouette-mask-request.v1` JSON request.
2. Run `python -B scripts/validate_2d_silhouette_mask_request.py <request.json>`.
   Continue only for `candidate_for_review`; report dimensions, visible/partial-alpha
   counts, source hash, request hash and `candidate_fingerprint`.
3. Confirm the requested new output and alpha policy. Then run
   `python -B scripts/derive_2d_silhouette_mask.py <request.json>
   --expected-candidate-fingerprint <fingerprint> --authorize`.
   Never reuse a fingerprint after any request/source/output change.
4. Accept only `status: created` and `published: true`. Report output dimensions,
   SHA-256, alpha bounds, visible/partial-alpha counts, unique RGBA count and receipt hash.

## Safety and limits

Refuse missing, linked, malformed, non-RGBA8 or interlaced inputs; stale hashes; unknown
fields; source/target identity; existing target or `.meta`; and missing authorization.
Publication uses a verified same-directory stage and never overwrites. A failed invocation
removes only its unchanged owned output; a concurrently changed output is retained and
reported. This Skill creates only an alpha-derived silhouette mask. It does not provide
material/object masks, normals, depth, signed-distance fields, outlines, sprite slicing,
Unity import, Blender rendering or visual-quality certification.
