# Repository Restructure Record — 2026-11-10

## Baseline

- Repository: `jiwoo7158/GameAssetAI`
- Protected HEAD: `1029f9630b072b8e183072e83834b95c87fab05c`
- Baseline: 641 tracked files, 45 active Skill folders, 489 Python files.
- Recovery branch: `backup/pre-foundation-20261110`
- Work branch: `refactor/gameassetai-foundation`

## Retained and integrated

- Workspace link/path safety and Profile persistence concepts, redesigned without `--force`.
- Hash/no-overwrite distribution principles, redesigned as a four-Skill product bundle with an
  explicit product-wide backup update.
- Bounded static creation/revision, character template, Rig, Mixamo/Action, FBX, and core 2D
  helpers, moved into the shared internal Blender runtime.
- Blender Add-on source as an optional bounded UI/execution layer.

## Removed from active structure

- Historical B1-B8/M-stage roadmaps, session state, audits, validation narratives, and milestone
  harnesses. Git and the recovery branch preserve them.
- 45 narrow user-visible Skill folders and their duplicated Python payloads.
- Optional pass/collider/LOD micro-Skills and tests that displaced the core product surface.
- Duplicate root/Skill implementations, tracked bytecode/cache files, old template artifacts, and
  the force-overwrite Workspace path.

## Deliberate limitations

This foundation does not select the first new generator or accepted target asset. Retained Blender
code preserves engineering value but remains bounded by `docs/capabilities.md`. Live Blender,
Codex discovery, Add-on installation, external AI, and UnityWorkbench are not revalidated by this
offline restructure.

## Result

- Final tracked files: 141 (from 641).
- Final Python files: 110 (from 489).
- Final user-facing Skill folders: 4 (from 45).
- Current docs: 9 (from 80).
- Validation: 46 offline tests passed; repository structure/catalog/template/Skill/Python
  validation passed; staged diff whitespace check passed.
