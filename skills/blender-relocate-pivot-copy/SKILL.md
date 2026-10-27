---
name: blender-relocate-pivot-copy
description: Preview an explicitly chosen local pivot and relocate it on an independent copy of a simple Blender static mesh. Use for requested pivot/origin preparation, not automatic centering, scale application, rigging or export.
---

# Relocate an explicit pivot on a copy

Use when the user asks to inspect or relocate a named static mesh's origin to a specific
base-mesh local point. This Skill does not choose center, bottom, game axes or units.
Read current Blender Scene/addon and active Workspace Profile when game rules matter;
missing rules are unknown. Inspection is not authorization to edit.

Load these self-contained scripts in order: [transform snapshot](scripts/inspect_static_transform.py),
[static eligibility](scripts/preview_scale_copy.py), [pivot preview](scripts/preview_pivot_copy.py),
[copy apply](scripts/apply_pivot_copy.py). Send exact script contents through the current
Blender Python MCP tool; do not assume Blender sees installed file paths. Compile each
independently into one shared globals/locals dictionary and call in that same request.
Carry reports as JSON between requests; assume no persistent execution namespace. Pass
the user's request to MCP and inspect returned text, not only isError.

Call `preview_pivot_copy(object_name, local_pivot=[x,y,z], geometry_tolerance=...,
scene_name=...)` with an explicit source and local point. Tolerance must be an explicit
finite positive coordinate-error bound from user/Profile intent, not this Skill's test
fixture value. Preview changes no IDs and returns a bounded source fingerprint; show the
predicted world origin and clarify whether that point is intended before applying.

Only after authorization for this exact relocation, call `apply_pivot_copy` with identical
point/tolerance/Scene, preview `source_sha256` as `expected_source_sha256`, an unused
explicit `result_name` (at most 63 UTF-8 bytes), and `authorized=True`. It creates
an independent Object/Mesh copy, translates copied vertices and origin so reported world
positions stay fixed. Scale/rotation, topology, UV states and shared material refs are
checked. It never applies scale to the source or chooses a pivot policy.

The narrow supported source is a simple positive-scale XYZ static polygon mesh in Object
mode. Reflections/zero scale, parents/children, delta transforms, rig/animation, modifiers,
constraints, vertex groups, Shape Keys, linked data, custom normals and unsupported attrs
refuse. Apply additionally refuses file-wide animation/constraints. Do not remove existing
dependencies to make a source pass. Missing/stale preview, no authorization or name
collision refuse; no-change still requires authorization/freshness.

If a copy is created, inspect source/output and check independent Mesh, world positions,
origin and retained UV/material refs. A failure removes only newly owned IDs when safe;
`failure_cleanup=unverified` requires exact-ID inspection before any retry. An uncertain
MCP result also requires reinventory. Coincident objects are expected; do not move/hide/
delete the source, save or export without a separate request. Reported matrices may be
stale; no graph refresh, evaluated geometry, normals/tangents, procedural appearance,
numerical conditioning, engine import or arbitrary concurrent callbacks are certified.
Blender 5.0.1 synthetic evidence covers only this narrow workflow.
