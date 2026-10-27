# Asset inspection validation — 2026-09-16

## Use case / decision

First narrow workflow: read-only scene/named/selection inventory. It is independent of
game-specific budgets and provides targets/dependencies for subsequent validation.
Source: `skills/blender-inspect-asset/`. No automatic rig/animation generation or export.

## Environment and verified capabilities

Windows, Blender 5.0.1, ahujasid/blender-mcp (user-provided identity), addon [1, 7],
protocol 7. Codex client build/commit and MCP source commit are unknown.
The current tools `get_addon_status`, `get_scene_info`, `execute_blender_code`,
`get_viewport_screenshot`, and `get_object_info` were actually exercised.

- Native Python and MCP report the same current Scene objects: Cube, Light, Camera.
- Screenshot shows those three objects, confirming object inventory visually.
- Base Cube native counts: 8 vertices, 12 edges, 6 polygons, 12 tessellated triangles.
- Missing-object tool probe returns error text despite `isError: false`; Skill explicitly
  checks content/structured result, not only the tool envelope.
- Initial current context: Object mode, active Cube, no selected objects, unsaved/dirty file.

## Live regression

Loaded exact repository helper source through MCP, then executed
`tests/blender-scene/run_inspection.py` in the same Blender namespace.

Initial run: 27 checks passed. Latest strengthened run: **36 checks passed**, synthetic
fixture cleanup complete, both from repository sources and portable ZIP helpers.
Includes empty scene/selection, missing scene/target, invalid scope/list, explicit named
and selected scope, shared mesh, Shape Keys, node material, two rest bones with parent/deform
flags, Armature modifier target, layered Action binding, NLA reuse, file-wide Action inventory,
and edit-mode counts withheld without mode switching by the helper.

The fixture is a separate native Scene with exact invocation-owned IDs. Only fixture
creation/setup changes Blender state; it does not constitute a production rigging feature.
A 0.25-unit fixture translation was inspected/restored. Original window scene/view layer
were restored, original-scene fingerprint matched, and all tracked Scene/object/mesh/
armature/material/Action/Shape Key datablock names returned to their original lists.
Latest source fingerprint: `f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d`.

The fingerprint includes inspection facts, source mesh coordinates/topology/UV/Shape Key
coordinates/weights, rest/pose matrices, Action curves/keyframe handles, and context
(selection/active/mode/frame). A real fixture keyframe change was detected and restored.
Partial per-object failures, nonfinite JSON fields, and armature edit-mode uncertainties
were also tested. It is a bounded preservation check,
not a binary audit of every Blender datablock property. The current file was already dirty;
temporary fixture creation does not promise preservation of a clean file's dirty flag.
No original object, mesh, rig, animation, file, or external project was replaced or saved.

## Limitations / next work

Read-only helper workflow passed its representative/failure/preservation checks on this
version; installed-client discovery and cross-session Profile behavior remain unverified.
Evaluated topology, instance counts, keyframe contents, skinning/retarget quality, engine
compatibility, and other Blender versions are not certified. Static mesh diagnostics
have now been tested separately; see `docs/static-mesh-validation.md`.
The next gate is installed-client discovery/Profile awareness in the generated Workspace.
