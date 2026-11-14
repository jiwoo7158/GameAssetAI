---
name: gameassetai-modify-asset
description: Inspect and revise an explicitly selected existing game asset through a copy-first, evidence-bounded Blender workflow without overstating unverified mesh, rig, or animation support.
---

# GameAssetAI Modify Asset

Use this Skill for an explicitly selected existing asset and a requested proportion, silhouette,
part, color, material, Rig, or animation change. Route Profile administration to
`gameassetai-workspace`, new-source creation to `gameassetai-create-asset`, and result allocation or
publication to `gameassetai-output-asset`.

Use the bundled CLI from the Skill's actual installation. From a project-scoped distribution root,
the shared entrypoint is `.agents/skills/gameassetai-workspace/scripts/gameassetai.py`; at user
scope resolve the copied `gameassetai-workspace/scripts/gameassetai.py`. Never assume that the
Workspace root contains the development-only `scripts/gameassetai.py`.

1. Validate the Workspace, load the active Profile, and resolve the exact source path/object.
2. Read the text request, selected style, and user references. Use a built-in reference-role id or
   a bounded lowercase portable custom id such as top/detail/material/silhouette; do not use a
   path or freeform prose as the role. Do not
   confuse a pre-production AI reference with a Blender preview or final 2D output.
3. Decide whether the request is asset-local or an explicit durable game rule. Do not update the
   Profile for a one-off edit.
4. Inspect the current Blender Scene and create a copy or verified checkpoint before material
   changes. Preserve the original unless replacement was explicitly requested.
5. Choose Blender native operations, bounded task-specific code, or a currently adopted helper or
   provider whose contract matches the asset. For a registered external tool, query the Workspace
   Skill's Tools registry and cached last-check status, then verify the current environment before
   use. Metadata alone is not installation or capability evidence; do not silently substitute a
   different tool when the user selected one. Then validate preservation, structure, and
   visible/semantic invariants from relevant views.
6. Keep the existing concrete asset id. Continue an in-progress task only when its exact path and
   manifest validate and its recorded inputs still exist. If a completed result will be changed or
   compared, allocate the next numbered task with a descriptive purpose and preserve the old one.

For development work, a change that still answers the same validation question reuses the current
experiment; a genuinely different question or acceptance criterion requires a separate experiment.
Inspect experiment metadata rather than guessing from folder names, and ask when the distinction is
unclear. For user work, use the active Profile game id and official catalog category. Never create
a new asset id solely to express `v2`, a changed color, proportion, material, or other revision.

The active Runtime does not currently adopt the historical static, humanoid, Mixamo, Action, or 2D
helper collection; those candidates are isolated and are not an execution fallback. Codex may
compose bounded task code for the exact revision, but one successful revision is not a reusable
capability claim. Arbitrary semantic mesh editing, automatic clothing/hair fitting, facial work,
and general nonhumanoid Rig generation remain unproved. Existing suitable Rigs and Actions are
first-class inputs; never delete or replace them merely to simplify the task.

Route each preserved revision artifact through the output Skill: obtain an official no-overwrite
path, register only the actual nonempty result, and record a reviewed status separately. Never
label a revision accepted from a successful script or structural test alone.

If the request exceeds an implemented contract, narrow it with the user or report the capability
gap. On failure, preserve the checkpoint and source, state what changed before failure, and do not
continue to output as though the asset were accepted. A moved or deleted output blocks only that
explicit continuation; do not recreate it or block an independent new task.
