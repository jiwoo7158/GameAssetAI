---
name: gameassetai-output-asset
description: Classify and allocate safe numbered development or Workspace result paths, continue exact in-progress tasks, and publish bounded deliverables from accepted sources.
---

# GameAssetAI Output Asset

Use this Skill whenever a creation, revision, preview, comparison, or publication needs an official
result path. Route Workspace/Profile administration to `gameassetai-workspace`; route source
creation or revision to the matching Skill. Export or final publication still requires a source
that passed explicit visible and semantic review.

## Classify before allocation

1. Decide the storage domain. Development research uses the Repository
   `output/experiments/`; real game work uses a user Workspace `outputs/`; ordinary tests use an
   operating-system temporary directory and do not invoke production allocation.
2. For development work, inspect existing experiment metadata:

   ```text
   python scripts/gameassetai.py outputs experiment list <repository>
   ```

   Reuse an experiment only when the validation purpose, core question, and evaluation criteria
   match. A revision, retry, or method comparison under that same goal stays in the experiment.
   A different question or acceptance criterion requires a new descriptive experiment. Never
   select by similar name alone. When the request is ambiguous, ask the minimum clarification;
   do not create or reuse a default.

   ```text
   python scripts/gameassetai.py outputs experiment create <repository> <experiment-id> \
     --purpose <text> --question <text> --criterion <text>
   ```

3. Use one catalog top-level category: `character`, `equipment-prop`, `environment`, or
   `vfx-mesh`. The asset id identifies the concrete target, not its version. The purpose identifies
   this individual result.
4. Allocate a new task through the Runtime:

   ```text
   # Development experiment
   python scripts/gameassetai.py outputs begin <repository> --space development \
     --experiment <experiment-id> --category <category> --asset <asset-id> --purpose <purpose>

   # User game work; game defaults to the active Profile and an explicit --game must match it
   python scripts/gameassetai.py outputs begin <workspace> --space workspace \
     --category <category> --asset <asset-id> --purpose <purpose>
   ```

   This creates `<number>-<purpose>/manifest.json` with no artifact subfolders. It uses the current
   maximum number under that asset plus one and claims the directory atomically. Do not use dates,
   times, UUIDs, generic `test`/`final` names, or add another classification level.
5. Continue work only from the exact in-progress task path:

   ```text
   python scripts/gameassetai.py outputs continue <exact-task-path>
   ```

   A completed, accepted, or rejected result must remain unchanged; allocate a new number for a
   new comparable result. If the exact task or a recorded artifact was moved/deleted, report that
   continuation failure and do not recreate it.
6. Create only artifact directories actually needed by this task. Execute the bounded
   exporter/renderer only after its source is accepted, keep manifest artifact paths relative to
   the task, validate the task, and report the exact path. Never overwrite an existing artifact.

The allocator rejects link/reparse-point components, path escape, unknown categories, active-game
mismatches, unidentified experiments, and collisions. Manifests are local descriptions, not hidden
product state. Users may move or delete any part of either result tree; this removes those copies
but must not damage code, Profiles, settings, catalogs, installed Skills, packaging, validation, or
independent future work. A prior result becomes input only when the user explicitly selects it.

Current helpers cover bounded static and Generic animated FBX preparation, deterministic
static/action PNG rendering, batch coordination, quantization, and sprite-sheet assembly. They do
not prove Unity Humanoid Avatar setup, every material round trip, autonomous pixel-art direction,
or an accepted end-to-end eight-direction workflow.

An AI concept/reference image supplied before modeling, a Blender preview rendered for review,
and a final game PNG/pixel sprite/sprite sheet are distinct artifacts. Do not infer an export
destination from a project bookmark. Use UnityWorkbench only when explicitly requested, and never
make a later run depend implicitly on an earlier output directory.
