"""Guarded Action path remap for explicitly aligned humanoid rigs."""
from __future__ import annotations

import hashlib
import json
import math
import bpy


ALIGNED_RETARGET_SCHEMA = "gameassetai.aligned-retarget-request.v1"
_ALIGNED_KEYS = {
    "schema", "scene_name", "source_armature", "target_armature",
    "source_action", "target_action", "source_mapping", "target_mapping",
    "source_slot_identifier", "rest_tolerance", "preserve_source",
    "bind_result", "set_fake_user",
}


def _aligned_digest(value):
    payload = json.dumps(value, ensure_ascii=False, allow_nan=False,
                         sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _aligned_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite nonnegative number")
    value = float(value)
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{label} must be a finite nonnegative number")
    return value


def _matrix_max_delta(left, right):
    values = [abs(float(left[row][column]) - float(right[row][column]))
              for row in range(4) for column in range(4)]
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Matrix comparison produced a non-finite value")
    return max(values, default=0.0)


def _object_transform_values(obj):
    if obj.rotation_mode == "QUATERNION":
        rotation = [float(value) for value in obj.rotation_quaternion]
    elif obj.rotation_mode == "AXIS_ANGLE":
        rotation = [float(value) for value in obj.rotation_axis_angle]
    else:
        rotation = [float(value) for value in obj.rotation_euler]
    values = ([float(value) for value in obj.location] + rotation +
              [float(value) for value in obj.scale])
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Object transform contains a non-finite value")
    return {"rotation_mode": obj.rotation_mode, "values": values}


def _object_transform_delta(left, right):
    left_values, right_values = _object_transform_values(left), _object_transform_values(right)
    if left_values["rotation_mode"] != right_values["rotation_mode"]:
        return math.inf
    return max((abs(a - b) for a, b in zip(left_values["values"],
                                            right_values["values"])), default=0.0)


def _aligned_pose_snapshot(obj, mapping):
    return {
        "parent": obj.parent.name if obj.parent else None,
        "object_transform": _object_transform_values(obj),
        "bones": {
            role: {
                "name": mapping[role],
                "matrix_local": [[float(value) for value in row]
                                 for row in obj.data.bones[mapping[role]].matrix_local],
                "rotation_mode": obj.pose.bones[mapping[role]].rotation_mode,
                "constraints": [(item.name, item.type) for item in obj.pose.bones[mapping[role]].constraints],
            }
            for role in sorted(mapping)
        },
        "object_constraints": [(item.name, item.type) for item in obj.constraints],
        "drivers": [(curve.data_path, curve.array_index)
                    for curve in (obj.animation_data.drivers if obj.animation_data else ())],
    }


def _mapped_curve_path(target, bone_name, property_name):
    return target.pose.bones[bone_name].path_from_id() + "." + property_name


def preview_aligned_retarget(request):
    """Build a freshness-bound plan for name-only Action remap; perform no writes."""
    report = {"schema": "gameassetai.aligned-retarget-plan.v1", "status": "error",
              "errors": [], "reviews": [], "authorization": False}
    if not isinstance(request, dict):
        report["errors"].append("Request must be an object")
        return report
    unknown, missing = sorted(set(request) - _ALIGNED_KEYS), sorted(_ALIGNED_KEYS - set(request))
    if unknown:
        report["errors"].append("Unknown request fields: " + ", ".join(unknown))
    if missing:
        report["errors"].append("Missing request fields: " + ", ".join(missing))
    if unknown or missing:
        return report
    if request["schema"] != ALIGNED_RETARGET_SCHEMA:
        report["errors"].append("Unsupported request schema")
        return report
    for key in ("scene_name", "source_armature", "target_armature",
                "source_action", "target_action"):
        value = request[key]
        if not isinstance(value, str) or not value or value != value.strip():
            report["errors"].append(f"{key} must be an exact nonempty name without outer whitespace")
    target_name = request["target_action"]
    if isinstance(target_name, str) and len(target_name.encode("utf-8")) > 255:
        report["errors"].append("target_action exceeds Blender's observed 255-byte UTF-8 ID-name limit")
    if request["source_action"] == target_name:
        report["errors"].append("Source and target Action names must differ")
    for key in ("preserve_source", "bind_result", "set_fake_user"):
        if type(request[key]) is not bool:
            report["errors"].append(f"{key} must be boolean")
    if request["preserve_source"] is not True:
        report["errors"].append("This workflow requires preserve_source=true")
    if request["bind_result"] is not False:
        report["errors"].append("This bounded workflow requires bind_result=false")
    if request["set_fake_user"] is not True:
        report["errors"].append("The unbound result requires set_fake_user=true")
    try:
        tolerance = _aligned_number(request["rest_tolerance"], "rest_tolerance")
    except ValueError as exc:
        report["errors"].append(str(exc))
        return report
    if report["errors"]:
        return report
    if bpy.data.actions.get(target_name) is not None:
        report["errors"].append("Target Action name already exists")
        return report

    readiness = inspect_retarget_readiness(
        request["scene_name"], request["source_armature"], request["target_armature"],
        request["source_mapping"], request["target_mapping"], request["source_action"],
        REQUIRED_ROLES, request["source_slot_identifier"])
    if readiness.get("status") != "ok" or not readiness.get("retarget_candidate"):
        report["errors"].append("A complete retarget-readiness candidate is required")
        report["readiness"] = readiness
        return report
    if readiness["unmapped_animated_bones"]:
        report["errors"].append("Every animated pose bone must be explicitly mapped")
    if readiness["non_bone_channels"]:
        report["errors"].append("Only mapped pose-bone transform channels are supported")
    scene = bpy.data.scenes[request["scene_name"]]
    source = scene.objects[request["source_armature"]]
    target = scene.objects[request["target_armature"]]
    action = bpy.data.actions[request["source_action"]]
    slots = list(getattr(action, "slots", ()))
    if len(slots) > 1:
        report["errors"].append("Aligned remap currently supports at most one Action slot")
    if len(slots) == 1 and slots[0].target_id_type not in {"OBJECT", "UNSPECIFIED"}:
        report["errors"].append("Source Action slot must target an Object")
    if len(slots) == 1 and request["source_slot_identifier"] != slots[0].identifier:
        report["errors"].append("Request slot does not match the sole source Action slot")
    if len(slots) == 0 and request["source_slot_identifier"] is not None:
        report["errors"].append("A slot identifier was supplied for a slotless Action")

    try:
        object_delta = _object_transform_delta(source, target)
        role_deltas = {}
        for role in REQUIRED_ROLES:
            source_bone = source.data.bones[request["source_mapping"][role]]
            target_bone = target.data.bones[request["target_mapping"][role]]
            role_deltas[role] = _matrix_max_delta(source_bone.matrix_local,
                                                   target_bone.matrix_local)
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        report["errors"].append("Could not compare aligned rest transforms: " + str(exc))
        return report
    if source.parent is not None or target.parent is not None:
        report["errors"].append("Parented Armature Objects are unsupported")
    if object_delta > tolerance:
        report["errors"].append("Source and target Object transforms are not aligned")
    misaligned = sorted(role for role, delta in role_deltas.items() if delta > tolerance)
    if misaligned:
        report["errors"].append("Mapped rest matrices are not aligned: " + ", ".join(misaligned))

    source_state = _aligned_pose_snapshot(source, request["source_mapping"])
    target_state = _aligned_pose_snapshot(target, request["target_mapping"])
    if source_state["object_constraints"] or target_state["object_constraints"]:
        report["errors"].append("Armature Object constraints are unsupported")
    if source_state["drivers"] or target_state["drivers"]:
        report["errors"].append("Armature Object drivers are unsupported")
    constrained = sorted(
        role for role in REQUIRED_ROLES
        if source_state["bones"][role]["constraints"] or target_state["bones"][role]["constraints"])
    if constrained:
        report["errors"].append("Mapped pose-bone constraints are unsupported: " +
                                ", ".join(constrained))
    rotations = {"rotation_euler", "rotation_quaternion", "rotation_axis_angle"}
    mismatched_modes = sorted(
        role for role, channels in readiness["role_transform_channels"].items()
        if rotations.intersection(channels)
        and source_state["bones"][role]["rotation_mode"] !=
            target_state["bones"][role]["rotation_mode"])
    if mismatched_modes:
        report["errors"].append("Animated rotation modes differ: " + ", ".join(mismatched_modes))
    if report["errors"]:
        report["readiness"] = readiness
        return report

    candidate = {
        "operation": "copy_aligned_action_paths_unbound",
        "scene_name": scene.name,
        "source_armature": source.name,
        "target_armature": target.name,
        "source_action": action.name,
        "target_action": target_name,
        "source_slot_identifier": request["source_slot_identifier"],
        "rest_tolerance": tolerance,
        "object_transform_max_delta": object_delta,
        "role_rest_matrix_max_delta": role_deltas,
        "mapped_animated_roles": readiness["mapped_animated_roles"],
        "source_content_sha256": action_content_fingerprint(action),
        "source_state_sha256": _aligned_digest(source_state),
        "target_state_sha256": _aligned_digest(target_state),
        "request_sha256": _aligned_digest(request),
        "preserve_source": True,
        "bind_result": False,
        "set_fake_user": True,
    }
    report.update({"status": "candidate_for_review", "request": dict(request),
                   "candidate": candidate, "readiness": readiness})
    report["reviews"].append(
        "This copies stored curve values and remaps only bone data paths; it performs no pose-space conversion or bake")
    report["reviews"].append(
        "The result remains unbound with a fake user; source and target rig bindings stay unchanged")
    return report


def _curve_value_payload(curve):
    snapshot = _curve_snapshot(curve)
    snapshot.pop("data_path", None)
    snapshot.pop("group", None)
    return snapshot


def apply_aligned_retarget(plan, authorization=False):
    """Create one unbound Action only when a fresh strict-alignment plan still matches."""
    result = {"schema": "gameassetai.aligned-retarget-result.v1",
              "status": "error", "errors": []}
    if authorization is not True:
        result["errors"].append("Explicit authorization=true is required")
        return result
    if (not isinstance(plan, dict)
            or plan.get("schema") != "gameassetai.aligned-retarget-plan.v1"
            or plan.get("status") != "candidate_for_review"):
        result["errors"].append("A candidate_for_review plan is required")
        return result
    request, candidate = plan.get("request"), plan.get("candidate")
    if not isinstance(request, dict) or not isinstance(candidate, dict):
        result["errors"].append("Plan request/candidate is missing")
        return result
    fresh = preview_aligned_retarget(request)
    if fresh.get("status") != "candidate_for_review" or fresh.get("candidate") != candidate:
        result["errors"].append("Aligned retarget preview is stale")
        return result

    scene = bpy.data.scenes[request["scene_name"]]
    source_obj = scene.objects[request["source_armature"]]
    target_obj = scene.objects[request["target_armature"]]
    source = bpy.data.actions[request["source_action"]]
    target_name = request["target_action"]
    source_snapshot = action_content_snapshot(source)
    source_refs = _action_references(source)
    target_state = _aligned_pose_snapshot(target_obj, request["target_mapping"])
    reverse = {bone: role for role, bone in request["source_mapping"].items()}
    expected = {}
    for curve, unused_slot in _curves_with_slots(source):
        bone_name, property_name = _retarget_bone_channel(curve.data_path)
        role = reverse[bone_name]
        path = _mapped_curve_path(target_obj, request["target_mapping"][role], property_name)
        key = (path, curve.array_index)
        if key in expected:
            result["errors"].append("Mapped source channels collide on the target")
            return result
        expected[key] = _curve_value_payload(curve)

    created = None
    try:
        created = source.copy()
        created.name = target_name
        created.use_fake_user = True
        if created.name != target_name or created == source:
            raise RuntimeError("Blender did not create the exact independent target Action")
        slots = list(getattr(created, "slots", ()))
        if len(slots) == 1:
            slots[0].name_display = target_obj.name
            if slots[0].target_id_type != "OBJECT":
                raise RuntimeError("Copied Action slot is not Object-compatible")
        for group in getattr(created, "groups", ()):
            role = reverse.get(group.name)
            if role is not None:
                group.name = request["target_mapping"][role]
        actual = {}
        for curve, unused_slot in _curves_with_slots(created):
            parsed = _retarget_bone_channel(curve.data_path)
            if parsed is None or parsed[0] not in reverse:
                raise RuntimeError("Copied Action contains an unsupported channel")
            source_bone, property_name = parsed
            role = reverse[source_bone]
            curve.data_path = _mapped_curve_path(
                target_obj, request["target_mapping"][role], property_name)
            key = (curve.data_path, curve.array_index)
            if key in actual:
                raise RuntimeError("Mapped output channels collide")
            actual[key] = _curve_value_payload(curve)
        if actual != expected:
            raise RuntimeError("Remapped Action values/settings differ from the source")
        if _action_references(created) != ([], []):
            raise RuntimeError("Remapped Action was unexpectedly bound")
        if action_content_snapshot(source) != source_snapshot or _action_references(source) != source_refs:
            raise RuntimeError("Source Action or its references changed")
        if _aligned_pose_snapshot(target_obj, request["target_mapping"]) != target_state:
            raise RuntimeError("Target Armature changed")
        result.update({
            "status": "created",
            "source_action": source.name,
            "target_action": created.name,
            "target_slot_identifier": slots[0].identifier if slots else None,
            "remapped_curve_count": len(actual),
            "mapped_roles": candidate["mapped_animated_roles"],
            "target_fake_user": created.use_fake_user,
            "target_unbound": True,
            "source_references_preserved": True,
            "target_armature_preserved": True,
        })
        return result
    except Exception as exc:
        if created is not None and bpy.data.actions.get(created.name) == created:
            bpy.data.actions.remove(created)
        result["errors"].append(str(exc))
        return result


