"""Development-only rotation-bake retarget through owned working rig copies."""
from __future__ import annotations

import hashlib
import json
import math
import uuid
import bpy


ROTATION_BAKE_SCHEMA = "gameassetai.rotation-retarget-bake-request.v1"
_ROTATION_BAKE_KEYS = {
    "schema", "scene_name", "source_armature", "target_armature",
    "source_action", "target_action", "source_mapping", "target_mapping",
    "source_slot_identifier", "frame_start", "frame_end", "frame_step",
    "preserve_source", "bind_result", "set_fake_user", "rotation_only",
}
_ROTATION_PROPERTIES = {"rotation_euler", "rotation_quaternion", "rotation_axis_angle"}


def _rotation_bake_digest(value):
    payload = json.dumps(value, ensure_ascii=False, allow_nan=False,
                         sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _rotation_bake_integer(value, label):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return int(value)


def preview_rotation_retarget_bake(request):
    """Plan an unbound rotation-only sampled Action; perform no writes or frame changes."""
    report = {"schema": "gameassetai.rotation-retarget-bake-plan.v1",
              "status": "error", "errors": [], "reviews": [], "authorization": False}
    if not isinstance(request, dict):
        report["errors"].append("Request must be an object")
        return report
    unknown, missing = sorted(set(request) - _ROTATION_BAKE_KEYS), sorted(_ROTATION_BAKE_KEYS - set(request))
    if unknown:
        report["errors"].append("Unknown request fields: " + ", ".join(unknown))
    if missing:
        report["errors"].append("Missing request fields: " + ", ".join(missing))
    if unknown or missing:
        return report
    if request["schema"] != ROTATION_BAKE_SCHEMA:
        report["errors"].append("Unsupported request schema")
    for key in ("scene_name", "source_armature", "target_armature",
                "source_action", "target_action"):
        value = request[key]
        if not isinstance(value, str) or not value or value != value.strip():
            report["errors"].append(f"{key} must be an exact nonempty name without outer whitespace")
    if request["source_action"] == request["target_action"]:
        report["errors"].append("Source and target Action names must differ")
    if isinstance(request["target_action"], str) and len(request["target_action"].encode("utf-8")) > 255:
        report["errors"].append("target_action exceeds Blender's observed 255-byte UTF-8 ID-name limit")
    for key in ("preserve_source", "bind_result", "set_fake_user", "rotation_only"):
        if type(request[key]) is not bool:
            report["errors"].append(f"{key} must be boolean")
    if request["preserve_source"] is not True:
        report["errors"].append("This workflow requires preserve_source=true")
    if request["bind_result"] is not False:
        report["errors"].append("This workflow requires bind_result=false")
    if request["set_fake_user"] is not True:
        report["errors"].append("The unbound result requires set_fake_user=true")
    if request["rotation_only"] is not True:
        report["errors"].append("This bounded workflow requires rotation_only=true")
    try:
        start = _rotation_bake_integer(request["frame_start"], "frame_start")
        end = _rotation_bake_integer(request["frame_end"], "frame_end")
        step = _rotation_bake_integer(request["frame_step"], "frame_step")
    except ValueError as exc:
        report["errors"].append(str(exc))
        return report
    if end < start:
        report["errors"].append("frame_end must be greater than or equal to frame_start")
    if step != 1:
        report["errors"].append("The first bounded rotation bake requires frame_step=1")
    if end - start > 10000:
        report["errors"].append("Requested bake range exceeds 10001 frames")
    if report["errors"]:
        return report
    if bpy.data.actions.get(request["target_action"]) is not None:
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
        report["errors"].append("Only mapped pose-bone rotation channels are supported")
    unsupported = sorted(
        role for role, channels in readiness["role_transform_channels"].items()
        if set(channels) - _ROTATION_PROPERTIES)
    if unsupported:
        report["errors"].append("Location or scale channels are unsupported: " + ", ".join(unsupported))
    scene = bpy.data.scenes[request["scene_name"]]
    source = scene.objects[request["source_armature"]]
    target = scene.objects[request["target_armature"]]
    action = bpy.data.actions[request["source_action"]]
    slots = list(getattr(action, "slots", ()))
    if len(slots) > 1:
        report["errors"].append("Rotation bake currently supports at most one Action slot")
    if len(slots) == 1 and request["source_slot_identifier"] != slots[0].identifier:
        report["errors"].append("Request slot does not match the sole source Action slot")
    if len(slots) == 0 and request["source_slot_identifier"] is not None:
        report["errors"].append("A slot identifier was supplied for a slotless Action")
    if source.parent is not None or target.parent is not None:
        report["errors"].append("Parented Armature Objects are unsupported")
    try:
        source_object = _object_transform_values(source)
        target_object = _object_transform_values(target)
    except ValueError as exc:
        report["errors"].append(str(exc))
        return report
    identity = {"rotation_mode": "QUATERNION", "values": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0]}
    def identity_like(obj, snapshot):
        location = [float(value) for value in obj.location]
        scale = [float(value) for value in obj.scale]
        if obj.rotation_mode == "QUATERNION":
            rotation_ok = max(abs(a-b) for a,b in zip(obj.rotation_quaternion, (1,0,0,0))) <= 1e-6
        elif obj.rotation_mode == "AXIS_ANGLE":
            rotation_ok = abs(float(obj.rotation_axis_angle[0])) <= 1e-6
        else:
            rotation_ok = max(abs(float(value)) for value in obj.rotation_euler) <= 1e-6
        return (max(abs(value) for value in location) <= 1e-6 and
                max(abs(value-1.0) for value in scale) <= 1e-6 and rotation_ok)
    if not identity_like(source, source_object) or not identity_like(target, target_object):
        report["errors"].append("Both Armature Objects must have identity transforms")
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
        report["errors"].append("Mapped pose-bone constraints are unsupported: " + ", ".join(constrained))
    for role in REQUIRED_ROLES:
        source_bone = source.data.bones[request["source_mapping"][role]]
        target_bone = target.data.bones[request["target_mapping"][role]]
        if source_bone.inherit_scale != target_bone.inherit_scale:
            report["errors"].append("Mapped inherit-scale modes differ: " + role)
    if report["errors"]:
        report["readiness"] = readiness
        return report

    frames = list(range(start, end + 1, step))
    candidate = {
        "operation": "rotation_only_local_basis_bake_unbound",
        "scene_name": scene.name,
        "source_armature": source.name,
        "target_armature": target.name,
        "source_action": action.name,
        "target_action": request["target_action"],
        "source_slot_identifier": request["source_slot_identifier"],
        "frames": frames,
        "frame_count": len(frames),
        "mapped_animated_roles": readiness["mapped_animated_roles"],
        "source_content_sha256": action_content_fingerprint(action),
        "source_state_sha256": _aligned_digest(source_state),
        "target_state_sha256": _aligned_digest(target_state),
        "request_sha256": _rotation_bake_digest(request),
        "preserve_source": True,
        "bind_result": False,
        "set_fake_user": True,
        "rotation_only": True,
    }
    report.update({"status": "candidate_for_review", "request": dict(request),
                   "candidate": candidate, "readiness": readiness})
    report["reviews"].append(
        "The bake copies evaluated local matrix_basis rotations; it does not normalize humanoid pose space or preserve world-space limb orientation")
    report["reviews"].append(
        "Every integer frame is keyed as quaternion rotation on an owned temporary target copy; the result remains unbound")
    return report


def _quaternion_equivalent(left, right, tolerance=1e-5):
    return abs(abs(float(left.dot(right))) - 1.0) <= tolerance


def apply_rotation_retarget_bake(plan, authorization=False):
    """Bake local-basis rotations on owned copies and keep only one unbound Action."""
    result = {"schema": "gameassetai.rotation-retarget-bake-result.v1",
              "status": "error", "errors": []}
    if authorization is not True:
        result["errors"].append("Explicit authorization=true is required")
        return result
    if (not isinstance(plan, dict)
            or plan.get("schema") != "gameassetai.rotation-retarget-bake-plan.v1"
            or plan.get("status") != "candidate_for_review"):
        result["errors"].append("A candidate_for_review plan is required")
        return result
    request, candidate = plan.get("request"), plan.get("candidate")
    if not isinstance(request, dict) or not isinstance(candidate, dict):
        result["errors"].append("Plan request/candidate is missing")
        return result
    fresh = preview_rotation_retarget_bake(request)
    if fresh.get("status") != "candidate_for_review" or fresh.get("candidate") != candidate:
        result["errors"].append("Rotation retarget preview is stale")
        return result

    scene = bpy.data.scenes[request["scene_name"]]
    source = scene.objects[request["source_armature"]]
    target = scene.objects[request["target_armature"]]
    source_action = bpy.data.actions[request["source_action"]]
    source_snapshot = action_content_snapshot(source_action)
    source_refs = _action_references(source_action)
    source_state = _aligned_pose_snapshot(source, request["source_mapping"])
    target_state = _aligned_pose_snapshot(target, request["target_mapping"])
    window = bpy.context.window
    if window is None or bpy.context.mode != "OBJECT":
        result["errors"].append("Apply requires an Object-mode Blender window")
        return result
    original_scene, original_layer = window.scene, window.view_layer
    token = uuid.uuid4().hex
    work_scene = source_work = target_work = source_data = target_data = created = None
    expected = {}
    try:
        work_scene = bpy.data.scenes.new("GAI_RotationBake_" + token)
        work_scene["gameassetai_test_owner"] = token
        source_data = source.data.copy(); target_data = target.data.copy()
        source_work = source.copy(); target_work = target.copy()
        for item in (source_data, target_data, source_work, target_work):
            item["gameassetai_test_owner"] = token
        source_work.data = source_data; target_work.data = target_data
        source_work.animation_data_clear(); target_work.animation_data_clear()
        work_scene.collection.objects.link(source_work)
        work_scene.collection.objects.link(target_work)
        source_work.animation_data_create()
        source_work.animation_data.action = source_action
        if len(getattr(source_action, "slots", ())) == 1:
            source_work.animation_data.action_slot = source_action.slots[0]
        window.scene = work_scene
        reverse = {bone: role for role, bone in request["source_mapping"].items()}
        animated_roles = set(candidate["mapped_animated_roles"])
        for frame in candidate["frames"]:
            work_scene.frame_set(frame)
            expected[frame] = {}
            for role in sorted(animated_roles):
                source_pose = source_work.pose.bones[request["source_mapping"][role]]
                target_pose = target_work.pose.bones[request["target_mapping"][role]]
                quaternion = source_pose.matrix_basis.to_quaternion().normalized()
                expected[frame][role] = quaternion.copy()
                target_pose.rotation_mode = "QUATERNION"
                target_pose.location = (0.0, 0.0, 0.0)
                target_pose.scale = (1.0, 1.0, 1.0)
                target_pose.rotation_quaternion = quaternion
                target_pose.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        if target_work.animation_data is None or target_work.animation_data.action is None:
            raise RuntimeError("Blender did not create a baked Action")
        created = target_work.animation_data.action
        created["gameassetai_test_owner"] = token
        created.name = request["target_action"]
        created.use_fake_user = True
        if created.name != request["target_action"]:
            raise RuntimeError("Blender did not preserve the exact target Action name")
        slots = list(getattr(created, "slots", ()))
        if len(slots) == 1:
            slots[0].name_display = target.name
        for curve in _curves(created):
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"
        for frame in candidate["frames"]:
            work_scene.frame_set(frame)
            for role, quaternion in expected[frame].items():
                actual = target_work.pose.bones[request["target_mapping"][role]].matrix_basis.to_quaternion().normalized()
                if not _quaternion_equivalent(actual, quaternion):
                    raise RuntimeError(f"Baked rotation verification failed at frame {frame}, role {role}")
        curve_count = len(_curves(created))
        expected_curve_count = len(animated_roles) * 4
        if curve_count != expected_curve_count:
            raise RuntimeError("Unexpected baked F-Curve count")
        target_work.animation_data.action = None
        if _action_references(created) != ([], []):
            raise RuntimeError("Baked Action was unexpectedly bound")
        source_work.animation_data.action = None
        if action_content_snapshot(source_action) != source_snapshot or _action_references(source_action) != source_refs:
            raise RuntimeError("Source Action or its references changed")
        if (_aligned_pose_snapshot(source, request["source_mapping"]) != source_state or
                _aligned_pose_snapshot(target, request["target_mapping"]) != target_state):
            raise RuntimeError("Source or target Armature changed")
        result.update({
            "status": "created",
            "source_action": source_action.name,
            "target_action": created.name,
            "target_slot_identifier": slots[0].identifier if slots else None,
            "frame_start": candidate["frames"][0],
            "frame_end": candidate["frames"][-1],
            "frame_count": len(candidate["frames"]),
            "mapped_roles": sorted(animated_roles),
            "curve_count": curve_count,
            "target_fake_user": created.use_fake_user,
            "target_unbound": True,
            "source_references_preserved": True,
            "source_target_armatures_preserved": True,
        })
    except Exception as exc:
        result["errors"].append(str(exc))
        if created is not None:
            if target_work is not None and target_work.animation_data and target_work.animation_data.action == created:
                target_work.animation_data.action = None
            if bpy.data.actions.get(created.name) == created:
                bpy.data.actions.remove(created)
            created = None
    finally:
        window.scene, window.view_layer = original_scene, original_layer
        for obj in (source_work, target_work):
            if obj is not None and bpy.data.objects.get(obj.name) == obj:
                bpy.data.objects.remove(obj, do_unlink=True)
        for data in (source_data, target_data):
            if data is not None and data.users == 0:
                bpy.data.armatures.remove(data)
        if work_scene is not None and bpy.data.scenes.get(work_scene.name) == work_scene:
            bpy.data.scenes.remove(work_scene)
    return result


