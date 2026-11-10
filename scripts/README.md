# Development Entrypoints

- `gameassetai.py`: catalog, Workspace/Profile, specification, output, and package commands.
- `create_workspace.py`: safe compatibility wrapper; there is no force-overwrite mode.
- `validate_workspace.py`: read-only compatibility wrapper.
- `validate_repo.py`: current product layout and offline contract validation.

Blender runtime modules live in `src/gameassetai/blender/` and are bundled internally; do not add
duplicate root or Skill copies.
