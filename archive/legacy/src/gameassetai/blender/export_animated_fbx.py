"""Preview and stage/publish one explicit skinned animated FBX without source mutation."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import uuid

import bpy
from mathutils import Vector


ANIMATED_PLAN_SCHEMA = "gameassetai.animated-fbx-export-plan.v1"
ANIMATED_RESULT_SCHEMA = "gameassetai.animated-fbx-export-result.v1"


def _animated_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _animation_state(obj):
    data = obj.animation_data
    if data is None:
        return {"exists": False, "action": None, "slot": None, "nla": [], "drivers": []}
    return {"exists": True, "action": data.action.name if data.action else None,
            "slot": getattr(getattr(data, "action_slot", None), "identifier", None),
            "nla": [(track.name, strip.name, strip.action.name if strip.action else None)
                    for track in data.nla_tracks for strip in track.strips],
            "drivers": [(curve.data_path, curve.array_index) for curve in data.drivers]}


def _mesh_snapshot(obj):
    mesh = obj.data
    groups = []
    for vertex in mesh.vertices:
        groups.append([(group.group, float(group.weight)) for group in vertex.groups])
    return {"object_matrix": [[float(value) for value in row] for row in obj.matrix_world],
            "vertices": [[float(value) for value in vertex.co] for vertex in mesh.vertices],
            "polygons": [list(poly.vertices) for poly in mesh.polygons],
            "uv": [[[float(value) for value in loop.uv] for loop in layer.data]
                   for layer in mesh.uv_layers],
            "groups": groups,
            "group_names": [group.name for group in obj.vertex_groups],
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
            "modifiers": [(mod.name, mod.type, getattr(getattr(mod, "object", None), "name", None))
                          for mod in obj.modifiers],
            "parent": obj.parent.name if obj.parent else None}


def _rig_snapshot(obj):
    return {"object_matrix": [[float(value) for value in row] for row in obj.matrix_world],
            "bones": [{"name": bone.name, "parent": bone.parent.name if bone.parent else None,
                       "use_deform": bool(bone.use_deform),
                       "matrix_local": [[float(value) for value in row]
                                        for row in bone.matrix_local]}
                      for bone in obj.data.bones],
            "constraints": [constraint.type for constraint in obj.constraints],
            "pose_constraints": {bone.name: [constraint.type for constraint in bone.constraints]
                                 for bone in obj.pose.bones if bone.constraints}}


def _source_snapshot(mesh, rig, action):
    return {"mesh": _mesh_snapshot(mesh), "rig": _rig_snapshot(rig),
            "action": action_content_snapshot(action),
            "mesh_animation": _animation_state(mesh),
            "rig_animation": _animation_state(rig)}


def _source_fingerprint(mesh, rig, action):
    return _animated_digest(_source_snapshot(mesh, rig, action))


def _pose_signature(scene, rig, mesh, bones, frames):
    result = {}
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        positions = {}
        for name in bones:
            pose = rig.pose.bones[name]
            positions[name] = {
                "head": [float(value) for value in (rig.matrix_world @ pose.head)],
                "tail": [float(value) for value in (rig.matrix_world @ pose.tail)],
            }
        evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
        temporary = evaluated.to_mesh()
        try:
            points = [mesh.matrix_world @ vertex.co for vertex in temporary.vertices]
            low = [min(point[index] for point in points) for index in range(3)]
            high = [max(point[index] for point in points) for index in range(3)]
            stride = max(1, len(points) // 64)
            sample_indices = list(range(0, len(points), stride))[:64]
            vertex_samples = {str(index): [float(value) for value in points[index]]
                              for index in sample_indices}
        finally:
            evaluated.to_mesh_clear()
        result[str(frame)] = {"bones": positions, "bounds_min": low, "bounds_max": high,
                              "vertex_samples": vertex_samples}
    return result


def preview_animated_fbx_export(request):
    report = {"schema": ANIMATED_PLAN_SCHEMA, "status": "error", "errors": [],
              "blockers": [], "authorization": False}
    preflight = validate_animated_fbx_request(request)
    if not preflight["ready_for_blender_inspection"]:
        report["errors"].extend(preflight["errors"])
        return report
    scene = bpy.data.scenes.get(request["scene_name"])
    mesh = bpy.data.objects.get(request["mesh_object_name"])
    rig = bpy.data.objects.get(request["armature_object_name"])
    action = bpy.data.actions.get(request["action_name"])
    if scene is None:
        report["blockers"].append("scene_not_found")
    if mesh is None or mesh.type != "MESH" or (scene and scene.objects.get(mesh.name) is None):
        report["blockers"].append("mesh_not_found_in_scene")
    if rig is None or rig.type != "ARMATURE" or (scene and scene.objects.get(rig.name) is None):
        report["blockers"].append("armature_not_found_in_scene")
    if action is None:
        report["blockers"].append("action_not_found")
    if report["blockers"]:
        return report
    if any(value.library or value.override_library for value in (mesh, mesh.data, rig, rig.data)):
        report["blockers"].append("linked_or_overridden_data")
    if action.library or action.override_library:
        report["blockers"].append("linked_or_overridden_action")
    if mesh.parent not in (None, rig):
        report["blockers"].append("unsupported_mesh_parent")
    if rig.parent is not None:
        report["blockers"].append("unsupported_armature_parent")
    modifiers = [mod for mod in mesh.modifiers if mod.type == "ARMATURE"]
    if len(modifiers) != 1 or modifiers[0].object != rig:
        report["blockers"].append("requires_exactly_one_matching_armature_modifier")
    if any(mod.type != "ARMATURE" for mod in mesh.modifiers):
        report["blockers"].append("unsupported_non_armature_modifier")
    if mesh.data.shape_keys is not None or not mesh.vertex_groups or not mesh.data.uv_layers:
        report["blockers"].append("requires_weights_uv_and_no_shape_keys")
    if rig.constraints or any(bone.constraints for bone in rig.pose.bones):
        report["blockers"].append("constraints_not_supported")
    if _animation_state(rig)["drivers"] or _animation_state(mesh)["drivers"]:
        report["blockers"].append("drivers_not_supported")
    slots = list(getattr(action, "slots", ()))
    if (len(slots) != 1 or getattr(slots[0], "target_id_type", None) != "OBJECT"
            or slots[0].identifier != request["action_slot_identifier"]):
        report["blockers"].append("action_slot_mismatch")
    curves = list(_curves(action))
    if not curves or any(not curve.data_path.startswith('pose.bones["') for curve in curves):
        report["blockers"].append("action_requires_pose_bone_channels_only")
    start, end = request["clip"]["frame_start"], request["clip"]["frame_end"]
    action_start, action_end = map(float, action.frame_range)
    if start < action_start or end > action_end:
        report["blockers"].append("clip_outside_action_range")
    bones = request["rig"]["validation_bones"]
    if any(rig.pose.bones.get(name) is None for name in bones):
        report["blockers"].append("validation_bone_missing")
    if report["blockers"]:
        return report
    source = _source_fingerprint(mesh, rig, action)
    candidate = {"request_sha256": preflight["request_sha256"],
                 "source_fingerprint": source,
                 "mesh_vertices": len(mesh.data.vertices),
                 "mesh_polygons": len(mesh.data.polygons),
                 "uv_layers": len(mesh.data.uv_layers),
                 "vertex_groups": len(mesh.vertex_groups),
                 "bone_count": len(rig.data.bones),
                 "deform_bone_count": sum(bone.use_deform for bone in rig.data.bones),
                 "action_curve_count": len(curves), "frame_start": start, "frame_end": end,
                 "fps": request["clip"]["fps"],
                 "duration_seconds": (end - start) / request["clip"]["fps"],
                 "selected_action_bound_on_source": (_animation_state(rig)["action"] == action.name),
                 "loop": False, "root_motion": "IN_PLACE"}
    report.update(status="candidate_for_review", request=json.loads(json.dumps(request)),
                  candidate=candidate)
    return report


def _remove_temporary(scene, mesh_obj, rig_obj, mesh_data, rig_data):
    for obj in (mesh_obj, rig_obj):
        if obj is not None and bpy.data.objects.get(obj.name) == obj:
            if obj.animation_data:
                obj.animation_data_clear()
            bpy.data.objects.remove(obj, do_unlink=True)
    if mesh_data is not None and bpy.data.meshes.get(mesh_data.name) == mesh_data and not mesh_data.users:
        bpy.data.meshes.remove(mesh_data)
    if rig_data is not None and bpy.data.armatures.get(rig_data.name) == rig_data and not rig_data.users:
        bpy.data.armatures.remove(rig_data)
    if scene is not None and bpy.data.scenes.get(scene.name) == scene:
        bpy.data.scenes.remove(scene)


def export_animated_fbx_staged(plan, authorization=False):
    result = {"schema": ANIMATED_RESULT_SCHEMA, "status": "error", "errors": [],
              "target_created": False, "stage_cleaned": False, "source_preserved": False}
    if authorization is not True:
        result["errors"].append("Explicit authorization=true is required")
        return result
    if (not isinstance(plan, dict) or plan.get("schema") != ANIMATED_PLAN_SCHEMA
            or plan.get("status") != "candidate_for_review"):
        result["errors"].append("A candidate_for_review plan is required")
        return result
    request, candidate = plan.get("request"), plan.get("candidate")
    fresh = preview_animated_fbx_export(request) if isinstance(request, dict) else None
    if (not fresh or fresh.get("status") != "candidate_for_review"
            or fresh.get("candidate") != candidate):
        result["errors"].append("Animated FBX preview is stale")
        return result
    source_scene = bpy.data.scenes[request["scene_name"]]
    source_mesh = bpy.data.objects[request["mesh_object_name"]]
    source_rig = bpy.data.objects[request["armature_object_name"]]
    source_action = bpy.data.actions[request["action_name"]]
    source_fingerprint = candidate["source_fingerprint"]
    source_snapshot = _source_snapshot(source_mesh, source_rig, source_action)
    source_refs = _action_references(source_action)
    selected_before = list(bpy.context.selected_objects)
    active_before = bpy.context.view_layer.objects.active
    window_scene = bpy.context.window.scene if bpy.context.window else bpy.context.scene
    window_frame = (window_scene.frame_current, window_scene.frame_subframe)
    target = Path(request["target"]["target_file"])
    stage = target.parent / ("." + target.stem + ".gameassetai-" + uuid.uuid4().hex + ".stage.fbx")
    temporary_scene = temporary_mesh = temporary_rig = mesh_data = rig_data = None
    published = False
    try:
        meta = Path(str(target) + ".meta")
        if target.exists() or _export_path_is_link(target) or meta.exists() or _export_path_is_link(meta):
            raise FileExistsError("Target FBX or .meta appeared before export")
        temporary_scene = bpy.data.scenes.new("GAA_AnimatedExport_" + uuid.uuid4().hex)
        rig_data = source_rig.data.copy()
        mesh_data = source_mesh.data.copy()
        temporary_rig = source_rig.copy(); temporary_rig.data = rig_data
        temporary_mesh = source_mesh.copy(); temporary_mesh.data = mesh_data
        temporary_rig.name = source_rig.name + "__GAA_EXPORT"
        temporary_mesh.name = source_mesh.name + "__GAA_EXPORT"
        temporary_rig.animation_data_clear(); temporary_mesh.animation_data_clear()
        temporary_scene.collection.objects.link(temporary_rig)
        temporary_scene.collection.objects.link(temporary_mesh)
        for modifier in temporary_mesh.modifiers:
            if modifier.type == "ARMATURE":
                modifier.object = temporary_rig
        if source_mesh.parent == source_rig:
            temporary_mesh.parent = temporary_rig
        temporary_rig.animation_data_create().action = source_action
        temporary_rig.animation_data.action_slot = source_action.slots[0]
        clip = request["clip"]
        temporary_scene.frame_start = clip["frame_start"]
        temporary_scene.frame_end = clip["frame_end"]
        temporary_scene.render.fps = clip["fps"]
        review_frames = sorted({clip["frame_start"], (clip["frame_start"] + clip["frame_end"]) // 2,
                                clip["frame_end"]})
        if bpy.context.window:
            bpy.context.window.scene = temporary_scene
        pose_signature = _pose_signature(temporary_scene, temporary_rig, temporary_mesh,
                                         request["rig"]["validation_bones"], review_frames)
        animation_data = temporary_rig.animation_data
        track = animation_data.nla_tracks.new()
        track.name = "GAA_SELECTED_ACTION_EXPORT"
        strip = track.strips.new(source_action.name, clip["frame_start"], source_action)
        strip.name = source_action.name
        strip.action_frame_start = clip["frame_start"]
        strip.action_frame_end = clip["frame_end"]
        strip.frame_start = clip["frame_start"]
        strip.frame_end = clip["frame_end"]
        animation_data.action = None
        transform, geometry, materials = request["transform"], request["geometry"], request["materials"]
        rig, animation = request["rig"], request["animation"]
        with bpy.context.temp_override(scene=temporary_scene, view_layer=temporary_scene.view_layers[0],
                                       active_object=temporary_rig,
                                       selected_objects=[temporary_mesh, temporary_rig],
                                       selected_editable_objects=[temporary_mesh, temporary_rig]):
            temporary_mesh.select_set(True)
            temporary_rig.select_set(True)
            bpy.context.view_layer.objects.active = temporary_rig
            outcome = bpy.ops.export_scene.fbx(
                filepath=str(stage), check_existing=False, use_selection=True,
                object_types={"ARMATURE", "MESH"}, use_mesh_modifiers=geometry["use_mesh_modifiers"],
                path_mode=materials["path_mode"], embed_textures=False,
                axis_forward=transform["axis_forward"], axis_up=transform["axis_up"],
                global_scale=transform["global_scale"], apply_unit_scale=transform["apply_unit_scale"],
                apply_scale_options=transform["apply_scale_options"],
                use_space_transform=transform["use_space_transform"],
                bake_space_transform=transform["bake_space_transform"],
                add_leaf_bones=rig["add_leaf_bones"],
                use_armature_deform_only=rig["deform_bones_only"],
                armature_nodetype=rig["armature_nodetype"],
                bake_anim=True, bake_anim_use_all_bones=True,
                bake_anim_use_nla_strips=True, bake_anim_use_all_actions=False,
                bake_anim_force_startend_keying=True, bake_anim_step=animation["bake_step"],
                bake_anim_simplify_factor=animation["simplify_factor"], use_custom_props=True)
        if "FINISHED" not in outcome or not stage.is_file() or _export_path_is_link(stage):
            raise RuntimeError("Blender did not create the animated FBX stage")
        content = stage.read_bytes()
        if not content.startswith(b"Kaydara FBX Binary") or len(content) < 1024:
            raise RuntimeError("Staged output is not a nonempty binary FBX")
        if target.exists() or _export_path_is_link(target) or meta.exists() or _export_path_is_link(meta):
            raise FileExistsError("Target FBX or .meta appeared before publication")
        publication = promote_export_artifact(stage, target)
        published = True
        if not target.is_file() or target.read_bytes() != content or publication["overwrite_performed"]:
            raise RuntimeError("Published animated FBX verification failed")
        stage.unlink()
        result.update({"status": "created", "target_created": True, "stage_cleaned": True,
                       "target_file": str(target), "bytes": len(content),
                       "sha256": hashlib.sha256(content).hexdigest(),
                       "request_sha256": candidate["request_sha256"],
                       "source_fingerprint": source_fingerprint,
                       "mesh_object": source_mesh.name, "armature_object": source_rig.name,
                       "action": source_action.name, "action_slot_identifier": request["action_slot_identifier"],
                       "frame_start": clip["frame_start"], "frame_end": clip["frame_end"],
                       "fps": clip["fps"], "duration_seconds": candidate["duration_seconds"],
                       "loop": False, "root_motion": "IN_PLACE",
                       "validation_bones": request["rig"]["validation_bones"],
                       "pose_signature": pose_signature, "source_preserved": True})
        result["receipt_sha256"] = _animated_digest(result)
    except Exception as exc:
        result["errors"].append(str(exc))
        if not published and stage.is_file() and not _export_path_is_link(stage):
            stage.unlink()
            result["stage_cleaned"] = True
    finally:
        _remove_temporary(temporary_scene, temporary_mesh, temporary_rig, mesh_data, rig_data)
        if bpy.context.window and window_scene and bpy.data.scenes.get(window_scene.name):
            bpy.context.window.scene = window_scene
        if bpy.data.scenes.get(window_scene.name):
            window_scene.frame_set(window_frame[0], subframe=window_frame[1])
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in selected_before:
            if bpy.data.objects.get(obj.name):
                obj.select_set(True)
        if active_before and bpy.data.objects.get(active_before.name):
            bpy.context.view_layer.objects.active = active_before
        after_snapshot = _source_snapshot(source_mesh, source_rig, source_action)
        references_preserved = _action_references(source_action) == source_refs
        if after_snapshot != source_snapshot or not references_preserved:
            result["status"] = "error"
            result["source_preserved"] = False
            difference = _first_difference(source_snapshot, after_snapshot)
            result["errors"].append(
                "Source preservation verification failed"
                + (f" at {difference}" if difference else " in Action references"))
    return result
# Retained bounded Blender capability; product support remains evidence-scoped.
