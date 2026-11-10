# Product Skills

GameAssetAI exposes four task-oriented Skills: Workspace management, asset creation, asset
modification, and output. Narrow Blender operations live in the shared runtime and are routed
internally; they are not separate product commands.

Source Skills intentionally contain instructions only. `scripts/gameassetai.py package build`
creates self-contained installable copies by vendoring the shared runtime, catalog, and Workspace
template into each built Skill. Generated bundles are not committed. Install all four together;
do not point an installed Skill back at this source tree.

For project scope, first create or connect and validate the user-selected Workspace, then install
and validate the four Skills under that Workspace's `.codex/skills`, and only then create/select a
Profile. Use the project-install workflow rather than creating `.codex/skills` in an unrecognized
folder. A user-scoped install under `~/.codex/skills/` does not depend on Workspace creation.

All four Skills share the Runtime output contract. User tasks use
`outputs/<game>/<category>/<asset>/<number>-<purpose>/`; development experiments use the separate
Repository `output/experiments/` hierarchy. Result trees are disposable and never packaged.
