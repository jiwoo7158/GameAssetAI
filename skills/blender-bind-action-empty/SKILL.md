---
name: blender-bind-action-empty
description: Bind one explicit, protected, currently unbound Blender Action to one explicit Armature whose current Action, NLA tracks and drivers are empty, then optionally undo that exact binding with a verified receipt. Use to activate a newly copied, baked or composed Action without replacing existing animation; do not use for Action replacement, NLA editing, retargeting, export, or Unity configuration.
---

# Bind Action To Empty Armature

Connect one existing Action to one empty Armature without changing the Action, Rig,
selection, mode, files or any existing animation. Return a content-bound receipt that can
undo only the exact binding created by this workflow.

## Inputs and refusal

Require exact Scene, Armature, Action and Action-slot names. Require
`binding_policy=EMPTY_ONLY`, `preserve_action=true`, and `set_fake_user=true`.

The Action must already be fake-user protected, completely unbound and have exactly one
Object slot. The target Object must be an Armature with no current Action, NLA tracks or
Object drivers; its Armature data must also have no animation state. Refuse inferred
targets, occupied targets, arbitrary/multiple slots, stale previews, changed Action
content, missing authorization, or a rollback receipt that does not exactly match the
current binding.

## Execution

1. Inspect Blender addon and Scene state.
2. Execute `scripts/bind_action_empty.py` in one shared globals/locals dictionary.
3. Build `gameassetai.action-binding-request.v1` and call
   `preview_action_binding(request)`.
4. Report the Action fingerprint, whether an empty animation-data block already exists,
   target, slot and blockers. Preview is never authorization.
5. Call `apply_action_binding(plan, authorization=True)` only after explicit authorization
   for that exact plan. Retain its complete `gameassetai.action-binding-receipt.v1`.
6. Verify the exact current Action/slot reference and unchanged Action content.
7. If the user explicitly requests undo, call
   `rollback_action_binding(receipt, authorization=True)` with the unchanged receipt and
   verify that the protected Action remains present and unbound.

Applying changes only the target's current Action binding. Rollback removes only that
binding and restores absence of the animation-data block when this workflow created it.
Never delete an Action, replace an existing Action, create NLA tracks, retarget, alter
curves or rigs, export, save, or claim Unity compatibility.
