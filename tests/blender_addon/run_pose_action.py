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
    sys.path[:0] = [str(root / "scripts"), str(root / "tests" / "blender_addon")]
    from run_character_base import request as character_request
    from create_character_base import create_character, remove_created_character
    from rig_character_base import create_rig, remove_created_rig
    from author_pose_action import author_action

    scene = bpy.context.scene
    char = create_character(character_request(scene.name), authorized=True)
    rig_request = {"schema":"gameassetai.character-rig-request.v1","scene_name":scene.name,"mesh_object_name":char["object_name"],"armature_object_name":"GAA Action Rig","armature_data_name":"GAA Action Armature","rig_name":"GAA Action","policy":{"target":"OWNED_CHARACTER_BASE_ONLY","existing_rig":"REFUSE","weights":"REGION_ASSIGNMENT_V1","source_mesh":"PRESERVE_GEOMETRY","failure":"ROLL_BACK_RIG_CHANGES"}}
    rig = create_rig(rig_request, authorized=True)
    action_request = {"schema":"gameassetai.pose-action-request.v1","scene_name":scene.name,"armature_object_name":rig["armature_object_name"],"action_name":"GAA Test Ready","frame_start":1,"frame_end":12,"fps":12,"front_axis":"-Y","keyframes":[{"frame":1,"rotations_degrees":{"upper_arm.L":[0,0,0],"forearm.L":[0,0,0]}},{"frame":6,"rotations_degrees":{"upper_arm.L":[0,0,-15],"forearm.L":[0,0,-45]}},{"frame":12,"rotations_degrees":{"upper_arm.L":[0,0,0],"forearm.L":[0,0,0]}}],"policy":{"existing_action":"REFUSE","current_action":"REQUIRE_EMPTY","channels":"ROTATION_EULER_XYZ_ONLY","interpolation":"BEZIER_AUTO_CLAMPED","mutation":"CREATE_AND_BIND"}}
    wrong = dict(action_request); wrong["front_axis"] = "+Y"
    try:
        author_action(wrong, authorized=True)
        raise AssertionError("front-axis mismatch must fail")
    except ValueError as exc:
        assert "front_axis mismatch" in str(exc)
    receipt = author_action(action_request, authorized=True)
    action = bpy.data.actions[receipt["action_name"]]
    assert receipt["status"] == "created" and receipt["fcurve_count"] == 6 and receipt["key_count"] == 18
    assert action.get("gameassetai_character_front_axis") == "-Y"
    assert bpy.data.objects[rig["armature_object_name"]].animation_data.action == action
    bpy.data.objects[rig["armature_object_name"]].animation_data.action = None
    bpy.data.actions.remove(action)
    location_request = {"schema":"gameassetai.pose-action-request.v2","scene_name":scene.name,"armature_object_name":rig["armature_object_name"],"action_name":"GAA Test Bob","frame_start":1,"frame_end":12,"fps":12,"front_axis":"-Y","keyframes":[{"frame":1,"rotations_degrees":{"thigh.L":[0,0,0]},"locations_local":{"root":[0,0,0]}},{"frame":6,"rotations_degrees":{"thigh.L":[10,0,0]},"locations_local":{"root":[0,0,0.025]}},{"frame":12,"rotations_degrees":{"thigh.L":[0,0,0]},"locations_local":{"root":[0,0,0]}}],"policy":{"existing_action":"REFUSE","current_action":"REQUIRE_EMPTY","channels":"ROTATION_EULER_XYZ_AND_LOCATION","interpolation":"BEZIER_AUTO_CLAMPED","mutation":"CREATE_AND_BIND"}}
    location_receipt = author_action(location_request, authorized=True)
    location_action = bpy.data.actions[location_receipt["action_name"]]
    assert location_receipt["location_bones"] == ["root"]
    assert location_receipt["fcurve_count"] == 6 and location_receipt["key_count"] == 18
    scene.frame_set(6)
    assert abs(bpy.data.objects[rig["armature_object_name"]].pose.bones["root"].location.z - 0.025) < 1e-6
    bpy.data.objects[rig["armature_object_name"]].animation_data.action = None
    bpy.data.actions.remove(location_action)
    remove_created_rig(rig); remove_created_character(char)
    print("GameAssetAI pose Action: 9 checks passed (front-axis and local-location guarded)")


if __name__ == "__main__":
    main()
