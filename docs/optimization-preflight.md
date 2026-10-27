# Advisory static optimization preflight — 2026-09-16

## Scope and decision

After user-reported client inspection/diagnostics/preview and synthetic copy-apply outcomes
passed, added one development-only planning function, not a fourth Skill or decimator.
`scripts/plan_static_optimization.py` consumes `mesh-diagnostics.v1` base reports and an
explicit nonnegative integer target. It never reads Blender, parses Profile Markdown,
chooses a polygon budget, computes a decimation ratio, authorizes mutation or certifies
engine readiness. Repository scripts are not automatically installed Skill resources.

Read active Profile and live source again when rules matter. Supply a target only when
it is explicitly established by the user/Profile; other budgets do not silently become
optimization targets. With no target return `needs_target`. `within_target` means only
triangle count is within this target, not that the asset is game-ready.

Failed/incomplete or evaluated reports return `error`. Preservation sensitivity and
non-budget diagnostic errors return `blocked`; review findings require review. Triangle
budget excess alone is a planning motivation rather than a geometry defect. An excess
over a positive explicit target can return `candidate_for_copy_preview`, never permission
to apply. Zero target on a surface requires review rather than deleting all faces.

Inputs are trusted diagnostic output, not a complete independent schema validator or
live state certificate. Every plan reports `freshness: not_verified`,
`mutation_authorized: false`, `optimization_method: null`. No stale report may authorize
a later edit; no fingerprint binding or modifier/copy implementation exists yet.

## Offline use and tests

```powershell
python -B scripts/plan_static_optimization.py path/to/fresh-diagnostics.json --target-triangles 10
python -B -m unittest discover -s tests/scripts -p 'test_*.py' -v
```

Diagnostics JSON is an optional development artifact, not a required user `input/` folder.
Omit `--target-triangles` to preserve unknown target. Exit 1 means execution/input error;
exit 0 includes blocked/review/needs-target outcomes, so callers must inspect `status`.

Five offline test methods cover target absence/equality/excess/zero, invalid booleans/types,
preservation/review/error/budget separation, incomplete/failed/evaluated reports, unverified
counts, empty surfaces, immutable input, no method/authorization and unknown freshness.
Total development tools 30 passed; Workspace suite 43 passed/4 symlink-privilege skips.

## Direct live evidence

External MCP confirmed Blender 5.0.1, addon [1,7], protocol 7. Existing actual ZIP helpers
passed inspection 36 + diagnostics 73 + cleanup 57 = 166 checks again, fixtures removed.
Then independently compiled planner source in that isolated namespace; current Cube base
diagnostics fed the planner for targets None/10/12/20/0. Expected statuses all passed:
needs_target / candidate_for_copy_preview / within_target / within_target / needs_review.
All five plans have no method or authorization. Original fingerprint remained
`f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d`.
Targets 10/20 here are explicit development test inputs, not saved game Profile rules.

To reproduce via MCP: generate `prepare_blender_check.py --suite all --bundle-dir
.local/source-bundles/namespace-fix-20260916`; transmit its exact `code`. Separately compile
the exact planner source into the same globals/locals dictionary, and call
`plan_static_optimization(diagnose_mesh(explicit_object_name, evaluate=False), target)`.
Use the current user request on MCP calls, check errors and compare native inspector
fingerprint before/after. No dependency refresh, mode changes or original edits are needed
for the planner. Existing fixture suite still requires authorized synthetic tests.

## Next development boundary

Actual copy optimization needs a separate narrow design/fixture unit: representative UV
seams/material boundaries, silhouette goals, verified live modifier capabilities, bounded
source fingerprint and independent copy, no-overwrite, validation/rollback. Triangle target
alone cannot define visual quality. Do not enlarge loose cleanup into automatic decimation,
apply transforms, touch rigs/actions or release this advisory tool as an optimization Skill.

The first bounded experiment is specified in
`tests/static-mesh/optimization-test-plan.md`. Native capabilities and protected-boundary
behavior still require connected Blender tests. Coplanar dissolve can leave triangles
unchanged; edge/polygon reduction must not be reported as meeting a triangle target.
