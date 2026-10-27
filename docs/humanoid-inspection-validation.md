# Humanoid inspection validation — 2026-09-22

`blender-inspect-humanoid` is a read-only Armature inspection Skill intended to precede
Mixamo preparation, retargeting and Unity Humanoid work. It accepts an explicit canonical
role-to-bone mapping; absent mappings remain incomplete instead of guessing from names.

The Blender 5.0.1 synthetic fixture created a separate owned Scene and 16-role Armature,
then passed 11 checks: complete mapping, ancestor hierarchy, JSON/read-only behavior,
no-name-guessing, missing bone, duplicate-bone refusal, inconsistent hierarchy,
non-deform review, animation sensitivity, Edit Mode refusal and exact original-state
restoration. The fixture Armature/Object/Action/Scene were removed. The original Scene
remained Cube/Light/Camera with one material.

Repository-source, packaged-ZIP and exact installed-Workspace helper runs each passed the
same 11 checks with exact teardown. The humanoid ZIP SHA-256 is
`3139659171020e101f72ec73767d9dae1a8e3f73674cda760bba2f91bf94d00e`.
No-overwrite deployment added only
`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-inspect-humanoid`; source and installed
bytes align. Skill Creator's optional quick validator could not run because host Python
lacks PyYAML, so no dependency was installed. Repository validation supplies the
applicable structural check.

`ok` is deliberately narrow: mapped bones exist and satisfy the bounded ancestry rules.
Multiple roots, non-deform mapped bones and existing animation are review findings because
export policy is Profile-specific. The result does not certify pose, bone axes, skin
weights, twist bones, Mixamo upload/retarget quality, Unity Avatar validity or export.

The refreshed client subsequently exposed the Skill automatically. Because the current
Scene contained only Cube/Light/Camera, it correctly performed no humanoid call, guessed
no mapping and made no Blender change. This closes discovery and missing-target refusal.
The remaining independent host gate is an explicit-mapping read-only call on a disposable
or known rig.
No production Armature must be altered to test this Skill.
