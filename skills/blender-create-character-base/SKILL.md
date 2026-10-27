---
name: blender-create-character-base
description: Create one new stylized low-poly humanoid blockout Mesh in Blender from explicit proportions, A-pose or T-pose and four opaque material colors. Use VOLUME_ISLANDS for separated blockout work or v3 BOOLEAN_CONNECTED for a guarded semantically joined candidate. The rejected VOXEL_CONNECTED path remains suspended.
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

The implemented path uses Blender BMesh primitives, Blender's exact Boolean modifier and
project-owned validators. Its Boolean result removes only confirmed sub-`1e-4` sliver edges that
Blender 5.0 QuadriFlow rejects, then rechecks the result; this is source cleanup, not automatic
retopology. It has no external runtime dependency. ReQuad, native QuadriFlow and RetopoFlow are
research candidates for the planned deformation-topology stage, not installed or approved
dependencies and not evidence that the stage exists.

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
V3 `BOOLEAN_CONNECTED` creates a single closed surface while preserving bilateral clearance. It
is an input to later modeling and rigging work, not a finished character.

## Workflow

1. Inspect the target Scene and requested output names.
2. Translate the character brief into one complete
   `gameassetai.character-base-request.v1` or `.v3` request.
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
- Test fixtures are disposable; user-review candidates remain until accepted, replaced or
  explicitly discarded.

## Validation and completion

- Focused Blender tests cover authorization refusal, requested names, material roles, component
  and manifold checks, bilateral clearance, bounded Boolean micro-edge cleanup, suspended voxel
  refusal, rollback and restoration.
- A representative v3 blockout has passed agent multi-view review, so the strongest current
  evidence for the bounded blockout responsibility is `representative`, not `accepted`.
- Completion of this Skill's current blockout responsibility does not certify UVs, joint edge
  flow, skinning or deformation. The planned deformation-topology extension requires its own
  representative pose and visual acceptance gates before the evidence metadata may advance.

## Boundary

This Skill creates a proportioned low-poly base with semantic body volumes. It does not create an
Armature, UV layout, production edge flow or deformation readiness. Rig creation, weight
assignment and animation are separate workflows and must not product-route the current Boolean
surface until a deformation-topology/revision gate has passed.
