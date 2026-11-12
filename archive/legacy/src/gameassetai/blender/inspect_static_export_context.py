"""Read-only static export context; load inspect_asset and transform inspector first."""
import bpy


_EXPORT_OPERATORS = {"FBX": ("export_scene", "fbx"),
                     "GLTF": ("export_scene", "gltf")}


def inspect_static_export_context(object_name, *, scene_name=None, requested_format=None):
    report = {"schema": "gameassetai.static-export-context.v1", "status": "error",
              "errors": [], "export_authorized": False, "engine_ready": None,
              "export_path": None, "basis": "base_and_reported_state_no_dependency_refresh"}
    try:
        if requested_format is not None and requested_format not in _EXPORT_OPERATORS:
            raise ValueError("Explicit requested_format must be FBX or GLTF when supplied")
        inspection = inspect_static_transform(object_name, scene_name=scene_name)
        if inspection["status"] != "ok":
            raise ValueError("Transform inspection refused: " + "; ".join(inspection["errors"]))
        scene = bpy.data.scenes[inspection["scene"]]
        obj = scene.objects[inspection["object"]]
        mesh = obj.data
        operators = {}
        for label, (module, name) in _EXPORT_OPERATORS.items():
            try:
                props = getattr(getattr(bpy.ops, module), name).get_rna_type().properties
                entry = {"available": True, "operator": f"bpy.ops.{module}.{name}",
                         "parameter_names": [p.identifier for p in props]}
                if label == "FBX":
                    entry["axis_identifiers"] = {
                        key: [item.identifier for item in props[key].enum_items]
                        for key in ("axis_forward", "axis_up")}
                    entry["apply_scale_options_identifiers"] = [
                        item.identifier for item in props["apply_scale_options"].enum_items]
                    scale = props["global_scale"]
                    entry["global_scale_hard_range"] = [scale.hard_min, scale.hard_max]
                operators[label] = entry
            except (AttributeError, RuntimeError, TypeError) as exc:
                operators[label] = {"available": False, "operator": f"bpy.ops.{module}.{name}",
                                    "lookup_error": type(exc).__name__ + ": " + str(exc)}
        dependencies = []
        if obj.parent is not None:
            dependencies.append("parent")
        if obj.children:
            dependencies.append("children")
        if obj.modifiers:
            dependencies.append("modifiers")
        if obj.constraints:
            dependencies.append("constraints")
        if obj.vertex_groups:
            dependencies.append("vertex_groups")
        if mesh.shape_keys:
            dependencies.append("shape_keys")
        if obj.animation_data or mesh.animation_data:
            dependencies.append("animation_data")
        if mesh.users > 1:
            dependencies.append("shared_mesh")
        if obj.library or mesh.library or obj.override_library or mesh.override_library:
            dependencies.append("linked_or_override_data")
        if any(mod.type == "ARMATURE" for mod in obj.modifiers):
            dependencies.append("armature_modifier")
        if not mesh.polygons:
            dependencies.append("no_polygon_surface")
        selected = bool(obj.select_get(view_layer=bpy.context.view_layer)) if scene == bpy.context.scene else None
        report.update(status="inspected", object=obj.name, scene=scene.name,
                      requested_format=requested_format,
                      requested_operator_available=(operators[requested_format]["available"]
                                                   if requested_format is not None else None),
                      exporter_capabilities=operators,
                      mesh={"name": mesh.name, "vertices": len(mesh.vertices),
                            "faces": len(mesh.polygons),
                            "base_triangles": sum(max(0, len(face.vertices) - 2) for face in mesh.polygons),
                            "uv_layers": [layer.name for layer in mesh.uv_layers],
                            "material_slots": [slot.material.name if slot.material else None
                                               for slot in obj.material_slots]},
                      transform=inspection,
                      unit_settings={"system": scene.unit_settings.system,
                                     "scale_length": scene.unit_settings.scale_length},
                      selection_observation={"selected_in_active_view_layer": selected,
                                             "selection_was_changed": False},
                      dependencies=dependencies,
                      unresolved_contract=["engine_import_behavior", "target_format_policy",
                                           "export_destination", "axis_conversion_policy",
                                           "unit_conversion_policy", "selection_scope",
                                           "material_texture_policy"],
                      limitations=["Operator RNA presence is not a successful export or import test",
                                   "Base triangles are not evaluated or engine-imported topology",
                                   "No file write, selection change, graph refresh or readiness certificate"])
    except (ValueError, TypeError, RuntimeError) as exc:
        report["errors"].append(str(exc))
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
