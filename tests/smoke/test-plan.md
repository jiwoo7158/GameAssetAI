# Initial Smoke Test Plan

These tests are intentionally simple.

## 1. Repository

- run `python scripts/validate_repo.py`
- expected: repository structure OK
- run `python -B -m unittest discover -s tests/workspace -p "test_*.py" -v`
- expected: all runnable offline tests pass; any link-related skips are reported explicitly

## 2. Workspace

- create a new workspace with `scripts/create_workspace.py`
- expected: workspace contains AGENTS, profiles, config, notes
- run `scripts/validate_workspace.py` against it; null active profile is valid initially
- see `docs/workspace-contract.md` for preservation and `--force` boundaries

## 3. Blender MCP

With Blender open:

Use a dedicated scratch scene and follow `docs/blender-verification.md`. This manual
section is **not yet run**; the offline suite does not replace it.

- ask Codex to inspect the active scene
- create or select a cube
- ask Codex to report its transform
- make one harmless transform change
- verify the Blender scene actually changed

Record the tested MCP implementation and version in a new development note.

## 4. Profile behavior

Offline creation/switch/reference reading has regression coverage. The following Codex
client behavior still requires manual verification in a generated personal workspace.

- create one game profile
- make it active
- ask Codex to summarize the active profile
- switch to another profile
- confirm the context changes

Do not begin production asset skills until these foundation checks work.
