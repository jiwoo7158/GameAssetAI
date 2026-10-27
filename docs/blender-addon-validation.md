# Blender Add-on foundation validation — 2026-10-25

## Implemented

`blender_addon/gameassetai` is a standard Blender 5 Add-on source package with:

- a `GameAssetAI` 3D View sidebar panel;
- explicit resolution, framing, view and neutral-lighting controls;
- an owned Scene Preset Builder that creates an orthographic camera and two area lights around
  the active Mesh;
- an owned Blender 5 compositor graph using Render Layers, relative nearest downsample,
  Pixelate, render-size nearest expansion and a group output;
- removal operators that restore the prior camera, render settings and compositor graph while
  refusing unowned name collisions.
- explicit Armature and Action selectors plus a guarded preview operator that binds only the
  selected Action, sets its frame range and retains every Action datablock.
- reversible `Flat Lit`, band-count `Cel Banded` and `Emission Unlit` style materials. Original
  slots and polygon indices are retained; restore refuses missing, edited or unowned state.
- current-frame PNG export with explicit path, no-overwrite publication, same-directory staging,
  PNG signature verification and render-setting restoration.
- portable JSON save/load for camera, lighting, pixel and material-style settings. Object, Action
  and output paths are intentionally excluded from portable presets.
- a sequence bridge that passes the explicit Mesh, Armature, Action and pixel settings through
  the existing Skill validators, candidate/framing checks, stage/job hash chain and background
  renderer. It does not implement another sequence renderer inside the Add-on.
- a sprite-sheet handoff that consumes the last verified sequence receipt and calls the existing
  atomic assembler with explicit grid, padding, PNG and metadata paths.

## Focused evidence

The Scene/compositor factory-startup Blender 5.0.1 fixture passes 17 checks. It verifies setup, ownership,
orthographic framing, resolution/transparent background, Blender 5 socket-based compositor
settings, graph wiring, cleanup and exact global state restoration.

The focused Action-preview fixture passes four checks: explicit selection, binding, range/frame
setup and preservation of both test Actions. The updated Add-on was registered in the live
Workbench and points at `GAA Scout Walk Loop v2`.

The focused material fixture passes nine checks, including owned-node creation, band provenance,
polygon-index preservation, second-apply refusal and exact original-slot restoration. The focused
PNG exporter passes five checks, including atomic publication, PNG signature, render-setting
restoration, overwrite refusal and stage cleanup.

The portable-preset round-trip passes five checks covering new-file publication, schema marking,
restoration of changed controls and stage cleanup.

The sequence-bridge request fixture passes five checks. A live end-to-end run on
`GAA Scout Walk Forward Loop` produced seven 64x64 frames for source frames 1, 5, 9, 13, 17, 21
and 25. All frames were published together, the receipt SHA-256 is
`5528efce83a16096fb4188720f825104249f442129acd0754b82d2d45affb0a8`, and no stage/job remained.

The sprite-sheet bridge fixture passes four checks. Its live handoff assembled those seven frames
into a 259x129 RGBA sheet with a 4x2 grid and 1px padding. The sheet receipt SHA-256 is
`fad6d6a72099b994da088c4f7658780f26704b4df79549a2520e81fa44cd9fad`.

The former `Pixel Preview` panel heading was inaccurate because it configured the Scene rather
than displaying a live preview. It is now `Pixel Scene Setup`, and its target label follows the
explicit Mesh target rather than whichever Object happens to be active.

The Add-on is now installed at Blender 5.0's user Add-ons path and enabled in saved Preferences.
Runtime verification resolves `gameassetai.__file__` from that installed path and confirms the
Scene property group plus `GAA_PT_pixel_pipeline` panel registration. All 14 source files
(excluding generated `__pycache__`) hash-match the installed files.

`scripts/inspect_blender_addon_installation.py` provides the repeatable read-only lifecycle
check. It parses literal `bl_info` metadata without importing the Add-on, compares every
non-cache source/installed file by SHA-256, reports missing/extra/changed files, and checks the
declared minimum Blender version against an explicitly supplied runtime version. Five offline
tests cover aligned, absent, changed/extra, invalid metadata and incompatible-Blender cases.

`scripts/update_blender_addon.py` adds hash-bound `plan`, atomic `apply` and recoverable `restore`.
It refuses source/installation drift after planning, stages only verified source files, preserves
the entire prior installation as a backup, and retains the replaced new version on restore. Four
focused tests cover update, no-op alignment, drift refusal and restoration. The current live
0.1.5 plan reports `already_aligned`, so no installed files were rewritten.

A separate Blender 5.0.1 process was then started without `--factory-startup`. Saved Preferences
automatically enabled `gameassetai`, imported it from the user Add-ons directory and registered
`Scene.gameassetai` plus `GAA_PT_pixel_pipeline`. All five restart checks passed. The interactive
character Workbench did not need to be closed or altered for this proof.

Installable archive:

- `.local/source-bundles/gameassetai-blender-addon-0.1.5.zip`
- 66,167 bytes
- SHA-256 `1bb82d28f898fafa4cd55fc480a141c3d2b59dc514171dbfbb53ae9563a4bc90`

## Next Add-on modules

1. multi-item batch dispatch;
2. richer animation review controls.
