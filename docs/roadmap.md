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

Closeout recorded on 2026-11-10: the foundation commit reported 141 tracked files, 110 Python
files, four intended product Skills, and nine current documents. Its then-current repository
validation and 46 offline tests passed, including installed Runtime execution, output-tree
deletion/recreation, and retained static/character/2D/FBX contract regressions. This is historical
closeout evidence rather than a claim about the current checkout. Live Blender/MCP, Codex client
discovery, the retained Add-on, and engine import were not rerun in that package.

## Completed foundation-hardening work package (2026-11-11)

- Requirements advanced: `REQ-SPEC`, `REQ-WORKSPACE`, `REQ-DISTRIBUTION`, `REQ-OUTPUT`, and
  `REQ-SAFE`.
- Existing implementation to reuse: the four-Skill bundle contract, JSON Profile persistence,
  atomic JSON publication, link/reparse-point detection, no-overwrite output allocation, and the
  focused offline test suite.
- Concrete gaps: the Workspace Skill is present locally but excluded by an over-broad ignore
  pattern and absent from Git; Profiles lack a validated field-level update path; output and Skill
  installation paths do not consistently reject linked intermediate components; onboarding and
  reference-image guidance are incomplete; and no GitHub Actions workflow verifies the foundation.
- Non-goals: changing the product architecture or catalog, implementing a new asset generator,
  introducing an AI provider, running long Blender art experiments, creating UnityWorkbench, or
  modifying a real user Workspace or game project.
- Affected files: `.gitignore`; existing Workspace, output, distribution, and CLI modules; the four
  existing Skill instructions; Workspace template instructions; focused tests; current user and
  engineering documentation; and one CI workflow.
- Validation assets: repository-tracked source plus isolated temporary Workspaces, output trees,
  bundles, installed Skill directories, collision cases, and supported link/junction fixtures.
- Acceptance criteria:
  1. All four Skill sources are tracked, frontmatter-valid, packaged, installed, and executable
     without a development-checkout path.
  2. Profile fields can be read and explicitly updated with schema validation, preservation of
     untouched fields, atomic publication, and no implicit legacy conversion.
  3. Output and distribution operations reject linked path components, escape attempts, and
     collisions without damaging existing data; deleting `outputs/` remains safe.
  4. Workspace and Skill guidance consistently distinguishes durable Profile rules, per-asset
     requests, user-provided AI references, Blender previews, and final 2D outputs.
  5. Linux and Windows CI run repository validation and the complete offline test suite, including
     a regression that fails when any required Skill source is absent from Git.
- Unresolved user decisions: none for this bounded hardening package. Live Codex client discovery,
  Blender/MCP execution, Windows junction creation where the runner lacks permission, and engine
  behavior remain separate environment gates and must be reported rather than inferred.

Closeout recorded on 2026-11-11: pull request #2 was merged to `master` as `b8ee12c`. Repository
validation and 54 offline tests passed locally, with two Windows symlink cases skipped because the
process lacked symlink privilege; equivalent Windows Junction refusal tests passed. The actual
GitHub Actions run passed on Linux and Windows. The package was also built, validated, installed
under an isolated temporary `.codex/skills` root, and its installed catalog command ran without a
development-checkout dependency. Live Codex host discovery, Blender/MCP execution, visual asset
quality, and engine behavior were not validated and remain incomplete environment/product gates.

## Implemented / Under Review — output-management foundation work package (2026-11-11)

- Requirements advanced: `REQ-STYLE`, `REQ-WORKSPACE`, `REQ-DISTRIBUTION`, `REQ-OUTPUT`, and
  `REQ-SAFE`.
- Existing implementation to reuse: the v2 Workspace marker and active JSON Profile, canonical
  catalog loader, atomic JSON publication, link/reparse-point checks, four-Skill bundle builder,
  installed Runtime entrypoint, and Linux/Windows offline CI.
- Concrete gaps: project-scoped onboarding can install `.codex/skills` before a Workspace is
  recognized; Profile style fields do not verify registered ids or 3D/2D dimensions; output runs
  use date/UUID ids and omit the asset-id level; development experiments have no official
  path/metadata contract; and current Skills do not require an explicit new-versus-existing
  experiment decision.
- Non-goals: Blender execution, asset or sprite generation, visual-quality experiments, a new
  generation provider, output migration/backup, UnityWorkbench work, dynamic prompt management,
  or changes to the product catalog and overall provider architecture.
- Affected files: existing catalog, Workspace, output, distribution, filesystem, and CLI modules;
  focused tests; `.gitignore`; root and Workspace instructions; the four existing Skills; current
  architecture, requirements, Workspace, distribution, quality, capability, and user guidance.
- Validation assets: only isolated temporary repository-shaped roots, Workspaces, experiment and
  user task trees, bundles, project-scoped installations, deletion/collision cases, and supported
  link/Junction fixtures. No Blender asset, real user Workspace, repository `output/`, or external
  project is a test target.
- Representative asset: none. This package establishes storage and onboarding contracts and is
  not evidence for asset generation or visual quality.
- Acceptance criteria:
  1. Fresh project-scoped onboarding creates or connects and validates a Workspace before it
     installs and validates all four Skills; Profile creation and selection remain a later step.
  2. Profile create, load, update, select, and Workspace validation reject unknown or
     dimension-mismatched official style ids without changing the existing Profile.
  3. Development work uses
     `output/experiments/<experiment>/<category>/<asset>/<number>-<purpose>/`; user work uses
     `outputs/<game>/<category>/<asset>/<number>-<purpose>/`, with catalog categories and no
     date/UUID folder names.
  4. Experiment creation and reuse are explicit, experiment metadata records the validation goal,
     and the Runtime never guesses reuse from a similar name or creates a default experiment.
  5. Task allocation uses atomic directory creation, the current maximum local number, no
     overwrite, no unnecessary artifact subdirectories, and exact-path validation for continuing
     in-progress work.
  6. Moving or deleting any or all result trees cannot break Repository validation, package
     building, Profiles, or allocation of a new independent task.
  7. Documentation, Skills, Runtime, CLI, tests, and CI describe and enforce the same policy.
- Unresolved user decisions: the Runtime cannot decide whether two natural-language validation
  goals are semantically identical. It lists and validates experiment metadata; when the request
  does not establish new versus existing work, the agent must ask for the minimum clarification.

Implementation evidence recorded on 2026-11-11: repository validation and 68 offline tests passed. Two Windows
symlink cases were skipped because the local process lacks symlink privilege; equivalent Junction
refusal tests for output allocation and Skill installation passed. The suite exercised the actual
CLI for ordered project installation, installed-Runtime Profile and output commands, bundle
build/validation, experiment/task deletion and recreation, concurrent numbering, style-dimension
rejection, and legacy output read-only validation. No Repository `output/`, Blender asset, user
Workspace, or external project was created or modified. Live Codex host discovery, Blender/MCP,
visual quality, and engine behavior were outside this package and remain unverified. This package
remains under review in draft pull request #3 and is not complete until approved and merged.

## Implemented / Under Review — Workspace distribution and result lifecycle work package (2026-11-11)

- Requirements advanced: `REQ-WORKSPACE`, `REQ-DISTRIBUTION`, `REQ-OUTPUT`, `REQ-SAFE`, and
  `REQ-QUALITY`.
- Existing implementation to reuse: four-Skill self-contained bundle construction and validation,
  installed Runtime entrypoints, v2 Workspace/Profile persistence, output experiment and numbered
  task allocation, link/Junction rejection, atomic JSON publication, and Linux/Windows CI.
- Concrete gaps: project and user Skill guidance still uses the superseded `.codex/skills`
  locations; there is no allowlisted `dist/workspace` product tree or safe initialization path for
  a cloned distribution; output allocation is limited to Workspace-internal storage; and artifact
  path allocation, manifest registration, and reviewed task-state transitions lack a shared API.
- Non-goals: publishing `dist/workspace` before this draft PR is approved and merged, creating a
  second Repository or distribution branch, adding an installer/updater service or database,
  running Blender, producing an asset, validating visual quality, introducing a provider, or
  modifying a real user Workspace.
- Affected files: existing distribution, Workspace, output, filesystem, and CLI modules; packaging
  source files; focused tests and repository validation; CI plus one master-only distribution
  workflow; root/Workspace/Skill instructions; and current architecture, requirements,
  capabilities, quality, distribution, Workspace, and user guidance.
- Validation assets: isolated temporary source checkouts, generated distribution trees, simulated
  Git clones, user-scoped Skill copies, internal/external output roots, manifests, update fixtures,
  and supported link/Junction cases. No real Workspace, Repository `output/`, Blender file, or
  external project is a test target.
- Representative asset: none. File and deployment contracts are tested without claiming asset or
  visual-quality evidence.
- Acceptance criteria:
  1. Official local discovery paths are `.agents/skills` for project scope and
     `$HOME/.agents/skills` for user scope; existing `.codex/skills` folders are left untouched.
  2. One allowlisted distribution tree contains product-managed instructions, all four
     self-contained Skills, initialization templates, ignore rules, and source/version metadata,
     and runs without the development checkout.
  3. A verified distribution clone can be initialized idempotently without overwriting Profiles,
     settings, notes, outputs, or other existing personal files.
  4. The default internal output root, configured Workspace root, Profile override, and explicit
     one-task root follow a documented priority and preserve the existing category/asset/number
     hierarchy with link, escape, and collision checks.
  5. Artifact subdirectories are created only on demand; actual files can be registered once; and
     manifest state changes are atomic, validated, and do not treat automated tests as quality
     acceptance.
  6. Pull requests build and validate the distribution without publishing it. Only a successful
     approved `master` push may append a normal commit to `dist/workspace`; the workflow never
     force-pushes or targets another branch.
  7. Repository validation, the complete offline suite, and Linux/Windows CI pass while result
     movement/deletion remains independent of new work and packaging.
- Unresolved environment gates: live Codex Desktop and VS Code discovery, GitHub-hosted deployment
  permissions until the approved merge triggers them, Blender/MCP behavior, movable real `.blend`
  dependencies, visual acceptance, and engine import remain unverified and must be reported as
  such.

Implementation evidence recorded on 2026-11-11: repository validation and 80 offline tests passed;
two Windows symlink tests were skipped because the local process lacks symlink privilege, while
the equivalent output-root, output-intermediate, and Skill-installation Junction checks passed.
The suite built and validated the allowlisted distribution, ran its vendored Runtime, initialized
a simulated clone without replacing personal data, copied the same Skills to user scope, preserved
ignored Profile/note/output data through a fast-forward Pull, enforced official output-root
precedence, and exercised artifact reservation, registration, release, and reviewed state changes.
An additional CLI build/validation of the generated distribution passed in an isolated temporary
directory. No real Workspace, Repository `output/`, Blender asset, external project, or
`dist/workspace` branch was created or modified. The dedicated Skill quick validator could not run
because PyYAML is absent from the local tool environment; repository frontmatter validation,
bundle hash validation, installed-manifest validation, and vendored CLI execution passed instead.
This package remains under review in draft pull request #3 and is not complete until user approval
and merge. Hosted Linux/Windows CI results for these commits are recorded only after push.

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
