"""Plan one stable orthographic camera from evaluated Action-range union bounds."""
from __future__ import annotations

import math

from mathutils import Vector


def preview_2d_action_sequence_framing(request, preflight, candidate):
    report = {"schema": "gameassetai.2d-action-sequence-framing-preview.v1",
              "status": "error", "errors": [], "camera_created": False,
              "render_authorized": False}
    try:
        if (not isinstance(candidate, dict)
                or candidate.get("schema") != CANDIDATE_SCHEMA
                or candidate.get("status") != "candidate_for_review"
                or candidate.get("blockers") != []):
            raise ValueError("A blocker-free Action-sequence candidate is required")
        fresh = inspect_2d_action_sequence_candidate(request, preflight)
        if fresh.get("status") != "candidate_for_review":
            raise ValueError("Action-sequence candidate is no longer valid")
        for key in ("request_sha256", "frame_plan_sha256", "source_fingerprint",
                    "action_fingerprint", "evaluation_fingerprint"):
            if fresh.get(key) != candidate.get(key):
                raise ValueError("Action-sequence candidate changed before framing")

        template = request["static_template"]
        direction = Vector(template["view"]["direction"])
        up = Vector(template["view"]["up"])
        right = up.cross(direction)
        projected = candidate["evaluation"]["projected_union_bounds"]
        minimum, maximum = projected["minimum"], projected["maximum"]
        center_components = [(a + b) / 2.0 for a, b in zip(minimum, maximum)]
        half_width, half_height, half_depth = [
            (maximum[index] - minimum[index]) / 2.0 for index in range(3)]
        width, height = template["style"]["resolution"]
        aspect = float(width) / float(height)
        margin = float(template["view"]["framing_margin"])
        fitted = (max(2.0 * half_width, 2.0 * half_height * aspect)
                  if aspect >= 1.0 else
                  max(2.0 * half_height, 2.0 * half_width / aspect))
        scale = fitted * (1.0 + 2.0 * margin)
        if not math.isfinite(scale) or scale <= 0.0:
            raise ValueError("Evaluated projected bounds cannot produce positive framing")
        frame_width, frame_height = ((scale, scale / aspect) if aspect >= 1.0
                                     else (scale * aspect, scale))
        center = (right * center_components[0] + up * center_components[1]
                  + direction * center_components[2])
        extent = max(half_width, half_height, half_depth, 0.001)
        distance = half_depth + extent * 2.0 + 1.0
        anchor = Vector(candidate["evaluation"]["anchor_world"])
        anchor_projected = [anchor.dot(right), anchor.dot(up), anchor.dot(direction)]
        anchor_pixel = [
            (0.5 + (anchor_projected[0] - center_components[0]) / frame_width) * width,
            (0.5 + (anchor_projected[1] - center_components[1]) / frame_height) * height,
        ]
        plan = {
            "projection": "ORTHOGRAPHIC", "position": list(center + direction * distance),
            "center": list(center),
            "basis_columns": {"right_x": list(right), "up_y": list(up),
                              "back_z": list(direction)},
            "orthographic_scale": scale,
            "clip_start": max(0.001, distance - half_depth - extent * 1.5),
            "clip_end": distance + half_depth + extent * 1.5,
            "resolution": [width, height], "aspect": aspect,
            "camera_frame": [frame_width, frame_height],
            "framing_margin_per_side": margin,
            "projected_half_extents": [half_width, half_height, half_depth],
            "anchor_policy": request["framing"]["anchor_policy"],
            "anchor_world": list(anchor), "anchor_pixel_from_bottom_left": anchor_pixel,
        }
        report.update(status="planned", request_sha256=candidate["request_sha256"],
                      frame_plan_sha256=candidate["frame_plan_sha256"],
                      source_fingerprint=candidate["source_fingerprint"],
                      action_fingerprint=candidate["action_fingerprint"],
                      evaluation_fingerprint=candidate["evaluation_fingerprint"],
                      plan=plan, plan_fingerprint=_hash(plan),
                      limitations=["One camera fits the evaluated sampled-frame union",
                                   "Anchor pixel uses the Mesh Object origin; no root bone is guessed",
                                   "No Camera, Scene or file was created"])
    except (ValueError, TypeError, KeyError, RuntimeError, OverflowError) as exc:
        report["errors"].append(str(exc))
    return report
