"""Read-only shared orthographic framing for a validated static impostor bundle."""
from __future__ import annotations

import hashlib
import json
import math

import bpy
from mathutils import Vector

import inspect_2d_depth_pass_candidate as _depth_candidate_module
import inspect_2d_normal_pass_candidate as _normal_candidate_module
import inspect_2d_static_render_candidate as _color_candidate_module
from validate_2d_depth_pass_request import (SCHEMA as DEPTH_SCHEMA,
                                            validate_2d_depth_pass_request)
from validate_2d_impostor_bundle_request import validate_2d_impostor_bundle_request
from validate_2d_normal_pass_request import (SCHEMA as NORMAL_SCHEMA,
                                             validate_2d_normal_pass_request)
from validate_2d_static_render_request import (SCHEMA as COLOR_SCHEMA,
                                               validate_2d_static_render_request)


SCHEMA = "gameassetai.2d-impostor-shared-framing-preview.v1"

# The three legacy candidate modules were originally executed in the matching validator's
# namespace and therefore resolve SCHEMA dynamically. Make that dependency explicit when
# composing them as ordinary modules; no candidate code or Blender state is modified.
_color_candidate_module.SCHEMA = COLOR_SCHEMA
_normal_candidate_module.SCHEMA = NORMAL_SCHEMA
_depth_candidate_module.SCHEMA = DEPTH_SCHEMA


def _hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_payload(scene, obj):
    mesh = obj.data
    return {
        "scene": scene.name,
        "frame": [scene.frame_current, scene.frame_subframe],
        "unit": [scene.unit_settings.system, scene.unit_settings.scale_length],
        "object": {"name": obj.name, "data": mesh.name,
                   "matrix_world": [list(row) for row in obj.matrix_world],
                   "bound_box": [list(corner) for corner in obj.bound_box],
                   "visible_render": not obj.hide_render},
        "mesh": {"vertices": [list(vertex.co) for vertex in mesh.vertices],
                 "edges": [list(edge.vertices) for edge in mesh.edges],
                 "polygons": [{"vertices": list(face.vertices),
                               "material_index": face.material_index,
                               "use_smooth": face.use_smooth}
                              for face in mesh.polygons]},
    }


def _candidate(kind, child):
    if kind == "COLOR":
        preflight = validate_2d_static_render_request(child)
        return _color_candidate_module.inspect_2d_static_render_candidate(child, preflight)
    if kind == "NORMAL":
        preflight = validate_2d_normal_pass_request(child)
        return _normal_candidate_module.inspect_2d_normal_pass_candidate(child, preflight)
    if kind == "DEPTH":
        preflight = validate_2d_depth_pass_request(child)
        return _depth_candidate_module.inspect_2d_depth_pass_candidate(child, preflight)
    raise ValueError("Unsupported bundle pass kind")


def _plan(obj, view, resolution):
    direction, up = Vector(view["direction"]), Vector(view["up"])
    right = up.cross(direction)
    if (abs(direction.length - 1.0) > 1e-6 or abs(up.length - 1.0) > 1e-6
            or abs(direction.dot(up)) > 1e-6 or abs(right.length - 1.0) > 1e-6):
        raise ValueError("Camera direction/up are no longer orthonormal")
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    center = sum(points, Vector()) / len(points)
    offsets = [point - center for point in points]
    half_width = max(abs(offset.dot(right)) for offset in offsets)
    half_height = max(abs(offset.dot(up)) for offset in offsets)
    half_depth = max(abs(offset.dot(direction)) for offset in offsets)
    width, height = resolution
    aspect = float(width) / float(height)
    fitted = (max(2.0 * half_width, 2.0 * half_height * aspect) if aspect >= 1.0
              else max(2.0 * half_height, 2.0 * half_width / aspect))
    scale = fitted * (1.0 + 2.0 * float(view["framing_margin"]))
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("Projected bounds cannot produce a positive orthographic scale")
    extent = max(half_width, half_height, half_depth, 0.001)
    distance = half_depth + extent * 2.0 + 1.0
    return {
        "projection": "ORTHOGRAPHIC",
        "center": list(center), "position": list(center + direction * distance),
        "basis_columns": {"right_x": list(right), "up_y": list(up),
                          "back_z": list(direction)},
        "orthographic_scale": scale,
        "clip_start": max(0.001, distance - half_depth - extent * 1.5),
        "clip_end": distance + half_depth + extent * 1.5,
        "resolution": [width, height], "aspect": aspect,
        "framing_margin_per_side": float(view["framing_margin"]),
        "projected_half_extents": [half_width, half_height, half_depth],
    }


def preview_2d_impostor_shared_framing(request, request_preflight):
    """Inspect every child and bind one canonical camera plan per explicit view."""
    report = {"schema": SCHEMA, "status": "error", "errors": [], "blockers": [],
              "camera_created": False, "render_authorized": False,
              "request_sha256": None, "source_fingerprint": None, "views": []}
    try:
        if not isinstance(request, dict) or not isinstance(request_preflight, dict):
            raise ValueError("Request and request_preflight must be objects")
        fresh = validate_2d_impostor_bundle_request(request)
        if (fresh.get("status") != "ready"
                or fresh.get("ready_for_shared_framing_preview") is not True):
            raise ValueError("A currently valid impostor bundle request is required")
        if request_preflight != fresh:
            raise ValueError("Bundle request or offline preflight changed")
        scene = bpy.data.scenes.get(fresh["scene_name"])
        obj = scene.objects.get(fresh["object_name"]) if scene else None
        if obj is None or obj.type != "MESH" or obj.data.is_editmode:
            raise ValueError("Requested static Mesh is no longer inspectable")

        source_fingerprint = _hash(_source_payload(scene, obj))
        child_reports, blockers = [], []
        request_items = request["items"]
        for planned, item in zip(fresh["items"], request_items):
            candidate = _candidate(item["pass_kind"], item["request"])
            if candidate.get("status") != "candidate_for_review" or candidate.get("blockers") != []:
                reasons = candidate.get("blockers") or ["candidate_not_reviewable"]
                blockers.extend(f"{item['id']}:{value}" for value in reasons)
            if candidate.get("request_sha256") != planned["request_sha256"]:
                raise ValueError(f"Child request binding changed for {item['id']}")
            child_reports.append({"position": planned["position"], "id": item["id"],
                                  "view_id": item["view_id"],
                                  "pass_kind": item["pass_kind"],
                                  "request_sha256": planned["request_sha256"],
                                  "candidate_schema": candidate.get("schema"),
                                  "candidate_status": candidate.get("status"),
                                  "source_fingerprint": candidate.get("source_fingerprint"),
                                  "setup_fingerprint": candidate.get("setup_fingerprint"),
                                  "output_fingerprint": candidate.get("output_fingerprint")})
        if blockers:
            report.update(status="blocked", request_sha256=fresh["request_sha256"],
                          source_fingerprint=source_fingerprint,
                          blockers=sorted(set(blockers)), children=child_reports)
            return report

        views = []
        for view_entry in fresh["views"]:
            view_id = view_entry["view_id"]
            framing = view_entry["framing"]
            plan = _plan(obj, framing["view"], framing["resolution"])
            plan_fingerprint = _hash(plan)
            children = []
            for child in child_reports:
                if child["view_id"] == view_id:
                    bound = dict(child)
                    bound["shared_plan_fingerprint"] = plan_fingerprint
                    children.append(bound)
            views.append({"view_id": view_id, "plan": plan,
                          "plan_fingerprint": plan_fingerprint, "children": children})
        report.update(status="planned", request_sha256=fresh["request_sha256"],
                      source_fingerprint=source_fingerprint, views=views,
                      view_count=len(views), child_count=len(child_reports), children=child_reports,
                      preview_fingerprint=_hash({"request_sha256": fresh["request_sha256"],
                                                 "source_fingerprint": source_fingerprint,
                                                 "views": views}),
                      limitations=["Plans use base Object bound_box, not evaluated geometry",
                                   "No Camera, render setup, output or manifest was created",
                                   "A later coordinator must recheck request/source/plan hashes"])
    except (ValueError, TypeError, KeyError, OverflowError, RuntimeError) as exc:
        report["errors"].append(str(exc))
    return report
