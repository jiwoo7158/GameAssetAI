import hashlib
import json
import re
import sys
import uuid
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

# Reuse the installed sibling inspection Skills in a normal standalone Workspace.
# The same layout exists under repository ``skills/`` during development.
_skills_root = Path(__file__).resolve().parents[2]
for _relative in (("blender-inspect-humanoid", "scripts"),
                  ("blender-inspect-mixamo-preflight", "scripts")):
    _helper_root = _skills_root.joinpath(*_relative)
    if _helper_root.is_dir() and str(_helper_root) not in sys.path:
        sys.path.insert(0, str(_helper_root))

from validate_humanoid_animation_import_request import validate_request
from inspect_humanoid import inspect_humanoid
import inspect_mixamo_preflight as _mixamo_preflight


# The existing preflight helper is normally loaded after inspect_humanoid into one
# Blender execution namespace.  Preserve that contract when importing it as a module.
_mixamo_preflight.inspect_humanoid = inspect_humanoid
inspect_mixamo_preflight = _mixamo_preflight.inspect_mixamo_preflight


OWNER_KEY = "gameassetai_humanoid_animation_owner"
ROLE_ORDER = (
    "hips", "spine", "chest", "neck", "head",
    "upper_leg_l", "lower_leg_l", "foot_l", "upper_leg_r", "lower_leg_r", "foot_r",
    "upper_arm_l", "lower_arm_l", "hand_l", "upper_arm_r", "lower_arm_r", "hand_r",
)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def _sha_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _curves(action):
    if hasattr(action, "fcurves"):
        try:
            return list(action.fcurves)
        except Exception:
            pass
    result = []
    for layer in getattr(action, "layers", ()): 
        for strip in getattr(layer, "strips", ()):
            for bag in getattr(strip, "channelbags", ()):
                result.extend(bag.fcurves)
    return result


def _animation_snapshot(obj):
    data = obj.animation_data
    return {"exists": data is not None,
            "action": data.action.name if data and data.action else None,
            "nla": len(data.nla_tracks) if data else 0,
            "drivers": len(data.drivers) if data else 0}


def _mesh_fingerprint(obj):
    mesh = obj.data
    payload = {"coordinates": [[float(value) for value in vertex.co] for vertex in mesh.vertices],
               "uv": ([[float(value) for value in item.uv]
                       for item in mesh.uv_layers.active.data]
                      if mesh.uv_layers and mesh.uv_layers.active else None)}
    return hashlib.sha256(_canonical(payload).encode()).hexdigest()


def _rig_fingerprint(obj):
    payload = [{"name": bone.name, "parent": bone.parent.name if bone.parent else None,
                "matrix": [[float(value) for value in row] for row in bone.matrix_local]}
               for bone in obj.data.bones]
    return hashlib.sha256(_canonical(payload).encode()).hexdigest()


def _new_data(before, collection):
    return [item for item in collection if item.as_pointer() not in before]


def _remove_new_data(before):
    for obj in _new_data(before["objects"], bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for scene in _new_data(before["scenes"], bpy.data.scenes):
        bpy.data.scenes.remove(scene)
    for collection in _new_data(before["collections"], bpy.data.collections):
        if collection.users == 0:
            bpy.data.collections.remove(collection)
    for action in _new_data(before["actions"], bpy.data.actions):
        # FBX-imported Actions may carry a fake user.  They are nevertheless
        # owned by this failed invocation and must not survive rollback.
        bpy.data.actions.remove(action)
    for armature in _new_data(before["armatures"], bpy.data.armatures):
        if armature.users == 0:
            bpy.data.armatures.remove(armature)
    for mesh in _new_data(before["meshes"], bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for material in _new_data(before["materials"], bpy.data.materials):
        if material.users == 0:
            bpy.data.materials.remove(material)
    for image in _new_data(before["images"], bpy.data.images):
        if image.users == 0:
            bpy.data.images.remove(image)


def _data_baseline():
    names = ("objects", "collections", "actions", "armatures", "meshes", "materials", "images", "scenes")
    return {name: {item.as_pointer() for item in getattr(bpy.data, name)} for name in names}


def _mapped_channels(action, mapping):
    reverse = {name: role for role, name in mapping.items()}
    animated, unmapped, non_bone, mapped_scale = set(), set(), [], []
    pattern = re.compile(r'^pose\.bones\["(.+)"\]\.(rotation_quaternion|rotation_euler|rotation_axis_angle|location|scale)$')
    for curve in _curves(action):
        match = pattern.match(curve.data_path)
        if not match:
            values = [float(point.co[1]) for point in curve.keyframe_points]
            if (curve.data_path not in {"location", "rotation_euler", "rotation_quaternion", "scale"}
                    or (values and max(values) - min(values) > 1e-6)):
                non_bone.append(curve.data_path)
            continue
        bone, channel = match.groups()
        role = reverse.get(bone)
        if role is None:
            unmapped.add(bone)
        else:
            animated.add(role)
            if (channel == "scale" and
                    any(abs(float(point.co[1]) - 1.0) > 1e-5
                        for point in curve.keyframe_points)):
                mapped_scale.append(role)
    return sorted(animated), sorted(unmapped), sorted(set(non_bone)), sorted(set(mapped_scale))


def import_and_retarget(request, *, authorized=False):
    if authorized is not True:
        raise ValueError("authorized=true is required for FBX import and Action creation")
    validated = validate_request(request)
    data = validated["request"]
    source_path = Path(data["source_fbx"]["path"])
    if not source_path.is_file() or source_path.is_symlink():
        raise ValueError("source FBX must be an existing regular non-symbolic file")
    actual_sha = _sha_file(source_path)
    if actual_sha != data["source_fbx"]["sha256"]:
        raise ValueError(f"source FBX SHA-256 mismatch: expected {data['source_fbx']['sha256']}, got {actual_sha}")
    scene = bpy.data.scenes.get(data["scene_name"])
    target = scene.objects.get(data["target"]["armature_name"]) if scene else None
    mesh = scene.objects.get(data["target"]["mesh_object_name"]) if scene else None
    if target is None or target.type != "ARMATURE" or mesh is None or mesh.type != "MESH":
        raise ValueError("explicit target Armature/Mesh does not exist in the named Scene")
    if bpy.data.actions.get(data["target"]["result_action_name"]):
        raise ValueError("result Action name is occupied")
    if bpy.data.collections.get(data["target"]["import_collection_name"]):
        raise ValueError("import Collection name is occupied")
    target_state = _animation_snapshot(target)
    if target_state["action"] or target_state["nla"] or target_state["drivers"]:
        raise ValueError("target Armature animation state is not empty")
    if target.data.animation_data and (target.data.animation_data.action
                                      or target.data.animation_data.nla_tracks
                                      or target.data.animation_data.drivers):
        raise ValueError("target Armature data animation state is not empty")
    if not any(mod.type == "ARMATURE" and mod.object == target for mod in mesh.modifiers):
        raise ValueError("target Mesh is not bound to the explicit target Armature")
    target_inspection = inspect_humanoid(target.name, data["target_mapping"], scene.name)
    if target_inspection.get("status") != "ok":
        raise ValueError("target explicit Humanoid mapping is incomplete")
    before = _data_baseline()
    mesh_before, rig_before = _mesh_fingerprint(mesh), _rig_fingerprint(target)
    frame_before = (scene.frame_current, scene.frame_subframe)
    selected_before = [obj for obj in bpy.context.selected_objects]
    active_before = bpy.context.view_layer.objects.active
    window = bpy.context.window
    original_scene = window.scene if window else None
    token = uuid.uuid4().hex
    result_action = source_armature = source_action = import_collection = temp_scene = None
    animation_data_existed = target.animation_data is not None
    try:
        if window is None or bpy.context.mode != "OBJECT":
            raise ValueError("FBX import requires an Object-mode Blender window")
        temp_scene = bpy.data.scenes.new("GAI_AnimationImport_" + token)
        temp_scene[OWNER_KEY] = token
        window.scene = temp_scene
        bpy.ops.import_scene.fbx(filepath=str(source_path), use_anim=True,
                                 automatic_bone_orientation=False, use_prepost_rot=True)
        imported_objects = _new_data(before["objects"], bpy.data.objects)
        armatures = [obj for obj in imported_objects if obj.type == "ARMATURE"]
        expected_armature = data["source_fbx"]["expected_armature_name"]
        if expected_armature is not None:
            armatures = [obj for obj in armatures if obj.name == expected_armature]
        if len(armatures) != 1:
            raise ValueError("FBX must import exactly one matching source Armature")
        source_armature = armatures[0]
        source_action = source_armature.animation_data.action if source_armature.animation_data else None
        expected_action = data["source_fbx"]["expected_action_name"]
        if source_action is None or (expected_action is not None and source_action.name != expected_action):
            raise ValueError("FBX source Armature does not have the expected current Action")
        preflight = inspect_mixamo_preflight(source_armature.name, temp_scene.name,
                                             data["source_fbx"]["mixamo_prefix"])
        if preflight.get("status") != "ok":
            raise ValueError("source Armature failed exact Mixamo preflight")
        source_inspection = inspect_humanoid(source_armature.name, data["source_mapping"], temp_scene.name)
        if source_inspection.get("status") != "ok":
            raise ValueError("source explicit Humanoid mapping is incomplete")
        animated_roles, unmapped_bones, non_bone, mapped_scale = _mapped_channels(
            source_action, data["source_mapping"])
        if non_bone:
            raise ValueError("source Action has unsupported or animated object channels: " +
                             ", ".join(non_bone))
        if mapped_scale:
            raise ValueError("source Action has non-unit mapped scale channels")
        if not animated_roles:
            raise ValueError("source Action has no mapped Humanoid animation")
        import_collection = bpy.data.collections.new(data["target"]["import_collection_name"])
        import_collection[OWNER_KEY] = token
        scene.collection.children.link(import_collection)
        for obj in imported_objects:
            if import_collection.objects.get(obj.name) is None:
                import_collection.objects.link(obj)
            obj[OWNER_KEY] = token
        for item in _new_data(before["actions"], bpy.data.actions):
            item[OWNER_KEY] = token
        window.scene = scene
        if bpy.data.scenes.get(temp_scene.name) == temp_scene:
            bpy.data.scenes.remove(temp_scene)
        temp_scene = None
        scene.frame_set(data["frame"]["start"])
        bpy.context.view_layer.update()
        source_first_location = source_armature.pose.bones[
            data["source_mapping"]["hips"]].matrix_basis.translation.copy()
        result_action = bpy.data.actions.new(data["target"]["result_action_name"])
        result_action[OWNER_KEY] = token
        result_action["gameassetai_source_fbx_sha256"] = actual_sha
        result_action["gameassetai_source_action"] = source_action.name
        result_action["gameassetai_fps"] = data["frame"]["fps"]
        result_action.use_fake_user = True
        target.animation_data_create().action = result_action
        for frame in range(data["frame"]["start"], data["frame"]["end"] + 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            for pose_bone in target.pose.bones:
                pose_bone.location = (0, 0, 0)
                pose_bone.rotation_mode = "QUATERNION"
                pose_bone.rotation_quaternion = (1, 0, 0, 0)
                pose_bone.scale = (1, 1, 1)
            bpy.context.view_layer.update()
            for role in ROLE_ORDER:
                source_pose = source_armature.pose.bones[data["source_mapping"][role]]
                target_pose = target.pose.bones[data["target_mapping"][role]]
                source_rest = source_armature.data.bones[data["source_mapping"][role]].matrix_local
                target_rest = target.data.bones[data["target_mapping"][role]].matrix_local
                delta = source_pose.matrix.to_quaternion() @ source_rest.to_quaternion().conjugated()
                desired_rotation = (delta @ target_rest.to_quaternion()).normalized()
                desired = desired_rotation.to_matrix().to_4x4()
                desired.translation = target_pose.head
                target_pose.matrix = desired
                target_pose.rotation_mode = "QUATERNION"
                target_pose.keyframe_insert("rotation_quaternion", frame=frame, group=target_pose.name)
            hips = target.pose.bones[data["target_mapping"]["hips"]]
            source_location = source_armature.pose.bones[
                data["source_mapping"]["hips"]].matrix_basis.translation - source_first_location
            if data["root_motion"]["policy"] == "TRANSFER":
                mask = data["root_motion"]["axis_mask"]
                scale = data["root_motion"]["translation_scale"]
                hips.location = Vector(tuple(source_location[index] * scale if mask[index] else 0.0
                                             for index in range(3)))
            else:
                hips.location = (0, 0, 0)
            hips.keyframe_insert("location", frame=frame, group=hips.name)
        for curve in _curves(result_action):
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"
        if _mesh_fingerprint(mesh) != mesh_before or _rig_fingerprint(target) != rig_before:
            raise RuntimeError("target Mesh/UV or Armature rest data changed")
        result = {"status": "created", "request_sha256": validated["request_sha256"],
                  "source_fbx_sha256": actual_sha, "source_armature": source_armature.name,
                  "source_action": source_action.name, "source_mapping": data["source_mapping"],
                  "unmapped_animated_bones": unmapped_bones,
                  "target_armature": target.name, "target_mesh": mesh.name,
                  "result_action": result_action.name,
                  "result_slot_identifier": (result_action.slots[0].identifier
                                             if len(result_action.slots) == 1 else None),
                  "result_bound": target.animation_data.action == result_action,
                  "frame_start": data["frame"]["start"], "frame_end": data["frame"]["end"],
                  "fps": data["frame"]["fps"], "root_motion": data["root_motion"],
                  "import_collection": import_collection.name, "source_preserved": True,
                  "target_geometry_uv_preserved": True, "target_rest_preserved": True}
        result["receipt_sha256"] = hashlib.sha256(_canonical(result).encode()).hexdigest()
        return result
    except Exception:
        if target.animation_data and target.animation_data.action == result_action:
            target.animation_data.action = None
        if not animation_data_existed and target.animation_data and not target.animation_data.nla_tracks:
            target.animation_data_clear()
        _remove_new_data(before)
        if _mesh_fingerprint(mesh) != mesh_before or _rig_fingerprint(target) != rig_before:
            raise RuntimeError("rollback could not verify preserved target data")
        raise
    finally:
        if window and original_scene and bpy.data.scenes.get(original_scene.name):
            window.scene = original_scene
        if bpy.data.scenes.get(scene.name):
            scene.frame_set(frame_before[0], subframe=frame_before[1])
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in selected_before:
            if bpy.data.objects.get(obj.name):
                obj.select_set(True)
        if active_before and bpy.data.objects.get(active_before.name):
            bpy.context.view_layer.objects.active = active_before
