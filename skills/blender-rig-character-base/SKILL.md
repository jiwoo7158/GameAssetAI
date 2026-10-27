---
name: blender-rig-character-base
description: Create and weight an 18-bone humanoid Armature for an owned GameAssetAI blockout or an explicit compatible A-pose Mesh. Use v1/v2 for generated blockouts, or v3 with reviewed object-local joint landmarks for rig fitting and bounded envelope weights. Do not use for automatic landmark guessing, replacing an existing rig, facial rigs, IK controls, animation, or Mixamo upload.
---

# Blender Rig Character Base

Add the first deformable humanoid skeleton to a reviewed character candidate. V1/v2 remain
coupled to `blender-create-character-base` metadata. V3 accepts a local explicit Humanoid Mesh
only when the caller supplies the complete reviewed A-pose landmark map; it never guesses joints.

Do not rig a candidate merely because it is owned or has one closed component. Require recorded
multi-view acceptance and no known unintended limb/foot bridge. The current
`VOXEL_CONNECTED` character experiment is rejected and must not be used as a rig target. The v3
Boolean-connected Mesh remains a blockout and is not a v3 target merely because it is owned.

## Workflow

1. Confirm the exact Workbench Scene and current character Mesh Object.
2. For v1/v2, refuse targets not owned by the character-base workflow. For v3, require one local,
   non-empty Object-mode Mesh with no existing modifier, vertex group, Shape Key or animation.
3. Build a complete `gameassetai.character-rig-request.v1`, `.v2` or `.v3` request with unused
   Armature names. V3 requires object-local root/pelvis/spine/chest/neck/head-top plus bilateral
   shoulder/elbow/wrist/hand-tip and hip/knee/ankle/toe landmarks.
4. Review the 18-bone hierarchy, `-Y` front convention and landmark placement before creation.
5. After explicit authorization, run `scripts/rig_character_base.py`.
6. Show the Armature over the same visible Mesh and verify vertex-group coverage.
7. Keep this current rigged candidate for pose/deformation review; do not immediately remove it.

## Output

- root, pelvis, spine, chest, neck and head bones;
- paired upper-arm, forearm and hand bones;
- paired thigh, shin and foot bones;
- 17 matching deform vertex groups covering every vertex;
- v1 rigid region assignment or v2 smooth two-bone transition bands at major joints;
- v3 fitted bones plus normalized landmark-envelope weights with at most four influences,
  no opposite-side limb influence and an explicit transition-width ratio;
- one Armature modifier bound to the new Armature;
- request, landmark and receipt hashes, source geometry/UV fingerprints and weight diagnostics.

The generated character's canonical front is `-Y`. Any authored pose must verify that evaluated
hands and feet move toward the same front hemisphere instead of relying on local Euler signs.

## Boundary

V3 supports reviewed single-body A-pose humanoids whose joints can be expressed by the exact
landmark contract. It preserves vertex coordinates and the active UV layer, refuses existing rigs
instead of replacing them, and rolls back its Armature, modifier and groups after a failure.
It is not landmark detection, automatic weighting for arbitrary clothing/hair, twist-bone or
corrective-shape support, facial rigging, or Mixamo certification. Compact and lanky v4 template
characters passed saved/reopened shoulder, elbow, hip and knee probes; the next gate is a real
Mixamo round trip, not a claim that all humanoids are supported.
