"""Replace one exact current Action with one protected unbound Action, with rollback."""
from __future__ import annotations

import bpy


ACTION_REPLACEMENT_SCHEMA = "gameassetai.action-replacement-request.v1"
_REPLACEMENT_KEYS = {"schema", "scene_name", "armature_name", "current_action",
                     "current_slot_identifier", "replacement_action",
                     "replacement_slot_identifier", "replacement_policy",
                     "preserve_both_actions", "set_fake_users"}


def _single_object_slot(action, identifier):
    slots = list(getattr(action, "slots", ()))
    return (len(slots) == 1 and getattr(slots[0], "target_id_type", None) == "OBJECT"
            and slots[0].identifier == identifier)


def _replacement_receipt_payload(receipt):
    return {key: value for key, value in receipt.items() if key != "receipt_sha256"}


def preview_action_replacement(request):
    """Return a no-write plan for replacing one exact current Action only."""
    report = {"schema": "gameassetai.action-replacement-plan.v1", "status": "error",
              "errors": [], "reviews": [], "authorization": False}
    if not isinstance(request, dict):
        report["errors"].append("Request must be an object")
        return report
    unknown = sorted(set(request) - _REPLACEMENT_KEYS)
    missing = sorted(_REPLACEMENT_KEYS - set(request))
    if unknown:
        report["errors"].append("Unknown request fields: " + ", ".join(unknown))
    if missing:
        report["errors"].append("Missing request fields: " + ", ".join(missing))
    if unknown or missing:
        return report
    if request["schema"] != ACTION_REPLACEMENT_SCHEMA:
        report["errors"].append("Unsupported request schema")
    for key in ("scene_name", "armature_name", "current_action",
                "current_slot_identifier", "replacement_action",
                "replacement_slot_identifier"):
        value = request[key]
        if not isinstance(value, str) or not value or value != value.strip():
            report["errors"].append(f"{key} must be an exact nonempty name")
    if request["current_action"] == request["replacement_action"]:
        report["errors"].append("Current and replacement Actions must differ")
    if request["replacement_policy"] != "CURRENT_ONLY":
        report["errors"].append("Only replacement_policy=CURRENT_ONLY is supported")
    for key in ("preserve_both_actions", "set_fake_users"):
        if request[key] is not True:
            report["errors"].append(f"This workflow requires {key}=true")
    if report["errors"]:
        return report
    scene = bpy.data.scenes.get(request["scene_name"])
    target = scene.objects.get(request["armature_name"]) if scene else None
    current = bpy.data.actions.get(request["current_action"])
    replacement = bpy.data.actions.get(request["replacement_action"])
    if target is None or target.type != "ARMATURE":
        report["errors"].append("Target Armature not found in the named Scene")
    if current is None:
        report["errors"].append("Current Action not found")
    if replacement is None:
        report["errors"].append("Replacement Action not found")
    if report["errors"]:
        return report
    state = _animation_state(target)
    if (state["action"] != current.name
            or state["slot"] != request["current_slot_identifier"]):
        report["errors"].append("Target current Action or slot does not match the request")
    if state["nla_tracks"]:
        report["errors"].append("Target Armature has NLA tracks")
    if state["drivers"]:
        report["errors"].append("Target Armature has Object animation drivers")
    armature_state = _animation_state(target.data)
    if armature_state["action"] is not None or armature_state["nla_tracks"] or armature_state["drivers"]:
        report["errors"].append("Target Armature data has animation state")
    if _action_references(current) != ([target.name], []):
        report["errors"].append("Current Action must be bound only as the target's current Action")
    if _action_references(replacement) != ([], []):
        report["errors"].append("Replacement Action must be completely unbound")
    if not current.use_fake_user or not replacement.use_fake_user:
        report["errors"].append("Both Actions must already be fake-user protected")
    if not _single_object_slot(current, request["current_slot_identifier"]):
        report["errors"].append("Current Action requires the exact single Object slot")
    if not _single_object_slot(replacement, request["replacement_slot_identifier"]):
        report["errors"].append("Replacement Action requires the exact single Object slot")
    if report["errors"]:
        return report
    candidate = {"operation": "replace_exact_current_action",
                 "replacement_policy": "CURRENT_ONLY",
                 "current_action_sha256": action_content_fingerprint(current),
                 "replacement_action_sha256": action_content_fingerprint(replacement),
                 "target_state_sha256": _binding_digest({"object": state,
                                                           "data": armature_state}),
                 "request_sha256": _binding_digest(request)}
    report.update({"status": "candidate_for_review", "request": dict(request),
                   "candidate": candidate})
    report["reviews"].append("Both Actions remain protected; only the target's current binding changes")
    report["reviews"].append("Rollback requires the exact receipt and unchanged Actions/binding")
    return report


def apply_action_replacement(plan, authorization=False):
    """Swap one fresh exact current binding and return a rollback receipt."""
    result = {"schema": "gameassetai.action-replacement-result.v1",
              "status": "error", "errors": []}
    if authorization is not True:
        result["errors"].append("Explicit authorization=true is required")
        return result
    if (not isinstance(plan, dict)
            or plan.get("schema") != "gameassetai.action-replacement-plan.v1"
            or plan.get("status") != "candidate_for_review"):
        result["errors"].append("A candidate_for_review plan is required")
        return result
    request, candidate = plan.get("request"), plan.get("candidate")
    fresh = preview_action_replacement(request) if isinstance(request, dict) else None
    if (not fresh or fresh.get("status") != "candidate_for_review"
            or fresh.get("candidate") != candidate):
        result["errors"].append("Action replacement preview is stale")
        return result
    scene = bpy.data.scenes[request["scene_name"]]
    target = scene.objects[request["armature_name"]]
    current = bpy.data.actions[request["current_action"]]
    replacement = bpy.data.actions[request["replacement_action"]]
    data = target.animation_data
    try:
        data.action = replacement
        data.action_slot = replacement.slots[0]
        if (_animation_state(target)["action"] != replacement.name
                or _animation_state(target)["slot"] != request["replacement_slot_identifier"]
                or _action_references(current) != ([], [])
                or _action_references(replacement) != ([target.name], [])):
            raise RuntimeError("Blender did not create the exact requested replacement")
        if (action_content_fingerprint(current) != candidate["current_action_sha256"]
                or action_content_fingerprint(replacement) != candidate["replacement_action_sha256"]):
            raise RuntimeError("Action content changed during replacement")
        receipt = {"schema": "gameassetai.action-replacement-receipt.v1",
                   "scene_name": scene.name, "armature_name": target.name,
                   "previous_action": current.name,
                   "previous_slot_identifier": request["current_slot_identifier"],
                   "replacement_action": replacement.name,
                   "replacement_slot_identifier": request["replacement_slot_identifier"],
                   "replacement_policy": "CURRENT_ONLY",
                   "previous_action_sha256": candidate["current_action_sha256"],
                   "replacement_action_sha256": candidate["replacement_action_sha256"]}
        receipt["receipt_sha256"] = _binding_digest(receipt)
        result.update({"status": "replaced", "receipt": receipt,
                       "both_actions_preserved": True})
        return result
    except Exception as exc:
        if data.action == replacement:
            data.action = current
            data.action_slot = current.slots[0]
        result["errors"].append(str(exc))
        return result


def rollback_action_replacement(receipt, authorization=False):
    """Restore the previous Action only from one authentic unchanged receipt."""
    result = {"schema": "gameassetai.action-replacement-rollback-result.v1",
              "status": "error", "errors": []}
    if authorization is not True:
        result["errors"].append("Explicit authorization=true is required")
        return result
    required = {"schema", "scene_name", "armature_name", "previous_action",
                "previous_slot_identifier", "replacement_action",
                "replacement_slot_identifier", "replacement_policy",
                "previous_action_sha256", "replacement_action_sha256", "receipt_sha256"}
    if not isinstance(receipt, dict) or set(receipt) != required:
        result["errors"].append("Exact action-replacement receipt is required")
        return result
    if (receipt["schema"] != "gameassetai.action-replacement-receipt.v1"
            or receipt["replacement_policy"] != "CURRENT_ONLY"
            or receipt["receipt_sha256"] != _binding_digest(_replacement_receipt_payload(receipt))):
        result["errors"].append("Action-replacement receipt is invalid")
        return result
    scene = bpy.data.scenes.get(receipt["scene_name"])
    target = scene.objects.get(receipt["armature_name"]) if scene else None
    previous = bpy.data.actions.get(receipt["previous_action"])
    replacement = bpy.data.actions.get(receipt["replacement_action"])
    if target is None or target.type != "ARMATURE" or previous is None or replacement is None:
        result["errors"].append("Receipt target or Action no longer exists")
        return result
    data = target.animation_data
    slot = getattr(data, "action_slot", None) if data else None
    if (data is None or data.action != replacement
            or getattr(slot, "identifier", None) != receipt["replacement_slot_identifier"]
            or data.nla_tracks or data.drivers
            or _action_references(replacement) != ([target.name], [])
            or _action_references(previous) != ([], [])):
        result["errors"].append("Current replacement does not exactly match the receipt")
        return result
    if (not _single_object_slot(previous, receipt["previous_slot_identifier"])
            or not _single_object_slot(replacement, receipt["replacement_slot_identifier"])
            or action_content_fingerprint(previous) != receipt["previous_action_sha256"]
            or action_content_fingerprint(replacement) != receipt["replacement_action_sha256"]):
        result["errors"].append("Action content or slots changed after replacement")
        return result
    try:
        data.action = previous
        data.action_slot = previous.slots[0]
        if (_action_references(previous) != ([target.name], [])
                or _action_references(replacement) != ([], [])
                or action_content_fingerprint(previous) != receipt["previous_action_sha256"]
                or action_content_fingerprint(replacement) != receipt["replacement_action_sha256"]):
            raise RuntimeError("Rollback did not restore the exact previous binding")
        result.update({"status": "rolled_back", "both_actions_preserved": True})
        return result
    except Exception as exc:
        if data.action == previous:
            data.action = replacement
            data.action_slot = replacement.slots[0]
        result["errors"].append(str(exc))
        return result
# Retained bounded Blender capability; product support remains evidence-scoped.
