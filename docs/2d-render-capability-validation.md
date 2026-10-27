# 2D render capability validation

## Scope

This is Phase 0 capability evidence for the planned downstream 3D-to-2D pipeline. It is
not a rendering Skill and does not claim pixel-art quality, color accuracy, deterministic
pixels, published files or Unity sprite compatibility.

The repository helper `scripts/inspect_2d_render_capabilities.py` reads the active Scene's
render settings and Blender RNA metadata. The `2d-render-capabilities` Blender suite checks
that inventory without creating a camera, light, compositor graph, image or file.

## Live result — 2026-09-29

Blender 5.0.1 passed all 10 checks through the current Blender MCP execution path:

- the render operator exists and polls successfully with Eevee active
- PNG, RGBA and configurable color depth are exposed
- orthographic cameras and `ortho_scale` are available
- resolution, transparent-film and output-path controls are available
- `Image.save` and `Image.save_render` are exposed as RNA functions
- render-layer, scale, pixelate and file-output compositor node types are available
- color transform, exposure and gamma settings are readable
- active Scene, mode, frame, objects, selection, render settings and relevant datablock
  counts are identical before and after inspection

The user Scene remained `Cube`, `Light`, `Camera` with one material after the test.

## Blender 5 compatibility findings

Blender 5.0.1 exposes compositor access on `Scene.compositing_node_group`; the legacy
`Scene.node_tree` property is absent. The legacy `CompositorNodeComposite` and
`CompositorNodeValToRGB` Python type names are also absent, while
`CompositorNodeOutputFile`, `CompositorNodePixelate`, `CompositorNodeScale` and
`CompositorNodeRLayers` are present.

RNA methods and properties must be inspected through `bl_rna.functions` and
`bl_rna.properties`. Python `hasattr`/`callable` checks on `bpy.types.Image` and
`bpy.types.Camera` under-reported valid APIs and caused the first probe to fail. The
helper was corrected and the suite then passed.

Color-management enum metadata is dynamic or incomplete in this environment: the current
view transform is `AgX`, while the RNA enum list reports only `NONE`. Future code must read
current values and validate explicit assignments instead of treating that enum list as a
complete preset catalog. Render-engine enum metadata has the same general limitation.

## Next gate

Define game-neutral, Profile-backed request schemas and fingerprints before any render
write. The first write-capable test must use an owned temporary Scene and unique staged
output under a test directory, validate dimensions/alpha/file collision behavior, and
remove only invocation-owned data and files.
