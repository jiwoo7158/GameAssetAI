# Workspace and Profile Guide

## Command environments

Development checkout commands run from the Repository root and require the source template:

```powershell
python -B scripts/gameassetai.py workspace create <workspace> --template workspace-template
```

An installed Skill is self-contained. Run from any installed GameAssetAI Skill directory and omit
the template argument:

```powershell
python -B scripts/gameassetai.py workspace create <workspace>
```

Codex may invoke these commands through `gameassetai-workspace`; users do not need to run them
manually for every task.

## Create or connect

```powershell
python -B scripts/gameassetai.py workspace create <workspace>
python -B scripts/gameassetai.py workspace connect <workspace>
python -B scripts/gameassetai.py workspace validate <workspace>
```

The path is user-selected and never hard-coded. A valid existing v2 Workspace returns `connected`
without changes. An unknown nonempty directory is refused. There is no force-overwrite path, and
safe update adds only missing neutral README files; it never replaces personal `AGENTS.md`,
configuration, Profiles, notes, or outputs.

## Profiles and durable rules

```powershell
python -B scripts/gameassetai.py profile create <workspace> my-game `
  --name "My Game" --description "Persistent art and technical context" `
  --three-d-style stylized-chibi-low-poly
python -B scripts/gameassetai.py profile select <workspace> my-game
python -B scripts/gameassetai.py profile list <workspace>
python -B scripts/gameassetai.py profile show <workspace>
python -B scripts/gameassetai.py profile show <workspace> --profile my-game
python -B scripts/gameassetai.py profile get <workspace> art_direction.palette
python -B scripts/gameassetai.py profile set <workspace> art_direction.palette `
  --value-json '["moss", "bark"]'
python -B scripts/gameassetai.py profile clear <workspace>
```

The setter changes one dot-separated mutable setting, preserves every unnamed field, validates the
complete candidate, and publishes atomically. Mutable areas are `name`, `description`, children of
`styles`, `art_direction`, `asset_defaults`, `rig_animation`, and `output_defaults`. Schema, id,
and system metadata are not direct user-set targets.

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

## Project mappings and outputs

`config/projects.json` stores absolute-path bookmarks by game and label, such as `blender`,
`unity`, `source-art`, or `unity-workbench`. The current CLI validates structure but does not write
mappings. A bookmark is not authorization to export or modify its target, and UnityWorkbench is
used only on explicit request.

```powershell
python -B scripts/gameassetai.py outputs begin <workspace> `
  --game my-game --category weapon --asset bronze-sword
```

This creates `outputs/my-game/weapon/<unique-run-id>/manifest.json`. The allocator rejects
link/junction path components, Workspace escape, and collisions. Create `models/`, `previews/`,
`exports/`, or `sprites/` only when needed. Users may delete `outputs/` completely; that deletes
its deliverable copies but leaves configuration, Profiles, installed Skills, and future run
creation functional.
