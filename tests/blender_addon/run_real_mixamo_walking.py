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
    parser.add_argument("--source-fbx", type=Path, required=True)
    parser.add_argument("--skill-script-root", type=Path, required=True)
    parser.add_argument("--require-external-inputs", action="store_true")
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def main():
    args = parse_args()
    missing = []
    if not args.source_fbx.is_file():
        missing.append(f"source FBX is absent: {args.source_fbx}")
    if not (args.skill_script_root / "import_humanoid_animation.py").is_file():
        missing.append(f"installed/source Skill script is absent: {args.skill_script_root}")
    for name in ("GAA M2 Compact Rig", "GAA M2 Compact Mesh Object"):
        if bpy.context.scene.objects.get(name) is None:
            missing.append(f"loaded external target is absent: {name}")
    if missing:
        result = {"status": "skipped_external_input_unavailable", "reasons": missing}
        print("GAMEASSETAI_REAL_MIXAMO " + json.dumps(result))
        if args.require_external_inputs:
            raise FileNotFoundError("; ".join(missing))
        return
    if args.artifact_root.exists():
        manifest = args.artifact_root / "manifest.json"
        if not manifest.is_file():
            raise FileExistsError("existing artifact root is not a managed run")
        identity = json.loads(manifest.read_text(encoding="utf-8"))
        if (identity.get("schema") != "gameassetai.artifact-run.v1"
                or identity.get("run_id") != args.artifact_root.name):
            raise ValueError("artifact run manifest identity is invalid")
    else:
        args.artifact_root.mkdir(parents=True)
    sys.path.insert(0, str(args.skill_script_root))
    sys.path.insert(0, str(args.repo_root / "tests" / "blender_addon"))
    from import_humanoid_animation import import_and_retarget
    from run_humanoid_animation_import import canonical, evaluated, render_frames

    source_sha = hashlib.sha256(args.source_fbx.read_bytes()).hexdigest()
    scene = bpy.context.scene
    target = scene.objects["GAA M2 Compact Rig"]
    mesh = scene.objects["GAA M2 Compact Mesh Object"]
    if target.animation_data and (target.animation_data.action or target.animation_data.nla_tracks
                                  or target.animation_data.drivers):
        raise AssertionError("M2 target is not animation-empty")
    for pose_bone in target.pose.bones:
        pose_bone.rotation_mode = "QUATERNION"
        pose_bone.rotation_quaternion = (1, 0, 0, 0)
        pose_bone.location = (0, 0, 0)
        pose_bone.scale = (1, 1, 1)

    request = {
        "schema": "gameassetai.humanoid-animation-import-request.v1",
        "scene_name": scene.name,
        "source_fbx": {
            "path": str(args.source_fbx), "sha256": source_sha, "format": "FBX",
            "expected_armature_name": "Armature",
            "expected_action_name": "Armature|mixamo.com|Layer0",
            "mixamo_prefix": "mixamorig:",
        },
        "target": {
            "armature_name": target.name, "mesh_object_name": mesh.name,
            "result_action_name": "GAA M3 Mixamo Walking",
            "import_collection_name": "GAA M3 Real Mixamo Source",
        },
        "source_mapping": SOURCE_MAPPING, "target_mapping": TARGET_MAPPING,
        "frame": {"start": 1, "end": 32, "step": 1, "fps": 30},
        "root_motion": {"policy": "IN_PLACE", "axis_mask": [False, False, False],
                        "translation_scale": 1.0},
        "policy": {"source_import": "KEEP_OWNED_COLLECTION",
                   "target_animation": "EMPTY_ONLY", "result_action": "NEW_BOUND_ACTION",
                   "preserve_sources": True, "overwrite": False,
                   "failure": "ROLL_BACK_NEW_DATA"},
    }
    rest = evaluated(mesh)
    receipt = import_and_retarget(request, authorized=True)
    source = bpy.data.objects[receipt["source_armature"]]
    samples = {}
    poses = {}
    direction_errors = {}
    direction_roles = ("spine", "head", "upper_arm_l", "lower_arm_l", "upper_arm_r",
                       "lower_arm_r", "upper_leg_l", "lower_leg_l", "foot_l",
                       "upper_leg_r", "lower_leg_r", "foot_r")
    review_frames = (1, 8, 16, 24, 32)
    all_frame_clearance = {}
    all_frame_bounds_diagonal = {}
    for frame in range(1, 33):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        evaluated_vertices = evaluated(mesh)
        if not all(math.isfinite(value) for vertex in evaluated_vertices for value in vertex):
            raise AssertionError(f"non-finite evaluated Mesh coordinate at frame {frame}")
        low = Vector(tuple(min(vertex[index] for vertex in evaluated_vertices) for index in range(3)))
        high = Vector(tuple(max(vertex[index] for vertex in evaluated_vertices) for index in range(3)))
        all_frame_bounds_diagonal[str(frame)] = (high - low).length
        if frame in review_frames:
            poses[frame] = evaluated_vertices
            samples[str(frame)] = max((a - b).length for a, b in zip(rest, poses[frame]))
        direction_errors[str(frame)] = {}
        for role in direction_roles:
            source_direction = (source.matrix_world.to_3x3() @
                                source.pose.bones[SOURCE_MAPPING[role]].matrix.to_3x3() @
                                Vector((0.0, 1.0, 0.0))).normalized()
            target_direction = (target.matrix_world.to_3x3() @
                                target.pose.bones[TARGET_MAPPING[role]].matrix.to_3x3() @
                                Vector((0.0, 1.0, 0.0))).normalized()
            direction_errors[str(frame)][role] = source_direction.angle(target_direction)
        all_frame_clearance[str(frame)] = {
            "hand_separation": abs(target.pose.bones["hand.L"].head.x -
                                   target.pose.bones["hand.R"].head.x),
            "foot_separation": abs(target.pose.bones["foot.L"].head.x -
                                   target.pose.bones["foot.R"].head.x),
        }
    maximum_direction_error = max(value for frame in direction_errors.values()
                                  for value in frame.values())
    if maximum_direction_error > 0.05:
        raise AssertionError(f"mapped joint direction error is too large: {maximum_direction_error}")
    minimum_hand_separation = min(item["hand_separation"] for item in all_frame_clearance.values())
    minimum_foot_separation = min(item["foot_separation"] for item in all_frame_clearance.values())
    if minimum_hand_separation < 0.10 or minimum_foot_separation < 0.05:
        raise AssertionError("left/right limb clearance collapsed during the Action")
    changes = {f"{left}_{right}": max((a - b).length for a, b in zip(poses[left], poses[right]))
               for left, right in zip(review_frames, review_frames[1:])}
    if min(changes.values()) < 0.01:
        raise AssertionError("real Mixamo Action did not visibly change the target Mesh")
    side_clearance = {}
    for frame in review_frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        side_clearance[str(frame)] = {
            "hands_x": [target.pose.bones["hand.L"].head.x,
                        target.pose.bones["hand.R"].head.x],
            "feet_x": [target.pose.bones["foot.L"].head.x,
                       target.pose.bones["foot.R"].head.x],
        }
        side_clearance[str(frame)]["hand_separation"] = abs(
            side_clearance[str(frame)]["hands_x"][0] - side_clearance[str(frame)]["hands_x"][1])
        side_clearance[str(frame)]["foot_separation"] = abs(
            side_clearance[str(frame)]["feet_x"][0] - side_clearance[str(frame)]["feet_x"][1])
    preview_root = args.artifact_root / "previews"
    preview_root.mkdir(exist_ok=True)
    images = render_frames(preview_root, mesh, 1.58, frames=review_frames,
                           views=("front", "side", "three_quarter"))
    blend_path = args.artifact_root / "m3-real-mixamo-walking.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    report = {
        "schema": "gameassetai.real-mixamo-walking-validation.v1",
        "status": "structural_pass_visual_review_required",
        "source_fbx": str(args.source_fbx), "source_fbx_sha256": source_sha,
        "mixamo_service_download_user_supplied": True,
        "checks": {"import_mapping": "pass", "action_binding": "pass",
                   "source_target_preservation": "pass", "retarget_motion": "pass",
                   "visual_quality": "pending_review"},
        "receipt": receipt, "mesh_displacement_from_rest": samples,
        "mesh_displacement_between_samples": changes, "images": images,
        "left_right_joint_clearance": side_clearance,
        "joint_direction_error_radians": direction_errors,
        "maximum_joint_direction_error_radians": maximum_direction_error,
        "all_frame_clearance": all_frame_clearance,
        "minimum_hand_separation": minimum_hand_separation,
        "minimum_foot_separation": minimum_foot_separation,
        "all_frame_bounds_diagonal": all_frame_bounds_diagonal,
        "blend": str(blend_path), "blender_version": bpy.app.version_string,
    }
    report["report_sha256"] = hashlib.sha256(canonical(report).encode()).hexdigest()
    report_path = args.artifact_root / "m3-real-mixamo-validation.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("GAMEASSETAI_REAL_MIXAMO " + json.dumps({
          "status": "automatic_pass_visual_review_required",
          "report": str(report_path), "blend": str(blend_path), "changes": changes}))


if __name__ == "__main__":
    main()
