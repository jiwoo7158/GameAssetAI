# Character base creation validation — 2026-10-25

## Scope

`blender-create-character-base` creates one visible stylized low-poly humanoid base Mesh from
explicit proportions, pose and colors. Schema v1 preserves the original separate-volume
blockout. Schema v2 retains `VOLUME_ISLANDS` and refuses the rejected `VOXEL_CONNECTED` mode.
Schema v3 adds guarded `BOOLEAN_CONNECTED`, which unions deliberately overlapping semantic
volumes without whole-body voxel remeshing.
Schema v4 adds explicit `DEFORMATION_TEMPLATE`, which duplicates a hash-pinned local CC0 Mesh,
preserves topology and UV loops, and applies bounded non-affine proportion controls. V4 remains
experimental evidence, not accepted product input for general rigging or animation.

## Current status

`VOLUME_ISLANDS` remains a usable visible blockout/fixture mode. The validator now refuses
`VOXEL_CONNECTED`. Live review found unintended fusion/bridging around nearby leg and foot geometry
even though it produced one closed manifold component. Do not bypass the validator or use the old
output for rig, animation, render or export claims.

The v3 candidate is now implemented and passes automatic component, closed-manifold,
bilateral foot/lower-leg clearance, below-knee cross-side-edge, and Blender QuadriFlow-preflight
micro-edge gates. A live four-view check
showed separate legs and feet with intended ankle/hip/shoulder connections. This is agent-reviewed
engineering evidence; user visual acceptance is still required, followed by a separate
deformation-topology/UV/pose gate before downstream product rigging.

The v4 path was validated with Blender Studio Human Base Meshes v1.4.1
`GEO-body_male_stylized` (`CC0-1.0`), supplied by absolute path and exact SHA-256 rather than
vendored. Compact and lanky outputs each retain 12,502 vertices, 12,500 quads, one closed
component and 50,000 UV loops. A bad-hash request restored the exact datablock baseline; the
external source hash stayed unchanged; both `.blend` files reopened in Blender 5.0.1. Armature
probes exercised elbow, knee, shoulder and hip, but the lanky knee reached a minimum local
face-area ratio of 0.052 and the generated-fixture rig needed validation-only arm refitting.
Therefore the provider is implemented and representative, while the `deformation-ready`
acceptance gate remains failed pending rig/weight adaptation.

## Output

- one new owned Collection;
- one Mesh Object and one Mesh data-block;
- semantic head, neck, torso, pelvis, arms, hands, legs and feet volumes in that Mesh;
- A-pose or T-pose;
- skin, primary outfit, secondary outfit and boots material slots;
- optional one-component exact-Boolean topology that preserves the source material roles;
- component counts before and after topology conversion;
- non-manifold edge count and bilateral semantic-clearance evidence;
- request and receipt SHA-256 evidence.

## Focused evidence

The current Blender 5.0.1 factory-startup fixture passes 22 checks for authorization refusal,
one-Mesh volume-blockout creation, four material slots, nontrivial topology, symmetric horizontal
bounds, expected ground/height bounds, hashes, explicit connected-mode refusal, ownership cleanup
exact output naming, guarded Boolean connection, manifold topology, bilateral clearance, suspended
voxel refusal, bounded post-Boolean micro-edge cleanup, ownership cleanup and exact global
restoration. Earlier 13-check voxel evidence is
historical and rejected.

The cleanup removes only degenerate/sliver edges below Blender's native QuadriFlow `1e-4`
preflight tolerance, recalculates normals and refuses any result that still contains one. It does
not claim automatic retopology or deformation readiness. A compact/lanky rerun proved that this
allows QuadriFlow to execute while preserving separated legs and feet, but neither QuadriFlow nor
ReQuad passed the later topology gate: QuadriFlow damaged UV validity and retained intersection
candidates, while ReQuad's engine output contained open boundaries. The generated joint grids were
not accepted as explicit deformation-oriented edge flow.

The live v3 candidate `GAA Scout v3 Boolean Current` has 369 vertices, 373 polygons, one component,
zero non-manifold edges, 0.024138 m minimum foot/lower-leg centerline clearance and no cross-side
edge below the knee. It remains visible in `GameAssetAI_Character_Topology_v3_Workbench`.

A live v2 candidate was created in `GameAssetAI_Character_Topology_Workbench`: 3,738 vertices,
3,738 quad polygons, one component, no boundary/non-manifold edges and four material roles. The
same candidate accepted the existing 18-bone rig and all 3,738 vertices received deform weights.
A first reversible arm/leg pose smoke test completed without a disconnected part and was restored
to rest pose.

That evidence is now classified as a failed validation design: it proved mechanical connectivity
and cleanup but did not test intended anatomical separation. The live candidate was rejected after
front-view inspection exposed fused/bridged lower-body geometry.

The portable v2 source bundle is `.local/source-bundles/blender-create-character-base-v2.zip`
(SHA-256 `8972ee4b01c9827df788accc8e3ba3bb3d31c259b841b243a771924c148adfaf`).
That archive is retained as historical connected-mode evidence. The current suspension bundle is
`.local/source-bundles/blender-create-character-base-suspended-20261025.zip` (SHA-256
`e4bea3ad99cbe569ce10856a34d91bacfd00ab9bd414f4723fa4254aa9e0b3a2`).
The current v3.1 source bundle (including failure-path Blender context restoration) is
`.local/source-bundles/blender-create-character-base-v3.1-20261025.zip` (SHA-256
`f3fca1a0912aff7545f364cd950d719189a5e007eb1777a90abf212a408a774a`).
The bounded micro-edge-cleanup source bundle is
`.local/source-bundles/blender-create-character-base-microedge-20261026.zip` (SHA-256
`720a31e2858136337429de26e56920c92b5d3b123b49732800b5ab353c93f065`). The installed Workspace
copy is hash-aligned with source; its previous installed copy is preserved under
`D:/AI/GameAssetAI-Workspace/.agents/skill-backups/blender-create-character-base-20261026-pre-microedge-cleanup`.

## Boundary

`VOXEL_CONNECTED` does not prove a usable deformation input. Global voxel remeshing can connect
spatially close but semantically separate surfaces. The live candidate also has many poles and no
UV layout. Material
boundaries are reconstructed from the nearest source surface, and the current rig still uses
rigid per-region v1 weights. Production topology, joint blending, UVs, semantic revision controls,
Mixamo compatibility and animation-ready export therefore remain later stages.

## B6.1 bounded styled template creation and revision — 2026-11-04

B6.0 code review classified the existing layers as follows: v4 hash/source/topology/UV loading,
owner-token rollback and material roles are reused; proportion controls are extended; primitive/
Boolean character generation remains blockout-only; voxel connection remains rejected. M2 v3 is
reused only behind explicit landmarks and visible deformation review. M3.3/M3.4/M4 remain usable
only after that gate and were not changed or rerun. No external runtime was needed. Hair/clothing/
equipment fitting needs a new bounded component-production and refit strategy in B6.2; creatures
need a different topology/rig path in B6.3.

Creation v5 retains the explicit hash-pinned CC0 v1.4.1 source boundary and adds recorded art-
direction provenance plus bounded semantic controls for head, torso, arms, legs, hands and feet.
Six point-domain weight attributes drive real coordinate changes without changing connectivity or
UV loops. Revision v1 accepts only an unrigged owned v5 source and creates a new Collection,
Object and Mesh; Materials are shared read-only and vertices outside adjusted regions remain exact.

The accepted SD/stylized representative and its larger-head, shorter-arm, larger-hand/foot copy
retain 12,502 vertices, 12,500 quads, 25,000 triangles, complete UVs and zero bilateral symmetry
error. The revision changed 8,988 vertices and preserved 3,510 exactly. Bad source hash and an
injected post-copy failure restored exact Blender baselines. Six common-camera views were directly
accepted and the saved Blend reopened in Blender 5.0.1. Evidence is under
`D:/Blender/MCP_Test/GameAssetAI/runs/B6.1/20261104T023823Z-stylized-sd-humanoid-e69798bc`.

This is a style-aware base from one known topology, not arbitrary character generation. It does
not generate hair, clothing, equipment, new facial topology, Shape Keys or creatures. Empty eye
sockets/basic facial forms remain inherited from the source template.
