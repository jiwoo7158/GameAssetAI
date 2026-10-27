---
name: blender-inspect-animation
description: Inventory existing Blender Actions, animation bindings, NLA strips, drivers, keyframes, and explicitly mapped root-motion channels without edits. Use when reviewing animation data before cleanup, extraction, retargeting, Mixamo work, or Unity export; do not use it to import, rename, evaluate, bake, retarget, or modify animation.
---

# Inspect Animation

Analyze stored animation data only. Do not change frames, selection, mode, Actions, slots,
F-Curves, drivers, NLA tracks, objects, rigs, meshes, or files.

## Inputs

Use the current or named Scene. A named Object limits binding inspection to that Object,
its data, and Mesh Shape Keys; the Action inventory remains file-wide so unbound Actions
are visible. Accept root-bone names only as explicit data from the user, an earlier verified
mapping, or the active Workspace Profile. Never guess a root bone from naming.

## Execution

1. Inspect Blender addon and Scene state before executing code.
2. Read `scripts/inspect_animation.py` and execute it in one Blender MCP Python request.
   Use one shared dictionary for `exec` globals and locals, then call
   `inspect_animation(scene_name, object_name, root_bone_names)` in that same request.
   Do not assume definitions survive a later MCP call.
3. Treat the report as read-only inventory. Do not switch mode or evaluate the animation
   graph to obtain additional results.

## Interpretation

- `ok` means the bounded inventory completed; it does not mean the animation is valid.
- Report Actions including unused Actions, slots, F-Curve/key counts and stored frame
  ranges; report current bindings, drivers and NLA strips separately.
- Report bone root-motion channels only when their bone names were explicitly supplied.
  An Object-level location curve is reported only when a named Object was inspected.
- Cyclic means a stored F-Curve has a Cycles modifier. It does not certify a seamless loop.
- This result does not validate pose quality, loop continuity, root-motion policy, Action
  naming, retarget compatibility, Mixamo acceptance, Unity clip settings, or export.

State explicitly that Blender was not modified and identify any requested scope that this
inventory does not prove.
