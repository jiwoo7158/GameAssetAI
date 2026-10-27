"""Read-only Blender candidate and vertex-range probe for a depth-pass request."""
from __future__ import annotations

import hashlib
import json
import math

import bpy


def _depth_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _depth_source_payload(scene, obj):
    mesh = obj.data
    return {"scene": scene.name, "frame": [scene.frame_current, scene.frame_subframe],
            "unit": [scene.unit_settings.system, scene.unit_settings.scale_length],
            "object": {"name": obj.name, "mesh": mesh.name,
                       "matrix_world": [list(row) for row in obj.matrix_world],
                       "hide_render": obj.hide_render},
            "mesh": {"vertices": [list(vertex.co) for vertex in mesh.vertices],
                     "edges": [list(edge.vertices) for edge in mesh.edges],
                     "polygons": [list(face.vertices) for face in mesh.polygons]}}


def _depth_world_bounds(obj):
    vector = __import__("mathutils").Vector
    points = [obj.matrix_world @ vector(corner) for corner in obj.bound_box]
    values = [[float(axis) for axis in point] for point in points]
    if not all(math.isfinite(axis) for point in values for axis in point):
        raise ValueError("Object bounds are nonfinite")
    minimum = [min(point[axis] for point in values) for axis in range(3)]
    maximum = [max(point[axis] for point in values) for axis in range(3)]
    return {"minimum": minimum, "maximum": maximum,
            "center": [(a + b) / 2 for a, b in zip(minimum, maximum)],
            "dimensions": [b - a for a, b in zip(minimum, maximum)]}


def inspect_2d_depth_pass_candidate(request, preflight):
    report = {"schema": "gameassetai.2d-depth-pass-candidate.v1", "status": "error",
              "errors": [], "blockers": [], "render_authorized": False,
              "destination_rechecked": False}
    try:
        if (request.get("schema") != SCHEMA or preflight.get("schema") != SCHEMA
                or preflight.get("ready_for_blender_inspection") is not True
                or preflight.get("errors") != []):
            raise ValueError("A successful depth-pass request preflight is required")
        request_hash = _depth_hash(request)
        if preflight.get("request_sha256") != request_hash:
            raise ValueError("Request changed since offline preflight")
        scene = bpy.data.scenes.get(request["scene_name"])
        obj = scene.objects.get(request["object_name"]) if scene else None
        if obj is None:
            raise ValueError("Requested Scene/Object was not found")
        if obj.type != "MESH" or obj.data.is_editmode:
            raise ValueError("Requested Object must be an Object-mode Mesh")
        mesh = obj.data
        blockers = []
        checks = ((not mesh.vertices or not mesh.polygons, "non_renderable_empty_mesh"),
                  (obj.hide_render, "object_hidden_for_render"),
                  (bool(obj.parent), "parent_dependency_unsupported"),
                  (bool(obj.constraints), "object_constraints_unsupported"),
                  (bool(obj.modifiers), "modifiers_unsupported"),
                  (bool(obj.animation_data or mesh.animation_data), "animation_unsupported"),
                  (bool(mesh.shape_keys), "shape_keys_unsupported"),
                  (bool(obj.library or mesh.library), "linked_library_data_unsupported"))
        blockers.extend(name for condition, name in checks if condition)
        vector = __import__("mathutils").Vector
        direction, up = vector(request["view"]["direction"]), vector(request["view"]["up"])
        right = up.cross(direction)
        world_vertices = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
        projections = [float(point.dot(direction)) for point in world_vertices]
        if not projections or not all(math.isfinite(value) for value in projections):
            raise ValueError("Base-Mesh vertex depth projections are empty or nonfinite")
        near_projection, far_projection = max(projections), min(projections)
        span = near_projection - far_projection
        if not math.isfinite(span) or span <= 1e-6:
            blockers.append("base_mesh_depth_span_too_small")
        samples = [] if span <= 1e-6 else [
            {"vertex_index": index, "world_position": list(world_vertices[index]),
             "projection": projection,
             "depth_01": (near_projection - projection) / span,
             "encoded_rgb_reference": [max(0, min(255, round(
                 (near_projection - projection) / span * 255)))] * 3}
            for index, projection in list(enumerate(projections))[:64]]
        source = _depth_source_payload(scene, obj)
        setup = {"view": request["view"], "depth": request["depth"],
                 "style": request["style"], "blender_version": bpy.app.version_string}
        report.update(status="blocked" if blockers else "candidate_for_review",
                      request_sha256=request_hash, source_fingerprint=_depth_hash(source),
                      setup_fingerprint=_depth_hash(setup),
                      output_fingerprint=_depth_hash(request["output"]),
                      scene=scene.name, object=obj.name,
                      mesh={"vertices": len(mesh.vertices), "edges": len(mesh.edges),
                            "polygons": len(mesh.polygons)},
                      camera_basis={"right": list(right), "up": list(up),
                                    "back_toward_camera": list(direction)},
                      depth_range={"near_projection": near_projection,
                                   "far_projection": far_projection,
                                   "span": span,
                                   "near_vertex_indices": [index for index, value in enumerate(projections)
                                                           if abs(value - near_projection) <= 1e-9],
                                   "far_vertex_indices": [index for index, value in enumerate(projections)
                                                          if abs(value - far_projection) <= 1e-9]},
                      vertex_reference_samples=samples,
                      world_bounds=_depth_world_bounds(obj), blockers=sorted(set(blockers)),
                      limitations=["Range is relative to this base Mesh and request only",
                                   "The future renderer must separately prove visible-fragment interpolation",
                                   "No Camera, shader, image or file was created"])
    except (ValueError, TypeError, KeyError, OverflowError, RuntimeError) as exc:
        report["errors"].append(str(exc))
    return report

