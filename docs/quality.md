# Quality and Testing

## Foundation tests

Offline tests use temporary directories and verify catalogs, specifications, Workspace safety,
Profile persistence, output-tree independence, package hashes, installed runtime execution,
field-level Profile updates, link-safe output and installation paths, no-overwrite install, backup
update, local Blender-environment contracts, legacy isolation, and repository layout. Output tests cover explicit
experiment selection, catalog categories, active-game matching, current-maximum numbering,
concurrent claims, partial/complete deletion, exact continuation, and legacy read-only validation.
Profile tests cover unknown and dimension-mismatched style ids plus failed-update preservation.
Distribution tests cover the required Workspace-before-project-Skill onboarding order. Repository
tests also build a cloneable Workspace distribution, initialize it without replacing partial
personal state, copy the same Skills to user scope, simulate a normal fast-forward Pull, and verify
line-ending-stable hashes. Output tests cover output-root precedence and deletion, official
artifact paths, concurrent registration, atomic failed updates, review-state transitions, and
Windows Junction rejection. Repository validation checks that all four Skill entrypoints are
Git-tracked, that `/output/` is anchored in `.gitignore`, and that no development result is tracked.
An archive-independence regression copies the product into a separate temporary checkout without
`archive/`, initializes a temporary Git index, and reruns repository validation plus the complete
formal suite. That child suite builds and executes the four-Skill bundle and Workspace
distribution, proving that historical Blender code is not a hidden product dependency.

```powershell
python -B -m unittest discover -s tests -p "test_*.py" -v
python -B scripts/validate_repo.py
```

These tests do not prove visual asset quality, live MCP behavior, Codex discovery, a Blender
Add-on, or engine runtime behavior. Historical tests under `archive/legacy/` are not run by formal
CI and are not counted as current capability evidence.

`.github/workflows/ci.yml` runs both commands on `ubuntu-latest` and `windows-latest` with Python
3.10 for product-branch pushes and pull requests (excluding generated `dist/workspace` pushes),
then builds and validates the generated Workspace tree in the
runner's temporary directory. CI uses no paid API, secret, user Workspace, Unity project, or
generated asset input. `.github/workflows/publish-workspace.yml` is separate: only a successful
`master` push can grant its job `contents: write`, and it re-runs the complete offline gate before
appending a normal commit to `dist/workspace`. A workflow definition and local pass are not a
claim that a particular remote run or publication succeeded; link the actual GitHub Actions run
when reporting remote status.

## Production acceptance

Use five distinct evidence gates:

1. **Environment execution:** the selected executable/tool starts, reports its version, and
   propagates errors. This proves no asset behavior.
2. **Structural test:** schemas, paths, topology/metadata, preservation, and deterministic helper
   contracts pass. Synthetic fixtures remain `tested` only.
3. **Representative execution:** the current workflow runs on a semantically relevant asset and
   records reproducible inputs; this still does not grant visual acceptance.
4. **Visible/semantic acceptance:** reviewed views and game-use invariants pass with registered
   evidence, producing `accepted`.
5. **Engine proof:** the accepted exported artifact passes the intended engine import/runtime gate.

Never skip a gate by citing an archived helper, old contract test, successful render, or file
existence. The 2026-11-13 Blender 5.2.4 diagnostic reaches gate 1 only.

Every new generator or material revision needs a representative asset and defined visible
invariants. Validate source preservation and structure, inspect relevant Blender views, record an
explicit accept/reject result, and stop downstream work on rejection. Synthetic cubes are suitable
for plumbing only.

For engine claims, export the actual accepted artifact and verify the intended engine import and
runtime behavior. For 2D claims, review framing, silhouette, direction consistency, frame timing,
palette/readability, and sheet layout rather than merely checking PNG dimensions.

Task status follows the same boundary. `complete` means publication ended, not that quality was
accepted. `accepted` or `rejected` requires a recorded visible/semantic review summary and one or
more distinct registered artifacts. Each evidence path is rechecked at transition time as an
existing nonempty real file safely inside the task; invalid evidence leaves the Manifest unchanged.
Unit tests use synthetic bytes to verify this contract and are never quality evidence. Later
movement/deletion does not retroactively erase a recorded decision or block independent work.

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

Result-tree deletion tests prove Runtime independence, not Blender-file portability. A future
representative `.blend` movement test must inventory external images, linked libraries, textures,
caches, and other dependencies, choose relative-path or packed-resource policy deliberately, and
reopen the moved file before claiming portability.
