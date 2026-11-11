# Requirements

These stable ids express product obligations; they do not imply implementation.

| ID | Requirement |
| --- | --- |
| `REQ-PRODUCT` | Installable, style-driven Codex workflow for usable game assets. |
| `REQ-CATALOG` | Extensible data catalog with separate registration, implementation, and evidence state. |
| `REQ-STYLE` | Independent extensible 3D and 2D styles plus game-specific Profile overrides. |
| `REQ-SPEC` | Shared structured input whose normal flow is text plus a style preset plus user-provided reference images, with explicit reference roles, asset type, providers, revision, Rig/animation, and outputs. |
| `REQ-GENERATION` | Replaceable Blender/local/external providers; asset type is not tied to one provider. |
| `REQ-MODIFY` | Existing assets and natural-language revision are first-class, with preservation and explicit scope. |
| `REQ-CHARACTER` | Humanoid and nonhumanoid character paths without a universal anatomy or skeleton assumption. |
| `REQ-ANIMATION` | Existing Rig/Action, Mixamo-eligible, cleanup, editing, and asset-specific animation paths. |
| `REQ-2D` | Optional preview, pixel/cel/toon, direction, action-frame, and sprite outputs from accepted 3D. |
| `REQ-OUTPUT` | Separate disposable development experiments and user game outputs, with configurable explicit roots, catalog categories, concrete asset ids, atomic local task numbers, purpose names, on-demand artifact directories, no overwrite, registered files, and reviewed local manifests. |
| `REQ-WORKSPACE` | User-selected persistent Workspace with Profiles, project bookmarks, settings, notes, and outputs. |
| `REQ-DISTRIBUTION` | One allowlisted `dist/workspace` product tree plus self-contained Skills using official `.agents/skills` roots, declared runtime/catalog/templates, verified clone initialization, safe install/update, and preserved Git history. |
| `REQ-INTEGRATION` | Optional UnityWorkbench and external projects only through explicit paths and authorization. |
| `REQ-SAFE` | Inspect-first, copy/checkpoint, rollback, source preservation, and no hidden output dependency. |
| `REQ-QUALITY` | Structural plus visible/semantic acceptance; engine claims require engine evidence. |
| `REQ-COST` | Useful local foundation without a paid generation dependency. |

## Foundation acceptance

- The catalog can add a type or child through JSON without a Python file or Skill.
- Asset Specifications validate against catalog and style ids without assuming humanoids.
- Workspace creation accepts a custom path, reconnects safely, refuses unknown nonempty folders,
  recognizes legacy Workspaces without mutation, and never provides a force-overwrite path.
- Profile create/select/clear/list/get/set persists through validated files independently of chat
  sessions; an explicit field update preserves all unnamed settings. Official style fields accept
  only catalog ids of the correct 3D/2D dimension, while freeform game direction remains separate.
- Development results allocate under
  `output/experiments/<experiment>/<category>/<asset>/<number>-<purpose>/`; user results allocate
  under `outputs/<game>/<category>/<asset>/<number>-<purpose>/`. Experiment reuse is explicit and
  based on validation-goal metadata, not folder-name similarity.
- Moving or deleting any or all result directories leaves Repository validation, Workspace
  validation, Profiles, catalog, installed Skills, package building, and independent new task
  allocation intact. Continuing a missing task fails only that exact continuation.
- User output-root precedence is explicit one-task selection, Profile override, Workspace
  preference, then internal `outputs/`. External roots must already exist, cannot escape through a
  link/Junction, and are never silently recreated after movement or deletion.
- A task creates `models/`, `previews/`, `sprites/`, or `exports/` only when requested. Only an
  existing nonempty reserved official artifact can be registered. Reservations and Manifest
  writes are atomic, and accepted/rejected states require distinct registered evidence that is
  still an existing nonempty real file inside the task at review time rather than a test result.
  A failed transition leaves the Manifest unchanged; later evidence movement/deletion preserves
  the historical review and independent-work behavior.
- Logical Asset Specification formats map explicitly to compatible artifact kinds/extensions.
  Broader artifact registration does not imply a generator, exporter, or engine-proven capability.
- Four product Skills build with a vendored runtime and no development checkout dependency.
- The generated Workspace distribution contains only allowlisted product files, validates after a
  normal Windows or Linux Git clone, and initializes ignored personal state without overwriting it.
- Project Skills live under `.agents/skills`; user Skills live under `$HOME/.agents/skills`.
  Existing `.codex/skills` installations are left untouched and are not claimed as current roots.
- Fresh project-scoped onboarding creates/connects and validates the Workspace before installing
  and validating its four Skills; Profile creation and selection occur afterward. User-scoped
  installation remains independent of Workspace creation.
- Existing installed Skills are never overwritten during install; update requires an explicit
  unused backup path and retains the previous installation.
- Current code contains no active B/M stage authority or hard-coded personal output path.
- Pull requests build and validate but do not publish. Only the master-push workflow may append a
  normal, non-force commit to `dist/workspace`.
