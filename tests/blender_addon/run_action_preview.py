import argparse
from pathlib import Path
import sys

import bpy


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(args)


def main():
    root = Path(parse_args().repo_root).resolve()
    sys.path.insert(0, str(root / "blender_addon"))
    import gameassetai

    gameassetai.register()
    scene = bpy.context.scene
    bpy.ops.object.armature_add()
    armature = bpy.context.object
    armature.name = "GAA Preview Rig"
    first = bpy.data.actions.new("GAA Preview Idle")
    second = bpy.data.actions.new("GAA Preview Walk")
    armature.animation_data_create().action = first
    armature.pose.bones[0].rotation_mode = "XYZ"
    armature.pose.bones[0].rotation_euler.x = 0.0
    armature.pose.bones[0].keyframe_insert("rotation_euler", frame=1)
    armature.pose.bones[0].rotation_euler.x = 0.2
    armature.pose.bones[0].keyframe_insert("rotation_euler", frame=12)
    armature.animation_data.action = second
    armature.pose.bones[0].rotation_euler.x = 0.0
    armature.pose.bones[0].keyframe_insert("rotation_euler", frame=3)
    armature.pose.bones[0].rotation_euler.x = -0.2
    armature.pose.bones[0].keyframe_insert("rotation_euler", frame=18)
    armature.animation_data.action = first

    settings = scene.gameassetai
    settings.animation_armature = armature
    settings.animation_action = second
    result = bpy.ops.gameassetai.preview_action()
    assert result == {"FINISHED"}
    assert armature.animation_data.action == second
    assert (scene.frame_start, scene.frame_end, scene.frame_current) == (3, 18, 3)
    assert bpy.data.actions.get(first.name) is first and bpy.data.actions.get(second.name) is second

    gameassetai.unregister()
    print("GameAssetAI Action preview: 4 checks passed")


if __name__ == "__main__":
    main()
