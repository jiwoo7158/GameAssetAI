# GameAssetAI Workspace Instructions

This is a persistent user Workspace, not the GameAssetAI development repository.

Before game-specific work:

1. Read `config/active-profile.json`.
2. Load the exact referenced JSON Profile from `profiles/`.
3. Apply its style, project, preservation, rig/animation, and output rules only where specified.
4. Inspect the current Blender Scene before modifying existing data.

If no Profile is active, do not invent game-specific art direction, budgets, Rig policy, or export
destinations. Catalog registration is not proof that a generator exists. Report unsupported work
honestly.

Existing Blender files and game projects may live anywhere. Paths in `config/projects.json` are
bookmarks, not write authorization. Never move or modify a project unless the current request
requires it. `unity-workbench` is optional and must only be used on explicit request.

Store generated deliverables under `outputs/<game>/<asset-category>/<run-id>/` unless the user
selects another destination. Outputs are disposable from GameAssetAI's perspective: deleting the
entire `outputs/` tree must not affect Profiles, settings, installed Skills, catalogs, or new work.
Do not treat a prior run as hidden state. A user may explicitly select an earlier artifact as a
new source.

Preserve existing meshes, Armatures, Actions, materials, images, and external files. Prefer copies
or verified checkpoints before destructive changes. Stop downstream rigging, animation, 2D, and
export work when the source fails visible or semantic review.
