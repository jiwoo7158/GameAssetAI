# Skill Distribution and Codex Setup

## Product surface

- `gameassetai-workspace`
- `gameassetai-create-asset`
- `gameassetai-modify-asset`
- `gameassetai-output-asset`

Narrow Blender helpers are internal Runtime modules. Asset nouns remain catalog data, not Skills.

## Build and validate in a development checkout

```powershell
python -B scripts/gameassetai.py package build . <new-bundle-directory>
python -B scripts/gameassetai.py package validate <bundle-directory>
python -B scripts/gameassetai.py package zip <bundle-directory> <new-archive.zip>
```

The destination must not exist. Each built Skill receives the shared Runtime, catalog, Workspace
template, portable entrypoint, and a hash manifest. Source files do not embed the checkout's
absolute path, and ZIP timestamps are deterministic.

## Codex installation scopes

Current official Codex guidance recognizes:

- project scope: `<opened-project>/.codex/skills/<skill-name>/SKILL.md`;
- user scope: `~/.codex/skills/<skill-name>/SKILL.md`.

See [Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills)
for the official path examples and manual `/skills` or `$skill-name` activation guidance. On this
Windows development machine, the user-scoped root resolves under `%USERPROFILE%\.codex\skills`.
Do not assume a host-specific UI copied or refreshed Skills until it is checked in that host.

Choose one scope:

- install in a GameAssetAI-Workspace's `.codex/skills` to make the four Skills project-scoped when
  that Workspace is opened in Codex Desktop or VS Code + Codex;
- install in the user's `.codex/skills` to make them user-scoped across projects.

Fresh install from the development checkout:

```powershell
python -B scripts/gameassetai.py package install <bundle> <workspace>\.codex\skills
```

The operation preflights all four names, rejects linked path components, and refuses if any target
exists. It stages all folders before promotion. After installation, open/reload the intended Codex
environment, inspect `/skills` when available, or explicitly invoke `$gameassetai-workspace` in a
new conversation. File/package validation does not itself prove Desktop or VS Code discovery.

## Explicit update with recovery

```powershell
python -B scripts/gameassetai.py package update <bundle> <skills-directory> `
  --backup <new-unused-real-backup-directory>
```

All four existing Skills must be real directories. The backup must not exist or be linked. Current
versions are moved intact to the backup; staged new versions replace them. A promotion failure
restores old paths. Successful update retains the backup for manual recovery and review.

## Installed Runtime use

Each installed Skill directory has its own portable entrypoint:

```powershell
python -B scripts/gameassetai.py catalog validate
python -B scripts/gameassetai.py workspace validate <workspace>
```

These commands run without the development Repository. Package build/install/update commands
remain development/distribution operations rather than normal daily Workspace commands.

## External setup boundary

Skill installation does not install or configure Blender, Blender MCP, the Blender Add-on, AI
models, credentials, Unity, or UnityWorkbench. Verify Blender and MCP separately before production
work. External AI and UnityWorkbench remain optional and explicit.
