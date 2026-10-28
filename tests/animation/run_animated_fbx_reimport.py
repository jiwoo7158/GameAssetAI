"""Fresh-process Blender round-trip validation for one M4 animated FBX."""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--fbx", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def evaluated_vertices(mesh):
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    temporary = evaluated.to_mesh()
    try:
        return [mesh.matrix_world @ vertex.co for vertex in temporary.vertices]
    finally:
        evaluated.to_mesh_clear()


def main():
    options = args()
    receipt = json.loads(options.receipt.read_text(encoding="utf-8"))
    scene = bpy.context.scene
    scene.render.fps = receipt["fps"]
    before_objects = set(bpy.data.objects)
    before_actions = set(bpy.data.actions)
    outcome = bpy.ops.import_scene.fbx(filepath=str(options.fbx), use_anim=True,
                                       anim_offset=1.0, automatic_bone_orientation=False)
    if "FINISHED" not in outcome:
        raise RuntimeError("FBX import did not finish")
    objects = [obj for obj in bpy.data.objects if obj not in before_objects]
    actions = [action for action in bpy.data.actions if action not in before_actions]
    meshes = [obj for obj in objects if obj.type == "MESH"]
    rigs = [obj for obj in objects if obj.type == "ARMATURE"]
    if len(meshes) != 1 or len(rigs) != 1 or not actions:
        raise AssertionError({"meshes": [o.name for o in meshes], "rigs": [o.name for o in rigs],
                              "actions": [a.name for a in actions]})
    mesh, rig = meshes[0], rigs[0]
    action = rig.animation_data.action if rig.animation_data else None
    if action is None or action not in actions:
        raise AssertionError("imported Armature has no imported current Action")
    start, end = map(float, action.frame_range)
    if abs(start - receipt["frame_start"]) > 1e-4 or abs(end - receipt["frame_end"]) > 1e-4:
        raise AssertionError(f"Action range mismatch: {start}, {end}")
    modifiers = [mod for mod in mesh.modifiers if mod.type == "ARMATURE" and mod.object == rig]
    required = receipt["validation_bones"]
    if (len(modifiers) != 1 or not mesh.vertex_groups or not mesh.data.uv_layers
            or any(rig.pose.bones.get(name) is None for name in required)):
        raise AssertionError("reimported skin/UV/bones are incomplete")
    samples, signatures = {}, {}
    max_joint_head_error = 0.0
    max_bone_tail_error = 0.0
    max_vertex_sample_error = 0.0
    max_bounds_error = 0.0
    for frame in (receipt["frame_start"],
                  (receipt["frame_start"] + receipt["frame_end"]) // 2,
                  receipt["frame_end"]):
        scene.frame_set(frame); bpy.context.view_layer.update()
        vertices = evaluated_vertices(mesh)
        if not all(math.isfinite(value) for point in vertices for value in point):
            raise AssertionError("non-finite evaluated vertex")
        samples[frame] = vertices
        low = [min(point[index] for point in vertices) for index in range(3)]
        high = [max(point[index] for point in vertices) for index in range(3)]
        signature = receipt["pose_signature"][str(frame)]
        for name in required:
            pose = rig.pose.bones[name]
            actual_head = rig.matrix_world @ pose.head
            actual_tail = rig.matrix_world @ pose.tail
            max_joint_head_error = max(
                max_joint_head_error,
                (actual_head - Vector(signature["bones"][name]["head"])).length)
            max_bone_tail_error = max(
                max_bone_tail_error,
                (actual_tail - Vector(signature["bones"][name]["tail"])).length)
        for index, expected in signature["vertex_samples"].items():
            max_vertex_sample_error = max(
                max_vertex_sample_error,
                (vertices[int(index)] - Vector(expected)).length)
        max_bounds_error = max(max_bounds_error,
                               max(abs(low[index] - signature["bounds_min"][index]) for index in range(3)),
                               max(abs(high[index] - signature["bounds_max"][index]) for index in range(3)))
        signatures[str(frame)] = {"bounds_min": low, "bounds_max": high}
    movement = max((left - right).length for left, right in
                   zip(samples[receipt["frame_start"]], samples[receipt["frame_end"]]))
    if (movement < 0.01 or max_joint_head_error > 0.01
            or max_vertex_sample_error > 0.01 or max_bounds_error > 0.02):
        raise AssertionError({"movement": movement,
                              "joint_head_error": max_joint_head_error,
                              "bone_tail_error": max_bone_tail_error,
                              "vertex_sample_error": max_vertex_sample_error,
                              "bounds_error": max_bounds_error})
    sys.path.insert(0, str(options.repo_root / "tests" / "blender_addon"))
    from run_humanoid_animation_import import render_frames
    points = samples[receipt["frame_start"]]
    height = max(point.z for point in points) - min(point.z for point in points)
    previews = render_frames(options.run_directory / "previews", mesh, height,
                             frames=(1, 12, 24), views=("front", "side"))
    blend = options.run_directory / "m4-animated-fbx-reimport.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    report = {"schema": "gameassetai.animated-fbx-blender-roundtrip.v1", "status": "pass",
              "fbx": str(options.fbx), "mesh": mesh.name, "armature": rig.name,
              "action": action.name, "frame_range": [start, end], "fps": scene.render.fps,
              "bone_count": len(rig.data.bones), "vertex_groups": len(mesh.vertex_groups),
              "uv_layers": len(mesh.data.uv_layers), "material_slots": len(mesh.material_slots),
              "evaluated_mesh_movement": movement,
              "maximum_joint_head_error": max_joint_head_error,
              "maximum_bone_tail_error": max_bone_tail_error,
              "maximum_vertex_sample_error": max_vertex_sample_error,
              "maximum_bounds_error": max_bounds_error, "previews": previews,
              "blend": str(blend), "blender_version": bpy.app.version_string}
    output = options.run_directory / "blender-reimport-validation.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("GAMEASSETAI_ANIMATED_FBX_REIMPORT " + json.dumps(
        {"status": "pass", "report": str(output), "blend": str(blend),
         "movement": movement, "joint_head_error": max_joint_head_error,
         "bone_tail_error": max_bone_tail_error,
         "vertex_sample_error": max_vertex_sample_error,
         "bounds_error": max_bounds_error}, sort_keys=True))


if __name__ == "__main__":
    main()
