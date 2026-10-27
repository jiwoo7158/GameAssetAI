import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


SOURCE_MAPPING = {
    "hips": "mixamorig:Hips", "spine": "mixamorig:Spine", "chest": "mixamorig:Spine2",
    "neck": "mixamorig:Neck", "head": "mixamorig:Head",
    "upper_arm_l": "mixamorig:LeftArm", "lower_arm_l": "mixamorig:LeftForeArm",
    "hand_l": "mixamorig:LeftHand", "upper_arm_r": "mixamorig:RightArm",
    "lower_arm_r": "mixamorig:RightForeArm", "hand_r": "mixamorig:RightHand",
    "upper_leg_l": "mixamorig:LeftUpLeg", "lower_leg_l": "mixamorig:LeftLeg",
    "foot_l": "mixamorig:LeftFoot", "upper_leg_r": "mixamorig:RightUpLeg",
    "lower_leg_r": "mixamorig:RightLeg", "foot_r": "mixamorig:RightFoot",
}
TARGET_MAPPING = {
    "hips": "pelvis", "spine": "spine", "chest": "chest", "neck": "neck", "head": "head",
    "upper_arm_l": "upper_arm.L", "lower_arm_l": "forearm.L", "hand_l": "hand.L",
    "upper_arm_r": "upper_arm.R", "lower_arm_r": "forearm.R", "hand_r": "hand.R",
    "upper_leg_l": "thigh.L", "lower_leg_l": "shin.L", "foot_l": "foot.L",
    "upper_leg_r": "thigh.R", "lower_leg_r": "shin.R", "foot_r": "foot.R",
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--target-blend", type=Path, required=True)
    parser.add_argument("--skill-script-root", type=Path)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def data_counts():
    return {name: sorted(item.name for item in getattr(bpy.data, name))
            for name in ("objects", "armatures", "meshes", "materials", "actions", "collections")}


def evaluated(obj):
    item = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    return [vertex.co.copy() for vertex in item.vertices]


def point_at(obj, location, target):
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_frames(output, mesh, height, frames=(1, 6, 12)):
    scene = bpy.context.scene
    hidden = {obj: obj.hide_render for obj in scene.objects if obj != mesh}
    for obj in hidden: obj.hide_render = True
    camera_data = bpy.data.cameras.new("GAA M3 Camera")
    camera = bpy.data.objects.new("GAA M3 Camera", camera_data)
    scene.collection.objects.link(camera); scene.camera = camera
    camera_data.type = "ORTHO"; camera_data.ortho_scale = height * 1.10
    light_data = bpy.data.lights.new("GAA M3 Key", "AREA")
    light_data.energy = 900; light_data.size = height * 2
    light = bpy.data.objects.new("GAA M3 Key", light_data); scene.collection.objects.link(light)
    point_at(light, (height * 1.5, -height * 2, height * 2.1), (0, 0, height * 0.5))
    scene.render.engine = "BLENDER_EEVEE"; scene.render.resolution_x = 512
    scene.render.resolution_y = 512; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"; scene.render.film_transparent = True
    result = {}
    for frame in frames:
        scene.frame_set(frame)
        for view, location in {"front": (0, -height * 3.2, height * .51),
                               "side": (height * 3.2, 0, height * .51)}.items():
            point_at(camera, location, (0, 0, height * .5))
            path = output / f"frame-{frame:02d}-{view}.png"
            scene.render.filepath = str(path); bpy.ops.render.render(write_still=True)
            result[f"{frame}-{view}"] = str(path)
    bpy.data.objects.remove(camera, do_unlink=True); bpy.data.cameras.remove(camera_data)
    bpy.data.objects.remove(light, do_unlink=True); bpy.data.lights.remove(light_data)
    for obj, value in hidden.items():
        if obj.name in bpy.data.objects: obj.hide_render = value
    return result


def make_source_fbx(path, target):
    scene = bpy.context.scene
    data = target.data.copy(); data.name = "Synthetic Mixamo Armature"
    source = target.copy(); source.data = data; source.name = "SyntheticMixamoSource"
    source.animation_data_clear(); scene.collection.objects.link(source)
    rename = {target_name: source_name for source_name, target_name in
              ((SOURCE_MAPPING[role], TARGET_MAPPING[role]) for role in SOURCE_MAPPING)}
    for bone in data.bones:
        if bone.name in rename: bone.name = rename[bone.name]
    source.animation_data_create()
    action = bpy.data.actions.new("SyntheticMixamoWalk")
    source.animation_data.action = action
    for frame, phase in ((1, -1.0), (6, 1.0), (12, -1.0)):
        for bone in source.pose.bones:
            bone.rotation_mode = "QUATERNION"; bone.rotation_quaternion = (1, 0, 0, 0)
            bone.location = (0, 0, 0)
        source.pose.bones[SOURCE_MAPPING["upper_arm_l"]].rotation_mode = "XYZ"
        source.pose.bones[SOURCE_MAPPING["upper_arm_r"]].rotation_mode = "XYZ"
        source.pose.bones[SOURCE_MAPPING["upper_leg_l"]].rotation_mode = "XYZ"
        source.pose.bones[SOURCE_MAPPING["upper_leg_r"]].rotation_mode = "XYZ"
        source.pose.bones[SOURCE_MAPPING["lower_leg_l"]].rotation_mode = "XYZ"
        source.pose.bones[SOURCE_MAPPING["lower_leg_r"]].rotation_mode = "XYZ"
        source.pose.bones[SOURCE_MAPPING["upper_arm_l"]].rotation_euler.x = math.radians(24 * phase)
        source.pose.bones[SOURCE_MAPPING["upper_arm_r"]].rotation_euler.x = math.radians(-24 * phase)
        source.pose.bones[SOURCE_MAPPING["upper_leg_l"]].rotation_euler.x = math.radians(-28 * phase)
        source.pose.bones[SOURCE_MAPPING["upper_leg_r"]].rotation_euler.x = math.radians(28 * phase)
        source.pose.bones[SOURCE_MAPPING["lower_leg_l"]].rotation_euler.x = math.radians(28 if phase > 0 else 4)
        source.pose.bones[SOURCE_MAPPING["lower_leg_r"]].rotation_euler.x = math.radians(28 if phase < 0 else 4)
        source.pose.bones[SOURCE_MAPPING["hips"]].location.y = (frame - 1) * -0.01
        for role in ("hips", "upper_arm_l", "upper_arm_r", "upper_leg_l", "upper_leg_r",
                     "lower_leg_l", "lower_leg_r"):
            pose = source.pose.bones[SOURCE_MAPPING[role]]
            pose.keyframe_insert("rotation_quaternion" if pose.rotation_mode == "QUATERNION"
                                 else "rotation_euler", frame=frame)
        source.pose.bones[SOURCE_MAPPING["hips"]].keyframe_insert("location", frame=frame)
    scene.frame_start = 1; scene.frame_end = 12
    for obj in bpy.context.selected_objects: obj.select_set(False)
    source.select_set(True); bpy.context.view_layer.objects.active = source
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={"ARMATURE"},
                             bake_anim=True, bake_anim_use_all_bones=True,
                             bake_anim_use_all_actions=True, bake_anim_simplify_factor=0.0,
                             add_leaf_bones=False, axis_forward="-Z", axis_up="Y")
    source.animation_data.action = None
    bpy.data.actions.remove(action)
    bpy.data.objects.remove(source, do_unlink=True)
    bpy.data.armatures.remove(data)


def main():
    args = parse_args(); output = args.artifact_root
    output.mkdir(parents=True, exist_ok=False)
    if args.skill_script_root is None:
        sys.path.insert(0, str(args.repo_root / "scripts"))
    script_root = args.skill_script_root or args.repo_root / "skills" / "blender-import-humanoid-animation" / "scripts"
    sys.path.insert(0, str(script_root))
    from export_mixamo_handoff import export_mixamo_handoff
    from import_humanoid_animation import import_and_retarget

    scene = bpy.context.scene
    target = scene.objects["GAA M2 Compact Rig"]
    mesh = scene.objects["GAA M2 Compact Mesh Object"]
    target.animation_data_clear()
    for pose in target.pose.bones:
        pose.rotation_mode = "QUATERNION"; pose.rotation_quaternion = (1, 0, 0, 0)
        pose.location = (0, 0, 0); pose.scale = (1, 1, 1)
    scene.frame_set(1); bpy.context.view_layer.update()
    source_fbx = output / "synthetic-mixamo-walk.fbx"
    make_source_fbx(source_fbx, target)
    handoff = export_mixamo_handoff(scene.name, mesh.name, target.name,
                                    str(output / "m2-compact-mixamo-handoff.fbx"), authorized=True)
    source_sha = hashlib.sha256(source_fbx.read_bytes()).hexdigest()
    request = {
        "schema": "gameassetai.humanoid-animation-import-request.v1", "scene_name": scene.name,
        "source_fbx": {"path": str(source_fbx), "sha256": source_sha, "format": "FBX",
                       "expected_armature_name": None, "expected_action_name": None,
                       "mixamo_prefix": "mixamorig:"},
        "target": {"armature_name": target.name, "mesh_object_name": mesh.name,
                   "result_action_name": "GAA M3 Synthetic Walk",
                   "import_collection_name": "GAA M3 Imported Source"},
        "source_mapping": SOURCE_MAPPING, "target_mapping": TARGET_MAPPING,
        "frame": {"start": 1, "end": 12, "step": 1, "fps": 30},
        "root_motion": {"policy": "IN_PLACE", "axis_mask": [False, False, False],
                        "translation_scale": 1.0},
        "policy": {"source_import": "KEEP_OWNED_COLLECTION", "target_animation": "EMPTY_ONLY",
                   "result_action": "NEW_BOUND_ACTION", "preserve_sources": True,
                   "overwrite": False, "failure": "ROLL_BACK_NEW_DATA"},
    }
    baseline = data_counts()
    bad = json.loads(json.dumps(request)); bad["source_mapping"]["head"] = "mixamorig:MissingHead"
    rollback = False
    rollback_error = None
    try:
        import_and_retarget(bad, authorized=True)
    except ValueError as error:
        rollback_error = str(error)
        rollback = "source explicit Humanoid mapping" in str(error)
    after_failed_import = data_counts()
    if not rollback or after_failed_import != baseline or target.animation_data is not None:
        raise AssertionError("failed imported mapping did not restore the exact baseline: " +
                             json.dumps({"rollback": rollback,
                                         "before": baseline,
                                         "after": after_failed_import,
                                         "error": rollback_error,
                                         "target_animation": target.animation_data is not None},
                                        sort_keys=True))
    rest = evaluated(mesh)
    receipt = import_and_retarget(request, authorized=True)
    scene.frame_set(1); bpy.context.view_layer.update(); pose1 = evaluated(mesh)
    scene.frame_set(6); bpy.context.view_layer.update(); pose6 = evaluated(mesh)
    scene.frame_set(12); bpy.context.view_layer.update(); pose12 = evaluated(mesh)
    change_1_6 = max((a-b).length for a,b in zip(pose1, pose6))
    change_6_12 = max((a-b).length for a,b in zip(pose6, pose12))
    if min(change_1_6, change_6_12) < 0.03:
        raise AssertionError("retargeted Action did not visibly deform the target Mesh")
    images = render_frames(output, mesh, 1.58)
    blend = output / "m3-synthetic-retarget.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    report = {"schema": "gameassetai.humanoid-animation-import-validation.v1",
              "status": "pass", "source_kind": "synthetic_mixamo_signature_fbx",
              "mixamo_service_round_trip": False, "receipt": receipt, "handoff": handoff,
              "rollback_after_import": rollback, "mesh_displacement_1_6": change_1_6,
              "mesh_displacement_6_12": change_6_12, "images": images,
              "blend": str(blend), "source_fbx": str(source_fbx),
              "blender_version": bpy.app.version_string}
    report["report_sha256"] = hashlib.sha256(canonical(report).encode()).hexdigest()
    report_path = output / "m3-validation.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("GAMEASSETAI_M3 " + json.dumps({"status": "pass", "report": str(report_path),
          "blend": str(blend), "displacements": [change_1_6, change_6_12]}))


if __name__ == "__main__":
    main()
