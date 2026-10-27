# Mixamo preparation preflight — 2026-09-22

`blender-inspect-mixamo-preflight` is a read-only prerequisite for later Mixamo import,
retarget and Unity Humanoid work. It recognizes one complete exact Mixamo suffix signature,
derives an explicit canonical mapping, reuses the bounded humanoid hierarchy inspection,
and reviews bound Mesh vertex groups, Armature Object transform and existing animation.

Repository-source, packaged-ZIP and exact installed-Workspace helper runs each passed the
same eight Blender 5.0.1 checks: signature detection, humanoid mapping, bound Mesh groups,
missing-group review, non-identity transform review, wrong-prefix incomplete result,
Edit Mode refusal and exact original-state restoration. Synthetic Scene/Object/Mesh/
Armature IDs were removed; the original Cube/Light/Camera Scene remained unchanged.

The ZIP SHA-256 is
`9a42ec2d372221b36ae78ec324ae27e47bbcea392cfb1065d32224022b6c97c3`.
No-overwrite deployment added only
`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-inspect-mixamo-preflight`; source and
installed bytes align. Client discovery is not yet verified.

The exact suffix set is a narrow deterministic signature, not fuzzy mapping. `ok` does
not certify T/A pose, bone axes, skin quality, facial/twist bones, root motion, Mixamo
upload acceptance, retarget quality, Unity Avatar creation or export. No rig data is
modified, uploaded or sent to an external account.
