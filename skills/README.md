# Product Skills

GameAssetAI exposes four task-oriented Skills: Workspace management, asset creation, asset
modification, and output. Narrow Blender operations live in the shared runtime and are routed
internally; they are not separate product commands.

Source Skills intentionally contain instructions only. `scripts/gameassetai.py package build`
creates self-contained installable copies by vendoring the shared runtime, catalog, and Workspace
template into each built Skill. Generated bundles are not committed. Install all four together in
either a project-scoped `.codex/skills/` directory or the user-scoped `~/.codex/skills/` directory;
do not point an installed Skill back at this source tree.
