# Static Collider and LOD Workflow Decision

## Decision

Treat colliders and LODs as two separate workflows. They have different correctness
questions, engine constraints and destructive risks; one combined generator would hide those
differences. Start with read-only inspection of explicitly named existing collider Meshes.
Do not generate geometry, add engine components or reduce a render Mesh in the first slice.

## Existing-collider v1 boundary

The first request is `gameassetai.static-collider-candidate-request.v1`:

- one exact Blender Scene and one exact render base-Mesh Object
- 1-32 explicitly named, distinct existing base-Mesh collider Objects
- an explicit kind for every collider: `STATIC_TRIANGLE_MESH` or
  `CONVEX_MESH_CANDIDATE`
- explicit `WORLD` comparison space and `BASE_MESH` geometry source
- a scale-relative convexity tolerance only for convex candidates
- fixed explicit-only, base-Mesh-only, read-only policy

The inspector will report topology, transforms, world bounds, overlap/containment facts and
convex-candidate evidence. It must not claim that a collider is appropriate for gameplay,
that an engine will accept it, or that its cost is suitable. Those depend on the target engine,
body type and game profile.

## Refusal boundary

The initial Blender candidate must refuse missing or ambiguous Objects, edit mode, non-Mesh
types, modifiers, constraints, parenting, Shape Keys, animation, vertex groups, linked or
override data, nonfinite coordinates/transforms, singular transforms and stale request data.
It will inspect only base vertices/polygons and will not evaluate the dependency graph.

For `CONVEX_MESH_CANDIDATE`, open/non-manifold or degenerate geometry and a vertex outside a
face half-space beyond the explicit relative tolerance are blockers. Triangle-mesh candidates
may report those facts without being relabeled convex.

## Existing-LOD v1 direction

The next LOD inspection contract takes an explicit ordered chain of 2-8 existing base-Mesh
Objects. V1 requires contiguous indices beginning at LOD0, exact identical world matrices and
strictly decreasing base triangulation because these are explicit request policies rather than
inferred game defaults. It reports world bounds, triangle ratios and material-slot relationships.
It does not evaluate modifiers, infer naming, define screen thresholds or certify silhouette.

LOD creation remains a separate independent-copy operation requiring silhouette, UV/material
and engine-policy evidence. Collider acceptance never implies LOD acceptance.

The v1 request validator and Blender candidate inspector now pass offline and representative
native tests. A 12/8/4 triangle synthetic chain passes; stale request hashes, matrix drift,
modifiers and nondecreasing triangle order are blocked. The read-only Skill is packaged and
installed; refreshed-client evidence remains.

## Validation gates

1. Offline request hashing and refusal tests. Completed with five tests.
2. Read-only Blender candidate fixture with a closed convex Mesh, an invalid convex candidate,
   dependency refusal, stale-request refusal and exact teardown.
   Completed with nine checks on Blender 5.0.1 for repository, source-Skill and installed
   helpers.
3. Package and locally install a narrowly scoped inspection Skill. Completed; refreshed-client
   discovery and host behavior remain.
4. Collider generation, Unity component configuration and LOD generation require separate
   designs and representative tests.
