# Workspace and Profile Guide

## Command environments

Development checkout commands run from the Repository root and require the source template:

```powershell
$DevelopmentCli = "scripts/gameassetai.py"
python -B $DevelopmentCli workspace create <workspace> --template workspace-template
```

An installed Skill is self-contained. Resolve the entrypoint from that Skill's actual installation
directory and omit the template argument:

```powershell
$GameAssetAICli = "<installed-skill-root>/gameassetai-workspace/scripts/gameassetai.py"
python -B $GameAssetAICli workspace create <workspace>
```

Codex may invoke these commands through `gameassetai-workspace`; users do not need to run them
manually for every task.

## Local Blender executable

Configure the Blender executable in the root where this environment is used. Development normally
uses the Repository root; a project-scoped distribution uses its clone root; user-scoped Skills
may use the selected Workspace root. The command writes ignored `.local/environment.json`, not a
Profile or committed product file:

```powershell
# Development checkout
python -B $DevelopmentCli environment blender set . <absolute-blender-executable>
python -B $DevelopmentCli environment blender show .
python -B $DevelopmentCli environment blender validate .

# Project distribution or user-scoped Skill
python -B $GameAssetAICli environment blender set <configuration-root> `
  <absolute-blender-executable>
python -B $GameAssetAICli environment blender validate <configuration-root>
```

The setter requires an existing real absolute file and rejects linked/reparse-point paths. The
validator starts an unsaved factory-startup background process, reads Blender/Python versions, and
confirms that an intentional Python error returns nonzero. It does not open, save, model, render,
install an Add-on, or connect MCP. A missing local setting produces a clear error; installed Skills
never read the development checkout's `.local/` file implicitly.

The normal project-scoped product is a `dist/workspace` clone. Its four Skills already live under
`.agents/skills`; initialize personal state once without a development checkout:

```powershell
$GameAssetAICli = ".agents/skills/gameassetai-workspace/scripts/gameassetai.py"
python -B $GameAssetAICli workspace init-clone .
```

The command first validates `distribution.json`, product hashes, templates, and all four Skills,
then adds only missing ignored `config/` and `profiles/` files. Repeating it preserves existing
personal data. Arbitrary nonempty directories and unrelated Git repositories are refused.

For a fresh project-scoped install, use the integrated distribution command from a development
checkout before Profile creation:

```powershell
python -B $DevelopmentCli package install-project <bundle> <workspace> `
  --template workspace-template
python -B $DevelopmentCli package validate-install <workspace>\.agents\skills
```

It creates or connects the Workspace, validates it, installs all four Skills, and validates their
hash manifests in that order. Only then create/select the Profile. Do not create
`<workspace>/.agents/skills` first: that makes a new target nonempty before it has a recognized
Workspace marker. User-scoped installation is independent and may precede Workspace creation.

## Create or connect

```powershell
python -B $GameAssetAICli workspace create <workspace>
python -B $GameAssetAICli workspace connect <workspace>
python -B $GameAssetAICli workspace validate <workspace>
```

The path is user-selected and never hard-coded. A valid existing v2 Workspace returns `connected`
without changes. An unknown nonempty directory is refused. There is no force-overwrite path, and
safe update adds only missing neutral README files; it never replaces personal `AGENTS.md`,
configuration, Profiles, notes, or outputs.

## Profiles and durable rules

```powershell
python -B $GameAssetAICli profile create <workspace> my-game `
  --name "My Game" --description "Persistent art and technical context" `
  --three-d-style stylized-chibi-low-poly
python -B $GameAssetAICli profile select <workspace> my-game
python -B $GameAssetAICli profile list <workspace>
python -B $GameAssetAICli profile show <workspace>
python -B $GameAssetAICli profile show <workspace> --profile my-game
python -B $GameAssetAICli profile get <workspace> art_direction.palette
python -B $GameAssetAICli profile set <workspace> art_direction.palette `
  --value-json '["moss", "bark"]'
python -B $GameAssetAICli profile clear <workspace>
```

The setter changes one dot-separated mutable setting, preserves every unnamed field, validates the
complete candidate, and publishes atomically. Mutable areas are `name`, `description`, children of
`styles`, `art_direction`, `asset_defaults`, `rig_animation`, and `output_defaults`. Schema, id,
and system metadata are not direct user-set targets.

`styles.three_d` accepts null or a registered 3D catalog id; `styles.two_d` accepts only registered
2D ids. Unknown and dimension-mismatched ids are rejected on creation, load, update, selection, and
Workspace validation without rewriting the file. User-specific prose such as palette, silhouette,
or inspiration rules belongs in `art_direction`, not in an invented official style id.

Before each game task, load the active Profile, compare its durable rules with the current text and
references, and distinguish a one-asset override from a persistent game-wide request. Persist a
rule only when the user explicitly asks or approves. Ask before resolving conflicts or ambiguous
style changes; never update another game's Profile.

Profiles can hold game concept, independent 3D/2D styles, palette, silhouette and proportion
rules, material/texture policy, camera/render settings, Rig/animation policy, output/engine
settings, and cross-asset production rules. Missing information remains missing; the system does
not infer and save it automatically.

## Reference inputs and output stages

The normal creation flow uses text, a style preset, and user-supplied reference images, commonly
generated with an external image AI. Label concept/front/side/back/three-quarter roles. A task may
continue without images when its Profile and text are sufficient; otherwise explain which visual
information is needed. GameAssetAI does not require or automatically call an image-generation API.

Keep these stages distinct:

1. concept/reference images supplied before 3D production;
2. Blender preview renders used for source review;
3. final game PNG, pixel sprite, animation frames, or sprite sheets.

For a new 3D asset, preserve the editable `.blend` as the first primary deliverable unless the
user explicitly selects another bounded source contract. FBX and all 2D forms are downstream
requests and never replace source preservation merely because their artifact paths are supported.

## Legacy Workspace handling

A recognized older Workspace returns `legacy-connected` with `migration_required: true` and is not
modified. Automatic Markdown-to-JSON migration is deliberately unavailable because arbitrary
Markdown rules cannot be mapped safely without review.

Manual migration procedure:

1. Make an independent backup of the legacy Workspace.
2. Inventory each Markdown Profile and current active selection.
3. Create a separate v2 Workspace or JSON Profile; do not initialize over the legacy directory.
4. Copy only confirmed durable rules into the corresponding JSON areas.
5. Validate, compare with the original, and switch only after user approval.
6. Retain the original until the user decides it is no longer needed.

## Project mappings and user outputs

`config/projects.json` stores absolute-path bookmarks by game and label, such as `blender`,
`unity`, `source-art`, or `unity-workbench`. The current CLI validates structure but does not write
mappings. A bookmark is not authorization to export or modify its target, and UnityWorkbench is
used only on explicit request.

User output roots are separate from project bookmarks. The priority is an explicit one-task
`--output-root`, then the active Profile's optional `output_defaults.root`, then the Workspace's
optional `settings.preferences.output_root`, then internal `<workspace>/outputs`. Inspect, set, or
clear the Workspace preference with:

```powershell
python -B $GameAssetAICli workspace output-root <workspace>
python -B $GameAssetAICli workspace output-root <workspace> --set <absolute-existing-directory>
python -B $GameAssetAICli workspace output-root <workspace> --clear
```

External roots require an explicitly selected existing real directory and reject links/Junctions.
If one is moved or removed, Workspace/Profile validation still works, but allocation reports the
missing root instead of silently recreating it; select another root or clear the override.

User results use this fixed classification:

```text
outputs/<game-id>/<asset-category>/<asset-id>/<number>-<purpose>/manifest.json
```

- `game-id` is the active Profile; an explicit game argument must match it.
- `asset-category` is one of `character`, `equipment-prop`, `environment`, or `vfx-mesh`.
- `asset-id` is the concrete target, so revisions keep it rather than adding `v2`.
- the task is the next local three-or-more-digit number plus a descriptive purpose.

```powershell
python -B $GameAssetAICli outputs begin <workspace> --space workspace `
  --category equipment-prop --asset bronze-sword --purpose initial-model
python -B $GameAssetAICli outputs begin <workspace> --space workspace `
  --category equipment-prop --asset bronze-sword --purpose external-comparison `
  --output-root <absolute-existing-directory>
python -B $GameAssetAICli outputs continue `
  <task-path> [--workspace <workspace>]
```

New comparable results receive a new number. Exact continuation requires the existing task to be
`in-progress`; completed work is not reopened for overwrite. The allocator derives the number from
the current filesystem, claims atomically, rejects link/Junction components, escape, invalid
categories, and active-game mismatch, and creates no artifact folders in advance. Dates, times,
UUIDs, global counters, and generic `test`/`final` names are not task folder names.

Create only the next required artifact path, publish the file without overwrite, and then register
the real nonempty file in the Manifest:

```powershell
python -B $GameAssetAICli outputs artifact-path <task> `
  --kind model --filename bronze-sword.blend [--workspace <workspace>]
python -B $GameAssetAICli outputs register <task> `
  <task>\models\bronze-sword.blend [--workspace <workspace>]
python -B $GameAssetAICli outputs release <task> `
  exports/unused-export.fbx [--workspace <workspace>]
```

Official task subdirectories are `models/`, `previews/`, `sprites/`, and `exports/`; they are not
created until requested. `artifact-path` atomically records a task-local reservation so concurrent
work cannot claim the same relative path; `register` consumes that reservation after the real file
exists. A task cannot change state while a reservation remains. `complete` means artifact production ended without a quality decision.
Release only an abandoned reservation whose artifact was never published; if a file exists, it
must be registered or handled explicitly rather than hidden by releasing its reservation.
`accepted` and `rejected` require a review summary and distinct registered evidence paths. At the
moment the review is recorded, every evidence path must still be a nonempty real file inside the
task with no linked/Junction component. A failed review transition leaves the Manifest unchanged.
After a successful review, later user movement or deletion does not erase the historical decision
and does not block independent work. Only
`in-progress -> complete|accepted|rejected` and `complete -> accepted|rejected` are allowed;
accepted/rejected tasks are terminal. Automated tests or file creation never justify acceptance.

Manifest mutations use the task-local `.gameassetai-manifest.lock`. Normal completion and handled
exceptions remove it. A busy error can mean another process is writing; do not delete the lock
while that process may still be active. If a process terminated abnormally, first confirm that no
GameAssetAI process is using that exact task, then inspect the PID text and Manifest before any
manual cleanup. The Runtime does not automatically delete an apparently stale lock.

Users may move or delete one task, one asset, or all of `outputs/`. This removes those copies, but
configuration, Profiles, installed Skills, catalog access, and a new independent task remain
functional. A missing in-progress task fails only its explicit continuation and is not recreated.

This storage independence is not a claim that every `.blend` is self-contained after movement.
Blender files may reference external textures, linked libraries, images, caches, or other absolute
paths. A production workflow must inspect those dependencies and deliberately use reviewed
relative paths or Blender resource packing where appropriate. Real `.blend` portability was not
tested in this package and remains a representative Blender validation gate.

## Development experiment outputs

Development results are separate from this Workspace and live only in a development checkout:

```text
output/experiments/<experiment-id>/<asset-category>/<asset-id>/<number>-<purpose>/
```

`experiment.json` records the purpose, core question, and evaluation criteria. Before allocating a
task, list metadata and explicitly reuse the experiment only when the validation goal matches, or
create a descriptive new experiment when it does not:

```powershell
python -B $DevelopmentCli outputs experiment list <repository>
python -B $DevelopmentCli outputs experiment create <repository> chibi-character-quality `
  --purpose "Validate chibi visual quality" `
  --question "Does the method meet the target silhouette?" `
  --criterion "Readable front and three-quarter silhouette"
python -B $DevelopmentCli outputs begin <repository> --space development `
  --experiment chibi-character-quality --category character `
  --asset chibi-adventurer --purpose initial-model
```

A new request alone does not create a new experiment, and a shared asset name does not merge
different validation goals. The Runtime does not guess natural-language equivalence: when metadata
does not resolve the choice, obtain the minimum user clarification. Repository `/output/` is
ignored, optional, disposable, and never package or test input.
