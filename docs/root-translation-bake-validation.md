# Root translation bake validation — 2026-09-26

`blender-bake-root-translation-copy` creates one fake-user-protected, unbound Action with
exactly three location curves for an explicitly named parentless target root bone. It
requires a `TRANSFER` or `IN_PLACE` policy, an Armature-space XYZ boolean mask and an
explicit scalar; it never infers roots, axes or proportions.

`TRANSFER` maps the evaluated absolute source `matrix_basis.translation` through the
source root rest orientation into Armature space, applies the mask and scalar, then maps
through the inverse target root rest orientation. `IN_PLACE` writes zero location at every
sample. Rotation, scale, Object motion and Action composition are excluded.

Blender 5.0.1 passed 12 checks from repository source, portable ZIP and installed
Workspace helpers: preview/authorization/staleness, mask/scale/constraint refusals,
translation-only output, linear integer keys, TRANSFER and IN_PLACE creation, source and
target preservation, and exact teardown.

Archive:
`.local/source-bundles/root-translation-bake-20260926/blender-bake-root-translation-copy.zip`

SHA-256: `a1180b71d260ae52878e126142478fdf1d05a51f92741d7159fab32ea711b451`

Installed without overwrite at
`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-bake-root-translation-copy`.

This does not merge with the rotation-bake Action, bind either result, validate visual
motion/deformation, import Mixamo assets, export, or configure Unity root motion.
Refreshed-client discovery remains a separate host gate.
