---
name: blender-create-game-asset
description: Route a natural-language Blender game-asset request into the existing static creation, character base, rig, imported-humanoid animation, game-Action preparation, inspection, revision and optional 2D/Unity FBX export Skills. Use when the user asks to create or continue a character, weapon, prop, enemy or environment asset and has not named a narrower Skill. This router coordinates reviewed stages; it does not replace their scripts or claim unsupported general modeling, Mixamo web automation or broad multi-rig export.
---

# Blender Create Game Asset

Turn one asset request into a staged Blender workflow using the smallest applicable existing
Skill. Read [references/pipeline.md](references/pipeline.md) to select the route. Do not reproduce
another Skill's schema or implementation inside this router.

Inspect the connected Blender Scene and decide first whether the request is new creation or work
on an existing asset. Preserve existing objects, rigs and Actions unless replacement is explicit.

Use these creation entries:

- recognizable low-poly prop, weapon, furniture-like or simple environment assembly, including
  an explicit profile-authored silhouette, a bounded matched-profile beveled solid, and owned
  semantic geometry revision, plus bounded revision of an explicitly mapped static external GLB:
  `blender-create-static-asset`;
- new low-poly humanoid blockout: `blender-create-character-base`;
- reviewed owned character base that needs its first rig: `blender-rig-character-base`;
- explicit hash-pinned Mixamo-style FBX Action for an empty compatible Humanoid rig:
  `blender-import-humanoid-animation`;
- explicit range/FPS cleanup of an imported or existing Armature Action into a new independent
  game clip: `blender-prepare-game-action`;
- reviewed single-Mesh/single-Armature Action for Unity Generic FBX:
  `blender-export-animated-fbx`;
- explicit reviewed key poses on a suitable empty Armature: `blender-author-pose-action`.

For characters, use `VOLUME_ISLANDS` for separated blockouts or guarded v3
`BOOLEAN_CONNECTED` for the current connected candidate. Never route the rejected global
`VOXEL_CONNECTED` mode. Do not route from structural or visual success directly to product
rigging: v3 is still Boolean blockout topology and must pass an explicit deformation-topology,
UV and pose-deformation gate first.

For an existing asset, inspect before choosing a modification Skill. Use the animation
copy/range/retarget/bake Skills only for their documented narrow inputs; do not treat them as a
general animation generator. Collider, LOD, masks, render passes and Unity checks are optional
downstream work, never substitutes for creating the requested asset.

For requests such as "apply this imported Mixamo walk", require only the missing absolute FBX
path/hash, exact target Mesh/Armature, explicit source/target role mappings, frame range/FPS and
root-motion policy. Route the complete request through `blender-import-humanoid-animation`; do
not ask the user to invoke its internal inspection and Action helpers one by one. The Skill does
not upload to, log into or download from Adobe Mixamo.

For requests such as "cut frames 1-24 into a separate Action starting at frame 1", inspect the
exact Armature, Action/slot, range, source/target FPS and root bone. Use strict
`blender-extract-action-range` when its exact-boundary LINEAR contract accepts the Action;
otherwise route once through `blender-prepare-game-action`. Do not silently repair a loop, convert
root motion, bind/replace the current Action or edit NLA.

For requests such as "export this character and Walking Clip for Unity", require the exact Scene,
Mesh, Armature, Action/slot, inclusive range/FPS, new `.fbx` target, Unity axis/unit policy,
non-loop policy and `IN_PLACE` root-motion policy. Route once through
`blender-export-animated-fbx`; it selects the named Action on an owned temporary rig even when the
source Action is unbound. Do not substitute the current bound Action or route the rig through the
static exporter.

Keep one visible current candidate and recoverable checkpoints. Do not accumulate every failed
revision in the Scene. Continue through multiple stages when the user's request already covers
them, but validate each stage before using it as the next stage's input.

Only offer 2D Pixel/Cel/Toon rendering after the 3D source is reviewable. Never route a rigged
character through the static-only FBX exporter. Animated FBX v1 is limited to the explicit
single-Mesh/single-Armature/single-Action Unity Generic contract; Humanoid Avatar certification,
loop repair, root-motion conversion and Animator Controller authoring remain separate gaps.

For requests such as "make a stylized low-poly axe and thin its cutting edge" or "make a chamfered
supply crate and deepen its panel", route one complete v4 request through
`blender-create-static-asset` when matching outer/core profiles can represent the requested solid.
Use v3 when constant-depth profile extrusion is sufficient. Translate a complete explicit request
or active-profile style decision into the style object; do not infer missing art direction.
Geometry revision is supported only for an owned matching-version semantic part and must create an
independent collection.

For requests such as "extend the handle in this existing GLB" or "modify only this mapped metal
part", inspect the actual file first and require its absolute path/SHA-256, provenance, a complete
unique Mesh Object-to-role map, unused source/result Collection names, and an explicit local-axis
end region (`axis`, `side`, `threshold`, `delta`). Route the request through
`blender-create-static-asset` external-revision v1. It creates independent result Meshes and shares
materials read-only. Do not infer roles, treat the imported source as a native-owned assembly, or
claim `.blend`, modifier, Shape Key, vertex-group, topology, arbitrary-selection, material or UV
editing support. Unsupported external structures must be refused rather than rebuilt from primitives.
