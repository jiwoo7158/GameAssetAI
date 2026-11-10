# Quality and Testing

## Foundation tests

Offline tests use temporary directories and verify catalogs, specifications, Workspace safety,
Profile persistence, output-tree independence, package hashes, installed runtime execution,
field-level Profile updates, link-safe output and installation paths, no-overwrite install, backup
update, retained Blender contract validators, and repository layout. Repository validation also
checks that all four required Skill entrypoints are Git-tracked, not merely present locally.

```powershell
python -B -m unittest discover -s tests -p "test_*.py" -v
python -B scripts/validate_repo.py
```

These tests do not prove visual asset quality, live MCP behavior, Codex discovery, Blender Add-on
survival, or engine runtime behavior.

`.github/workflows/ci.yml` runs both commands on `ubuntu-latest` and `windows-latest` with Python
3.10 for pushes and pull requests. CI uses no paid API, secret, user Workspace, Unity project, or
generated asset input. A workflow definition and local pass are not a claim that a particular
remote run succeeded; link the actual GitHub Actions run when reporting remote CI status.

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
