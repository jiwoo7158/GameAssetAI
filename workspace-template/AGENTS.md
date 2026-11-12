# GameAssetAI Workspace Instructions

This is a persistent user Workspace, not the GameAssetAI development repository. Durable game
rules live in JSON Profiles, not in chat memory.

Codex reasoning may direct Blender native operations and write bounded task-specific code for the
current asset. Do not require a prewritten generator for every asset, but do not promote one task
script into a supported reusable capability without product review and representative evidence.

When this Workspace is a `dist/workspace` clone, `.agents/skills/`, this file, templates, product
documentation, and `distribution.json` are product-managed. Personal state belongs in ignored
`config/`, `profiles/`, `notes/`, `outputs/`, or `AGENTS.local.md`. If `AGENTS.local.md` exists,
read it explicitly when its user rules are relevant; do not assume a host discovers it by name.

## Before every game-specific task

1. Validate this Workspace and read `config/active-profile.json`.
2. Load the exact selected file from `profiles/`. If no Profile is active, do not invent a game
   concept, style, budget, Rig policy, render setup, or export destination.
3. Read the current text request and identify each user-supplied reference image as concept, front,
   side, back, three-quarter, or another explicit role. A user-generated AI concept image is an
   input to 3D work; a Blender render is a review preview; a game PNG/pixel sprite/sprite sheet is
   a later output. Never treat one stage as another or assume a missing image exists.
4. Compare the request and references with the active Profile. Explain a style conflict instead of
   silently ignoring either source.
5. Distinguish an asset-local request from a durable game-wide rule before changing the Profile.
6. Inspect the current Blender Scene and exact targets before modifying existing data.
   Validate the configured executable and live MCP connection separately; one does not prove the
   other.
7. Before allocating output, decide whether this is a new asset, a new preserved result for an
   existing asset, or an exact continuation of an in-progress task. Use the active Profile id as
   the game id and the catalog top-level category; do not invent a test game or category.

## Durable Profile information

A Profile may store only information the user supplied or approved, including:

- game name, concept, and durable art direction;
- independent 3D and 2D styles;
- palette, design, silhouette, and game-specific proportion rules;
- material and texture rules;
- camera and rendering rules;
- Rig and animation policy;
- output formats and engine-related settings;
- cross-asset production rules and persistent style characteristics learned from references.

Fields are optional where the schema permits. Do not fill gaps by guessing. Character, weapon,
environment, and other asset families in the same game share this Profile unless an explicit
asset-local override applies.

## Profile changes

"Make this sword handle red" is local to that asset. "Keep every weapon in this game red and in
this style" may be a durable rule. Update a Profile only when persistence is explicit or the user
approves it. If a requested rule conflicts with existing settings or has multiple reasonable
interpretations, ask before changing it. Never copy a rule into another game's Profile.

Use the installed Workspace Skill to read the exact setting before changing one field, then
validate after the atomic update:

```powershell
$GameAssetAICli = ".agents/skills/gameassetai-workspace/scripts/gameassetai.py"
python -B $GameAssetAICli profile get <workspace> art_direction.palette
python -B $GameAssetAICli profile set <workspace> art_direction.palette --value-json <json>
python -B $GameAssetAICli workspace validate <workspace> --require-profile
```

The path above is for project-scoped installation from the Workspace root. At user scope, resolve
the actual copied `gameassetai-workspace/scripts/gameassetai.py` path. Do not assume a distribution
Workspace contains the development-only root `scripts/gameassetai.py`.

The CLI preserves fields not named by the update. It does not automatically infer rules from an
image, merge arbitrary Profile documents, or migrate a legacy Markdown Profile.

## Data and output safety

Paths in `config/projects.json` are bookmarks, not write authorization. Existing Blender files,
meshes, Armatures, Actions, materials, images, source references, and game projects may live
anywhere; preserve them and prefer a copy or checkpoint. `unity-workbench` is optional and may be
used only when the user explicitly requests it.

Allocate generated deliverables through the installed Runtime. The default root is this
Workspace's `outputs/`; a one-task explicit root overrides a Profile `output_defaults.root`, which
overrides the Workspace `settings.preferences.output_root`. Every external root requires explicit
selection, must already be a real directory, and is not inferred from `config/projects.json`.
Regardless of root, use `<game-id>/<asset-category>/<asset-id>/<number>-<purpose>/`. The only category ids are
`character`, `equipment-prop`, `environment`, and `vfx-mesh`. The asset id names the concrete
target; a revision of the same target keeps that id. A new comparable result receives the next
number in that asset directory, while an exact in-progress continuation must validate the exact
existing task path. Completed work is never reopened for overwrite.

Task folder names use a three-or-more-digit local number and descriptive purpose, for example
`001-initial-model` or `002-silhouette-refinement`. Do not use dates, times, UUIDs, generic
`test`/`final` names, or extra classification levels. Create artifact subfolders only when that
task needs them: `models/`, `previews/`, `sprites/`, or `exports/`. Plan paths through the Runtime
to record a task-local reservation, then register actual nonempty files to consume it. Never
overwrite an existing file, and keep Manifest artifact
paths relative to the task. `accepted` and `rejected` require distinct registered review evidence
that is still a nonempty real file inside the task when the review is recorded; links and
Junctions are refused and a failed transition leaves the Manifest unchanged. Later movement or
deletion preserves the historical review record and does not block independent work. File creation
or a Python test is not visual/semantic acceptance. The local `manifest.json` describes the task;
it is not global state.

Manifest mutations use the task-local `.gameassetai-manifest.lock`. Normal completion and handled
errors remove it. If a busy error occurs, do not delete the lock while another process may still
be using the task. After an abnormal termination, first verify that no GameAssetAI process is using
that exact task, then inspect the PID text and Manifest before any manual cleanup.

If a planned file is abandoned before publication, release that reservation through the Runtime.
Never release a reservation to hide an existing unregistered file.

`outputs/` is disposable user output: deleting or moving all or part of it removes those copies but
must not affect Profiles, settings, installed Skills, catalogs, or an independent new task. Do not
restore moved results automatically. A prior result is input only when the user explicitly selects
it; if an exact in-progress task is missing, report that continuation error without blocking new
work. If an approved external root itself was moved or deleted, do not recreate the old location;
select a new root or clear the setting before starting another task.

Catalog registration is not proof that a generator exists. Stop downstream Rig, animation, 2D,
and export work when a source fails visible or semantic review, and report unsupported work
honestly.

For a new 3D task, preserve an editable `.blend` as the first primary artifact unless the user
explicitly chooses another bounded source contract. FBX, previews, sprites, and sheets are later
explicit outputs. A local Blender executable may be stored only in ignored
`.local/environment.json` through `environment blender set`; never commit or copy a personal path
into a Profile or Skill.
