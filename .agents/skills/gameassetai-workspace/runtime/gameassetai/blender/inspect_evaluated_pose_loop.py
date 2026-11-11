"""Compare explicit pose-bone endpoint transforms on an isolated Armature copy."""
from __future__ import annotations

import math
import re
import uuid

import bpy


EVALUATED_POSE_LOOP_SCHEMA = "gameassetai.evaluated-pose-loop-request.v2"
_EVALUATED_POSE_LOOP_KEYS = {
    "schema", "scene_name", "armature_name", "action_name", "bone_names",
    "slot_identifier", "frame_start", "frame_end", "translation_tolerance",
    "rotation_tolerance_radians", "scale_tolerance", "velocity_sample_frames",
    "translation_velocity_tolerance", "angular_velocity_tolerance_radians_per_frame",
    "scale_velocity_tolerance_per_frame",
}
_POSE_PROPERTIES = {
    "location", "rotation_euler", "rotation_quaternion", "rotation_axis_angle", "scale",
}
_POSE_PATH = re.compile(
    r'^pose\.bones\["((?:[^"\\]|\\.)*)"\]\.([A-Za-z_][A-Za-z0-9_]*)$')


def _pose_loop_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return result


def _pose_loop_frame(value, label):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return int(value)


def _pose_property(data_path):
    match = _POSE_PATH.match(data_path)
    if match is None:
        return None, None
    bone = match.group(1).replace('\\"', '"').replace('\\\\', '\\')
    return bone, match.group(2)


def _pose_endpoint(pose_bone):
    location, rotation, scale = pose_bone.matrix_basis.decompose()
    rotation.normalize()
    values = (*location, *rotation, *scale)
    if any(not math.isfinite(float(value)) for value in values):
        raise RuntimeError(f"Non-finite evaluated pose for bone {pose_bone.name}")
    return location.copy(), rotation.copy(), scale.copy()


def _pose_endpoint_metrics(start, end):
    start_location, start_rotation, start_scale = start
    end_location, end_rotation, end_scale = end
    dot = min(1.0, max(0.0, abs(float(start_rotation.dot(end_rotation)))))
    return {
        "start": {
            "translation": [float(v) for v in start_location],
            "rotation_quaternion": [float(v) for v in start_rotation],
            "scale": [float(v) for v in start_scale],
        },
        "end": {
            "translation": [float(v) for v in end_location],
            "rotation_quaternion": [float(v) for v in end_rotation],
            "scale": [float(v) for v in end_scale],
        },
        "translation_distance": float((end_location - start_location).length),
        "rotation_angle_radians": float(2.0 * math.acos(dot)),
        "scale_max_component_delta": float(max(abs(end_scale[i] - start_scale[i])
                                                for i in range(3))),
    }


def _rotation_velocity(first, second, frame_delta):
    delta = first.rotation_difference(second)
    delta.normalize()
    if delta.w < 0.0:
        delta.negate()
    w = min(1.0, max(-1.0, float(delta.w)))
    angle = 2.0 * math.acos(w)
    sine = math.sqrt(max(0.0, 1.0 - w * w))
    if sine <= 1e-12 or angle <= 1e-12:
        return [0.0, 0.0, 0.0]
    return [float(delta[index + 1] / sine * angle / frame_delta) for index in range(3)]


def _pose_velocity(first, second, frame_delta):
    first_location, first_rotation, first_scale = first
    second_location, second_rotation, second_scale = second
    return {
        "translation_per_frame": [float((second_location[i] - first_location[i]) / frame_delta)
                                  for i in range(3)],
        "rotation_vector_radians_per_frame": _rotation_velocity(
            first_rotation, second_rotation, frame_delta),
        "scale_per_frame": [float((second_scale[i] - first_scale[i]) / frame_delta)
                            for i in range(3)],
    }


def _vector_distance(first, second):
    return float(math.sqrt(sum((first[index] - second[index]) ** 2 for index in range(3))))


def inspect_evaluated_pose_loop(request):
    """Evaluate exact endpoint frames and compare local-basis pose transforms."""
    report = {"schema": "gameassetai.evaluated-pose-loop-report.v1",
              "status": "error", "errors": [], "reviews": []}
    if not isinstance(request, dict):
        report["errors"].append("Request must be an object")
        return report
    unknown = sorted(set(request) - _EVALUATED_POSE_LOOP_KEYS)
    missing = sorted(_EVALUATED_POSE_LOOP_KEYS - set(request))
    if unknown:
        report["errors"].append("Unknown request fields: " + ", ".join(unknown))
    if missing:
        report["errors"].append("Missing request fields: " + ", ".join(missing))
    if unknown or missing:
        return report
    if request["schema"] != EVALUATED_POSE_LOOP_SCHEMA:
        report["errors"].append("Unsupported request schema")
    for key in ("scene_name", "armature_name", "action_name"):
        value = request[key]
        if not isinstance(value, str) or not value or value != value.strip():
            report["errors"].append(f"{key} must be an exact nonempty name without outer whitespace")
    names = request["bone_names"]
    if (not isinstance(names, list) or not names or
            any(not isinstance(name, str) or not name or name != name.strip() for name in names) or
            len(set(names)) != len(names)):
        report["errors"].append("bone_names must be a nonempty unique list of exact names")
        names = []
    slot_identifier = request["slot_identifier"]
    if slot_identifier is not None and (not isinstance(slot_identifier, str) or not slot_identifier):
        report["errors"].append("slot_identifier must be null or a nonempty exact identifier")
    try:
        start = _pose_loop_frame(request["frame_start"], "frame_start")
        end = _pose_loop_frame(request["frame_end"], "frame_end")
        translation_tolerance = _pose_loop_number(
            request["translation_tolerance"], "translation_tolerance")
        rotation_tolerance = _pose_loop_number(
            request["rotation_tolerance_radians"], "rotation_tolerance_radians")
        scale_tolerance = _pose_loop_number(request["scale_tolerance"], "scale_tolerance")
        velocity_sample_frames = _pose_loop_frame(
            request["velocity_sample_frames"], "velocity_sample_frames")
        translation_velocity_tolerance = _pose_loop_number(
            request["translation_velocity_tolerance"], "translation_velocity_tolerance")
        angular_velocity_tolerance = _pose_loop_number(
            request["angular_velocity_tolerance_radians_per_frame"],
            "angular_velocity_tolerance_radians_per_frame")
        scale_velocity_tolerance = _pose_loop_number(
            request["scale_velocity_tolerance_per_frame"],
            "scale_velocity_tolerance_per_frame")
    except ValueError as exc:
        report["errors"].append(str(exc))
        return report
    if end <= start:
        report["errors"].append("frame_end must be greater than frame_start")
    if end - start > 10000:
        report["errors"].append("Requested endpoint range exceeds 10000 frames")
    if velocity_sample_frames < 1:
        report["errors"].append("velocity_sample_frames must be at least 1")
    elif 2 * velocity_sample_frames > end - start:
        report["errors"].append(
            "velocity_sample_frames must fit both endpoint intervals without crossing")
    if report["errors"]:
        return report

    scene = bpy.data.scenes.get(request["scene_name"])
    obj = scene.objects.get(request["armature_name"]) if scene else None
    action = bpy.data.actions.get(request["action_name"])
    if scene is None:
        report["errors"].append("Named Scene not found")
    if obj is None:
        report["errors"].append("Named Armature Object not found in Scene")
    elif obj.type != "ARMATURE":
        report["errors"].append("Named Object is not an Armature")
    if action is None:
        report["errors"].append("Named Action not found")
    if report["errors"]:
        return report
    missing_bones = [name for name in names if obj.data.bones.get(name) is None]
    if missing_bones:
        report["errors"].append("Named bones not found: " + ", ".join(missing_bones))
    if obj.parent is not None:
        report["errors"].append("Parented Armature Objects are not supported")
    if obj.constraints or any(pose.constraints for pose in obj.pose.bones):
        report["errors"].append("Object and pose-bone constraints are not supported")
    if ((obj.animation_data and obj.animation_data.drivers)
            or (obj.data.animation_data and obj.data.animation_data.drivers)):
        report["errors"].append("Object and Armature-data drivers are not supported")

    slots = list(getattr(action, "slots", ()))
    identifiers = [slot.identifier for slot in slots]
    if slot_identifier is None and len(slots) > 1:
        report["errors"].append("slot_identifier is required for a multi-slot Action")
    if slot_identifier is not None and slot_identifier not in identifiers:
        report["errors"].append("Named Action slot not found")
    effective_slot = slot_identifier if slot_identifier is not None else (
        identifiers[0] if identifiers else None)
    applicable = [(curve, slot) for curve, slot in _curves_with_slots(action)
                  if effective_slot is None or slot in {None, effective_slot}]
    animated_bones = set()
    unsupported = []
    for curve, _ in applicable:
        bone_name, prop = _pose_property(curve.data_path)
        if bone_name is None or prop not in _POSE_PROPERTIES:
            unsupported.append(curve.data_path)
        else:
            animated_bones.add(bone_name)
    if unsupported:
        report["errors"].append("Only pose transform F-Curves are supported: " +
                                ", ".join(sorted(set(unsupported))))
    outside = sorted(animated_bones - set(names))
    if outside:
        report["errors"].append("Animated bones omitted from bone_names: " + ", ".join(outside))
    if not animated_bones:
        report["errors"].append("No pose transform F-Curves match the selected Action slot")
    if report["errors"]:
        return report

    window = bpy.context.window
    if window is None or bpy.context.mode != "OBJECT":
        report["errors"].append("Evaluation requires an Object-mode Blender window")
        return report
    original_scene, original_layer = window.scene, window.view_layer
    original_frame, original_subframe = original_scene.frame_current, original_scene.frame_subframe
    source_snapshot = _evaluated_root_source_snapshot(obj)
    action_snapshot = action_content_snapshot(action)
    action_refs = _action_references(action)
    token = uuid.uuid4().hex
    work_scene = work_obj = work_data = None
    endpoints = {}
    try:
        work_scene = bpy.data.scenes.new("GAI_EvaluatedPoseLoop_" + token)
        work_scene["gameassetai_test_owner"] = token
        work_data = obj.data.copy()
        work_obj = obj.copy()
        for item in (work_data, work_obj):
            item["gameassetai_test_owner"] = token
        work_obj.data = work_data
        work_obj.animation_data_clear()
        work_scene.collection.objects.link(work_obj)
        work_obj.animation_data_create()
        work_obj.animation_data.action = action
        if effective_slot is not None:
            work_obj.animation_data.action_slot = next(
                slot for slot in slots if slot.identifier == effective_slot)
        window.scene = work_scene
        samples = {}
        sample_frames = {
            "start": start, "start_inner": start + velocity_sample_frames,
            "end_inner": end - velocity_sample_frames, "end": end,
        }
        for label, frame in sample_frames.items():
            work_scene.frame_set(frame)
            depsgraph = bpy.context.evaluated_depsgraph_get()
            evaluated = work_obj.evaluated_get(depsgraph)
            samples[label] = {name: _pose_endpoint(evaluated.pose.bones[name]) for name in names}
        for name in names:
            metrics = _pose_endpoint_metrics(samples["start"][name], samples["end"][name])
            metrics["animated"] = name in animated_bones
            metrics["translation_matches"] = metrics["translation_distance"] <= translation_tolerance
            metrics["rotation_matches"] = metrics["rotation_angle_radians"] <= rotation_tolerance
            metrics["scale_matches"] = metrics["scale_max_component_delta"] <= scale_tolerance
            metrics["endpoint_matches"] = (metrics["translation_matches"] and
                                            metrics["rotation_matches"] and
                                            metrics["scale_matches"])
            start_velocity = _pose_velocity(samples["start"][name],
                                            samples["start_inner"][name],
                                            velocity_sample_frames)
            end_velocity = _pose_velocity(samples["end_inner"][name],
                                          samples["end"][name],
                                          velocity_sample_frames)
            translation_velocity_delta = _vector_distance(
                start_velocity["translation_per_frame"],
                end_velocity["translation_per_frame"])
            angular_velocity_delta = _vector_distance(
                start_velocity["rotation_vector_radians_per_frame"],
                end_velocity["rotation_vector_radians_per_frame"])
            scale_velocity_delta = max(
                abs(start_velocity["scale_per_frame"][index] -
                    end_velocity["scale_per_frame"][index]) for index in range(3))
            metrics["velocity"] = {
                "sample_frames": velocity_sample_frames,
                "start": start_velocity, "end": end_velocity,
                "translation_delta": translation_velocity_delta,
                "angular_delta_radians_per_frame": angular_velocity_delta,
                "scale_max_component_delta_per_frame": float(scale_velocity_delta),
                "translation_matches": (
                    translation_velocity_delta <= translation_velocity_tolerance),
                "rotation_matches": angular_velocity_delta <= angular_velocity_tolerance,
                "scale_matches": scale_velocity_delta <= scale_velocity_tolerance,
            }
            metrics["velocity"]["tangent_matches"] = all(
                metrics["velocity"][key] for key in
                ("translation_matches", "rotation_matches", "scale_matches"))
            endpoints[name] = metrics
        report.update({
            "status": "ok", "blender_version": bpy.app.version_string,
            "scene": scene.name, "armature": obj.name, "action": action.name,
            "slot_identifier": effective_slot, "frame_start": start, "frame_end": end,
            "tolerances": {"translation": translation_tolerance,
                           "rotation_radians": rotation_tolerance, "scale": scale_tolerance,
                           "translation_velocity": translation_velocity_tolerance,
                           "angular_velocity_radians_per_frame": angular_velocity_tolerance,
                           "scale_velocity_per_frame": scale_velocity_tolerance},
            "bones": endpoints,
            "all_endpoints_match": all(item["endpoint_matches"] for item in endpoints.values()),
            "all_tangents_match": all(item["velocity"]["tangent_matches"]
                                      for item in endpoints.values()),
        })
        report["reviews"].append(
            "Finite endpoint differences approximate seam velocity; they do not certify subframe extrema, deformation or visual loop continuity")
        report["reviews"].append(
            "Constraints, drivers, Object channels and NLA blending are intentionally excluded")
    except Exception as exc:
        report["status"] = "error"
        report["errors"].append(str(exc))
    finally:
        window.scene, window.view_layer = original_scene, original_layer
        original_scene.frame_set(original_frame, subframe=original_subframe)
        if work_obj is not None and bpy.data.objects.get(work_obj.name) == work_obj:
            work_obj.animation_data_clear()
            bpy.data.objects.remove(work_obj, do_unlink=True)
        if work_data is not None and work_data.users == 0:
            bpy.data.armatures.remove(work_data)
        if work_scene is not None and bpy.data.scenes.get(work_scene.name) == work_scene:
            bpy.data.scenes.remove(work_scene)
    preservation_mismatches = []
    if _evaluated_root_source_snapshot(obj) != source_snapshot:
        preservation_mismatches.append("Armature state")
    if action_content_snapshot(action) != action_snapshot:
        preservation_mismatches.append("Action content")
    if _action_references(action) != action_refs:
        preservation_mismatches.append("Action references")
    if preservation_mismatches:
        report["status"] = "error"
        report["errors"].append("Source changed during evaluation: " +
                                ", ".join(preservation_mismatches))
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
