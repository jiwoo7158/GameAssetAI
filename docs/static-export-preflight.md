# Static export preflight — 2026-09-19

## Scope

`scripts/inspect_static_export_context.py` is a **development-only read-only** Blender
snapshot for a named static Mesh. It depends on the existing asset/transform inspectors
when transmitted through MCP. It does not select an object, export a file, refresh the
dependency graph, certify Unity/Unreal import, or install a Skill.

The helper reports base vertex/face/triangle counts, UV-layer and material-slot names,
reported transform/unit settings, selected state only when observable in the active view
layer, and preservation-sensitive dependencies (parent/children, modifier, constraint,
weights, shape keys, animation, shared Mesh, linked data). It queries current exporter RNA
for FBX/glTF operator availability and parameter **names**, not assumed defaults or a
successful export. Explicit optional `requested_format` is FBX or GLTF; absent format
remains unspecified. `engine_ready=None`, `export_authorized=False`, `export_path=None`.

No active Workspace Profile exists at this checkpoint (read-only active-reference lookup;
reference SHA `d14461f6f09ae2b001a84e16178f9262e0d9fbbf57f8415abd6aa5a328440206`).
No axes, length conversion, target format, selection scope, destination, material/texture
policy or engine import behavior is inferred. Existing Unity/Unreal projects are not opened
or relocated. Game-specific choices belong in Workspace Profile or explicit user intent.

## Native evidence

Blender 5.0.1, MCP addon [1,7], protocol 7. `bpy.ops.export_scene.fbx` exposes
`filepath`, `use_selection`, `global_scale`, `apply_unit_scale`, `axis_forward`, `axis_up`;
`bpy.ops.export_scene.gltf` exposes `filepath`, `use_selection`, `export_yup`, `export_apply`.
These were queried in the running Blender; no operator was executed. Current original
Scene reported Cube/Light/Camera and one material; unit system METRIC, scale length 1.0.
Those values describe only this Blender Scene, not a game rule.

Owned synthetic quad with one UV/material: **17 checks pass** for inventory, no-policy/
no-authorization status, observed operator parameters, missing/wrong target and invalid
format refusal, shared-Mesh/modifier review, unchanged fixture and exact ID teardown.
Original fingerprint restored:
`f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d`.
Raw decoded helper hash and full operator property list in ignored
`.local/validation/export-context-20260919.json`.

Run `python -B scripts/prepare_blender_check.py --suite export-context` and transmit the
payload through current Blender MCP. This tests a snapshot, not file persistence or import.

## Next boundary

The next synthetic FBX boundary was executed after the read-only preflight:
`tests/static-mesh/run_fbx_export_probe.py`, suite `fbx-probe`. It created one owned Mesh
in a separate Scene and a unique file under the repository's ignored `.local/validation/`
directory. The exporter was called with **test-only** explicit `axis_forward=-Z`,
`axis_up=Y`, `global_scale=1`, `apply_unit_scale=False`, `use_selection=True`, Mesh-only,
no animation/modifier evaluation. These values are not Unity defaults or recommendations.

The Blender 5.0.1 FBX operator finished and wrote one binary FBX. A temporary context
override exposed only the synthetic Object. The binary contained its Mesh model record
and no model records for original Cube/Light/Camera. A first naive substring check falsely
flagged the FBX `DefaultCamera` metadata; it was corrected to check actual model records.
The file was then imported by Blender's own FBX importer into another owned Scene, with
no animation/image search. **19 checks pass**: one imported Mesh, one face, three vertices,
UV values, non-null material reference and unchanged reported world positions within
test-only 1e-5 tolerance (observed maximum residual 2.384185791015625e-07). The original
Scene fingerprint, active Object, selection and data-name lists matched afterward.
Only exact test-owned imported/source IDs and the single temporary file/directory were
removed; the temporary directory is absent. Full response/source hashes:
`.local/validation/fbx-roundtrip-20260919.json`.

## Observed overwrite hazard and bounded publication experiment

On Blender 5.0.1 the native FBX operator overwrote an **existing test-owned** sentinel
file when called with `check_existing=False`. No user file was involved. A production
workflow must not call it directly on a destination that may already exist; a read-only
existence check alone has a time-of-check/time-of-use race.

`scripts/promote_export_artifact.py` is a single-file development helper: after a caller
has created and validated a staging file, it requires distinct absolute paths in the same
real non-linked directory, refuses an existing target, then uses `os.link` to create a
new target atomically without replacement. It keeps the staged path; caller owns its
cleanup. Hardlink-unsupported volumes fail closed, with no copy/replace fallback. This
does not itself validate ownership, FBX content, engine import, sidecars or arbitrary
concurrent edits.

The synthetic FBX probe now has **23 Blender checks**: native overwrite of only the
owned sentinel was observed; publication of the verified stage created a new target;
re-publication to that existing target raised `FileExistsError` and preserved both the
target and the second stage. Exact three-file directory and all synthetic Blender IDs
were removed, original Scene/context/fingerprint unchanged. Offline tests additionally
cover collision, invalid paths and mocked unsupported hardlink behavior. Latest raw
response/source hashes: `.local/validation/fbx-no-overwrite-20260919.json`.

This proves one Blender-exporter-to-Blender-importer synthetic roundtrip, **not Unity
import**, shading/material appearance fidelity, evaluated geometry, rig/animation,
arbitrary axes/units or production-file safety. A production export workflow still needs
explicit Profile/user settings, target/version evidence, a complete staged-artifact/
sidecar policy and no-overwrite,
export and engine import inspection. No export Skill was created or installed.

Subsequently, a separate synthetic FBX was imported into the live Unity 6000.3.9f1
Editor and instantiated in a non-saved Preview Scene. See
[`unity-import-validation.md`](unity-import-validation.md). That narrower Unity result
does not turn the test-only FBX parameters into defaults or certify production export.

On 2026-09-21 the read-only `export-context` harness was extended to report current
FBX forward/up enum identifiers and `global_scale` hard limits from operator RNA.
Native Blender 5.0.1 rerun passed **19 checks**, including exact synthetic cleanup and
original fingerprint restoration. Observed axes: `X/Y/Z/-X/-Y/-Z`; observed scale
range: `0.0010000000474974513` to `1000.0`. These observations bound the
development-only request preflight in `unity-export-contract.md`, but are not
game-specific axis/scale recommendations and must be rechecked at runtime.

The later request-hash-bound, read-only Blender candidate review expanded this
same synthetic `export-context` suite to **29 checks**. The earlier 19-check count
is historical. It verified current operator poll, preservation/texture blockers,
missing or changed request refusal, unchanged original Scene fingerprint and exact
test-ID teardown. See `unity-export-contract.md` for limits; no file was exported.

A later isolated textured `path_mode=COPY` probe **did** export a test-owned FBX
and observed a sibling `.fbm/source.png` copy. Its exact files were cleaned and
the original Blender context restored. This is sidecar behavior evidence only,
not a production textured-export policy; see `unity-export-contract.md`.

The next texture-free boundary is `scripts/export_static_fbx_staged.py` and
`--suite fbx-staged`. It binds an offline request and live candidate fingerprint,
exports only the named Mesh to a unique same-directory stage, verifies binary/Object/
source state, then atomically publishes without overwrite. Blender 5.0.1 passed
**10 checks**, including injected target-`.meta` appearance after staging and before
publish. The uncommitted stage was removed, conflict preserved for inspection, and
the harness later removed its exact owned sentinel. Original Scene and ID lists matched.

The read-only `export-context` suite now passes **34 checks** after observing and
validating current `apply_scale_options` identifiers. The request also explicitly
carries `use_space_transform` and `bake_space_transform`; none are inferred.
