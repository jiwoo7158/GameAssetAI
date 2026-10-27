---
name: blender-inspect-static-colliders
description: Inspect explicitly named existing Blender base-Mesh collider candidates relative to one static render Mesh, including topology, world bounds, dependencies, and bounded convexity evidence. Use for read-only collider preflight; do not use to discover or generate colliders, create LODs, or configure Unity.
---

# Blender Inspect Static Colliders

Inspect existing explicitly named collider Mesh candidates without changing Blender. Never infer colliders from names, selection, collections, or proximity.

## Request boundary

Use `gameassetai.static-collider-candidate-request.v1` with:

- one exact Scene and render base-Mesh Object
- 1-32 distinct exact collider Mesh Objects
- explicit `STATIC_TRIANGLE_MESH` or `CONVEX_MESH_CANDIDATE` intent per collider
- `BASE_MESH`, `WORLD`, and fixed `EXPLICIT_ONLY / BASE_MESH_ONLY / READ_ONLY` policy
- an explicit finite `0..0.01` scale-relative tolerance for each convex candidate; triangle-mesh candidates require null tolerance

Do not translate engine settings or Profile values into missing request fields.

## Workflow

1. Load both packaged helpers from `scripts/` in order: validator, then inspector.
2. Validate the complete request and retain its request SHA-256. If validation fails, report the errors and stop.
3. Run the Blender inspector with the exact request hash. It must remain in Object mode and access only the named Scene/Objects.
4. Report render/collider Mesh counts, transforms, world AABBs, AABB relationships, dependencies, and convexity evidence. Distinguish `candidate_for_review` from blocker-free: a candidate may contain blockers.
5. Report the source fingerprint and limitations. Confirm that no Scene, Object, Mesh, selection, mode, file, or engine component was changed.

## Fail closed

Treat missing/non-Mesh or edit-mode Objects, nonfinite/singular transforms, modifiers, constraints, parents, Shape Keys, vertex groups, animation, linked/override data, stale request hashes, and invalid convex evidence as errors or blockers. Do not evaluate modifiers or the dependency graph to make a blocked candidate appear valid.

Closed-half-space evidence does not certify gameplay coverage, physics cost, rigid-body compatibility, Unity import, or visual quality. This Skill does not create or replace collider geometry and does not inspect or generate LOD chains.
