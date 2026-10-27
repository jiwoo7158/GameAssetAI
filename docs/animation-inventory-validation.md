# Animation inventory Skill — 2026-09-23

`blender-inspect-animation` is a read-only inventory for existing Blender Actions,
current Action/slot bindings, drivers, NLA tracks/strips and stored F-Curve/keyframe
channels. It accepts explicit root bone names; it does not infer a root from names or
evaluate/change the current frame. The development helper remains byte-identical to the
packaged helper.

An owned Blender 5.0.1 synthetic Armature/Action fixture passed 11 checks from repository
source, the portable ZIP and the installed personal-Workspace helper. In addition to
Action/curve/key/binding coverage, the fixture proves NLA strip inventory, one driver
count and visibility of an unused zero-user Action. Explicit root-motion channels, no
root guessing, invalid-root refusal, JSON/frame preservation and exact teardown also
pass. Test Scenes, Objects, Armatures and Actions were removed; Cube/Light/Camera remained
unchanged.

The Skill was installed without overwrite at
`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-inspect-animation`; all ten repository
Skills and installed copies are byte-aligned. The portable Skill ZIP SHA-256 is
`30f93ff4fa2ff78596ec8ef10493508352a430920310df4c0a782c2aef484085`.
Client discovery remains unverified until a refreshed session exposes the new catalog.

This Skill does not import FBX/BVH, extract or rename Actions, judge loop continuity,
evaluate poses, retarget, edit curves or certify root motion for a game. Those are later
steps that should consume this stored-data inventory and explicit Workspace Profile or
mapping rules.
