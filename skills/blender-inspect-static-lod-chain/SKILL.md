---
name: blender-inspect-static-lod-chain
description: Inspect an explicitly ordered chain of existing static Blender base-Mesh LOD Objects for triangle reduction, exact world-transform alignment, bounds relationships, materials, and unsupported dependencies. Use for read-only LOD preflight; do not use to discover, generate, decimate, export, or configure engine LODs.
---

# Blender Inspect Static LOD Chain

Inspect only the exact existing LOD Mesh Objects named by the user. Never infer a chain from names, Collections, visibility, selection, or triangle counts.

## Request boundary

Use `gameassetai.static-lod-chain-request.v1` with:

- one exact Scene and an ordered list of 2-8 unique Mesh Object names
- contiguous `level_index` values beginning at zero
- `BASE_MESH`, `WORLD`, and fixed `EXPLICIT_ONLY / BASE_MESH_ONLY / READ_ONLY` scope
- explicit `EXACT_WORLD_MATRIX` alignment and `STRICTLY_DECREASING` base-triangle policy

These are v1 request policies, not inferred game or engine defaults. Do not accept approximate transforms, evaluated modifiers, missing indices, screen thresholds, or generation instructions.

## Workflow

1. Load the packaged validator and inspector from `scripts/` in that order.
2. Validate the complete request and retain its SHA-256. Report validation errors and stop if it is not `ready`.
3. Run the Blender inspector with the exact request hash. It is read-only and resolves only the named Scene and base Meshes in Object mode.
4. Report every level's base vertices/edges/polygons/triangles, world transform/bounds, material slots, triangle ratios, center/extent relationships, dependencies, blockers, review items, and source fingerprint.
5. Distinguish a returned `candidate_for_review` from blocker-free readiness. Confirm that Blender state and files were not changed.

## Fail closed

Treat a stale request, missing/non-Mesh or edit-mode level, empty/nonfinite geometry, singular transform, modifier, parent, constraint, Shape Key, vertex group, animation, linked/override data, world-matrix difference, or nondecreasing triangle count as an error or blocker. Do not evaluate or apply modifiers to make a chain pass.

Triangle and AABB relationships do not certify silhouette, UVs, shading, runtime cost, transition quality, or engine compatibility. This Skill does not generate/decimate LODs, choose ratios or screen thresholds, export assets, configure Unity, or inspect colliders.
