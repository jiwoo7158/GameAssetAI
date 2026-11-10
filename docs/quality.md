# Quality and Testing

## Foundation tests

Offline tests use temporary directories and verify catalogs, specifications, Workspace safety,
Profile persistence, output-tree independence, package hashes, installed runtime execution,
no-overwrite install, backup update, retained Blender contract validators, and repository layout.

```powershell
python -B -m unittest discover -s tests -p "test_*.py" -v
python -B scripts/validate_repo.py
```

These tests do not prove visual asset quality, live MCP behavior, Codex discovery, Blender Add-on
survival, or engine runtime behavior.

## Production acceptance

Every new generator or material revision needs a representative asset and defined visible
invariants. Validate source preservation and structure, inspect relevant Blender views, record an
explicit accept/reject result, and stop downstream work on rejection. Synthetic cubes are suitable
for plumbing only.

For engine claims, export the actual accepted artifact and verify the intended engine import and
runtime behavior. For 2D claims, review framing, silhouette, direction consistency, frame timing,
palette/readability, and sheet layout rather than merely checking PNG dimensions.

## Temporary development artifacts

Do not commit `.blend`, `.fbx`, generated `.png`, package bundles, or experiment directories.
Tests use operating-system temporary directories. Any manually retained representative evidence
must record provenance and reproduction instructions in the work package without becoming a
runtime dependency.
