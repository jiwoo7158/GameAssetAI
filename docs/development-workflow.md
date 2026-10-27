# Development Workflow

## Goal

Develop GameAssetAI through small verified increments.

## Offline foundation gate

Before requiring Blender, run repository validation and the isolated regression suite:

```bash
python -B scripts/validate_repo.py
python -B -m unittest discover -s tests/workspace -p "test_*.py" -v
python -B -m unittest discover -s tests/scripts -p "test_*.py" -v
```

Workspace creation/configuration can be tested before the environment phase. See
`docs/workspace-contract.md`. Passing offline tests does not prove Blender behavior or
Codex runtime profile awareness. Both foundation phases remain required before treating
profile-dependent production asset workflows as validated. Under the current user request,
profile-independent read-only inspection/diagnostics were implemented and tested first;
their source evidence is not proof that the installed client reads Profiles correctly.

## Phase 1 — environment verification

Before writing production skills:

- have the user configure/connect the chosen Blender MCP as an external tool
- verify Codex can inspect the Blender scene
- verify Codex can make a harmless object change
- verify Blender Python execution if supported
- record tool limitations

Document findings under `docs/`.
Use `docs/blender-verification.md` for safe preparation, checks, and the evidence record.

## Phase 2 — workspace workflow

Validate:

- workspace creation
- profile creation
- active-profile switching
- project-path mapping
- reading game-specific rules from the active profile

Only after this works should asset skills depend on profiles.
The offline suite checks file-level behavior; manually verify Codex's actual profile reading
and switching in the generated workspace before considering this workflow fully validated.

Explicit current-session reading/switching to live diagnostics has now passed;
`docs/profile-workflow-validation.md` records exact restoration. Automatic Skill
discovery and fresh Workspace Profile A/B/null behavior subsequently passed by user report.
Raw routing/client-build evidence remains separate. Keep direct native evidence and user
reports distinguishable; do not repeat passed client gates.

## Phase 3 — first production skill

Choose one narrow workflow.

Recommended first candidates:

- inspect current Blender scene as a game asset
- validate a static mesh
- prepare an existing static mesh for Unity

Do not start with the hardest character / retargeting problem.

This section records the repository's original bootstrap order. The current continuation is
governed by `docs/PROJECT_AUDIT.md`, `docs/IMPLEMENTATION_MEMORY.md` and the active section of
`docs/roadmap.md`; do not restart historical Phase 3 merely because it appears here.

## Significant-change work package

Before a new Skill or major Skill revision, record in the active roadmap/session state:

- requirement IDs and the concrete missing capability;
- the existing Skill/helper that owns the responsibility;
- Blender-native, existing GameAssetAI, open-source and custom alternatives considered;
- non-goals, affected files and approval boundaries;
- focused tests, representative Blender asset and success/failure criteria.

External software review is read-only research. Installation and pipeline integration remain
separate user-approved changes. Prefer an adapter behind the existing Skill owner instead of a
parallel Skill that duplicates the same task.

## Phase 4 — regression

For every skill change:

1. read the relevant test plan
2. run the skill against representative data
3. inspect Blender results
4. record failures
5. update skill / script
6. re-test

## Phase 5 — local installation

When a skill is stable:

- ensure its directory is self-contained
- remove personal paths
- verify documentation
- install/update only the verified Skill in the personal Workspace/client
- confirm local exposure, invocation and regression behavior

External/public release packaging and Git tagging are out of current scope.

## Development rule

If reality in Blender contradicts the documentation, update the documentation.

The repository should describe tested behavior, not hoped-for behavior.
# Visible review artifact lifecycle

Automated fixtures and user-facing work are different lifecycles.

- Automated fixtures use isolated temporary Scenes and are removed after assertions.
- A user-facing modeling task keeps exactly one current review candidate in a named Workbench
  Scene when that is useful for review. Supporting camera, lights and a candidate rig may be part
  of that review state.
- Revise the current candidate in place when safe. For risky changes, make one temporary owned
  backup and remove it after successful verification.
- Do not reset the visible result to the default Cube after every check.
- Do not accumulate every model revision in the active Scene.
- This is a recoverability convention, not a user requirement to keep a particular Object, Scene
  or Blender process open. A verified checkpoint permits replacement or restart when the work
  package needs it. Preserve major recovery points as separate `.blend` checkpoints when a
  destination has been agreed.

