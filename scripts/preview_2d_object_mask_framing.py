"""Read-only union-bounds orthographic framing for an Object-mask candidate."""
from __future__ import annotations

import math
from mathutils import Vector


def preview_2d_object_mask_framing(request, candidate):
    report = {"schema": "gameassetai.2d-object-mask-framing-preview.v1", "status": "error",
              "errors": [], "camera_created": False, "render_authorized": False}
    try:
        if (candidate.get("schema") != "gameassetai.2d-object-mask-candidate.v1"
                or candidate.get("status") != "candidate_for_review"
                or candidate.get("blockers") != []
                or candidate.get("request_sha256") != _object_mask_hash(request)):
            raise ValueError("A current blocker-free Object-mask candidate is required")
        scene = bpy.data.scenes.get(candidate.get("scene"))
        target = scene.objects.get(candidate.get("target_object")) if scene else None
        occluders = ([scene.objects.get(name) for name in candidate.get("occluder_objects", [])]
                     if scene else [])
        if target is None or any(obj is None for obj in occluders):
            raise ValueError("Candidate Objects are no longer present")
        if candidate["source_fingerprint"] != _object_mask_hash(
                _object_mask_source_payload(scene, target, occluders)):
            raise ValueError("Object sources changed since candidate inspection")
        setup = {"view": request["view"], "mask": request["mask"],
                 "style": request["style"], "blender_version": bpy.app.version_string}
        if (candidate["setup_fingerprint"] != _object_mask_hash(setup)
                or candidate["output_fingerprint"] != _object_mask_hash(request["output"])):
            raise ValueError("Setup or output changed since candidate inspection")
        direction, up = Vector(request["view"]["direction"]), Vector(request["view"]["up"])
        right = up.cross(direction)
        if (abs(direction.length - 1) > 1e-6 or abs(up.length - 1) > 1e-6
                or abs(direction.dot(up)) > 1e-6 or abs(right.length - 1) > 1e-6):
            raise ValueError("Camera direction/up are no longer orthonormal")
        objects = [target, *occluders]
        points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
        center = sum(points, Vector()) / len(points)
        offsets = [point - center for point in points]
        half_width = max(abs(offset.dot(right)) for offset in offsets)
        half_height = max(abs(offset.dot(up)) for offset in offsets)
        half_depth = max(abs(offset.dot(direction)) for offset in offsets)
        width, height = request["style"]["resolution"]
        aspect = width / height
        fitted = (max(2 * half_width, 2 * half_height * aspect) if aspect >= 1
                  else max(2 * half_height, 2 * half_width / aspect))
        scale = fitted * (1 + 2 * float(request["view"]["framing_margin"]))
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError("Union bounds cannot produce a positive orthographic scale")
        extent = max(half_width, half_height, half_depth, 0.001)
        distance = half_depth + extent * 2 + 1
        plan = {"projection": "ORTHOGRAPHIC", "center": list(center),
                "position": list(center + direction * distance),
                "basis_columns": {"right_x": list(right), "up_y": list(up),
                                  "back_z": list(direction)},
                "orthographic_scale": scale,
                "clip_start": max(0.001, distance - half_depth - extent * 1.5),
                "clip_end": distance + half_depth + extent * 1.5,
                "resolution": [width, height], "aspect": aspect,
                "framing_margin_per_side": float(request["view"]["framing_margin"]),
                "projected_half_extents": [half_width, half_height, half_depth]}
        report.update(status="planned", request_sha256=candidate["request_sha256"],
                      source_fingerprint=candidate["source_fingerprint"],
                      setup_fingerprint=candidate["setup_fingerprint"],
                      output_fingerprint=candidate["output_fingerprint"], plan=plan,
                      plan_fingerprint=_object_mask_hash(plan),
                      limitations=["Framing covers the target plus every explicit occluder",
                                   "No Camera or render setup was created"])
    except (ValueError, TypeError, KeyError, OverflowError, RuntimeError) as exc:
        report["errors"].append(str(exc))
    return report
