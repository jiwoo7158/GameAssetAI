"""Extract one strict exact-key linear frame range into an unbound Action copy."""
from __future__ import annotations

import hashlib
import json
import math

import bpy


ACTION_RANGE_SCHEMA = "gameassetai.action-range-extraction-request.v1"
_RANGE_KEYS = {"schema", "scene_name", "source_action", "source_slot_identifier",
               "target_action", "frame_start", "frame_end", "frame_policy",
               "preserve_source", "bind_result", "set_fake_user"}


def _range_digest(value):
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False,
                     sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _range_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return int(value)


def _curve_frames(curve):
    return [float(point.co.x) for point in curve.keyframe_points]


def preview_action_range_extraction(request):
    """Return a no-write plan for strict linear exact-boundary extraction."""
    report = {"schema": "gameassetai.action-range-extraction-plan.v1",
              "status": "error", "errors": [], "reviews": [], "authorization": False}
    if not isinstance(request, dict):
        report["errors"].append("Request must be an object")
        return report
    unknown = sorted(set(request) - _RANGE_KEYS)
    missing = sorted(_RANGE_KEYS - set(request))
    if unknown:
        report["errors"].append("Unknown request fields: " + ", ".join(unknown))
    if missing:
        report["errors"].append("Missing request fields: " + ", ".join(missing))
    if unknown or missing:
        return report
    if request["schema"] != ACTION_RANGE_SCHEMA:
        report["errors"].append("Unsupported request schema")
    for key in ("scene_name", "source_action", "source_slot_identifier", "target_action"):
        value = request[key]
        if not isinstance(value, str) or not value or value != value.strip():
            report["errors"].append(f"{key} must be an exact nonempty name")
    if request["source_action"] == request["target_action"]:
        report["errors"].append("Source and target Action names must differ")
    if request["frame_policy"] not in {"KEEP_FRAMES", "REBASE_TO_ZERO", "REBASE_TO_ONE"}:
        report["errors"].append("frame_policy must be KEEP_FRAMES, REBASE_TO_ZERO or REBASE_TO_ONE")
    for key, expected in (("preserve_source", True), ("bind_result", False),
                          ("set_fake_user", True)):
        if request[key] is not expected:
            report["errors"].append(f"This workflow requires {key}={str(expected).lower()}")
    try:
        start = _range_int(request["frame_start"], "frame_start")
        end = _range_int(request["frame_end"], "frame_end")
    except ValueError as exc:
        report["errors"].append(str(exc))
        return report
    if end <= start:
        report["errors"].append("frame_end must be greater than frame_start")
    if end - start > 10000:
        report["errors"].append("Extraction range exceeds 10001 frames")
    if report["errors"]:
        return report
    scene = bpy.data.scenes.get(request["scene_name"])
    source = bpy.data.actions.get(request["source_action"])
    if scene is None:
        report["errors"].append("Scene not found")
    if source is None:
        report["errors"].append("Source Action not found")
    if bpy.data.actions.get(request["target_action"]) is not None:
        report["errors"].append("Target Action already exists")
    if report["errors"]:
        return report
    slots = list(getattr(source, "slots", ()))
    if (len(slots) != 1 or getattr(slots[0], "target_id_type", None) != "OBJECT"
            or slots[0].identifier != request["source_slot_identifier"]):
        report["errors"].append("Source Action requires the exact single Object slot")
    curves = _curves(source)
    if not curves:
        report["errors"].append("Source Action has no F-Curves")
    kept_keys = 0
    for curve in curves:
        points = list(curve.keyframe_points)
        frames = _curve_frames(curve)
        if curve.sampled_points or curve.modifiers:
            report["errors"].append("Sampled points and F-Curve modifiers are not supported")
            break
        if len(frames) != len(set(frames)):
            report["errors"].append("Duplicate keyframe times are not supported")
            break
        if float(start) not in frames or float(end) not in frames:
            report["errors"].append("Every F-Curve requires exact start and end keys")
            break
        if any(point.interpolation != "LINEAR" for point in points):
            report["errors"].append("Every source keyframe must use LINEAR interpolation")
            break
        kept_keys += sum(start <= frame <= end for frame in frames)
    if report["errors"]:
        return report
    current, nla = _action_references(source)
    policy = request["frame_policy"]
    output_start = start if policy == "KEEP_FRAMES" else (0 if policy == "REBASE_TO_ZERO" else 1)
    frame_offset = start - output_start
    candidate = {"operation": "extract_exact_linear_range_copy",
                 "frame_start": start, "frame_end": end,
                 "frame_policy": policy, "frame_offset": frame_offset,
                 "output_frame_start": output_start,
                 "output_frame_end": end - frame_offset,
                 "curve_count": len(curves),
                 "kept_keyframe_count": kept_keys,
                 "kept_pose_marker_count": sum(start <= marker.frame <= end
                                                for marker in source.pose_markers),
                 "source_content_sha256": action_content_fingerprint(source),
                 "source_references_sha256": _range_digest({"current": current,
                                                              "nla": nla}),
                 "request_sha256": _range_digest(request)}
    report.update({"status": "candidate_for_review", "request": dict(request),
                   "candidate": candidate})
    report["reviews"].append("Only exact existing linear keys are retained; no boundary values are synthesized")
    report["reviews"].append("The result remains unbound; key, handle and pose-marker times use one reviewed offset")
    return report


def apply_action_range_extraction(plan, authorization=False):
    """Create one independent unbound range copy from a fresh strict plan."""
    result = {"schema": "gameassetai.action-range-extraction-result.v1",
              "status": "error", "errors": []}
    if authorization is not True:
        result["errors"].append("Explicit authorization=true is required")
        return result
    if (not isinstance(plan, dict)
            or plan.get("schema") != "gameassetai.action-range-extraction-plan.v1"
            or plan.get("status") != "candidate_for_review"):
        result["errors"].append("A candidate_for_review plan is required")
        return result
    request, candidate = plan.get("request"), plan.get("candidate")
    fresh = preview_action_range_extraction(request) if isinstance(request, dict) else None
    if (not fresh or fresh.get("status") != "candidate_for_review"
            or fresh.get("candidate") != candidate):
        result["errors"].append("Action range preview is stale")
        return result
    source = bpy.data.actions[request["source_action"]]
    source_snapshot = action_content_snapshot(source)
    source_refs = _action_references(source)
    created = None
    start, end = candidate["frame_start"], candidate["frame_end"]
    offset = candidate["frame_offset"]
    output_start, output_end = candidate["output_frame_start"], candidate["output_frame_end"]
    try:
        created = source.copy()
        created.name = request["target_action"]
        created.use_fake_user = True
        if created.name != request["target_action"] or created == source:
            raise RuntimeError("Blender did not create the exact independent target Action")
        for curve in _curves(created):
            for index in reversed(range(len(curve.keyframe_points))):
                point = curve.keyframe_points[index]
                if not start <= float(point.co.x) <= end:
                    curve.keyframe_points.remove(point, fast=True)
            for point in curve.keyframe_points:
                point.co.x -= offset
                point.handle_left.x -= offset
                point.handle_right.x -= offset
            curve.update()
        for index in reversed(range(len(created.pose_markers))):
            marker = created.pose_markers[index]
            if not start <= marker.frame <= end:
                created.pose_markers.remove(marker)
        for marker in created.pose_markers:
            marker.frame -= offset
        target_curves = _curves(created)
        if len(target_curves) != candidate["curve_count"]:
            raise RuntimeError("Target F-Curve count differs from the source")
        frames = [_curve_frames(curve) for curve in target_curves]
        if (any(not values or min(values) < output_start or max(values) > output_end
                or float(output_start) not in values or float(output_end) not in values for values in frames)
                or sum(len(values) for values in frames) != candidate["kept_keyframe_count"]):
            raise RuntimeError("Target keyframe range differs from the reviewed extraction")
        if (len(created.pose_markers) != candidate["kept_pose_marker_count"]
                or any(not output_start <= marker.frame <= output_end
                       for marker in created.pose_markers)):
            raise RuntimeError("Target pose markers differ from the reviewed extraction")
        if _action_references(created) != ([], []):
            raise RuntimeError("Extracted Action was unexpectedly bound")
        if (action_content_snapshot(source) != source_snapshot
                or _action_references(source) != source_refs):
            raise RuntimeError("Source Action or its references changed")
        result.update({"status": "created", "source_action": source.name,
                       "target_action": created.name, "source_frame_start": start,
                       "source_frame_end": end, "frame_policy": candidate["frame_policy"],
                       "frame_offset": offset, "frame_start": output_start,
                       "frame_end": output_end, "curve_count": len(target_curves),
                       "keyframe_count": sum(len(values) for values in frames),
                       "pose_marker_count": len(created.pose_markers),
                       "target_content_sha256": action_content_fingerprint(created),
                       "target_fake_user": True, "target_unbound": True,
                       "source_references_preserved": True})
        return result
    except Exception as exc:
        if created is not None and bpy.data.actions.get(created.name) == created:
            bpy.data.actions.remove(created)
        result["errors"].append(str(exc))
        return result
# Retained bounded Blender capability; product support remains evidence-scoped.
