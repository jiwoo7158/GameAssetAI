"""Read-only Blender candidate inspection for a validated static 3D-to-2D request.

Load ``validate_2d_static_render_request.py`` first. This module never creates render
setup data, authorizes a write, or rechecks/publishes the destination.
"""
from __future__ import annotations

import hashlib
import json
import math

import bpy


def _render_json_value(value):
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Nonfinite Blender source value")
        return value
    try:
        return [_render_json_value(item) for item in value]
    except TypeError:
        return str(value)


def _render_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _render_material(material):
    if material is None:
        return None
    result = {"name": material.name, "diffuse_color": list(material.diffuse_color),
              "metallic": material.metallic, "roughness": material.roughness,
              "use_nodes": material.use_nodes, "nodes": [], "links": []}
    tree = material.node_tree if material.use_nodes else None
    if tree:
        nodes = list(tree.nodes)
        indexes = {node: index for index, node in enumerate(nodes)}
        for node in nodes:
            result["nodes"].append({
                "type": node.bl_idname,
                "inputs": [{"identifier": socket.identifier,
                            "linked": socket.is_linked,
                            "value": _render_json_value(getattr(socket, "default_value", None))}
                           for socket in node.inputs],
            })
        result["links"] = sorted((indexes[link.from_node], link.from_socket.identifier,
                                  indexes[link.to_node], link.to_socket.identifier)
                                 for link in tree.links)
    return result


def _render_source_payload(scene, obj):
    mesh = obj.data
    return {
        "scene": scene.name,
        "frame": [scene.frame_current, scene.frame_subframe],
        "unit": [scene.unit_settings.system, scene.unit_settings.scale_length],
        "object": {"name": obj.name, "data": mesh.name,
                   "matrix_world": [list(row) for row in obj.matrix_world],
                   "visible_render": not obj.hide_render},
        "mesh": {"vertices": [list(vertex.co) for vertex in mesh.vertices],
                 "edges": [list(edge.vertices) for edge in mesh.edges],
                 "polygons": [{"vertices": list(face.vertices),
                               "material_index": face.material_index,
                               "use_smooth": face.use_smooth}
                              for face in mesh.polygons],
                 "uvs": [{"name": layer.name, "active_render": layer.active_render,
                          "values": [list(item.uv) for item in layer.data]}
                         for layer in mesh.uv_layers]},
        "materials": [_render_material(slot.material) for slot in obj.material_slots],
    }


def _render_world_bounds(obj):
    points = [obj.matrix_world @ __import__("mathutils").Vector(corner)
              for corner in obj.bound_box]
    values = [[float(axis) for axis in point] for point in points]
    if not all(math.isfinite(axis) for point in values for axis in point):
        raise ValueError("Object world bounds are nonfinite")
    minimum = [min(point[axis] for point in values) for axis in range(3)]
    maximum = [max(point[axis] for point in values) for axis in range(3)]
    return {"minimum": minimum, "maximum": maximum,
            "center": [(a + b) / 2.0 for a, b in zip(minimum, maximum)],
            "dimensions": [b - a for a, b in zip(minimum, maximum)]}


def inspect_2d_static_render_candidate(request, request_preflight):
    report = {"schema": "gameassetai.2d-static-render-candidate.v1",
              "status": "error", "errors": [], "blockers": [],
              "render_authorized": False, "destination_rechecked": False}
    try:
        if not isinstance(request, dict) or not isinstance(request_preflight, dict):
            raise ValueError("Request and preflight must be objects")
        if (request.get("schema") != SCHEMA
                or request_preflight.get("schema") != SCHEMA
                or request_preflight.get("ready_for_blender_inspection") is not True
                or request_preflight.get("errors") != []):
            raise ValueError("A successful static 2D request preflight is required")
        request_hash = _render_hash(request)
        if request_preflight.get("request_sha256") != request_hash:
            raise ValueError("Request changed since offline preflight")
        scene = bpy.data.scenes.get(request.get("scene_name"))
        if scene is None:
            raise ValueError("Requested Scene not found")
        obj = scene.objects.get(request.get("object_name"))
        if obj is None:
            raise ValueError("Requested Object not found in Scene")
        if obj.type != "MESH":
            raise ValueError("Requested Object must be a Mesh")
        if obj.data.is_editmode:
            raise ValueError("Edit Mode Mesh inspection is refused")

        blockers = []
        if not obj.data.vertices or not obj.data.polygons:
            blockers.append("non_renderable_empty_mesh")
        if obj.hide_render:
            blockers.append("object_hidden_for_render")
        if obj.parent:
            blockers.append("parent_dependency_unsupported")
        if obj.constraints:
            blockers.append("object_constraints_unsupported")
        if obj.modifiers:
            blockers.append("modifiers_unsupported")
        if obj.animation_data or obj.data.animation_data:
            blockers.append("animation_unsupported_by_static_candidate")
        if obj.data.shape_keys:
            blockers.append("shape_keys_unsupported")
        if obj.library or obj.data.library:
            blockers.append("linked_library_data_unsupported")
        for slot in obj.material_slots:
            material = slot.material
            if material and material.use_nodes and material.node_tree:
                if any(node.type in {"TEX_IMAGE", "GROUP"} for node in material.node_tree.nodes):
                    blockers.append("material_texture_or_group_unsupported")
                    break

        style = request["style"]
        lighting = request["lighting"]
        if style["mode"] != "PIXEL":
            blockers.append("style_mode_not_implemented")
        if (style["palette_mode"] == "FIXED"
              and any(color[3] != 1 for color in style["palette"])):
            blockers.append("fixed_palette_requires_opaque_colors")
        if style["anti_aliasing"] != "DISABLED" or style["nearest_neighbor"] is not True:
            blockers.append("first_pixel_sampling_policy_required")
        if lighting["mode"] != "OWNED_NEUTRAL":
            blockers.append("source_lighting_copy_not_implemented")
        if request["output"]["color_mode"] != "RGBA" or request["output"]["color_depth"] != 8:
            blockers.append("first_output_format_requires_rgba8")
        outline_mode = style.get("outline_mode", "NONE")
        if outline_mode not in {"NONE", "OUTER"}:
            blockers.append("outline_mode_not_implemented")
        shading_mode = style.get("shading_mode", "NONE")
        if shading_mode not in {"NONE", "VALUE_STEPS"}:
            blockers.append("shading_mode_not_implemented")

        source = _render_source_payload(scene, obj)
        setup = {"profile": request["profile"], "view": request["view"],
                 "lighting": lighting, "style": style,
                 "blender_version": bpy.app.version_string}
        output = request["output"]
        report.update(
            status="blocked" if blockers else "candidate_for_review",
            request_sha256=request_hash,
            source_fingerprint=_render_hash(source),
            setup_fingerprint=_render_hash(setup),
            output_fingerprint=_render_hash(output),
            scene=scene.name, object=obj.name,
            mesh={"vertices": len(obj.data.vertices), "edges": len(obj.data.edges),
                  "polygons": len(obj.data.polygons),
                  "uv_layers": [layer.name for layer in obj.data.uv_layers]},
            world_bounds=_render_world_bounds(obj),
            blockers=sorted(set(blockers)),
            supported_now={"style_mode": "PIXEL", "palette_modes": ["NONE", "AUTO", "FIXED"],
                           "lighting_mode": "OWNED_NEUTRAL",
                           "projection": "ORTHOGRAPHIC",
                           "outline_modes": ["NONE", "OUTER_1PX"],
                           "shading_modes": ["NONE", "VALUE_STEPS_2_TO_32"]},
            limitations=["No camera, light, material, compositor, image or file was created",
                         "No destination freshness recheck or render authorization",
                         "Fingerprint covers base Mesh/material state, not evaluated deformation"],
        )
    except (ValueError, TypeError, KeyError, OverflowError, RuntimeError) as exc:
        report["errors"].append(str(exc))
    return report
