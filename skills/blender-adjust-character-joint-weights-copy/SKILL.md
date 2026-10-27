---
name: blender-adjust-character-joint-weights-copy
description: Preview and create an independent character Mesh copy with an explicit shoulder or hip weight-transition adjustment while preserving the source and sharing its verified owned Armature. Use for guarded joint-weight refinement of GameAssetAI-generated characters; do not use for arbitrary rigs, topology edits, automatic weight quality claims, or source overwrite.
---

# Blender Adjust Character Joint Weights Copy

## Current safety status

This Skill is retained as an experimental copy/preservation backend and is suspended from the
default character route. Its first live source had rejected voxel-connected topology; improved
weight metrics did not detect fused/bridged legs or feet. Do not use it to continue that candidate.

Before applying to a future source, require explicit topology acceptance covering bilateral limb
clearance, intended connectivity, self-intersection and front/side/three-quarter silhouette. A
weight metric cannot override a failed geometry review.

Refine one explicit shoulder or hip transition on an independent Object/Mesh copy. The source
character, geometry, materials and Armature remain unchanged.

## Workflow

1. Identify the exact Scene, owned character Mesh and its owned Armature.
2. Build the complete `gameassetai.character-joint-weight-copy-request.v1` request accepted by
   `scripts/validate_character_joint_weight_copy_request.py`.
3. Run `preview_character_joint_weight_copy.py`. Review affected vertex count and the maximum
   target-pair weight delta across neighboring affected vertices before and after the proposal.
4. Apply only after approval using the four exact preview fingerprints and `authorized=true`.
5. Show the output in a real shoulder/hip pose before treating it as the current candidate.

The adjustment is explicit: `SHOULDER` or `HIP`, `LEFT`, `RIGHT` or `BOTH`, and a transition width
ratio from `0.01` through `0.08` of character height. It redistributes only the selected adjacent
bone-pair's existing total weight using a smooth transition; every other weight is preserved.

## Boundary

Only owned `blender-create-character-base` meshes with one verified owned Armature modifier are
supported. The output is a new Object and Mesh sharing the existing Armature and material data.
This metric detects abrupt pair-weight changes; it does not certify volume preservation,
silhouette, self-intersection, animation quality, Mixamo compatibility or production skinning.
