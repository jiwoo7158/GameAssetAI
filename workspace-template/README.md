# GameAssetAI-Workspace

This is the user's normal Codex workspace for Blender game-asset work.

It does not contain Unity / Unreal projects and does not require them to be moved.

## Contents

- `AGENTS.md` — stable workspace instructions
- `profiles/` — one file per game's asset rules
- `config/projects.json` — optional mappings to existing project paths
- `config/active-profile.json` — currently selected game profile
- `notes/` — optional personal / development notes

## Normal use

1. Open this workspace folder in Codex.
2. Open Blender separately.
3. Ensure Blender MCP is available.
4. Select or create the game profile you want.
5. Work normally.

Existing Blender, Unity, and Unreal files may remain in their existing locations.

This README is copied from GameAssetAI's `workspace-template/` during first-time setup.
The source template is not a Blender asset folder. Do not recreate this personal workspace
every session; `--force` would overwrite personal configuration and instructions.

To select a game, copy `profiles/_PROFILE_TEMPLATE.md` to `profiles/YourGame.md`, record
known durable rules, and set `"profile": "YourGame"` in `config/active-profile.json`.
Use the exact filename stem without `.md` or a path. `null` means no game is selected.
Project mappings are optional named objects of absolute path strings in `projects.json`;
they reference existing projects, do not move them, and are not export permissions.
Detailed contract and development validation commands live in the GameAssetAI repository
under `docs/workspace-contract.md` (not a required installed-skill dependency).
