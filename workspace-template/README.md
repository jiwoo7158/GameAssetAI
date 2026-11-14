# GameAssetAI Workspace

Open this directory as the project/source folder for normal Codex Desktop or VS Code + Codex
game-asset work.

- `profiles/`: persistent game-specific art and technical rules.
- `config/active-profile.json`: exact active Profile id.
- `config/projects.json`: optional absolute-path bookmarks, including `unity-workbench`.
- `config/settings.json`: personal, game-neutral preferences.
- `.local/environment.json`: optional ignored local Blender executable selection; configure it
  through the bundled Runtime, never by committing a personal path.
- `.local/external-tools.json`: optional ignored absolute connection to one user-owned
  `GameAssetAI-Tools` root shared by all game Profiles. Workspace initialization does not create
  it; use the Workspace Skill to initialize or connect one explicitly.
- `.agents/skills/`: optional project-scoped installed Skills. In a `dist/workspace` clone these
  product files already exist; in bundle onboarding create them only after Workspace validation.
- `outputs/`: user deliverables under
  `<game>/<category>/<asset>/<number>-<purpose>/`, created on demand and freely movable/removable.
- Task artifact paths are reserved by the Runtime before publication; registration consumes the
  reservation after a real nonempty file exists. Only needed artifact directories are created.
  A new accepted/rejected review rechecks that each distinct registered evidence file is present,
  nonempty, and safely inside the task at that moment.
- `config/settings.json` and a Profile's `output_defaults` may select an existing external output
  root. One-task explicit selection has highest priority; external roots are never inferred from
  project bookmarks or silently recreated.
- `notes/`: optional personal notes.

`GameAssetAI-Tools` is not a Workspace child, output root, Git branch, or bundled product. A
registration records management information only; it does not prove that a tool is installed,
active, compatible, executable, or supported. Moving or deleting the Tools root leaves core
Workspace/Profile/output behavior usable and does not cause the old location to be recreated.

Codex may use Blender native operations and bounded task-specific code for the current asset; a
prewritten generator is not required for every noun. Preserve an editable `.blend` as the first
primary 3D artifact unless another bounded source contract is explicitly selected. Codex reports
the exact registered path; Blender GUI review is optional and opening the file does not authorize
an overwrite or implicit revision. Export and 2D artifacts are later explicit steps.

Use `gameassetai-workspace` to create, select, inspect, and explicitly update Profiles. Existing
game projects and user-supplied reference/source files may remain at their original paths; do not
copy them into this Workspace unless the user chooses to. Deleting any or all of `outputs/`
deletes those asset copies, but it must not affect GameAssetAI configuration or the ability to
start an independent new task. Continue an existing task only by its exact validated path.
