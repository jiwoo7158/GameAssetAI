# Development Entrypoints

- `gameassetai.py`: catalog, Workspace/Profile, specification, output, and package commands.
- `create_workspace.py`: safe compatibility wrapper; there is no force-overwrite mode.
- `validate_workspace.py`: read-only compatibility wrapper.
- `validate_repo.py`: current product layout and offline contract validation.

The active shared Runtime lives in `src/gameassetai/` and is bundled internally; do not add
duplicate root or Skill copies. Unverified historical Blender modules under `archive/legacy/` are
not imported or bundled. Task-specific Blender code stays in an isolated work/output context
unless a reviewed durable responsibility justifies adoption into active source.
