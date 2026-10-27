# GameAssetAI Workspace Instructions

This folder is the persistent user workspace for Blender game-asset work.

## Primary behavior

Before applying game-specific assumptions:

1. read `config/active-profile.json`
2. load the referenced profile from `profiles/`
3. apply that profile together with the installed GameAssetAI skills

The reference is an exact-case filename stem without `.md` or path separators.
Reject missing, empty, reserved (`README`, `_PROFILE_TEMPLATE`), or linked profiles.
Re-read the active reference before game-specific work; do not reuse stale rules after
a switch. Unspecified profile fields are unknown, not permission to invent defaults.

If no valid active profile exists, do not silently invent game-specific constraints.
Ask for or create a profile when such constraints matter.

## External projects

Existing Unity / Unreal / Blender projects may live outside this workspace.

Optional path mappings are stored in:

```text
config/projects.json
```

Do not move, rename, or restructure those projects unless the user explicitly asks.
Mappings are named objects of absolute path strings. Verify the actual target when a task
needs it; mapping a path alone does not authorize writes or select an export destination.

## Current Blender scene

Treat the open Blender scene as the primary source of truth for currently loaded assets.

If the user has already imported a model, armature, or animation into Blender, inspect the scene directly instead of requiring them to copy the original file into this workspace.

## One-off references

Do not require a permanent `references/` directory.

One-off images, files, or descriptions may be supplied directly for the current task.

Persistent game-wide rules belong in the active profile.

## Preservation

Existing meshes, armatures, materials, Actions, and animations may be valuable.

Analyze before destructive changes and preserve existing data unless modification or replacement is clearly requested.

## Engine defaults

Read the active profile for the target engine.

Do not assume Unity or Unreal when the active profile specifies otherwise.

## Profile changes

When the user states a durable rule for the current game, offer to update the active profile or update it when explicitly requested.

Do not place project-specific rules into installed reusable skills.
Create/switch profiles by editing personal workspace files, not by recreating the workspace
or overwriting its configuration with the creation script's `--force` option.
