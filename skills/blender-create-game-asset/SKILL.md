---
name: blender-create-game-asset
description: Route a natural-language Blender game-asset request into the existing static creation, character base, rig, imported-humanoid animation, game-Action preparation, inspection, revision and optional 2D/export Skills. Use when the user asks to create or continue a character, weapon, prop, enemy or environment asset and has not named a narrower Skill. This router coordinates reviewed stages; it does not replace their scripts or claim unsupported general modeling, Mixamo web automation or rigged export.
---

# Blender Create Game Asset

Turn one asset request into a staged Blender workflow using the smallest applicable existing
Skill. Read [references/pipeline.md](references/pipeline.md) to select the route. Do not reproduce
another Skill's schema or implementation inside this router.

Inspect the connected Blender Scene and decide first whether the request is new creation or work
on an existing asset. Preserve existing objects, rigs and Actions unless replacement is explicit.

Use these creation entries:

- recognizable low-poly prop, weapon or simple environment assembly:
  `blender-create-static-asset`;
- new low-poly humanoid blockout: `blender-create-character-base`;
- reviewed owned character base that needs its first rig: `blender-rig-character-base`;
- explicit hash-pinned Mixamo-style FBX Action for an empty compatible Humanoid rig:
  `blender-import-humanoid-animation`;
- explicit range/FPS cleanup of an imported or existing Armature Action into a new independent
  game clip: `blender-prepare-game-action`;
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

Keep one visible current candidate and recoverable checkpoints. Do not accumulate every failed
revision in the Scene. Continue through multiple stages when the user's request already covers
them, but validate each stage before using it as the next stage's input.

Only offer 2D Pixel/Cel/Toon rendering after the 3D source is reviewable. Only offer engine export
when an exporter actually supports that asset type. Never route a rigged character through the
current static-only FBX exporter.
