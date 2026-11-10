---
name: gameassetai-modify-asset
description: Inspect and revise an explicitly selected existing game asset with copy-first preservation, including bounded mesh, material, rig, Mixamo, and Action workflows.
---

# GameAssetAI Modify Asset

Use this Skill for an explicitly selected existing asset and a requested proportion, silhouette,
part, color, material, Rig, or animation change. Route Profile administration to
`gameassetai-workspace`, new-source creation to `gameassetai-create-asset`, and result allocation or
publication to `gameassetai-output-asset`.

1. Validate the Workspace, load the active Profile, and resolve the exact source path/object.
2. Read the text request, selected style, and user references. Label each image's role; do not
   confuse a pre-production AI reference with a Blender preview or final 2D output.
3. Decide whether the request is asset-local or an explicit durable game rule. Do not update the
   Profile for a one-off edit.
4. Inspect the current Blender Scene and create a copy or verified checkpoint before material
   changes. Preserve the original unless replacement was explicitly requested.
5. Use only a bounded helper whose contract matches the asset, then validate preservation,
   structure, and visible/semantic invariants from relevant views.
6. Keep the existing concrete asset id. Continue an in-progress task only when its exact path and
   manifest validate and its recorded inputs still exist. If a completed result will be changed or
   compared, allocate the next numbered task with a descriptive purpose and preserve the old one.

For development work, a change that still answers the same validation question reuses the current
experiment; a genuinely different question or acceptance criterion requires a separate experiment.
Inspect experiment metadata rather than guessing from folder names, and ask when the distinction is
unclear. For user work, use the active Profile game id and official catalog category. Never create
a new asset id solely to express `v2`, a changed color, proportion, material, or other revision.

The Runtime retains narrow helpers for static semantic replacement, transform and mesh cleanup,
humanoid inspection, Mixamo-oriented preparation, Action copying/editing, and template-character
revision. It does not provide arbitrary semantic mesh editing, automatic clothing/hair fitting,
facial work, or general nonhumanoid Rig generation. Existing suitable Rigs and Actions are
first-class inputs; never delete or replace them merely to simplify the task.

If the request exceeds an implemented contract, narrow it with the user or report the capability
gap. On failure, preserve the checkpoint and source, state what changed before failure, and do not
continue to output as though the asset were accepted. A moved or deleted output blocks only that
explicit continuation; do not recreate it or block an independent new task.
