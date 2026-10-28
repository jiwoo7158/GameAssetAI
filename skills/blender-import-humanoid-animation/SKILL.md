---
name: blender-import-humanoid-animation
description: Import one explicit hash-pinned Humanoid FBX, verify an exact Mixamo-style mapping, retarget one Action into pose space for an explicit compatible target rig, and bind a new independent Action. Use for a reviewed M2 A-pose target and one bounded animation; do not use for web upload, mapping guesses, arbitrary rigs, facial animation, NLA editing, or Unity export.
metadata:
  contract: gameassetai.skill-contract.v1
  requirements: REQ-CHAR, REQ-ANIM, REQ-SAFE
  evidence: accepted
  external-dependencies: none
---

# Blender Import Humanoid Animation

## Requirements and responsibility

Import one local FBX into an owned collection, validate its exact source mapping with the existing
Humanoid/Mixamo inspectors, sample one explicit frame range, create one independent target Action,
and bind it only to an animation-empty target Armature. Preserve the imported source Action and
all target Mesh coordinates, UVs, Armature rest data and existing files.

Use `scripts/validate_humanoid_animation_import_request.py`, then call
`scripts/import_humanoid_animation.py` only after explicit authorization. The implementation
loads `inspect_humanoid.py` and `inspect_mixamo_preflight.py` from their installed sibling Skills
(or the matching repository Skill layout) rather than duplicating them.

## Implementation basis and dependencies

The workflow uses Blender's built-in FBX importer/exporter, Blender Action/pose APIs, the existing
GameAssetAI Humanoid and Mixamo inspectors, and project-owned pose-space sampling. It adds no
external Python package or web dependency. Adobe login/upload/download is deliberately outside
the Skill and always remains a user-controlled external action.

## Workflow

1. Require the exact unused output names, local FBX path/hash, explicit source/target mappings,
   frame/FPS range and root-motion policy.
2. Validate the target rig/mesh and empty animation state, then import into a temporary Scene.
3. Run the existing exact Mixamo preflight and Humanoid mapping checks.
4. Sample evaluated source poses, bake the independent target Action and bind it to the empty rig.
5. Verify target deformation, preservation and provenance before saving a new `.blend` checkpoint.

## Supported input

- one absolute, regular, non-symbolic `.fbx` file with exact lowercase SHA-256;
- exactly one imported Armature and one bound Action, optionally checked against expected names;
- complete explicit source and target mappings for the 17 supported humanoid roles;
- one local M2-compatible target Armature, one bound Mesh and empty target animation state;
- integer inclusive frame range, step 1, explicit FPS;
- `IN_PLACE` or explicit scaled/masked `TRANSFER` hips translation.

The rotation bake collapses each Source role to its nearest mapped ancestor, so optional Mixamo
`Spine1` and shoulder motion reaches the mapped chest/upper-arm exactly once. It maps the evaluated
Source bone direction to the Target, preserves Target rest roll, transfers Source local-Y twist,
and uses `Bone.convert_local_to_pose()` with the actual Target parent pose/rest matrices before
keying quaternion rotation. This handles Source/Target rest-pose and Bone Roll differences without
editing either rest rig. It is not a stored local-Euler name copy or global rest-delta copy.

Unmapped animated Source bones are reported. Finger/toe motion is not represented by the current
18-bone Target, while mapped descendants retain the relevant parent-chain direction. Time-varying
Armature-object channels, unsupported non-bone channels and non-unit mapped scale channels are
refused; constant FBX axis-conversion channels and unit scale bakes are accepted. `IN_PLACE` has
representative acceptance; `TRANSFER` root motion remains implemented but not service-approved.

## Preservation

FBX import runs first in a temporary Scene. On success, imported source data moves into one owned
Collection in the target Scene, the source Action remains bound to its source Armature, and one
new protected target Action is bound to the previously empty target. On failure, remove only the
newly imported datablocks, Collection and result Action and restore target binding, frame and
selection. Never overwrite a file or replace existing animation.

## Validation and completion

Completion requires an imported Armature/Action, complete explicit mappings, actual target Mesh
movement over the requested frames, preserved source/target data, rollback after a forced
mid-operation failure, saved-file reopen, multi-frame visual review and installed-source hash
alignment. Automatic structure/motion checks and explicit visual acceptance are recorded
separately.

`scripts/export_mixamo_handoff.py` is a separate bounded helper in this Skill for a new, explicit
FBX handoff file containing only one target Mesh and Armature. It does not upload anything and is
not the Unity export workflow.

## Boundary

The synthetic Mixamo-signature regression still proves rollback and bounded mechanics. A real
Adobe Mixamo Walking FBX also passed import, exact mapping, 32-frame direction/clearance checks,
Source/Target preservation, save/reopen and explicit Front/Side/Three-quarter visual acceptance
on the M2 Compact character. This acceptance is limited to the documented 17-role M2-compatible
rig and `IN_PLACE`; it does not certify arbitrary rigs, facial/finger animation or root transfer.
