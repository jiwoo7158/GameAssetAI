"""Read-only stored F-Curve endpoint comparison for one Blender Action."""
from __future__ import annotations

import math
import bpy


def _loop_number(value, label, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    value = float(value)
    if not math.isfinite(value) or (positive and value < 0.0):
        raise ValueError(f"{label} must be finite and nonnegative")
    return value


def _curves_with_slots(action):
    entries = []
    for curve in getattr(action, "fcurves", ()):
        entries.append((curve, None))
    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            for bag in getattr(strip, "channelbags", ()):
                slot = getattr(getattr(bag, "slot", None), "identifier", None)
                for curve in bag.fcurves:
                    entries.append((curve, slot))
    seen = set()
    result = []
    for curve, slot in entries:
        pointer = curve.as_pointer()
        if pointer not in seen:
            seen.add(pointer); result.append((curve, slot))
    return result


def inspect_action_loop(scene_name, action_name, start_frame, end_frame,
                        value_tolerance, frame_tolerance=1e-6):
    """Compare stored F-Curve components at explicit endpoints without changing frames."""
    report = {"schema": "gameassetai.action-loop-endpoints.v1", "status": "error",
              "errors": [], "reviews": []}
    scene = bpy.data.scenes.get(scene_name) if isinstance(scene_name, str) else None
    if scene is None:
        report["errors"].append("Named Scene not found")
        return report
    if not isinstance(action_name, str) or not action_name:
        report["errors"].append("action_name must be a nonempty string")
        return report
    action = bpy.data.actions.get(action_name)
    if action is None:
        report["errors"].append("Named Action not found")
        return report
    try:
        start = _loop_number(start_frame, "start_frame")
        end = _loop_number(end_frame, "end_frame")
        tolerance = _loop_number(value_tolerance, "value_tolerance", positive=True)
        frame_epsilon = _loop_number(frame_tolerance, "frame_tolerance", positive=True)
    except ValueError as exc:
        report["errors"].append(str(exc))
        return report
    if end <= start:
        report["errors"].append("end_frame must be greater than start_frame")
        return report

    channels = []
    for curve, slot in _curves_with_slots(action):
        try:
            first = float(curve.evaluate(start)); last = float(curve.evaluate(end))
        except (TypeError, ValueError, RuntimeError) as exc:
            report["errors"].append(
                f"Could not evaluate {curve.data_path}[{curve.array_index}]: {exc}")
            return report
        if not math.isfinite(first) or not math.isfinite(last):
            report["errors"].append("FCurve endpoint evaluation produced a non-finite value")
            return report
        frames = [float(point.co.x) for point in curve.keyframe_points]
        delta = abs(last - first)
        channels.append({"slot": slot, "data_path": curve.data_path,
                         "array_index": curve.array_index,
                         "start_value": first, "end_value": last,
                         "absolute_delta": delta,
                         "component_match": delta <= tolerance,
                         "has_start_key": any(abs(value - start) <= frame_epsilon for value in frames),
                         "has_end_key": any(abs(value - end) <= frame_epsilon for value in frames),
                         "keyframe_count": len(frames),
                         "cyclic_modifier": any(mod.type == "CYCLES" for mod in curve.modifiers)})
    if not channels:
        report["status"] = "incomplete"
        report["reviews"].append("The Action has no F-Curves to compare")
    else:
        report["status"] = "ok"
    all_match = bool(channels) and all(item["component_match"] for item in channels)
    all_keyed = bool(channels) and all(item["has_start_key"] and item["has_end_key"]
                                       for item in channels)
    if any(item["data_path"].endswith(("rotation_quaternion", "rotation_axis_angle",
                                       "rotation_euler")) for item in channels):
        report["reviews"].append(
            "Rotation channels are compared component-by-component; equivalent wrapped or sign-flipped rotations are not resolved")
    if not all_keyed and channels:
        report["reviews"].append(
            "At least one channel lacks a key at an explicit boundary; evaluated extrapolation/interpolation was compared")
    report["reviews"].append(
        "Endpoint component equality does not certify tangent, velocity, pose, constraint, root-motion or visual loop continuity")
    report.update({"blender_version": bpy.app.version_string, "scene": scene.name,
                   "action": action.name, "start_frame": start, "end_frame": end,
                   "value_tolerance": tolerance, "frame_tolerance": frame_epsilon,
                   "channels": channels, "all_components_match": all_match,
                   "all_channels_keyed_at_boundaries": all_keyed,
                   "endpoint_candidate": all_match and all_keyed})
    return report

