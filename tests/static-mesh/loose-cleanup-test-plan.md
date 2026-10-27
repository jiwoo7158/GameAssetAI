# Loose geometry cleanup test plan

Use only invocation-owned synthetic Scene/Object/Mesh IDs in Object mode. Load exact
inspection helper/fingerprint and cleanup helper, then run run_loose_cleanup_tests.
Check preview and no-op create no IDs; isolate/wire categories require separate flags;
index-shifting removals retain surface positions/UV/material/smooth state; copied Mesh
is independent while shared original users remain unchanged. Inject a copied-mesh
write failure and a copied retained-surface validation failure; require rollback without
new ID leaks. Apply with the fingerprint retained from an explicit prior preview.
Check name collisions, invalid
inputs, Shape Keys, animation (target and unrelated file data), groups, unsupported
attributes and nonfinite state. Restore tracked datablock names and original fingerprint.
Require the preview source_sha256 before apply; missing/stale fingerprints refuse changes.
Nonidentity/unflushed nonfinite transforms and unchanged user Edit mode are covered.
Matching quad fixture checks 7→4 vertices, 5→4 edges, one retained face/UV and zero
remaining loose geometry; wire-only must retain all seven vertices including endpoints.

Helper may edit/delete only new copied BMesh elements. Never run cleanup on original
Cube or any production asset as a synthetic regression convenience. After native test
get screenshot and scene inventory; returned original scene must remain unchanged.
