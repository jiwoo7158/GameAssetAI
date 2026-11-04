import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--base-report", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def landmarks(height, depth):
    result = {
        "root": [0, 0, 0], "pelvis": [0, 0, height * 0.50],
        "spine": [0, 0, height * 0.61], "chest": [0, 0, height * 0.71],
        "neck": [0, 0, height * 0.79], "head_top": [0, 0, height * 1.0],
    }
    for side, sign in (("L", 1.0), ("R", -1.0)):
        result.update({
            f"shoulder.{side}": [sign * height * 0.120, 0, height * 0.765],
            f"elbow.{side}": [sign * height * 0.180, 0, height * 0.665],
            f"wrist.{side}": [sign * height * 0.235, 0, height * 0.575],
            f"hand_tip.{side}": [sign * height * 0.275, 0, height * 0.545],
            f"hip.{side}": [sign * height * 0.066, 0, height * 0.505],
            f"knee.{side}": [sign * height * 0.066, 0, height * 0.300],
            f"ankle.{side}": [sign * height * 0.066, 0, height * 0.072],
            f"toe.{side}": [sign * height * 0.066, -depth * 0.62, height * 0.025],
        })
    return result


def main():
    options = args()
    report = json.loads(options.base_report.read_text(encoding="utf-8"))
    sys.path.insert(0, str(options.repo_root / "scripts"))
    sys.path.insert(0, str(options.repo_root / "tests" / "blender_addon"))
    import rig_character_base
    from run_humanoid_rig_adaptation import evaluated_coordinates, joint_quality, mesh_facts, render_views

    obj = bpy.data.objects[report["revision_receipt"]["object_name"]]
    original = mesh_facts(obj)
    height = max(vertex.co.z for vertex in obj.data.vertices) - min(vertex.co.z for vertex in obj.data.vertices)
    depth = max(vertex.co.y for vertex in obj.data.vertices) - min(vertex.co.y for vertex in obj.data.vertices)
    request = {
        "schema": "gameassetai.character-rig-request.v3", "scene_name": bpy.context.scene.name,
        "mesh_object_name": obj.name, "armature_object_name": "GAA B6 SD Revised Rig",
        "armature_data_name": "GAA B6 SD Revised Armature", "rig_name": "GAA B6 SD Revised",
        "fitting": {"mode": "EXPLICIT_LANDMARKS", "pose": "A_POSE", "front_axis": "-Y",
                    "coordinate_space": "OBJECT_LOCAL", "landmarks": landmarks(height, depth),
                    "transition_width_ratio": 0.05, "max_influences": 4},
        "policy": {"target": "EXPLICIT_HUMANOID_MESH", "existing_rig": "REFUSE",
                   "weights": "LANDMARK_ENVELOPE_V3", "source_mesh": "PRESERVE_GEOMETRY_AND_UV",
                   "failure": "ROLL_BACK_RIG_CHANGES"},
    }
    receipt = rig_character_base.create_rig(request, authorized=True)
    armature = bpy.data.objects[receipt["armature_object_name"]]
    preserved = mesh_facts(obj)
    failures = []
    if preserved["coordinates"] != original["coordinates"] or preserved["uv"] != original["uv"]:
        failures.append("rig changed source coordinates or UV")
    rest = evaluated_coordinates(obj)
    preview = options.artifact_root / "rig-previews"
    preview.mkdir(exist_ok=False)
    rest_images = render_views(preview, "rest", obj, height)
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
    armature.pose.bones["upper_arm.L"].rotation_euler.x = math.radians(-22)
    armature.pose.bones["forearm.L"].rotation_euler.z = math.radians(-62)
    armature.pose.bones["thigh.R"].rotation_euler.x = math.radians(-27)
    armature.pose.bones["shin.R"].rotation_euler.x = math.radians(56)
    bpy.context.view_layer.update()
    posed = evaluated_coordinates(obj)
    posed_images = render_views(preview, "posed", obj, height)
    joints = {
        "left_shoulder": joint_quality(obj, rest, posed, "chest", "upper_arm.L"),
        "left_elbow": joint_quality(obj, rest, posed, "upper_arm.L", "forearm.L"),
        "right_hip": joint_quality(obj, rest, posed, "pelvis", "thigh.R"),
        "right_knee": joint_quality(obj, rest, posed, "thigh.R", "shin.R"),
    }
    for name, facts in joints.items():
        if not facts["blended_vertices"] or facts["minimum_area_ratio"] is None:
            failures.append(name + " lacks measurable blended deformation")
        elif facts["minimum_area_ratio"] < 0.08:
            failures.append(name + " has severe local face compression")
    if receipt["weight_validation"]["maximum_weight_sum_error"] > 1e-6:
        failures.append("weights are not normalized")
    if receipt["weight_validation"]["cross_side_influence_count"]:
        failures.append("cross-side influences exist")
    blend = options.artifact_root / "b6-1-stylized-sd-character-rigged.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    result = {
        "schema": "gameassetai.character-b6-rig-gate.v1",
        "status": "structural_pass_visual_review_required" if not failures else "failed",
        "failures": failures, "request": request, "receipt": receipt, "joint_quality": joints,
        "source_geometry_uv_preserved": preserved["coordinates"] == original["coordinates"] and preserved["uv"] == original["uv"],
        "rest_images": rest_images, "posed_images": posed_images,
        "images": {**{"rest_" + k: v for k, v in rest_images.items()},
                   **{"posed_" + k: v for k, v in posed_images.items()}},
        "required_visual_checks": ["shoulder_deformation", "elbow_deformation", "hip_deformation",
                                   "knee_deformation", "no_cross_side_collapse", "styled_silhouette_retained"],
        "blend": str(blend), "blender_version": bpy.app.version_string,
    }
    result["report_sha256"] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    output = options.artifact_root / "rig-validation.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if failures:
        raise AssertionError("; ".join(failures))
    print("GAMEASSETAI_B6_RIG_GATE " + json.dumps({"status": result["status"], "report": str(output), "blend": str(blend)}))


if __name__ == "__main__":
    main()
