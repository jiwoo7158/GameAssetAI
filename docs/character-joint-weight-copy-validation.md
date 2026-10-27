# Character joint-weight copy validation -- 2026-10-25

## Status: algorithm retained, live product evidence invalidated

`blender-adjust-character-joint-weights-copy` previews and creates one independent character
Object/Mesh copy with an explicit `SHOULDER` or `HIP` transition-width adjustment. It preserves
the source object, geometry, materials and verified owned Armature, and redistributes only the
selected adjacent bone-pair's existing total weight.

The Blender 5.0.1 factory-startup fixture passes eight focused checks: blocker-free preview,
authorization refusal, persistent independent copy creation, shared verified Armature, exact
geometry preservation, exact source-weight preservation, metrics/receipt generation and exact
cleanup.

Live application on `GAA Scout Connected Current` used a `0.035` character-height transition
width on both sides:

- shoulder: 456 vertices / 840 measured local edges; maximum target-pair edge delta changed from
  `0.539509` to `0.523474`;
- hip: 200 vertices / 344 measured local edges; maximum target-pair edge delta changed from
  `0.562104` to `0.373643`.

With the same explicit six-bone review pose, evaluated edge-stretch comparisons were:

| Region | Source p95 / max | Refined p95 / max |
| --- | --- | --- |
| Shoulder | `0.216139 / 0.918174` | `0.201798 / 0.762483` |
| Hip | `0.721259 / 3.204531` | `0.463600 / 3.163987` |

The final candidate was restored to rest pose. These numbers show reduced discontinuity and
stretch for this pose, but the source was later rejected because global voxel remeshing fused or
bridged lower-body geometry. These values prove only copy/preservation and local weight arithmetic;
they are not character-quality progress. Suspend product routing until a source passes anatomical
clearance, intended-connectivity, self-intersection and multi-view acceptance gates.

Checkpoint: `D:/Blender/MCP_Test/GameAssetAI_Character_JointRefined_v3.blend` (310,580 bytes,
SHA-256 `f3970f052f370634856da4492382cfc98245fc7b44131de5d3aca950be8123ed`).
Portable Skill bundle: `.local/source-bundles/blender-adjust-character-joint-weights-copy.zip`
(6,840 bytes, SHA-256 `b11cc05fe556dd9a4a2e4bb8970901e20fc05c8fc0c66e2461adfc666d496f93`).
