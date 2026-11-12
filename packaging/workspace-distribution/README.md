# GameAssetAI Workspace Distribution

This branch is generated from reviewed GameAssetAI development source. Do not develop product code
directly in this branch.

## First project-scoped setup

1. Clone only the `dist/workspace` branch into the directory you want to use as the persistent
   GameAssetAI Workspace.
2. From the clone root, use the bundled Workspace Skill entrypoint. The generated product has no
   development `scripts/` directory, and it does not need the development Repository:

   ```powershell
   $GameAssetAICli = ".agents/skills/gameassetai-workspace/scripts/gameassetai.py"
   python -B $GameAssetAICli workspace init-clone .
   python -B $GameAssetAICli workspace validate .
   ```

3. Create and select a game Profile, then inspect the active Profile and default output root:

   ```powershell
   python -B $GameAssetAICli profile create . my-game `
     --name "My Game" --description "Persistent game art profile" `
     --three-d-style stylized-chibi-low-poly
   python -B $GameAssetAICli profile select . my-game
   python -B $GameAssetAICli profile show .
   python -B $GameAssetAICli workspace validate . --require-profile
   python -B $GameAssetAICli workspace output-root .
   ```

4. Open this same directory in Codex Desktop or VS Code + Codex. The four project Skills are under
   `.agents/skills/`. Confirm that the host discovers them; file validation does not prove host
   discovery.

## Result-task commands from the clone root

Allocate a new task only when actual work needs a result directory. The command prints the exact
task path; use that returned path for validation and later lifecycle commands:

```powershell
python -B $GameAssetAICli outputs begin . --space workspace `
  --category equipment-prop --asset bronze-sword --purpose initial-model
python -B $GameAssetAICli outputs validate <task-path>
```

These commands allocate storage only. They do not claim that an asset generator, Blender export,
or visual acceptance ran.

`config/`, `profiles/`, `notes/`, `outputs/`, `.local/`, and `AGENTS.local.md` are personal and ignored by
Git. Initialization and product updates never overwrite them. `outputs/` is created only when an
internal result is needed.

Output artifact paths are reserved through the bundled Runtime before a producer writes them.
Register the real nonempty file to consume the reservation; do not publish by overwriting an
existing path. A new accepted/rejected review additionally checks that every distinct registered
evidence path is still an existing nonempty real file inside the task at that moment. Later user
movement or deletion preserves the historical review record and does not block independent work.

Manifest changes use `.gameassetai-manifest.lock` inside the task. Normal completion and handled
errors remove it. A busy error may mean another process is active; do not delete the lock while
that process may still be writing. After confirming no GameAssetAI process is using the exact task,
inspect the recorded PID and task state before any manual cleanup.

## Update

Use GitHub Desktop **Fetch origin** and **Pull origin**, or run `git pull --ff-only`. Stop and
inspect any conflict; do not reset, clean, or delete personal files to force an update. Restart
Codex only when a changed Skill is not rediscovered automatically.

## User-scoped Skills

To use the same release at user scope, copy only the four directories under `.agents/skills/` into
`$HOME/.agents/skills/`. Do not install the same Skill at both project and user scope unless you
intend to manage the duplicate entries explicitly. A separate persistent Workspace is still
required for Profiles and game settings. For manual CLI use, resolve the actual installed
`gameassetai-workspace/scripts/gameassetai.py` path and use that path as `$GameAssetAICli`; do not
assume a development `scripts/` directory or hard-code a different user's home path.

## Manual environment checks before asset work

- `python --version` confirms the interpreter used by the bundled CLI.
- Confirm the four Skills in Codex Desktop or VS Code + Codex, restarting the host only if changed
  Skills are not rediscovered.
- Record and validate the user's existing Blender executable without hard-coding it into product
  files:

  ```powershell
  python -B $GameAssetAICli environment blender set . <absolute-blender-executable>
  python -B $GameAssetAICli environment blender validate .
  ```

  This writes ignored `.local/environment.json` and runs only unsaved factory-startup background
  diagnostics. It does not create an asset or configure MCP.
- Confirm Blender MCP connectivity in the selected Codex host before relying on it.

These are environment checks, not evidence that modeling, rendering, export, visual quality, or an
engine round trip works. Setup never enables an Add-on, changes MCP/VS Code settings, or installs
Blender automatically.

The product distribution does not install Blender, Blender MCP, external AI services, Unity, or
UnityWorkbench. `distribution.json` records the product version, source commit, layout version,
and product-file hashes.
