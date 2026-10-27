# Static mesh diagnostics validation — 2026-09-16

## Use case and boundary

Second sequential workflow: read-only named mesh diagnostics before cleanup/export.
Source: `skills/blender-validate-static-mesh/`. No repair, modifier application, rig
replacement, file export, hard-coded engine, art style, or game budget.
Clearly applicable workspace rules may be supplied explicitly; absent rules remain untested.

Environment: Windows, Blender 5.0.1, ahujasid/blender-mcp (user-provided identity), addon
[1, 7], protocol 7. Client build and MCP repository commit are unknown.

## Demonstrated failure and correction

The first live fixture run failed `animation_shape_key_preservation`.
An object had keyframes at frames 1/10 but a source location that had not been refreshed
at the current frame. `evaluated_depsgraph_get()` refreshed animation and changed this
source transform during otherwise read-only viewport evaluation.
The failed fixture was torn down; a subsequent native check confirmed only Scene,
Cube/Light/Camera, and no generated Actions remained.

Correction: evaluate only in the current Scene and conservatively refuse viewport
evaluation when file datablocks (including embedded node trees) contain animation,
Drivers, NLA, object constraints, or pose constraints. This includes dependencies
outside the target Scene. Never delete animation or constraints to bypass this boundary.
Base diagnostics remain available without graph refresh. This conservative policy may
reject unrelated animated data in another scene; it intentionally avoids claiming to
prove a dependency graph's full side-effect freedom. Other evaluation callbacks/add-ons
are not exhaustively tested.

## Retest results

`tests/static-mesh/run_diagnostics.py`: **73 live checks passed**, fixture cleanup complete.

- Existing Cube: 12 base triangles, closed edge incidence, UV layer, no generic findings.
- Supplied test budget 10 reports 12 > 10; equal limit 12 passes that check. These are
  fixture constraints, not GameAssetAI game defaults.
- Open planes are review items, not automatic errors; UV/closure become requirements
  only when explicitly supplied. Missing/invalid names/rules/mode fail without widened scope.
- Empty/loose/wire/collinear/coincident geometry, edge winding/overconnection, and
  mirrored/singular transforms produced the expected distinct facts/findings.
- Synthetic Subdivision cube: base 12 vs viewport-evaluated 48 triangles.
- Evaluation released its temporary mesh, including a simulated post-evaluation metrics
  exception; source geometry remained unchanged.
- Target animation and unrelated animated object both blocked evaluation. Base checks
  preserved Shape Keys and existing Action/curves; nonfinite mesh data withheld triangle
  checks while still producing strict JSON. Edit mode was not changed by the helper.
- Original-scene fingerprint and all tracked datablock names matched after teardown.

Latest combined payload also passed inspection 36 + static diagnostics 73 checks.
Strengthened fingerprint includes source coordinates/topology/UV/Shape Keys/weights,
armature rest/pose matrices, Action curve/keyframe handles, and user context. A fixture
keyframe edit was detected by the fingerprint and restored. This remains a bounded
preservation test, not a binary audit of every ID property.

## Limitations / next gate

`no_findings` is not engine readiness. Vertex-manifold cases, self-intersections, outward
normals, UV overlap/density, render/export/instance geometry, engine imports, imported
production rig/animation formats, and other versions remain unverified.
Source workflows are Blender-tested; installation/discovery and real workspace Profile
awareness must be verified before profile-dependent cleanup or engine preparation.
