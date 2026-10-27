"""Read-only orthographic camera/framing plan for a reviewed static 2D candidate.

Load the request validator and candidate inspector first. This computes a plan only; it
does not create a Camera, change a Scene, render, or authorize output.
"""
from __future__ import annotations

import math

from mathutils import Vector


def preview_2d_orthographic_framing(request, candidate):
    report = {"schema": "gameassetai.2d-orthographic-framing-preview.v1",
              "status": "error", "errors": [], "camera_created": False,
              "render_authorized": False}
    try:
        if not isinstance(request, dict) or not isinstance(candidate, dict):
            raise ValueError("Request and candidate must be objects")
        if (candidate.get("schema") != "gameassetai.2d-static-render-candidate.v1"
                or candidate.get("status") != "candidate_for_review"
                or candidate.get("blockers") != []):
            raise ValueError("A blocker-free reviewed candidate is required")
        if candidate.get("request_sha256") != _render_hash(request):
            raise ValueError("Request changed since candidate inspection")
        scene = bpy.data.scenes.get(candidate.get("scene"))
        obj = scene.objects.get(candidate.get("object")) if scene else None
        if obj is None or obj.type != "MESH" or obj.data.is_editmode:
            raise ValueError("Candidate source is no longer inspectable")
        if candidate.get("source_fingerprint") != _render_hash(_render_source_payload(scene, obj)):
            raise ValueError("Source changed since candidate inspection")
        setup = {"profile": request["profile"], "view": request["view"],
                 "lighting": request["lighting"], "style": request["style"],
                 "blender_version": bpy.app.version_string}
        if candidate.get("setup_fingerprint") != _render_hash(setup):
            raise ValueError("Setup changed since candidate inspection")
        if candidate.get("output_fingerprint") != _render_hash(request["output"]):
            raise ValueError("Output changed since candidate inspection")

        direction = Vector(request["view"]["direction"])
        up = Vector(request["view"]["up"])
        right = up.cross(direction)
        if abs(direction.length - 1.0) > 1e-6 or abs(up.length - 1.0) > 1e-6:
            raise ValueError("Camera direction/up must remain unit vectors")
        if abs(direction.dot(up)) > 1e-6 or abs(right.length - 1.0) > 1e-6:
            raise ValueError("Camera direction/up must remain perpendicular")
        points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        center = sum(points, Vector()) / len(points)
        offsets = [point - center for point in points]
        half_width = max(abs(offset.dot(right)) for offset in offsets)
        half_height = max(abs(offset.dot(up)) for offset in offsets)
        half_depth = max(abs(offset.dot(direction)) for offset in offsets)
        width, height = request["style"]["resolution"]
        aspect = float(width) / float(height)
        margin = float(request["view"]["framing_margin"])
        if aspect >= 1.0:
            # Blender's ortho_scale is the horizontal frame span in landscape output.
            fitted_scale = max(2.0 * half_width, 2.0 * half_height * aspect)
        else:
            # In portrait output it is the vertical span.
            fitted_scale = max(2.0 * half_height, 2.0 * half_width / aspect)
        ortho_scale = fitted_scale * (1.0 + 2.0 * margin)
        if not math.isfinite(ortho_scale) or ortho_scale <= 0.0:
            raise ValueError("Projected bounds cannot produce a positive orthographic scale")
        extent = max(half_width, half_height, half_depth, 0.001)
        distance = half_depth + extent * 2.0 + 1.0
        position = center + direction * distance
        clip_start = max(0.001, distance - half_depth - extent * 1.5)
        clip_end = distance + half_depth + extent * 1.5
        plan = {
            "projection": "ORTHOGRAPHIC",
            "center": list(center), "position": list(position),
            "basis_columns": {"right_x": list(right), "up_y": list(up),
                              "back_z": list(direction)},
            "orthographic_scale": ortho_scale,
            "clip_start": clip_start, "clip_end": clip_end,
            "resolution": [width, height], "aspect": aspect,
            "camera_frame": ([ortho_scale, ortho_scale / aspect] if aspect >= 1.0
                             else [ortho_scale * aspect, ortho_scale]),
            "framing_margin_per_side": margin,
            "projected_half_extents": [half_width, half_height, half_depth],
        }
        report.update(status="planned", request_sha256=candidate["request_sha256"],
                      source_fingerprint=candidate["source_fingerprint"],
                      setup_fingerprint=candidate["setup_fingerprint"],
                      output_fingerprint=candidate["output_fingerprint"],
                      plan=plan, plan_fingerprint=_render_hash(plan),
                      limitations=["Plan uses base Object bound_box, not evaluated geometry",
                                   "Margin is a fraction of fitted extent on each side",
                                   "No Camera or render setup has been created"])
    except (ValueError, TypeError, KeyError, OverflowError, RuntimeError) as exc:
        report["errors"].append(str(exc))
    return report

