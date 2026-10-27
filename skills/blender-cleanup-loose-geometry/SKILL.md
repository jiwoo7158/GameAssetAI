---
name: blender-cleanup-loose-geometry
description: Preview and optionally remove explicitly unwanted isolated vertices or wire edges from a separate copy of an existing simple Blender mesh. Preserve the original; not merge-by-distance, surface repair, rig cleanup, modifier application, or export.
---

# Clean explicitly unwanted loose geometry on a copy

When loading helper source with `exec`, use one dictionary for both globals and locals:
`namespace = {}; exec(compile(helper_source, "<cleanup-helper>", "exec"), namespace, namespace)`.
Call `namespace["cleanup_loose_geometry"](...)` in that same MCP request. Separate
globals/locals can leave imports unavailable to helper functions. Compile each source
separately; do not concatenate future-import-bearing files or rely on earlier MCP
call namespaces. Carry the preview fingerprint as JSON data, not a surviving function.

Read the scene/addon status through live MCP first. Use an explicit source object name;
missing selection is not permission to choose another object. Loose geometry may be
intentional. A request merely to inspect or optimize does not authorize removing it.
Clarify which categories are unwanted if the request does not establish that.

Read [scripts/cleanup_loose.py](scripts/cleanup_loose.py), transmit its exact source to
Blender Python execution in a separate namespace, and call `cleanup_loose_geometry`.
Do not assume Blender can open local installed paths. Pass the actual user request to
MCP tools where required and inspect error text even when isError is false.

Start with `apply=False`. Explicit options `remove_isolated_vertices` and
`remove_wire_edges` default to False. The preview lists affected source indices and
counts and makes no copy. Removing a wire edge does not implicitly authorize removing
its now-isolated endpoints: those remain unless isolated-vertex removal was also requested.

After preview, use `apply=True` only when the user's request authorizes that exact
cleanup. Pass the preview's `source_sha256` as `expected_source_sha256`; missing/stale
fingerprints refuse changes. Supply a globally unused explicit `result_name`; existing names are refused,
not overwritten or auto-suffixed. The helper makes independent Object/Mesh datablocks,
edits only the copied BMesh, validates retained face positions/UV/material/smooth flags,
then links the result to the explicitly targeted Scene root collection. It never
changes active object/selection/mode/transforms, hides originals, applies modifiers,
or saves/exports. Materials remain shared references; this is not a deep material backup.

Re-read active Workspace Profile before game-specific conclusions or follow-up work.
This cleanup has no triangle/engine/art defaults. Profile budgets do not authorize
topology deletion, and unknown rules stay unknown. Do not run repository tests on
valuable data just to use the Skill: tests create separate synthetic fixtures.

## Output and validation

Schema `gameassetai.loose-cleanup.v1` reports `status`, explicit source/options, source
indices, counts, and output names/token when created. `preview` and `no_change` are
valid outcomes. No applicable removal means no new datablocks even with apply=True.
After success inspect both source and copy, verify original geometry unchanged and
copied Mesh independent, then obtain viewport screenshot and scene inventory.
Coincident overlapping copies are expected because transforms are preserved; do not
move/hide/delete an original simply to make the screenshot clearer.

## Failure boundary

- Object-mode only; edit data is not flushed and user mode is never forced.
- Refuse linked/override data, parents/children, modifiers/constraints, Shape Keys,
  vertex groups, object/mesh animation, custom normals, and unsupported generic
  attributes. File-wide animation/constraints block apply conservatively to avoid
  dependency refresh changing existing animated source properties. Preview remains
  available only for supported simple source meshes.
- Refuse nonfinite coordinates/transforms, empty face surfaces and invalid names/options.
- On failed creation/validation/linking, discard only exact new invocation-owned IDs
  if no external links/users appeared. Cleanup uncertainty is explicitly reported;
  never remove an existing source, rig, Action, or wildcard-matched object.
- Do not automatically re-run apply after an uncertain MCP result. Reinspect Scene and
  output name/token to avoid creating duplicates. Source/index lists can change between
  preview and apply: re-preview if source state changes.

Blender 5.0.1 synthetic fixture verification is recorded in the development repository.
This is limited loose-geometry cleanup, not a watertightness/manifold/engine-readiness
guarantee or compatibility certificate for imported rigs, custom attributes or add-ons.
