"""Read-only translation evidence for one explicit Object or Armature bone in an Action."""
from __future__ import annotations

import math
import re
import bpy


_ROOT_BONE_PATH = re.compile(r'^pose\.bones\["((?:[^"\\]|\\.)*)"\]\.location$')


def _root_number(value, label, *, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    if nonnegative and value < 0.0:
        raise ValueError(f"{label} must be nonnegative")
    return value


def _decoded_bone(data_path):
    match = _ROOT_BONE_PATH.match(data_path)
    return (match.group(1).replace('\\"', '"').replace('\\\\', '\\')
            if match else None)


def inspect_root_motion(scene_name, object_name, action_name, start_frame, end_frame,
                        value_tolerance, bone_name=None, slot_identifier=None):
    """Inspect explicit root translation channels without graph/frame changes or writes."""
    report = {"schema": "gameassetai.root-motion-inspection.v1", "status": "error",
              "errors": [], "reviews": []}
    scene = bpy.data.scenes.get(scene_name) if isinstance(scene_name, str) else None
    if scene is None:
        report["errors"].append("Named Scene not found")
        return report
    obj = scene.objects.get(object_name) if isinstance(object_name, str) else None
    if obj is None:
        report["errors"].append("Named Object not found in Scene")
        return report
    action = bpy.data.actions.get(action_name) if isinstance(action_name, str) else None
    if action is None:
        report["errors"].append("Named Action not found")
        return report
    if bone_name is not None:
        if not isinstance(bone_name, str) or not bone_name:
            report["errors"].append("bone_name must be null or a nonempty exact name")
            return report
        if obj.type != "ARMATURE" or obj.data.bones.get(bone_name) is None:
            report["errors"].append("Named bone not found on the Armature Object")
            return report
    if slot_identifier is not None and (not isinstance(slot_identifier, str) or not slot_identifier):
        report["errors"].append("slot_identifier must be null or a nonempty exact identifier")
        return report
    try:
        start = _root_number(start_frame, "start_frame")
        end = _root_number(end_frame, "end_frame")
        tolerance = _root_number(value_tolerance, "value_tolerance", nonnegative=True)
    except ValueError as exc:
        report["errors"].append(str(exc))
        return report
    if end <= start:
        report["errors"].append("end_frame must be greater than start_frame")
        return report

    slots = [slot.identifier for slot in getattr(action, "slots", ())]
    if slot_identifier is None and len(slots) > 1:
        report["errors"].append("slot_identifier is required for a multi-slot Action")
        return report
    if slot_identifier is not None and slot_identifier not in slots:
        report["errors"].append("Named Action slot not found")
        return report
    effective_slot = slot_identifier if slot_identifier is not None else (slots[0] if slots else None)

    channels = []
    other_root_transforms = []
    for curve, slot in _curves_with_slots(action):
        if effective_slot is not None and slot not in {None, effective_slot}:
            continue
        is_root = (curve.data_path == "location" if bone_name is None
                   else _decoded_bone(curve.data_path) == bone_name)
        if is_root and curve.data_path.endswith("location"):
            if curve.array_index not in {0, 1, 2}:
                continue
            first = float(curve.evaluate(start)); last = float(curve.evaluate(end))
            keyed_values = [float(point.co.y) for point in curve.keyframe_points
                            if start <= float(point.co.x) <= end]
            if (not math.isfinite(first) or not math.isfinite(last) or
                    any(not math.isfinite(value) for value in keyed_values)):
                report["errors"].append("Root translation contains a non-finite value")
                return report
            low = min(keyed_values, default=None); high = max(keyed_values, default=None)
            span = (high - low) if keyed_values else None
            channels.append({"axis": "XYZ"[curve.array_index], "array_index": curve.array_index,
                             "slot": slot, "data_path": curve.data_path,
                             "start_value": first, "end_value": last,
                             "net_delta": last - first, "keyed_min": low, "keyed_max": high,
                             "keyed_span": span, "keyframe_count_in_range": len(keyed_values),
                             "translation_evidence": (abs(last - first) > tolerance or
                                                      (span is not None and span > tolerance))})
        elif ((bone_name is None and curve.data_path.startswith("rotation_")) or
              (bone_name is not None and _decoded_bone(curve.data_path.replace(
                  ".rotation_quaternion", ".location").replace(
                  ".rotation_euler", ".location").replace(
                  ".rotation_axis_angle", ".location")) == bone_name)):
            other_root_transforms.append({"data_path": curve.data_path,
                                          "array_index": curve.array_index, "slot": slot})

    vector = [0.0, 0.0, 0.0]
    for channel in channels:
        vector[channel["array_index"]] = channel["net_delta"]
    report.update({"status": "ok", "blender_version": bpy.app.version_string,
                   "scene": scene.name, "object": obj.name, "object_type": obj.type,
                   "action": action.name, "slot_identifier": effective_slot,
                   "target_kind": "BONE" if bone_name is not None else "OBJECT",
                   "bone": bone_name, "start_frame": start, "end_frame": end,
                   "value_tolerance": tolerance, "translation_channels": channels,
                   "missing_translation_axes": [axis for axis in "XYZ"
                                                if axis not in {c["axis"] for c in channels}],
                   "net_translation": vector,
                   "net_distance": math.sqrt(sum(value * value for value in vector)),
                   "translation_evidence": any(c["translation_evidence"] for c in channels),
                   "other_root_transform_channels": other_root_transforms})
    if not channels:
        report["reviews"].append("No stored location F-Curves matched the explicit root target")
    if other_root_transforms:
        report["reviews"].append("Root rotation channels exist but are not interpreted by this translation inspection")
    report["reviews"].append(
        "Stored endpoint/key evidence does not include constraints, drivers, NLA blending, evaluated poses, interpolation extrema or engine root-motion policy")
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
