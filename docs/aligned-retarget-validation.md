# Aligned Action-copy retarget validation

Validated on 2026-09-26 with Blender 5.0.1 through
`ahujasid/blender-mcp` at `localhost:9876`.

## Scope

`blender-retarget-aligned-action-copy` creates one independent, fake-user-protected,
unbound Action by copying stored F-Curves and replacing explicit source bone data paths
with explicit target bone data paths. It is intentionally limited to rigs that already
have matching mapped rest matrices, Object transforms, supported rotation modes and no
relevant constraints or drivers.

It is not a general pose-space retargeter. It does not convert differing rest poses,
axes, rolls or proportions; evaluate poses; create constraints; bind the result; bake;
transfer root-motion policy; export; or save Blender.

## Safety contract

Preview must be fresh and exact. Apply requires `authorization=True`, an unused result
Action name, source preservation, an unbound result and fake-user persistence. It refuses:

- incomplete or inferred humanoid mappings
- animated pose bones outside the mapping
- non-bone or unsupported channels
- differing mapped rest matrices or Object transforms
- differing animated rotation modes
- parented Armatures, Object/pose-bone constraints or Object drivers
- multiple Action slots, name collisions and stale previews

The only persistent successful output is the new unbound Action datablock. Source Action,
current/NLA references, both Armatures and target bindings remain unchanged.

## Blender evidence

The owned fixture uses two full humanoid mappings with identical rest matrices but
different bone names. The source Action animates hip location and an upper-arm quaternion.
Repository source, packaged ZIP and installed Workspace helpers each pass 16 checks:

- candidate preview
- authorization refusal
- stale-source refusal
- Object-transform mismatch refusal
- animated rotation-mode mismatch refusal
- pose-bone constraint refusal
- rest-matrix mismatch refusal
- name-collision refusal
- successful fresh preview after restoration
- independent unbound fake-user result
- complete source-to-target path remap
- key/value/settings and source preservation
- target Armature preservation
- target slot display-name update
- group-name handling where available
- exact fixture teardown and original-Scene restoration

The first native iteration found that `matrix_world` can remain cached after a direct
Object-channel change without a dependency refresh. The guard now refuses parented
Armatures and compares raw location, active rotation representation and scale without
forcing a Scene update. A second iteration confirmed that any temporary rest edit makes
an earlier preview stale, so apply requires a new preview after restoration.

## Packaging and evidence boundary

Archive:

`.local/source-bundles/aligned-retarget-20260926/blender-retarget-aligned-action-copy.zip`

SHA-256:
`dc3812b76355d122a53c093b35f1d0be0fda63dc60947385769f1b677214565e`

Installed without overwrite at:

`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-retarget-aligned-action-copy`

Source, ZIP and installed helper execution are verified. Refreshed-client discovery and
no-input behavior remain separate. No user asset or Unity project was accessed. Ordinary
Mixamo-to-custom-rig retargeting remains unimplemented because it normally requires
pose-space conversion and evaluated/baked validation.

