import hashlib
import json
import math

import bpy

from validate_pose_action_request import validate_request


OWNER_KEY = "gameassetai_pose_action_owner"


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _curves(action):
    result = []
    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            for bag in getattr(strip, "channelbags", ()):
                result.extend(bag.fcurves)
    return result


def author_action(request, *, authorized=False):
    if not authorized:
        raise ValueError("authorized=true is required for persistent Action creation")
    validated = validate_request(request)
    data = validated["request"]
    scene = bpy.data.scenes.get(data["scene_name"])
    arm = scene.objects.get(data["armature_object_name"]) if scene else None
    if arm is None or arm.type != "ARMATURE":
        raise ValueError("explicit Armature target does not exist")
    if bpy.data.actions.get(data["action_name"]):
        raise ValueError("action_name is already in use")
    anim = arm.animation_data
    if anim and (anim.action or len(anim.nla_tracks) or anim.drivers):
        raise ValueError("Armature current Action, NLA and drivers must be empty")
    required_bones = sorted(set(validated["animated_bones"]) | set(validated["location_bones"]))
    missing = [name for name in required_bones if arm.pose.bones.get(name) is None]
    if missing:
        raise ValueError(f"animated bones do not exist: {missing}")
    rig_axis = arm.get("gameassetai_character_front_axis")
    if rig_axis and rig_axis != data["front_axis"]:
        raise ValueError(f"front_axis mismatch: rig={rig_axis}, request={data['front_axis']}")

    created = None
    original_frame = scene.frame_current
    try:
        for bone in arm.pose.bones:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = (0.0, 0.0, 0.0)
            bone.location = (0.0, 0.0, 0.0)
        for item in data["keyframes"]:
            scene.frame_set(item["frame"])
            for name, degrees in item["rotations_degrees"].items():
                pose = arm.pose.bones[name]
                pose.rotation_euler = tuple(math.radians(value) for value in degrees)
                pose.keyframe_insert(data_path="rotation_euler", frame=item["frame"], group=name)
            for name, location in item.get("locations_local", {}).items():
                pose = arm.pose.bones[name]
                pose.location = tuple(location)
                pose.keyframe_insert(data_path="location", frame=item["frame"], group=name)
        created = arm.animation_data.action
        created.name = data["action_name"]
        created[OWNER_KEY] = validated["request_sha256"]
        created["gameassetai_character_front_axis"] = data["front_axis"]
        curves = _curves(created)
        for curve in curves:
            for point in curve.keyframe_points:
                point.interpolation = "BEZIER"
                point.handle_left_type = "AUTO_CLAMPED"
                point.handle_right_type = "AUTO_CLAMPED"
        scene.frame_start, scene.frame_end, scene.render.fps = data["frame_start"], data["frame_end"], data["fps"]
        receipt = {"status":"created","action_name":created.name,"armature_object_name":arm.name,"front_axis":data["front_axis"],"frame_range":[data["frame_start"],data["frame_end"]],"fps":data["fps"],"animated_bones":validated["animated_bones"],"location_bones":validated["location_bones"],"fcurve_count":len(curves),"key_count":sum(len(c.keyframe_points) for c in curves),"request_sha256":validated["request_sha256"]}
        receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt).encode()).hexdigest()
        return receipt
    except Exception:
        if created is not None:
            if arm.animation_data and arm.animation_data.action == created: arm.animation_data.action = None
            if created.users == 0: bpy.data.actions.remove(created)
        raise
    finally:
        scene.frame_set(original_frame)

