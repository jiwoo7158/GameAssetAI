# GameAssetAI Workspace

Open this directory as the project/source folder for normal Codex Desktop or VS Code + Codex
game-asset work.

- `profiles/`: persistent game-specific art and technical rules.
- `config/active-profile.json`: exact active Profile id.
- `config/projects.json`: optional absolute-path bookmarks, including `unity-workbench`.
- `config/settings.json`: personal, game-neutral preferences.
- `.codex/skills/`: optional project-scoped installed Skills; create it only when installing here.
- `outputs/`: user deliverables, created on demand and removable as a complete tree.
- `notes/`: optional personal notes.

Use `gameassetai-workspace` to create, select, inspect, and explicitly update Profiles. Existing
game projects and user-supplied reference/source files may remain at their original paths; do not
copy them into this Workspace unless the user chooses to. Deleting `outputs/` deletes its asset
copies, but it must not affect GameAssetAI configuration or the ability to start a new run.
