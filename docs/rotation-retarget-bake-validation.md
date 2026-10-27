# Rotation-only retarget bake validation

Validated on 2026-09-26 with Blender 5.0.1 through
`ahujasid/blender-mcp` at `localhost:9876`.

## Scope

`blender-bake-rotation-retarget-copy` samples evaluated mapped source-bone
`matrix_basis` rotations at every integer frame, writes quaternion keys to an owned
temporary target-rig copy, then keeps only one fake-user-protected, unbound Action.

Unlike the aligned path-remap Skill, mapped source and target rest matrices may differ.
This does not make the workflow a general retargeter: local-basis rotation equality does
not guarantee equal world-space poses, visual equivalence or correct deformation.

The workflow rejects location, scale, Object/root-motion and non-bone channels. It also
rejects unmapped animated bones, parents, non-identity Armature Object transforms,
Object/pose-bone constraints, Object drivers, differing inherit-scale modes, multiple
Action slots, target collisions, stale previews, non-unit frame steps and ranges over
10001 frames.

## Blender evidence

The owned fixture creates two full explicit humanoid mappings with deliberately different
rest directions. The source uses Euler rotation keys on one mapped arm bone; the result is
a three-frame quaternion bake on the target bone name.

Repository source, packaged ZIP and installed Workspace helpers each pass 12 checks:

- differing-rest candidate
- missing-authorization refusal
- stale-source refusal
- non-identity Object-transform refusal
- pose-bone constraint refusal
- non-unit step refusal
- independent unbound fake-user result
- expected frame/curve/role shape
- target-bone paths
- integer-frame linear keys
- source Action and target Armature preservation
- exact teardown and original-Scene restoration

The first native run found that the temporary source copy was still counted as an Action
reference during preservation validation. The temporary binding is now explicitly cleared
before the original reference set is compared.

## Packaging and evidence boundary

Archive:

`.local/source-bundles/rotation-retarget-bake-20260926/blender-bake-rotation-retarget-copy.zip`

SHA-256:
`3718075d937d050fd6cd47a07390125ef9ab335d7b20aceb721313ed45edf612`

Installed without overwrite at:

`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-bake-rotation-retarget-copy`

Source, ZIP and installed helper execution are verified. Refreshed-client discovery and
no-input refusal remain separate. No user asset or Unity project was accessed.

Still unimplemented: hip translation/proportion scaling, root motion, world/humanoid-space
pose matching, constraint-aware retargeting, result binding, production Mixamo fixtures,
deformation review and Unity animation import.

