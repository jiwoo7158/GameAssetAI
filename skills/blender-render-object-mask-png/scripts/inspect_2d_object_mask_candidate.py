"""Read-only Blender inspection for one explicit static Object visibility mask."""
from __future__ import annotations

import hashlib
import json
import math

import bpy


def _object_mask_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _object_mask_item_payload(obj):
    mesh = obj.data
    return {"name": obj.name, "mesh": mesh.name,
            "matrix_world": [list(row) for row in obj.matrix_world],
            "hide_render": obj.hide_render,
            "vertices": [list(vertex.co) for vertex in mesh.vertices],
            "edges": [list(edge.vertices) for edge in mesh.edges],
            "polygons": [list(face.vertices) for face in mesh.polygons]}


def _object_mask_source_payload(scene, target, occluders):
    return {"scene": scene.name, "frame": [scene.frame_current, scene.frame_subframe],
            "unit": [scene.unit_settings.system, scene.unit_settings.scale_length],
            "target": _object_mask_item_payload(target),
            "occluders": [_object_mask_item_payload(obj) for obj in occluders]}


def _object_mask_bounds(objects):
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


def _object_mask_blockers(obj, role):
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


def inspect_2d_object_mask_candidate(request, preflight):
    report = {"schema": "gameassetai.2d-object-mask-candidate.v1", "status": "error",
              "errors": [], "blockers": [], "render_authorized": False,
              "destination_rechecked": False}
    try:
        if (not isinstance(request, dict) or not isinstance(preflight, dict)
                or request.get("schema") != SCHEMA or preflight.get("schema") != SCHEMA
                or preflight.get("ready_for_blender_inspection") is not True
                or preflight.get("errors") != []):
            raise ValueError("A successful Object-mask request preflight is required")
        request_hash = _object_mask_hash(request)
        if preflight.get("request_sha256") != request_hash:
            raise ValueError("Request changed since offline preflight")
        scene = bpy.data.scenes.get(request["scene_name"])
        if scene is None:
            raise ValueError("Requested Scene not found")
        target = scene.objects.get(request["target_object_name"])
        if target is None:
            raise ValueError("Requested target Object not found in Scene")
        occluders = []
        for name in request["occluder_object_names"]:
            obj = scene.objects.get(name)
            if obj is None:
                raise ValueError("Requested occluder Object not found in Scene: " + name)
            occluders.append(obj)
        blockers = _object_mask_blockers(target, "target")
        for obj in occluders:
            blockers.extend(_object_mask_blockers(obj, "occluder"))
        objects = [target, *occluders]
        source = _object_mask_source_payload(scene, target, occluders)
        setup = {"view": request["view"], "mask": request["mask"],
                 "style": request["style"], "blender_version": bpy.app.version_string}
        report.update(status="blocked" if blockers else "candidate_for_review",
                      request_sha256=request_hash,
                      source_fingerprint=_object_mask_hash(source),
                      setup_fingerprint=_object_mask_hash(setup),
                      output_fingerprint=_object_mask_hash(request["output"]),
                      scene=scene.name, target_object=target.name,
                      occluder_objects=[obj.name for obj in occluders],
                      objects=[{"name": obj.name, "role": "target" if obj == target else "occluder",
                                "vertices": len(obj.data.vertices) if obj.type == "MESH" else None,
                                "polygons": len(obj.data.polygons) if obj.type == "MESH" else None}
                               for obj in objects],
                      world_bounds=_object_mask_bounds(objects), blockers=sorted(set(blockers)),
                      limitations=["Only the exact target and explicit occluder list participate",
                                   "Base static Meshes only; evaluated geometry is refused",
                                   "No Camera, material, Scene or file was created"])
    except (ValueError, TypeError, KeyError, OverflowError, RuntimeError) as exc:
        report["errors"].append(str(exc))
    return report
