---
name: blender-copy-action
description: Preview and create one explicitly named, unbound persistent copy of an existing Blender Action while preserving the source and all current/NLA references. Use to organize or extract an existing animation non-destructively; do not use it to rename, rebind, retarget, edit, import, or export animation.
---

# Copy an Action without rebinding

This Skill only duplicates one existing Action under an explicit unused name. The source
Action and every current Action/NLA reference remain unchanged. The copy is deliberately
unbound and receives a fake user so it survives saving. Inspection is not authorization.

## Request and preview

Require an exact Scene name, source Action name and target Action name. The supported
request must explicitly set `preserve_source=true`, `bind_copy=false`, and
`set_fake_user=true`. Reject target names longer than 255 UTF-8 bytes because Blender
5.0.1 otherwise truncates them silently. Never auto-suffix, replace, rename, bind, or
infer a name from game-specific policy.

Read and execute these packaged helpers in order in one shared globals/locals dictionary:

1. `scripts/inspect_animation.py`
2. `scripts/plan_action_copy.py`
3. `scripts/action_copy.py`

Call `preview_action_copy(request)` first. It makes no changes and returns a
`candidate_for_review` with request, inventory and detailed Action-content hashes plus
the existing current/NLA references that must remain untouched. Report the exact source,
target, persistence behavior and references.

## Apply and verify

Call `apply_action_copy(plan, authorization=True)` only after the user authorizes that
exact candidate. The helper re-previews immediately and refuses a stale source, changed
references, missing source, target collision, malformed request, or missing authorization.

On `created`, verify that the source still exists, the target is an independent Action,
the target has no current/NLA references, the source references are unchanged, and the
target content hash matches the source content. Do not bind the copy, remove the source,
save the blend file, export, or start editing unless separately requested.

## Boundaries

This is a conservative Action datablock copy, not clip extraction by frame range. It does
not split takes, rename the source, change slots, create NLA strips, assign an Action,
judge loop continuity, evaluate poses, bake, retarget, or establish Unity clip settings.
Unsupported custom-property values or non-finite animation data refuse. If an apply call
has an uncertain transport result, re-inventory by exact target name before retrying.
