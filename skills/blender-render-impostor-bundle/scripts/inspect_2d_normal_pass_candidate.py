"""Read-only Blender candidate and flat-face reference probe for a normal-pass request."""
from __future__ import annotations

import hashlib
import json
import math

import bpy


def _normal_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _normal_source_payload(scene, obj):
    mesh = obj.data
    return {"scene": scene.name, "frame": [scene.frame_current, scene.frame_subframe],
            "unit": [scene.unit_settings.system, scene.unit_settings.scale_length],
            "object": {"name": obj.name, "mesh": mesh.name,
                       "matrix_world": [list(row) for row in obj.matrix_world],
                       "hide_render": obj.hide_render},
            "mesh": {"vertices": [list(vertex.co) for vertex in mesh.vertices],
                     "edges": [list(edge.vertices) for edge in mesh.edges],
                     "polygons": [{"vertices": list(face.vertices),
                                   "normal": list(face.normal),
                                   "use_smooth": face.use_smooth}
                                  for face in mesh.polygons]}}


def _normal_world_bounds(obj):
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


def inspect_2d_normal_pass_candidate(request, preflight):
    report = {"schema": "gameassetai.2d-normal-pass-candidate.v1", "status": "error",
              "errors": [], "blockers": [], "render_authorized": False,
              "destination_rechecked": False}
    try:
        if (request.get("schema") != SCHEMA or preflight.get("schema") != SCHEMA
                or preflight.get("ready_for_blender_inspection") is not True
                or preflight.get("errors") != []):
            raise ValueError("A successful normal-pass request preflight is required")
        request_hash = _normal_hash(request)
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
        normal_matrix = obj.matrix_world.to_3x3().inverted().transposed()
        samples = []
        for face in mesh.polygons[:64]:
            world = (normal_matrix @ face.normal).normalized()
            components = [float(world.dot(axis)) for axis in (right, up, direction)]
            encoded = [max(0, min(255, round((value * 0.5 + 0.5) * 255)))
                       for value in components]
            samples.append({"polygon_index": face.index, "use_smooth": face.use_smooth,
                            "world_face_normal": list(world),
                            "camera_basis_reference": components,
                            "encoded_rgb_reference": encoded})
        source = _normal_source_payload(scene, obj)
        setup = {"view": request["view"], "normal": request["normal"],
                 "style": request["style"], "blender_version": bpy.app.version_string}
        report.update(status="blocked" if blockers else "candidate_for_review",
                      request_sha256=request_hash, source_fingerprint=_normal_hash(source),
                      setup_fingerprint=_normal_hash(setup),
                      output_fingerprint=_normal_hash(request["output"]),
                      scene=scene.name, object=obj.name,
                      mesh={"vertices": len(mesh.vertices), "edges": len(mesh.edges),
                            "polygons": len(mesh.polygons),
                            "smooth_polygons": sum(1 for face in mesh.polygons if face.use_smooth)},
                      camera_basis={"right": list(right), "up": list(up),
                                    "back_toward_camera": list(direction)},
                      flat_face_reference_samples=samples,
                      world_bounds=_normal_world_bounds(obj), blockers=sorted(set(blockers)),
                      limitations=["Reference samples use polygon normals and are exact only for flat faces",
                                   "The future renderer must separately prove interpolated shading normals",
                                   "No Camera, shader, image or file was created"])
    except (ValueError, TypeError, KeyError, OverflowError, RuntimeError) as exc:
        report["errors"].append(str(exc))
    return report
