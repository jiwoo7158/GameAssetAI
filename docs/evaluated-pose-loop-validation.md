# Evaluated pose-loop validation — 2026-09-28

## Scope

`blender-inspect-evaluated-pose-loop` compares the evaluated local-basis transforms at
two explicit integer frames for an explicit complete list of animated pose bones in one
Action slot. It reports translation distance, shortest quaternion angle and maximum scale
component delta per bone, plus start-forward/end-backward finite-difference translation,
rotation-vector and scale velocities and aggregate endpoint/seam results.

This remains narrower than visual loop validation. Matching sampled endpoint velocities
do not prove subframe continuity, good deformation, correct root-motion policy, or Unity
runtime behavior.

## Safety boundary

The helper requires exact Scene, Armature, Action, bone-list, slot, frame and tolerance
inputs. It refuses parented Armature Objects, constraints, drivers, Object or custom
property curves, unsupported pose properties, omitted animated bones, ranges over 10000
frames and velocity intervals that cross. Missing inputs never cause synthetic user-scene
data to be created.

Evaluation uses an owned temporary Scene and independent Armature Object/data copy. The
existing Action is temporarily bound only to that copy. The helper compares stored source
state, Action content and Action references before and after, then removes every temporary
ID. It retains no Action and does not save the Blender file.

## Blender evidence

Blender 5.0.1 passed 16 checks from repository source, portable ZIP and the installed
Workspace copy:

- matching endpoint poses with a matching root tangent and mismatching child angular tangent
- per-bone and aggregate endpoint/velocity tolerance results
- explicit animation flags
- missing-bone, omitted-animated-bone, bad-slot, crossing-interval, constraint and
  Object-motion refusal
- source Armature/Action preservation
- exact fixture teardown and original Scene restoration

The first run exposed a location-only path decoder inherited from the stored root-motion
inspector; this Skill now uses its own general pose-transform path parser. The next run
showed the synthetic fixture had a stale pose cache after key insertion; the fixture now
synchronizes its current frame before recording the preservation baseline. User scenes
are not refreshed to manufacture a passing baseline.

Archive:

`.local/source-bundles/evaluated-pose-velocity-20260928/blender-inspect-evaluated-pose-loop.zip`

SHA-256:

`0b06e3bce184d4190c9dbbef937da4a6e5104acd3635573c32ede76b42eb7e0d`

Installed without overwrite at:

`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-inspect-evaluated-pose-loop`

The previous endpoint-only version is retained at:

`D:/AI/GameAssetAI-Workspace/.agents/skill-backups/blender-inspect-evaluated-pose-loop-20260928-pre-velocity`

## Remaining evidence

Endpoint-only refreshed-client discovery and correct no-input refusal are user-confirmed.
Refreshed-client visibility of the v2 velocity inputs remains a host gate. Subframe, NLA,
constraint, deformation, visual and Unity loop validation remain separate future work.
