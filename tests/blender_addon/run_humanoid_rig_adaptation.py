import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--source-blend", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--case", choices=("compact", "lanky"), required=True)
    parser.add_argument("--rig-script-root", type=Path)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def mesh_facts(obj):
    mesh = obj.data
    return {
        "coordinates": [[float(value) for value in vertex.co] for vertex in mesh.vertices],
        "uv": ([[float(value) for value in loop.uv] for loop in mesh.uv_layers.active.data]
               if mesh.uv_layers and mesh.uv_layers.active else None),
        "modifiers": [modifier.name for modifier in obj.modifiers],
        "groups": [group.name for group in obj.vertex_groups],
    }


def evaluated_coordinates(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [vertex.co.copy() for vertex in evaluated.to_mesh().vertices]


def face_area(points, polygon):
    vertices = [points[index] for index in polygon.vertices]
    origin = vertices[0]
    return sum((vertices[index] - origin).cross(vertices[index + 1] - origin).length * 0.5
               for index in range(1, len(vertices) - 1))


def joint_quality(obj, rest, posed, first, second):
    groups = {group.name: group.index for group in obj.vertex_groups}
    selected = []
    for vertex in obj.data.vertices:
        values = {group.group: group.weight for group in vertex.groups}
        if values.get(groups[first], 0.0) > 0.05 and values.get(groups[second], 0.0) > 0.05:
            selected.append(vertex.index)
    selected = set(selected)
    ratios = []
    for polygon in obj.data.polygons:
        if selected.intersection(polygon.vertices):
            before = face_area(rest, polygon)
            if before > 1e-12:
                ratios.append(face_area(posed, polygon) / before)
    ratios.sort()
    return {"blended_vertices": len(selected), "affected_faces": len(ratios),
            "minimum_area_ratio": ratios[0] if ratios else None,
            "median_area_ratio": ratios[len(ratios) // 2] if ratios else None}


def point_at(obj, location, target):
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_views(output, label, target, height):
    scene = bpy.context.scene
    hidden = {obj: obj.hide_render for obj in scene.objects if obj != target}
    for obj in hidden:
        obj.hide_render = True
    camera_data = bpy.data.cameras.new("GAA M2 Camera")
    camera = bpy.data.objects.new("GAA M2 Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = height * 1.10
    light_data = bpy.data.lights.new("GAA M2 Key", "AREA")
    light_data.energy = 900
    light_data.size = height * 2.0
    light = bpy.data.objects.new("GAA M2 Key", light_data)
    scene.collection.objects.link(light)
    point_at(light, (height * 1.5, -height * 2.0, height * 2.1), (0, 0, height * 0.5))
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    views = {"front": (0, -height * 3.2, height * 0.51),
             "side": (height * 3.2, 0, height * 0.51),
             "three-quarter": (height * 2.35, -height * 2.35, height * 0.54)}
    paths = {}
    for name, location in views.items():
        point_at(camera, location, (0, 0, height * 0.5))
        path = output / f"{label}-{name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        paths[name] = str(path)
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)
    bpy.data.objects.remove(light, do_unlink=True)
    bpy.data.lights.remove(light_data)
    for obj, value in hidden.items():
        if obj.name in bpy.data.objects:
            obj.hide_render = value
    return paths


def landmarks(case, height, depth):
    arm_x = ((0.120, 0.195, 0.255, 0.290) if case == "compact"
             else (0.082, 0.132, 0.174, 0.198))
    leg_x = 0.070 if case == "compact" else 0.047
    result = {
        "root": [0, 0, 0], "pelvis": [0, 0, height * 0.50],
        "spine": [0, 0, height * 0.62], "chest": [0, 0, height * 0.72],
        "neck": [0, 0, height * 0.825], "head_top": [0, 0, height * 0.98],
    }
    for side, sign in (("L", 1.0), ("R", -1.0)):
        result.update({
            f"shoulder.{side}": [sign * height * arm_x[0], 0, height * 0.785],
            f"elbow.{side}": [sign * height * arm_x[1], 0, height * 0.675],
            f"wrist.{side}": [sign * height * arm_x[2], 0, height * 0.565],
            f"hand_tip.{side}": [sign * height * arm_x[3], 0, height * 0.525],
            f"hip.{side}": [sign * height * leg_x, 0, height * 0.515],
            f"knee.{side}": [sign * height * leg_x, 0, height * 0.305],
            f"ankle.{side}": [sign * height * leg_x, 0, height * 0.075],
            f"toe.{side}": [sign * height * leg_x, -depth * 0.62, height * 0.025],
        })
    return result


def main():
    args = parse_args()
    output = args.artifact_root / args.case
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.repo_root / "scripts"))
    from create_character_base import create_character
    if args.rig_script_root:
        sys.path.insert(0, str(args.rig_script_root))
    import rig_character_base as rig_module

    profiles = {
        "compact": {"height": 1.58, "shoulder_width_ratio": 0.39, "hip_width_ratio": 0.27,
                    "body_depth_ratio": 0.19, "limb_thickness_ratio": 0.067,
                    "head_height_ratio": 0.19},
        "lanky": {"height": 1.96, "shoulder_width_ratio": 0.29, "hip_width_ratio": 0.19,
                  "body_depth_ratio": 0.13, "limb_thickness_ratio": 0.043,
                  "head_height_ratio": 0.15},
    }
    p = profiles[args.case]
    source_sha = hashlib.sha256(args.source_blend.read_bytes()).hexdigest()
    prefix = "GAA M2 " + args.case.title()
    character_request = {
        "schema": "gameassetai.character-base-request.v4", "scene_name": "Scene",
        "character_name": prefix, "collection_name": prefix + " Collection",
        "object_name": prefix + " Mesh Object", "mesh_name": prefix + " Mesh",
        "pose": "A_POSE", "topology_mode": "DEFORMATION_TEMPLATE",
        "template": {"source_file": str(args.source_blend), "source_sha256": source_sha,
                     "mesh_name": "GEO-body_male_stylized",
                     "source_name": "Blender Studio Human Base Meshes",
                     "source_version": "1.4.1", "license": "CC0-1.0", "front_axis": "-Y"},
        "proportions": p,
        "colors": {"skin": [0.72, 0.42, 0.28, 1], "primary": [0.18, 0.36, 0.58, 1],
                   "secondary": [0.12, 0.52, 0.48, 1], "boots": [0.05, 0.04, 0.04, 1]},
        "policy": {"existing_names": "REFUSE", "source_scene": "PRESERVE",
                   "creation": "NEW_SINGLE_MESH_CHARACTER", "failure": "ROLL_BACK_OWNED_DATA",
                   "rigging": "NOT_INCLUDED"},
    }
    character = create_character(character_request, authorized=True)
    obj = bpy.data.objects[character["object_name"]]
    original = mesh_facts(obj)
    fitting = {"mode": "EXPLICIT_LANDMARKS", "pose": "A_POSE", "front_axis": "-Y",
               "coordinate_space": "OBJECT_LOCAL",
               "landmarks": landmarks(args.case, p["height"], p["height"] * p["body_depth_ratio"]),
               "transition_width_ratio": 0.045, "max_influences": 4}
    rig_request = {
        "schema": "gameassetai.character-rig-request.v3", "scene_name": "Scene",
        "mesh_object_name": obj.name, "armature_object_name": prefix + " Rig",
        "armature_data_name": prefix + " Armature", "rig_name": prefix,
        "fitting": fitting,
        "policy": {"target": "EXPLICIT_HUMANOID_MESH", "existing_rig": "REFUSE",
                   "weights": "LANDMARK_ENVELOPE_V3",
                   "source_mesh": "PRESERVE_GEOMETRY_AND_UV",
                   "failure": "ROLL_BACK_RIG_CHANGES"},
    }

    baseline_objects = sorted(bpy.data.objects.keys())
    baseline_armatures = sorted(bpy.data.armatures.keys())
    original_fingerprint = rig_module._mesh_fingerprints
    calls = 0
    def fail_after_weighting(mesh):
        nonlocal calls
        calls += 1
        result = original_fingerprint(mesh)
        if calls > 1:
            result = dict(result); result["geometry_sha256"] = "0" * 64
        return result
    rig_module._mesh_fingerprints = fail_after_weighting
    rollback_refused = False
    try:
        rig_module.create_rig(rig_request, authorized=True)
    except RuntimeError as error:
        rollback_refused = "source Mesh coordinates or UV changed" in str(error)
    finally:
        rig_module._mesh_fingerprints = original_fingerprint
    if (not rollback_refused or sorted(bpy.data.objects.keys()) != baseline_objects
            or sorted(bpy.data.armatures.keys()) != baseline_armatures
            or mesh_facts(obj) != original):
        raise AssertionError("post-weight failure did not exactly restore rig target state")

    receipt = rig_module.create_rig(rig_request, authorized=True)
    armature = bpy.data.objects[receipt["armature_object_name"]]
    preserved = mesh_facts(obj)
    if preserved["coordinates"] != original["coordinates"] or preserved["uv"] != original["uv"]:
        raise AssertionError("rig adaptation changed source coordinates or UV")
    rest = evaluated_coordinates(obj)
    rest_images = render_views(output, "rest", obj, p["height"])
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
    armature.pose.bones["upper_arm.L"].rotation_euler.x = math.radians(-24)
    armature.pose.bones["forearm.L"].rotation_euler.z = math.radians(-68)
    armature.pose.bones["thigh.R"].rotation_euler.x = math.radians(-30)
    armature.pose.bones["shin.R"].rotation_euler.x = math.radians(62)
    bpy.context.view_layer.update()
    posed = evaluated_coordinates(obj)
    posed_images = render_views(output, "posed", obj, p["height"])
    joints = {
        "left_elbow": joint_quality(obj, rest, posed, "upper_arm.L", "forearm.L"),
        "right_knee": joint_quality(obj, rest, posed, "thigh.R", "shin.R"),
        "left_shoulder": joint_quality(obj, rest, posed, "chest", "upper_arm.L"),
        "right_hip": joint_quality(obj, rest, posed, "pelvis", "thigh.R"),
    }
    failures = []
    for name, facts in joints.items():
        if not facts["blended_vertices"]:
            failures.append(name + " has no blended neighborhood")
        if facts["minimum_area_ratio"] is None or facts["minimum_area_ratio"] < 0.08:
            failures.append(name + " has severe local face compression")
    if receipt["weight_validation"]["maximum_weight_sum_error"] > 1e-6:
        failures.append("weight sums are not normalized")
    if receipt["weight_validation"]["cross_side_influence_count"]:
        failures.append("cross-side influences exist")
    if hashlib.sha256(args.source_blend.read_bytes()).hexdigest() != source_sha:
        failures.append("external source changed")
    blend_path = output / f"{args.case}-m2-rig-adaptation.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    report = {"schema": "gameassetai.humanoid-rig-adaptation-validation.v1",
              "status": "pass" if not failures else "failed", "case": args.case,
              "failures": failures, "character_receipt": character, "rig_receipt": receipt,
              "joint_quality": joints, "source_preserved": True,
              "rollback_after_weighting": rollback_refused,
              "rest_images": rest_images, "posed_images": posed_images,
              "blend": str(blend_path), "blender_version": bpy.app.version_string,
              "m1_baseline": ({"left_elbow": 0.6460647533230921,
                               "right_knee": 0.11426954421820022}
                              if args.case == "compact" else
                              {"left_elbow": 0.7983384350239472,
                               "right_knee": 0.05232755160471957})}
    report["report_sha256"] = hashlib.sha256(canonical(report).encode()).hexdigest()
    report_path = output / f"{args.case}-m2-validation.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("GAMEASSETAI_M2_RIG " + json.dumps({"status": report["status"], "case": args.case,
          "report": str(report_path), "blend": str(blend_path), "joints": joints}))
    if failures:
        raise AssertionError("; ".join(failures))


if __name__ == "__main__":
    main()
