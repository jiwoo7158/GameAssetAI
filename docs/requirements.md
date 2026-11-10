# Requirements

These stable ids express product obligations; they do not imply implementation.

| ID | Requirement |
| --- | --- |
| `REQ-PRODUCT` | Installable, style-driven Codex workflow for usable game assets. |
| `REQ-CATALOG` | Extensible data catalog with separate registration, implementation, and evidence state. |
| `REQ-STYLE` | Independent extensible 3D and 2D styles plus game-specific Profile overrides. |
| `REQ-SPEC` | Shared structured input for text, references, asset type, providers, revision, Rig/animation, and outputs. |
| `REQ-GENERATION` | Replaceable Blender/local/external providers; asset type is not tied to one provider. |
| `REQ-MODIFY` | Existing assets and natural-language revision are first-class, with preservation and explicit scope. |
| `REQ-CHARACTER` | Humanoid and nonhumanoid character paths without a universal anatomy or skeleton assumption. |
| `REQ-ANIMATION` | Existing Rig/Action, Mixamo-eligible, cleanup, editing, and asset-specific animation paths. |
| `REQ-2D` | Optional preview, pixel/cel/toon, direction, action-frame, and sprite outputs from accepted 3D. |
| `REQ-OUTPUT` | No-overwrite editable outputs with disposable run directories and descriptive manifests. |
| `REQ-WORKSPACE` | User-selected persistent Workspace with Profiles, project bookmarks, settings, notes, and outputs. |
| `REQ-DISTRIBUTION` | Self-contained installed Skills with declared runtime, catalog, template, safe install, update, and backup. |
| `REQ-INTEGRATION` | Optional UnityWorkbench and external projects only through explicit paths and authorization. |
| `REQ-SAFE` | Inspect-first, copy/checkpoint, rollback, source preservation, and no hidden output dependency. |
| `REQ-QUALITY` | Structural plus visible/semantic acceptance; engine claims require engine evidence. |
| `REQ-COST` | Useful local foundation without a paid generation dependency. |

## Foundation acceptance

- The catalog can add a type or child through JSON without a Python file or Skill.
- Asset Specifications validate against catalog and style ids without assuming humanoids.
- Workspace creation accepts a custom path, reconnects safely, refuses unknown nonempty folders,
  recognizes legacy Workspaces without mutation, and never provides a force-overwrite path.
- Profile create/select/clear/list persists through files independently of chat sessions.
- Output allocation uses unique game/category/run paths, and deleting `outputs/` leaves Workspace
  validation, Profiles, catalog, installed Skills, and future run creation intact.
- Four product Skills build with a vendored runtime and no development checkout dependency.
- Existing installed Skills are never overwritten during install; update requires an explicit
  unused backup path and retains the previous installation.
- Current code contains no active B/M stage authority or hard-coded personal output path.
