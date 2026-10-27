---
name: blender-rig-character-base
description: Create and region-weight an explicit humanoid Armature for one owned GameAssetAI character-base Mesh. Use after the visible base character has been reviewed and has no existing rig, modifiers, or vertex groups. Do not use for arbitrary production topology, automatic Mixamo upload, facial rigs, IK controls, animation, or replacing an existing Armature.
---

# Blender Rig Character Base

Add the first deformable humanoid skeleton to the current reviewed character candidate. This
Skill is intentionally coupled to `blender-create-character-base` metadata so it cannot claim
safe automatic rigging for unrelated meshes.

Do not rig a candidate merely because it is owned or has one closed component. Require recorded
multi-view acceptance and no known unintended limb/foot bridge. The current
`VOXEL_CONNECTED` character experiment is rejected and must not be used as a rig target. The v3
Boolean-connected Mesh is also only a blockout until a separate deformation-topology gate exists;
do not use this Skill to promote it as production-ready.

## Workflow

1. Confirm the exact Workbench Scene and current character Mesh Object.
2. Refuse targets not owned by the character-base workflow or targets with existing modifiers or
   vertex groups.
3. Build a complete `gameassetai.character-rig-request.v1` request with unused Armature names.
4. Review the 18-bone hierarchy and region-weighting boundary before persistent creation.
5. After explicit authorization, run `scripts/rig_character_base.py`.
6. Show the Armature over the same visible Mesh and verify vertex-group coverage.
7. Keep this current rigged candidate for pose/deformation review; do not immediately remove it.

## Output

- root, pelvis, spine, chest, neck and head bones;
- paired upper-arm, forearm and hand bones;
- paired thigh, shin and foot bones;
- 17 matching deform vertex groups covering every vertex;
- v1 rigid region assignment or v2 smooth two-bone transition bands at major joints;
- one Armature modifier bound to the new Armature;
- request and receipt hashes.

The generated character's canonical front is `-Y`. Any authored pose must verify that evaluated
hands and feet move toward the same front hemisphere instead of relying on local Euler signs.

## Boundary

V2 linear joint blending is a deterministic improvement for the generated connected body, but it
is not heat weighting, production skinning, twist-bone support or deformation quality
certification. Pose real bones and inspect shoulders, elbows, hips and knees before animation.
