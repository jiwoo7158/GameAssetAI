"""Evaluate one explicit root bone Action on an owned temporary Armature copy."""
from __future__ import annotations

import math
import uuid

import bpy


EVALUATED_ROOT_MOTION_SCHEMA = "gameassetai.evaluated-root-motion-request.v1"
_EVALUATED_ROOT_KEYS = {
    "schema", "scene_name", "armature_name", "action_name", "bone_name",
    "slot_identifier", "frame_start", "frame_end", "frame_step", "tolerance",
}
_OBJECT_TRANSFORM_PATHS = {
    "location", "rotation_euler", "rotation_quaternion", "rotation_axis_angle",
    "scale", "delta_location", "delta_rotation_euler", "delta_rotation_quaternion",
    "delta_scale",
}


def _evaluated_root_integer(value, label):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return int(value)


def _evaluated_root_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    return value


def _evaluated_root_source_snapshot(obj):
    data = obj.animation_data
    return {
        "location": tuple(float(v) for v in obj.location),
        "rotation_mode": obj.rotation_mode,
        "rotation_euler": tuple(float(v) for v in obj.rotation_euler),
        "rotation_quaternion": tuple(float(v) for v in obj.rotation_quaternion),
        "rotation_axis_angle": tuple(float(v) for v in obj.rotation_axis_angle),
        "scale": tuple(float(v) for v in obj.scale),
        "delta_location": tuple(float(v) for v in obj.delta_location),
        "delta_rotation_euler": tuple(float(v) for v in obj.delta_rotation_euler),
        "delta_scale": tuple(float(v) for v in obj.delta_scale),
        "parent": obj.parent.name if obj.parent else None,
        "action": data.action.name if data and data.action else None,
        "slot": getattr(getattr(data, "action_slot", None), "identifier", None),
        "pose": {
            bone.name: {
                "location": tuple(float(v) for v in bone.location),
                "rotation_mode": bone.rotation_mode,
                "rotation_euler": tuple(float(v) for v in bone.rotation_euler),
                "rotation_quaternion": tuple(float(v) for v in bone.rotation_quaternion),
                "rotation_axis_angle": tuple(float(v) for v in bone.rotation_axis_angle),
                "scale": tuple(float(v) for v in bone.scale),
            }
            for bone in obj.pose.bones
        },
    }


def _evaluated_root_metrics(points):
    start = points[0]
    end = points[-1]
    delta = end - start
    path_length = sum((points[index] - points[index - 1]).length
                      for index in range(1, len(points)))
    return {
        "start": [float(v) for v in start],
        "end": [float(v) for v in end],
        "net_translation": [float(v) for v in delta],
        "net_distance": float(delta.length),
        "path_length": float(path_length),
        "max_distance_from_start": float(max((point - start).length for point in points)),
        "bounds_min": [float(min(point[index] for point in points)) for index in range(3)],
        "bounds_max": [float(max(point[index] for point in points)) for index in range(3)],
    }


def inspect_evaluated_root_motion(request):
    """Sample an Action on an isolated rig copy and report root positions in three spaces."""
    report = {"schema": "gameassetai.evaluated-root-motion-report.v1",
              "status": "error", "errors": [], "reviews": []}
    if not isinstance(request, dict):
        report["errors"].append("Request must be an object")
        return report
    unknown = sorted(set(request) - _EVALUATED_ROOT_KEYS)
    missing = sorted(_EVALUATED_ROOT_KEYS - set(request))
    if unknown:
        report["errors"].append("Unknown request fields: " + ", ".join(unknown))
    if missing:
        report["errors"].append("Missing request fields: " + ", ".join(missing))
    if unknown or missing:
        return report
    if request["schema"] != EVALUATED_ROOT_MOTION_SCHEMA:
        report["errors"].append("Unsupported request schema")
    for key in ("scene_name", "armature_name", "action_name", "bone_name"):
        value = request[key]
        if not isinstance(value, str) or not value or value != value.strip():
            report["errors"].append(f"{key} must be an exact nonempty name without outer whitespace")
    slot_identifier = request["slot_identifier"]
    if slot_identifier is not None and (not isinstance(slot_identifier, str) or not slot_identifier):
        report["errors"].append("slot_identifier must be null or a nonempty exact identifier")
    try:
        start = _evaluated_root_integer(request["frame_start"], "frame_start")
        end = _evaluated_root_integer(request["frame_end"], "frame_end")
        step = _evaluated_root_integer(request["frame_step"], "frame_step")
        tolerance = _evaluated_root_number(request["tolerance"], "tolerance")
    except ValueError as exc:
        report["errors"].append(str(exc))
        return report
    if end < start:
        report["errors"].append("frame_end must be greater than or equal to frame_start")
    if step != 1:
        report["errors"].append("This bounded evaluator requires frame_step=1")
    if end - start > 10000:
        report["errors"].append("Requested evaluation range exceeds 10001 frames")
    if tolerance < 0.0:
        report["errors"].append("tolerance must be nonnegative")
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
    bone = obj.data.bones.get(request["bone_name"])
    if bone is None:
        report["errors"].append("Named root bone not found")
        return report
    if bone.parent is not None:
        report["errors"].append("The explicit root-motion bone must have no parent")
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
    object_channels = sorted({curve.data_path for curve, _ in applicable
                              if curve.data_path in _OBJECT_TRANSFORM_PATHS})
    if object_channels:
        report["errors"].append("Object transform channels are not supported: " +
                                ", ".join(object_channels))
    location_curves = [curve for curve, _ in applicable
                       if _decoded_bone(curve.data_path) == bone.name
                       and curve.data_path.endswith(".location")
                       and curve.array_index in {0, 1, 2}]
    if not location_curves:
        report["errors"].append("No location F-Curve matches the explicit root bone")
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
    points = {"LOCAL_BASIS": [], "ARMATURE": [], "WORLD": []}
    try:
        work_scene = bpy.data.scenes.new("GAI_EvaluatedRootMotion_" + token)
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
        for frame in range(start, end + 1, step):
            work_scene.frame_set(frame)
            depsgraph = bpy.context.evaluated_depsgraph_get()
            evaluated = work_obj.evaluated_get(depsgraph)
            pose = evaluated.pose.bones[bone.name]
            local_point = pose.matrix_basis.translation.copy()
            armature_point = pose.matrix.translation.copy()
            world_point = (evaluated.matrix_world @ pose.matrix).translation.copy()
            for space, point in (("LOCAL_BASIS", local_point),
                                 ("ARMATURE", armature_point), ("WORLD", world_point)):
                if any(not math.isfinite(float(value)) for value in point):
                    raise RuntimeError(f"Non-finite evaluated position in {space} space")
                points[space].append(point)
        metrics = {space: _evaluated_root_metrics(values) for space, values in points.items()}
        report.update({
            "status": "ok",
            "blender_version": bpy.app.version_string,
            "scene": scene.name,
            "armature": obj.name,
            "action": action.name,
            "bone": bone.name,
            "slot_identifier": effective_slot,
            "frame_start": start,
            "frame_end": end,
            "frame_step": step,
            "sample_count": len(points["WORLD"]),
            "tolerance": tolerance,
            "spaces": metrics,
            "net_translation_evidence": metrics["WORLD"]["net_distance"] > tolerance,
            "path_translation_evidence": metrics["WORLD"]["path_length"] > tolerance,
        })
        report["reviews"].append(
            "WORLD metrics include the Armature Object's static transform; no Unity root-motion policy is inferred")
        report["reviews"].append(
            "Integer-frame sampling evaluates interpolation and bone hierarchy but excludes constraints, drivers, NLA blending and subframes")
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
