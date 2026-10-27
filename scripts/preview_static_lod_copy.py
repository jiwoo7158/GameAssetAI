"""Transient Blender preview for an independent-copy static LOD request."""
from __future__ import annotations

import hashlib
import json
import math
import uuid

import bpy
from mathutils import Vector

from validate_static_lod_copy_request import validate_static_lod_copy_request


SCHEMA = "gameassetai.static-lod-copy-preview.v1"


def _sha256(value):
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=True,
                           separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _finite(values):
    return all(math.isfinite(float(value)) for value in values)


def _dependencies(obj):
    found = []
    mesh = obj.data
    if obj.parent is not None: found.append("parent")
    if obj.modifiers: found.append("modifiers")
    if obj.constraints: found.append("constraints")
    if mesh.shape_keys is not None: found.append("shape_keys")
    if obj.vertex_groups: found.append("vertex_groups")
    if obj.animation_data is not None or mesh.animation_data is not None:
        found.append("animation")
    if obj.library or obj.override_library or mesh.library or mesh.override_library:
        found.append("linked_or_override_data")
    if mesh.users != 1: found.append("shared_mesh_data")
    if len(mesh.color_attributes): found.append("color_attributes")
    uv_names = {layer.name for layer in mesh.uv_layers}
    builtin_attributes = {"position", "sharp_face", "sharp_edge", "material_index"}
    custom = sorted(attribute.name for attribute in mesh.attributes
                    if not attribute.name.startswith(".")
                    and attribute.name not in uv_names
                    and attribute.name not in builtin_attributes)
    if custom: found.append("custom_attributes:" + ",".join(custom))
    return found


def _facts(obj):
    mesh = obj.data
    vertices = [[float(value) for value in vertex.co] for vertex in mesh.vertices]
    polygons = [{"vertices": list(polygon.vertices),
                 "material_index": int(polygon.material_index)} for polygon in mesh.polygons]
    if not vertices or not polygons or not _finite(v for point in vertices for v in point):
        raise ValueError("source must have nonempty finite base geometry")
    matrix = [[float(value) for value in row] for row in obj.matrix_world]
    if not _finite(v for row in matrix for v in row):
        raise ValueError("source has a nonfinite world matrix")
    determinant = float(obj.matrix_world.to_3x3().determinant())
    if not math.isfinite(determinant) or determinant == 0.0:
        raise ValueError("source must have a finite nonsingular world transform")
    world = [list(obj.matrix_world @ Vector(point)) for point in vertices]
    low = [min(point[axis] for point in world) for axis in range(3)]
    high = [max(point[axis] for point in world) for axis in range(3)]
    uv_layers = [{"name": layer.name,
                  "values": [[float(value) for value in item.uv] for item in layer.data]}
                 for layer in mesh.uv_layers]
    if not _finite(value for layer in uv_layers for pair in layer["values"] for value in pair):
        raise ValueError("source has nonfinite UV data")
    return {"object_name": obj.name, "mesh_name": mesh.name,
            "vertex_count": len(vertices), "edge_count": len(mesh.edges),
            "polygon_count": len(polygons),
            "triangle_count": sum(max(0, len(item["vertices"]) - 2) for item in polygons),
            "world_matrix": matrix, "world_determinant": determinant,
            "world_bounds": {"minimum": low, "maximum": high,
                             "center": [(a + b) / 2.0 for a, b in zip(low, high)],
                             "half_extents": [(b - a) / 2.0 for a, b in zip(low, high)]},
            "material_slots": [material.name if material else None for material in mesh.materials],
            "uv_layers": uv_layers, "local_vertices": vertices, "polygons": polygons}


def _public(facts):
    public = {key: value for key, value in facts.items()
              if key not in ("local_vertices", "polygons", "uv_layers")}
    public["uv_layers"] = [{"name": item["name"], "value_count": len(item["values"])}
                           for item in facts["uv_layers"]]
    return public


def _restore_context(scene, active, selected, frame, subframe):
    bpy.context.window.scene = scene
    scene.frame_set(frame, subframe=subframe)
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in selected:
        if obj.name in scene.objects:
            obj.select_set(True)
    bpy.context.view_layer.objects.active = active if active and active.name in scene.objects else None


def preview_static_lod_copy(request, expected_request_sha256=None):
    """Evaluate Decimate on disposable independent IDs and remove them before returning."""
    report = {"schema": SCHEMA, "status": "error", "request_sha256": None,
              "source_fingerprint": None, "setup_fingerprint": None,
              "preview_fingerprint": None, "errors": [], "blockers": [],
              "review_items": [], "mutation_authorized": False,
              "persistent_output_created": False}
    temp_scene = temp_object = temp_mesh = None
    original_scene = bpy.context.scene
    original_active = bpy.context.view_layer.objects.active
    original_selected = list(bpy.context.selected_objects)
    original_frame = original_scene.frame_current
    original_subframe = original_scene.frame_subframe
    try:
        preflight = validate_static_lod_copy_request(request)
        report["request_sha256"] = preflight["request_sha256"]
        if preflight["status"] != "ready":
            report["errors"].extend(preflight["errors"]); return report
        if (expected_request_sha256 is not None
                and expected_request_sha256 != preflight["request_sha256"]):
            report["errors"].append("request fingerprint changed since review"); return report
        scene = bpy.data.scenes.get(request["scene_name"])
        if scene is None: raise ValueError("named Scene is missing")
        source = scene.objects.get(request["source_object_name"])
        if source is None or source.type != "MESH":
            raise ValueError("named source base-Mesh Object is missing from Scene")
        if bpy.context.mode != "OBJECT" or source.mode != "OBJECT" or source.data.is_editmode:
            raise ValueError("Object mode is required for the source Mesh")
        if bpy.data.objects.get(request["output_object_name"]) is not None:
            report["blockers"].append("output_object_name_already_exists")
        if bpy.data.meshes.get(request["output_mesh_name"]) is not None:
            report["blockers"].append("output_mesh_name_already_exists")
        dependencies = _dependencies(source)
        report["blockers"].extend(dependencies)
        source_before = _facts(source)
        if source_before["triangle_count"] <= 0:
            report["blockers"].append("source_has_no_base_triangles")
        source_binding = {"request_sha256": preflight["request_sha256"],
                          "scene_name": scene.name, "facts": source_before,
                          "dependencies": dependencies}
        report["source_fingerprint"] = _sha256(source_binding)
        setup = {"request_sha256": preflight["request_sha256"],
                 "source_fingerprint": report["source_fingerprint"],
                 "method": "DECIMATE_COLLAPSE", "ratio": float(request["operation"]["ratio"]),
                 "triangulate": False, "blender_version": bpy.app.version_string,
                 "intended_output_object_name": request["output_object_name"],
                 "intended_output_mesh_name": request["output_mesh_name"]}
        report["setup_fingerprint"] = _sha256(setup)
        report.update({"status": "candidate_for_review", "scene_name": scene.name,
                       "source": _public(source_before), "dependencies": dependencies,
                       "intended_output": {"object_name": request["output_object_name"],
                                           "mesh_name": request["output_mesh_name"]}})
        if report["blockers"]:
            return report

        token = uuid.uuid4().hex
        temp_scene = bpy.data.scenes.new(".gameassetai-lod-preview-" + token)
        temp_object = source.copy(); temp_object.name = ".gameassetai-lod-preview-object-" + token
        temp_mesh = source.data.copy(); temp_mesh.name = ".gameassetai-lod-preview-mesh-" + token
        temp_object.data = temp_mesh
        temp_object.matrix_world = source.matrix_world.copy()
        temp_scene.collection.objects.link(temp_object)
        bpy.context.window.scene = temp_scene
        bpy.context.view_layer.objects.active = temp_object
        temp_object.select_set(True)
        modifier = temp_object.modifiers.new("GameAssetAI LOD Preview", "DECIMATE")
        modifier.decimate_type = "COLLAPSE"
        modifier.ratio = float(request["operation"]["ratio"])
        if hasattr(modifier, "use_collapse_triangulate"):
            modifier.use_collapse_triangulate = False
        result = bpy.ops.object.modifier_apply(modifier=modifier.name)
        if result != {"FINISHED"}:
            raise RuntimeError("Blender did not apply the temporary Decimate modifier")
        preview = _facts(temp_object)
        source_after = _facts(source)
        if _sha256(source_after) != _sha256(source_before):
            report["blockers"].append("source_changed_during_preview")
        if preview["triangle_count"] <= 0:
            report["blockers"].append("preview_has_no_base_triangles")
        if preview["triangle_count"] >= source_before["triangle_count"]:
            report["blockers"].append("preview_did_not_reduce_triangles")
        if preview["world_matrix"] != source_before["world_matrix"]:
            report["blockers"].append("preview_world_matrix_differs")
        if preview["material_slots"] != source_before["material_slots"]:
            report["blockers"].append("preview_material_slots_differ")
        source_uv = [item["name"] for item in source_before["uv_layers"]]
        preview_uv = [item["name"] for item in preview["uv_layers"]]
        if preview_uv != source_uv:
            report["blockers"].append("preview_uv_layers_differ")
        source_bounds = source_before["world_bounds"]
        preview_bounds = preview["world_bounds"]
        relation = {"actual_triangle_ratio": preview["triangle_count"] /
                                               source_before["triangle_count"],
                    "bounds_center_delta": [b - a for a, b in zip(
                        source_bounds["center"], preview_bounds["center"])],
                    "bounds_half_extent_delta": [b - a for a, b in zip(
                        source_bounds["half_extents"], preview_bounds["half_extents"])],
                    "world_matrix_matches": preview["world_matrix"] == source_before["world_matrix"],
                    "material_slots_match": preview["material_slots"] == source_before["material_slots"],
                    "uv_layer_names_match": preview_uv == source_uv}
        preview_public = _public(preview)
        preview_public["object_name"] = request["output_object_name"]
        preview_public["mesh_name"] = request["output_mesh_name"]
        preview_binding = {key: value for key, value in preview.items()
                           if key not in ("object_name", "mesh_name")}
        report["preview"] = preview_public
        report["relation_to_source"] = relation
        report["review_items"].append("bounds_changes_require_visual_review")
        report["preview_fingerprint"] = _sha256({"setup_fingerprint": report["setup_fingerprint"],
                                                  "preview": preview_binding,
                                                  "relation_to_source": relation})
        report["limitations"] = [
            "The preview uses disposable Object/Mesh/Scene IDs and creates no requested output",
            "Triangle and bounds evidence does not certify silhouette, UV or shading quality",
            "No persistent apply, rollback, Unity LODGroup or screen threshold is authorized"]
    except (ValueError, TypeError, RuntimeError, OverflowError, ZeroDivisionError) as exc:
        report["errors"].append(str(exc))
        report["status"] = "error"
    finally:
        if bpy.context.window.scene != original_scene:
            bpy.context.window.scene = original_scene
        if temp_object is not None and temp_object.name in bpy.data.objects:
            bpy.data.objects.remove(temp_object, do_unlink=True)
        if temp_mesh is not None and temp_mesh.name in bpy.data.meshes and temp_mesh.users == 0:
            bpy.data.meshes.remove(temp_mesh)
        if temp_scene is not None and temp_scene.name in bpy.data.scenes:
            bpy.data.scenes.remove(temp_scene)
        _restore_context(original_scene, original_active, original_selected,
                         original_frame, original_subframe)
    return report
