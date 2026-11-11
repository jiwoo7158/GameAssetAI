# Product Skills

GameAssetAI exposes four task-oriented Skills: Workspace management, asset creation, asset
modification, and output. Narrow Blender operations live in the shared runtime and are routed
internally; they are not separate product commands.

Source Skills intentionally contain instructions only. `scripts/gameassetai.py package build`
creates self-contained installable copies by vendoring the shared runtime, catalog, and Workspace
template into each built Skill. Generated bundles are not committed. Install all four together;
do not point an installed Skill back at this source tree.

The normal project-scoped product is the generated `dist/workspace` branch. Clone it, run the
bundled `workspace init-clone` command, and then create/select a Profile; its four self-contained
Skills already live under `.agents/skills/`. Bundle-based onboarding remains available for
development and installs only after Workspace creation/validation. User-scoped installation copies
the same four generated Skill directories to `$HOME/.agents/skills/` and does not depend on
Workspace creation. Do not move or delete an existing legacy `.codex/skills` installation
automatically, and avoid duplicate project/user copies with the same Skill names.

All four Skills share the Runtime output contract. User tasks use
`outputs/<game>/<category>/<asset>/<number>-<purpose>/`; development experiments use the separate
Repository `output/experiments/` hierarchy. An explicitly selected external output root keeps the
same game/category/asset/task hierarchy. Result trees are disposable and never packaged.
