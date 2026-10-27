"""Read-only Blender inspection for one explicit static Object color-ID pass."""
from __future__ import annotations

import hashlib
import json
import math

import bpy


def _object_id_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _object_id_item_payload(obj):
    mesh = obj.data
    return {"name": obj.name, "mesh": mesh.name,
            "matrix_world": [list(row) for row in obj.matrix_world],
            "hide_render": obj.hide_render,
            "vertices": [list(vertex.co) for vertex in mesh.vertices],
            "edges": [list(edge.vertices) for edge in mesh.edges],
            "polygons": [list(face.vertices) for face in mesh.polygons]}


def _object_id_source_payload(scene, objects):
    return {"scene": scene.name, "frame": [scene.frame_current, scene.frame_subframe],
            "unit": [scene.unit_settings.system, scene.unit_settings.scale_length],
            "objects": [_object_id_item_payload(obj) for obj in objects]}


def _object_id_bounds(objects):
    vector = __import__("mathutils").Vector
    points = [obj.matrix_world @ vector(corner) for obj in objects for corner in obj.bound_box]
    values = [[float(axis) for axis in point] for point in points]
    if not values or not all(math.isfinite(axis) for point in values for axis in point):
        raise ValueError("Object union bounds are empty or nonfinite")
    minimum = [min(point[axis] for point in values) for axis in range(3)]
    maximum = [max(point[axis] for point in values) for axis in range(3)]
    return {"minimum": minimum, "maximum": maximum,
            "center": [(a + b) / 2 for a, b in zip(minimum, maximum)],
            "dimensions": [b - a for a, b in zip(minimum, maximum)]}


def _object_id_blockers(obj, role):
    blockers = []
    prefix = role + ":" + obj.name + ":"
    if obj.type != "MESH":
        return [prefix + "not_mesh"]
    mesh = obj.data
    checks = ((not mesh.vertices or not mesh.polygons, "non_renderable_empty_mesh"),
              (obj.hide_render, "hidden_for_render"), (bool(obj.parent), "parent_unsupported"),
              (bool(obj.constraints), "constraints_unsupported"),
              (bool(obj.modifiers), "modifiers_unsupported"),
              (bool(obj.animation_data or mesh.animation_data), "animation_unsupported"),
              (bool(mesh.shape_keys), "shape_keys_unsupported"),
              (bool(obj.library or mesh.library), "linked_data_unsupported"),
              (mesh.is_editmode, "edit_mode_unsupported"))
    blockers.extend(prefix + name for condition, name in checks if condition)
    return blockers


def inspect_2d_object_id_candidate(request, preflight):
    report = {"schema": "gameassetai.2d-object-id-candidate.v1", "status": "error",
              "errors": [], "blockers": [], "render_authorized": False,
              "destination_rechecked": False}
    try:
        if (not isinstance(request, dict) or not isinstance(preflight, dict)
                or request.get("schema") != SCHEMA or preflight.get("schema") != SCHEMA
                or preflight.get("ready_for_blender_inspection") is not True
                or preflight.get("errors") != []):
            raise ValueError("A successful Object-ID request preflight is required")
        request_hash = _object_id_hash(request)
        if preflight.get("request_sha256") != request_hash:
            raise ValueError("Request changed since offline preflight")
        scene = bpy.data.scenes.get(request["scene_name"])
        if scene is None:
            raise ValueError("Requested Scene not found")
        objects = []
        for entry in request["objects"]:
            name = entry["object_name"]
            obj = scene.objects.get(name)
            if obj is None:
                raise ValueError("Requested ID Object not found in Scene: " + name)
            objects.append(obj)
        blockers = []
        for index, obj in enumerate(objects):
            blockers.extend(_object_id_blockers(obj, "id" + str(index)))
        source = _object_id_source_payload(scene, objects)
        setup = {"view": request["view"], "objects": request["objects"],
                 "style": request["style"], "blender_version": bpy.app.version_string}
        vector = __import__("mathutils").Vector
        direction, up = vector(request["view"]["direction"]), vector(request["view"]["up"])
        right = up.cross(direction)
        report.update(status="blocked" if blockers else "candidate_for_review",
                      request_sha256=request_hash,
                      source_fingerprint=_object_id_hash(source),
                      setup_fingerprint=_object_id_hash(setup),
                      output_fingerprint=_object_id_hash(request["output"]),
                      scene=scene.name,
                      camera_basis={"right": list(right), "up": list(up),
                                    "back_toward_camera": list(direction)},
                      objects=[{"name": obj.name,
                                "id_rgba": request["objects"][index]["id_rgba"],
                                "id_rgba8": [round(float(value) * 255)
                                             for value in request["objects"][index]["id_rgba"]],
                                "vertices": len(obj.data.vertices) if obj.type == "MESH" else None,
                                "polygons": len(obj.data.polygons) if obj.type == "MESH" else None}
                               for index, obj in enumerate(objects)],
                      world_bounds=_object_id_bounds(objects), blockers=sorted(set(blockers)),
                      limitations=["Only the exact ordered Object-ID list participates",
                                   "Base static Meshes only; evaluated geometry is refused",
                                   "No Camera, material, Scene or file was created"])
    except (ValueError, TypeError, KeyError, OverflowError, RuntimeError) as exc:
        report["errors"].append(str(exc))
    return report

