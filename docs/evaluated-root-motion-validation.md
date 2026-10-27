# Evaluated root-motion validation — 2026-09-26

## Scope

`blender-inspect-evaluated-root-motion` measures one explicitly named parentless bone
while a named Action is evaluated on an owned temporary Armature copy. It samples every
integer frame and reports the root position in local-basis, Armature and world space.

This closes the gap between stored F-Curve endpoint inspection and evaluated translation
evidence. A clip may have zero net displacement while still travelling away from and back
to its start; `path_translation_evidence` detects that sampled path independently from
`net_translation_evidence`.

## Safety boundary

The helper requires exact Scene, Armature, Action, bone and range inputs. It rejects
parented root bones, parented Armature Objects, constraints, drivers, Object-transform
Action channels, missing root-location curves, ambiguous Action slots, non-unit frame
steps and ranges over 10001 frames.

Evaluation happens in a temporary Scene with an independent Armature datablock and Object.
The existing Action is bound only to that temporary Object, then unbound before teardown.
Stored Object/pose properties, Action content and Action references are compared before and
after. No output Action or file is retained.

## Blender evidence

Blender 5.0.1 passed 11 checks from repository Skill source, the portable ZIP and the
installed Workspace copy:

- integer-frame evaluation and three-space metrics
- a returning loop with zero net displacement but a nonzero sampled path
- static Armature Object scale reflected in world-space distance
- constraint, frame-step, slot and Object-motion refusal
- source Armature/Action preservation
- exact synthetic fixture teardown and original Scene restoration

The first native run exposed an invalid preservation assertion: evaluated
`matrix_world`/`matrix_basis` caches were being compared as if they were stored data.
The guard now compares stored transform and pose properties, Action content and references,
then restores the original Scene frame to refresh evaluation deterministically.

Archive:

`.local/source-bundles/evaluated-root-motion-20260926/blender-inspect-evaluated-root-motion.zip`

SHA-256:

`3d32271de279fc31df46135ea5566b105dac1b2212d04c0753aa25e35fb3b131`

Installed without overwrite at:

`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-inspect-evaluated-root-motion`

## Limitations

The result is sampled at integer frames and excludes constraints, drivers, NLA blending
and subframe extrema. World metrics include the static Armature Object transform. They do
not select a root-motion bone, decide in-place versus moving policy, scale motion for a
target rig, transfer motion, validate deformation, configure Unity or certify engine
behavior. Refreshed-client discovery remains a separate host gate.
