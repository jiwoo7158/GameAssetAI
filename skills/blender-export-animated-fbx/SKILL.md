---
name: blender-export-animated-fbx
description: Export one explicit skinned Mesh, Armature, and independent Action as a staged no-overwrite Unity-oriented animated FBX, preserving all Blender sources. Use after a game Action is reviewed and prepared; do not use for static-only export, multi-character batches, automatic loop/root-motion edits, Animator Controller creation, or Unreal.
metadata:
  contract: gameassetai.skill-contract.v1
  requirements: REQ-ENGINE, REQ-CHAR, REQ-ANIM, REQ-SAFE, REQ-WORKFLOW
  evidence: engine-proven
  external-dependencies: none
---

# Blender Export Animated FBX

## Requirements and responsibility

Export one named local Mesh, its one explicit Armature modifier, and one explicit Object-slot
Action to a new Unity-oriented FBX. The selected Action may be unbound on the source rig. Bind it
only to owned temporary copies, export exactly the requested range, validate the staged binary and
publish without overwrite. Preserve source Mesh/weights/UV/material slots, Armature/rest pose,
Action/F-Curves/slot, NLA/current bindings, Scene context and the `.blend` file.

## Implementation basis and dependencies

Use Blender 5.0.1's built-in FBX exporter, existing GameAssetAI Action snapshot helpers and the
static export Skill's hard-link publication helper. Load these in one globals/locals dictionary:

1. `blender-inspect-animation/scripts/inspect_animation.py`;
2. `blender-copy-action/scripts/action_copy.py`;
3. `blender-export-static-fbx/scripts/promote_export_artifact.py`;
4. this Skill's `validate_animated_fbx_request.py` and `export_animated_fbx.py`.

No external Python package is required. Unity validation is a downstream evidence gate and does
not change the Blender export contract.

## Workflow

1. Require exact Scene/Mesh/Armature/Action/slot, integer inclusive clip range, FPS, target path,
   Unity axis/unit policy, modifier/material policy, rig policy, non-loop policy and `IN_PLACE`.
2. Run `validate_animated_fbx_request(request)` outside or inside Blender, then
   `preview_animated_fbx_export(request)`. Report the source/request fingerprints and blockers.
3. After authorization for that exact candidate, call
   `export_animated_fbx_staged(plan, authorization=True)`.
4. Reimport the FBX in a fresh Blender 5.0.1 process and check the weighted skinned Mesh, UV,
   required bones, Action range/FPS, representative pose signatures and actual Mesh deformation.
5. Import the exact hash-pinned FBX into an isolated Unity validation folder. Keep Generic and
   Humanoid evidence separate; do not infer loop approval.

## Preservation

The exporter creates independent Mesh/Object and Armature/Object copies in a temporary Scene,
redirects only the copied Armature modifier, binds only the copied rig, and cleans those data after
export. It refuses linked/shared ambiguity, unsupported dependencies, missing weights/UV, source
constraints/drivers, output or `.meta` collision, stale preview and non-Unity policy. Failure before
publication removes only its exact stage and temporary Blender data. A published target is never
silently removed or overwritten.

## Validation and completion

Implemented means a staged FBX is published with SHA-256 and a preservation receipt.
Blender-validated additionally requires fresh-process reimport with one skinned Mesh/Armature,
required bones, vertex groups, UV, one Action covering the requested duration, representative pose
agreement and evaluated Mesh motion. Engine-proven additionally requires an actual Unity import,
Generic rig/clip discovery, non-loop state, correct duration/FPS and sampled skin deformation.

The Action range is inclusive; a 1-24 clip at 30 FPS has 23 intervals and duration 23/30 seconds.
`loop=false` is mandatory in this first version. Loop metadata is never changed or approved by the
exporter.

## Boundary

Version 1 supports one local Mesh, one local Armature, one Armature modifier, one Object-slot pose
Action, Blender materials without texture-copy/baking, applied exporter modifiers, deform bones,
Unity `-Z/Y` axes, unit scale, `IN_PLACE`, one owned temporary NLA take named from the selected
Action, no source NLA/all-Actions export and no animation simplify.
It does not support multiple Meshes/Actions, linked data, Shape Keys, constraints/drivers, custom
animated object channels, root-motion conversion, loop editing, texture baking, Humanoid Avatar
certification, Animator Controllers, GLB or Unreal.
