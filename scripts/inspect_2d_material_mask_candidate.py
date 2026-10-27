"""Read-only Blender inspection for one validated material-slot mask request."""
from __future__ import annotations

import hashlib
import json
import math

import bpy


def _mask_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _mask_source_payload(scene, obj):
    mesh = obj.data
    return {"scene": scene.name, "frame": [scene.frame_current, scene.frame_subframe],
            "unit": [scene.unit_settings.system, scene.unit_settings.scale_length],
            "object": {"name": obj.name, "mesh": mesh.name,
                       "matrix_world": [list(row) for row in obj.matrix_world],
                       "hide_render": obj.hide_render},
            "mesh": {"vertices": [list(vertex.co) for vertex in mesh.vertices],
                     "edges": [list(edge.vertices) for edge in mesh.edges],
                     "polygons": [{"vertices": list(face.vertices),
                                   "material_index": face.material_index}
                                  for face in mesh.polygons]},
            "material_slots": [slot.material.name if slot.material else None
                               for slot in obj.material_slots]}


def _mask_world_bounds(obj):
    vector = __import__("mathutils").Vector
    points = [obj.matrix_world @ vector(corner) for corner in obj.bound_box]
    values = [[float(axis) for axis in point] for point in points]
    if not all(math.isfinite(axis) for point in values for axis in point):
        raise ValueError("Object world bounds are nonfinite")
    minimum = [min(point[axis] for point in values) for axis in range(3)]
    maximum = [max(point[axis] for point in values) for axis in range(3)]
    return {"minimum": minimum, "maximum": maximum,
            "center": [(a + b) / 2.0 for a, b in zip(minimum, maximum)],
            "dimensions": [b - a for a, b in zip(minimum, maximum)]}


def inspect_2d_material_mask_candidate(request, preflight):
    report = {"schema": "gameassetai.2d-material-mask-candidate.v1", "status": "error",
              "errors": [], "blockers": [], "render_authorized": False,
              "destination_rechecked": False}
    try:
        if (not isinstance(request, dict) or not isinstance(preflight, dict)
                or request.get("schema") != SCHEMA or preflight.get("schema") != SCHEMA
                or preflight.get("ready_for_blender_inspection") is not True
                or preflight.get("errors") != []):
            raise ValueError("A successful material-mask request preflight is required")
        request_hash = _mask_hash(request)
        if preflight.get("request_sha256") != request_hash:
            raise ValueError("Request changed since offline preflight")
        scene = bpy.data.scenes.get(request["scene_name"])
        obj = scene.objects.get(request["object_name"]) if scene else None
        if obj is None:
            raise ValueError("Requested Scene/Object was not found")
        if obj.type != "MESH" or obj.data.is_editmode:
            raise ValueError("Requested Object must be an Object-mode Mesh")

        blockers = []
        mesh = obj.data
        if not mesh.vertices or not mesh.polygons:
            blockers.append("non_renderable_empty_mesh")
        if obj.hide_render:
            blockers.append("object_hidden_for_render")
        if obj.parent:
            blockers.append("parent_dependency_unsupported")
        if obj.constraints:
            blockers.append("object_constraints_unsupported")
        if obj.modifiers:
            blockers.append("modifiers_unsupported")
        if obj.animation_data or mesh.animation_data:
            blockers.append("animation_unsupported")
        if mesh.shape_keys:
            blockers.append("shape_keys_unsupported")
        if obj.library or mesh.library:
            blockers.append("linked_library_data_unsupported")
        slot_index = request["mask"]["material_slot_index"]
        if slot_index >= len(obj.material_slots):
            blockers.append("material_slot_index_out_of_range")
        elif obj.material_slots[slot_index].material is None:
            blockers.append("target_material_slot_is_empty")
        assigned = sum(1 for face in mesh.polygons if face.material_index == slot_index)
        if assigned == 0:
            blockers.append("target_material_slot_has_no_faces")
        invalid_faces = sum(1 for face in mesh.polygons
                            if face.material_index < 0 or face.material_index >= len(obj.material_slots))
        if invalid_faces:
            blockers.append("face_material_index_out_of_range")

        source = _mask_source_payload(scene, obj)
        setup = {"view": request["view"], "mask": request["mask"],
                 "style": request["style"], "blender_version": bpy.app.version_string}
        report.update(status="blocked" if blockers else "candidate_for_review",
                      request_sha256=request_hash,
                      source_fingerprint=_mask_hash(source),
                      setup_fingerprint=_mask_hash(setup),
                      output_fingerprint=_mask_hash(request["output"]),
                      scene=scene.name, object=obj.name,
                      mesh={"vertices": len(mesh.vertices), "edges": len(mesh.edges),
                            "polygons": len(mesh.polygons),
                            "material_slots": len(obj.material_slots)},
                      material_slot={"index": slot_index,
                                     "name": (obj.material_slots[slot_index].material.name
                                              if slot_index < len(obj.material_slots)
                                              and obj.material_slots[slot_index].material else None),
                                     "assigned_polygons": assigned},
                      world_bounds=_mask_world_bounds(obj), blockers=sorted(set(blockers)),
                      limitations=["Base Mesh only; modifiers, animation and Shape Keys are refused",
                                   "Material appearance is ignored; only exact face slot assignment is used",
                                   "No Camera, material, image or file was created"])
    except (ValueError, TypeError, KeyError, OverflowError, RuntimeError) as exc:
        report["errors"].append(str(exc))
    return report
