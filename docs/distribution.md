# Skill Distribution

## Product surface

- `gameassetai-workspace`
- `gameassetai-create-asset`
- `gameassetai-modify-asset`
- `gameassetai-output-asset`

Narrow Blender helpers are internal modules. Asset nouns are catalog data, not Skills.

## Build and validate

```powershell
python -B scripts/gameassetai.py package build . <new-bundle-directory>
python -B scripts/gameassetai.py package validate <bundle-directory>
python -B scripts/gameassetai.py package zip <bundle-directory> <new-archive.zip>
```

The destination must not exist. Each built Skill receives the shared Python runtime, catalog,
Workspace template, portable entrypoint, and a hash manifest. No source file embeds the checkout's
absolute path. ZIP timestamps are deterministic.

## Fresh install

```powershell
python -B scripts/gameassetai.py package install <bundle> <skills-directory>
```

The operation preflights all four names and refuses if any exists. It stages all new folders and
promotes them only after complete copy. It does not refresh or prove Codex client discovery.

## Explicit update with recovery

```powershell
python -B scripts/gameassetai.py package update <bundle> <skills-directory> `
  --backup <new-unused-backup-directory>
```

All four existing Skills must be real directories. The backup must not exist. Current versions are
moved intact to the backup; staged new versions replace them. A promotion failure restores old
paths. Successful update retains the backup for manual recovery and review. Personal/drifted
files are therefore preserved in the backup rather than silently merged.

## External setup boundary

Skill installation does not install Blender, Blender MCP, the Add-on, AI models, API credentials,
or Unity. Those remain explicit environment-specific setup tasks.
