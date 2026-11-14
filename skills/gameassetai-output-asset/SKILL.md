---
name: gameassetai-output-asset
description: Classify and allocate safe numbered development or Workspace result paths, continue exact in-progress tasks, and publish bounded deliverables from accepted sources.
---

# GameAssetAI Output Asset

Use this Skill whenever a creation, revision, preview, comparison, or publication needs an official
result path. Route Workspace/Profile administration to `gameassetai-workspace`; route source
creation or revision to the matching Skill. Export or final publication still requires a source
that passed explicit visible and semantic review.

Resolve the CLI before running a command. From a project-scoped distribution root use
`$GameAssetAICli = ".agents/skills/gameassetai-workspace/scripts/gameassetai.py"`; at user scope
use the actual copied `gameassetai-workspace/scripts/gameassetai.py`. Development experiments run
from a development Repository with `$DevelopmentCli = "scripts/gameassetai.py"`. A distribution
Workspace does not contain that development-only root `scripts/` directory.

## Classify before allocation

1. Decide the storage domain. Development research uses the Repository
   `output/experiments/`; real game work uses a user Workspace `outputs/`; ordinary tests use an
   operating-system temporary directory and do not invoke production allocation.
2. For development work, inspect existing experiment metadata:

   ```powershell
   python -B $DevelopmentCli outputs experiment list <repository>
   ```

   Reuse an experiment only when the validation purpose, core question, and evaluation criteria
   match. A revision, retry, or method comparison under that same goal stays in the experiment.
   A different question or acceptance criterion requires a new descriptive experiment. Never
   select by similar name alone. When the request is ambiguous, ask the minimum clarification;
   do not create or reuse a default.

   ```powershell
   python -B $DevelopmentCli outputs experiment create <repository> <experiment-id> `
     --purpose <text> --question <text> --criterion <text>
   ```

3. Use one catalog top-level category: `character`, `equipment-prop`, `environment`, or
   `vfx-mesh`. The asset id identifies the concrete target, not its version. The purpose identifies
   this individual result.
4. Allocate a new task through the Runtime:

   ```powershell
   # Development experiment
   python -B $DevelopmentCli outputs begin <repository> --space development `
     --experiment <experiment-id> --category <category> --asset <asset-id> --purpose <purpose>

   # User game work; game defaults to the active Profile and an explicit --game must match it
   python -B $GameAssetAICli outputs begin <workspace> --space workspace `
     --category <category> --asset <asset-id> --purpose <purpose>

   # One-task external root; it must already exist and be explicitly selected
   python -B $GameAssetAICli outputs begin <workspace> --space workspace `
     --category <category> --asset <asset-id> --purpose <purpose> `
     --output-root <absolute-directory>
   ```

   This creates `<number>-<purpose>/manifest.json` with no artifact subfolders. It uses the current
   maximum number under that asset plus one and claims the directory atomically. Do not use dates,
   times, UUIDs, generic `test`/`final` names, or add another classification level.
5. Continue work only from the exact in-progress task path:

   ```powershell
   python -B $GameAssetAICli outputs continue <exact-task-path> [--workspace <workspace>]
   ```

   A completed, accepted, or rejected result must remain unchanged; allocate a new number for a
   new comparable result. If the exact task or a recorded artifact was moved/deleted, report that
   continuation failure and do not recreate it.
6. Create only the artifact directory needed by the next file and obtain its no-overwrite path
   through the Runtime:

   ```powershell
   python -B $GameAssetAICli outputs artifact-path <task> `
     --kind <model|preview|sprite|export> --filename <descriptive-name.ext> `
     [--workspace <workspace>]
   ```

   The official directories are `models/`, `previews/`, `sprites/`, and `exports/`. Planning
   atomically records a task-local reservation, so a second worker cannot claim the same relative
   path. Publish the actual file without overwriting, then register that existing nonempty file;
   registration consumes the reservation:

   ```powershell
   python -B $GameAssetAICli outputs register <task> <artifact> `
     [--workspace <workspace>]
   ```

   If production is abandoned before a file exists, release only that unused reservation:

   ```powershell
   python -B $GameAssetAICli outputs release <task> <relative-artifact> `
     [--workspace <workspace>]
   ```

   Releasing is refused when a file exists at the reserved path; register or explicitly inspect
   that file instead.

   Asset Specification formats are logical requests: `blend` maps to model `.blend`, `fbx` to
   export `.fbx`, plain `png` to preview or sprite `.png`, and `sprite-sheet`/`png-sequence` to
   sprite `.png`. The artifact registry can safely store additional existing export/preview
   extensions, including GLB/GLTF/OBJ and JPG/WebP. Registration support is not a claim that a
   generator, Blender exporter, or engine import workflow for those formats is implemented.

7. Change state only through `outputs status`. Outstanding artifact reservations must be resolved
   before a state change. `complete` means file production ended without a quality decision.
   `accepted` or `rejected` requires a real visible/semantic review summary and one or more
   distinct registered evidence paths. At the transition, every evidence path must still resolve
   to a nonempty real file inside the task, without a link or Junction component. Invalid evidence
   leaves the Manifest unchanged:

   ```powershell
   python -B $GameAssetAICli outputs status <task> complete [--workspace <workspace>]
   python -B $GameAssetAICli outputs status <task> accepted `
     --review-summary <text> --review-evidence <relative-artifact> `
     [--workspace <workspace>]
   ```

   Tests and successful file creation never justify `accepted`. Accepted/rejected tasks are
   terminal; a completed task may receive a later accepted/rejected review but cannot receive new
   artifacts. Moving or deleting evidence after a successful review preserves the historical
   decision and does not block an independent new task.

   Manifest mutation uses `.gameassetai-manifest.lock` in the task. Normal completion and handled
   exceptions remove it. On a busy error, do not delete the lock while another process may be
   active. If abnormal termination is suspected, first confirm no process is using that exact task
   and inspect the recorded PID and Manifest; the Runtime does not delete stale-looking locks.

The default user root is `<workspace>/outputs`. A one-task `--output-root` overrides a Profile
`output_defaults.root`, which overrides the Workspace preference, which overrides that default.
External roots must exist and be explicitly selected; never infer them from project bookmarks or
silently recreate a moved/deleted root. External validation and continuation require the owning
Workspace so its Workspace id and Profile can be checked.

`GameAssetAI-Tools` and `.local/external-tools.json` are external-tool management state, never an
asset output root or task hierarchy. Do not store generated models, previews, sprites, exports, or
task Manifests there merely because a tool produced them. Use the normal Runtime-selected output
root and preserve the same no-overwrite lifecycle.

The allocator rejects link/reparse-point components, path escape, unknown categories, active-game
mismatches, unidentified experiments, and collisions. Manifests are local descriptions, not hidden
product state. Users may move or delete any part of either result tree; this removes those copies
but must not damage code, Profiles, settings, catalogs, installed Skills, packaging, validation, or
independent future work. A prior result becomes input only when the user explicitly selects it.

Artifact registration supports file lifecycle management, not production implementation. The
active product currently makes no helper-based claim for FBX preparation, PNG rendering,
quantization, or sprite-sheet assembly; historical candidates are isolated outside the package.
Do not infer Unity setup, material round trips, autonomous pixel-art direction, or an accepted
end-to-end eight-direction workflow from an allowed extension or output directory.

For a new 3D asset, plan the editable `.blend` as the first primary model artifact unless the user
explicitly selects another bounded source contract. Allocate exports and 2D products later as
separate explicit results; do not let a downstream artifact replace the preserved source.

Moving a task is valid product data management, but do not claim an individual `.blend` is portable
until its external textures, linked libraries, images, caches, and other dependencies were
inspected. Use reviewed relative paths or Blender resource packing only when appropriate and
verify the moved representative file before making a portability claim.

An AI concept/reference image supplied before modeling, a Blender preview rendered for review,
and a final game PNG/pixel sprite/sprite sheet are distinct artifacts. Do not infer an export
destination from a project bookmark. Use UnityWorkbench only when explicitly requested, and never
make a later run depend implicitly on an earlier output directory.
