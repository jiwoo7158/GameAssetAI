# Read-only asset inspection tests

Use `skills/blender-inspect-asset/scripts/inspect_asset.py` inside live Blender via MCP.
Do not run the helper with system Python or make Blender load repository-local paths.

Expected inputs: current/named scene, explicit names, scene/selection scope.
Expected outputs: `gameassetai.inspection.v1` inventory, or explicit error/partial result.

## Cases

- Current Cube: 8 base vertices, 6 polygons, 12 tessellated triangles, existing material.
- Empty scene: successful empty inventory.
- Empty selection, missing named object, missing scene: explicit error, no widened scope.
- Synthetic isolated scene: material, shared mesh data, modifier, two-bone armature,
  object Action, NLA reference, shape key. Verify relationships and file-wide Action label.
- Edit-mode fixture mesh: no stale count presented as verified; no forced mode change.
- Existing-asset preservation: compare current-scene/source fingerprints before and after
  helper calls and fixture teardown. Preserve selection, active object, mode, frame,
  topology, transforms, materials, bones, shape keys, and animation curves.

Fixtures are generated from native Blender data, contain no third-party assets, and are
removed only by exact IDs owned by the test invocation. Unexpected external fixture users
must abort cleanup rather than deleting unrelated data. Record actual outcomes in docs.
