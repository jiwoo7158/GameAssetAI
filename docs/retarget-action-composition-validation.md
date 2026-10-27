# Retarget Action composition validation — 2026-09-27

`blender-compose-retarget-actions` combines one strict quaternion-rotation-only Action and
one strict root-location-only Action into a new fake-user-protected, unbound Action. Both
inputs must have one Object slot, one linear key per requested integer frame, no sampled
points/modifiers, no bindings, and channels matching the explicit target Armature.

Blender 5.0.1 passed nine checks from repository source, portable ZIP and installed
Workspace helpers: preview, authorization and stale refusal, nonlinear-input refusal,
seven-curve output, combined paths, input/target preservation and exact teardown.

Archive: `.local/source-bundles/retarget-action-composition-20260927/blender-compose-retarget-actions.zip`

SHA-256: `df25084157cc4415d78595fc369282c557bf703e502234b82cdf43b21eea2340`

Installed without overwrite at
`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-compose-retarget-actions`.

The workflow does not bind the result, add NLA, merge arbitrary Actions, export, save,
validate deformation, or configure Unity. Client discovery is a separate host gate.
