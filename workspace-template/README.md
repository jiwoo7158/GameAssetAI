# GameAssetAI Workspace

Open this directory as the project/source folder for normal Codex Desktop or VS Code + Codex
game-asset work.

- `profiles/`: persistent game-specific art and technical rules.
- `config/active-profile.json`: exact active Profile id.
- `config/projects.json`: optional absolute-path bookmarks, including `unity-workbench`.
- `config/settings.json`: personal, game-neutral preferences.
- `.agents/skills/`: optional project-scoped installed Skills. In a `dist/workspace` clone these
  product files already exist; in bundle onboarding create them only after Workspace validation.
- `outputs/`: user deliverables under
  `<game>/<category>/<asset>/<number>-<purpose>/`, created on demand and freely movable/removable.
- Task artifact paths are reserved by the Runtime before publication; registration consumes the
  reservation after a real nonempty file exists. Only needed artifact directories are created.
- `config/settings.json` and a Profile's `output_defaults` may select an existing external output
  root. One-task explicit selection has highest priority; external roots are never inferred from
  project bookmarks or silently recreated.
- `notes/`: optional personal notes.

Use `gameassetai-workspace` to create, select, inspect, and explicitly update Profiles. Existing
game projects and user-supplied reference/source files may remain at their original paths; do not
copy them into this Workspace unless the user chooses to. Deleting any or all of `outputs/`
deletes those asset copies, but it must not affect GameAssetAI configuration or the ability to
start an independent new task. Continue an existing task only by its exact validated path.
