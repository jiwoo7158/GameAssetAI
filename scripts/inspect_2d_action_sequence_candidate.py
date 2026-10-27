"""Inspect one validated Action PNG-sequence candidate in an isolated temporary Scene."""
from __future__ import annotations

import hashlib
import json
import math
import re
import uuid

import bpy


CANDIDATE_SCHEMA = "gameassetai.2d-action-sequence-candidate.v1"
_POSE_PATH = re.compile(
    r'^pose\.bones\["((?:[^"\\]|\\.)*)"\]\.(location|rotation_euler|rotation_quaternion|rotation_axis_angle|scale)$')


def _hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _curves_with_slots(action):
    entries = [(curve, None) for curve in getattr(action, "fcurves", ())]
    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            for bag in getattr(strip, "channelbags", ()):
                slot = getattr(getattr(bag, "slot", None), "identifier", None)
                entries.extend((curve, slot) for curve in bag.fcurves)
    seen, result = set(), []
    for curve, slot in entries:
        pointer = curve.as_pointer()
        if pointer not in seen:
            seen.add(pointer)
            result.append((curve, slot))
    return result


def _rna_scalars(value, excluded=()):
    result = {}
    for prop in value.bl_rna.properties:
        if prop.identifier == "rna_type" or prop.identifier in excluded:
            continue
        if prop.type not in {"BOOLEAN", "INT", "FLOAT", "STRING", "ENUM"}:
            continue
        try:
            item = getattr(value, prop.identifier)
        except (AttributeError, TypeError, RuntimeError):
            continue
        if getattr(prop, "is_array", False):
            item = list(item)
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("Action or modifier contains non-finite settings")
        if isinstance(item, list) and any(isinstance(v, float) and not math.isfinite(v)
                                          for v in item):
            raise ValueError("Action or modifier contains non-finite settings")
        result[prop.identifier] = item
    return result


def _action_payload(action):
    curves = []
    for curve, slot in _curves_with_slots(action):
        curves.append({"slot": slot, "data_path": curve.data_path,
                       "array_index": curve.array_index,
                       "settings": _rna_scalars(curve, {"data_path", "array_index"}),
                       "keys": [{"co": [float(value) for value in point.co],
                                 "handle_left": [float(value) for value in point.handle_left],
                                 "handle_right": [float(value) for value in point.handle_right],
                                 "settings": _rna_scalars(
                                     point, {"co", "handle_left", "handle_right"})}
                                for point in curve.keyframe_points],
                       "modifiers": [{"type": modifier.type,
                                      "settings": _rna_scalars(modifier, {"type"})}
                                     for modifier in curve.modifiers]})
    return {"name": action.name,
            "slots": [[slot.identifier, getattr(slot, "target_id_type", None)]
                      for slot in getattr(action, "slots", ())],
            "curves": curves}


def _source_payload(mesh_obj, rig):
    mesh = mesh_obj.data
    group_names = {group.index: group.name for group in mesh_obj.vertex_groups}
    return {
        "mesh_object": mesh_obj.name,
        "mesh_matrix": [[float(value) for value in row] for row in mesh_obj.matrix_world],
        "vertices": [[float(value) for value in vertex.co] for vertex in mesh.vertices],
        "edges": [list(edge.vertices) for edge in mesh.edges],
        "polygons": [list(face.vertices) for face in mesh.polygons],
        "vertex_groups": sorted(group.name for group in mesh_obj.vertex_groups),
        "weights": [sorted((group_names[item.group], float(item.weight))
                           for item in vertex.groups) for vertex in mesh.vertices],
        "parent": mesh_obj.parent.name if mesh_obj.parent else None,
        "parent_inverse": [[float(value) for value in row]
                           for row in mesh_obj.matrix_parent_inverse],
        "modifiers": [{"name": modifier.name, "type": modifier.type,
                       "object": modifier.object.name if modifier.type == "ARMATURE"
                       and modifier.object else None,
                       "settings": _rna_scalars(modifier, {"name", "type", "object"})}
                      for modifier in mesh_obj.modifiers],
        "materials": [{"name": material.name,
                       "diffuse_color": [float(value) for value in material.diffuse_color],
                       "use_nodes": material.use_nodes,
                       "node_types": [node.bl_idname for node in material.node_tree.nodes]
                                     if material.use_nodes and material.node_tree else []}
                      for material in mesh.materials if material is not None],
        "armature": rig.name,
        "armature_matrix": [[float(value) for value in row] for row in rig.matrix_world],
        "bones": [{"name": bone.name, "parent": bone.parent.name if bone.parent else None,
                   "deform": bone.use_deform,
                   "head": [float(value) for value in bone.head_local],
                   "tail": [float(value) for value in bone.tail_local]}
                  for bone in rig.data.bones],
    }


def _bounds(points):
    if not points:
        raise ValueError("Evaluated Mesh contains no vertices")
    if any(not math.isfinite(float(value)) for point in points for value in point):
        raise ValueError("Evaluated Mesh contains non-finite coordinates")
    return {"minimum": [min(float(point[i]) for point in points) for i in range(3)],
            "maximum": [max(float(point[i]) for point in points) for i in range(3)]}


def inspect_2d_action_sequence_candidate(request, preflight):
    """Return evaluated union bounds and fingerprints without changing source data."""
    report = {"schema": CANDIDATE_SCHEMA, "status": "error", "errors": [],
              "blockers": [], "render_authorized": False}
    work_scene = work_rig = work_rig_data = work_mesh = work_mesh_data = None
    window = bpy.context.window
    original_scene = original_layer = None
    try:
        if (not isinstance(request, dict) or not isinstance(preflight, dict)
                or request.get("schema") != SCHEMA
                or preflight.get("schema") != SCHEMA
                or preflight.get("ready_for_blender_inspection") is not True
                or preflight.get("request_sha256") != _hash(request)
                or preflight.get("frame_plan_sha256") != _hash(preflight.get("frames"))):
            raise ValueError("A matching successful Action-sequence preflight is required")
        if window is None or bpy.context.mode != "OBJECT":
            raise ValueError("Candidate evaluation requires an Object-mode Blender window")
        template, animation = request["static_template"], request["animation"]
        scene = bpy.data.scenes.get(template["scene_name"])
        mesh_obj = scene.objects.get(template["object_name"]) if scene else None
        rig = scene.objects.get(animation["armature_name"]) if scene else None
        action = bpy.data.actions.get(animation["action_name"])
        if scene is None:
            raise ValueError("Requested Scene not found")
        if mesh_obj is None or mesh_obj.type != "MESH":
            raise ValueError("Requested Mesh Object not found in Scene")
        if rig is None or rig.type != "ARMATURE":
            raise ValueError("Requested Armature Object not found in Scene")
        if action is None:
            raise ValueError("Requested Action not found")

        blockers = []
        armature_modifiers = [modifier for modifier in mesh_obj.modifiers
                              if modifier.type == "ARMATURE"]
        if (len(mesh_obj.modifiers) != 1 or len(armature_modifiers) != 1
                or armature_modifiers[0].object != rig):
            blockers.append("exact_requested_armature_modifier_required")
        if mesh_obj.parent not in {None, rig}:
            blockers.append("mesh_parent_dependency_unsupported")
        if rig.parent is not None:
            blockers.append("armature_parent_dependency_unsupported")
        if mesh_obj.constraints or rig.constraints or any(bone.constraints for bone in rig.pose.bones):
            blockers.append("constraints_unsupported")
        if mesh_obj.data.shape_keys:
            blockers.append("shape_keys_unsupported")
        if (mesh_obj.library or mesh_obj.data.library or rig.library or rig.data.library
                or action.library):
            blockers.append("linked_library_data_unsupported")
        if ((mesh_obj.animation_data and mesh_obj.animation_data.drivers)
                or (rig.animation_data and rig.animation_data.drivers)
                or (rig.data.animation_data and rig.data.animation_data.drivers)):
            blockers.append("drivers_unsupported")
        deform_names = {bone.name for bone in rig.data.bones if bone.use_deform}
        if not deform_names.intersection(group.name for group in mesh_obj.vertex_groups):
            blockers.append("deform_vertex_group_required")

        slots = list(getattr(action, "slots", ()))
        identifiers = [slot.identifier for slot in slots]
        requested_slot = animation["slot_identifier"]
        if requested_slot is None and len(slots) > 1:
            blockers.append("slot_identifier_required_for_multi_slot_action")
        if requested_slot is not None and requested_slot not in identifiers:
            blockers.append("requested_action_slot_not_found")
        effective_slot = requested_slot if requested_slot is not None else (
            identifiers[0] if identifiers else None)
        applicable = [(curve, slot) for curve, slot in _curves_with_slots(action)
                      if effective_slot is None or slot in {None, effective_slot}]
        animated_bones = set()
        for curve, _ in applicable:
            match = _POSE_PATH.match(curve.data_path)
            if match is None:
                blockers.append("only_pose_transform_fcurves_supported")
                continue
            animated_bones.add(match.group(1).replace('\\"', '"').replace('\\\\', '\\'))
        if not applicable:
            blockers.append("selected_action_slot_has_no_fcurves")
        if animated_bones - set(rig.data.bones.keys()):
            blockers.append("action_references_missing_bones")
        if blockers:
            report.update(status="blocked", blockers=sorted(set(blockers)))
            return report

        source_before = _source_payload(mesh_obj, rig)
        action_before = _action_payload(action)
        original_scene, original_layer = window.scene, window.view_layer
        original_frame = (original_scene.frame_current, original_scene.frame_subframe)
        original_active = bpy.context.view_layer.objects.active
        original_selection = sorted(obj.name for obj in bpy.context.selected_objects)
        token = uuid.uuid4().hex
        work_scene = bpy.data.scenes.new("GAI_2DSequenceCandidate_" + token)
        work_rig_data = rig.data.copy()
        work_rig = rig.copy()
        work_rig.data = work_rig_data
        work_rig.animation_data_clear()
        work_mesh_data = mesh_obj.data.copy()
        work_mesh = mesh_obj.copy()
        work_mesh.data = work_mesh_data
        work_mesh.animation_data_clear()
        work_scene.collection.objects.link(work_rig)
        work_scene.collection.objects.link(work_mesh)
        if work_mesh.parent == rig:
            work_mesh.parent = work_rig
        for modifier in work_mesh.modifiers:
            if modifier.type == "ARMATURE":
                modifier.object = work_rig
        work_rig.animation_data_create()
        work_rig.animation_data.action = action
        if effective_slot is not None:
            work_rig.animation_data.action_slot = next(
                slot for slot in slots if slot.identifier == effective_slot)
        window.scene = work_scene
        direction = __import__("mathutils").Vector(template["view"]["direction"])
        up = __import__("mathutils").Vector(template["view"]["up"])
        right = up.cross(direction)
        per_frame, union_points, projected_points = [], [], []
        for planned in preflight["frames"]:
            frame = planned["source_frame"]
            work_scene.frame_set(frame)
            evaluated = work_mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
            evaluated_mesh = evaluated.to_mesh()
            try:
                points = [evaluated.matrix_world @ vertex.co for vertex in evaluated_mesh.vertices]
                union_points.extend(points)
                projected_points.extend((point.dot(right), point.dot(up), point.dot(direction))
                                        for point in points)
                per_frame.append({"source_frame": frame, "bounds": _bounds(points)})
            finally:
                evaluated.to_mesh_clear()
        evaluation = {"frames": per_frame, "union_bounds": _bounds(union_points),
                      "projected_union_bounds": _bounds(projected_points),
                      "anchor_world": [float(value) for value in work_mesh.matrix_world.translation],
                      "anchor_policy": request["framing"]["anchor_policy"],
                      "bounds_policy": request["framing"]["bounds_policy"]}
        report.update(status="candidate_for_review", blockers=[],
                      request_sha256=preflight["request_sha256"],
                      frame_plan_sha256=preflight["frame_plan_sha256"],
                      source_fingerprint=_hash(source_before),
                      action_fingerprint=_hash(action_before),
                      evaluation_fingerprint=_hash(evaluation),
                      scene=scene.name, mesh_object=mesh_obj.name, armature=rig.name,
                      action=action.name, slot_identifier=effective_slot,
                      frame_count=len(per_frame), evaluation=evaluation,
                      limitations=["Read-only isolated evaluation; no Camera, render or file output",
                                   "Only one Armature modifier and pose-transform F-Curves are supported"])
    except (ValueError, TypeError, KeyError, RuntimeError, OverflowError) as exc:
        report["errors"].append(str(exc))
    finally:
        if window is not None and original_scene is not None:
            window.scene, window.view_layer = original_scene, original_layer
            original_scene.frame_set(original_frame[0], subframe=original_frame[1])
            if original_active is not None and original_active.name in original_scene.objects:
                original_scene.view_layers[0].objects.active = original_active
            for obj in original_scene.objects:
                obj.select_set(obj.name in original_selection)
        if work_mesh is not None and bpy.data.objects.get(work_mesh.name) == work_mesh:
            bpy.data.objects.remove(work_mesh, do_unlink=True)
        if work_mesh_data is not None and work_mesh_data.users == 0:
            bpy.data.meshes.remove(work_mesh_data)
        if work_rig is not None and bpy.data.objects.get(work_rig.name) == work_rig:
            work_rig.animation_data_clear()
            bpy.data.objects.remove(work_rig, do_unlink=True)
        if work_rig_data is not None and work_rig_data.users == 0:
            bpy.data.armatures.remove(work_rig_data)
        if work_scene is not None and bpy.data.scenes.get(work_scene.name) == work_scene:
            bpy.data.scenes.remove(work_scene)
    if report["status"] == "candidate_for_review":
        if _source_payload(mesh_obj, rig) != source_before or _action_payload(action) != action_before:
            report["status"] = "error"
            report["errors"].append("Source Mesh, Armature or Action changed during evaluation")
    return report
