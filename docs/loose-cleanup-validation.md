# Loose geometry copy-cleanup validation — 2026-09-16

## Decision / tested boundary

After real Workspace Profile switching and both existing source workflows passed,
selected one low-dependency existing-asset operation: remove explicitly unwanted
isolated vertices/wire edges only on an independent Mesh/Object copy. No merge, surface
repair, rig editing, transform application, engine export, or assumed game rules.
Source `skills/blender-cleanup-loose-geometry/`, tests `tests/static-mesh/run_loose_cleanup.py`.

Windows, Blender 5.0.1, external user-identified ahujasid/blender-mcp, addon [1,7], protocol 7.
No source/MCP installation or telemetry setting change. Original unsaved Scene retained.

## Failures and improvements

- Initial ad-hoc source concatenation hit Python future-import placement SyntaxError.
  Nothing executed. Added loose-cleanup suite to the existing payload builder, which
  independently compiles each exact source in a shared isolated test namespace.
- First native preview rejected default Blender selection attributes as generic data.
  Queried real native attributes; added only observed built-in selection/UV-selection
  names to a strict allowlist. Arbitrary custom attributes remain refused.
- Expanded tests for nonidentity transforms, unflushed nonfinite local rotation,
  parent/modifier/mode guards and actual unrelated-animation guard error provenance.
- Apply now requires source_sha256 from a preview; missing/stale fingerprints refuse
  new IDs. The bounded hash covers source names, geometry, retained surface/UV/material
  references and transforms, not every possible datablock/custom property.

## Latest live results

**57 checks passed**, original fingerprint and all tracked names restored after exact
fixture teardown. Separate UUID-owned Scene/Object/Mesh/material/Action IDs only.

- Preview/no-op produce no new IDs. Isolated vs wire categories require separate flags.
- Source has isolated first vertex, surface triangle with distinct UV coordinates,
  and separate wire edge/endpoints. Both categories removed: 6 vertices/4 edges/1 face
  become 3/3/1, with retained face positions/UV/material/smooth state unchanged.
- Wire-only cleanup keeps its endpoints; isolated-only cleanup keeps wire geometry.
- Added user-workflow quad fixture: vertices 7→4, edges 5→4, one face and UV retained,
  independent output, zero remaining loose geometry. Quad wire-only keeps all 7 vertices.
- User separately reported synthetic instruction-led preview/apply/restore success;
  see `skill-session-validation.md` for provenance and the remaining routing boundary.
- Shared source Mesh remains unchanged for both original users. Output Mesh is independent.
  Editing copied vertex coordinates cannot affect either source object.
- Materials remain intentionally shared; no deep material backup claim.
- Simulated copied-mesh write failure: only new owned Object/Mesh IDs rolled back,
  no ID leak. Name collisions, invalid inputs, missing/stale preview fail without overwrite.
- Explicit prior-preview fingerprint is passed directly to apply. Deliberately changed
  copied retained surface fails validation and rolls back owned IDs without leaks.
- Shape Keys, vertex groups, object animation, unrelated file animation, parent/modifier,
  unsupported generic attributes, nonfinite data and Edit mode all refuse changes.
- Native/tool Scene still Cube, Light, Camera and viewport confirms original objects
  after initial successful teardown. No original user asset was cleaned/saved/exported.

## Remaining limitations

Linked/override imports, custom normals, every generic Attribute, embedded external
dependency callbacks and every Blender version are not certified. The allowlist and
retained-face validation intentionally favor refusal over silent attribute loss.
Original materials gain an extra reference if output is retained; that is expected.
Temporary tests may dirty a clean file; no clean-dirty-flag preservation guarantee.
No independent screenshot of each overlapping synthetic copy; native geometry validation
is stronger than visual overlap for this particular operation.

This is a narrow source-workflow verification, not full optimization/game readiness.
Automatic installed-client trigger/selection remains separate from source/native tests.
