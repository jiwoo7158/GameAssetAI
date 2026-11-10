# Workspace and Profile Guide

## Create or connect

```powershell
python -B scripts/gameassetai.py workspace create D:\AI\GameAssetAI-Workspace --template workspace-template
python -B scripts/gameassetai.py workspace connect D:\AI\GameAssetAI-Workspace --template workspace-template
```

The path is user-selected and never hard-coded. A valid existing v2 Workspace returns `connected`
without changes. A recognized earlier Workspace returns `legacy-connected` and
`migration_required: true`; this foundation deliberately does not rewrite it. Any other nonempty
directory is refused.

There is no `--force`. Safe update copies only missing neutral README files:

```powershell
python -B scripts/gameassetai.py workspace update <workspace> --template workspace-template
```

It never replaces personal `AGENTS.md`, configuration, Profiles, notes, or outputs.

## Profiles

```powershell
python -B scripts/gameassetai.py profile create <workspace> my-game `
  --name "My Game" --description "Persistent art and technical context" `
  --three-d-style stylized-chibi-low-poly
python -B scripts/gameassetai.py profile select <workspace> my-game
python -B scripts/gameassetai.py profile show <workspace>
python -B scripts/gameassetai.py profile list <workspace>
```

Profiles persist independently of chat sessions. Editing a Profile is intentionally explicit;
the current CLI creates/selects/reads but does not silently merge arbitrary fields.

## Project mappings

`config/projects.json` stores absolute path bookmarks by game and label. Labels may include
`blender`, `unity`, `source-art`, or `unity-workbench`. Validation checks structure only and does
not access paths. A bookmark is not authorization to export or modify that project.

## Outputs

```powershell
python -B scripts/gameassetai.py outputs begin <workspace> `
  --game my-game --category weapon --asset bronze-sword
```

This creates `outputs/my-game/weapon/<unique-run-id>/manifest.json`. Add `models/`, `previews/`,
`exports/`, or `sprites/` only when the task needs them. Users may delete `outputs/` at any time;
the next command recreates only the needed run path.
