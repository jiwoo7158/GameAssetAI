# Quality and Testing

## Foundation tests

Offline tests use temporary directories and verify catalogs, specifications, Workspace safety,
Profile persistence, output-tree independence, package hashes, installed runtime execution,
field-level Profile updates, link-safe output and installation paths, no-overwrite install, backup
update, retained Blender contract validators, and repository layout. Output tests cover explicit
experiment selection, catalog categories, active-game matching, current-maximum numbering,
concurrent claims, partial/complete deletion, exact continuation, and legacy read-only validation.
Profile tests cover unknown and dimension-mismatched style ids plus failed-update preservation.
Distribution tests cover the required Workspace-before-project-Skill onboarding order. Repository
validation also checks that all four Skill entrypoints are Git-tracked, that `/output/` is anchored
in `.gitignore`, and that no development result is tracked.

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

## Development experiments and temporary test artifacts

Development asset experiments may be stored locally under
`output/experiments/<experiment>/<category>/<asset>/<number>-<purpose>/`; `/output/` is ignored and
optional. Each experiment records its validation purpose locally, but neither it nor its task
manifests are a global registry. Moving or deleting any part is valid and must not affect new
independent work, source, tests, or packaging.

Do not commit `.blend`, `.fbx`, generated `.png`, package bundles, Workspace outputs, or development
experiment directories. Unit/integration tests use operating-system temporary directories and do
not create Repository `output/` or write to a real user Workspace. Any manually retained
representative evidence records provenance and reproduction instructions without becoming a
runtime dependency.
