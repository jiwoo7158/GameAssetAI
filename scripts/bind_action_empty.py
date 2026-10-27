"""Bind one protected unbound Action to one empty Armature, with receipt rollback."""
from __future__ import annotations

import hashlib
import json
import math

import bpy


ACTION_BINDING_SCHEMA = "gameassetai.action-binding-request.v1"
_REQUEST_KEYS = {"schema", "scene_name", "armature_name", "action_name",
                 "action_slot_identifier", "binding_policy", "preserve_action",
                 "set_fake_user"}


def _finite(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Action contains a non-finite numeric value")
    return value


def _curves(action):
    result = list(getattr(action, "fcurves", ()))
    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            for bag in getattr(strip, "channelbags", ()):
                result.extend(bag.fcurves)
    seen = set()
    return [curve for curve in result
            if not (curve.as_pointer() in seen or seen.add(curve.as_pointer()))]


def _rna_scalars(value, excluded=()):
    result = {}
    for prop in value.bl_rna.properties:
        if prop.identifier == "rna_type" or prop.identifier in excluded:
            continue
        if prop.type not in {"BOOLEAN", "INT", "FLOAT", "STRING", "ENUM"}:
            continue
        try:
            item = getattr(value, prop.identifier)
        except (AttributeError, TypeError, RuntimeError):
            continue
        if getattr(prop, "is_array", False):
            item = [(_finite(v) if isinstance(v, float) else v) for v in item]
        elif isinstance(item, float):
            item = _finite(item)
        result[prop.identifier] = item
    return result


def _custom(value):
    result = {}
    for key in sorted(value.keys()):
        item = value[key]
        if isinstance(item, (str, bool, int)) or item is None:
            result[key] = item
        elif isinstance(item, float):
            result[key] = _finite(item)
        elif hasattr(item, "to_list"):
            result[key] = [(_finite(v) if isinstance(v, float) else v)
                           for v in item.to_list()]
        else:
            raise ValueError(f"Unsupported Action custom property: {key}")
    return result


def _curve_snapshot(curve):
    return {"data_path": curve.data_path, "array_index": curve.array_index,
            "settings": _rna_scalars(curve, {"data_path", "array_index"}),
            "group": curve.group.name if curve.group else None,
            "keyframes": [{"co": [_finite(v) for v in point.co],
                            "handle_left": [_finite(v) for v in point.handle_left],
                            "handle_right": [_finite(v) for v in point.handle_right],
                            "settings": _rna_scalars(point, {"co", "handle_left", "handle_right"})}
                           for point in curve.keyframe_points],
            "samples": [[_finite(v) for v in point.co] for point in curve.sampled_points],
            "modifiers": [{"type": mod.type, "settings": _rna_scalars(mod, {"type"})}
                          for mod in curve.modifiers]}


def action_content_snapshot(action):
    curves = _curves(action)
    return {"action": _rna_scalars(action, {"name", "name_full", "users", "use_fake_user",
                                             "session_uid"}),
            "custom": _custom(action),
            "slots": [_rna_scalars(slot) for slot in getattr(action, "slots", ())],
            "layers": [{"settings": _rna_scalars(layer),
                        "strips": [{"settings": _rna_scalars(strip),
                                    "channelbag_slots": [bag.slot.identifier
                                                         for bag in getattr(strip, "channelbags", ())]}
                                   for strip in getattr(layer, "strips", ())]}
                       for layer in getattr(action, "layers", ())],
            "groups": [{"name": group.name, "settings": _rna_scalars(group, {"name"})}
                       for group in getattr(action, "groups", ())],
            "pose_markers": [{"name": marker.name, "frame": marker.frame,
                              "camera": marker.camera.name if marker.camera else None}
                             for marker in action.pose_markers],
            "curves": [_curve_snapshot(curve) for curve in curves]}


def action_content_fingerprint(action):
    payload = json.dumps(action_content_snapshot(action), ensure_ascii=False,
                         allow_nan=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _action_references(action):
    current, nla = [], []
    owners = []
    for obj in bpy.data.objects:
        owners.append(obj)
        if obj.data is not None:
            owners.append(obj.data)
        if obj.type == "MESH" and obj.data.shape_keys is not None:
            owners.append(obj.data.shape_keys)
    seen = set()
    for owner in owners:
        pointer = owner.as_pointer()
        if pointer in seen:
            continue
        seen.add(pointer)
        data = getattr(owner, "animation_data", None)
        if data is None:
            continue
        if data.action == action:
            current.append(owner.name)
        for track in data.nla_tracks:
            for strip in track.strips:
                if strip.action == action:
                    nla.append((owner.name, track.name, strip.name))
    return sorted(current), sorted(nla)


def _binding_digest(value):
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False,
                     sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _animation_state(owner):
    data = getattr(owner, "animation_data", None)
    if data is None:
        return {"exists": False, "action": None, "slot": None,
                "nla_tracks": 0, "drivers": 0}
    slot = getattr(data, "action_slot", None)
    return {"exists": True,
            "action": data.action.name if data.action else None,
            "slot": getattr(slot, "identifier", None),
            "nla_tracks": len(data.nla_tracks), "drivers": len(data.drivers)}


def _receipt_payload(receipt):
    return {key: value for key, value in receipt.items() if key != "receipt_sha256"}


def preview_action_binding(request):
    """Return a no-write, content-bound plan for the EMPTY_ONLY policy."""
    report = {"schema": "gameassetai.action-binding-plan.v1", "status": "error",
              "errors": [], "reviews": [], "authorization": False}
    if not isinstance(request, dict):
        report["errors"].append("Request must be an object")
        return report
    unknown = sorted(set(request) - _REQUEST_KEYS)
    missing = sorted(_REQUEST_KEYS - set(request))
    if unknown:
        report["errors"].append("Unknown request fields: " + ", ".join(unknown))
    if missing:
        report["errors"].append("Missing request fields: " + ", ".join(missing))
    if unknown or missing:
        return report
    if request["schema"] != ACTION_BINDING_SCHEMA:
        report["errors"].append("Unsupported request schema")
    for key in ("scene_name", "armature_name", "action_name", "action_slot_identifier"):
        value = request[key]
        if not isinstance(value, str) or not value or value != value.strip():
            report["errors"].append(f"{key} must be an exact nonempty name")
    if request["binding_policy"] != "EMPTY_ONLY":
        report["errors"].append("Only binding_policy=EMPTY_ONLY is supported")
    for key in ("preserve_action", "set_fake_user"):
        if request[key] is not True:
            report["errors"].append(f"This workflow requires {key}=true")
    if report["errors"]:
        return report
    scene = bpy.data.scenes.get(request["scene_name"])
    target = scene.objects.get(request["armature_name"]) if scene else None
    action = bpy.data.actions.get(request["action_name"])
    if target is None or target.type != "ARMATURE":
        report["errors"].append("Target Armature not found in the named Scene")
    if action is None:
        report["errors"].append("Action not found")
    if report["errors"]:
        return report
    state = _animation_state(target)
    if state["action"] is not None:
        report["errors"].append("Target Armature already has a current Action")
    if state["nla_tracks"]:
        report["errors"].append("Target Armature has NLA tracks")
    if state["drivers"]:
        report["errors"].append("Target Armature has Object animation drivers")
    armature_animation = _animation_state(target.data)
    if armature_animation["action"] is not None or armature_animation["nla_tracks"] or armature_animation["drivers"]:
        report["errors"].append("Target Armature data has animation state")
    current, nla = _action_references(action)
    if current or nla:
        report["errors"].append("Action must be completely unbound")
    if not action.use_fake_user:
        report["errors"].append("Action must already be fake-user protected")
    slots = list(getattr(action, "slots", ()))
    if len(slots) != 1 or getattr(slots[0], "target_id_type", None) != "OBJECT":
        report["errors"].append("Action requires exactly one Object slot")
    elif slots[0].identifier != request["action_slot_identifier"]:
        report["errors"].append("Action slot identifier does not match")
    if report["errors"]:
        return report
    candidate = {"operation": "bind_unbound_action_to_empty_armature",
                 "binding_policy": "EMPTY_ONLY",
                 "animation_data_existed_before": state["exists"],
                 "action_sha256": action_content_fingerprint(action),
                 "target_state_sha256": _binding_digest({"object": state,
                                                           "data": armature_animation}),
                 "request_sha256": _binding_digest(request)}
    report.update({"status": "candidate_for_review", "request": dict(request),
                   "candidate": candidate})
    report["reviews"].append("Binding changes the current Action but never deletes or replaces an Action")
    report["reviews"].append("Rollback requires the exact returned receipt and unchanged Action content")
    return report


def apply_action_binding(plan, authorization=False):
    """Apply one fresh EMPTY_ONLY plan and return a rollback receipt."""
    result = {"schema": "gameassetai.action-binding-result.v1", "status": "error",
              "errors": []}
    if authorization is not True:
        result["errors"].append("Explicit authorization=true is required")
        return result
    if (not isinstance(plan, dict) or plan.get("schema") != "gameassetai.action-binding-plan.v1"
            or plan.get("status") != "candidate_for_review"):
        result["errors"].append("A candidate_for_review plan is required")
        return result
    request, candidate = plan.get("request"), plan.get("candidate")
    fresh = preview_action_binding(request) if isinstance(request, dict) else None
    if (not fresh or fresh.get("status") != "candidate_for_review"
            or fresh.get("candidate") != candidate):
        result["errors"].append("Action binding preview is stale")
        return result
    scene = bpy.data.scenes[request["scene_name"]]
    target = scene.objects[request["armature_name"]]
    action = bpy.data.actions[request["action_name"]]
    try:
        data = target.animation_data_create()
        data.action = action
        data.action_slot = action.slots[0]
        state = _animation_state(target)
        if (state["action"] != action.name
                or state["slot"] != request["action_slot_identifier"]
                or state["nla_tracks"] or state["drivers"]):
            raise RuntimeError("Blender did not create the exact requested binding")
        if _action_references(action) != ([target.name], []):
            raise RuntimeError("Action references differ from the requested binding")
        if action_content_fingerprint(action) != candidate["action_sha256"]:
            raise RuntimeError("Action content changed during binding")
        receipt = {"schema": "gameassetai.action-binding-receipt.v1",
                   "scene_name": scene.name, "armature_name": target.name,
                   "action_name": action.name,
                   "action_slot_identifier": request["action_slot_identifier"],
                   "binding_policy": "EMPTY_ONLY",
                   "animation_data_existed_before": candidate["animation_data_existed_before"],
                   "action_sha256": candidate["action_sha256"]}
        receipt["receipt_sha256"] = _binding_digest(receipt)
        result.update({"status": "bound", "receipt": receipt,
                       "action_preserved": True, "replacement_performed": False})
        return result
    except Exception as exc:
        data = getattr(target, "animation_data", None)
        if data is not None and data.action == action:
            data.action = None
        if (not candidate["animation_data_existed_before"] and data is not None
                and data.action is None and not data.nla_tracks and not data.drivers):
            target.animation_data_clear()
        result["errors"].append(str(exc))
        return result


def rollback_action_binding(receipt, authorization=False):
    """Unbind exactly one unchanged binding described by an authentic receipt."""
    result = {"schema": "gameassetai.action-binding-rollback-result.v1",
              "status": "error", "errors": []}
    if authorization is not True:
        result["errors"].append("Explicit authorization=true is required")
        return result
    required = {"schema", "scene_name", "armature_name", "action_name",
                "action_slot_identifier", "binding_policy",
                "animation_data_existed_before", "action_sha256", "receipt_sha256"}
    if not isinstance(receipt, dict) or set(receipt) != required:
        result["errors"].append("Exact action-binding receipt is required")
        return result
    if (receipt["schema"] != "gameassetai.action-binding-receipt.v1"
            or receipt["binding_policy"] != "EMPTY_ONLY"
            or receipt["receipt_sha256"] != _binding_digest(_receipt_payload(receipt))):
        result["errors"].append("Action-binding receipt is invalid")
        return result
    scene = bpy.data.scenes.get(receipt["scene_name"])
    target = scene.objects.get(receipt["armature_name"]) if scene else None
    action = bpy.data.actions.get(receipt["action_name"])
    if target is None or target.type != "ARMATURE" or action is None:
        result["errors"].append("Receipt target or Action no longer exists")
        return result
    data = target.animation_data
    slot = getattr(data, "action_slot", None) if data else None
    if (data is None or data.action != action
            or getattr(slot, "identifier", None) != receipt["action_slot_identifier"]
            or data.nla_tracks or data.drivers
            or _action_references(action) != ([target.name], [])):
        result["errors"].append("Current binding does not exactly match the receipt")
        return result
    if action_content_fingerprint(action) != receipt["action_sha256"]:
        result["errors"].append("Action content changed after binding")
        return result
    data.action = None
    if not receipt["animation_data_existed_before"]:
        if data.action is not None or data.nla_tracks or data.drivers:
            result["errors"].append("Animation data cannot be restored to its absent state")
            return result
        target.animation_data_clear()
    if _action_references(action) != ([], []) or not action.use_fake_user:
        result["errors"].append("Rollback did not preserve the unbound protected Action")
        return result
    result.update({"status": "rolled_back", "action_preserved": True,
                   "animation_data_restored": (_animation_state(target)["exists"]
                                                == receipt["animation_data_existed_before"])})
    return result
