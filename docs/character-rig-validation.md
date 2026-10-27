# Character rig validation — 2026-10-25

`blender-rig-character-base` adds an 18-bone humanoid Armature, 17 deform groups and one Armature
modifier to the owned character-base Mesh without changing its geometry. Schema v1 retains rigid
region assignment. Schema v2 uses normalized smooth transition bands between adjacent bones at
the spine, neck, shoulders, elbows, wrists, hips, knees and ankles.

The rig mechanics remain tested, but the later connected live candidate is rejected because its
input topology visibly fused/bridged leg or foot geometry. Do not treat successful binding, full
weight coverage or pose execution on that candidate as product rig evidence.

The Blender 5.0.1 fixture passes 13 focused checks across both modes, covering authorization
refusal, exact bone count, Armature creation, full vertex coverage, normalized v2 multi-bone
weights, geometry preservation, receipt hashing, exact rig removal and complete character
cleanup. Blender 5 modifiers do not support arbitrary ID
properties, so modifier ownership is verified through the owned Armature token, exact modifier
name/type and exact Armature Object reference.

The connected live candidate uses v2 weights: 1,206 of 3,738 vertices have two influences and
every vertex weight sum is approximately 1.0. A six-limb-bone pose was reviewed from front, side
and three-quarter views, then restored to rest pose. This establishes a real skeleton and improved
first-pass weights. Targeted shoulder/hip editing, quantitative deformation checks, IK/control
rigs, animation, Mixamo compatibility and Unity Humanoid mapping remain separate gates.

Latest recovery copy:
`D:/Blender/MCP_Test/GameAssetAI_Character_Connected_BlendedWeights_v2.blend` (272,885 bytes,
SHA-256 `b3f890ec33a529c7a5fde46df1f729ff5423e09f676a5ddcc15c80a7d6d8690b`). The portable Skill
bundle is `.local/source-bundles/blender-rig-character-base-v2.zip` (5,382 bytes, SHA-256
`5d82a81a0cf7323f1b3d00081d5f6b472fa6018cc98f956efafed8061b53e57a`).

The installed Skill was then applied to the retained `GAA Scout Current` candidate in
`GameAssetAI_Character_Workbench`. It created 18 bones, 17 deform groups, weighted all 318
vertices and added one Armature modifier. A six-bone deformation-review pose was inspected from
front, three-quarter and side views. The character, rig, owned camera and lights remain in the
active Workbench Scene for the next weight/animation stage; they were deliberately not cleaned up.

The visible state was also saved as a new, non-overwriting recovery copy at
`D:/Blender/MCP_Test/GameAssetAI_Character_Workbench.blend`. Saving used Blender's copy mode, so
the interactive `MCPTest.blend` path was not replaced.

The retained rig now drives the first real authored Action, `GAA Scout Ready Loop`. User review
found the original upper/lower motion relationship incorrect. The final v3 keeps the lower body
stable and animates seven upper-body bones over 36 frames at 12 FPS with 21 layered-Action
F-Curves and 84 keys. Front and side frame strips were inspected and frames 1/36 match. The
corrected state is preserved at
`D:/Blender/MCP_Test/GameAssetAI_Character_Workbench_ReadyLoop_v3.blend`.
