# Workspace location verification — 2026-09-16

Canonical personal runtime Workspace: `D:/AI/GameAssetAI-Workspace`.
Development source remains `D:/GitHub/GameAssetAI`; external Blender/engine projects
are not moved. User supplied the new Workspace as a reference to this conversation.

## Observed / completed

- New Workspace AGENTS.md and both installed SKILL.md files read completely.
- Workspace validation passes; active Profile null, project mappings empty.
- Installed helper bytes were read from the new Workspace and executed through live MCP.
  Inspection succeeds: Camera, Cube, Light. Cube diagnostics succeed: 12 base triangles,
  no generic findings, no inferred game constraints. Inspection facts match before/after.
- Repository and new Workspace have no operational references to the retired location.
- Found old project trust entry in user Codex config.toml and removed only that table.
  New location was already trusted; unchanged. TOML parsing and semantic before/after
  comparison confirm no other configuration values changed, including MCP configuration.
  OpenAI Docs informed this targeted distinction between project trust and MCP settings:
  [official configuration sample](https://learn.chatgpt.com/docs/config-file/config-sample).
- Configuration backup: `.local/retired-workspaces/codex-config-before-retirement.toml`.
  It is a private ignored recovery artifact; do not publish it or treat it as active config.

## Incomplete retirement / real UI gate

Update: user subsequently removed the old folder. A fresh Test-Path check returned false
on 2026-09-16; folder-retirement blocker is resolved. The failed move below is historical
evidence, not a remaining action or proof of a created Workspace backup. Explicit real
Workspace Profile switching now passed; see `docs/profile-workflow-validation.md`.

`D:/Blender/GameAssetAI-Workspace` contains only the older template's seven files,
no personal game Profile, and empty active/mapping config. It is not a link/junction and
contains no observed linked descendants. AGENTS.md/README.md are older versions; other
five files match the new Workspace byte-for-byte.

Attempted approved recoverable folder move to
`.local/retired-workspaces/20260916-manual-workspace` failed because another process is
using the original directory. At that time the old folder remained and files were not removed;
the planned Workspace backup was NOT created. Config backup above did succeed.
Do not classify the move as successful because PowerShell reported process exit zero.
No process was killed. No individual template file was removed to work around the lock.

The earlier suggestion to close the app and retry retirement is now obsolete: the user
removed the old folder and its absence was verified. Do not ask for another deletion.
No broader Blender directory or original game asset belongs in this operation.

Installed helper execution and explicit two-Profile switching are verified. The user
subsequently confirmed session exposure and explicit Blender calls for all three Skills.
Three independent natural-language read-only outcomes were subsequently confirmed by the
user. Raw selected-Skill/MCP traces remain absent. See `skill-session-validation.md`.
No further source-folder setup, recreation or --force operation is needed.
