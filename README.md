# GameAssetAI Workspace Distribution

This branch is generated from reviewed GameAssetAI development source. Do not develop product code
directly in this branch.

## First project-scoped setup

1. Clone only the `dist/workspace` branch into the directory you want to use as the persistent
   GameAssetAI Workspace.
2. From the clone root, initialize personal Workspace state with the bundled Workspace Skill:

   ```powershell
   python -B .agents/skills/gameassetai-workspace/scripts/gameassetai.py `
     workspace init-clone .
   ```

3. Create and select a game Profile, then open this same directory in Codex Desktop or VS Code +
   Codex. The four project Skills are under `.agents/skills/`.

`config/`, `profiles/`, `notes/`, `outputs/`, and `AGENTS.local.md` are personal and ignored by
Git. Initialization and product updates never overwrite them. `outputs/` is created only when an
internal result is needed.

Output artifact paths are reserved through the bundled Runtime before a producer writes them.
Register the real nonempty file to consume the reservation; do not publish by overwriting an
existing path.

## Update

Use GitHub Desktop **Fetch origin** and **Pull origin**, or run `git pull --ff-only`. Stop and
inspect any conflict; do not reset, clean, or delete personal files to force an update. Restart
Codex only when a changed Skill is not rediscovered automatically.

## User-scoped Skills

To use the same release at user scope, copy only the four directories under `.agents/skills/` into
`$HOME/.agents/skills/`. Do not install the same Skill at both project and user scope unless you
intend to manage the duplicate entries explicitly. A separate persistent Workspace is still
required for Profiles and game settings.

The product distribution does not install Blender, Blender MCP, external AI services, Unity, or
UnityWorkbench. `distribution.json` records the product version, source commit, layout version,
and product-file hashes.
