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


DEFORM_GROUPS = (
    "pelvis", "spine", "chest", "neck", "head",
    "upper_arm.L", "forearm.L", "hand.L", "upper_arm.R", "forearm.R", "hand.R",
    "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R",
)


def _mesh_fingerprints(mesh):
    geometry = [[float(value) for value in vertex.co] for vertex in mesh.vertices]
    uv = None
    if mesh.uv_layers and mesh.uv_layers.active:
        uv = [[float(value) for value in loop.uv] for loop in mesh.uv_layers.active.data]
    return {
        "geometry_sha256": hashlib.sha256(_canonical(geometry).encode()).hexdigest(),
        "uv_sha256": hashlib.sha256(_canonical(uv).encode()).hexdigest() if uv is not None else None,
    }


def _validate_landmarks(obj, fitting):
    landmarks = {name: Vector(point) for name, point in fitting["landmarks"].items()}
    bounds = [Vector(corner) for corner in obj.bound_box]
    minimum = Vector(tuple(min(point[index] for point in bounds) for index in range(3)))
    maximum = Vector(tuple(max(point[index] for point in bounds) for index in range(3)))
    height = maximum.z - minimum.z
    if height <= 0.0:
        raise ValueError("Humanoid Mesh must have positive local height")
    tolerance = height * 0.15
    for name, point in landmarks.items():
        if any(point[index] < minimum[index] - tolerance or point[index] > maximum[index] + tolerance
               for index in range(3)):
            raise ValueError(f"landmark is outside the supported Mesh envelope: {name}")
    center = ("root", "pelvis", "spine", "chest", "neck", "head_top")
    if any(landmarks[left].z >= landmarks[right].z for left, right in zip(center, center[1:])):
        raise ValueError("center landmarks must increase from root through head_top")
    for side, sign in (("L", 1.0), ("R", -1.0)):
        if any(landmarks[f"{joint}.{side}"].x * sign <= 0.0
               for joint in ("shoulder", "elbow", "wrist", "hand_tip", "hip", "knee", "ankle", "toe")):
            raise ValueError(f"{side} landmarks must remain on their declared side")
        for chain in (("shoulder", "elbow", "wrist", "hand_tip"),
                      ("hip", "knee", "ankle", "toe")):
            points = [landmarks[f"{joint}.{side}"] for joint in chain]
            if any((tail - head).length < height * 0.02 for head, tail in zip(points, points[1:])):
                raise ValueError(f"{side} {chain[0]} chain contains a collapsed bone")
        if not (landmarks[f"hip.{side}"].z > landmarks[f"knee.{side}"].z
                > landmarks[f"ankle.{side}"].z):
            raise ValueError(f"{side} leg landmarks must descend from hip to ankle")
    return landmarks, height


def _build_landmark_bones(edit_bones, landmarks):
    root = _add_bone(edit_bones, "root", landmarks["root"], landmarks["pelvis"])
    root.use_deform = False
    pelvis = _add_bone(edit_bones, "pelvis", landmarks["pelvis"], landmarks["spine"], root)
    spine = _add_bone(edit_bones, "spine", landmarks["spine"], landmarks["chest"], pelvis)
    chest = _add_bone(edit_bones, "chest", landmarks["chest"], landmarks["neck"], spine)
    head_middle = landmarks["neck"].lerp(landmarks["head_top"], 0.24)
    neck = _add_bone(edit_bones, "neck", landmarks["neck"], head_middle, chest)
    _add_bone(edit_bones, "head", head_middle, landmarks["head_top"], neck)
    for side in ("L", "R"):
        suffix = "." + side
        upper = _add_bone(edit_bones, "upper_arm" + suffix, landmarks["shoulder" + suffix],
                          landmarks["elbow" + suffix], chest)
        forearm = _add_bone(edit_bones, "forearm" + suffix, landmarks["elbow" + suffix],
                            landmarks["wrist" + suffix], upper)
        _add_bone(edit_bones, "hand" + suffix, landmarks["wrist" + suffix],
                  landmarks["hand_tip" + suffix], forearm)
        thigh = _add_bone(edit_bones, "thigh" + suffix, landmarks["hip" + suffix],
                          landmarks["knee" + suffix], pelvis)
        shin = _add_bone(edit_bones, "shin" + suffix, landmarks["knee" + suffix],
                         landmarks["ankle" + suffix], thigh)
        _add_bone(edit_bones, "foot" + suffix, landmarks["ankle" + suffix],
                  landmarks["toe" + suffix], shin)


def _point_segment_distance(point, head, tail):
    delta = tail - head
    length_squared = delta.length_squared
    if length_squared <= 1e-12:
        return (point - head).length
    factor = max(0.0, min(1.0, (point - head).dot(delta) / length_squared))
    return (point - (head + delta * factor)).length


def _assign_groups_landmark_envelope(obj, arm_data, height, width_ratio, created_names):
    groups = {}
    for name in DEFORM_GROUPS:
        groups[name] = obj.vertex_groups.new(name=name)
        created_names.append(name)
    segments = {bone.name: (bone.head_local.copy(), bone.tail_local.copy())
                for bone in arm_data.bones if bone.name in groups}
    width = max(height * width_ratio, height * 0.015)
    epsilon = height * 0.002
    blended = missing = cross_side = 0
    maximum_influences = 0
    maximum_sum_error = 0.0
    for vertex in obj.data.vertices:
        side = "L" if vertex.co.x > epsilon else "R" if vertex.co.x < -epsilon else None
        candidates = {}
        for name, (head, tail) in segments.items():
            if name.endswith(".L") and side != "L":
                continue
            if name.endswith(".R") and side != "R":
                continue
            distance = _point_segment_distance(vertex.co, head, tail)
            candidates[name] = math.exp(-0.5 * (distance / width) ** 2)
        ordered = sorted(candidates.items(), key=lambda item: item[1], reverse=True)[:4]
        total = sum(weight for _name, weight in ordered)
        if total <= 1e-20:
            missing += 1
            continue
        normalized = [(name, weight / total) for name, weight in ordered if weight / total > 1e-6]
        norm_total = sum(weight for _name, weight in normalized)
        normalized = [(name, weight / norm_total) for name, weight in normalized]
        for name, weight in normalized:
            groups[name].add([vertex.index], weight, "REPLACE")
            if (vertex.co.x > epsilon and name.endswith(".R")) or (
                    vertex.co.x < -epsilon and name.endswith(".L")):
                cross_side += 1
        maximum_influences = max(maximum_influences, len(normalized))
        blended += int(len(normalized) > 1)
        maximum_sum_error = max(maximum_sum_error,
                                abs(1.0 - sum(weight for _name, weight in normalized)))
    if missing:
        raise RuntimeError(f"landmark weights left {missing} vertices unweighted")
    if cross_side:
        raise RuntimeError(f"landmark weights created {cross_side} cross-side influences")
    return {"blended_vertex_count": blended, "missing_vertex_count": missing,
            "cross_side_influence_count": cross_side, "maximum_influences": maximum_influences,
            "maximum_weight_sum_error": maximum_sum_error, "transition_width": width}


def create_rig(request, *, authorized=False):
    if not authorized:
        raise ValueError("authorized=true is required for persistent rig creation")
    validated = validate_request(request)
    data = validated["request"]
    scene = bpy.data.scenes.get(data["scene_name"])
    obj = scene.objects.get(data["mesh_object_name"]) if scene else None
    if scene is None or obj is None or obj.type != "MESH":
        raise ValueError("explicit Scene/Mesh target does not exist")
    adaptation = data["schema"].endswith(".v3")
    if not adaptation and (not obj.get(CHARACTER_OWNER_KEY)
                           or "gameassetai_character_request" not in obj):
        raise ValueError("target is not an owned GameAssetAI character base")
    if adaptation:
        if obj.library or obj.data.library or obj.data.shape_keys or obj.animation_data:
            raise ValueError("adaptation target must be local and have no Shape Keys or animation")
        if obj.mode != "OBJECT" or not obj.data.vertices or not obj.data.polygons:
            raise ValueError("adaptation target must be a non-empty Object-mode Mesh")
        if obj.get("gameassetai_character_front_axis", "-Y") != "-Y":
            raise ValueError("adaptation target front axis must be -Y")
    if obj.modifiers or obj.vertex_groups:
        raise ValueError("target already has modifiers or vertex groups")
    if bpy.data.objects.get(data["armature_object_name"]) or bpy.data.armatures.get(data["armature_data_name"]):
        raise ValueError("requested Armature names are occupied")
    if adaptation:
        landmarks, h = _validate_landmarks(obj, data["fitting"])
        p = character_request = None
        source_fingerprints = _mesh_fingerprints(obj.data)
    else:
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
        arm_obj["gameassetai_rig_request"] = _canonical(data)
        arm_obj["gameassetai_character_front_axis"] = obj.get("gameassetai_character_front_axis", "-Y")
        if adaptation:
            arm_obj.matrix_world = obj.matrix_world.copy()
        obj.users_collection[0].objects.link(arm_obj)
        arm_obj.show_in_front = True
        for selected in bpy.context.selected_objects:
            selected.select_set(False)
        arm_obj.select_set(True)
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode="EDIT")
        eb = arm_data.edit_bones
        if adaptation:
            _build_landmark_bones(eb, landmarks)
        else:
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
                _add_bone(eb, "hand" + suffix, hand,
                          hand + Vector((side * h * 0.045, 0, 0)), forearm)
                thigh = _add_bone(eb, "thigh" + suffix, (side * hip_x, 0, h * 0.56),
                                  (side * hip_x * 1.04, 0, h * 0.32), pelvis)
                shin = _add_bone(eb, "shin" + suffix, thigh.tail,
                                 (side * hip_x * 1.02, 0, h * 0.085), thigh)
                _add_bone(eb, "foot" + suffix, shin.tail,
                          (side * hip_x * 1.02, -h * p["body_depth_ratio"] * 0.42, h * 0.035), shin)
        bpy.ops.object.mode_set(mode="OBJECT")
        weight_mode = data["policy"]["weights"]
        if weight_mode == "LANDMARK_ENVELOPE_V3":
            weight_facts = _assign_groups_landmark_envelope(
                obj, arm_data, h, data["fitting"]["transition_width_ratio"], created_groups)
            blended_vertex_count = weight_facts["blended_vertex_count"]
        elif weight_mode == "LINEAR_JOINT_BLEND_V2":
            created_groups, blended_vertex_count = _assign_groups_blended(obj, p)
            weight_facts = None
        else:
            created_groups = _assign_groups(obj, p)
            blended_vertex_count = 0
            weight_facts = None
        modifier = obj.modifiers.new(name=data["rig_name"] + " Armature", type="ARMATURE")
        modifier.object = arm_obj
        if adaptation and _mesh_fingerprints(obj.data) != source_fingerprints:
            raise RuntimeError("source Mesh coordinates or UV changed during rig adaptation")
        receipt = {
            "status": "created", "mesh_object_name": obj.name,
            "armature_object_name": arm_obj.name, "armature_data_name": arm_data.name,
            "bone_names": sorted(bone.name for bone in arm_data.bones),
            "vertex_group_names": sorted(created_groups), "modifier_name": modifier.name,
            "request_sha256": validated["request_sha256"], "weighted_vertex_count": len(obj.data.vertices),
            "weight_mode": weight_mode, "blended_vertex_count": blended_vertex_count,
        }
        if adaptation:
            receipt.update({"fitting_mode": data["fitting"]["mode"],
                            "coordinate_space": data["fitting"]["coordinate_space"],
                            "landmark_sha256": hashlib.sha256(
                                _canonical(data["fitting"]["landmarks"]).encode()).hexdigest(),
                            "source_preserved": True, "source_fingerprints": source_fingerprints,
                            "weight_validation": weight_facts})
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
