# GameAssetAI Product Roadmap

This roadmap replaces the historical B1-B8 and M-stage sequences. Those sequences remain
recoverable from Git history and are not active work-order authority.

## Completed foundation work package — repository and product foundation (2026-11-10)

- Requirements advanced: `REQ-PRODUCT`, `REQ-CATALOG`, `REQ-STYLE`, `REQ-SPEC`,
  `REQ-WORKSPACE`, `REQ-DISTRIBUTION`, `REQ-OUTPUT`, `REQ-SAFE`, and `REQ-QUALITY`.
- Existing implementation to reuse: link-safe Workspace validation; no-overwrite and hash-bound
  Skill deployment/update mechanics; artifact ownership rules; bounded Blender scene inspection,
  static creation/revision, humanoid/Mixamo/Action/FBX helpers; deterministic 2D render and sprite
  helpers; the persistently installable Blender Add-on.
- Concrete gap: the repository exposes 45 narrow Skills, duplicates Python implementations
  between `scripts/` and Skill folders, treats historical B/M documents as active authority,
  permits a destructive Workspace `--force` merge, has no data-driven product catalog or style
  registry, and has no self-contained product bundle that vendors shared runtime code from one
  source location.
- Non-goals: choosing or implementing the first new asset generation engine; completing a new
  character generator; subscribing to or calling an external AI service; creating a Unity
  workbench; modifying a real game project; public release; long Blender art experiments.
- Affected areas: root instructions and README; `docs/`; `src/gameassetai/`; `catalog/`;
  `packaging/`; user-facing `skills/`; `workspace-template/`; developer `scripts/`; focused
  offline tests; removal of obsolete narrow Skills, duplicated scripts, milestone tests, and
  historical active-state documents.
- Validation assets: isolated temporary Workspaces, profiles, output runs, generated install
  bundles, and deliberately deleted output trees. No user Workspace or external project is a
  test target.
- Acceptance criteria:
  1. Catalog and style registries validate and can be extended without a Python module.
  2. Asset specifications separate asset type, style, inputs, generation selection, revision,
     rig/animation, and outputs without assuming humanoids.
  3. Workspace create/connect/update preserves personal files; profile create/select/show works.
  4. Output run allocation is collision-safe and disposable without damaging configuration.
  5. A product Skill bundle is built from four task-oriented source Skills plus shared runtime,
     installs without a repository-path dependency, and passes an installed-runtime smoke test.
  6. Retained Blender capabilities are documented with bounded evidence labels; unimplemented
     generation and free-form modification are not advertised as supported.
  7. Repository validation and focused offline tests pass with no active B/M work-order reference.
- User decisions still open after this package: first production asset family, first generation
  provider/engine, and the first representative visual acceptance target. No choice is made here.

Closeout: the repository now has 141 tracked files, 110 Python files, four product Skills, and
nine current documents. Repository validation and 46 offline tests pass, including installed
runtime execution, output-tree deletion/recreation, and retained static/character/2D/FBX contract
regressions. Live Blender/MCP, Codex client discovery, the retained Add-on, and engine import were
not rerun in this foundation package and remain labeled accordingly in `docs/capabilities.md`.

## Candidate development areas after the foundation

These are product areas, not a fixed implementation sequence. Choose the next bounded package
with the user and a representative asset before coding it.

1. Production generation engines and provider selection.
2. Static asset creation and semantic revision breadth.
3. Humanoid, non-humanoid, creature, and dynamic-object character paths.
4. Equipment, attachment, clothing, hair, and replaceable parts.
5. Rig selection, adaptation, animation import/editing, and retargeting.
6. Environment, modular structure, terrain, vegetation, and VFX-mesh production.
7. Accepted 3D-to-2D direction rendering and animated sprite output.
8. Optional UnityWorkbench import/runtime review when explicitly requested.

Every future package must name the representative asset, visible invariants, structural and
preservation checks, acceptance evidence, non-goals, and any external dependency decision.
