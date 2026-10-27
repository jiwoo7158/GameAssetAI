"""Read-only Blender-side review of an already validated explicit static FBX request.

Load inspect_static_export_context first. This cannot authorize export or validate a
destination; it binds one request digest to current Blender Object/Scene observations.
"""
import bpy
import hashlib
import json
import math


def _static_fbx_json_value(value):
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Nonfinite export source value")
        return value
    try:
        return [_static_fbx_json_value(item) for item in value]
    except TypeError:
        return str(value)


def _static_fbx_source_fingerprint(scene, obj):
    """Hash export-relevant reported state without evaluating or mutating the graph."""
    mesh = obj.data
    materials = []
    for slot in obj.material_slots:
        material = slot.material
        if material is None:
            materials.append(None)
            continue
        entry = {"name": material.name, "diffuse_color": list(material.diffuse_color),
                 "metallic": material.metallic, "roughness": material.roughness,
                 "use_nodes": material.use_nodes, "nodes": [], "links": []}
        if material.use_nodes and material.node_tree:
            nodes = list(material.node_tree.nodes)
            index = {node: position for position, node in enumerate(nodes)}
            for node in nodes:
                inputs = []
                for socket in node.inputs:
                    value = getattr(socket, "default_value", None)
                    inputs.append({"identifier": socket.identifier,
                                   "linked": socket.is_linked,
                                   "value": _static_fbx_json_value(value)})
                entry["nodes"].append({"type": node.bl_idname, "inputs": inputs})
            entry["links"] = sorted((index[link.from_node], link.from_socket.identifier,
                                     index[link.to_node], link.to_socket.identifier)
                                    for link in material.node_tree.links)
        materials.append(entry)
    attributes = []
    for attribute in mesh.attributes:
        values = []
        for item in attribute.data:
            for key in ("value", "vector", "color", "color_srgb", "uv"):
                if hasattr(item, key):
                    values.append(_static_fbx_json_value(getattr(item, key)))
                    break
            else:
                values.append(None)
        attributes.append({"name": attribute.name, "data_type": attribute.data_type,
                           "domain": attribute.domain, "values": values})
    payload = {
        "scene": scene.name,
        "unit": [scene.unit_settings.system, scene.unit_settings.scale_length],
        "frame": [scene.frame_current, scene.frame_subframe],
        "object": {"name": obj.name, "data": mesh.name,
                   "location": list(obj.location), "scale": list(obj.scale),
                   "rotation_mode": obj.rotation_mode,
                   "rotation_euler": list(obj.rotation_euler),
                   "rotation_quaternion": list(obj.rotation_quaternion),
                   "rotation_axis_angle": list(obj.rotation_axis_angle),
                   "matrix_world": [list(row) for row in obj.matrix_world]},
        "mesh": {"vertices": [list(v.co) for v in mesh.vertices],
                 "edges": [list(edge.vertices) for edge in mesh.edges],
                 "polygons": [{"vertices": list(face.vertices),
                                "material_index": face.material_index,
                                "use_smooth": face.use_smooth}
                               for face in mesh.polygons],
                 "uvs": [{"name": layer.name,
                           "active_render": layer.active_render,
                           "values": [list(item.uv) for item in layer.data]}
                          for layer in mesh.uv_layers],
                 "attributes": attributes},
        "materials": materials,
        "context": {"active_scene": bpy.context.scene.name,
                    "mode": bpy.context.mode,
                    "active_object": (bpy.context.view_layer.objects.active.name
                                      if bpy.context.view_layer.objects.active else None),
                    "selected": sorted(item.name for item in bpy.context.selected_objects)},
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def inspect_static_fbx_candidate(request, request_preflight):
    report = {"schema": "gameassetai.static-fbx-candidate.v1", "status": "error",
              "errors": [], "blockers": [], "export_authorized": False,
              "destination_rechecked": False, "sidecars_verified": False}
    try:
        if not isinstance(request, dict) or not isinstance(request_preflight, dict):
            raise ValueError("Request and offline preflight must be objects")
        if (request.get("schema") != "gameassetai.static-fbx-request.v1"
                or request_preflight.get("schema") != request["schema"]
                or request_preflight.get("ready_for_blender_inspection") is not True
                or request_preflight.get("errors") != []):
            raise ValueError("A successful offline request preflight is required")
        canonical = json.dumps(request, sort_keys=True, ensure_ascii=True,
                               separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if request_preflight.get("request_sha256") != digest:
            raise ValueError("Request changed since offline preflight")
        scene_name = request.get("scene_name")
        object_name = request.get("object_name")
        if not isinstance(scene_name, str) or not isinstance(object_name, str):
            raise ValueError("Exact Scene and Object names required")
        context = inspect_static_export_context(object_name, scene_name=scene_name,
                                                requested_format="FBX")
        if context["status"] != "inspected":
            raise ValueError("Blender context inspection refused: " + "; ".join(context["errors"]))
        capabilities = context["exporter_capabilities"]["FBX"]
        if not capabilities["available"]:
            raise ValueError("FBX exporter RNA unavailable")
        blockers = list(context["dependencies"])
        operator_poll = bpy.ops.export_scene.fbx.poll()
        if not operator_poll:
            blockers.append("fbx_operator_poll_failed")
        if bpy.context.mode != "OBJECT":
            blockers.append("object_mode_required")
        if bpy.context.scene.name != scene_name:
            blockers.append("requested_scene_not_active")
        for key in ("axis_forward", "axis_up"):
            if request.get(key) not in capabilities["axis_identifiers"][key]:
                blockers.append(key + "_unavailable")
        forward = request.get("axis_forward")
        up = request.get("axis_up")
        if isinstance(forward, str) and isinstance(up, str) and forward.lstrip("-") == up.lstrip("-"):
            blockers.append("axes_not_perpendicular")
        if request.get("apply_scale_options") not in capabilities["apply_scale_options_identifiers"]:
            blockers.append("apply_scale_options_unavailable")
        scale = request.get("global_scale")
        low, high = capabilities["global_scale_hard_range"]
        if (isinstance(scale, bool) or not isinstance(scale, (int, float))
                or not math.isfinite(float(scale)) or not low <= scale <= high):
            blockers.append("scale_outside_current_rna")
        for key in ("apply_unit_scale", "use_space_transform", "bake_space_transform",
                    "use_mesh_modifiers"):
            if not isinstance(request.get(key), bool):
                blockers.append(key + "_not_boolean")
        if request.get("path_mode") not in {"AUTO", "ABSOLUTE", "RELATIVE", "MATCH", "STRIP"}:
            blockers.append("path_mode_unsupported")
        if request.get("overwrite") is not False:
            blockers.append("overwrite_not_false")
        scene = bpy.data.scenes[scene_name]
        obj = scene.objects[object_name]
        for slot in obj.material_slots:
            material = slot.material
            if material and material.use_nodes and material.node_tree:
                if any(node.type in {"TEX_IMAGE", "GROUP"} for node in material.node_tree.nodes):
                    blockers.append("material_texture_or_group_unresolved")
                    break
        report.update(status="blocked" if blockers else "candidate_for_review",
                      request_sha256=digest, scene=scene_name, object=object_name,
                      source_fingerprint=_static_fbx_source_fingerprint(scene, obj),
                      fbx_operator_poll=operator_poll,
                      blockers=sorted(set(blockers)),
                      mesh=context["mesh"],
                      limitations=["No destination recheck or export authorization",
                                   "Material node scan is not exhaustive sidecar proof",
                                   "Current Blender state must be rechecked before writing"])
    except (ValueError, TypeError, OverflowError, KeyError, RuntimeError) as exc:
        report["errors"].append(str(exc))
    return report

