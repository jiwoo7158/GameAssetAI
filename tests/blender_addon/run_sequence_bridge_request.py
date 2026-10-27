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
    from gameassetai.operators.sequence_bridge import _load_helpers, _request

    gameassetai.register()
    scene = bpy.context.scene
    bpy.ops.object.armature_add()
    rig = bpy.context.object
    action = bpy.data.actions.new("GAA Bridge Action")
    rig.animation_data_create().action = action
    bone = rig.pose.bones[0]
    bone.rotation_mode = "XYZ"
    bone.keyframe_insert("rotation_euler", frame=1)
    bone.rotation_euler.x = 0.2
    bone.keyframe_insert("rotation_euler", frame=5)
    bpy.ops.mesh.primitive_cube_add()
    mesh = bpy.context.object
    settings = scene.gameassetai
    settings.animation_armature = rig
    settings.animation_action = action
    settings.material_target = mesh
    settings.sequence_output_directory = str(root)
    settings.sequence_prefix = "bridge-"
    settings.sequence_frame_step = 2
    request = _request(scene, settings)
    assert request["animation"]["action_name"] == action.name
    assert request["animation"]["frame_step"] == 2
    assert request["output"]["filename_prefix"] == "bridge-"
    namespace, renderer = _load_helpers(root / "scripts")
    assert callable(namespace["validate_2d_action_sequence_request"])
    assert renderer.name == "render_2d_action_sequence.py"
    gameassetai.unregister()
    print("GameAssetAI sequence bridge request: 5 checks passed")


if __name__ == "__main__":
    main()
