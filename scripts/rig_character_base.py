import hashlib
import json
import math
import uuid

import bpy
from mathutils import Vector

from validate_character_rig_request import validate_request


CHARACTER_OWNER_KEY = "gameassetai_character_owner"
RIG_OWNER_KEY = "gameassetai_rig_owner"


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _add_bone(edit_bones, name, head, tail, parent=None):
    bone = edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.parent = parent
    return bone


def _assign_groups(obj, proportions):
    h = proportions["height"]
    shoulder = h * proportions["shoulder_width_ratio"]
    hip = h * proportions["hip_width_ratio"]
    upper = h * 0.17
    lower = h * 0.16
    groups = {name: obj.vertex_groups.new(name=name) for name in (
        "pelvis", "spine", "chest", "neck", "head",
        "upper_arm.L", "forearm.L", "hand.L", "upper_arm.R", "forearm.R", "hand.R",
        "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R",
    )}
    shoulder_x = shoulder * 0.46
    for vertex in obj.data.vertices:
        x, y, z = vertex.co
        side = "L" if x >= 0 else "R"
        ax = abs(x)
        if z > h * 0.835:
            name = "head"
        elif z > h * 0.81 and ax < shoulder_x * 0.55:
            name = "neck"
        elif z > h * 0.54 and ax > shoulder_x * 0.72:
            distance = ax - shoulder_x
            name = (f"hand.{side}" if distance > upper + lower * 0.82 else
                    f"forearm.{side}" if distance > upper * 0.82 else f"upper_arm.{side}")
        elif z > h * 0.70:
            name = "chest"
        elif z > h * 0.61:
            name = "spine"
        elif z > h * 0.49:
            name = "pelvis"
        elif z > h * 0.31:
            name = f"thigh.{side}"
        elif z > h * 0.065:
            name = f"shin.{side}"
        else:
            name = f"foot.{side}"
        groups[name].add([vertex.index], 1.0, "REPLACE")
    return list(groups)


def _chain_weights(names, value, boundaries, width):
    for index, boundary in enumerate(boundaries):
        if value < boundary - width:
            return {names[index]: 1.0}
        if value <= boundary + width:
            t = (value - (boundary - width)) / (2.0 * width)
            t = t * t * (3.0 - 2.0 * t)
            return {names[index]: 1.0 - t, names[index + 1]: t}
    return {names[-1]: 1.0}


def _assign_groups_blended(obj, proportions):
    h = proportions["height"]
    shoulder = h * proportions["shoulder_width_ratio"]
    upper, lower = h * 0.17, h * 0.16
    names = (
        "pelvis", "spine", "chest", "neck", "head",
        "upper_arm.L", "forearm.L", "hand.L", "upper_arm.R", "forearm.R", "hand.R",
        "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R",
    )
    groups = {name: obj.vertex_groups.new(name=name) for name in names}
    shoulder_x = shoulder * 0.46
    width = h * 0.022
    blended = 0
    for vertex in obj.data.vertices:
        x, _y, z = vertex.co
        side = "L" if x >= 0 else "R"
        ax = abs(x)
        if z > h * 0.54 and ax > shoulder_x * 0.72:
            distance = ax - shoulder_x
            weights = _chain_weights(
                ("chest", f"upper_arm.{side}", f"forearm.{side}", f"hand.{side}"),
                distance,
                (-shoulder_x * 0.10, upper * 0.82, upper + lower * 0.82),
                width,
            )
        elif z < h * 0.54:
            weights = _chain_weights(
                (f"foot.{side}", f"shin.{side}", f"thigh.{side}", "pelvis"),
                z,
                (h * 0.065, h * 0.31, h * 0.49),
                width,
            )
        else:
            weights = _chain_weights(
                ("pelvis", "spine", "chest", "neck", "head"),
                z,
                (h * 0.61, h * 0.70, h * 0.81, h * 0.835),
                width,
            )
        nonzero = 0
        for name, weight in weights.items():
            if weight > 1e-6:
                groups[name].add([vertex.index], weight, "REPLACE")
                nonzero += 1
        blended += int(nonzero > 1)
    return list(groups), blended


def create_rig(request, *, authorized=False):
    if not authorized:
        raise ValueError("authorized=true is required for persistent rig creation")
    validated = validate_request(request)
    data = validated["request"]
    scene = bpy.data.scenes.get(data["scene_name"])
    obj = scene.objects.get(data["mesh_object_name"]) if scene else None
    if scene is None or obj is None or obj.type != "MESH":
        raise ValueError("explicit Scene/Mesh target does not exist")
    if not obj.get(CHARACTER_OWNER_KEY) or "gameassetai_character_request" not in obj:
        raise ValueError("target is not an owned GameAssetAI character base")
    if obj.modifiers or obj.vertex_groups:
        raise ValueError("target already has modifiers or vertex groups")
    if bpy.data.objects.get(data["armature_object_name"]) or bpy.data.armatures.get(data["armature_data_name"]):
        raise ValueError("requested Armature names are occupied")
    character_request = json.loads(obj["gameassetai_character_request"])
    p = character_request["proportions"]
    h = p["height"]
    shoulder = h * p["shoulder_width_ratio"]
    hip = h * p["hip_width_ratio"]
    upper, lower = h * 0.17, h * 0.16
    drop = 0.0 if character_request["pose"] == "T_POSE" else h * 0.085
    shoulder_x, hip_x = shoulder * 0.46, hip * 0.27
    token = uuid.uuid4().hex
    previous_active = bpy.context.view_layer.objects.active
    previous_selected = list(bpy.context.selected_objects)
    previous_mode = previous_active.mode if previous_active else "OBJECT"
    created_groups = []
    modifier = None
    arm_obj = None
    arm_data = None
    try:
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        arm_data = bpy.data.armatures.new(data["armature_data_name"])
        arm_data[RIG_OWNER_KEY] = token
        arm_obj = bpy.data.objects.new(data["armature_object_name"], arm_data)
        arm_obj[RIG_OWNER_KEY] = token
        arm_obj["gameassetai_character_front_axis"] = obj.get("gameassetai_character_front_axis", "-Y")
        obj.users_collection[0].objects.link(arm_obj)
        arm_obj.show_in_front = True
        for selected in bpy.context.selected_objects:
            selected.select_set(False)
        arm_obj.select_set(True)
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode="EDIT")
        eb = arm_data.edit_bones
        root = _add_bone(eb, "root", (0, 0, 0), (0, 0, h * 0.08))
        pelvis = _add_bone(eb, "pelvis", (0, 0, h * 0.48), (0, 0, h * 0.61), root)
        spine = _add_bone(eb, "spine", (0, 0, h * 0.61), (0, 0, h * 0.72), pelvis)
        chest = _add_bone(eb, "chest", (0, 0, h * 0.72), (0, 0, h * 0.82), spine)
        neck = _add_bone(eb, "neck", (0, 0, h * 0.82), (0, 0, h * 0.86), chest)
        _add_bone(eb, "head", (0, 0, h * 0.86), (0, 0, h * 0.98), neck)
        for side, suffix in ((1.0, ".L"), (-1.0, ".R")):
            shoulder_point = Vector((side * shoulder_x, 0, h * 0.79))
            elbow = shoulder_point + Vector((side * upper, 0, -drop))
            hand = elbow + Vector((side * lower, 0, -drop * 0.72))
            upper_bone = _add_bone(eb, "upper_arm" + suffix, shoulder_point, elbow, chest)
            forearm = _add_bone(eb, "forearm" + suffix, elbow, hand, upper_bone)
            _add_bone(eb, "hand" + suffix, hand, hand + Vector((side * h * 0.045, 0, 0)), forearm)
            thigh = _add_bone(eb, "thigh" + suffix, (side * hip_x, 0, h * 0.56), (side * hip_x * 1.04, 0, h * 0.32), pelvis)
            shin = _add_bone(eb, "shin" + suffix, thigh.tail, (side * hip_x * 1.02, 0, h * 0.085), thigh)
            _add_bone(eb, "foot" + suffix, shin.tail, (side * hip_x * 1.02, -h * p["body_depth_ratio"] * 0.42, h * 0.035), shin)
        bpy.ops.object.mode_set(mode="OBJECT")
        weight_mode = data["policy"]["weights"]
        if weight_mode == "LINEAR_JOINT_BLEND_V2":
            created_groups, blended_vertex_count = _assign_groups_blended(obj, p)
        else:
            created_groups = _assign_groups(obj, p)
            blended_vertex_count = 0
        modifier = obj.modifiers.new(name=data["rig_name"] + " Armature", type="ARMATURE")
        modifier.object = arm_obj
        receipt = {
            "status": "created", "mesh_object_name": obj.name,
            "armature_object_name": arm_obj.name, "armature_data_name": arm_data.name,
            "bone_names": sorted(bone.name for bone in arm_data.bones),
            "vertex_group_names": sorted(created_groups), "modifier_name": modifier.name,
            "request_sha256": validated["request_sha256"], "weighted_vertex_count": len(obj.data.vertices),
            "weight_mode": weight_mode, "blended_vertex_count": blended_vertex_count,
        }
        receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt).encode()).hexdigest()
        return receipt
    except Exception:
        if modifier and modifier.name in obj.modifiers:
            obj.modifiers.remove(modifier)
        for name in created_groups:
            group = obj.vertex_groups.get(name)
            if group: obj.vertex_groups.remove(group)
        if arm_obj and bpy.data.objects.get(arm_obj.name): bpy.data.objects.remove(arm_obj, do_unlink=True)
        if arm_data and bpy.data.armatures.get(arm_data.name) and arm_data.users == 0: bpy.data.armatures.remove(arm_data)
        raise
    finally:
        if bpy.context.object and bpy.context.object.mode != "OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
        for selected in bpy.context.selected_objects: selected.select_set(False)
        for selected in previous_selected:
            if bpy.data.objects.get(selected.name): selected.select_set(True)
        if previous_active and bpy.data.objects.get(previous_active.name): bpy.context.view_layer.objects.active = previous_active


def remove_created_rig(receipt):
    obj = bpy.data.objects.get(receipt["mesh_object_name"])
    arm_obj = bpy.data.objects.get(receipt["armature_object_name"])
    if obj is None or arm_obj is None:
        return
    token = arm_obj.get(RIG_OWNER_KEY)
    if not token or arm_obj.data.get(RIG_OWNER_KEY) != token:
        raise RuntimeError("rig ownership cannot be verified")
    modifier = obj.modifiers.get(receipt["modifier_name"])
    if modifier is None or modifier.type != "ARMATURE" or modifier.object != arm_obj:
        raise RuntimeError("rig modifier ownership cannot be verified")
    obj.modifiers.remove(modifier)
    for name in receipt["vertex_group_names"]:
        group = obj.vertex_groups.get(name)
        if group: obj.vertex_groups.remove(group)
    arm_data = arm_obj.data
    bpy.data.objects.remove(arm_obj, do_unlink=True)
    if arm_data.users == 0: bpy.data.armatures.remove(arm_data)
