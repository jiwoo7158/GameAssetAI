---
name: blender-create-character-base
description: Create or copy-revise a bounded humanoid base Mesh from explicit proportions, art direction and semantic body-region controls. Use native blockout modes or hash-pinned CC0 template v4/v5 paths for technical bases. Require separate user art-direction approval before treating a result as a character style or continuing to hair/clothing work.
metadata:
  contract: gameassetai.skill-contract.v1
  requirements: REQ-CHAR, REQ-STYLE, REQ-COST, REQ-SAFE
  evidence: representative
  external-dependencies: none
---

# Blender Create Character Base

## Requirements and responsibility

This user-facing creation specialist advances `REQ-CHAR`, `REQ-STYLE`, `REQ-COST` and
`REQ-SAFE`. It owns explicit stylized humanoid blockout creation and semantic blockout checks. It
does not own rig generation, Action authoring, general retopology or export. Route those stages
through their existing Skills only after this Skill's output has earned the required evidence.

## Implementation basis and dependencies

The native path uses Blender BMesh primitives, Blender's exact Boolean modifier and project-owned
validators. Its Boolean result removes only confirmed sub-`1e-4` sliver edges that
Blender 5.0 QuadriFlow rejects, then rechecks the result; this is source cleanup, not automatic
retopology. Optional schema v4 loads one explicit, absolute, hash-pinned `.blend` Mesh; the
validated provider is Blender Studio Human Base Meshes v1.4.1 (`CC0-1.0`). The asset is not
vendored or required, and native v1/v3 creation remains available without it. ReQuad and
QuadriFlow remain rejected as automatic production retopology providers for this workflow.

## Current safety status

The v2 validator refuses `VOXEL_CONNECTED` after
whole-body voxel remeshing connected spatially close but semantically separate leg/foot geometry
in the live candidate. Its implementation remains only as rejected historical code until it is
removed; do not bypass the validator or route that output downstream.

Schema v3 `BOOLEAN_CONNECTED` unions only deliberately overlapping semantic volumes and rejects
results that are not one manifold component, lose foot/lower-leg centerline clearance, or create
cross-side edges below the knee. It also refuses a result that retains a Blender QuadriFlow
preflight micro-edge after bounded cleanup. It remains a blockout candidate after live
multi-angle review; the Boolean surface is not deformation-ready topology.

Create a visible humanoid modeling base in a dedicated character Workbench Scene. The result is
one Mesh Object and four material slots. V1 and v2 `VOLUME_ISLANDS` preserve separate volumes.
V3 `BOOLEAN_CONNECTED` creates a single closed surface while preserving bilateral clearance. V4
`DEFORMATION_TEMPLATE` duplicates the named source Mesh, applies a bounded smooth regional
proportion warp without changing connectivity or UV loops, assigns the requested material roles
and records source/version/license/hash provenance.

V5 keeps the same explicit CC0 template boundary and adds art-direction provenance plus bounded
head/torso/arm/leg/hand/foot controls. It stores six point-domain semantic weight attributes,
applies actual coordinate changes, checks a declared triangle budget, and records what Blender
actually applied separately from unsupported style requests. Revision v1 accepts only an unrigged
owned v5 source and creates a new Collection/Object/Mesh. It shares Materials read-only while
preserving topology, active UV coordinates and vertices outside the adjusted semantic regions.
These controls do not redesign the inherited face/head topology or create actual hair/clothing.
The 2026-11-04 SD representative passed technical checks but was explicitly rejected by the user
as a character-art direction; never use it as a default or as B6.2 visual approval.

## Workflow

1. Inspect the target Scene and requested output names.
2. Translate the character brief into one complete
   `gameassetai.character-base-request.v1`, `.v3`, `.v4` or `.v5` request. Use v4/v5 only with a reviewed
   local CC0 template path, exact Mesh name and SHA-256.
3. Review height, body ratios, A/T pose and colors before persistent creation.
4. Validate with `scripts/validate_character_base_request.py`.
5. After explicit creation authorization, run `scripts/create_character_base.py` in Blender.
6. Make the Workbench Scene active and show front, three-quarter and side views.
7. Record technical validation separately from the user's art-direction decision. If style is not
   approved, stop before hair/clothing production, rig/animation/export or default-preset claims.
8. Keep only the current review candidate visible. Modify or replace that candidate after review;
   do not accumulate every iteration and do not delete the candidate immediately after showing it.

For a later request such as “make the head slightly larger, shorten the arms and enlarge hands and
feet”, use `gameassetai.character-base-revision-request.v1`. Require the exact owned v5 Collection
and Object, unused result names and explicit regional multipliers. Refuse a rigged source,
modifiers, vertex groups, Shape Keys, arbitrary imported topology and material/texture revision.

## Preservation

- Create a new Collection, one Object, one Mesh and four Materials.
- Refuse every occupied requested name.
- Preserve existing Scenes and data.
- Tag created data with one owner token and roll back only matching data on failure.
- Record `-Y` as the character's canonical front axis; feet, torso-facing controls and later
  animation must use the same convention.
- V4 refuses a symlink, missing/wrong hash, missing Mesh, Shape Keys or external Material
  dependencies and rolls back only data appended or created by that request.
- V5 uses the same source rules. Revision copies mutable Mesh data before editing, never changes the
  source, and refuses occupied result names. Materials remain shared read-only.
- Test fixtures are disposable; user-review candidates remain until accepted, replaced or
  explicitly discarded.

## Validation and completion

- Focused Blender tests cover authorization refusal, requested names, material roles, component
  and manifold checks, bilateral clearance, bounded Boolean micro-edge cleanup, suspended voxel
  refusal, rollback and restoration.
- A representative v3 blockout has passed agent multi-view review, so the strongest current
  evidence for the bounded blockout responsibility is `representative`, not `accepted`.
- V4 was exercised on compact and lanky non-affine proportions in Blender 5.0.1: both retained
  one closed all-quad 12,500-face component and a complete 50,000-loop UV map, preserved the
  source hash, rolled back a bad-hash request exactly, saved/reopened, and deformed under an
  Armature probe. Visual review found usable topology continuity but severe local compression in
  the lanky knee and limitations in the blockout-oriented rig/weights. V4 therefore remains an
  explicit experimental provider, not accepted `deformation-ready` product output.
- V5 was exercised on an SD-proportioned A-pose base and an independent larger-head,
  shorter-arm, larger-hand/foot revision. Both retained the 12,502-vertex/12,500-quad topology,
  complete UVs and source hash; injected creation/revision failures rolled back; six common-camera
  views and fresh-process reopen passed. The revised base also passed the bounded M2 v3 explicit-
  landmark shoulder/elbow/hip/knee gate. This is representative technical evidence only. User
  review rejected the resulting face, empty-looking eye area, painted-on clothing, missing hair
  and inconsistent body style, so no Character v5 output is an approved default art direction.

## Boundary

This Skill creates either a proportioned low-poly blockout or an explicit template-derived base.
It does not create an Armature or weights. V4/v5 preserve template UVs and edge flow but do not
certify arbitrary proportions, layered clothing/hair, facial features/rigging, creatures, Mixamo
compatibility or production deformation quality.
The generated-fixture rig must not be treated as a general template-rig adapter.
