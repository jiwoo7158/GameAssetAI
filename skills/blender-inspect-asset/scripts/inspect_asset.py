"""Execute inside Blender via MCP. All public operations are read-only."""
from __future__ import annotations

import json
import math
import bpy


def _animation(owner):
    data = getattr(owner, "animation_data", None)
    if data is None:
        return None
    slot = getattr(data, "action_slot", None)
    return {
        "action": data.action.name if data.action else None,
        "slot": getattr(slot, "identifier", None),
        "nla_tracks": [{"name": track.name, "mute": track.mute,
            "strips": [{"name": strip.name, "type": strip.type,
                        "action": strip.action.name if getattr(strip, "action", None) else None,
                        "frame_start": float(strip.frame_start), "frame_end": float(strip.frame_end)}
                       for strip in track.strips]} for track in data.nla_tracks],
    }


def _mesh(mesh):
    if mesh.is_editmode:
        return {"status": "unverified", "reason": "Edit-mode data is not flushed or mode-switched"}
    mesh.calc_loop_triangles()  # Refresh tessellation cache, not mesh topology.
    return {
        "status": "ok", "datablock": mesh.name, "users": mesh.users,
        "vertices": len(mesh.vertices), "edges": len(mesh.edges),
        "polygons": len(mesh.polygons), "triangles": len(mesh.loop_triangles),
        "uv_layers": [layer.name for layer in mesh.uv_layers],
        "shape_keys": [key.name for key in mesh.shape_keys.key_blocks] if mesh.shape_keys else [],
        "shape_key_animation": _animation(mesh.shape_keys) if mesh.shape_keys else None,
    }


def _material(material):
    tree = material.node_tree
    return {"name": material.name, "users": material.users,
            "use_nodes": material.use_nodes,
            "node_types": sorted(node.bl_idname for node in tree.nodes) if tree else [],
            "images": sorted({node.image.name for node in tree.nodes
                              if node.type == "TEX_IMAGE" and node.image}) if tree else []}


def _object(obj):
    data = obj.data
    result = {
        "name": obj.name, "type": obj.type, "data": data.name if data else None,
        "parent": obj.parent.name if obj.parent else None,
        "location": list(obj.location), "rotation_mode": obj.rotation_mode,
        "scale": list(obj.scale), "matrix_world": [list(row) for row in obj.matrix_world],
        "material_slots": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "modifiers": [{"name": mod.name, "type": mod.type,
                       "show_viewport": mod.show_viewport, "show_render": mod.show_render,
                       "object": mod.object.name if getattr(mod, "object", None) else None}
                      for mod in obj.modifiers],
        "constraints": [{"name": c.name, "type": c.type,
                         "target": c.target.name if getattr(c, "target", None) else None}
                        for c in obj.constraints],
        "object_animation": _animation(obj), "data_animation": _animation(data) if data else None,
    }
    if obj.type == "MESH":
        result["base_mesh"] = _mesh(data)
    elif obj.type == "ARMATURE":
        if getattr(data, "is_editmode", None) is not False:
            result["armature"] = {"status": "unverified", "datablock": data.name,
                                  "reason": "Rest bones withheld while edit-mode state is not verified"}
            return result
        result["armature"] = {
            "status": "ok", "datablock": data.name, "users": data.users,
            "bones": [{"name": bone.name, "parent": bone.parent.name if bone.parent else None,
                       "use_deform": bone.use_deform} for bone in data.bones],
        }
    return result


def inspect_scene(scene_name=None, object_names=None, scope="scene"):
    """No operators, selection changes, mode changes, or writes to user data."""
    report = {"schema": "gameassetai.inspection.v1", "status": "error", "errors": []}
    if scope not in ("scene", "selected"):
        report["errors"].append("scope must be scene or selected")
        return report
    if scene_name is not None and (not isinstance(scene_name, str) or not scene_name):
        report["errors"].append("scene_name must be a nonempty string or None")
        return report
    scene = bpy.context.scene if scene_name is None else bpy.data.scenes.get(scene_name)
    if scene is None:
        report["errors"].append(f"Scene not found: {scene_name}")
        return report
    if object_names is not None:
        if scope != "scene" or not isinstance(object_names, (list, tuple)) or not object_names:
            report["errors"].append("Explicit names require a nonempty list and scene scope")
            return report
        if any(not isinstance(name, str) or not name for name in object_names):
            report["errors"].append("Object names must be nonempty strings")
            return report
        missing = sorted({name for name in object_names if scene.objects.get(name) is None})
        if missing:
            report["errors"].append(f"Objects not found in scene: {missing}")
            return report
        targets = [scene.objects[name] for name in sorted(set(object_names))]
    elif scope == "selected":
        if scene != bpy.context.scene:
            report["errors"].append("Selection scope requires the current scene")
            return report
        targets = sorted(bpy.context.selected_objects, key=lambda o: o.name)
        if not targets:
            report["errors"].append("No objects selected; scene scope was not substituted")
            return report
    else:
        targets = sorted(scene.objects, key=lambda o: o.name)

    report.update({"blender_version": bpy.app.version_string, "scene": scene.name,
                   "scope": "named" if object_names is not None else scope,
                   "targets": [o.name for o in targets], "object_count": len(targets),
                   "objects": [], "materials": [], "file_actions": []})
    referenced_materials = {}
    for obj in targets:
        try:
            report["objects"].append(_object(obj))
            for slot in obj.material_slots:
                if slot.material:
                    referenced_materials[slot.material.name] = slot.material
        except Exception as exc:
            report["errors"].append(f"Object {obj.name}: {type(exc).__name__}: {exc}")
    for name, material in sorted(referenced_materials.items()):
        try:
            report["materials"].append(_material(material))
        except Exception as exc:
            report["errors"].append(f"Material {name}: {type(exc).__name__}: {exc}")
    for action in sorted(bpy.data.actions, key=lambda a: a.name):
        try:
            report["file_actions"].append({
                "name": action.name, "users": action.users,
                "frame_range": list(action.frame_range),
                "layered": getattr(action, "is_action_layered", None),
                "slots": [{"identifier": slot.identifier,
                           "target_id_type": getattr(slot, "target_id_type", None)}
                          for slot in getattr(action, "slots", ())],
            })
        except Exception as exc:
            report["errors"].append(f"Action {action.name}: {type(exc).__name__}: {exc}")
    withheld = 0
    def finite_json(value):
        nonlocal withheld
        if isinstance(value, float) and not math.isfinite(value):
            withheld += 1
            return None
        if isinstance(value, dict):
            return {key: finite_json(item) for key, item in value.items()}
        if isinstance(value, list):
            return [finite_json(item) for item in value]
        return value
    report = finite_json(report)
    if withheld:
        report["errors"].append(f"Nonfinite numerical fields withheld as null: {withheld}")
    report["status"] = "partial" if report["errors"] else "ok"
    return report
