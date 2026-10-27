---
name: blender-import-humanoid-animation
description: Import one explicit hash-pinned Humanoid FBX, verify an exact Mixamo-style mapping, retarget one Action into pose space for an explicit compatible target rig, and bind a new independent Action. Use for a reviewed M2 A-pose target and one bounded animation; do not use for web upload, mapping guesses, arbitrary rigs, facial animation, NLA editing, or Unity export.
metadata:
  contract: gameassetai.skill-contract.v1
  requirements: REQ-CHAR, REQ-ANIM, REQ-SAFE
  evidence: tested
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

The rotation bake samples evaluated source pose matrices and converts each mapped armature-space
rest delta onto the target rest orientation before keying target quaternion rotation. It is not a
stored local-Euler name copy. Unmapped animated source bones are reported; mapped descendants still
include their evaluated parent motion. Time-varying Armature-object channels, unsupported non-bone
channels and non-unit mapped scale channels are refused; constant FBX axis-conversion channels and
unit scale bakes are accepted.

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
alignment. Synthetic FBX evidence is labeled local validation, not Mixamo service proof.

`scripts/export_mixamo_handoff.py` is a separate bounded helper in this Skill for a new, explicit
FBX handoff file containing only one target Mesh and Armature. It does not upload anything and is
not the Unity export workflow.

## Boundary

The local synthetic Mixamo-signature FBX regression proves import, mapping, pose-space sampling,
target deformation, rollback, save/reopen and installed-Skill execution. It is not an Adobe
Mixamo service round trip. Do not call Mixamo integration complete until a real downloaded Mixamo
FBX passes the same workflow and visible review.
