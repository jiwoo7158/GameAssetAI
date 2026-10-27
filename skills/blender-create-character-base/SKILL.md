---
name: blender-create-character-base
description: Create a stylized humanoid base Mesh from explicit proportions and colors. Use native VOLUME_ISLANDS or guarded v3 BOOLEAN_CONNECTED for blockouts, or explicitly opt into experimental v4 DEFORMATION_TEMPLATE with a hash-pinned CC0 Blender Studio Human Base Mesh source. The rejected VOXEL_CONNECTED path remains suspended.
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

## Workflow

1. Inspect the target Scene and requested output names.
2. Translate the character brief into one complete
   `gameassetai.character-base-request.v1`, `.v3` or `.v4` request. Use v4 only with a reviewed
   local CC0 template path, exact Mesh name and SHA-256.
3. Review height, body ratios, A/T pose and colors before persistent creation.
4. Validate with `scripts/validate_character_base_request.py`.
5. After explicit creation authorization, run `scripts/create_character_base.py` in Blender.
6. Make the Workbench Scene active and show front, three-quarter and side views.
7. Keep only the current review candidate visible. Modify or replace that candidate after review;
   do not accumulate every iteration and do not delete the candidate immediately after showing it.

## Preservation

- Create a new Collection, one Object, one Mesh and four Materials.
- Refuse every occupied requested name.
- Preserve existing Scenes and data.
- Tag created data with one owner token and roll back only matching data on failure.
- Record `-Y` as the character's canonical front axis; feet, torso-facing controls and later
  animation must use the same convention.
- V4 refuses a symlink, missing/wrong hash, missing Mesh, Shape Keys or external Material
  dependencies and rolls back only data appended or created by that request.
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

## Boundary

This Skill creates either a proportioned low-poly blockout or an explicit template-derived base.
It does not create an Armature or weights. V4 preserves template UVs and edge flow but does not
certify arbitrary proportions, production skinning, Mixamo compatibility or deformation quality.
The generated-fixture rig must not be treated as a general template-rig adapter.
