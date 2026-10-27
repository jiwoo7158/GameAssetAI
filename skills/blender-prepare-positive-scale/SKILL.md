---
name: blender-prepare-positive-scale
description: Preview and explicitly apply positive local scale to an independent copy of a simple Blender mesh while checking base positions, pivot, UV and material references. Not general Apply Transforms, negative scale correction, rig preparation, pivot relocation or export.
---

# Prepare positive scale on an independent static copy

Use only for an explicitly requested scale-preparation operation. Inspection, cleanup or
a triangle budget does not authorize applying scale. Read live Scene/addon status first,
and reread the Workspace active reference/Profile before any game-specific assumptions.
Unknown units, axes, engine, pivot and geometry tolerance are not defaults to invent.

Read these self-contained sources in order: [inspector](scripts/inspect_static_transform.py),
[preview](scripts/preview_scale_copy.py), [apply](scripts/apply_scale_copy.py). Transmit their
exact contents through the currently exposed Blender Python execution tool; do not assume
Blender can read installed paths. Compile each independently into one dictionary used for
both globals and locals and call the function in that same MCP request. Carry preview data
as JSON between requests; no persistent execution namespace is assumed. Pass the actual
user request to MCP and inspect error text even if isError is false.

Call `preview_scale_copy(object_name, scene_name=..., geometry_tolerance=...)` first with
an explicit named mesh and explicitly supplied finite positive tolerance. The tolerance
is a coordinate-error bound, not permission to repair or relocate a pivot. Use an applicable
explicit Profile/user rule; clarify this bound if absent, rather than borrowing fixture
values. Missing selection is not permission to pick another object. Preview creates no
Object/Mesh; `no_change` is valid for unit scale.

Apply only after authorization for this exact operation, using `apply_scale_copy` with
the preview's `source_sha256` as `expected_source_sha256`, identical tolerance/Scene,
an unused explicit `result_name` (at most 63 UTF-8 bytes), and `authorized=True` conveying
that authorization. The helper recomputes freshness, independently copies Object/Mesh,
scales only copied coordinates and sets copied scale to one. Location/rotation/origin,
topology/edge flags/UV layers and material references are checked; materials stay shared.
Missing/stale fingerprints, name collisions and unsupported input refuse even for no-change.

## Safety and limits

- Positive scale only, XYZ rotation, Object mode, polygon surface; reject reflected/zero
  scale, delta transforms, parents/children, constraints/modifiers, groups/Shape Keys/
  animation, linked/override data, custom normals and unsupported generic attributes.
- Apply conservatively rejects file-wide animation data/drivers/constraints. Reported
  source world/basis inconsistency refuses; do not force graph refresh to bypass it.
- Native tests showed stale cached copied matrix_world after scale assignment and small
  decomposition rounding. Helper sets only the new copy's matrix and restores exact scale
  channels; do not replace this with scene-wide update or operations on the original.
- Validation covers base coordinates and reported matrices without dependency refresh,
  not evaluated geometry, numerical conditioning, normals/tangents, material appearance
  (especially procedural/object-space textures), engine import or a deep material backup.
- Ordinary write/validation/link failure removes only exact newly owned IDs with safe
  users/links. `failure_cleanup=unverified` means stop and inspect exact IDs; no blind retry,
  wildcard deletion or replacement. An uncertain MCP outcome requires reinventory first.

After success inspect source and output, confirm independent Mesh and unit output scale,
and obtain current Scene inventory/viewport when available. Coincident copies are expected;
do not move/hide/delete the original for display. Never save or export implicitly.
Blender 5.0.1 synthetic evidence supports this narrow development workflow, not a stable
general transform or production asset guarantee.
