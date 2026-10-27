---
name: blender-replace-current-action
description: Replace one explicitly identified current Blender Action on one Armature with one protected unbound Action, preserving both Actions and returning an exact rollback receipt. Use for a deliberate current-Action swap when NLA and drivers are absent; do not use for empty-target binding, Action deletion, NLA editing, retargeting, export, or Unity configuration.
---

# Replace Current Action

Swap one exact current Action for one exact unbound Action without changing either Action,
the Rig, selection, mode or files. Return a content-bound receipt that can restore only
the exact previous binding.

## Inputs and refusal

Require exact Scene, Armature, current/replacement Action and both Action-slot names.
Require `replacement_policy=CURRENT_ONLY`, `preserve_both_actions=true`, and
`set_fake_users=true`.

Both Actions must already be fake-user protected and have exactly one Object slot. The
current Action must be bound only as the named Armature's current Action; the replacement
must be completely unbound. The target Object must have no NLA tracks or drivers and its
Armature data must have no animation state. Refuse inferred targets, mismatched current
bindings, additional references, changed Action content, stale previews, missing
authorization, or a rollback receipt that does not exactly match current state.

## Execution

1. Inspect Blender addon and Scene state.
2. Execute these helpers in one shared globals/locals dictionary:
   - `scripts/bind_action_empty.py`
   - `scripts/replace_action_current.py`
3. Build `gameassetai.action-replacement-request.v1` and call
   `preview_action_replacement(request)`.
4. Report both Action fingerprints, exact slots, target-state hash and blockers. Preview
   is never authorization.
5. Call `apply_action_replacement(plan, authorization=True)` only after explicit
   authorization for that exact plan. Retain its complete
   `gameassetai.action-replacement-receipt.v1`.
6. Verify that the replacement is the exact current Action, the previous Action is
   protected and unbound, and both Action fingerprints are unchanged.
7. If the user explicitly requests undo, call
   `rollback_action_replacement(receipt, authorization=True)` and verify restoration of
   the exact previous Action/slot with the replacement protected and unbound.

Only the target's current Action binding may change. Never delete either Action, overwrite
curves, create NLA tracks, alter the Rig, retarget, export, save, or claim deformation or
Unity compatibility. Use the separate empty-target binding workflow when no current Action
exists.
