# Unity static FBX request preflight — development boundary

`scripts/validate_static_fbx_request.py` checks one **explicit** request before any
Blender or Unity mutation. It does not read Markdown Profile rules automatically,
choose per-game defaults, authorize a destination, export, or certify a result.
The caller must read the current active Profile (or obtain a direct user choice),
record the resulting values, and separately verify target Object/Scene state.
An absent Profile or missing required decision remains unknown and is refused.
The successful report includes a SHA-256 of the exact JSON request. A later
Blender-side check must receive that unchanged request and report together.

Required request fields (schema `gameassetai.static-fbx-request.v1`):

| Field | Constraint |
| --- | --- |
| `scene_name` | Exact nonempty Blender Scene name; existence checked later in Blender |
| `object_name` | Exact nonempty Blender Object name; existence/type checked later in Blender |
| `target_file` | Absolute new `.fbx` path in an existing non-linked directory; no existing FBX or `.meta` |
| `axis_forward`, `axis_up` | Explicit Blender FBX enum axes on distinct dimensions |
| `global_scale` | Explicit finite number within observed Blender 5.0.1 FBX RNA hard range 0.0010000000474974513–1000 |
| `apply_unit_scale`, `use_space_transform`, `bake_space_transform`, `use_mesh_modifiers` | Explicit booleans; no Blender defaults are inferred |
| `apply_scale_options` | Explicit current FBX scaling enum |
| `path_mode` | Explicit `AUTO`, `ABSOLUTE`, `RELATIVE`, `MATCH` or `STRIP`; `COPY` refused until sidecars are handled |
| `overwrite` | Must be `false` |

The enum identifiers and scale bound were observed read-only in Blender 5.0.1 through
the connected MCP on 2026-09-21. Runtime code must re-check the current operator RNA,
not assume the same bounds after a Blender change. For a static request the exporter
must restrict scope to one inspected Mesh, use no animation baking, and
revalidate scene state/fingerprint before writing. It must stage in the intended
destination directory, verify all generated artifacts, and publish without overwrite;
`scripts/export_static_fbx_staged.py` now implements that narrow operation for an
already inspected, texture-free single-file candidate. It requires explicit
authorization, rechecks the request/source and target/`.meta`, verifies the staged FBX,
and publishes by same-directory hard link without replacement. It does not solve
texture sidecars or a general multi-file transaction. Destination mapping alone is not
authorization to write into a Unity project.

The preflight is intentionally narrow: it does not validate material appearance,
textures, unit correctness, pivot/orientation for a particular game, modifier result,
Unity importer settings or platform builds. The synthetic Unity FBX check in
[`unity-import-validation.md`](unity-import-validation.md) is evidence for one fixture,
not a set of export defaults. Do not promote this helper into a Skill or run an export
against an existing asset from this report alone.

## Live Blender candidate review

`scripts/inspect_static_fbx_candidate.py` is a separate development-only,
read-only check loaded with `inspect_static_export_context.py`. It matches the
request hash to the offline report, inspects the exact named Scene/Object, rechecks
the current FBX axis enums/scale limits and operator poll, and returns a current
Scene fingerprint. A synthetic no-dependency Mesh can be a
`candidate_for_review`, **never `export_authorized`**. Inactive Scene, shared Mesh,
modifiers, other preservation dependencies and direct image-texture/node-group
materials block that narrow candidate. The node scan is deliberately incomplete;
it cannot certify absence of every texture path or sidecar.

The `export-context` native Blender 5.0.1 harness passed **34 checks** after a
request-scoped fingerprint test correction: the fingerprint includes active Scene,
Object and selection, so it must be compared under the *same* temporary context
override. It checked changed/missing preflight, invalid axes/scale, inactive Scene,
shared Mesh, modifier and texture-node refusal, no authorization, and exact fixture
cleanup/original Scene restoration. The first run failed only because it compared
fingerprints captured under different contexts; no source asset was changed.

The later `fbx-staged` suite exercises the write boundary on owned synthetic data.
Blender 5.0.1 passed **10 checks**: missing authorization and stale candidate refusal,
verified one-file publication, source preservation, target collision preservation,
injected `.meta` appearance between stage and publication refusal, no stage leak,
exact cleanup and original Scene preservation. This remains a development helper,
not a production exporter or installed Skill.

## Unity axis and unit observations

An authorized synthetic Unity 6000.3.9f1 test compared four Blender FBX settings.
`FBX_SCALE_NONE` retained correct world size through root scale 100.
`FBX_SCALE_UNITS` produced scale one but retained an approximately 270-degree X-axis
root rotation. Unity `ModelImporter.bakeAxisConversion=true` changed that to about
90 degrees instead of eliminating it. For this **static Mesh only**, Blender
`bake_space_transform=true` produced zero position/rotation, scale one and expected
world bounds. Blender labels that option experimental and warns against assuming it
for armature/animation workflows.

The final request-bound staged test used `-Z/Y`, scale 1,
`apply_unit_scale=true`, `FBX_SCALE_UNITS`, `use_space_transform=true` and
`bake_space_transform=true`. Unity imported 4 vertices, 2 triangles, 4 UVs, one
submesh/material and zero clips; root transform was identity and world bounds were
`2 x 0 x 1`. The active Scene stayed not dirty. All synthetic FBX/meta files were
deleted and the two pre-existing Scene files retained their hashes. These are fixture
inputs, not universal game defaults.

## COPY sidecar evidence

A separate test-only Blender 5.0.1 probe used one owned Scene/Mesh/material with a
2×2 PNG connected through an Image Texture node. Exporting with `path_mode=COPY`
and `embed_textures=False` wrote **three** files inside an exact owned temporary
directory: the source `source/source.png`, `output/probe.fbx` (18,684 bytes), and
`output/probe.fbm/source.png`. The copied PNG's SHA-256 matched the source
(`E8908CADF976C1DDFAD7F060835FB596892B6FDEE8E3250E3FDF4ED00CE27996`).
The FBX referenced `source.png`. Blender Scene/context and all tracked ID-name
lists matched after fixture teardown. The exact three files and their empty
directories were inspected, then removed; no Unity project path was touched.

This confirms that a single-file no-overwrite hardlink publisher is **insufficient**
for textured `COPY` export: a sibling `.fbm` tree needs ownership, collision,
publication and rollback rules. It does not prove every texture/material produces
the same layout. Until a multi-artifact transaction is designed and tested,
`path_mode=COPY` and direct image-texture candidates remain refused.

Offline tests in `tests/scripts/test_static_fbx_request.py` cover an explicit valid
request, missing/unknown fields, axes, scale, flags, overwrite and existing target/
`.meta` collisions. They create no Blender/Unity artifacts. Test with:

```text
python -B -m unittest discover -s tests/scripts -p "test_static_fbx_request.py" -q
```
