"""Preview and apply one guarded, unbound copy of an existing Blender Action."""
from __future__ import annotations

import hashlib
import json
import math
import bpy


def _finite(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Action contains a non-finite numeric value")
    return value


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


def _first_difference(left, right, path="content"):
    if type(left) is not type(right):
        return f"{path} type"
    if isinstance(left, dict):
        if left.keys() != right.keys(): return f"{path} keys"
        for key in left:
            found = _first_difference(left[key], right[key], f"{path}.{key}")
            if found: return found
        return None
    if isinstance(left, list):
        if len(left) != len(right): return f"{path} length"
        for index, (a, b) in enumerate(zip(left, right)):
            found = _first_difference(a, b, f"{path}[{index}]")
            if found: return found
        return None
    return None if left == right else path


def preview_action_copy(request):
    """Create a read-only plan plus a detailed source-content fingerprint."""
    if not isinstance(request, dict):
        return {"schema": "gameassetai.action-copy-plan.v1", "status": "error",
                "errors": ["Request must be an object"], "reviews": [],
                "authorization": False}
    scene_name = request.get("scene_name")
    inventory = inspect_animation(scene_name)
    plan = plan_action_copy(inventory, request)
    if plan["status"] != "candidate_for_review":
        return plan
    source = bpy.data.actions.get(request["source_action"])
    try:
        plan["candidate"]["source_content_sha256"] = action_content_fingerprint(source)
    except (TypeError, ValueError, OverflowError) as exc:
        plan["status"] = "error"
        plan["errors"].append(str(exc))
        plan.pop("candidate", None)
    return plan


def _action_references(action):
    current, nla = [], []
    owners = []
    for obj in bpy.data.objects:
        owners.append(obj)
        if obj.data is not None: owners.append(obj.data)
        if obj.type == "MESH" and obj.data.shape_keys is not None:
            owners.append(obj.data.shape_keys)
    seen = set()
    for owner in owners:
        pointer = owner.as_pointer()
        if pointer in seen: continue
        seen.add(pointer)
        data = getattr(owner, "animation_data", None)
        if data is None: continue
        if data.action == action: current.append(owner.name)
        for track in data.nla_tracks:
            for strip in track.strips:
                if strip.action == action:
                    nla.append((owner.name, track.name, strip.name))
    return sorted(current), sorted(nla)


def apply_action_copy(plan, authorization=False):
    """Apply a fresh preview once; never bind or replace an Action."""
    result = {"schema": "gameassetai.action-copy-result.v1", "status": "error",
              "errors": []}
    if authorization is not True:
        result["errors"].append("Explicit authorization=true is required")
        return result
    if (not isinstance(plan, dict) or plan.get("schema") != "gameassetai.action-copy-plan.v1"
            or plan.get("status") != "candidate_for_review"):
        result["errors"].append("A candidate_for_review plan is required")
        return result
    request = plan.get("request")
    candidate = plan.get("candidate", {})
    if not isinstance(request, dict) or not isinstance(candidate, dict):
        result["errors"].append("Plan request/candidate is missing")
        return result
    fresh = preview_action_copy(request)
    if fresh.get("status") != "candidate_for_review" or fresh.get("candidate") != candidate:
        result["errors"].append("Action copy preview is stale")
        return result
    source = bpy.data.actions.get(request["source_action"])
    target_name = request["target_action"]
    if source is None or bpy.data.actions.get(target_name) is not None:
        result["errors"].append("Source is missing or target now exists")
        return result
    source_pointer = source.as_pointer()
    source_snapshot = action_content_snapshot(source)
    source_refs = _action_references(source)
    created = None
    try:
        created = source.copy()
        created.name = target_name
        created.use_fake_user = True
        if created.name != target_name or created.as_pointer() == source_pointer:
            raise RuntimeError("Blender did not create the exact independent target Action")
        copied_snapshot = action_content_snapshot(created)
        if copied_snapshot != source_snapshot:
            raise RuntimeError("Copied Action content differs from the source at " +
                               _first_difference(source_snapshot, copied_snapshot))
        if _action_references(created) != ([], []):
            raise RuntimeError("Copied Action was unexpectedly bound")
        if _action_references(source) != source_refs or action_content_snapshot(source) != source_snapshot:
            raise RuntimeError("Source Action or its references changed")
        result.update({"status": "created", "source_action": source.name,
                       "target_action": created.name, "target_fake_user": created.use_fake_user,
                       "target_content_sha256": action_content_fingerprint(created),
                       "source_references_preserved": True, "target_unbound": True})
        return result
    except Exception as exc:
        if created is not None and created.as_pointer() != source_pointer:
            bpy.data.actions.remove(created)
        result["errors"].append(str(exc))
        return result
