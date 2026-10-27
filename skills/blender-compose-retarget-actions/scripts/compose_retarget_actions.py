"""Compose validated rotation-only and root-location-only Actions into one unbound copy."""
from __future__ import annotations

import hashlib
import json
import math
import re
import uuid

import bpy


COMPOSE_RETARGET_SCHEMA = "gameassetai.compose-retarget-actions-request.v1"
_COMPOSE_KEYS = {"schema", "scene_name", "target_armature", "rotation_action",
                 "translation_action", "target_action", "target_root_bone",
                 "frame_start", "frame_end", "frame_step", "preserve_sources",
                 "bind_result", "set_fake_user"}
_BONE_CHANNEL = re.compile(r'^pose\.bones\["((?:[^"\\]|\\.)*)"\]\.(\w+)$')


def _compose_digest(value):
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False,
                     sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _compose_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return int(value)


def _compose_channel(curve):
    match = _BONE_CHANNEL.match(curve.data_path)
    if not match:
        return None
    return (match.group(1).replace('\\"', '"').replace('\\\\', '\\'), match.group(2))


def _compose_curve_map(action):
    result = {}
    for curve in _curves(action):
        key = (curve.data_path, int(curve.array_index))
        if key in result:
            raise ValueError("Action contains duplicate channels")
        result[key] = _curve_snapshot(curve)
    return result


def _compose_linear_integer(curve, frames):
    points = list(curve.keyframe_points)
    return ([float(point.co.x) for point in points] == [float(frame) for frame in frames]
            and all(point.interpolation == "LINEAR" for point in points)
            and not curve.sampled_points and not curve.modifiers
            and all(math.isfinite(float(point.co.y)) for point in points))


def preview_retarget_action_composition(request):
    """Validate two narrow bake outputs and build a no-write composition plan."""
    report = {"schema": "gameassetai.compose-retarget-actions-plan.v1", "status": "error",
              "errors": [], "reviews": [], "authorization": False}
    if not isinstance(request, dict):
        report["errors"].append("Request must be an object"); return report
    unknown, missing = sorted(set(request)-_COMPOSE_KEYS), sorted(_COMPOSE_KEYS-set(request))
    if unknown: report["errors"].append("Unknown request fields: "+", ".join(unknown))
    if missing: report["errors"].append("Missing request fields: "+", ".join(missing))
    if unknown or missing: return report
    if request["schema"] != COMPOSE_RETARGET_SCHEMA: report["errors"].append("Unsupported request schema")
    for key in ("scene_name","target_armature","rotation_action","translation_action",
                "target_action","target_root_bone"):
        value=request[key]
        if not isinstance(value,str) or not value or value!=value.strip():
            report["errors"].append(f"{key} must be an exact nonempty name")
    if len({request["rotation_action"],request["translation_action"],request["target_action"]}) != 3:
        report["errors"].append("Rotation, translation and target Action names must differ")
    for key,expected in (("preserve_sources",True),("bind_result",False),("set_fake_user",True)):
        if request[key] is not expected: report["errors"].append(f"This workflow requires {key}={str(expected).lower()}")
    try:
        start=_compose_int(request["frame_start"],"frame_start")
        end=_compose_int(request["frame_end"],"frame_end")
        step=_compose_int(request["frame_step"],"frame_step")
    except ValueError as exc: report["errors"].append(str(exc)); return report
    if end<start: report["errors"].append("frame_end must be >= frame_start")
    if step!=1: report["errors"].append("This bounded composition requires frame_step=1")
    if end-start>10000: report["errors"].append("Composition range exceeds 10001 frames")
    if report["errors"]: return report
    scene=bpy.data.scenes.get(request["scene_name"])
    target=scene.objects.get(request["target_armature"]) if scene else None
    rotation=bpy.data.actions.get(request["rotation_action"])
    translation=bpy.data.actions.get(request["translation_action"])
    if target is None or target.type!="ARMATURE": report["errors"].append("Target Armature not found")
    if rotation is None: report["errors"].append("Rotation Action not found")
    if translation is None: report["errors"].append("Translation Action not found")
    if bpy.data.actions.get(request["target_action"]) is not None: report["errors"].append("Target Action already exists")
    if report["errors"]: return report
    if target.data.bones.get(request["target_root_bone"]) is None:
        report["errors"].append("Target root bone not found")
    if target.constraints or any(pb.constraints for pb in target.pose.bones):
        report["errors"].append("Target constraints are not supported")
    for label,action in (("Rotation",rotation),("Translation",translation)):
        if not action.use_fake_user or _action_references(action)!=([],[]):
            report["errors"].append(f"{label} Action must be fake-user protected and unbound")
        if len(getattr(action,"slots",()))!=1 or action.slots[0].target_id_type!="OBJECT":
            report["errors"].append(f"{label} Action requires exactly one Object slot")
    frames=list(range(start,end+1))
    rotation_keys=set(); translation_keys=set()
    for curve in _curves(rotation):
        parsed=_compose_channel(curve)
        if parsed is None or parsed[1]!="rotation_quaternion" or curve.array_index not in {0,1,2,3}:
            report["errors"].append("Rotation Action must contain quaternion bone channels only"); break
        if target.data.bones.get(parsed[0]) is None:
            report["errors"].append("Rotation Action references a missing target bone"); break
        if not _compose_linear_integer(curve,frames):
            report["errors"].append("Rotation curves require one linear key per requested integer frame"); break
        rotation_keys.add((curve.data_path,curve.array_index))
    for curve in _curves(translation):
        parsed=_compose_channel(curve)
        if (parsed!=(request["target_root_bone"],"location") or curve.array_index not in {0,1,2}):
            report["errors"].append("Translation Action must contain target-root location channels only"); break
        if not _compose_linear_integer(curve,frames):
            report["errors"].append("Translation curves require one linear key per requested integer frame"); break
        translation_keys.add((curve.data_path,curve.array_index))
    if len(rotation_keys)==0: report["errors"].append("Rotation Action has no curves")
    if len(translation_keys)!=3: report["errors"].append("Translation Action requires exactly XYZ curves")
    if rotation_keys & translation_keys: report["errors"].append("Input channels collide")
    if report["errors"]: return report
    candidate={"operation":"compose_rotation_and_root_translation_unbound",
               "frames":frames,"frame_count":len(frames),"rotation_curve_count":len(rotation_keys),
               "translation_curve_count":3,"rotation_sha256":action_content_fingerprint(rotation),
               "translation_sha256":action_content_fingerprint(translation),
               "target_state_sha256":_compose_digest(_evaluated_root_source_snapshot(target)),
               "request_sha256":_compose_digest(request)}
    report.update({"status":"candidate_for_review","request":dict(request),"candidate":candidate})
    report["reviews"].append("The result remains unbound; composition does not authorize binding or export")
    return report


def apply_retarget_action_composition(plan, authorization=False):
    """Copy the rotation Action and append sampled root-location curves on a temp rig."""
    result={"schema":"gameassetai.compose-retarget-actions-result.v1","status":"error","errors":[]}
    if authorization is not True: result["errors"].append("Explicit authorization=true is required"); return result
    if not isinstance(plan,dict) or plan.get("schema")!="gameassetai.compose-retarget-actions-plan.v1" or plan.get("status")!="candidate_for_review":
        result["errors"].append("A candidate_for_review plan is required"); return result
    request,candidate=plan.get("request"),plan.get("candidate")
    fresh=preview_retarget_action_composition(request) if isinstance(request,dict) else None
    if not fresh or fresh.get("status")!="candidate_for_review" or fresh.get("candidate")!=candidate:
        result["errors"].append("Composition preview is stale"); return result
    scene=bpy.data.scenes[request["scene_name"]]; target=scene.objects[request["target_armature"]]
    rotation=bpy.data.actions[request["rotation_action"]]; translation=bpy.data.actions[request["translation_action"]]
    rotation_state,translation_state=_compose_curve_map(rotation),_compose_curve_map(translation)
    rotation_refs,translation_refs=_action_references(rotation),_action_references(translation)
    target_state=_evaluated_root_source_snapshot(target)
    window=bpy.context.window
    if window is None or bpy.context.mode!="OBJECT": result["errors"].append("Apply requires Object mode"); return result
    original_scene,original_layer=window.scene,window.view_layer
    token=uuid.uuid4().hex; work_scene=work_obj=work_data=created=None
    try:
        created=rotation.copy(); created.name=request["target_action"]; created.use_fake_user=True
        if created.name!=request["target_action"]: raise RuntimeError("Exact target Action name was not preserved")
        work_scene=bpy.data.scenes.new("GAI_ComposeRetarget_"+token); work_data=target.data.copy(); work_obj=target.copy()
        for item in (work_scene,work_data,work_obj): item["gameassetai_test_owner"]=token
        work_obj.data=work_data; work_obj.animation_data_clear(); work_scene.collection.objects.link(work_obj)
        work_obj.animation_data_create(); work_obj.animation_data.action=created
        if len(created.slots)==1: work_obj.animation_data.action_slot=created.slots[0]
        curves={curve.array_index:curve for curve in _curves(translation)}
        window.scene=work_scene
        root=work_obj.pose.bones[request["target_root_bone"]]
        for frame in candidate["frames"]:
            root.location=tuple(float(curves[index].evaluate(frame)) for index in range(3))
            root.keyframe_insert(data_path="location",frame=frame)
        for curve in _curves(created):
            if _compose_channel(curve)==(request["target_root_bone"],"location"):
                for point in curve.keyframe_points: point.interpolation="LINEAR"
        actual=_compose_curve_map(created)
        for key,value in rotation_state.items():
            if actual.get(key)!=value: raise RuntimeError("Rotation channel changed during composition")
        for key,value in translation_state.items():
            if key not in actual: raise RuntimeError("Translation channel missing from composition")
            source_curve=next(c for c in _curves(translation) if (c.data_path,c.array_index)==key)
            output_curve=next(c for c in _curves(created) if (c.data_path,c.array_index)==key)
            for frame in candidate["frames"]:
                if abs(source_curve.evaluate(frame)-output_curve.evaluate(frame))>1e-6:
                    raise RuntimeError("Translation values differ after composition")
        work_obj.animation_data.action=None
        if _action_references(created)!=([],[]): raise RuntimeError("Composed Action is unexpectedly bound")
        if _compose_curve_map(rotation)!=rotation_state or _compose_curve_map(translation)!=translation_state:
            raise RuntimeError("Source Action content changed")
        if _action_references(rotation)!=rotation_refs or _action_references(translation)!=translation_refs:
            raise RuntimeError("Source Action references changed")
        if _evaluated_root_source_snapshot(target)!=target_state: raise RuntimeError("Target Armature changed")
        result.update({"status":"created","target_action":created.name,
                       "curve_count":len(actual),"rotation_curve_count":len(rotation_state),
                       "translation_curve_count":3,"target_unbound":True,"target_fake_user":True,
                       "sources_target_preserved":True})
    except Exception as exc:
        result["errors"].append(str(exc))
        if created is not None:
            if work_obj and work_obj.animation_data and work_obj.animation_data.action==created: work_obj.animation_data.action=None
            if bpy.data.actions.get(created.name)==created: bpy.data.actions.remove(created)
            created=None
    finally:
        window.scene,window.view_layer=original_scene,original_layer
        if work_obj is not None and bpy.data.objects.get(work_obj.name)==work_obj: bpy.data.objects.remove(work_obj,do_unlink=True)
        if work_data is not None and work_data.users==0: bpy.data.armatures.remove(work_data)
        if work_scene is not None and bpy.data.scenes.get(work_scene.name)==work_scene: bpy.data.scenes.remove(work_scene)
    return result

