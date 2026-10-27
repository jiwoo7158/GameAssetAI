"""Guarded root-bone translation bake through owned temporary rig copies."""
from __future__ import annotations

import hashlib
import json
import math
import uuid

import bpy
from mathutils import Vector


ROOT_TRANSLATION_BAKE_SCHEMA = "gameassetai.root-translation-bake-request.v1"
_ROOT_TRANSLATION_KEYS = {
    "schema", "scene_name", "source_armature", "target_armature", "source_action",
    "target_action", "source_root_bone", "target_root_bone", "source_slot_identifier",
    "frame_start", "frame_end", "frame_step", "motion_policy", "translation_scale",
    "axis_mask", "preserve_source", "bind_result", "set_fake_user",
}
_OBJECT_TRANSFORMS = {"location", "rotation_euler", "rotation_quaternion",
                      "rotation_axis_angle", "scale", "delta_location",
                      "delta_rotation_euler", "delta_rotation_quaternion", "delta_scale"}


def _root_bake_digest(value):
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False,
                     sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _root_bake_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return int(value)


def _root_bake_object_identity(obj, tolerance=1e-6):
    return (obj.parent is None and obj.location.length <= tolerance
            and abs(obj.rotation_euler.x) <= tolerance
            and abs(obj.rotation_euler.y) <= tolerance
            and abs(obj.rotation_euler.z) <= tolerance
            and all(abs(float(value) - 1.0) <= tolerance for value in obj.scale))


def _root_bake_state(obj, bone_name):
    bone = obj.data.bones[bone_name]
    return {
        "object": _evaluated_root_source_snapshot(obj),
        "bone_matrix_local": tuple(tuple(float(v) for v in row) for row in bone.matrix_local),
        "bone_parent": bone.parent.name if bone.parent else None,
        "bone_inherit_scale": bone.inherit_scale,
    }


def preview_root_translation_bake(request):
    """Create a hash-bound root-translation plan without writes or frame changes."""
    report = {"schema": "gameassetai.root-translation-bake-plan.v1", "status": "error",
              "errors": [], "reviews": [], "authorization": False}
    if not isinstance(request, dict):
        report["errors"].append("Request must be an object")
        return report
    unknown = sorted(set(request) - _ROOT_TRANSLATION_KEYS)
    missing = sorted(_ROOT_TRANSLATION_KEYS - set(request))
    if unknown: report["errors"].append("Unknown request fields: " + ", ".join(unknown))
    if missing: report["errors"].append("Missing request fields: " + ", ".join(missing))
    if unknown or missing: return report
    if request["schema"] != ROOT_TRANSLATION_BAKE_SCHEMA:
        report["errors"].append("Unsupported request schema")
    for key in ("scene_name", "source_armature", "target_armature", "source_action",
                "target_action", "source_root_bone", "target_root_bone"):
        value = request[key]
        if not isinstance(value, str) or not value or value != value.strip():
            report["errors"].append(f"{key} must be an exact nonempty name")
    if request["source_armature"] == request["target_armature"]:
        report["errors"].append("Source and target Armatures must differ")
    if request["source_action"] == request["target_action"]:
        report["errors"].append("Source and target Action names must differ")
    slot_id = request["source_slot_identifier"]
    if slot_id is not None and (not isinstance(slot_id, str) or not slot_id):
        report["errors"].append("source_slot_identifier must be null or a nonempty identifier")
    for key, expected in (("preserve_source", True), ("bind_result", False),
                          ("set_fake_user", True)):
        if request[key] is not expected:
            report["errors"].append(f"This workflow requires {key}={str(expected).lower()}")
    policy = request["motion_policy"]
    if policy not in {"TRANSFER", "IN_PLACE"}:
        report["errors"].append("motion_policy must be TRANSFER or IN_PLACE")
    mask = request["axis_mask"]
    if not isinstance(mask, list) or len(mask) != 3 or any(type(v) is not bool for v in mask):
        report["errors"].append("axis_mask must be exactly three booleans for Armature XYZ")
    elif policy == "TRANSFER" and not any(mask):
        report["errors"].append("TRANSFER requires at least one enabled axis")
    elif policy == "IN_PLACE" and any(mask):
        report["errors"].append("IN_PLACE requires axis_mask=[false,false,false]")
    scale = request["translation_scale"]
    if isinstance(scale, bool) or not isinstance(scale, (int, float)) or not math.isfinite(float(scale)):
        report["errors"].append("translation_scale must be finite")
    elif not 0.0 < float(scale) <= 1000.0:
        report["errors"].append("translation_scale must be greater than 0 and at most 1000")
    elif policy == "IN_PLACE" and float(scale) != 1.0:
        report["errors"].append("IN_PLACE requires translation_scale=1")
    try:
        start = _root_bake_int(request["frame_start"], "frame_start")
        end = _root_bake_int(request["frame_end"], "frame_end")
        step = _root_bake_int(request["frame_step"], "frame_step")
    except ValueError as exc:
        report["errors"].append(str(exc)); return report
    if end < start: report["errors"].append("frame_end must be >= frame_start")
    if step != 1: report["errors"].append("This bounded workflow requires frame_step=1")
    if end - start > 10000: report["errors"].append("Bake range exceeds 10001 frames")
    if report["errors"]: return report

    scene = bpy.data.scenes.get(request["scene_name"])
    source = scene.objects.get(request["source_armature"]) if scene else None
    target = scene.objects.get(request["target_armature"]) if scene else None
    action = bpy.data.actions.get(request["source_action"])
    if scene is None: report["errors"].append("Named Scene not found")
    if source is None or source.type != "ARMATURE": report["errors"].append("Source Armature not found")
    if target is None or target.type != "ARMATURE": report["errors"].append("Target Armature not found")
    if action is None: report["errors"].append("Source Action not found")
    if bpy.data.actions.get(request["target_action"]) is not None:
        report["errors"].append("Target Action name already exists")
    if report["errors"]: return report
    source_bone = source.data.bones.get(request["source_root_bone"])
    target_bone = target.data.bones.get(request["target_root_bone"])
    if source_bone is None: report["errors"].append("Source root bone not found")
    if target_bone is None: report["errors"].append("Target root bone not found")
    if source_bone and source_bone.parent: report["errors"].append("Source root bone must be parentless")
    if target_bone and target_bone.parent: report["errors"].append("Target root bone must be parentless")
    for label, obj in (("Source", source), ("Target", target)):
        if not _root_bake_object_identity(obj):
            report["errors"].append(f"{label} Armature requires identity transform and no parent")
        if obj.constraints or any(pb.constraints for pb in obj.pose.bones):
            report["errors"].append(f"{label} constraints are not supported")
        if ((obj.animation_data and obj.animation_data.drivers)
                or (obj.data.animation_data and obj.data.animation_data.drivers)):
            report["errors"].append(f"{label} drivers are not supported")
    slots = list(getattr(action, "slots", ()))
    ids = [slot.identifier for slot in slots]
    if slot_id is None and len(slots) > 1: report["errors"].append("Source slot is required")
    if slot_id is not None and slot_id not in ids: report["errors"].append("Source slot not found")
    effective_slot = slot_id if slot_id is not None else (ids[0] if ids else None)
    applicable = [(curve, slot) for curve, slot in _curves_with_slots(action)
                  if effective_slot is None or slot in {None, effective_slot}]
    if any(curve.data_path in _OBJECT_TRANSFORMS for curve, _ in applicable):
        report["errors"].append("Object transform channels are not supported")
    roots = [curve for curve, _ in applicable
             if _decoded_bone(curve.data_path) == request["source_root_bone"]
             and curve.data_path.endswith(".location") and curve.array_index in {0, 1, 2}]
    if not roots: report["errors"].append("Source root has no location F-Curve")
    if report["errors"]: return report
    candidate = {
        "operation": "root_translation_only_unbound_bake", "frames": list(range(start, end + 1)),
        "frame_count": end - start + 1, "motion_policy": policy,
        "translation_scale": float(scale), "axis_mask": list(mask),
        "source_content_sha256": action_content_fingerprint(action),
        "source_state_sha256": _root_bake_digest(_root_bake_state(source, source_bone.name)),
        "target_state_sha256": _root_bake_digest(_root_bake_state(target, target_bone.name)),
        "request_sha256": _root_bake_digest(request), "source_slot_identifier": effective_slot,
    }
    report.update({"status": "candidate_for_review", "request": dict(request),
                   "candidate": candidate})
    report["reviews"].append("The result contains root-bone location curves only and remains unbound")
    report["reviews"].append("TRANSFER maps absolute source basis location through Armature space; no proportion is inferred")
    return report


def apply_root_translation_bake(plan, authorization=False):
    """Bake one independent root-location Action after exact-plan authorization."""
    result = {"schema": "gameassetai.root-translation-bake-result.v1",
              "status": "error", "errors": []}
    if authorization is not True:
        result["errors"].append("Explicit authorization=true is required"); return result
    if not isinstance(plan, dict) or plan.get("schema") != "gameassetai.root-translation-bake-plan.v1" or plan.get("status") != "candidate_for_review":
        result["errors"].append("A candidate_for_review plan is required"); return result
    request, candidate = plan.get("request"), plan.get("candidate")
    fresh = preview_root_translation_bake(request) if isinstance(request, dict) else None
    if not fresh or fresh.get("status") != "candidate_for_review" or fresh.get("candidate") != candidate:
        result["errors"].append("Root translation preview is stale"); return result
    scene = bpy.data.scenes[request["scene_name"]]
    source, target = scene.objects[request["source_armature"]], scene.objects[request["target_armature"]]
    action = bpy.data.actions[request["source_action"]]
    source_state = _root_bake_state(source, request["source_root_bone"])
    target_state = _root_bake_state(target, request["target_root_bone"])
    action_state, action_refs = action_content_snapshot(action), _action_references(action)
    window = bpy.context.window
    if window is None or bpy.context.mode != "OBJECT":
        result["errors"].append("Apply requires an Object-mode Blender window"); return result
    original_scene, original_layer = window.scene, window.view_layer
    token = uuid.uuid4().hex
    work_scene = source_work = target_work = source_data = target_data = created = None
    expected = {}
    try:
        work_scene = bpy.data.scenes.new("GAI_RootTranslationBake_" + token)
        source_data, target_data = source.data.copy(), target.data.copy()
        source_work, target_work = source.copy(), target.copy()
        for item in (work_scene, source_data, target_data, source_work, target_work):
            item["gameassetai_test_owner"] = token
        source_work.data, target_work.data = source_data, target_data
        source_work.animation_data_clear(); target_work.animation_data_clear()
        work_scene.collection.objects.link(source_work); work_scene.collection.objects.link(target_work)
        source_work.animation_data_create(); source_work.animation_data.action = action
        slot_id = candidate["source_slot_identifier"]
        if slot_id is not None:
            source_work.animation_data.action_slot = next(s for s in action.slots if s.identifier == slot_id)
        window.scene = work_scene
        source_rest = source_work.data.bones[request["source_root_bone"]].matrix_local.to_3x3()
        target_rest_inv = target_work.data.bones[request["target_root_bone"]].matrix_local.to_3x3().inverted_safe()
        mask = candidate["axis_mask"]
        for frame in candidate["frames"]:
            work_scene.frame_set(frame)
            source_location = source_work.pose.bones[request["source_root_bone"]].matrix_basis.translation
            armature_delta = source_rest @ source_location
            if candidate["motion_policy"] == "TRANSFER":
                desired = Vector((armature_delta[i] * candidate["translation_scale"] if mask[i] else 0.0
                                  for i in range(3)))
            else:
                desired = Vector((0.0, 0.0, 0.0))
            target_location = target_rest_inv @ desired
            expected[frame] = target_location.copy()
            pose = target_work.pose.bones[request["target_root_bone"]]
            pose.location = target_location
            pose.keyframe_insert(data_path="location", frame=frame)
        created = target_work.animation_data.action
        if created is None: raise RuntimeError("Blender did not create an Action")
        created["gameassetai_test_owner"] = token; created.name = request["target_action"]
        created.use_fake_user = True
        if created.name != request["target_action"]: raise RuntimeError("Exact target Action name was not preserved")
        for curve in _curves(created):
            for point in curve.keyframe_points: point.interpolation = "LINEAR"
        if len(_curves(created)) != 3: raise RuntimeError("Expected exactly three location F-Curves")
        for frame, expected_location in expected.items():
            work_scene.frame_set(frame)
            actual = target_work.pose.bones[request["target_root_bone"]].matrix_basis.translation
            if (actual - expected_location).length > 1e-5:
                raise RuntimeError("Baked root translation verification failed")
        target_work.animation_data.action = None; source_work.animation_data.action = None
        if _action_references(created) != ([], []): raise RuntimeError("Created Action is unexpectedly bound")
        if action_content_snapshot(action) != action_state or _action_references(action) != action_refs:
            raise RuntimeError("Source Action changed")
        if _root_bake_state(source, request["source_root_bone"]) != source_state or _root_bake_state(target, request["target_root_bone"]) != target_state:
            raise RuntimeError("Source or target Armature changed")
        result.update({"status": "created", "target_action": created.name,
                       "target_slot_identifier": created.slots[0].identifier if len(created.slots) else None,
                       "frame_count": len(expected), "curve_count": 3,
                       "motion_policy": candidate["motion_policy"],
                       "translation_scale": candidate["translation_scale"],
                       "axis_mask": candidate["axis_mask"], "target_unbound": True,
                       "target_fake_user": True, "source_target_preserved": True})
    except Exception as exc:
        result["errors"].append(str(exc))
        if created is not None:
            if target_work and target_work.animation_data and target_work.animation_data.action == created:
                target_work.animation_data.action = None
            if bpy.data.actions.get(created.name) == created: bpy.data.actions.remove(created)
            created = None
    finally:
        window.scene, window.view_layer = original_scene, original_layer
        for obj in (source_work, target_work):
            if obj is not None and bpy.data.objects.get(obj.name) == obj: bpy.data.objects.remove(obj, do_unlink=True)
        for data in (source_data, target_data):
            if data is not None and data.users == 0: bpy.data.armatures.remove(data)
        if work_scene is not None and bpy.data.scenes.get(work_scene.name) == work_scene: bpy.data.scenes.remove(work_scene)
    return result
