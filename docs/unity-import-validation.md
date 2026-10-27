# Synthetic Unity FBX import validation — 2026-09-21

This is a bounded engine-import test, **not** a production export contract or a new
Skill. Unity 6000.3.9f1 was already open on `GameEngineering`; Blender 5.0.1 and
`ahujasid/blender-mcp` addon 1.7/protocol 7 were connected. Unity MCP was not exposed
to this Codex session, so the live Editor was inspected through the installed Unity
CLI/Pipeline connection. Its first sandboxed status check could not see the Editor;
the same read-only check with approved elevated access found it ready on port 7800.

The only Unity project path used for the test was
`C:\Users\jiwoo\UnityProject\GameEngineering\Assets\Blender`. Before the test it
contained only `Blender.unity` and `Blender.unity.meta`. The open scene was
`Assets/Blender/Blender.unity`, not dirty, with two root objects. The test used a
new uniquely named FBX in that folder; the existing scene was neither saved nor
edited. Unity's normal asset import created its matching `.fbx.meta` and internal
import cache; no direct edits were made to other Unity project paths.

## Fixture and observed import

- Synthetic Blender-owned quad: 4 vertices, 2 triangles, one UV layer and one
  material, object location `(1, 2, 3)`, scale `(2, 1, 1)`. Only this object was
  exported. Test-only FBX settings were `axis_forward=-Z`, `axis_up=Y`,
  `global_scale=1`, `apply_unit_scale=False`, Mesh-only, no baked animation or
  modifier evaluation. These settings are **observations**, not game defaults.
- Blender produced a 15,292-byte binary FBX. Its synthetic Blender IDs were
  removed after export; the original Blender Scene remained Cube/Light/Camera.
- Unity recognized the file with `ModelImporter` and a GameObject model prefab.
  The imported Mesh had 4 vertices, 2 triangles, one submesh, 4 UV coordinates,
  4 normals and 4 tangents. One MeshFilter, MeshRenderer and material reference
  were present. The material used the supported `Standard` shader in this
  project's Built-in Render Pipeline; visual/material fidelity was not tested.
- The imported world vertex positions were `(-1,3,-2)`, `(-5,3,-3)`,
  `(-5,3,-2)`, `(-1,3,-3)` (rounded to 0.01), consistent with this fixture's
  scaled geometry and the tested Blender-to-Unity axis conversion. UV values
  included the expected four corners, and world normals were `(0,1,0)`.
- Default Unity importer observations: `globalScale=1`, `useFileScale=true`,
  `fileScale=0.01`, `bakeAxisConversion=false`, `importAnimation=true`,
  `isReadable=false`. The prefab root showed a large compensating scale; usable
  world geometry must be judged after the full transform hierarchy, not by the
  raw Mesh bounds or root scale alone. No animation or rig was in this fixture.
- `PrefabUtility.InstantiatePrefab` succeeded in a new in-memory Preview Scene:
  one root, MeshFilter and Renderer. That Preview Scene was closed without saving.
  The user's `Blender.unity` remained active, not dirty and at two roots.

## Cleanup and limits

After inspection, Unity's `AssetDatabase.DeleteAsset` removed only the exact
test FBX and its generated `.meta`. The repository-side staging FBX was also
deleted after exact SHA-256/size verification. The Unity folder again contained
only its original two files. Their SHA-256 hashes matched the pre-test values:
`Blender.unity` `D3E92CB4E393601199E0D0C870706A3A80377429F5C6117D7A944CD75F21D8FB`;
its `.meta` `0D9695875929209775B5E8E37206FFFD02588306055B133BE79DF694AC248603`.
The original Blender Scene still reported three objects and no test-owned IDs.

The first one-off Blender teardown stopped at a premature material-user check:
the owned Mesh still referenced its owned material even after the Object was
removed. This was corrected by verifying ownership and zero Mesh users, removing
the Mesh, then checking/removing the material and finally the separate Scene.
The exact tagged IDs were verified absent afterward. A repeatable fixture should
encode this cleanup order in a `finally` block.

This validates one simple static FBX import and temporary instantiation in this
Unity version. It does **not** certify arbitrary models, evaluated modifiers,
textures/material appearance, colliders, LOD, rigs, animation, other pipelines,
platform builds or a reusable export policy. A Workspace Profile or explicit
per-game decisions still need to specify format, axes, units, destination,
selection, material policy and overwrite handling before a production exporter
can be offered. The user's existing Unity/Blender projects stay in place.

## Request-bound staged follow-up

A later same-day test used the request-bound staged exporter. The contract now
explicitly carries `apply_scale_options`, `use_space_transform` and
`bake_space_transform`. Four owned variants showed that raw Mesh bounds alone are
misleading: `FBX_SCALE_NONE` imported with root scale 100 while retaining correct
world size; `FBX_SCALE_UNITS` changed scale to one but retained axis-correction
rotation. Unity Bake Axis Conversion did not remove that rotation for this fixture.
The static-only Blender bake variant imported with identity root transform and correct
`2 x 0 x 1` world bounds.

The final staged FBX imported as one GameObject/MeshFilter/Renderer: 4 vertices,
2 triangles, 4 UVs, one submesh/material and no animation clips. Preview Scene only;
the open `Blender.unity` remained active, not dirty and at two roots. Unity then
removed the exact FBX and generated `.meta`. The folder returned to the original
Scene and meta with the hashes above. Blender labels `bake_space_transform`
experimental, so this static evidence does not extend to rigs or animation.
