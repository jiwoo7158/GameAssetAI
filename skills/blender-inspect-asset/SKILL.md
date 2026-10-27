---
name: blender-inspect-asset
description: Inspect the current Blender scene or explicitly targeted game assets without editing them. Use for object, base mesh, material, armature, and existing animation inventories, not asset creation, cleanup, rigging, retargeting, or export.
---

# Inspect Blender game assets

When loading helper source with `exec`, use one dictionary for both globals and locals:
`namespace = {}; exec(compile(helper_source, "<asset-helper>", "exec"), namespace, namespace)`.
Call `namespace["inspect_scene"](...)` in that same MCP request. Separate globals/locals
can leave imports unavailable to helper functions. Compile each source separately;
do not concatenate future-import-bearing files or rely on earlier MCP call namespaces.

## Scope and inputs

Report observable scene/data facts without changing selection, mode, transforms, meshes,
rigs, Actions, or files. Inputs are the current scene, an explicit scene name, explicit
object names, or an explicit request to inspect selected objects. Never substitute the
whole scene when a selected/named target is missing.

## Procedure

1. Discover the live Blender tools. In the tested MCP implementation, use
   `get_addon_status` and `get_scene_info` before code execution. Check tool-level results
   for error text even if `isError` is false. Do not install or reconfigure MCP.
2. If game-specific conclusions are requested, re-read the workspace's
   `config/active-profile.json` and its exact-case `profiles/<stem>.md`. Missing/unspecified
   rules are unknown. Factual inventories need no active profile; do not invent engine,
   style, polygon budget, rig preference, or export destination.
3. Read [scripts/inspect_asset.py](scripts/inspect_asset.py). Send its exact source through
   the available Blender Python-execution tool, then call `inspect_scene(...)` in that
   same execution namespace and print the returned dictionary as JSON. Local Python is
   not Blender; do not run this helper locally expecting a scene connection. Do not assume
   Blender can open the installed skill's local path. Pass the user's actual request to
   MCP tools where required.

   Example appended to the helper source:

   ```python
   print(json.dumps(inspect_scene(scope="scene"), ensure_ascii=False, allow_nan=False))
   ```

   Use `scope="selected"` only when selection is the intended target. For named targets,
   use `inspect_scene(object_names=["name supplied by the user"])`. Use an explicit
   `scene_name` only when requested; named objects must belong to that scene.
4. Check `status`, `errors`, and per-object uncertainties before reporting. Compare names
   and counts against the tool's scene inventory; a summary tool may be truncated. Native
   scene inventory is authoritative for the helper's explicit scope, not the entire file.
   Screenshot confirmation is useful when available, not a reason to change visibility
   or selection. State discrepancies rather than silently continuing.

## Outputs and validation

Return a concise inventory matching the requested scope. Include mesh counts and relevant
material/rig/animation dependencies only when useful. Distinguish base topology from final
evaluated/exported topology; modifiers are listed, not applied.
Source transforms/matrices reflect stored/cached state; this helper does not refresh the
dependency graph to resolve unsynchronized animation or dependency-driven transforms.
Material entries describe referenced datablocks, not engine compatibility. Armature entries describe rest bones,
not deform quality or Humanoid/Mixamo certification. Existing rigs/animations are inputs,
not invitations to replace them.

The helper returns schema `gameassetai.inspection.v1`: scene/scope/targets, objects,
referenced materials, and a separately labeled file-wide Action inventory. Object and
data animation links include current Action/slot and NLA strips. Successful empty-scene
inventory is valid; empty selection and missing named targets are explicit errors.
Validation must confirm target names, scope, count consistency, and no source changes.

## Failure behavior and limitations

- Without trustworthy Python execution, return the verified subset from live tools and
  explicitly list unavailable fields. Do not present it as the full helper result.
- Edit-mode mesh counts are withheld rather than flushing edits or changing mode.
- Edit-mode rest bones are also withheld; nonfinite numerical fields become null with a
  partial/error explanation instead of invalid JSON or an unqualified success.
- Individual inspection failures produce `partial`, never an unqualified success.
- The scene lists datablock objects, not dependency-graph instances or engine-ready assets.
- Actions are file-wide, may be unused, and are not assumed to belong to every target.
  Slot/layer metadata is feature-detected; keyframe contents/retargeting are not inspected.
- No evaluated mesh, pose-quality, UV-quality, self-intersection, export, or performance
  certification is implied. Tested on Blender 5.0.1; other versions require revalidation.
- Preservation tests use synthetic fixtures and source fingerprints. They do not establish
  compatibility with every imported rig or animation format.

No destructive operations or external file writes are part of this skill.
