# Guard-enforced coplanar preview — 2026-09-18

## Implemented boundary

Development-only `scripts/preview_coplanar.py`, not an installed Skill or apply operation.
Load exact `cleanup_loose.py` for `_loose_state`, `check_affine_uv.py` and preview sources
in the same globals/locals dictionary through native MCP. The separate experiment payload
loads these automatically. No Blender-readable local source path is assumed.

`preview_coplanar(explicit_object_name, angle_limit=..., tolerance=..., scene_name=...)`
requires explicit positive finite parameters (booleans refused); prototype angle cap
0.001 radians. These are developmental numerical tolerances, not game defaults/budgets.
The whole mesh must have a planar affine mapping in EVERY UV layer, assigned valid
surface materials and no loose/nonmanifold/degenerate surface. The restriction deliberately
rejects UV-island/general curved assets rather than guessing safe local changes.

Refuse Edit mode, linked/overrides, parent/children, modifiers/constraints/groups, Shape
Keys, animation binding, custom normals and unsupported generic attributes. The observed
`uv_seam` BOOLEAN/EDGE built-in is supported here; unexpected schema is refused. Initial
reuse of the installed cleanup gate failed because its attribute allowlist excludes
uv_seam. Corrected only this prototype's inspection guard; installed cleanup was NOT
relaxed or changed. Preview never evaluates the dependency graph.

The source fingerprint includes object/mesh names, source geometry, corner UV/material/
smooth data, material reference names, UV layer names, transforms, seam/sharp edge flags,
face normals and exact parameters. It is bounded: not every property, users/links or
material contents. There is no apply function consuming it yet and no live freshness
certificate. Budget or hash availability cannot authorize edits.

Subsequent apply unit now consumes source_sha256 and validates an additional canonical
predicted_geometry_sha256; see `coplanar-apply.md`. Statements above about the preview-only
checkpoint are historical; preview itself still creates no permanent IDs or edit authority.

An ephemeral BMesh simulates native dissolve with verified NORMAL/MATERIAL/SEAM/SHARP/UV
delimiters, only internal candidate edges and no boundary dissolve. No `to_mesh`, Mesh/Object
copies, linking, selection/mode changes, save/export or permanent ID allocation occurs.
The BMesh is freed in finally on both success and operator failure. Compare boundary
positions, corner UV/material/smooth sets and area before reporting predicted counts.

## Output

Schema `gameassetai.coplanar-preview.v1`: status error/blocked/preview, errors, source names,
parameters and bounded source_sha256 where inspection succeeds. Blocked gives the failed
UV/planarity reason; preview gives before/predicted counts [vertices,edges,faces,triangles],
changed and triangle_reduction. Candidate indices include protected edges; they are NOT
an exact promised-removal list. Every report has mutation_authorized=false.

This is structural simplification, not ratio-based triangle reduction, general UV quality
or engine readiness. A valid preview can predict no change. Geometry and UV currently
share one explicit absolute tolerance; separate scale/unit policies remain future work.

## Direct evidence and reproduction

```powershell
python -B scripts/prepare_blender_check.py --suite coplanar-experiment
```

Transmit returned code with the actual user request to the exposed native MCP tool.
Blender 5.0.1, addon [1,7], protocol 7. Final experiment 107 normal checks + 4 failure
teardown checks passed; this total includes prior capability experiments and new preview
checks, not 111 independent preview checks. Seven source cases:

- affine continuous plane previews 4/5/2/2 → 4/4/1/2 (no triangle reduction);
- material/seam/sharp boundaries preview unchanged;
- nonaffine UV, UV split and noncoplanar sources blocked before native dissolve;
- changing seam or UV changes fingerprint; seam changes prediction, broken UV blocks;
- invalid angle/tolerance and missing target refuse;
- injected preview operator failure reports error, frees BMesh, leaves IDs/source unchanged;
- all previews create no IDs; exact synthetic fixture teardown restores original fingerprint
  and tracked datablock lists.

Original fingerprint `f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d`.
The capability experiment intentionally continues its unguarded nonaffine-copy probe;
that demonstrates native UV delimiter limitations, not preview permission to apply.

## Next unit

Before copy apply: separate explicit authorization/API, fresh preview binding, globally
unused output name, file-wide evaluation risk guard, independent object/mesh data,
same bounded validation against predicted output, retained protected flags and rollback
for write/validation/link failures. Preview source does not ship in installed Skill ZIPs;
do not package a cross-repository helper dependency as a self-contained Skill.
