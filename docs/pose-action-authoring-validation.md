# Pose Action authoring validation — 2026-10-25

`blender-author-pose-action` creates one new Blender 5 layered pose Action from explicit complete
per-frame XYZ rotations. Schema v2 additionally accepts an explicit, complete set of local bone
location triples for reviewed root/pelvis correction. It requires an empty Armature animation
state and an explicit front axis.

The focused Blender 5.0.1 fixture passes nine checks: mismatched rig/request front axes are refused,
the correct request creates and binds one Action, two bones produce six F-Curves and eighteen
keys, `-Y` provenance is retained, v2 creates verified root-location channels, and all fixture
data is removed.

The live `GAA Scout Ready Loop` v4 motivated this guard. Evaluated v3 hands moved toward `+Y`
while both feet defined forward as `-Y`. V4 reverses the arm rotations; evaluated hand and foot
tails are all in the `-Y` hemisphere at frames 12 and 24, confirmed again in right-side views.

The installed Skill then authored `GAA Scout Walk Loop` without replacing the preserved Ready
Loop. Walk v1 contains 24 F-Curves and 120 keys over frames 1–25 at 12 FPS. Front and right-side
strips at frames 1/7/13/19/25 confirm alternating contact and passing poses, consistent `-Y`
forward motion and a matching loop endpoint. The result is saved at
`D:/Blender/MCP_Test/GameAssetAI_Character_Workbench_Walk_v1.blend`.

Walk v2 preserves Walk v1 and Ready Loop as separate Actions, adds a reviewed root local-Y height
curve (the rig's root local Y maps to world Z), and keeps all 25 sampled mesh minima above
`-0.001m`. Front and right-side strips over nine frames show no shoulder, elbow, hip or knee tear
requiring a weight rewrite. The result is saved without replacing the interactive file at
`D:/Blender/MCP_Test/GameAssetAI_Character_Workbench_Walk_v2.blend` (SHA-256
`a3d7fc6d40d0e53e62ccd052fd572833ada246525ec54219aa7b9ca364cb169b`).

User playback review found that Walk v2 read as backward locomotion and that reverse playback read
as forward. `GAA Scout Walk Forward Loop` therefore preserves the v2 poses and root-height curve
but maps target time as `26 - source frame`. The original Ready, Walk v1 and Walk v2 Actions remain
available. The corrected Action retains `-Y` front provenance, 27 F-Curves, 243 keys, matching
frames 1/25 and less than 1mm sampled ground penetration. The live Add-on selector now points to
this Action. Checkpoint:
`D:/Blender/MCP_Test/GameAssetAI_Character_Workbench_WalkForward_v1.blend` (SHA-256
`11990d18cc7be0d05560d1fbdda34054ecc049f00d10350aabf21d1217a93199`).
