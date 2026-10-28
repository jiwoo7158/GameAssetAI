"""Focused Blender fixture for evaluated game-Action preparation."""
import argparse
import json
import sys
from pathlib import Path

import bpy


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--skills-root", type=Path)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def load_api(repo, skills_root=None):
    skills = skills_root or (repo / "skills")
    namespace = {"__name__": "gameassetai_prepare_game_action_test"}
    for path in (skills / "blender-inspect-animation" / "scripts" /
                 "inspect_animation.py",
                 skills / "blender-copy-action" / "scripts" / "action_copy.py",
                 skills / "blender-prepare-game-action" / "scripts" /
                 "prepare_game_action.py"):
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace, namespace)
    return namespace


def main():
    options = args()
    api = load_api(options.repo_root, options.skills_root)
    before = {name: sorted(item.name for item in getattr(bpy.data, name))
              for name in ("objects", "armatures", "meshes", "actions", "scenes")}
    scene = bpy.data.scenes.new("GAA_ActionPrepare_Focused")
    armature = bpy.data.armatures.new("GAA_ActionPrepareData_Focused")
    rig = bpy.data.objects.new("GAA_ActionPrepareRig_Focused", armature)
    scene.collection.objects.link(rig)
    bpy.context.window.scene = scene
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    root = armature.edit_bones.new("root")
    root.head, root.tail = (0, 0, 0), (0, 0, 1)
    child = armature.edit_bones.new("child")
    child.head, child.tail, child.parent = (0, 0, 1), (0, 0, 2), root
    bpy.ops.object.mode_set(mode="OBJECT")
    action = bpy.data.actions.new("GAA Imported Bezier Action")
    action.use_fake_user = True
    rig.animation_data_create().action = action
    for frame, root_x, angle in ((1, 0.0, -0.4), (3, 0.4, 0.7), (5, 0.8, -0.2)):
        rig.pose.bones["root"].location = (root_x, 0, 0)
        rig.pose.bones["root"].rotation_mode = "XYZ"
        rig.pose.bones["root"].rotation_euler = (0, 0, angle)
        rig.pose.bones["child"].rotation_mode = "XYZ"
        rig.pose.bones["child"].rotation_euler = (0, angle * 0.5, 0)
        for name in ("root", "child"):
            pose = rig.pose.bones[name]
            pose.keyframe_insert("location", frame=frame, group=name)
            pose.keyframe_insert("rotation_euler", frame=frame, group=name)
    for curve in api["_curves"](action):
        for point in curve.keyframe_points:
            point.interpolation = "BEZIER"
    source_snapshot = api["action_content_snapshot"](action)
    refs = api["_action_references"](action)
    request = {
        "schema": api["SCHEMA"], "scene_name": scene.name, "armature_name": rig.name,
        "source_action": action.name, "source_slot_identifier": action.slots[0].identifier,
        "target_action": "GAA Prepared Clip", "root_bone_name": "root",
        "frame": {"source_start": 2, "source_end": 4, "source_fps": 24,
                  "target_fps": 24, "output_start": 1},
        "sampling": {"mode": "EVALUATED_POSE", "key_cleanup": "EXACT_REDUNDANT"},
        "tolerances": {"translation": 1e-6, "rotation_radians": 1e-3, "scale": 1e-6},
        "policy": {"preserve_source": True, "bind_result": False,
                   "set_fake_user": True, "failure": "ROLL_BACK_NEW_DATA"},
    }
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    plan = api["preview_game_action_preparation"](request)
    check("bezier_missing_boundaries_supported", plan["status"] == "candidate_for_review")
    check("authorization_required",
          api["apply_game_action_preparation"](plan)["status"] == "error")
    collision = bpy.data.actions.new(request["target_action"])
    check("collision_refused", api["preview_game_action_preparation"](request)["status"] == "error")
    bpy.data.actions.remove(collision)
    plan = api["preview_game_action_preparation"](request)
    original_cleanup = api["_remove_exact_redundant"]
    api["_remove_exact_redundant"] = lambda _: (_ for _ in ()).throw(RuntimeError("induced"))
    failed = api["apply_game_action_preparation"](plan, True)
    api["_remove_exact_redundant"] = original_cleanup
    check("induced_failure_rolled_back", failed["status"] == "error"
          and bpy.data.actions.get(request["target_action"]) is None)
    receipt = api["apply_game_action_preparation"](
        api["preview_game_action_preparation"](request), True)
    prepared = bpy.data.actions.get(request["target_action"])
    if receipt["status"] != "created" or prepared is None:
        raise AssertionError("created: " + repr(receipt))
    checks.append("created")
    check("range_and_fps", receipt["frame_start"] == 1 and receipt["frame_end"] == 3
          and receipt["source_fps"] == receipt["target_fps"] == 24)
    check("independent_unbound", prepared.use_fake_user
          and api["_action_references"](prepared) == ([], []))
    check("sample_error_bounded",
          receipt["maximum_sampled_pose_error"]["translation"] <= 1e-6
          and receipt["maximum_sampled_pose_error"]["rotation_radians"] <= 1e-3
          and receipt["maximum_sampled_pose_error"]["scale"] <= 1e-6)
    check("source_preserved", api["action_content_snapshot"](action) == source_snapshot
          and api["_action_references"](action) == refs
          and rig.animation_data.action == action)
    quaternion_curves = [curve for curve in api["_curves"](prepared)
                         if curve.data_path.endswith("rotation_quaternion")]
    check("quaternion_output", len(quaternion_curves) == 8)
    bpy.data.actions.remove(prepared)
    downsample = json.loads(json.dumps(request))
    downsample["target_action"] = "GAA Prepared 12 FPS Clip"
    downsample["frame"]["target_fps"] = 12
    downsample["frame"]["output_start"] = 0
    downsample["sampling"]["key_cleanup"] = "NONE"
    downsampled = api["apply_game_action_preparation"](
        api["preview_game_action_preparation"](downsample), True)
    prepared = bpy.data.actions.get(downsample["target_action"])
    check("fps_resample_and_zero_rebase", downsampled["status"] == "created"
          and downsampled["sample_count"] == 2 and downsampled["frame_start"] == 0
          and downsampled["frame_end"] == 1 and downsampled["target_fps"] == 12)
    bpy.data.actions.remove(prepared)
    rig.animation_data_clear()
    action.use_fake_user = False
    bpy.data.actions.remove(action)
    bpy.data.objects.remove(rig, do_unlink=True)
    bpy.data.armatures.remove(armature)
    bpy.data.scenes.remove(scene)
    after = {name: sorted(item.name for item in getattr(bpy.data, name))
             for name in ("objects", "armatures", "meshes", "actions", "scenes")}
    check("fixture_cleanup", before == after)
    print("GAMEASSETAI_PREPARE_ACTION " + json.dumps(
        {"status": "pass", "checks": checks, "receipt": receipt}, sort_keys=True))


if __name__ == "__main__":
    main()
